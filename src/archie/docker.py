"""Docker operations."""

import hashlib
import os
import pwd
import re
import subprocess
import sys
import time
from pathlib import Path

IMAGE_NAME = "archie-sandbox"
CONTAINER_PREFIX = "archie-"

# Host user info
_user_info = pwd.getpwuid(os.getuid())
HOST_USERNAME = _user_info.pw_name
HOST_UID = _user_info.pw_uid

ARCHIE_HOME = Path.home() / ".archie"
SESSIONS_DIR = ARCHIE_HOME / "sessions"

_AK_CONFIG_PATH = Path.home() / ".agent-kit" / "config.yaml"
_DEFAULT_BRAIN_DIR = ARCHIE_HOME / "brain"


# --- Low-level Docker helpers ---


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


# --- Config helpers ---


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


# --- Session helpers ---


def _hash_suffix() -> str:
    """Generate a short hash for unnamed sessions."""
    return hashlib.sha1(str(time.time_ns()).encode()).hexdigest()[:5]


def validate_session_name(name: str) -> None:
    """Reject session names that could escape the session directory."""
    if not name or ".." in name or name.startswith("/") or name.startswith("."):
        from archie.output import print_error

        print_error(f"Invalid session name: {name!r}")
        raise SystemExit(1)


def _has_git(path: Path) -> bool:
    """Check if a directory has a git repo."""
    return (path / ".git").is_dir()


def _get_remote_url(repo: Path) -> str:
    """Get origin remote URL from a local repo."""
    result = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        from archie.output import print_error

        print_error(f"No remote 'origin' in {repo.name}")
        raise SystemExit(1)
    return result.stdout.strip()


