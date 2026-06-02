# Contributing

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker (for sandbox commands)

### Setup

```bash
git clone <repo-url>
cd archie

uv tool install -e .
archie init
archie build
archie status
```

## Repository Layout

```
archie/
├── persona/                     # Who Archie is
│   ├── agents/                  # Agent configs (JSON) — orchestrator + subagents
│   ├── skills/                  # Layered knowledge modules
│   ├── prompts/                 # Utility scripts (build-signals.py)
│   └── guidance/                # Steering files (tools.md, LOCAL.md)
├── src/archie/                  # Unified Python CLI
│   ├── cli.py                   # Click CLI — main group + session commands
│   ├── config.py                # Config loading (~/.archie/config.yaml)
│   ├── docker.py                # Container operations (build, run, list)
│   ├── output.py                # Rich terminal output, themed banner
│   ├── errors.py                # JSON output + error handling for agent commands
│   ├── init.py                  # archie init — one-time setup
│   ├── project.py               # Project detection
│   ├── mcp.py                   # MCP server utilities
│   ├── auth/                    # Credential management + OAuth
│   ├── brain/                   # Brain operations (search, index, git, refs)
│   ├── linear/                  # Linear integration
│   ├── jira/                    # Jira integration
│   ├── notion/                  # Notion integration
│   ├── slack/                   # Slack integration
│   ├── google/                  # Google Workspace integration
│   └── digest/                  # Digest generation
├── sandbox/
│   ├── Dockerfile               # Sandbox image (Debian + dev tools)
│   └── entrypoint.sh            # Container entrypoint (setup + passthrough)
├── tests/
├── docs/
├── plugin.json                  # Skill sharing manifest
└── pyproject.toml
```

## Architecture

### Output Design

Two output modes coexist, determined by audience:

**Human-focused commands** use Rich (colours, tables, banners, progress):

- `archie` (session launch), `archie ls`, `archie rm`
- `archie init`, `archie install`, `archie build`, `archie status`
- `archie auth login`, `archie auth status`

**Agent-focused commands** output JSON to stdout, errors to stderr:

- `archie brain *`, `archie linear *`, `archie jira *`
- `archie notion *`, `archie slack *`, `archie google *`
- `archie project`, `archie digest`

**Rule:** If the primary consumer is the AI agent (called from within a session), output
JSON via `output()`. If the primary consumer is the human at a terminal, use Rich.

### Client Class Pattern

Service integrations follow a consistent structure:

```
src/archie/<service>/
├── __init__.py          # Empty or minimal
├── cli.py              # Click group + subcommands (thin layer)
├── client.py           # Business logic (no CLI, no sys.exit)
└── resolve.py          # Name → ID resolution helpers (optional)
```

**Client classes:**
- Accept credentials in `__init__` (token, API key, etc.)
- Never read config, env vars, or call `sys.exit()`
- Raise exceptions on failure (`AuthError`, `ArchieError`, `httpx.HTTPStatusError`)
- Return plain data (dicts, lists) — no formatting

**CLI modules:**
- Construct client via a `_get_client()` helper that reads credentials
- Call client methods → pass result to `output()`
- Decorated with `@handle_errors` for clean error handling

### Error Handling

```python
from archie.errors import ArchieError, AuthError, handle_errors, output

@linear.command()
@handle_errors
def issues() -> None:
    """List issues."""
    client = _get_client()
    output(client.get_issues(filters))
```

Exception hierarchy:
- `ArchieError` — base error (exit 1)
- `AuthError(ArchieError)` — credential problems (exit 2)
- `ConfigError(ArchieError)` — configuration problems (exit 1)
- `ScopeError(ArchieError)` — resource outside access scope (exit 1)

The `@handle_errors` decorator catches these plus `httpx.HTTPStatusError` and exits
cleanly with an error message to stderr.

### Credential Flow

Credentials are stored at `~/.archie/credentials.yaml` (0600 permissions). At container
launch, `inject.py` maps credentials to environment variables via a hardcoded
`CREDENTIAL_ENV_MAP` and injects them as `-e` flags. Inside the container, client code
reads from the credential store first (`~/.archie/credentials.yaml` is mounted read-write),
falling back to environment variables. The env var injection ensures credentials are
available even if the credential store read fails.

