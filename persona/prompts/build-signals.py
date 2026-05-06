#!/usr/bin/env python3
"""Build signals section for prompt assembly. Reads signals.yaml, outputs markdown."""

import re
import sys
from pathlib import Path

MAX_SIGNALS = 7
PATTERN_THRESHOLD = 2


def load_signals(path: Path) -> list[dict]:
    """Parse signals.yaml without PyYAML — each entry is a simple key: value block."""
    if not path.exists():
        return []
    signals: list[dict] = []
    current: dict = {}
    for line in path.read_text().splitlines():
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


def main() -> None:
    if len(sys.argv) < 2:
        return

    signals_path = Path(sys.argv[1])
    signals = load_signals(signals_path)
    if not signals:
        return

    recent = [s for s in reversed(signals) if s.get("type") in ("correction", "failure")]
    recent = recent[:MAX_SIGNALS]
    patterns = detect_patterns(signals)

    if not recent and not patterns:
        return

    lines = ["# Signals", "", "These are recent mistakes and corrections. Avoid repeating them.", ""]

    if recent:
        lines.append("Recent corrections/failures:")
        for s in recent:
            lines.append(f"- {s.get('summary', '?')}")
        lines.append("")

    if patterns:
        lines.append("Patterns:")
        for p in patterns:
            lines.append(f"- {p}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
