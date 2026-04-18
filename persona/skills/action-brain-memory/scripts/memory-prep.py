#!/usr/bin/env python3
"""Prepare conversation transcripts for memory summarisation.

Reads kiro-cli conversation history, parses transcripts into clean turn pairs
(user input + assistant response), strips tool-use noise, and outputs structured
data ready for LLM summarisation.

Usage:
    python3 memory-prep.py [--since TIMESTAMP] [--project NAME] [--set-watermark TIMESTAMP]

Options:
    --since TIMESTAMP   Unix ms timestamp. Defaults to stored watermark.
    --project NAME      Only include conversations for this project.
    --set-watermark TS  Write watermark and exit (no output).

Output (JSON to stdout):
    {
        "conversations": [
            {
                "project": "archie",
                "date": "2026-04-18",
                "conversation_id": "abc-123",
                "updated_at": 1713434567000,
                "turns": [
                    {"user": "...", "assistant": "..."},
                    ...
                ]
            },
            ...
        ],
        "watermark": 1713434567000
    }

project is the project name derived from the working directory, or empty string
for general (non-project) sessions.
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

KIRO_DB = Path.home() / ".local" / "share" / "kiro-cli" / "data.sqlite3"
BRAIN_DB = Path.home() / ".archie" / "brain" / "shared" / "brain.db"
AK_CONFIG = Path.home() / ".agent-kit" / "config.yaml"

# Lines matching these prefixes are stripped from assistant responses
TOOL_NOISE = ("[Tool uses:", "[Tool use:", "[Subagent")


def _project_dir_name() -> str:
    """Load the basename of project_dir from agent-kit config (e.g. 'dev')."""
    if AK_CONFIG.exists():
        try:
            import yaml

            with AK_CONFIG.open() as f:
                config = yaml.safe_load(f) or {}
            return Path(config.get("project_dir", "~/dev")).expanduser().name
        except Exception:
            pass
    return "dev"


def get_watermark() -> int:
    """Read the last-processed watermark. Returns 0 if unset."""
    if not BRAIN_DB.exists():
        return 0
    conn = sqlite3.connect(BRAIN_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS memory_watermark "
        "(id INTEGER PRIMARY KEY CHECK (id = 1), last_processed_at INTEGER NOT NULL)"
    )
    row = conn.execute("SELECT last_processed_at FROM memory_watermark WHERE id = 1").fetchone()
    conn.close()
    return row[0] if row else 0


def set_watermark(ts: int) -> None:
    """Write the watermark."""
    BRAIN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(BRAIN_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS memory_watermark "
        "(id INTEGER PRIMARY KEY CHECK (id = 1), last_processed_at INTEGER NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO memory_watermark (id, last_processed_at) VALUES (1, ?)", (ts,)
    )
    conn.commit()
    conn.close()


def resolve_project(key: str) -> str:
    """Extract project name from a conversation key (working directory path)."""
    dir_name = _project_dir_name()
    marker = f"/{dir_name}/"
    idx = key.find(marker)
    if idx == -1:
        return ""
    remainder = key[idx + len(marker) :]
    if not remainder:
        return ""
    return remainder.split("/")[0]


def parse_turns(transcript: list) -> list[dict]:
    """Parse transcript items into user/assistant turn pairs.

    User messages start with '>'. Consecutive non-user items are the assistant
    response. Tool-use lines are stripped.
    """
    turns = []
    current_user = None
    current_asst = []

    for item in transcript:
        s = str(item).strip()
        if not s:
            continue

        if s.startswith(">"):
            if current_user is not None:
                turns.append(_make_turn(current_user, current_asst))
            current_user = s.lstrip("> ").strip()
            current_asst = []
        else:
            if any(s.startswith(prefix) for prefix in TOOL_NOISE):
                continue
            # Strip inline tool-use markers
            cleaned = s
            for prefix in TOOL_NOISE:
                while prefix in cleaned:
                    start = cleaned.index(prefix)
                    end = cleaned.find("]", start)
                    if end == -1:
                        break
                    cleaned = (cleaned[:start] + cleaned[end + 1 :]).strip()
            if cleaned:
                current_asst.append(cleaned)

    if current_user is not None:
        turns.append(_make_turn(current_user, current_asst))

    return turns


def _make_turn(user: str, asst_parts: list[str]) -> dict:
    """Create a turn dict from user text and assistant response parts."""
    asst = "\n\n".join(p for p in asst_parts if p.strip())
    return {"user": user, "assistant": asst}


def main() -> None:
    args = sys.argv[1:]

    if "--set-watermark" in args:
        idx = args.index("--set-watermark")
        ts = int(args[idx + 1])
        set_watermark(ts)
        print(f"Watermark set to {ts}", file=sys.stderr)
        return

    since = None
    project_filter = None
    i = 0
    while i < len(args):
        if args[i] == "--since" and i + 1 < len(args):
            since = int(args[i + 1])
            i += 2
        elif args[i] == "--project" and i + 1 < len(args):
            project_filter = args[i + 1]
            i += 2
        else:
            print(f"Unknown argument: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if since is None:
        since = get_watermark()

    if not KIRO_DB.exists():
        print(json.dumps({"conversations": [], "watermark": since}))
        return

    conn = sqlite3.connect(KIRO_DB)
    rows = conn.execute(
        "SELECT key, conversation_id, value, updated_at "
        "FROM conversations_v2 WHERE updated_at > ? ORDER BY updated_at ASC",
        (since,),
    ).fetchall()
    conn.close()

    conversations = []
    max_watermark = since

    for key, conversation_id, value, updated_at in rows:
        project = resolve_project(key)
        if project_filter and project != project_filter:
            continue

        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            continue

        transcript = data.get("transcript", [])
        if not transcript:
            continue

        turns = parse_turns(transcript)
        if not turns:
            continue

        date = datetime.fromtimestamp(updated_at / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

        conversations.append({
            "project": project,
            "date": date,
            "conversation_id": conversation_id,
            "updated_at": updated_at,
            "turns": turns,
        })
        max_watermark = max(max_watermark, updated_at)

    print(
        json.dumps({"conversations": conversations, "watermark": max_watermark}, indent=2),
        file=sys.stdout,
    )
    print(f"Found {len(conversations)} conversations since {since}", file=sys.stderr)


if __name__ == "__main__":
    main()
