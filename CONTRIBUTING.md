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
archie install
archie status
```

## Repository Layout

```
archie/
├── persona/                     # Who Archie is
│   ├── agents/                  # Agent configs (JSON) — orchestrator + subagents
│   ├── skills/                  # Layered knowledge modules
│   ├── prompts/                 # System prompts (.prompt.md)
│   └── guidance/                # Steering files (tool usage, conventions)
├── src/archie/                  # Platform capabilities (Python CLI)
│   ├── cli.py                   # Click CLI — archie, shell, install, build, status
│   ├── config.py                # Config loading, project discovery, status checks
│   ├── docker.py                # Container operations (build, run, list)
│   ├── output.py                # Rich terminal output, themed banner
│   └── auth/
│       ├── __init__.py          # Minimal — credential store moved to agent-kit
│       └── inject.py            # Resolves ak.* credential paths for container injection
├── sandbox/
│   └── Dockerfile               # Sandbox image (Debian + dev tools)
├── agent-kit/                   # Separate git repo — CLI toolkit for SaaS APIs
├── docs/
│   ├── vision.md                # Design rationale, principles, phasing
│   └── brain.md                 # How Archie uses the second brain
├── tests/
└── pyproject.toml
```

## Architecture

### Two Codebases

Archie has two codebases with distinct responsibilities:

- **archie** (this repo) — persona, skills, prompts, sandbox, CLI, config. Everything
  about how Archie behaves and runs.
- **agent-kit** (`agent-kit/` subdirectory, separate git repo) — CLI toolkit for
  structured access to external services and data stores. Credentials, brain management,
  Notion, Linear, Slack, project detection.

When adding a capability, determine where it belongs:

| Goes in agent-kit | Goes in archie |
|--------------------|----------------|
| Structured CLI access to external services | LLM reasoning, extraction, decision-making |
| Mechanical operations (no LLM needed) | Archie-specific workflows and orchestration |
| Reusable by systems other than Archie | Prompt-driven behaviour |
| Credential management | Skills and persona |

See [agent-kit CONTRIBUTING.md](agent-kit/CONTRIBUTING.md) for agent-kit conventions.

### Credential Flow

Credentials are managed by agent-kit (`ak auth`). Archie's config maps agent-kit
credential paths to container environment variables:

```yaml
credentials:
  GH_TOKEN: ak.github.token
  NOTION_TOKEN: ak.notion.access_token
```

At container launch, `inject.py` reads from `~/.agent-kit/credentials.yaml` and injects
as `-e` flags. OAuth tokens are auto-refreshed if expired.

### Project Detection

Project directory is configured in agent-kit (`project_dir` in `~/.agent-kit/config.yaml`).
Archie reads this to determine which directory to mount into the container.

Inside the container, `ak project` resolves the current project and `ak project --config`
enriches with brain project config (issues provider, slack, etc).

### Container Mounts

The sandbox always mounts:
- The current project directory (read-write)
- The brain directory (read-only, or read-write when the project is `archie`)
- Persona files to kiro-cli paths
- Agent-kit config directory
- Kiro-cli data directory
- User-configured mounts from `~/.archie/config.yaml`

## Persona

### System Prompt

`persona/prompts/archie.prompt.md` defines Archie's identity and behaviour. It contains
a "Critical Rules" section — these rules counter specific behavioural tendencies in the
underlying AI harness (kiro-cli) and must be preserved across prompt rewrites. They are
functional, not stylistic.

### Skills

Skills follow a layered naming convention:

| Layer    | Prefix       | Purpose                                    |
|----------|--------------|--------------------------------------------|
| Policy   | `policy-*`   | Standards and conventions                   |
| Workflow | `workflow-*` | Multi-step orchestration                    |
| Tool     | `tool-*`     | Operational guidance for specific tools     |
| Action   | `action-*`   | Self-contained tasks                        |
| Archie   | `archie-*`   | Self-referential platform operations        |

`archie-*` skills operate on the archie platform itself. They have implicit knowledge of
the architecture and compose other skills (plan, implement, review) with archie-specific
context.

After editing persona files, run `archie install` to deploy to `~/.archie/persona/`.
The `{{USER}}` placeholder in `persona/agents/archie.json` is templated during install.

### Adding a Skill

Use the `action-create-skill` skill for guidance on structure, naming, and conventions.
Skills live in `persona/skills/<name>/SKILL.md` with optional `references/` subdirectory.

## CLI

### Adding a Command

Built-in commands are defined in `src/archie/cli.py` as Click commands registered on the
`main` group.

Running `archie` with no subcommand launches kiro-cli in the sandbox. Subcommands
(`install`, `build`, `shell`, `status`) are for platform management.

### Config

`~/.archie/config.yaml` is created by `archie install` with defaults from `DEFAULT_CONFIG`
in `config.py`. It holds:

- `theme` — banner colour
- `env` — environment variables forwarded into containers
- `credentials` — maps env vars to agent-kit credential paths (`ak.service.field`)
- `mounts` — additional files/directories mounted into containers

Config changes are picked up immediately. Persona changes require `archie install`.

### Package Data

Runtime files bundled via `[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml`:

- `sandbox/Dockerfile` → `archie/sandbox/Dockerfile`
- `persona/` → `archie/persona/`

If you add new runtime data files, add a corresponding `force-include` entry.

## Documentation

- `docs/vision.md` — design rationale, principles, and phasing
- `docs/brain.md` — how Archie uses the second brain

Keep README.md as the user-facing entry point. Keep CONTRIBUTING.md for development
conventions (primary consumer: `archie-add-capability` skill). Use `docs/` for depth.

## Code Style

Uses [ruff](https://docs.astral.sh/ruff/) (line length 100, Python 3.11 target).

```bash
uv run ruff check src/ && uv run ruff format --check src/
```

## Commit Messages

[Conventional commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`.

## Submitting Changes

1. Create a branch from `main`
2. Make changes
3. Run ruff check and format
4. Commit with conventional commit message
5. Push and create PR
