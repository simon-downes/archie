"""CLI entry point for archie."""

import os
import shutil
import sys
from importlib.resources import as_file, files
from pathlib import Path

import click

from archie.config import check_status, install, is_installed, is_sandbox, load_config
from archie.docker import (
    IMAGE_NAME,
    SESSIONS_DIR,
    build_image,
    container_name_for_session,
    create_session_clone,
    docker_output,
    hash_suffix,
    image_info,
    list_containers,
    list_sessions,
    resolve_session,
    run_container,
    session_status,
)
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
BUILTIN_COMMANDS = {"install", "status", "build", "ls", "rm"}


def _safe_remove_session(session_dir: Path) -> None:
    """Remove a session directory, with safety check that it's under SESSIONS_DIR."""
    try:
        session_dir.resolve().relative_to(SESSIONS_DIR.resolve())
    except ValueError:
        print_error(f"Refusing to delete {session_dir} — not under {SESSIONS_DIR}")
        sys.exit(1)
    shutil.rmtree(session_dir)
    # Clean up empty parent
    parent = session_dir.parent
    if parent.exists() and parent != SESSIONS_DIR and not any(parent.iterdir()):
        parent.rmdir()


class ArchieCLI(click.Group):
    """Click group with install guard and dynamic tool commands.

    Overrides parse_args so that unrecognised positional arguments are treated
    as prompt text rather than erroring with "No such command".
    """

    def parse_args(self, ctx, args):
        """Intercept args before command resolution to extract prompt."""
        # Find the first non-option arg and check if it's a command
        rest = list(args)
        opts = []
        # NOTE: if a new value-taking option is added to main(), add it here too
        value_options = ("--name",)
        while rest:
            if rest[0].startswith("-"):
                opt = rest.pop(0)
                opts.append(opt)
                if opt in value_options and rest:
                    opts.append(rest.pop(0))
            else:
                break

        if rest:
            # Check if first positional is a known command
            cmd_name = rest[0]
            if self.get_command(ctx, cmd_name) is not None:
                # It's a real command — let Click handle normally
                return super().parse_args(ctx, args)
            # Not a command — stash as prompt in ctx.obj, pass only opts to Click
            ctx.ensure_object(dict)
            ctx.obj["_prompt_args"] = rest
            return super().parse_args(ctx, opts)

        return super().parse_args(ctx, args)

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

        from archie.config import resolve_project

        args = ctx.args if ctx.args else default_args
        sys.exit(run_container([command, *args], tool_name=name, project=resolve_project()))

    tool_cmd.help = f"Run {command} in the sandbox."
    return tool_cmd


def _print_not_ready(s) -> None:
    if not s.docker_installed:
        print_error(f"[{C_KEY}]Docker[/] is not installed")
    elif not s.docker_running:
        print_error(f"[{C_KEY}]Docker[/] is not running")


# --- Main command ---


