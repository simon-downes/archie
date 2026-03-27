"""Auth CLI commands."""

import os
import secrets
import sys
from datetime import UTC, datetime

import click

from archie.auth import set_field
from archie.config import load_config
from archie.output import print_error, print_info, print_success


@click.group()
def auth() -> None:
    """Manage credentials for services."""


@auth.command(name="set")
@click.argument("service")
@click.argument("fields", nargs=-1, required=True)
def set_cmd(service: str, fields: tuple[str, ...]) -> None:
    """Store credentials for a service.

    Prompts interactively for each value, or reads from stdin when piped.
    """
    for field in fields:
        if sys.stdin.isatty():
            value = click.prompt(f"{service}.{field}", hide_input=True)
        else:
            value = sys.stdin.readline().strip()
            if not value:
                print_error(f"No value provided for {service}.{field}")
                sys.exit(1)

        set_field(service, field, value)

    print_success(f"Stored {len(fields)} field(s) for {service}")


@auth.command(name="import")
@click.argument("service")
@click.argument("env_vars", nargs=-1, required=True)
def import_cmd(service: str, env_vars: tuple[str, ...]) -> None:
    """Import credentials from environment variables.

    Field names are lowercased env var names.
    """
    missing = [v for v in env_vars if v not in os.environ]
    if missing:
        print_error(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    for var in env_vars:
        field = var.lower()
        # Strip service name prefix if present (e.g. AWS_ACCESS_KEY_ID → access_key_id)
        prefix = f"{service.lower()}_"
        if field.startswith(prefix):
            field = field[len(prefix) :]
        set_field(service, field, os.environ[var])

    print_success(f"Imported {len(env_vars)} field(s) for {service}")


@auth.command(name="status")
def status_cmd() -> None:
    """Show credential status for all configured services."""
    from datetime import datetime

    from rich.console import Console

    from archie.auth import get_field

    console = Console()
    config = load_config()
    auth_services = config.get("auth", {})

    if not auth_services:
        click.echo("No auth services configured")
        return

    for service, svc_config in auth_services.items():
        svc_type = svc_config.get("type", "static")
        fields = svc_config.get("fields", ["access_token"] if svc_type == "oauth" else [])

        # Check if any credentials exist
        has_creds = any(get_field(service, f) is not None for f in fields)

        if has_creds:
            icon = "[green]✓[/]"
        else:
            icon = "[red]✗[/]"

        line = f"  {icon} [bold]{service}[/]  [dim]{svc_type}[/]"

        # Show expiry for OAuth
        if svc_type == "oauth":
            expires_at = get_field(service, "expires_at")
            if expires_at:
                try:
                    expiry = datetime.fromisoformat(expires_at)
                    if datetime.now(expiry.tzinfo) > expiry:
                        line += "  [red]expired[/]"
                    else:
                        line += f"  [dim]expires {expires_at}[/]"
                except (ValueError, TypeError):
                    pass

        console.print(line)


@auth.command(name="login")
@click.argument("service")
def login_cmd(service: str) -> None:
    """Authenticate with an OAuth service via browser."""
    from importlib.resources import as_file, files

    import yaml

    from archie.auth.oauth import (
        CALLBACK_PORT,
        build_auth_url,
        discover_endpoints,
        exchange_code,
        generate_pkce,
        open_browser,
        register_client,
        wait_for_callback,
    )

    config = load_config()
    auth_config = config.get("auth", {}).get(service, {})

    if auth_config.get("type") != "oauth":
        print_error(f"Service {service} is not an OAuth provider")
        sys.exit(1)

    redirect_uri = f"http://localhost:{CALLBACK_PORT}/callback"

    # Discover endpoints if not in config
    if "token_endpoint" not in auth_config:
        server_url = auth_config.get("server_url")
        if not server_url:
            # Try bundled providers
            try:
                providers_pkg = files("archie").joinpath("auth", "providers.yaml")
                with as_file(providers_pkg) as p:
                    providers = yaml.safe_load(p.read_text())
                provider = providers.get("providers", {}).get(service)
                if provider:
                    server_url = provider.get("server_url")
            except Exception:
                pass

        if not server_url:
            print_error(f"No server_url configured for {service}")
            sys.exit(1)

        print_info("Discovering OAuth endpoints...")
        try:
            metadata = discover_endpoints(server_url)
            auth_config["authorization_endpoint"] = metadata["authorization_endpoint"]
            auth_config["token_endpoint"] = metadata["token_endpoint"]
            if "registration_endpoint" in metadata:
                auth_config["registration_endpoint"] = metadata["registration_endpoint"]
        except Exception as e:
            print_error(f"Failed to discover endpoints: {e}")
            sys.exit(1)

    # Register client if needed
    if "client_id" not in auth_config:
        reg_endpoint = auth_config.get("registration_endpoint")
        if not reg_endpoint:
            print_error(f"No client_id or registration_endpoint for {service}")
            sys.exit(1)

        print_info("Registering OAuth client...")
        try:
            client_data = register_client(reg_endpoint, redirect_uri)
            auth_config["client_id"] = client_data["client_id"]
        except Exception as e:
            print_error(f"Client registration failed: {e}")
            sys.exit(1)

    # Write discovered config back
    from archie.config import CONFIG_PATH

    full_config = load_config()
    full_config.setdefault("auth", {})[service] = auth_config
    CONFIG_PATH.write_text(yaml.dump(full_config, default_flow_style=False, sort_keys=False))

    # Run OAuth flow
    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    auth_url = build_auth_url(
        auth_config["authorization_endpoint"],
        auth_config["client_id"],
        redirect_uri,
        state,
        challenge,
    )

    if not open_browser(auth_url):
        click.echo(f"\nOpen this URL in your browser:\n{auth_url}\n")

    print_info("Waiting for authentication...")
    code, returned_state, error = wait_for_callback()

    if error:
        print_error(f"Authentication failed: {error}")
        sys.exit(1)

    if not code:
        print_error("Authentication timed out")
        sys.exit(1)

    if returned_state != state:
        print_error("State mismatch — possible CSRF attack")
        sys.exit(1)

    # Exchange code for tokens
    try:
        tokens = exchange_code(
            auth_config["token_endpoint"],
            auth_config["client_id"],
            code,
            verifier,
            redirect_uri,
        )
    except Exception as e:
        print_error(f"Token exchange failed: {e}")
        sys.exit(1)

    # Store tokens
    set_field(service, "access_token", tokens["access_token"])
    if "refresh_token" in tokens:
        set_field(service, "refresh_token", tokens["refresh_token"])
    if "expires_in" in tokens:
        expires_at = datetime.now(UTC).timestamp() + tokens["expires_in"]
        set_field(service, "expires_at", datetime.fromtimestamp(expires_at, UTC).isoformat())

    print_success(f"Authenticated with {service}")


@auth.command(name="refresh")
@click.argument("service")
def refresh_cmd(service: str) -> None:
    """Refresh OAuth tokens for a service."""
    from archie.auth import get_field
    from archie.auth.oauth import refresh_token

    config = load_config()
    auth_config = config.get("auth", {}).get(service, {})

    if auth_config.get("type") != "oauth":
        print_error(f"Service {service} is not an OAuth provider")
        sys.exit(1)

    token_endpoint = auth_config.get("token_endpoint")
    client_id = auth_config.get("client_id")
    stored_refresh = get_field(service, "refresh_token")

    if not all([token_endpoint, client_id, stored_refresh]):
        print_error(
            f"Missing OAuth config or refresh token for {service}. Run 'archie auth login {service}' first."
        )
        sys.exit(1)

    try:
        tokens = refresh_token(token_endpoint, client_id, stored_refresh)
    except Exception as e:
        print_error(f"Token refresh failed: {e}")
        sys.exit(1)

    set_field(service, "access_token", tokens["access_token"])
    if "refresh_token" in tokens:
        set_field(service, "refresh_token", tokens["refresh_token"])
    if "expires_in" in tokens:
        from datetime import datetime

        expires_at = datetime.now(UTC).timestamp() + tokens["expires_in"]
        set_field(service, "expires_at", datetime.fromtimestamp(expires_at, UTC).isoformat())

    print_success(f"Refreshed tokens for {service}")
