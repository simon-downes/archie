# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Identify unprocessed session logs and compute batches for memory extraction."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

TRIVIAL_THRESHOLD = 100  # total user content chars
SMALL_SESSION_TURNS = 10
SMALL_BATCH_SIZE = 5


def load_config() -> tuple[Path, str]:
    """Read brain dir and agent name from archie config."""
    config_path = Path.home() / ".archie" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    brain_dir = Path(config.get("brain_dir", "~/.archie/brain")).expanduser()
    agent = "archie"
    return brain_dir, agent


def load_processed(path: Path) -> dict[str, dict]:
    """Parse .processed file into {session_id: {turns, status, processed_at}}."""
    entries = {}
    if not path.exists():
        return entries
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            entries[parts[0]] = {
                "turns": int(parts[1]),
                "status": parts[2],
                "processed_at": parts[3],
            }
    return entries


def save_processed(path: Path, entries: dict[str, dict]):
    """Write .processed file from entries dict."""
    lines = []
    for sid, info in sorted(entries.items()):
        lines.append(f"{sid}\t{info['turns']}\t{info['status']}\t{info['processed_at']}")
    path.write_text("\n".join(lines) + "\n")


def parse_log(path: Path) -> dict | None:
    """Extract metadata from a distilled log file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "turns" not in data:
        return None
    turns = data.get("turns") or []
    total_user_content = sum(len(t.get("user") or "") for t in turns)
    return {
        "path": str(path),
        "session_id": data["session_id"],
        "project": data.get("project", "general"),
        "started": data.get("started", ""),
        "turns": len(turns),
        "total_user_content": total_user_content,
    }


def classify_sessions(logs_dir: Path, processed: dict) -> tuple[list, list, int, int]:
    """Classify all logs into actionable/trivial/up-to-date."""
    actionable = []
    trivial_new = []
    up_to_date = 0

    for log_file in sorted(logs_dir.glob("*.yaml")):
        meta = parse_log(log_file)
        if meta is None:
            continue

        sid = meta["session_id"]
        entry = processed.get(sid)

        if entry:
            if meta["turns"] <= entry["turns"]:
                up_to_date += 1
                continue
            # Turn count increased — delta
            actionable.append({
                "path": meta["path"],
                "mode": "delta",
                "turns": meta["turns"],
                "processed_at": entry["processed_at"],
            })
        else:
            # New session — check if trivial
            if meta["total_user_content"] < TRIVIAL_THRESHOLD:
                trivial_new.append(meta)
            else:
                actionable.append({
                    "path": meta["path"],
                    "mode": "new",
                    "turns": meta["turns"],
                })

    return actionable, trivial_new, up_to_date, len(trivial_new)


def compute_batches(actionable: list) -> list[list]:
    """Group actionable sessions into batches by sizing rules."""
    large = [s for s in actionable if s["turns"] >= SMALL_SESSION_TURNS]
    small = [s for s in actionable if s["turns"] < SMALL_SESSION_TURNS]

    batches = []
    # Large sessions: 1 per batch
    for session in large:
        batches.append([session])

    # Small sessions: up to SMALL_BATCH_SIZE per batch
    for i in range(0, len(small), SMALL_BATCH_SIZE):
        batches.append(small[i : i + SMALL_BATCH_SIZE])

    return batches


def main():
    brain_dir, agent = load_config()
    logs_dir = brain_dir / f"_{agent}" / "logs"
    processed_path = logs_dir / ".processed"

    processed = load_processed(processed_path)
    actionable, trivial_new, up_to_date, skipped_count = classify_sessions(
        logs_dir, processed
    )

    # Record trivial sessions in .processed
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for meta in trivial_new:
        processed[meta["session_id"]] = {
            "turns": meta["turns"],
            "status": "skipped",
            "processed_at": now,
        }
    save_processed(processed_path, processed)

    # Compute batches
    batches = compute_batches(actionable)

    # Count modes
    new_count = sum(1 for s in actionable if s["mode"] == "new")
    delta_count = sum(1 for s in actionable if s["mode"] == "delta")

    parts = []
    if new_count + delta_count > 0:
        parts.append(f"{new_count + delta_count} to process ({new_count} new, {delta_count} delta)")
    if skipped_count > 0:
        parts.append(f"{skipped_count} trivial skipped")
    parts.append(f"{up_to_date} up-to-date")
    summary = ", ".join(parts)

    output = {
        "batches": batches,
        "skipped": skipped_count,
        "up_to_date": up_to_date,
        "summary": summary,
    }

    json.dump(output, sys.stdout, indent=2)
    print(file=sys.stderr)
    print(summary, file=sys.stderr)


if __name__ == "__main__":
    main()
