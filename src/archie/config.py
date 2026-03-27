"""Configuration loading."""

import shutil
import subprocess
from dataclasses import dataclass, field
from importlib.resources import as_file, files
from pathlib import Path

import yaml

ARCHIE_HOME = Path.home() / ".archie"
CONFIG_PATH = ARCHIE_HOME / "config.yaml"
PERSONA_PATH = ARCHIE_HOME / "persona"

DEFAULT_CONFIG = {
    "project_dir": "~/dev",
    "theme": "blue",
    "env": {
        "TERM": "$TERM",
        "COLORTERM": "$COLORTERM",
        "EDITOR": "$EDITOR",
    },
    "tools": {
        "kiro": {
            "command": "kiro-cli",
            "args": ["chat", "--agent", "archie"],
        },
        "toad": {
            "command": "toad",
        },
    },
    "auth": {
        "github": {
            "type": "static",
            "fields": ["token"],
        },
        "notion": {
            "type": "oauth",
        },
        "aws": {
            "type": "static",
            "fields": ["access_key_id", "secret_access_key", "session_token"],
        },
    },
    "credentials": {
        "GH_TOKEN": "github.token",
        "NOTION_TOKEN": "notion.access_token",
        "AWS_ACCESS_KEY_ID": "aws.access_key_id",
        "AWS_SECRET_ACCESS_KEY": "aws.secret_access_key",
        "AWS_SESSION_TOKEN": "aws.session_token",
    },
    "mounts": [
        ["~/.archie/persona/agents", "~/.kiro/agents"],
        ["~/.archie/persona/skills", "~/.kiro/skills"],
        ["~/.archie/persona/prompts", "~/.kiro/prompts"],
        ["~/.archie/persona/guidance", "~/.kiro/steering"],
        ["~/Library/Application Support/kiro-cli", "~/.local/share/kiro-cli"],
        "~/.toad",
        ["~/.gitconfig", "~/.gitconfig:ro"],
        ["~/.ssh", "~/.ssh:ro"],
    ],
}


@dataclass
class StatusCheck:
    """Result of environment status checks."""

    docker_installed: bool = False
    docker_running: bool = False
    project_dir_exists: bool = False
    project_dir: str = ""
    project: str | None = None
    missing_mounts: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        """True if environment is ready to run containers."""
        return self.docker_installed and self.docker_running and self.project_dir_exists


def is_installed() -> bool:
    """Check if archie has been installed."""
    return PERSONA_PATH.exists() and CONFIG_PATH.exists()


def install() -> None:
    """Extract bundled persona to ~/.archie/persona/ and create default config."""
    ARCHIE_HOME.mkdir(parents=True, exist_ok=True)

    # Remove existing persona and extract fresh copy
    if PERSONA_PATH.exists():
        shutil.rmtree(PERSONA_PATH)

    # Try package data first (installed wheel), fall back to source tree (dev)
    try:
        with as_file(files("archie").joinpath("persona")) as src:
            shutil.copytree(str(src), str(PERSONA_PATH))
    except FileNotFoundError:
        src = Path(__file__).resolve().parents[2] / "persona"
        if not src.exists():
            raise FileNotFoundError("Persona not found in package data or source tree") from None
        shutil.copytree(str(src), str(PERSONA_PATH))

    # Template persona files with user info
    _template_persona()

    # Create config if missing
    if not CONFIG_PATH.exists():
        _write_config(DEFAULT_CONFIG)


def load_config() -> dict:
    """Load config from ~/.archie/config.yaml."""
    try:
        with CONFIG_PATH.open() as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        from archie.output import print_error

        print_error(f"Invalid YAML in {CONFIG_PATH}")
        raise SystemExit(1) from None


