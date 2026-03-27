"""Auth CLI commands."""

import os
import sys

import click

from archie.auth import set_field
from archie.output import print_error, print_success


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
    # Placeholder — implemented in milestone 4
    click.echo("Not yet implemented")
