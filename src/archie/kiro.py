"""archie kiro — assemble prompt and run kiro-cli."""

import os
import re
import subprocess
import sys
from pathlib import Path

import click

from archie.config import is_sandbox, load_config

KIRO_HOME = Path.home() / ".kiro"
PROMPT_OUT = KIRO_HOME / "archie" / "prompt.md"


@click.command()
@click.argument("prompt", nargs=-1)
def kiro(prompt: tuple[str, ...]) -> None:
    """Assemble system prompt and run kiro-cli."""
    if is_sandbox():
        _setup_persona()
    _assemble_prompt()
    _set_title()

    command = ["kiro-cli", "chat", "--agent", "archie"]
    if not sys.stdout.isatty():
        command.append("--no-interactive")
    if prompt:
        command.append(" ".join(prompt))

    try:
        sys.exit(subprocess.run(command).returncode)
    except FileNotFoundError:
        click.echo("Error: kiro-cli not found. Is it installed?", err=True)
        sys.exit(1)


def _setup_persona() -> None:
    """Symlink persona dirs to ~/.kiro/ paths (sandbox only)."""
    persona = Path("/opt/archie/persona")
    if not persona.exists():
        return

    KIRO_HOME.mkdir(parents=True, exist_ok=True)

    links = {
        "skills": "skills",
        "agents": "agents",
        "guidance": "steering",
    }
    for src_name, dest_name in links.items():
        src = persona / src_name
        dest = KIRO_HOME / dest_name
        if not src.exists():
            continue
        if dest.is_symlink() or dest.exists():
            if dest.is_symlink() and dest.resolve() == src.resolve():
                continue
            dest.unlink() if dest.is_symlink() else None
        dest.symlink_to(src)


def _assemble_prompt() -> None:
    """Resolve @ directives in soul.md and write assembled prompt."""
    config = load_config()
    brain_dir = Path(config.get("brain_dir", "~/.archie/brain")).expanduser()
    agent_dir = brain_dir / "_archie"
    user_dir = brain_dir / "simon"
    soul_path = agent_dir / "soul.md"

    if not soul_path.exists():
        return

    PROMPT_OUT.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for line in soul_path.read_text().splitlines():
        if line.startswith("@agent "):
            file = line[7:].strip()
            path = agent_dir / file
            if path.exists() and path.stat().st_size > 0:
                lines.append(path.read_text())
                lines.append("")
        elif line.startswith("@user "):
            file = line[6:].strip()
            path = user_dir / file
            if path.exists() and path.stat().st_size > 0:
                content = path.read_text()
                # Strip YAML frontmatter
                content = _strip_frontmatter(content)
                lines.append(content)
                lines.append("")
        elif line.startswith("@script "):
            alias = line[8:].strip()
            output = _run_script(alias, config, agent_dir)
            if output:
                lines.append(output)
                lines.append("")
        else:
            lines.append(line)

    PROMPT_OUT.write_text("\n".join(lines))


def _strip_frontmatter(content: str) -> str:
    """Strip YAML frontmatter (--- delimited) from content."""
    if not content.startswith("---"):
        return content
    lines = content.split("\n")
    # Find closing ---
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1 :])
    return content


def _run_script(alias: str, config: dict, agent_dir: Path) -> str | None:
    """Run a prompt script and return its stdout."""
    scripts = config.get("prompt", {}).get("scripts", {})
    cmd = scripts.get(alias)
    if not cmd:
        # Built-in: signals
        if alias == "signals":
            return _build_signals(agent_dir)
        return None

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() or None
    except (subprocess.TimeoutExpired, OSError):
        return None


def _build_signals(agent_dir: Path) -> str | None:
    """Build signals section from signals.yaml (inlined from build-signals.py)."""
    signals_path = agent_dir / "signals.yaml"
    if not signals_path.exists() or signals_path.stat().st_size == 0:
        return None

    signals = _parse_signals(signals_path)
    if not signals:
        return None

    recent = [s for s in reversed(signals) if s.get("type") in ("correction", "failure")][:7]
    patterns = _detect_patterns(signals)

    if not recent and not patterns:
        return None

    lines = [
        "# Signals",
        "",
        "These are recent mistakes and corrections. Avoid repeating them.",
        "",
    ]

    if recent:
        lines.append("Recent corrections/failures:")
        for s in recent:
            lines.append(f"- {s.get('summary', '?')}")
        lines.append("")

    if patterns:
        lines.append("Patterns:")
        for p in patterns:
            lines.append(f"- {p}")

    return "\n".join(lines)


def _parse_signals(path: Path) -> list[dict]:
    """Parse signals.yaml without PyYAML."""
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


def _detect_patterns(signals: list[dict]) -> list[str]:
    """Detect repeated signal categories."""
    counts: dict[str, int] = {}
    for s in signals:
        cat = s.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return [f"{cat}: {n} occurrences" for cat, n in sorted(counts.items()) if n >= 2]


def _set_title() -> None:
    """Set terminal title."""
    title = os.environ.get("ARCHIE_TITLE", "Archie")
    sys.stdout.write(f"\033]0;{title}\007")
    sys.stdout.flush()
