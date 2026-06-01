"""Resolve credentials for container injection."""

from datetime import UTC, datetime

import yaml

from archie.config import CREDENTIALS_PATH

# Hardcoded mapping: (service, field) → env var name
CREDENTIAL_ENV_MAP = {
    ("github", "token"): "GH_TOKEN",
    ("notion", "access_token"): "NOTION_TOKEN",
    ("linear", "token"): "LINEAR_TOKEN",
    ("slack", "webhook_url"): "SLACK_WEBHOOK_URL",
    ("slack", "client_id"): "SLACK_CLIENT_ID",
    ("slack", "client_secret"): "SLACK_CLIENT_SECRET",
    ("jira", "email"): "JIRA_EMAIL",
    ("jira", "token"): "JIRA_TOKEN",
    ("jira", "cloud_id"): "JIRA_CLOUD_ID",
    ("google", "client_id"): "GOOGLE_CLIENT_ID",
    ("google", "client_secret"): "GOOGLE_CLIENT_SECRET",
    ("aws", "access_key_id"): "AWS_ACCESS_KEY_ID",
    ("aws", "secret_access_key"): "AWS_SECRET_ACCESS_KEY",
    ("aws", "session_token"): "AWS_SESSION_TOKEN",
    ("scalr", "token"): "SCALR_TOKEN",
    ("scalr", "hostname"): "SCALR_HOSTNAME",
}


def _load_credentials() -> dict:
    """Load credentials from ~/.archie/credentials.yaml."""
    if not CREDENTIALS_PATH.exists():
        return {}
    try:
        with CREDENTIALS_PATH.open() as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return {}


def _is_expired(service: str, creds: dict) -> bool:
    """Check if a service's credentials have expired."""
    expires_at = (creds.get(service) or {}).get("expires_at")
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(str(expires_at))
        return datetime.now(expiry.tzinfo) > expiry
    except (ValueError, TypeError):
        return False


def _try_refresh(service: str) -> bool:
    """Attempt to refresh expired OAuth tokens."""
    try:
        from archie.config import load_config

        config = load_config()
        auth_config = config.get("auth", {}).get(service, {})
        token_endpoint = auth_config.get("token_endpoint")
        if not token_endpoint:
            return False

        creds = _load_credentials()
        service_creds = creds.get(service) or {}
        refresh_token = service_creds.get("refresh_token")
        client_id = service_creds.get("client_id") or auth_config.get("client_id")
        client_secret = service_creds.get("client_secret") or auth_config.get("client_secret")

        if not all([token_endpoint, client_id, refresh_token]):
            return False

        import httpx

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
        if client_secret:
            data["client_secret"] = client_secret

        resp = httpx.post(
            token_endpoint,
            data=data,
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

        CREDENTIALS_PATH.write_text(yaml.dump(creds, default_flow_style=False, sort_keys=False))
        os.chmod(str(CREDENTIALS_PATH), stat.S_IRUSR | stat.S_IWUSR)
        return True
    except Exception:
        return False


def resolve_credentials() -> dict[str, str]:
    """Resolve credentials to env var name → value pairs.

    Reads ~/.archie/credentials.yaml and maps via CREDENTIAL_ENV_MAP.
    Auto-refreshes expired OAuth tokens.
    """
    services_refreshed: set[str] = set()
    env = {}
    creds = _load_credentials()

    for (service, field), env_name in CREDENTIAL_ENV_MAP.items():
        # Auto-refresh expired OAuth tokens (once per service)
        if service not in services_refreshed:
            services_refreshed.add(service)
            if _is_expired(service, creds):
                if _try_refresh(service):
                    from archie.output import print_info

                    print_info(f"Refreshed expired tokens for {service}")
                    creds = _load_credentials()
                else:
                    from archie.output import print_error

                    print_error(f"Failed to refresh expired tokens for {service}")

        value = (creds.get(service) or {}).get(field)
        if value is not None:
            env[env_name] = str(value)

    return env