### Container Workflow

The sandbox mounts:
- The archie repo at `/opt/archie` (read-write)
- `~/.archie/` (read-write — config, credentials, service caches)
- Brain directory (read-write)
- Project directory (read-write)
- User-configured mounts from `~/.archie/config.yaml`

The entrypoint installs archie from the mounted repo (`uv tool install -e /opt/archie`)
and passes through to the command. The default command is `archie kiro`, which symlinks
persona dirs to kiro-cli paths, assembles the system prompt from brain-resident files
(resolving `@` directives in `_archie/soul.md`), and launches kiro-cli.

## Adding a Service Integration

1. Create `src/archie/<service>/` with `__init__.py`, `client.py`, `cli.py`
2. Write the client class — accepts credentials, returns data, raises on error
3. Write the CLI module — Click group, `_get_client()` helper, `@handle_errors` on commands
4. Register the group in `src/archie/cli.py`
5. Add credential mapping to `src/archie/auth/inject.py` if needed
6. Add tests in `tests/`

## Persona

### System Prompt

The system prompt is assembled by `archie kiro` from brain-resident files.
The live template is `_archie/soul.md` in the brain, which uses `@` directives to include
other files:

- `@agent <file>` — include from `<brain>/_archie/<file>`
- `@user <file>` — include from `<brain>/simon/<file>` (strips frontmatter)
- `@script <alias>` — run command from config or built-in (e.g. `signals`)

The seed lives at `persona/agents/archie.md` and is deployed to the brain on `archie init`.

### Skills

Skills follow a layered naming convention:

| Layer    | Prefix       | Purpose                                    |
|----------|--------------|--------------------------------------------|
| Policy   | `policy-*`   | Standards and conventions                   |
| Workflow | `workflow-*` | Multi-step orchestration                    |
| Tool     | `tool-*`     | Operational guidance for specific tools     |
| Action   | `action-*`   | Self-contained tasks                        |
| Archie   | `archie-*`   | Self-referential platform operations        |

### Adding a Skill

Use the `action-create-skill` skill for guidance on structure, naming, and conventions.
Skills live in `persona/skills/<name>/SKILL.md` with optional `references/` subdirectory.

After adding a skill, add its path to `plugin.json`.

## CLI

### Adding a Command

Built-in commands are defined in `src/archie/cli.py` as Click commands registered on the
`main` group. Service subcommands are defined in their own `<service>/cli.py` and imported
into the main CLI.

Running `archie` with no subcommand launches kiro-cli in the sandbox. Subcommands
(`init`, `install`, `build`, `status`, `ls`, `rm`) are for platform management.

### Config

`~/.archie/config.yaml` is created by `archie init`. It holds:

- `brain_dir` — path to the brain directory
- `project_dir` — path to the projects root
- `archie_repo` — path to this repo
- `theme` — banner colour
- `env` — environment variables forwarded into containers
- `mounts` — additional files/directories mounted into containers
- `networks` — Docker networks to connect containers to
- `auth` — OAuth provider configuration
- `projects` — per-project config (issue tracker, slack channel, etc.)
- `prompt.scripts` — commands for `@script` directive resolution

### Package Data

Runtime files bundled via `[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml`:

- `sandbox/Dockerfile` → `archie/sandbox/Dockerfile`
- `persona/` → `archie/persona/`
- `src/archie/auth/providers.yaml` → `archie/auth/providers.yaml`
- `src/archie/brain/templates` → `archie/brain/templates`

If you add new runtime data files, add a corresponding `force-include` entry.

## Code Style

Uses [ruff](https://docs.astral.sh/ruff/) (line length 100, Python 3.11 target).

```bash
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/
```

## Commit Messages

[Conventional commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`.

## Submitting Changes

1. Create a branch from `main`
2. Make changes
3. Run ruff check and format
4. Run tests: `uv run pytest`
5. Commit with conventional commit message
6. Push and create PR
