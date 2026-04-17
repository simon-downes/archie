"""Resolve credentials from config mappings for container injection."""

from datetime import UTC, datetime
from pathlib import Path

import yaml

# Agent Kit credential store
_AK_CREDENTIALS_PATH = Path.home() / ".agent-kit" / "credentials.yaml"


def _load_ak_credentials() -> dict:
    """Load agent-kit credentials file."""
    if not _AK_CREDENTIALS_PATH.exists():
        return {}
    try:
        with _AK_CREDENTIALS_PATH.open() as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return {}


def _resolve_ak(dotpath: str) -> str | None:
    """Resolve an ak.service.field dotpath against agent-kit credentials."""
    parts = dotpath.split(".", 2)
    if len(parts) != 3 or parts[0] != "ak":
        return None
    service, field = parts[1], parts[2]
    creds = _load_ak_credentials()
    service_data = creds.get(service)
    if isinstance(service_data, dict):
        value = service_data.get(field)
        return str(value) if value is not None else None
    return None


def _try_refresh_ak(service: str, config: dict) -> bool:
    """Attempt to refresh expired OAuth tokens via agent-kit."""
    try:
        ak_config_path = Path.home() / ".agent-kit" / "config.yaml"
        if not ak_config_path.exists():
            return False
        with ak_config_path.open() as f:
            ak_config = yaml.safe_load(f) or {}
        auth_config = ak_config.get("auth", {}).get(service, {})
        if auth_config.get("type") != "oauth":
            return False

        token_endpoint = auth_config.get("token_endpoint")
        client_id = auth_config.get("client_id")
        creds = _load_ak_credentials()
        refresh = (creds.get(service) or {}).get("refresh_token")

        if not all([token_endpoint, client_id, refresh]):
            return False

        import httpx

        resp = httpx.post(
            token_endpoint,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": client_id,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        tokens = resp.json()

        if service not in creds:
            creds[service] = {}
        creds[service]["access_token"] = tokens["access_token"]
        if "refresh_token" in tokens:
            creds[service]["refresh_token"] = tokens["refresh_token"]
        if "expires_in" in tokens:
            expires_at = datetime.now(UTC).timestamp() + tokens["expires_in"]
            creds[service]["expires_at"] = datetime.fromtimestamp(expires_at, UTC).isoformat()

        import os
        import stat

        _AK_CREDENTIALS_PATH.write_text(yaml.dump(creds, default_flow_style=False, sort_keys=False))
        os.chmod(str(_AK_CREDENTIALS_PATH), stat.S_IRUSR | stat.S_IWUSR)
        return True
    except Exception:
        return False


def _is_expired_ak(service: str) -> bool:
    """Check if an agent-kit service's credentials have expired."""
    creds = _load_ak_credentials()
    expires_at = (creds.get(service) or {}).get("expires_at")
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(str(expires_at))
        return datetime.now(expiry.tzinfo) > expiry
    except (ValueError, TypeError):
        return False


def resolve_credentials(config: dict) -> dict[str, str]:
    """Resolve credential mappings to env var name → value pairs.

    Supports ak.service.field dotpaths for agent-kit credentials.
    Checks expiry for OAuth credentials and auto-refreshes if needed.
    Missing credentials are silently skipped.
    """
    services_refreshed: set[str] = set()
    env = {}

    for env_name, dotpath in config.get("credentials", {}).items():
        if not isinstance(dotpath, str) or not dotpath.startswith("ak."):
            continue

        parts = dotpath.split(".", 2)
        if len(parts) != 3:
            continue
        service = parts[1]

        # Auto-refresh expired OAuth tokens (once per service)
        if service not in services_refreshed:
            services_refreshed.add(service)
            if _is_expired_ak(service):
                if _try_refresh_ak(service, config):
                    from archie.output import print_info

                    print_info(f"Refreshed expired tokens for {service}")
                else:
                    from archie.output import print_error

                    print_error(f"Failed to refresh expired tokens for {service}")

        value = _resolve_ak(dotpath)
        if value is not None:
            env[env_name] = value

    return env
