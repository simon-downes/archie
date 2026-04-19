#!/usr/bin/env python3
"""Prepare conversation transcripts for memory summarisation.

Reads kiro-cli conversation history from both storage formats:
- SQLite (older): ~/.local/share/kiro-cli/data.sqlite3
- File-based (newer): ~/.kiro/sessions/cli/<id>.json + <id>.jsonl

Parses transcripts into clean turn pairs (user input + assistant response),
strips tool-use noise, and outputs structured data ready for LLM summarisation.

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
SESSIONS_DIR = Path.home() / ".kiro" / "sessions" / "cli"
BRAIN_DB = Path.home() / ".archie" / "brain" / "shared" / "brain.db"
AK_CONFIG = Path.home() / ".agent-kit" / "config.yaml"


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


def _iso_to_ms(iso_str: str) -> int:
    """Convert ISO 8601 timestamp to unix milliseconds."""
    # Handle nanosecond precision by truncating to microseconds
    if "." in iso_str:
        base, frac = iso_str.split(".")
        # Split off timezone suffix
        tz_suffix = ""
        for tz in ("Z", "+", "-"):
            if tz in frac:
                idx = frac.index(tz)
                tz_suffix = frac[idx:]
                frac = frac[:idx]
                break
        frac = frac[:6]  # truncate to microseconds
        iso_str = f"{base}.{frac}{tz_suffix}"
    iso_str = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso_str)
    return int(dt.timestamp() * 1000)


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


# --- SQLite format (older) ---


def _parse_transcript_turns(transcript: list) -> list[dict]:
    """Parse transcript items into user/assistant turn pairs.

    User messages start with '>'. Consecutive non-user items are the assistant
    response. Tool-use lines are stripped.
    """
    turns = []
    current_user = None
    current_asst: list[str] = []

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
            cleaned = _strip_tool_noise(s)
            if cleaned:
                current_asst.append(cleaned)

    if current_user is not None:
        turns.append(_make_turn(current_user, current_asst))

    return turns


def load_sqlite_conversations(since: int) -> list[dict]:
    """Load conversations from the SQLite database."""
    if not KIRO_DB.exists():
        return []

    conn = sqlite3.connect(KIRO_DB)
    rows = conn.execute(
        "SELECT key, conversation_id, value, updated_at "
        "FROM conversations_v2 WHERE updated_at > ? ORDER BY updated_at ASC",
        (since,),
    ).fetchall()
    conn.close()

    conversations = []
    for key, conversation_id, value, updated_at in rows:
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            continue

        transcript = data.get("transcript", [])
        if not transcript:
            continue

        turns = _parse_transcript_turns(transcript)
        if not turns:
            continue

        conversations.append({
            "project": resolve_project(key),
            "date": datetime.fromtimestamp(updated_at / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
            "conversation_id": conversation_id,
            "updated_at": updated_at,
            "turns": turns,
        })

    return conversations


# --- File-based format (newer) ---


def _parse_jsonl_turns(jsonl_path: Path, since_ts: int = 0) -> list[dict]:
    """Parse a .jsonl session file into user/assistant turn pairs.

    Only includes turns where the Prompt timestamp is after since_ts (unix seconds).
    """
    turns = []
    current_user = None
    current_asst: list[str] = []
    include_turn = since_ts == 0

    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            kind = entry.get("kind")
            data = entry.get("data", {})

            if kind == "Prompt":
                if current_user is not None and include_turn:
                    turns.append(_make_turn(current_user, current_asst))
                current_user = _extract_text(data)
                current_asst = []
                ts = data.get("meta", {}).get("timestamp", 0)
                include_turn = ts > since_ts

            elif kind == "AssistantMessage" and include_turn:
                text = _extract_text(data)
                if text:
                    cleaned = _strip_tool_noise(text)
                    if cleaned:
                        current_asst.append(cleaned)

    if current_user is not None and include_turn:
        turns.append(_make_turn(current_user, current_asst))

    return turns


def _extract_text(data: dict) -> str:
    """Extract text content from a Prompt or AssistantMessage data dict."""
    content = data.get("content", [])
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("kind") == "text":
                parts.append(item.get("data", ""))
        return "\n".join(parts).strip()
    if isinstance(content, str):
        return content.strip()
    # Fallback for simple prompt format
    prompt = data.get("prompt", "")
    if isinstance(prompt, str):
        return prompt.strip()
    return ""


def load_file_conversations(since: int) -> list[dict]:
    """Load conversations from the file-based session store."""
    if not SESSIONS_DIR.exists():
        return []

    conversations = []
    for json_path in sorted(SESSIONS_DIR.glob("*.json")):
        jsonl_path = json_path.with_suffix(".jsonl")
        if not jsonl_path.exists():
            continue

        try:
            meta = json.loads(json_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        updated_at_str = meta.get("updated_at", "")
        if not updated_at_str:
            continue

        updated_at = _iso_to_ms(updated_at_str)
        if updated_at <= since:
            continue

        cwd = meta.get("cwd", "")
        session_id = meta.get("session_id", json_path.stem)

        # Skip subagent sessions (no agent_name set)
        agent_name = (meta.get("session_state") or {}).get("agent_name")
        if not agent_name:
            continue

        turns = _parse_jsonl_turns(jsonl_path, since_ts=since // 1000)
        if not turns:
            continue

        conversations.append({
            "project": resolve_project(cwd),
            "date": updated_at_str[:10],
            "conversation_id": session_id,
            "updated_at": updated_at,
            "turns": turns,
        })

    return conversations


# --- Shared helpers ---


def _strip_tool_noise(s: str) -> str:
    """Remove tool-use markers from a string."""
    noise_prefixes = ("[Tool uses:", "[Tool use:", "[Subagent")
    if any(s.startswith(p) for p in noise_prefixes):
        return ""
    cleaned = s
    for prefix in noise_prefixes:
        while prefix in cleaned:
            start = cleaned.index(prefix)
            end = cleaned.find("]", start)
            if end == -1:
                break
            cleaned = (cleaned[:start] + cleaned[end + 1 :]).strip()
    return cleaned


def _make_turn(user: str, asst_parts: list[str]) -> dict:
    """Create a turn dict from user text and assistant response parts."""
    asst = "\n\n".join(p for p in asst_parts if p.strip())
    return {"user": user, "assistant": asst}


# --- Main ---


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

    # Load from both sources
    conversations = load_sqlite_conversations(since) + load_file_conversations(since)

    # Filter by project if requested
    if project_filter:
        conversations = [c for c in conversations if c["project"] == project_filter]

    # Sort by updated_at
    conversations.sort(key=lambda c: c["updated_at"])

    max_watermark = max((c["updated_at"] for c in conversations), default=since)

    print(
        json.dumps({"conversations": conversations, "watermark": max_watermark}, indent=2),
        file=sys.stdout,
    )
    print(f"Found {len(conversations)} conversations since {since}", file=sys.stderr)


if __name__ == "__main__":
    main()
