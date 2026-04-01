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


def _get_gh_token() -> str:
    """Read GitHub token from credential store, or return empty string."""
    try:
        from archie.auth import get_field

        return get_field("github", "token") or ""
    except Exception:
        return ""


def build_image(context_path: Path) -> None:
    """Build the sandbox Docker image."""
    import time

    result = _docker(
        "build",
        "--build-arg",
        f"USERNAME={HOST_USERNAME}",
        "--build-arg",
        f"USER_UID={HOST_UID}",
        "--build-arg",
        f"GH_TOKEN={os.environ.get('GH_TOKEN') or _get_gh_token()}",
        "--build-arg",
        f"CACHEBUST_AK={int(time.time())}",
        "-t",
        IMAGE_NAME,
        str(context_path),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Build failed with exit code {result.returncode}")


def run_container(command: list[str], tool_name: str = "shell") -> int:
    """Run a command in the sandbox container.

    Args:
        command: Command and arguments to run in the container.
        tool_name: Used for container naming (archie-<tool>-<project>).
    """
    from archie.auth.inject import resolve_credentials
    from archie.config import load_config, resolve_env, resolve_mounts, resolve_project

    config = load_config()
    project = resolve_project()
    mounts = resolve_mounts(config)
    env = resolve_env(config)
    creds = resolve_credentials(config)

    host_home = str(Path.home())
    container_home = f"/home/{HOST_USERNAME}"
    container_project = str(project).replace(host_home, container_home)
    container_name = f"{CONTAINER_PREFIX}{_sanitize_name(tool_name)}-{_sanitize_name(project.name)}"

    # Check for existing session
    if _docker_output("ps", "-q", "--filter", f"name=^/{container_name}$"):
        from archie.output import print_error

        print_error(f"Session [bright_blue]{container_name}[/bright_blue] already running")
        return 1

    from archie.output import display_header

    display_header(tool_name, project.name, container_name)

    args = [
        "run",
        "--rm",
        "--name",
        container_name,
        "-v",
        f"{project}:{container_project}",
        "-w",
        container_project,
    ]

    if sys.stdin.isatty():
        args.append("-it")

    for name, value in {**env, **creds, "ARCHIE_PROJECT_ROOT": container_project}.items():
        args.extend(["-e", f"{name}={value}"])

    for host_path, container_mount in mounts:
        args.extend(["-v", f"{host_path}:{container_mount}"])

    args.extend([IMAGE_NAME, *command])

    try:
        return _docker(*args).returncode
    except KeyboardInterrupt:
        return 130
