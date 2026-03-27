# Python CLI Tool Standards

Standards for building CLI tools with Python using Click and Rich.

## Project Structure

MUST use the `src/` layout with hatchling build backend:

```
project/
├── src/<package>/
│   ├── __init__.py      # version string
│   ├── cli.py           # Click entry point
│   ├── output.py        # Rich output primitives (shared Console instances)
│   └── ...
├── tests/
├── pyproject.toml
└── README.md
```

- MUST define the entry point in `pyproject.toml` under `[project.scripts]`
- MUST use `[tool.hatch.build.targets.wheel] packages = ["src/<package>"]`
- SHOULD use `uv` for dependency management and `uv tool install` for global CLI installation
- MUST create shared `Console` instances at module level in `output.py` (one for stdout, one for stderr)
- MUST NOT create Console instances inside functions

### Command Organisation

- MUST use `@click.group()` for tools with multiple commands
- SHOULD use a custom `click.Group` subclass for cross-cutting concerns (e.g. install guards, pre-flight checks)
- MUST register subcommand groups via `main.add_command(group)`
- SHOULD use `context_settings={"ignore_unknown_options": True, "allow_extra_args": True}` for commands that pass arguments through to underlying tools

## CLI Framework

MUST use [Click](https://click.palletsprojects.com/) for CLI tools.
MUST use [Rich](https://rich.readthedocs.io/) for formatted terminal output.

### Global Options

- MUST support `--plain` on the top-level group to disable colours and formatting
- `--plain` SHOULD set `console.no_color = True` on the shared Console instances
- SHOULD support `--json` on individual commands where structured output is useful for scripting or agents

## Configuration

SHOULD use YAML for configuration files.

- SHOULD handle invalid YAML gracefully with a user-friendly error message
- SHOULD create default config with sensible defaults when appropriate
- Missing or incomplete config entries SHOULD fall back to defaults or be silently skipped

## Terminal Output

### Width

SHOULD consider terminal width when formatting output. A fixed width (e.g. 80) on the Console
prevents layout issues on wide terminals, but may not suit all use cases.

### Colour Palette

SHOULD define a fixed semantic colour palette. Colours map to meaning, not aesthetics:

| Role | Purpose | Example |
|------|---------|---------|
| Heading | Section titles | bright_magenta |
| Keyword | Resource names, identifiers | bright_blue |
| Command | Runnable CLI commands | bright_cyan |
| Value | Paths, filenames, data values | #5f87d7 |
| Plain | Default body text | white |
| Muted | Secondary info, types, timestamps | bright_black |
| Chrome | Rules, bullets, separators | dim |
| Status OK | Success icon only | #50c878 |
| Status Warn | Warning icon only | #f0c050 |
| Status Error | Error icon only | bright_red |

- Status colours SHOULD be reserved for icons (✓/!/✗), not used for text or decorative elements
- Theme/brand colours SHOULD be reserved for banners or branding, not operational output
- Message functions SHOULD accept Rich markup so callers control which parts are highlighted

### Output Primitives

SHOULD build a small set of reusable output functions rather than using inline Rich markup
throughout the codebase. See [references/OUTPUT-TEMPLATE.py](references/OUTPUT-TEMPLATE.py)
for a starter implementation.

Core primitives:

| Function | Purpose |
|----------|---------|
| `section(title)` | Rule with heading-coloured title |
| `status_table(*rows)` | Icon + label + detail aligned table |
| `kv_table(*rows)` | Key-value pairs |
| `data_table(*rows, styles)` | Generic aligned table |
| `print_success/error/warning/info(msg)` | Icon + message |
| `bullet_list(items)` | Indented bullets |
| `empty_state(text)` | Muted placeholder for empty results |
| `cmd(text)` | Command-coloured text |
| `human_time(iso)` | Relative timestamps ("in 59m", "2h ago") |

### Timestamps

SHOULD use human-friendly relative times in user-facing output where appropriate.
ISO timestamps MAY be used when precision matters or in `--json` output.