def create_session_clone(project: Path, session_name: str) -> Path:
    """Clone project and sub-repos into a session directory."""
    session_dir = SESSIONS_DIR / project.name / session_name

    # Clone top-level repo
    remote = _get_remote_url(project)
    result = subprocess.run(
        ["git", "clone", "--single-branch", remote, str(session_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        from archie.output import print_error

        print_error(f"Failed to clone {project.name}: {result.stderr.strip()}")
        raise SystemExit(1)

    # Clone sub-repos (immediate subdirectories with .git/)
    for child in sorted(project.iterdir()):
        if child.is_dir() and (child / ".git").is_dir():
            sub_remote = _get_remote_url(child)
            sub_dest = session_dir / child.name
            result = subprocess.run(
                ["git", "clone", "--single-branch", sub_remote, str(sub_dest)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                from archie.output import print_error

                print_error(f"Failed to clone {child.name}: {result.stderr.strip()}")
                raise SystemExit(1)

    return session_dir


def resolve_session(name: str, project: Path | None) -> tuple[Path | None, str, Path | None]:
    """Resolve session name to (project_path, session_name, session_dir | None).

    Splits qualified names (project/session) and validates the session name.
    Returns the extracted session_name separately so callers don't pass raw qualified names.
    """
    project_dir_cfg = _read_ak_config().get("project_dir", "~/dev")
    project_dir = Path(project_dir_cfg).expanduser().resolve()

    # Qualified name: "project/session"
    if "/" in name:
        proj_name, session_name = name.split("/", 1)
        validate_session_name(session_name)
        proj_path = project_dir / proj_name
        session_dir = SESSIONS_DIR / proj_name / session_name
        if session_dir.exists():
            return proj_path, session_name, session_dir
        return proj_path, session_name, None

    validate_session_name(name)

    # In a project dir — scope to this project
    if project:
        session_dir = SESSIONS_DIR / project.name / name
        if session_dir.exists():
            return project, name, session_dir
        return project, name, None

    # Outside project — search all sessions
    if SESSIONS_DIR.exists():
        matches = [p for p in SESSIONS_DIR.glob(f"*/{name}") if p.is_dir()]
        if len(matches) == 1:
            proj_name = matches[0].parent.name
            if proj_name == "general":
                return None, name, matches[0]
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


def container_name_for_session(project: Path | None, session_name: str) -> str:
    """Generate container name for a named session."""
    if project:
        return (
            f"{CONTAINER_PREFIX}shell-{_sanitize_name(project.name)}-{_sanitize_name(session_name)}"
        )
    return f"{CONTAINER_PREFIX}general-{_sanitize_name(session_name)}"


def session_status(session_dir: Path) -> str:
    """Get status for a session directory. Aggregates across all git repos."""
    # Find all git repos in the session dir
    repos = []
    if (session_dir / ".git").is_dir():
        repos.append(session_dir)
    for child in sorted(session_dir.iterdir()):
        if child.is_dir() and (child / ".git").is_dir():
            repos.append(child)

    if not repos:
        # Non-git session — report file count and size
        files = list(session_dir.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        if file_count == 0:
            return "empty"
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        return f"{file_count} files, {_human_size(total_size)}"

    total_ahead = 0
    total_modified = 0

    for repo in repos:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "@{upstream}..HEAD"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            total_ahead += len(result.stdout.strip().splitlines())

        result = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            total_modified += len(result.stdout.strip().splitlines())

    parts = []
    if total_ahead:
        parts.append(f"{total_ahead} ahead")
    if total_modified:
        parts.append(f"{total_modified} modified")
    return ", ".join(parts) if parts else "clean"


def _human_size(size: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size}{unit}" if unit == "B" else f"{size:.0f}{unit}"
        size /= 1024
    return f"{size:.0f}TB"


def list_sessions() -> list[dict]:
    """List all sessions — running containers and inactive session dirs."""
    sessions = []
    containers = list_containers()
    running_names = {c["name"] for c in containers}

    # Build lookup of known named sessions from session dirs
    known_named: dict[str, tuple[str, str, Path]] = {}
    if SESSIONS_DIR.exists():
        for parent in sorted(SESSIONS_DIR.iterdir()):
            if not parent.is_dir():
                continue
            for sess_dir in sorted(parent.iterdir()):
                if not sess_dir.is_dir():
                    continue
                proj = None if parent.name == "general" else Path(parent.name)
                cn = container_name_for_session(proj, sess_dir.name)
                known_named[cn] = (parent.name, sess_dir.name, sess_dir)

    # Running containers
    for c in containers:
        name = c["name"]
        if name in known_named:
            proj, sess, sd = known_named[name]
            sessions.append(
                {
                    "project": proj,
                    "session": sess,
                    "active": True,
                    "status": session_status(sd),
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
                sessions.append(
                    {
                        "project": stripped.removeprefix("shell-"),
                        "session": "(unnamed)",
                        "active": True,
                        "status": "",
                    }
                )

    # Inactive named sessions (no running container)
    for cn, (proj, sess, sd) in known_named.items():
        if cn not in running_names:
            sessions.append(
                {
                    "project": proj,
                    "session": sess,
                    "active": False,
                    "status": session_status(sd),
                }
            )

    return sessions


# --- Image operations ---


def image_info() -> dict | None:
    """Get sandbox image info. Returns None if image doesn't exist."""
    output = _docker_output("images", IMAGE_NAME, "--format", "{{.CreatedSince}}\t{{.Size}}")
    if not output:
        return None
    created, size = output.splitlines()[0].split("\t")
    return {"created": created, "size": size}


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


# --- Container execution ---


def run_container(
    command: list[str],
    *,
    tool_name: str = "shell",
    project: Path | None = None,
    session_name: str | None = None,
    session_dir: Path | None = None,
) -> int:
    """Run a command in the sandbox container.

    Args:
        command: Command and arguments to run in the container.
        tool_name: Used for container naming.
        project: Project path (None for general sessions).
        session_name: Named session identifier (None for unnamed).
        session_dir: Working directory to mount (None = mount project directly).
    """
    from archie.auth.inject import resolve_credentials
    from archie.config import load_config, resolve_env, resolve_mounts

    config = load_config()
    mounts = resolve_mounts(config)
    env = resolve_env(config)
    creds = resolve_credentials(config)

    host_home = str(Path.home())
    container_home = f"/home/{HOST_USERNAME}"

    # Determine container name
    if session_name:
        container_name = container_name_for_session(project, session_name)
    elif project:
        suffix = _hash_suffix()
        container_name = (
            f"{CONTAINER_PREFIX}{_sanitize_name(tool_name)}-{_sanitize_name(project.name)}-{suffix}"
        )
    else:
        suffix = _hash_suffix()
        container_name = f"{CONTAINER_PREFIX}general-{suffix}"

    from archie.output import display_header

    display_header(tool_name, project.name if project else "general", container_name)

    args = ["run", "--rm", "--name", container_name]

    # Mount working directory
    if project:
        container_project = str(project).replace(host_home, container_home)
        mount_source = str(session_dir) if session_dir else str(project)
        args.extend(["-v", f"{mount_source}:{container_project}", "-w", container_project])
    elif session_dir:
        container_workspace = f"{container_home}/workspace"
        args.extend(["-v", f"{session_dir}:{container_workspace}", "-w", container_workspace])

    # Mount brain (always read-write)
    brain_dir = _resolve_brain_dir()
    if brain_dir and brain_dir.exists():
        container_brain = str(brain_dir).replace(host_home, container_home)
        args.extend(["-v", f"{brain_dir}:{container_brain}"])

    if sys.stdin.isatty():
        args.append("-it")

    for name, value in {**env, **creds}.items():
        args.extend(["-e", f"{name}={value}"])

    title = f"Archie — {project.name}" if project else "Archie — general"
    args.extend(["-e", f"ARCHIE_TITLE={title}"])

    for host_path, container_mount in mounts:
        args.extend(["-v", f"{host_path}:{container_mount}"])

    args.extend([IMAGE_NAME, *command])

    try:
        return _docker(*args).returncode
    except KeyboardInterrupt:
        return 130
