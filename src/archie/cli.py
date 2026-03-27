"""CLI entry point for archie."""

import sys
from importlib.resources import as_file, files

import click

from archie.auth.cli import auth  # noqa: E402
from archie.config import check_status, install, is_installed, load_config
from archie.docker import IMAGE_NAME, build_image, list_containers, run_container
from archie.output import print_error, print_info, print_success

# Built-in commands that can't be used as tool names
BUILTIN_COMMANDS = {"install", "status", "build", "shell", "list", "auth"}


class ArchieCLI(click.Group):
    """Click group with install guard and dynamic tool commands."""

    def invoke(self, ctx):
        # Allow install without prior setup
        subcommand = ctx.invoked_subcommand or (
            ctx.protected_args[0] if ctx.protected_args else None
        )
        if subcommand and subcommand != "install" and not is_installed():
            print_error("Archie is not installed. Run 'archie install' first.")
            sys.exit(1)
        return super().invoke(ctx)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List built-in commands plus configured tools."""
        commands = list(super().list_commands(ctx))
        if is_installed():
            config = load_config()
            for name in config.get("tools", {}):
                if name not in commands:
                    commands.append(name)
        return sorted(commands)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Resolve built-in commands first, then configured tools."""
        # Try built-in commands first
        cmd = super().get_command(ctx, cmd_name)
        if cmd:
            return cmd

        # Try configured tools
        if not is_installed():
            return None

        config = load_config()
        tools = config.get("tools", {})
        if cmd_name in tools:
            return _make_tool_command(cmd_name, tools[cmd_name])

        return None


def _make_tool_command(name: str, tool_config: dict) -> click.Command:
    """Create a Click command for a configured tool."""
    command = tool_config["command"]
    default_args = tool_config.get("args", [])

    @click.command(
        name=name,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
        add_help_option=False,
    )
    @click.pass_context
    def tool_cmd(ctx: click.Context) -> None:
        s = check_status()
        if not s.ready:
            _print_not_ready(s)
            sys.exit(1)

        # Extra args replace defaults
        args = ctx.args if ctx.args else default_args
        sys.exit(run_container([command, *args], tool_name=name))

    tool_cmd.help = f"Run {command} in the sandbox."
    return tool_cmd


def _print_not_ready(s) -> None:
    """Print the first failing readiness check."""
    if not s.docker_installed:
        print_error("Docker is not installed")
    elif not s.docker_running:
        print_error("Docker is not running")
    elif not s.project_dir_exists:
        print_error(f"Project directory not found: {s.project_dir}")


@click.group(cls=ArchieCLI)
def main() -> None:
    """Archie — AI-assisted development toolkit."""


main.add_command(auth)


@main.command(name="install")
def install_cmd() -> None:
    """Install persona and default config to ~/.archie/."""
    print_info("Installing Archie...")
    install()
    print_success("Installed to ~/.archie/")


@main.command()
def status() -> None:
    """Check environment readiness."""
    from rich.console import Console

    console = Console()
    s = check_status()

    def check(ok: bool, label: str, detail: str = "") -> None:
        icon = "[green]✓[/]" if ok else "[red]✗[/]"
        msg = f"  {icon} {label}"
        if detail:
            msg += f"  [dim]{detail}[/]"
        console.print(msg)

    check(s.docker_installed, "Docker installed")
    check(s.docker_running, "Docker running")
    check(s.project_dir_exists, "Project directory", s.project_dir)
    check(s.project is not None, "Current project", s.project or "not in a project")

    if s.missing_mounts:
        console.print("\n  [yellow]![/] Missing mounts:")
        for m in s.missing_mounts:
            console.print(f"    [dim]{m}[/]")


@main.command()
def build() -> None:
    """Build the sandbox Docker image."""
    sandbox_pkg = files("archie").joinpath("sandbox", "Dockerfile")
    if not sandbox_pkg.is_file():
        print_error("Dockerfile not found in package data")
        sys.exit(1)

    print_info(f"Building {IMAGE_NAME} image...")
    try:
        with as_file(sandbox_pkg) as dockerfile:
            build_image(dockerfile.parent)
        print_success(f"Built {IMAGE_NAME}")
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(1)


@main.command()
def shell() -> None:
    """Start an interactive shell in the sandbox."""
    s = check_status()
    if not s.ready:
        _print_not_ready(s)
        sys.exit(1)

    sys.exit(run_container(["/bin/bash"]))


@main.command(name="list")
def list_cmd() -> None:
    """List running archie sessions."""
    from rich.console import Console

    containers = list_containers()
    if not containers:
        click.echo("No active sessions")
        return

    console = Console()
    for c in containers:
        console.print(f"[bright_blue]{c['name']}[/]  {c['status']}  {c['image']}")
