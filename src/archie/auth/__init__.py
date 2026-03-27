"""Credential store — read/write ~/.archie/credentials.yaml with 0600 permissions."""

import os
import stat

import yaml

from archie.config import ARCHIE_HOME
from archie.output import print_error

CREDENTIALS_PATH = ARCHIE_HOME / "credentials.yaml"


def load_credentials() -> dict:
    """Load credentials file. Warn if permissions too permissive."""
    if not CREDENTIALS_PATH.exists():
        return {}

    mode = stat.S_IMODE(CREDENTIALS_PATH.stat().st_mode)
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        from archie.output import console_err

        console_err.print(
            f"[yellow]Warning:[/yellow] {CREDENTIALS_PATH} has permissions "
            f"{oct(mode)} — expected 0600"
        )

    try:
        with CREDENTIALS_PATH.open() as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        print_error(f"Invalid YAML in {CREDENTIALS_PATH}")
        raise SystemExit(1) from None


def save_credentials(data: dict) -> None:
    """Write credentials file with 0600 permissions."""
    if not CREDENTIALS_PATH.exists():
        fd = os.open(str(CREDENTIALS_PATH), os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)

    CREDENTIALS_PATH.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def get_field(service: str, field: str) -> str | None:
    """Get a credential field. Returns None if not found."""
    creds = load_credentials()
    service_data = creds.get(service)
    if isinstance(service_data, dict):
        value = service_data.get(field)
        return str(value) if value is not None else None
    return None


def set_field(service: str, field: str, value: str) -> None:
    """Set a credential field."""
    creds = load_credentials()
    if service not in creds:
        creds[service] = {}
    creds[service][field] = value
    save_credentials(creds)
