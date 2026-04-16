# Contributing

## Key Rules

- Credentials go in `credentials.yaml`, never in `config.yaml` — the separation is structural
- Persona is the source of truth; `~/.archie/persona/` is the deploy target — edit in repo, `archie install` to deploy
- Config changes are picked up immediately; persona changes require `archie install`
- Built-in commands are code (`shell`, `build`, `install`, `status`, `auth`); tool commands come from config
- The sandbox always runs as the host user (UID matching), never root
- `src/archie/` is capabilities and tooling; `persona/` is identity and knowledge — don't mix them

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker (for sandbox commands)

### Setup

```bash
git clone <repo-url>
cd archie

# Install in editable mode (changes picked up immediately)
uv tool install -e .

# Or use the project venv
uv sync --extra dev
uv run archie --help

# Deploy persona and default config
archie install
```

### Verify

```bash
archie status    # Should show green checks for Docker and project directory
archie --help    # Should list all commands including configured tools
```

## Project Layout

```
archie/
├── persona/              # Identity — agents, skills, prompts, guidance
│   ├── agents/           # Agent configs (JSON) — one orchestrator + subagents
│   ├── skills/           # Layered knowledge modules (policy/workflow/tool/action)
│   ├── prompts/          # System prompts (.prompt.md)
│   └── guidance/         # Steering files (tool usage, conventions)
├── src/archie/           # Capabilities — Python CLI package
│   ├── cli.py            # Click group with dynamic tool commands
│   ├── config.py         # Config loading, project discovery, status checks
│   ├── docker.py         # Container operations
│   ├── output.py         # Rich terminal output, themed banner
│   └── auth/             # Credential management subsystem
│       ├── __init__.py   # Credential store (YAML I/O, file permissions)
│       ├── cli.py        # Auth subcommands (set, import, login, refresh, status)
│       ├── oauth.py      # OAuth2 + PKCE flow
│       ├── inject.py     # Credential → env var resolution for containers
│       └── providers.yaml # Bundled OAuth provider definitions
├── sandbox/              # Runtime — Docker image definition
│   └── Dockerfile        # Debian + full dev toolchain
├── tests/
└── pyproject.toml
```

## Code Style

Uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting. Configured in `pyproject.toml` (line length 100, Python 3.11 target).

```bash
# Check
uv run ruff check src/
uv run ruff format --check src/

# Fix
uv run ruff check src/ --fix
uv run ruff format src/
```

Run both before committing. No other formatters needed — ruff handles everything.

## Project Conventions

### Adding a CLI Command

Built-in commands are defined in `src/archie/cli.py` as Click commands registered on the `main` group. Add the command name to `BUILTIN_COMMANDS` to prevent collision with config-defined tools.

Tool commands (things that run in the sandbox) don't need code — add them to the `tools` section of `~/.archie/config.yaml`.

### Adding an Auth Provider

Static providers (API keys, tokens) need no code:

1. Add the service to the `auth` section of `DEFAULT_CONFIG` in `config.py` with `type: static` and `fields`
2. Add credential-to-env-var mappings in the `credentials` section
3. Users store credentials via `archie auth set <service> <field>`

OAuth providers need endpoint configuration:

1. Add the provider to `src/archie/auth/providers.yaml` with a `server_url` for endpoint discovery
2. Add the service to `DEFAULT_CONFIG` with `type: oauth`
3. Add credential mappings
4. The OAuth flow (`auth login`) handles discovery, registration, and token exchange automatically

### Config and Credentials

Config (`~/.archie/config.yaml`) holds:
- How to connect (auth provider types, OAuth endpoints, client IDs)
- What to inject (credential-to-env-var mappings)
- Runtime settings (mounts, env, tools, theme)

Credentials (`~/.archie/credentials.yaml`, mode 0600) holds:
- Actual secrets (tokens, keys)
- Token state (expires_at, refresh_token)

Never put secret values in config. Never put connection/mapping config in credentials.

### Persona Changes

The system prompt (`persona/prompts/archie.prompt.md`) contains a "Critical Rules" section.
These rules exist to counter specific behavioural tendencies in the underlying AI harness
(kiro-cli) and must be preserved across prompt rewrites. They are functional, not stylistic.

Skills follow a layered naming convention:

| Layer | Prefix | Purpose |
|-------|--------|---------|
| Policy | `policy-*` | Standards and conventions |
| Workflow | `workflow-*` | Multi-step orchestration |
| Tool | `tool-*` | Operational guidance for specific tools |
| Action | `action-*` | Self-contained tasks |
| Archie | `archie-*` | Self-referential platform operations |

`archie-*` skills are special — they operate on the archie platform itself and have implicit
knowledge of its architecture and conventions. They compose other skills (plan, implement,
review) with archie-specific context.

After editing persona files, run `archie install` to deploy to `~/.archie/persona/`. The `{{USER}}` placeholder in `persona/agents/archie.json` is templated during install.

### Documentation

Architecture decisions and detailed reference material live in `docs/`:

- `docs/vision.md` — design rationale, principles, and phasing
- `docs/brain.md` — brain structure, entity types, conventions (planned)

Keep README.md as the entry point for understanding and using the project. Keep CONTRIBUTING.md
for development conventions. Use `docs/` for depth that would clutter either of those.

### Package Data

Files that need to be available at runtime regardless of install method are bundled via `[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml`:

- `sandbox/Dockerfile` → `archie/sandbox/Dockerfile`
- `persona/` → `archie/persona/`
- `src/archie/auth/providers.yaml` → `archie/auth/providers.yaml`

If you add new runtime data files, add a corresponding `force-include` entry.

## Commit Messages

Uses [conventional commits](https://www.conventionalcommits.org/). Common types:

- `feat:` — new functionality
- `fix:` — bug fixes
- `docs:` — documentation changes
- `chore:` — maintenance, dependencies, config

## Submitting Changes

1. Create a branch from `main`
2. Make changes
3. Run `uv run ruff check src/ && uv run ruff format --check src/`
4. Commit with conventional commit message
5. Push and create PR