@click.group(
    invoke_without_command=True,
    cls=ArchieCLI,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option("--plain", is_flag=True, help="Disable colours and formatting")
@click.option("--name", default=None, help="Named session (isolated working directory)")
@click.option("--shell", "use_shell", is_flag=True, help="Run bash instead of kiro-cli")
@click.option("--bg", "background", is_flag=True, help="Run in background (not yet implemented)")
@click.pass_context
def main(
    ctx: click.Context, plain: bool, name: str | None, use_shell: bool, background: bool
) -> None:
    """Archie — personal AI platform."""
    if plain:
        from archie.output import console, console_err

        console.no_color = True
        console_err.no_color = True

    if ctx.invoked_subcommand is not None:
        return

    if background:
        if use_shell:
            print_error("Cannot combine --bg and --shell")
            sys.exit(1)

    # Inside sandbox: run kiro-cli directly (no Docker needed)
    if is_sandbox():
        prompt_args = (ctx.obj or {}).get("_prompt_args", [])
        prompt = " ".join(prompt_args) if prompt_args else None
        if not prompt and not sys.stdin.isatty():
            prompt = sys.stdin.read().strip() or None
        command = ["kiro-cli", "chat", "--agent", "archie"]
        if prompt:
            command.append(prompt)
        import subprocess as sp

        sys.exit(sp.run(command).returncode)

    if not is_installed():
        print_error(f"Archie is not installed. Run [{C_CMD}]archie install[/] first.")
        sys.exit(1)
    s = check_status()
    if not s.ready:
        _print_not_ready(s)
        sys.exit(1)

    # Remaining args are the prompt
    prompt_args = (ctx.obj or {}).get("_prompt_args", [])
    prompt = " ".join(prompt_args) if prompt_args else None

    # Read piped input if no prompt and not a TTY
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip() or None

    if background and not prompt:
        print_error("--bg requires a prompt")
        sys.exit(1)

    _run_session(name=name, use_shell=use_shell, prompt=prompt, background=background)


def _run_session(
    *, name: str | None, use_shell: bool, prompt: str | None, background: bool
) -> None:
    """Launch a session (named or unnamed, project or general, shell or kiro-cli)."""
    from archie.config import resolve_project
    from archie.docker import _has_cloneable_repos

    project = resolve_project()

    # Build the command
    if use_shell:
        if prompt:
            command = ["/bin/bash", "-c", prompt]
        else:
            command = ["/bin/bash"]
    else:
        command = ["kiro-cli", "chat", "--agent", "archie"]
        if background or not sys.stdout.isatty():
            command.append("--no-interactive")
        if prompt:
            command.append(prompt)

    # Named session
    if name:
        proj, session_name, existing_dir = resolve_session(name, project)

        # Check if container already running
        cn = container_name_for_session(proj, session_name)
        if docker_output("ps", "-q", "--filter", f"name=^/{cn}$"):
            print_error(f"Session [bright_blue]{session_name}[/bright_blue] is already running")
            sys.exit(1)

        # Create or reuse session directory
        session_dir = existing_dir
        if not session_dir:
            if proj and proj.exists() and _has_cloneable_repos(proj):
                print_info(f"Creating session [bright_blue]{session_name}[/bright_blue]...")
                session_dir = create_session_clone(proj, session_name)
            elif proj and proj.exists():
                # Project exists but no git — just create empty session dir
                session_dir = SESSIONS_DIR / proj.name / session_name
                session_dir.mkdir(parents=True, exist_ok=True)
            else:
                # Project doesn't exist or not in a project dir
                if proj and not proj.exists():
                    print_error(f"Project directory not found: {proj}")
                    sys.exit(1)
                proj = None
                session_dir = SESSIONS_DIR / "general" / session_name
                session_dir.mkdir(parents=True, exist_ok=True)
        else:
            status = session_status(session_dir)
            print_info(f"Resuming session [bright_blue]{session_name}[/bright_blue] ({status})")

        sys.exit(
            run_container(
                command,
                project=proj,
                session_name=session_name,
                session_dir=session_dir,
                background=background,
            )
        )

    # Unnamed session
    if project:
        # Unnamed project — mount project dir directly
        sys.exit(run_container(command, project=project, background=background))
    else:
        # Unnamed general — transient working dir
        suffix = hash_suffix()
        session_dir = SESSIONS_DIR / "general" / suffix
        session_dir.mkdir(parents=True, exist_ok=True)
        try:
            returncode = run_container(command, session_dir=session_dir, background=background)
        finally:
            # Clean up transient dir
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
        sys.exit(returncode)


# --- Subcommands ---


@main.command(name="install")
def install_cmd() -> None:
    """Install persona and default config to ~/.archie/."""
    print_info("Installing Archie...")
    install()
    print_success(f"Installed to [{C_VAL}]~/.archie/[/]")


@main.command(name="ls")
def ls_cmd() -> None:
    """List sessions and their statuses."""
    if is_sandbox():
        print_error("Not available inside the sandbox")
        sys.exit(1)
    all_sessions = list_sessions()
    if not all_sessions:
        print_info("No sessions")
        return

    data_table(
        *[
            (
                s["project"],
                s["session"],
                f"[{C_OK}]● running[/]" if s["active"] else f"[{C_MUTED}]○ inactive[/]",
                s["status"] or "—",
            )
            for s in all_sessions
        ],
        styles=[C_KEY, C_VAL, "", C_MUTED],
    )


@main.command(name="rm")
@click.argument("name", required=False)
@click.option("--all", "remove_all", is_flag=True, help="Remove all inactive sessions")
@click.option("-f", "force", is_flag=True, help="Force removal without prompts")
def rm_cmd(name: str | None, remove_all: bool, force: bool) -> None:
    """Remove session working directories."""
    if is_sandbox():
        print_error("Not available inside the sandbox")
        sys.exit(1)
    if name:
        _remove_one_session(name, force)
    elif remove_all:
        _remove_all_sessions(force)
    else:
        _remove_clean_sessions()


def _remove_one_session(name: str, force: bool) -> None:
    """Remove a specific named session."""
    from archie.config import resolve_project

    project = resolve_project()
    proj, session_name, session_dir = resolve_session(name, project)

    if not session_dir or not session_dir.exists():
        print_info(f"No session '{name}' found")
        return

    # Check for running container
    cn = container_name_for_session(proj, session_name)
    if docker_output("ps", "-q", "--filter", f"name=^/{cn}$"):
        print_error(f"Cannot remove — session [bright_blue]{session_name}[/bright_blue] is running")
        sys.exit(1)

    # Check dirty state
    status = session_status(session_dir)
    if status != "clean" and status != "empty" and not force:
        if not sys.stdin.isatty():
            print_error(f"Session has {status}. Use -f to force removal.")
            sys.exit(1)
        try:
            reply = input(f"  Session '{session_name}' has {status}. Remove? [y/N] ")
        except (EOFError, KeyboardInterrupt):
            sys.exit(1)
        if reply.strip().lower() != "y":
            return

    _safe_remove_session(session_dir)
    print_success(f"Removed session [bright_blue]{session_name}[/bright_blue]")


def _remove_all_sessions(force: bool) -> None:
    """Remove all inactive sessions, prompting for dirty ones."""
    all_sessions = list_sessions()
    inactive = [s for s in all_sessions if not s["active"] and s["session"] != "(unnamed)"]

    if not inactive:
        print_info("No inactive sessions to remove")
        return

    for s in inactive:
        proj_name = s["project"]
        sess_name = s["session"]
        session_dir = SESSIONS_DIR / proj_name / sess_name

        if not session_dir.exists():
            continue

        status = s["status"]
        if status not in ("clean", "empty", "") and not force:
            if not sys.stdin.isatty():
                continue
            try:
                reply = input(f"  {proj_name}/{sess_name} has {status}. Remove? [y/N] ")
            except (EOFError, KeyboardInterrupt):
                return
            if reply.strip().lower() != "y":
                continue

        _safe_remove_session(session_dir)
        print_success(f"Removed [bright_blue]{proj_name}/{sess_name}[/bright_blue]")


def _remove_clean_sessions() -> None:
    """Remove all inactive sessions that are clean."""
    all_sessions = list_sessions()
    inactive_clean = [
        s
        for s in all_sessions
        if not s["active"] and s["session"] != "(unnamed)" and s["status"] in ("clean", "empty", "")
    ]

    if not inactive_clean:
        print_info("No clean inactive sessions to remove")
        return

    for s in inactive_clean:
        session_dir = SESSIONS_DIR / s["project"] / s["session"]
        if session_dir.exists():
            _safe_remove_session(session_dir)
            print_success(f"Removed [bright_blue]{s['project']}/{s['session']}[/bright_blue]")


def _sandbox_status(as_json: bool) -> None:
    """Show reduced status inside the sandbox (no Docker info)."""
    import json as json_mod

    from archie.auth.inject import CREDENTIAL_ENV_MAP
    from archie.config import CONFIG_PATH, resolve_brain_dir

    config = load_config()
    brain_dir = resolve_brain_dir()

    # Check credentials via env vars (injected by host)
    creds_data = {}
    for (service, field_name), env_name in CREDENTIAL_ENV_MAP.items():
        key = f"{service}.{field_name}"
        configured = bool(os.environ.get(env_name))
        creds_data[key] = {"env": env_name, "configured": configured}

    if as_json:
        data = {
            "sandbox": True,
            "brain_dir": str(brain_dir),
            "brain_exists": brain_dir.exists(),
            "project_dir": config.get("project_dir", "~/dev"),
            "credentials": creds_data,
            "config_path": str(CONFIG_PATH),
        }
        click.echo(json_mod.dumps(data, indent=2))
        return

    display_header()

    section("Environment")
    status_table(
        (True, "Sandbox", "running"),
        (brain_dir.exists(), "Brain", str(brain_dir)),
    )

    if creds_data:
        section("Credentials")
        rows = []
        for key, info in creds_data.items():
            rows.append(
                (
                    info["configured"],
                    f"{info['env']} ← {key}",
                    "" if info["configured"] else "not set",
                )
            )
        status_table(*rows)

    section("Config")
    empty_state(str(CONFIG_PATH))


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool) -> None:
    """Check environment readiness."""
    import json as json_mod
    from datetime import datetime

    from archie.auth.inject import CREDENTIAL_ENV_MAP, _load_credentials
    from archie.config import CONFIG_PATH

    # Reduced status view inside sandbox
    if is_sandbox():
        _sandbox_status(as_json)
        return

    s = check_status()
    config = load_config()

    img = image_info()
    containers = list_containers()

    creds = _load_credentials()
    creds_data = {}
    for (service, field), env_name in CREDENTIAL_ENV_MAP.items():
        value = (creds.get(service) or {}).get(field)
        configured = value is not None
        expires_at = (creds.get(service) or {}).get("expires_at") if configured else None
        key = f"{service}.{field}"
        creds_data[key] = {
            "env": env_name,
            "configured": configured,
            **({"expires_at": str(expires_at)} if expires_at else {}),
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

    if creds_data:
        section("Credentials")
        rows = []
        for key, info in creds_data.items():
            detail = ""
            if info.get("expires_at"):
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
            rows.append((info["configured"], f"{info['env']} ← {key}", detail))
        status_table(*rows)

    section("Mounts")
    status_table(
        *[(m["exists"], m["path"], "missing" if not m["exists"] else "") for m in mounts_data]
    )

    from archie.config import resolve_brain_dir

    brain_dir = resolve_brain_dir()
    section("Brain")
    if brain_dir.exists():
        contexts = sorted(
            d.name for d in brain_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
        status_table(
            (True, "Directory", str(brain_dir)),
            *[(True, ctx, "") for ctx in contexts]
            if contexts
            else [(False, "No contexts", "run 'archie init'")],
        )
    else:
        status_table((False, "Directory", f"{brain_dir} (not found)"))

    # Sessions
    all_sessions = list_sessions()
    if all_sessions:
        section("Sessions")
        data_table(
            *[
                (
                    s["project"],
                    s["session"],
                    f"[{C_OK}]● running[/]" if s["active"] else f"[{C_MUTED}]○ inactive[/]",
                    s["status"] or "—",
                )
                for s in all_sessions
            ],
            styles=[C_KEY, C_VAL, "", C_MUTED],
        )

    section("Config")
    empty_state(str(CONFIG_PATH))


@main.command()
@click.option("--quick", is_flag=True, help="Use Docker cache for faster builds.")
def build(quick: bool) -> None:
    """Build the sandbox Docker image."""
    if is_sandbox():
        print_error("Not available inside the sandbox")
        sys.exit(1)
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


# --- Agent-facing subcommands (JSON output) ---

from archie.auth.cli import auth  # noqa: E402
from archie.brain.cli import brain  # noqa: E402
from archie.digest.cli import digest  # noqa: E402
from archie.google.cli import google  # noqa: E402
from archie.init import init as init_cmd  # noqa: E402
from archie.jira.cli import jira  # noqa: E402
from archie.linear.cli import linear  # noqa: E402
from archie.notion.cli import notion  # noqa: E402
from archie.project import project  # noqa: E402
from archie.slack.cli import slack  # noqa: E402

main.add_command(auth)
main.add_command(brain)
main.add_command(digest)
main.add_command(google)
main.add_command(init_cmd, name="init")
main.add_command(jira)
main.add_command(linear)
main.add_command(notion)
main.add_command(project)
main.add_command(slack)