def check_status() -> StatusCheck:
    """Check environment readiness."""
    status = StatusCheck()
    config = load_config()

    # Docker installed?
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, check=False)
        status.docker_installed = result.returncode == 0
    except FileNotFoundError:
        status.docker_installed = False

    # Docker running?
    if status.docker_installed:
        result = subprocess.run(["docker", "info"], capture_output=True, check=False)
        status.docker_running = result.returncode == 0

    # Project dir exists?
    project_dir = Path(config.get("project_dir", "~/dev")).expanduser().resolve()
    status.project_dir = str(project_dir)
    status.project_dir_exists = project_dir.exists()

    # Current project?
    try:
        cwd = Path.cwd().resolve()
        relative = cwd.relative_to(project_dir)
        status.project = str(project_dir / relative.parts[0])
    except (ValueError, IndexError):
        status.project = None

    # Missing mounts?
    for entry in config.get("mounts", []):
        src = entry if isinstance(entry, str) else entry[0]
        host_path = Path(src).expanduser()
        if not host_path.exists():
            status.missing_mounts.append(src)

    return status


def resolve_env(config: dict) -> dict[str, str]:
    """Resolve environment variables for the container.

    Values starting with $ are resolved from the host environment.
    Other values are passed through as-is.
    Only includes variables that resolve to a non-empty value.
    """
    import os

    env = {}
    for name, value in config.get("env", {}).items():
        if isinstance(value, str) and value.startswith("$"):
            resolved = os.environ.get(value[1:])
            if resolved:
                env[name] = resolved
        else:
            env[name] = str(value)
    return env


def resolve_mounts(config: dict) -> list[tuple[str, str]]:
    """Resolve mount entries to (host_path, container_mount) pairs.

    container_mount may include Docker options like :ro.

    Entries can be:
    - str: auto-mapped from host home to container home
    - list [src, dest]: explicit mapping (dest may include :ro etc.)
    """
    from archie.docker import HOST_USERNAME

    container_home = f"/home/{HOST_USERNAME}"
    host_home = str(Path.home())
    mounts = []

    for entry in config.get("mounts", []):
        if isinstance(entry, str):
            host_path = str(Path(entry).expanduser())
            container_mount = host_path.replace(host_home, container_home)
        else:
            host_path = str(Path(entry[0]).expanduser())
            # Split off any Docker options (e.g. :ro) before path substitution
            dest = entry[1]
            if ":" in dest.lstrip("~"):
                path_part, _, options = dest.rpartition(":")
                container_mount = f"{path_part.replace('~', container_home)}:{options}"
            else:
                container_mount = dest.replace("~", container_home)

        if Path(host_path).exists():
            mounts.append((host_path, container_mount))

    return mounts


def resolve_project() -> Path:
    """Discover the project directory from cwd.

    The project is the first subdirectory under project_dir that is an
    ancestor of (or equal to) the current working directory.

    Raises:
        SystemExit: If cwd is not under project_dir.
    """
    config = load_config()
    project_dir = Path(config.get("project_dir", "~/dev")).expanduser().resolve()
    cwd = Path.cwd().resolve()

    try:
        relative = cwd.relative_to(project_dir)
    except ValueError:
        from archie.output import print_error

        print_error(f"Not inside project directory ({project_dir})")
        raise SystemExit(1) from None

    # First component of the relative path is the project
    return project_dir / relative.parts[0]


def _template_persona() -> None:
    """Replace placeholders in persona files with user info."""
    import getpass

    username = getpass.getuser().split(".")[0].capitalize()
    agent_config = PERSONA_PATH / "agents" / "archie.json"

    if agent_config.exists():
        content = agent_config.read_text()
        content = content.replace("{{USER}}", username)
        agent_config.write_text(content)


def _write_config(config: dict) -> None:
    """Write config with inline list formatting for mount pairs."""

    class InlineListDumper(yaml.SafeDumper):
        pass

    def represent_list(dumper, data):
        if all(isinstance(item, str) for item in data):
            return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
        return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=False)

    InlineListDumper.add_representer(list, represent_list)

    CONFIG_PATH.write_text(yaml.dump(config, Dumper=InlineListDumper, sort_keys=False))
