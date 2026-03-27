"""Resolve credentials from config mappings for container injection."""

from datetime import UTC, datetime

from archie.auth import get_field
from archie.output import print_error


def _try_refresh(service: str, config: dict) -> bool:
    """Attempt to refresh OAuth tokens for a service. Returns True on success."""
    auth_config = config.get("auth", {}).get(service, {})
    token_endpoint = auth_config.get("token_endpoint")
    client_id = auth_config.get("client_id")
    refresh = get_field(service, "refresh_token")

    if not all([token_endpoint, client_id, refresh]):
        return False

    try:
        from archie.auth import set_fields
        from archie.auth.oauth import refresh_token

        tokens = refresh_token(token_endpoint, client_id, refresh)
        token_data = {"access_token": tokens["access_token"]}
        if "refresh_token" in tokens:
            token_data["refresh_token"] = tokens["refresh_token"]
        if "expires_in" in tokens:
            expires_at = datetime.now(UTC).timestamp() + tokens["expires_in"]
            token_data["expires_at"] = datetime.fromtimestamp(expires_at, UTC).isoformat()
        set_fields(service, token_data)
        return True
    except Exception:
        return False


def _is_expired(service: str) -> bool:
    """Check if a service's credentials have expired."""
    expires_at = get_field(service, "expires_at")
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(expires_at)
        return datetime.now(expiry.tzinfo) > expiry
    except (ValueError, TypeError):
        return False


def resolve_credentials(config: dict) -> dict[str, str]:
    """Resolve credential mappings to env var name → value pairs.

    Checks expiry for OAuth credentials and auto-refreshes if needed.
    Missing credentials are silently skipped.
    """
    # Collect which services need resolving
    services_seen: set[str] = set()
    env = {}

    for env_name, dotpath in config.get("credentials", {}).items():
        parts = dotpath.split(".", 1)
        if len(parts) != 2:
            continue
        service, field = parts

        # Auto-refresh expired OAuth tokens (once per service)
        if service not in services_seen:
            services_seen.add(service)
            auth_config = config.get("auth", {}).get(service, {})
            if auth_config.get("type") == "oauth" and _is_expired(service):
                if _try_refresh(service, config):
                    from archie.output import print_info

                    print_info(f"Refreshed expired tokens for {service}")
                else:
                    print_error(f"Failed to refresh expired tokens for {service}")

        value = get_field(service, field)
        if value is not None:
            env[env_name] = value

    return env
