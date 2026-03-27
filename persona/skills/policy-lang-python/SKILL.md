---
name: policy-lang-python
description: >
  Standards for writing quality Python code with modern tooling. Use when working with
  .py files, Python projects, or when Python is mentioned. Includes CLI tool standards
  for building command-line tools with Click, Rich, and uv. Use when creating CLI tools,
  adding commands, or working with terminal output formatting.
---

# Python Coding Standards

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in RFC 2119.

## Scope

This document defines toolchain preferences, code style, naming conventions, and language idioms for Python development.

Organisation-specific requirements (deployment patterns, security baselines, etc.) are defined in steering files loaded by the agent.

## Toolchain

### Package Management

**Use `uv` for dependency management and virtual environments**

- MUST define dependencies in `pyproject.toml`
- SHOULD separate development dependencies using `uv add --dev`

### Code Quality

**Formatting:**
- MUST use Black for code formatting if no existing formatter is present
- SHOULD run Black after making changes

**Linting:**
- MUST use Ruff for linting if no existing linter is present
- SHOULD run Ruff after making changes

**Configuration:**
- SHOULD configure tools in `pyproject.toml` when possible
- MUST ensure Black and Ruff configurations are compatible

### Testing

**Use pytest for testing if no existing test framework is present**

- SHOULD use pytest fixtures for test setup
- MUST organize tests in a `tests/` directory
- SHOULD aim for meaningful test names that describe behavior

## Code Style

### Style and Formatting

**PEP 8 compliance:**
- MUST follow PEP 8 style guidelines
- MUST use 4 spaces for indentation, never tabs
- SHOULD limit lines to 88 characters (Black formatter standard)
- MUST surround top-level functions and classes with two blank lines
- SHOULD use blank lines to separate logical sections
- MUST NOT include trailing whitespace
- MUST end files with a single newline

**Documentation:**
- MUST follow Google-style docstrings
- MUST NOT include type information in docstrings (use type hints instead)

### Naming Conventions

**Modules:** short, lowercase
- Examples: `users.py`, `db.py`, `api.py`

**Packages:** short, lowercase, no underscores
- Examples: `mypackage`, `utils`, `core`

**Classes:** PascalCase, nouns
- Examples: `UserProfile`, `DatabaseConnection`, `APIClient`

**Functions:** snake_case, verbs
- Examples: `get_user()`, `connect_to_db()`, `process_data()`

**Variables:** snake_case, nouns
- Examples: `user_list`, `connection_pool`, `max_retries`

**Constants:** UPPER_SNAKE_CASE
- Examples: `MAX_CONNECTIONS`, `DEFAULT_TIMEOUT`, `API_VERSION`

**Protected members:** single underscore prefix
- Examples: `_internal_method()`, `_cache`

**Private members:** double underscore prefix
- Examples: `__very_private()`, `__state`

## Type Hints

**MUST use type hints for all function signatures and variables**

```python
def get_user(user_id: str) -> User | None:
    """Retrieve user by ID."""
    return users.get(user_id)

def process_items(items: list[Item], max_count: int = 100) -> dict[str, Any]:
    """Process items and return summary."""
    results: dict[str, Any] = {}
    # ... processing logic
    return results
```

## Language Features

**SHOULD use idiomatic Python constructs:**

**List/dict comprehensions:**
```python
# Use comprehensions for simple transformations
user_ids = [u.id for u in users if u.is_active]
user_map = {u.id: u.name for u in users}
```

**enumerate():**
```python
# Use enumerate() instead of manual indexing
for idx, item in enumerate(items):
    print(f"{idx}: {item}")
```

**Context managers:**
```python
# Use with statements for resource management
with open("file.txt") as f:
    data = f.read()
```

**Unpacking:**
```python
# Use unpacking for clarity
first, *rest = items
x, y = coordinates
```

**dict.get() with defaults:**
```python
# Use dict.get() instead of checking key existence
value = config.get("timeout", 30)
```

## Error Handling

**SHOULD use specific exception types, not bare `except:`**

```python
# Good - specific exception handling
try:
    result = process_data(input)
except ValueError as e:
    logger.error(f"Invalid input: {e}")
except KeyError as e:
    logger.error(f"Missing key: {e}")

# Avoid - bare except
try:
    result = process_data(input)
except:  # Too broad
    pass
```

## Function Arguments

**SHOULD use `*args` and `**kwargs` judiciously, with clear documentation**

```python
def create_user(
    username: str,
    email: str,
    *,  # Force keyword-only arguments after this
    is_active: bool = True,
    **metadata: Any
) -> User:
    """
    Create a new user.
    
    Args:
        username: User's username
        email: User's email address
        is_active: Whether user account is active
        **metadata: Additional user metadata
    """
    pass
```

## Classes

**MUST define `__str__` and `__repr__` methods for custom classes that don't auto-generate them**
(not needed for dataclasses, Pydantic models, or NamedTuples)

```python
class User:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.name} ({self.id})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"User(id={self.id!r}, name={self.name!r})"
```

## Import Organization

**MUST group imports in this order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**MUST separate import groups by a blank line**

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import boto3
import requests
from pydantic import BaseModel

# Local
from myapp.models import User
from myapp.utils import logger
```

**Import preferences:**
- SHOULD use absolute imports over relative imports
- MUST NOT use wildcard imports (`from module import *`)
- SHOULD import modules, not individual functions when importing many items

```python
# Good - import module when using many items
import datetime
now = datetime.datetime.now()
delta = datetime.timedelta(days=1)

# Good - import specific items when using few
from datetime import datetime
now = datetime.now()

# Avoid - wildcard imports
from datetime import *  # Don't do this
```

## CLI Tools

When building command-line tools, see [references/CLI-TOOLS.md](references/CLI-TOOLS.md) for
standards covering project structure, Click patterns, Rich output, and configuration.
