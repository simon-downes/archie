#!/usr/bin/env python3
"""Prepare conversation transcripts for memory extraction.

Reads kiro-cli conversation history, extracts transcripts, normalises project names,
and outputs a JSON payload grouped by project — ready for LLM processing.

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
                "context": "shared",
                "conversation_id": "abc-123",
                "updated_at": 1713434567000,
                "transcript": "full transcript text..."
            },
            ...
        ],
        "watermark": 1713434567000
    }
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

KIRO_DB = Path.home() / ".local" / "share" / "kiro-cli" / "data.sqlite3"
BRAIN_DIR = Path.home() / ".archie" / "brain"
BRAIN_DB = BRAIN_DIR / "shared" / "brain.db"

# Matches /Users/<user>/dev/<project> or /home/<user>/dev/<project>
PROJECT_RE = re.compile(r"^/(?:Users|home)/[^/]+/dev/([^/]+)")


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


def resolve_project(key: str) -> str | None:
    """Extract project name from a conversation key (working directory path)."""
    m = PROJECT_RE.match(key)
    return m.group(1) if m else None


def resolve_context(project: str) -> str:
    """Map a project name to a brain context. Falls back to 'shared'."""
    for ctx_dir in sorted(BRAIN_DIR.iterdir()):
        if not ctx_dir.is_dir() or ctx_dir.name.startswith(("_", ".")):
            continue
        project_dir = ctx_dir / "projects" / project
        if project_dir.exists():
            return ctx_dir.name
    return "shared"


def main() -> None:
    args = sys.argv[1:]

    # Handle --set-watermark
    if "--set-watermark" in args:
        idx = args.index("--set-watermark")
        ts = int(args[idx + 1])
        set_watermark(ts)
        print(f"Watermark set to {ts}", file=sys.stderr)
        return

    # Parse options
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
        if not project:
            continue
        if project_filter and project != project_filter:
            continue

        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            continue

        transcript_parts = data.get("transcript", [])
        if not transcript_parts:
            continue

        transcript = "\n".join(str(t) for t in transcript_parts)
        if len(transcript.strip()) < 100:
            continue

        context = resolve_context(project)
        conversations.append({
            "project": project,
            "context": context,
            "conversation_id": conversation_id,
            "updated_at": updated_at,
            "transcript": transcript,
        })
        max_watermark = max(max_watermark, updated_at)

    print(
        json.dumps({"conversations": conversations, "watermark": max_watermark}, indent=2),
        file=sys.stdout,
    )
    print(f"Found {len(conversations)} conversations since {since}", file=sys.stderr)


if __name__ == "__main__":
    main()
