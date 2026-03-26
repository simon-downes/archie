"""Rich terminal output utilities."""

from rich.console import Console

console = Console()
console_err = Console(stderr=True)


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]Success:[/green] {message}")


def print_error(message: str) -> None:
    """Print error message."""
    console_err.print(f"[red]Error:[/red] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]Info:[/blue] {message}")


THEMES = {
    "blue": ["#a8d8ff", "#7bb8f0", "#4e98e0", "#2878d0", "#1060b8", "#0a4a9a"],
    "purple": ["#e8b4f8", "#d891f5", "#c471ed", "#ab4fe0", "#8b2fc9", "#6a0dad"],
    "green": ["#a8f0c0", "#78d89a", "#50c078", "#30a858", "#189040", "#087830"],
    "orange": ["#ffd0a0", "#ffb878", "#ff9850", "#e87830", "#d06018", "#b84808"],
    "cyan": ["#a8f0f0", "#78d8e0", "#50c0d0", "#30a0b8", "#1888a0", "#087088"],
    "red": ["#ffa8a8", "#f07878", "#e05050", "#c83030", "#b01818", "#900808"],
}


def display_header(tool_name: str, project: str, container_name: str) -> None:
    """Display execution context header with banner."""

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

    # Pad the E-bottom line to match the widest line, then append version
    max_width = max(len(line) for line in banner_lines)
    banner_lines[-2] = f"{banner_lines[-2]:<{max_width}}  [{colors[0]}]v{__version__}[/]"

    banner = "\n".join(f"[{c}]{line}[/]" for c, line in zip(colors, banner_lines, strict=True))
    info = (
        f"[{colors[0]}]{project}[/]"
        f" • [{colors[len(colors) // 2]}]{tool_name}[/]"
        f" • [{colors[-1]}]{container_name}[/]"
    )

    frame_color = colors[len(colors) // 2]

    from rich.panel import Panel

    content = f"{banner}\n\n{info}"
    console.print()
    console.print(Panel(content, border_style=frame_color, padding=(1, 2), width=80))
    console.print()
