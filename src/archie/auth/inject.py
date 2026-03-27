"""Resolve credentials from config mappings for container injection."""

from archie.auth import get_field


def resolve_credentials(config: dict) -> dict[str, str]:
    """Resolve credential mappings to env var name → value pairs.

    Reads the 'credentials' section from config, resolves each dotpath
    against the credentials file. Missing credentials are silently skipped.
    """
    env = {}
    for env_name, dotpath in config.get("credentials", {}).items():
        parts = dotpath.split(".", 1)
        if len(parts) != 2:
            continue
        service, field = parts
        value = get_field(service, field)
        if value is not None:
            env[env_name] = value
    return env
