"""CLI entry point for archie."""

import sys
from importlib.resources import as_file, files
from pathlib import Path

import click

from archie.auth.cli import auth  # noqa: E402
from archie.config import check_status, install, is_installed, load_config
from archie.docker import IMAGE_NAME, build_image, image_info, list_containers, run_container
from archie.output import (
    C_CMD,
    C_ERR,
    C_KEY,
    C_MUTED,
    C_OK,
    C_VAL,
    data_table,
    display_header,
    empty_state,
    human_time,
    print_error,
    print_info,
    print_success,
    section,
    status_table,
)

# Built-in commands that can't be used as tool names
BUILTIN_COMMANDS = {"install", "status", "build", "shell", "auth", "brain"}


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
@click.option("--plain", is_flag=True, help="Disable colours and formatting")
def main(plain: bool) -> None:
    """Archie — AI-assisted development toolkit."""
    if plain:
        from archie.output import console, console_err

        console.no_color = True
        console_err.no_color = True


main.add_command(auth)


@main.command(name="install")
def install_cmd() -> None:
    """Install persona and default config to ~/.archie/."""
    print_info("Installing Archie...")
    install()
    print_success(f"Installed to [{C_VAL}]~/.archie/[/]")


@main.command(name="brain")
@click.argument("name")
def brain_cmd(name: str) -> None:
    """Create a brain context with the standard directory structure."""
    from archie.config import BRAIN_PATH, create_brain_context

    context = BRAIN_PATH / name
    if context.exists():
        print_error(f"Brain context [{C_VAL}]{name}[/] already exists")
        sys.exit(1)

    create_brain_context(name)
    print_success(f"Created brain context [{C_VAL}]{name}[/] at [{C_VAL}]{context}[/]")


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool) -> None:
    """Check environment readiness."""
    import json as json_mod
    from datetime import datetime
    from pathlib import Path

    from archie.auth import get_field
    from archie.config import CONFIG_PATH

    s = check_status()
    config = load_config()

    # Collect all data
    img = image_info()
    containers = list_containers()

    auth_services = config.get("auth", {})
    creds_data = {}
    for service, svc_config in auth_services.items():
        svc_type = svc_config.get("type", "static")
        fields = svc_config.get("fields", ["access_token"] if svc_type == "oauth" else [])
        has_creds = any(get_field(service, f) is not None for f in fields)
        expires_at = get_field(service, "expires_at") if svc_type == "oauth" else None
        creds_data[service] = {
            "type": svc_type,
            "configured": has_creds,
            **({"expires_at": expires_at} if expires_at else {}),
        }

    mounts_data = []
    for entry in config.get("mounts", []):
        src = entry if isinstance(entry, str) else entry[0]
        mounts_data.append({"path": src, "exists": Path(src).expanduser().exists()})

    if as_json:
        data = {
            "environment": {
                "docker_installed": s.docker_installed,
                "docker_running": s.docker_running,
                "project_dir": s.project_dir,
                "project": s.project,
            },
            "image": {"name": IMAGE_NAME, **(img or {"created": None, "size": None})},
            "credentials": creds_data,
            "mounts": mounts_data,
            "sessions": containers,
            "config_path": str(CONFIG_PATH),
        }
        click.echo(json_mod.dumps(data, indent=2))
        return

    # Rich output
    display_header()

    section("Environment")
    status_table(
        (s.docker_installed, "Docker", "installed" if s.docker_installed else "not installed"),
        (s.docker_running, "Docker daemon", "running" if s.docker_running else "not running"),
        (s.project_dir_exists, "Project directory", s.project_dir),
        (s.project is not None, "Current project", s.project or "not in a project"),
    )

    section("Sandbox Image")
    if img:
        status_table((True, IMAGE_NAME, f"{img['created']}   {img['size']}"))
    else:
        status_table((False, IMAGE_NAME, "not built"))

    if auth_services:
        section("Credentials")
        rows = []
        for service, info in creds_data.items():
            detail = ""
            if info["type"] == "oauth" and info.get("expires_at"):
                try:
                    expiry = datetime.fromisoformat(info["expires_at"])
                    if datetime.now(expiry.tzinfo) > expiry:
                        detail = f"[{C_ERR}]expired {human_time(info['expires_at'])}[/]"
                    else:
                        detail = f"[{C_OK}]expires {human_time(info['expires_at'])}[/]"
                except (ValueError, TypeError):
                    pass
            elif not info["configured"]:
                detail = "not configured"
            rows.append((info["configured"], service, info["type"], detail))
        status_table(*rows)

    section("Mounts")
    status_table(
        *[(m["exists"], m["path"], "missing" if not m["exists"] else "") for m in mounts_data]
    )

    if containers:
        section("Sessions")
        data_table(
            *[(c["name"], c["status"], c["image"]) for c in containers],
            styles=[C_KEY, C_OK, C_MUTED],
        )

    section("Config")
    empty_state(str(CONFIG_PATH))


@main.command()
@click.option("--quick", is_flag=True, help="Use Docker cache for faster builds.")
def build(quick: bool) -> None:
    """Build the sandbox Docker image."""
    # Try package data first (installed mode), then source tree (editable mode)
    sandbox_pkg = files("archie").joinpath("sandbox", "Dockerfile")
    if sandbox_pkg.is_file():
        print_info(f"Building [{C_KEY}]{IMAGE_NAME}[/] image...")
        try:
            with as_file(sandbox_pkg) as dockerfile:
                build_image(dockerfile.parent, quick=quick)
            print_success(f"Built [{C_KEY}]{IMAGE_NAME}[/]")
            return
        except RuntimeError as e:
            print_error(str(e))
            sys.exit(1)

    # Editable install: look relative to the source tree
    source_dockerfile = Path(__file__).resolve().parent.parent.parent / "sandbox" / "Dockerfile"
    if source_dockerfile.is_file():
        print_info(f"Building [{C_KEY}]{IMAGE_NAME}[/] image...")
        try:
            build_image(source_dockerfile.parent, quick=quick)
            print_success(f"Built [{C_KEY}]{IMAGE_NAME}[/]")
            return
        except RuntimeError as e:
            print_error(str(e))
            sys.exit(1)

    print_error("Dockerfile not found in package data or source tree")
    sys.exit(1)


@main.command()
def shell() -> None:
    """Start an interactive shell in the sandbox."""
    s = check_status()
    if not s.ready:
        _print_not_ready(s)
        sys.exit(1)

    sys.exit(run_container(["/bin/bash"]))
