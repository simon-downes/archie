"""Shared error handling for archie CLI commands."""

import functools
import json
import sys
from typing import Any

import httpx


class ArchieError(Exception):
    """Base error. Exit code 1."""


class AuthError(ArchieError):
    """Authentication/credential errors. Exit code 2."""


class ConfigError(ArchieError):
    """Configuration errors."""


class ScopeError(ArchieError):
    """Resource outside configured access scope."""


def output(data: Any) -> None:
    """Write JSON to stdout."""
    print(json.dumps(data, indent=2))


def handle_errors(fn):
    """Decorator that catches known exceptions and exits cleanly.

    Maps exception types to exit codes:
    - AuthError → exit 2
    - ArchieError (and subclasses) → exit 1
    - httpx.HTTPStatusError 401/403 → exit 2
    - httpx.HTTPStatusError 429 → exit 1 with rate limit message
    - httpx.HTTPStatusError other → exit 1
    - ExceptionGroup → unwrap and re-handle the first cause
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ExceptionGroup as eg:
            cause = eg
            while isinstance(cause, ExceptionGroup) and cause.exceptions:
                cause = cause.exceptions[0]
            _handle(cause)
        except (
            AuthError,
            ArchieError,
            httpx.HTTPStatusError,
            ValueError,
            FileNotFoundError,
        ) as e:
            _handle(e)

    return wrapper


def _handle(e: BaseException) -> None:
    """Print error to stderr and exit with appropriate code."""
    if isinstance(e, AuthError):
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if isinstance(e, ArchieError):
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status in (401, 403):
            print("Error: authentication failed (check credentials)", file=sys.stderr)
            sys.exit(2)
        if status == 429:
            retry_after = e.response.headers.get("Retry-After", "unknown")
            body = e.response.text[:500]
            print(
                f"Error: rate limit exceeded — {e} | retry-after: {retry_after}s | body: {body}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Error: HTTP {status}: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    if isinstance(e, (ValueError, FileNotFoundError)):
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
