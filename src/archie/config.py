"""Configuration loading."""

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from importlib.resources import as_file, files
from pathlib import Path

import yaml

ARCHIE_HOME = Path.home() / ".archie"
CONFIG_PATH = ARCHIE_HOME / "config.yaml"
PERSONA_PATH = ARCHIE_HOME / "persona"

# macOS stores kiro data in ~/Library/Application Support/kiro-cli
# Linux stores it in ~/.local/share/kiro-cli (XDG default)
_KIRO_DATA_DIR = (
    "~/Library/Application Support/kiro-cli"
    if sys.platform == "darwin"
    else "~/.local/share/kiro-cli"
)

DEFAULT_CONFIG = {
    "theme": "blue",
    "env": {
        "TERM": "$TERM",
        "COLORTERM": "$COLORTERM",
        "EDITOR": "$EDITOR",
    },
    "credentials": {
        "GH_TOKEN": "ak.github.token",
        "NOTION_TOKEN": "ak.notion.access_token",
        "AWS_ACCESS_KEY_ID": "ak.aws.access_key_id",
        "AWS_SECRET_ACCESS_KEY": "ak.aws.secret_access_key",
        "AWS_SESSION_TOKEN": "ak.aws.session_token",
        "SCALR_TOKEN": "ak.scalr.token",
        "SCALR_HOSTNAME": "ak.scalr.hostname",
        "LINEAR_TOKEN": "ak.linear.token",
        "SLACK_WEBHOOK_URL": "ak.slack.webhook_url",
        "SLACK_CLIENT_ID": "ak.slack.client_id",
        "SLACK_CLIENT_SECRET": "ak.slack.client_secret",
        "JIRA_EMAIL": "ak.jira.email",
        "JIRA_TOKEN": "ak.jira.token",
        "JIRA_CLOUD_ID": "ak.jira.cloud_id",
        "GOOGLE_CLIENT_ID": "ak.google.client_id",
        "GOOGLE_CLIENT_SECRET": "ak.google.client_secret",
    },
    "mounts": [
        ["~/.archie/persona/agents", "~/.kiro/agents"],
        ["~/.archie/persona/skills", "~/.kiro/skills"],
        ["~/.archie/persona/prompts", "~/.kiro/prompts"],
        ["~/.archie/persona/guidance", "~/.kiro/steering"],
        ["~/.archie/persona/hooks", "~/.kiro/hooks"],
        ["~/.agent-kit", "~/.agent-kit:ro"],
        [_KIRO_DATA_DIR, "~/.local/share/kiro-cli"],
        "~/.toad",
        ["~/.archie/aws.config", "~/.aws/config:ro"],
        "~/.gitconfig:ro",
        ["~/.ssh/id_ed25519", "~/.ssh/id_ed25519:ro"],
        ["~/.ssh/id_ed25519.pub", "~/.ssh/id_ed25519.pub:ro"],
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
    credential_issues: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        """True if environment is ready to run containers."""
        return self.docker_installed and self.docker_running


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
    from archie.docker import _read_ak_config

    ak_config = _read_ak_config()
    project_dir = Path(ak_config.get("project_dir", "~/dev")).expanduser().resolve()
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
        if isinstance(entry, str):
            src, _ = _split_mount_options(entry)
        elif isinstance(entry, list) and len(entry) >= 1:
            src = entry[0]
        else:
            continue
        host_path = Path(src).expanduser()
        if not host_path.exists():
            status.missing_mounts.append(src)

    # Credential issues?
    from datetime import datetime

    from archie.auth.inject import _load_ak_credentials

    ak_creds = _load_ak_credentials()
    for service, fields in ak_creds.items():
        if isinstance(fields, dict) and "expires_at" in fields:
            try:
                expiry = datetime.fromisoformat(str(fields["expires_at"]))
                if datetime.now(expiry.tzinfo) > expiry:
                    status.credential_issues.append(f"{service}: expired")
            except (ValueError, TypeError):
                pass

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


def _split_mount_options(path: str) -> tuple[str, str]:
    """Split a path from trailing Docker mount options (e.g. :ro).

    Returns (path, options) where options includes the leading colon or is empty.
    Only splits on the last colon that isn't part of a ~ home prefix.
    """
    stripped = path.lstrip("~")
    if ":" in stripped:
        path_part, _, options = path.rpartition(":")
        return path_part, f":{options}"
    return path, ""


def resolve_mounts(config: dict) -> list[tuple[str, str]]:
    """Resolve mount entries to (host_path, container_mount) pairs.

    container_mount may include Docker options like :ro.

    Entries can be:
    - str: auto-mapped from host home to container home (supports :ro suffix)
    - list [src, dest]: explicit mapping (dest may include :ro etc.)

    Raises SystemExit on malformed entries.
    """
    from archie.docker import HOST_USERNAME
    from archie.output import print_error, print_warning

    container_home = f"/home/{HOST_USERNAME}"
    host_home = str(Path.home())
    mounts = []
    errors = []

    for i, entry in enumerate(config.get("mounts", [])):
        if isinstance(entry, str):
            path_part, options = _split_mount_options(entry)
            host_path = str(Path(path_part).expanduser())
            container_mount = host_path.replace(host_home, container_home) + options
        elif isinstance(entry, list):
            if len(entry) != 2:
                errors.append(f"  mount[{i}]: list must have 2 elements [src, dest], got {entry}")
                continue
            host_path = str(Path(entry[0]).expanduser())
            path_part, options = _split_mount_options(entry[1])
            container_mount = path_part.replace("~", container_home) + options
        else:
            errors.append(
                f"  mount[{i}]: expected string or [src, dest] list, got {type(entry).__name__}"
            )
            continue

        if Path(host_path).exists():
            mounts.append((host_path, container_mount))
        else:
            print_warning(f"Mount skipped — path not found: {host_path}")

    if errors:
        print_error("Invalid mount configuration:\n" + "\n".join(errors))
        raise SystemExit(1)

    return mounts


def resolve_project() -> Path | None:
    """Discover the project directory from cwd.

    The project is the first subdirectory under project_dir that is an
    ancestor of (or equal to) the current working directory.
    Reads project_dir from agent-kit config (~/.agent-kit/config.yaml).

    Returns None if cwd is not inside a project (at project_dir root or outside it).
    """
    from archie.docker import _read_ak_config

    ak_config = _read_ak_config()
    project_dir = Path(ak_config.get("project_dir", "~/dev")).expanduser().resolve()
    cwd = Path.cwd().resolve()

    try:
        relative = cwd.relative_to(project_dir)
    except ValueError:
        return None

    if not relative.parts:
        return None

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
