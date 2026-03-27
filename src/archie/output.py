"""Rich terminal output — style guide primitives and colour palette."""

from datetime import UTC, datetime, timedelta

from rich.console import Console
from rich.rule import Rule
from rich.table import Table

WIDTH = 80

console = Console(width=WIDTH)
console_err = Console(stderr=True, width=WIDTH)

# --- Fixed text colours ---
C_HEADING = "bright_magenta"
C_KEY = "bright_blue"
C_CMD = "bright_cyan"
C_VAL = "#5f87d7"
C_PLAIN = "white"
C_MUTED = "bright_black"
C_CHROME = "dim"

# --- Status colours (icons only) ---
C_OK = "#50c878"
C_WARN = "#f0c050"
C_ERR = "bright_red"

# --- Theme colours (banner only) ---
THEMES = {
    "blue": ["#a8d8ff", "#7bb8f0", "#4e98e0", "#2878d0", "#1060b8", "#0a4a9a"],
    "purple": ["#e8b4f8", "#d891f5", "#c471ed", "#ab4fe0", "#8b2fc9", "#6a0dad"],
    "green": ["#a8f0c0", "#78d89a", "#50c078", "#30a858", "#189040", "#087830"],
    "orange": ["#ffd0a0", "#ffb878", "#ff9850", "#e87830", "#d06018", "#b84808"],
    "cyan": ["#a8f0f0", "#78d8e0", "#50c0d0", "#30a0b8", "#1888a0", "#087088"],
    "red": ["#ffa8a8", "#f07878", "#e05050", "#c83030", "#b01818", "#900808"],
}


def _icon(ok: bool | None) -> str:
    if ok is True:
        return f"[{C_OK}]✓[/]"
    if ok is False:
        return f"[{C_ERR}]✗[/]"
    return f"[{C_WARN}]![/]"


# --- Primitives ---


def section(title: str) -> None:
    """Section header with left-aligned rule."""
    console.print()
    console.print(Rule(f"[{C_HEADING}]{title}[/]", style=C_CHROME, align="left"))
    console.print()


def status_table(*rows: tuple) -> None:
    """Print a status table. Rows: (ok, label, detail) or (ok, label, sublabel, detail)."""
    t = Table(show_header=False, box=None, padding=(0, 2), pad_edge=True, expand=False)
    t.add_column(width=3)
    t.add_column(style=C_KEY, min_width=12)
    if any(len(r) > 3 for r in rows):
        t.add_column(style=C_MUTED, min_width=8)
    t.add_column(style=C_MUTED)
    for r in rows:
        t.add_row(_icon(r[0]), *[str(x) for x in r[1:]])
    console.print(t)


def kv_table(*rows: tuple[str, str]) -> None:
    """Print key-value pairs."""
    t = Table(show_header=False, box=None, padding=(0, 2), pad_edge=True, expand=False)
    t.add_column(style=C_MUTED, min_width=14)
    t.add_column(style=C_VAL)
    for k, v in rows:
        t.add_row(k, v)
    console.print(t)


def data_table(*rows: tuple, styles: list[str] | None = None) -> None:
    """Print a data table with custom column styles."""
    if not rows:
        return
    t = Table(show_header=False, box=None, padding=(0, 2), pad_edge=True, expand=False)
    col_styles = styles or [C_PLAIN] * len(rows[0])
    for s in col_styles:
        t.add_column(style=s)
    for r in rows:
        t.add_row(*[str(x) for x in r])
    console.print(t)


def print_success(message: str) -> None:
    """Success message. Accepts Rich markup."""
    console.print(f"  [{C_OK}]✓[/]  {message}")


def print_error(message: str) -> None:
    """Error message. Accepts Rich markup."""
    console_err.print(f"  [{C_ERR}]✗[/]  {message}")


def print_warning(message: str) -> None:
    """Warning message. Accepts Rich markup."""
    console.print(f"  [{C_WARN}]![/]  {message}")


def print_info(message: str) -> None:
    """Info message. Accepts Rich markup."""
    console.print(f"  [{C_KEY}]→[/]  {message}")


def bullet_list(items: list[str]) -> None:
    """Indented bullet list. Items accept Rich markup."""
    for item in items:
        console.print(f"    [{C_CHROME}]•[/]  {item}")


def empty_state(text: str) -> None:
    """Placeholder for empty results."""
    console.print(f"  [{C_MUTED}]{text}[/]")


def cmd(text: str) -> None:
    """Display a runnable command."""
    console.print(f"    [{C_CMD}]{text}[/]")


def human_time(iso_timestamp: str) -> str:
    """Convert ISO timestamp to human-friendly relative time."""
    try:
        target = datetime.fromisoformat(iso_timestamp)
        now = datetime.now(target.tzinfo or UTC)
        delta = target - now
        if delta.total_seconds() < 0:
            return _format_delta(-delta) + " ago"
        return "in " + _format_delta(delta)
    except (ValueError, TypeError):
        return iso_timestamp


def _format_delta(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        h, m = seconds // 3600, (seconds % 3600) // 60
        return f"{h}h {m}m" if m else f"{h}h"
    return f"{seconds // 86400}d"


def display_header(tool_name: str, project: str, container_name: str) -> None:
    """Display startup banner with themed gradient."""
    from rich.panel import Panel

    from archie import __version__
    from archie.config import load_config

    banner_lines = [
        " █████╗ ██████╗  ██████╗██╗  ██╗██╗███████╗",
        "██╔══██╗██╔══██╗██╔════╝██║  ██║██║██╔════╝",
        "███████║██████╔╝██║     ███████║██║█████╗  ",
        "██╔══██║██╔══██╗██║     ██╔══██║██║██╔══╝  ",
        "██║  ██║██║  ██║╚██████╗██║  ██║██║███████╗",
        "╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚══════╝",
    ]

    config = load_config()
    colors = THEMES.get(config.get("theme", "blue"), THEMES["blue"])

    max_width = max(len(line) for line in banner_lines)
    banner_lines[-2] = f"{banner_lines[-2]:<{max_width}}  [{colors[0]}]v{__version__}[/]"

    banner = "\n".join(f"[{c}]{line}[/]" for c, line in zip(colors, banner_lines, strict=True))
    info = (
        f"[{C_KEY}]{project}[/]"
        f" [{C_CHROME}]•[/] [{C_HEADING}]{tool_name}[/]"
        f" [{C_CHROME}]•[/] [{C_MUTED}]{container_name}[/]"
    )

    frame_color = colors[len(colors) // 2]
    content = f"{banner}\n\n{info}"

    console.print()
    console.print(Panel(content, border_style=frame_color, padding=(1, 2), width=WIDTH))
    console.print()
