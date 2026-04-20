#!/usr/bin/env python3
"""AgentSpawn hook — inject learning context from signals and recent memory."""

import glob
import re
from pathlib import Path

SIGNALS_PATH = Path.home() / ".archie" / "brain" / "_memory" / "signals.yaml"
MEMORY_DIR = Path.home() / ".archie" / "brain" / "_memory"
MAX_SIGNALS = 7
PATTERN_THRESHOLD = 2


def load_signals() -> list[dict]:
    """Parse signals.yaml without PyYAML — each entry is a simple key: value block."""
    if not SIGNALS_PATH.exists():
        return []
    signals: list[dict] = []
    current: dict = {}
    for line in SIGNALS_PATH.read_text().splitlines():
        if line.startswith("- "):
            if current:
                signals.append(current)
            current = {}
            line = line[2:]
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(\w+):\s*"?(.+?)"?\s*$', line)
        if m:
            current[m.group(1)] = m.group(2)
    if current:
        signals.append(current)
    return signals


def detect_patterns(signals: list[dict]) -> list[str]:
    counts: dict[str, int] = {}
    for s in signals:
        cat = s.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return [f"{cat}: {n} occurrences" for cat, n in sorted(counts.items()) if n >= PATTERN_THRESHOLD]


def current_status() -> str:
    files = sorted(glob.glob(str(MEMORY_DIR / "*.md")), reverse=True)
    for f in files[:3]:
        text = Path(f).read_text()
        marker = "CURRENT STATUS:"
        idx = text.rfind(marker)
        if idx != -1:
            return text[idx + len(marker) :].strip().split("\n")[0].strip()
    return ""


def main() -> None:
    signals = load_signals()
    if not signals:
        return

    recent = [s for s in reversed(signals) if s.get("type") in ("correction", "failure")]
    recent = recent[:MAX_SIGNALS]
    patterns = detect_patterns(signals)
    status = current_status()

    lines = ["LEARNING CONTEXT:"]

    if recent:
        lines.append("Recent corrections/failures:")
        for s in recent:
            lines.append(f"- {s.get('summary', '?')}")

    if patterns:
        lines.append("Patterns:")
        for p in patterns:
            lines.append(f"- {p}")

    if status:
        lines.append(f"Status: {status}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
