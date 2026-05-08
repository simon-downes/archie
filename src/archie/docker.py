"""Docker operations."""

import os
import pwd
import re
import subprocess
import sys
from pathlib import Path

IMAGE_NAME = "archie-sandbox"
CONTAINER_PREFIX = "archie-"

# Host user info
_user_info = pwd.getpwuid(os.getuid())
HOST_USERNAME = _user_info.pw_name
HOST_UID = _user_info.pw_uid


def _sanitize_name(name: str) -> str:
    """Sanitize a string for use in Docker container names."""
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", name)


def _docker(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a docker command."""
    return subprocess.run(
        ["docker", *args],
        capture_output=capture,
        text=capture,
        check=False,
    )


def _docker_output(*args: str) -> str:
    """Run a docker command and return stripped stdout."""
    return _docker(*args, capture=True).stdout.strip()


def list_containers() -> list[dict]:
    """List running archie containers."""
    output = _docker_output(
        "ps",
        "--filter",
        f"name={CONTAINER_PREFIX}",
        "--format",
        "{{.Names}}\t{{.Status}}\t{{.Image}}",
    )
    if not output:
        return []

    containers = []
    for line in output.splitlines():
        name, status, image = line.split("\t")
        containers.append({"name": name, "status": status, "image": image})
    return containers


def image_info() -> dict | None:
    """Get sandbox image info. Returns None if image doesn't exist."""
    output = _docker_output("images", IMAGE_NAME, "--format", "{{.CreatedSince}}\t{{.Size}}")
    if not output:
        return None
    created, size = output.splitlines()[0].split("\t")
    return {"created": created, "size": size}


def _target_arch() -> str:
    """Map platform machine to Docker TARGETARCH value."""
    import platform

    machine = platform.machine()
    return {"x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(machine, "amd64")


def build_image(context_path: Path, *, quick: bool = False) -> None:
    """Build the sandbox Docker image."""
    args = ["build"]
    if not quick:
        args.append("--no-cache")
    args.extend(
        [
            "--build-arg",
            f"TARGETARCH={_target_arch()}",
            "--build-arg",
            f"USERNAME={HOST_USERNAME}",
            "--build-arg",
            f"USER_UID={HOST_UID}",
            "-t",
            IMAGE_NAME,
            str(context_path),
        ]
    )
    result = _docker(*args)
    if result.returncode != 0:
        raise RuntimeError(f"Build failed with exit code {result.returncode}")


_AK_CONFIG_PATH = Path.home() / ".agent-kit" / "config.yaml"
_DEFAULT_BRAIN_DIR = Path.home() / ".archie" / "brain"
ARCHIE_HOME = Path.home() / ".archie"


def _read_ak_config() -> dict:
    """Read agent-kit config, returning empty dict if missing."""
    if _AK_CONFIG_PATH.exists():
        try:
            import yaml

            with _AK_CONFIG_PATH.open() as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


def _resolve_brain_dir() -> Path:
    """Read brain dir from agent-kit config, fall back to default."""
    brain = _read_ak_config().get("brain", {})
    brain_dir = brain.get("dir") if isinstance(brain, dict) else None
    if brain_dir:
        return Path(brain_dir).expanduser()
    return _DEFAULT_BRAIN_DIR


def _has_git(project: Path) -> bool:
    """Check if a project directory has a git repo."""
    return (project / ".git").exists()


def create_or_reuse_worktree(project: Path, session_name: str) -> Path:
    """Create a worktree for a named session, or return existing one."""
    worktree_dir = ARCHIE_HOME / "worktrees" / project.name / session_name
    if worktree_dir.exists():
        return worktree_dir

    worktree_dir.parent.mkdir(parents=True, exist_ok=True)
    branch = f"archie/{session_name}"

    # Check if branch already exists
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--verify", branch],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        cmd = ["git", "-C", str(project), "worktree", "add", str(worktree_dir), branch]
    else:
        cmd = ["git", "-C", str(project), "worktree", "add", str(worktree_dir), "-b", branch]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        from archie.output import print_error

        msg = result.stderr.strip() or "unknown error"
        print_error(f"Failed to create worktree: {msg}")
        raise SystemExit(1)

    return worktree_dir


def _validate_session_name(name: str) -> None:
    """Reject session names that could escape the worktree directory."""
    if not name or ".." in name or name.startswith("/") or name.startswith("."):
        from archie.output import print_error

        print_error(f"Invalid session name: {name!r}")
        raise SystemExit(1)


def resolve_session(name: str, project: Path | None) -> tuple[Path | None, str, Path | None]:
    """Resolve session name to (project_path, session_name, worktree_dir | None).

    Splits qualified names (project/session) and validates the session name.
    Returns the extracted session_name separately so callers don't pass raw qualified names.
    """
    project_dir_cfg = _read_ak_config().get("project_dir", "~/dev")
    project_dir = Path(project_dir_cfg).expanduser().resolve()

    # Qualified name: "project/session"
    if "/" in name:
        proj_name, session_name = name.split("/", 1)
        _validate_session_name(session_name)
        proj_path = project_dir / proj_name
        worktree = ARCHIE_HOME / "worktrees" / proj_name / session_name
        if worktree.exists():
            return proj_path, session_name, worktree
        if proj_path.exists() and _has_git(proj_path):
            return proj_path, session_name, None
        return proj_path, session_name, None

    _validate_session_name(name)

    # In a project dir — scope to this project
    if project:
        worktree = ARCHIE_HOME / "worktrees" / project.name / name
        if worktree.exists():
            return project, name, worktree
        return project, name, None

    # Outside project — search all worktrees
    worktrees_root = ARCHIE_HOME / "worktrees"
    if worktrees_root.exists():
        matches = [p for p in worktrees_root.glob(f"*/{name}") if p.is_dir()]
        if len(matches) == 1:
            proj_name = matches[0].parent.name
            return project_dir / proj_name, name, matches[0]
        elif len(matches) > 1:
            projects = [m.parent.name for m in matches]
            from archie.output import print_error

            print_error(
                f"Ambiguous session [bright_blue]{name}[/bright_blue] — exists in: "
                f"{', '.join(projects)}. Use <project>/{name} to disambiguate."
            )
            raise SystemExit(1)

    return None, name, None


def session_container_name(project: Path | None, session_name: str) -> str:
    """Generate container name for a named session."""
    if project:
        return (
            f"{CONTAINER_PREFIX}shell-{_sanitize_name(project.name)}-{_sanitize_name(session_name)}"
        )
    return f"{CONTAINER_PREFIX}general-{_sanitize_name(session_name)}"


def worktree_status(worktree: Path) -> str:
    """Get git status summary for a worktree. Returns e.g. '3 ahead, 2 modified' or 'clean'."""
    parts = []

    # Ahead count
    result = subprocess.run(
        ["git", "-C", str(worktree), "rev-list", "@{upstream}..HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        count = len(result.stdout.strip().splitlines())
        parts.append(f"{count} ahead")

    # Modified files
    result = subprocess.run(
        ["git", "-C", str(worktree), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        count = len(result.stdout.strip().splitlines())
        parts.append(f"{count} modified")

    return ", ".join(parts) if parts else "clean"


def list_sessions() -> list[dict]:
    """List all sessions — running containers and inactive worktrees."""
    sessions = []
    containers = list_containers()
    running_names = {c["name"] for c in containers}

    # Build a set of known named-session container names from worktrees
    worktrees_root = ARCHIE_HOME / "worktrees"
    known_named: dict[str, tuple[str, str, Path]] = {}  # container_name → (project, session, path)
    if worktrees_root.exists():
        for project_dir in sorted(worktrees_root.iterdir()):
            if not project_dir.is_dir():
                continue
            for wt in sorted(project_dir.iterdir()):
                if not wt.is_dir():
                    continue
                cn = session_container_name(project_dir, wt.name)
                known_named[cn] = (project_dir.name, wt.name, wt)

    # Running containers
    for c in containers:
        name = c["name"]
        if name in known_named:
            proj, sess, wt = known_named[name]
            sessions.append(
                {
                    "project": proj,
                    "session": sess,
                    "active": True,
                    "status": worktree_status(wt),
                }
            )
        else:
            stripped = name.removeprefix(CONTAINER_PREFIX)
            if stripped.startswith("general-"):
                sessions.append(
                    {
                        "project": "general",
                        "session": stripped.removeprefix("general-"),
                        "active": True,
                        "status": "",
                    }
                )
            else:
                # Unnamed project session
                sessions.append(
                    {
                        "project": stripped.removeprefix("shell-"),
                        "session": "(unnamed)",
                        "active": True,
                        "status": "",
                    }
                )

    # Inactive worktrees (no running container)
    for cn, (proj, sess, wt) in known_named.items():
        if cn not in running_names:
            sessions.append(
                {
                    "project": proj,
                    "session": sess,
                    "active": False,
                    "status": worktree_status(wt),
                }
            )

    return sessions


def run_container(
    command: list[str],
    tool_name: str = "shell",
    session: str | None = None,
    worktree: Path | None = None,
    project_override: Path | None = None,
) -> int:
    """Run a command in the sandbox container.

    Args:
        command: Command and arguments to run in the container.
        tool_name: Used for container naming (archie-<tool>-<project>).
        session: Optional session name (named sessions use session_container_name).
        worktree: Optional worktree path to mount instead of the project directory.
        project_override: Explicit project path (used by session command for cross-project).
    """
    from archie.auth.inject import resolve_credentials
    from archie.config import load_config, resolve_env, resolve_mounts, resolve_project

    config = load_config()
    project = project_override or resolve_project()
    mounts = resolve_mounts(config)
    env = resolve_env(config)
    creds = resolve_credentials(config)

    host_home = str(Path.home())
    container_home = f"/home/{HOST_USERNAME}"

    if project:
        # Project session
        container_project = str(project).replace(host_home, container_home)
        if session:
            container_name = session_container_name(project, session)
        else:
            container_name = (
                f"{CONTAINER_PREFIX}{_sanitize_name(tool_name)}-{_sanitize_name(project.name)}"
            )
    else:
        # General session
        if session:
            container_name = session_container_name(None, session)
        else:
            import hashlib
            import time

            suffix = hashlib.sha1(str(time.time_ns()).encode()).hexdigest()[:5]
            container_name = f"{CONTAINER_PREFIX}general-{suffix}"

    # Check for existing container (skip for named sessions — caller already checked)
    if not session and (project is not None):
        if _docker_output("ps", "-q", "--filter", f"name=^/{container_name}$"):
            from archie.output import print_error

            print_error(f"Session [bright_blue]{container_name}[/bright_blue] already running")
            if sys.stdin.isatty():
                try:
                    reply = input("  Start a general session instead? [y/N] ")
                except (EOFError, KeyboardInterrupt):
                    return 1
                if reply.strip().lower() != "y":
                    return 1
                # Switch to general session
                import hashlib
                import time

                project = None
                suffix = hashlib.sha1(str(time.time_ns()).encode()).hexdigest()[:5]
                container_name = f"{CONTAINER_PREFIX}general-{suffix}"
            else:
                return 1

    from archie.output import display_header

    display_header(tool_name, project.name if project else "general", container_name)

    args = [
        "run",
        "--rm",
        "--name",
        container_name,
    ]

    if project:
        container_project = str(project).replace(host_home, container_home)
        if worktree:
            # Named session with worktree — mount worktree as project dir
            args.extend(["-v", f"{worktree}:{container_project}", "-w", container_project])
            # Mount main .git at its host path so worktree's gitdir: resolves
            host_git_dir = str(project / ".git")
            args.extend(["-v", f"{host_git_dir}:{host_git_dir}"])
        else:
            args.extend(["-v", f"{project}:{container_project}", "-w", container_project])

    # Mount brain if it exists (always read-write)
    brain_dir = _resolve_brain_dir()
    if brain_dir and brain_dir.exists():
        container_brain = str(brain_dir).replace(host_home, container_home)
        args.extend(["-v", f"{brain_dir}:{container_brain}"])

    if sys.stdin.isatty():
        args.append("-it")

    for name, value in {**env, **creds}.items():
        args.extend(["-e", f"{name}={value}"])

    # Terminal title — set inside container to override any shell/Docker defaults
    title = f"Archie — {project.name}" if project else "Archie — general"
    args.extend(["-e", f"ARCHIE_TITLE={title}"])

    for host_path, container_mount in mounts:
        args.extend(["-v", f"{host_path}:{container_mount}"])

    args.extend([IMAGE_NAME, *command])

    try:
        return _docker(*args).returncode
    except KeyboardInterrupt:
        return 130
