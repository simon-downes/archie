"""CLI entry point for archie."""

import sys
from importlib.resources import as_file, files

import click

from archie.auth.cli import auth  # noqa: E402
from archie.config import check_status, install, is_installed, load_config
from archie.docker import IMAGE_NAME, build_image, list_containers, run_container
from archie.output import (
    C_CMD,
    C_ERR,
    C_KEY,
    C_MUTED,
    C_OK,
    C_VAL,
    bullet_list,
    data_table,
    display_header,
    human_time,
    print_error,
    print_info,
    print_success,
    section,
    status_table,
)

# Built-in commands that can't be used as tool names
BUILTIN_COMMANDS = {"install", "status", "build", "shell", "auth"}


class ArchieCLI(click.Group):
    """Click group with install guard and dynamic tool commands."""

    def invoke(self, ctx):
        subcommand = ctx.invoked_subcommand or (
            ctx.protected_args[0] if ctx.protected_args else None
        )
        if subcommand and subcommand != "install" and not is_installed():
            print_error(f"Archie is not installed. Run [{C_CMD}]archie install[/] first.")
            sys.exit(1)
        return super().invoke(ctx)

    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = list(super().list_commands(ctx))
        if is_installed():
            config = load_config()
            for name in config.get("tools", {}):
                if name not in commands:
                    commands.append(name)
        return sorted(commands)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        cmd = super().get_command(ctx, cmd_name)
        if cmd:
            return cmd

        if not is_installed():
            return None

        config = load_config()
        tools = config.get("tools", {})
        if cmd_name in tools:
            return _make_tool_command(cmd_name, tools[cmd_name])

        return None


def _make_tool_command(name: str, tool_config: dict) -> click.Command:
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

        args = ctx.args if ctx.args else default_args
        sys.exit(run_container([command, *args], tool_name=name))

    tool_cmd.help = f"Run {command} in the sandbox."
    return tool_cmd


def _print_not_ready(s) -> None:
    if not s.docker_installed:
        print_error(f"[{C_KEY}]Docker[/] is not installed")
    elif not s.docker_running:
        print_error(f"[{C_KEY}]Docker[/] is not running")
    elif not s.project_dir_exists:
        print_error(f"Project directory not found: [{C_VAL}]{s.project_dir}[/]")


@click.group(cls=ArchieCLI)
def main() -> None:
    """Archie — AI-assisted development toolkit."""


main.add_command(auth)


@main.command(name="install")
def install_cmd() -> None:
    """Install persona and default config to ~/.archie/."""
    print_info("Installing Archie...")
    install()
    print_success(f"Installed to [{C_VAL}]~/.archie/[/]")


@main.command()
def status() -> None:
    """Check environment readiness."""
    s = check_status()

    display_header()

    section("Environment")
    status_table(
        (s.docker_installed, "Docker", "installed" if s.docker_installed else "not installed"),
        (s.docker_running, "Docker daemon", "running" if s.docker_running else "not running"),
        (s.project_dir_exists, "Project directory", s.project_dir),
        (s.project is not None, "Current project", s.project or "not in a project"),
    )

    if s.missing_mounts:
        section("Missing Mounts")
        bullet_list([f"[{C_VAL}]{m}[/]" for m in s.missing_mounts])

    # Credentials
    config = load_config()
    auth_services = config.get("auth", {})
    if auth_services:
        from datetime import datetime

        from archie.auth import get_field

        section("Credentials")
        rows = []
        for service, svc_config in auth_services.items():
            svc_type = svc_config.get("type", "static")
            fields = svc_config.get("fields", ["access_token"] if svc_type == "oauth" else [])
            has_creds = any(get_field(service, f) is not None for f in fields)
            detail = ""

            if svc_type == "oauth":
                expires_at = get_field(service, "expires_at")
                if expires_at:
                    try:
                        expiry = datetime.fromisoformat(expires_at)
                        if datetime.now(expiry.tzinfo) > expiry:
                            detail = f"[{C_ERR}]expired {human_time(expires_at)}[/]"
                        else:
                            detail = f"[{C_OK}]expires {human_time(expires_at)}[/]"
                    except (ValueError, TypeError):
                        pass
            elif not has_creds:
                detail = "not configured"

            rows.append((has_creds, service, svc_type, detail))

        status_table(*rows)

    # Sessions
    containers = list_containers()
    if containers:
        section("Sessions")
        data_table(
            *[(c["name"], c["status"], c["image"]) for c in containers],
            styles=[C_KEY, C_OK, C_MUTED],
        )


@main.command()
def build() -> None:
    """Build the sandbox Docker image."""
    sandbox_pkg = files("archie").joinpath("sandbox", "Dockerfile")
    if not sandbox_pkg.is_file():
        print_error("Dockerfile not found in package data")
        sys.exit(1)

    print_info(f"Building [{C_KEY}]{IMAGE_NAME}[/] image...")
    try:
        with as_file(sandbox_pkg) as dockerfile:
            build_image(dockerfile.parent)
        print_success(f"Built [{C_KEY}]{IMAGE_NAME}[/]")
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
