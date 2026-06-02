# Archie

Personal AI platform that manages your knowledge, understands your context, and acts on
your behalf. One integrated assistant — not a collection of tools.

## Three Pillars

- **Persona** — agent configurations, skills, prompts, and guidance that define how Archie
  behaves and what it knows
- **Brain** — a persistent second brain that stores your knowledge, contacts, goals, and
  context across all areas of your life
- **Sandbox** — Docker containers with a full development toolchain where Archie runs

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker

## Install

```bash
uv tool install git+https://github.com/simon-downes/archie.git
archie init
archie build
```

See [Getting Started](docs/getting-started.md) for credentials, brain setup, and first run.

## Commands

### Sessions

| Command | Description |
|---------|-------------|
| `archie` | Run Archie in the sandbox |
| `archie "prompt"` | Run with an initial prompt |
| `archie --name foo` | Named session (isolated working directory) |
| `archie --shell` | Interactive shell in the sandbox |
| `archie ls` | List sessions and statuses |
| `archie rm [name]` | Remove session working directories |

### Platform

| Command | Description |
|---------|-------------|
| `archie init` | One-time setup (config, credentials, brain) |
| `archie install` | Deploy persona to `~/.kiro/` (for local use) |
| `archie build` | Build the sandbox Docker image |
| `archie build --quick` | Rebuild using Docker cache |
| `archie status` | Check environment readiness |

### Services

| Command | Description |
|---------|-------------|
| `archie brain` | Brain operations (search, read, memory, index, commit, ref) |
| `archie auth` | Credential management (login, status, set) |
| `archie linear` | Linear issue tracking |
| `archie jira` | Jira issue tracking |
| `archie notion` | Notion pages and databases |
| `archie slack` | Slack channels and messaging |
| `archie google` | Google Workspace (mail, calendar, drive) |
| `archie project` | Project detection and config |
| `archie digest` | Digest generation |

## Project Structure

```
archie/
├── persona/                     # Who Archie is
│   ├── skills/                  # Layered knowledge modules
│   ├── agents/                  # Agent configs and definitions
│   └── guidance/                # Steering files (tools.md, LOCAL.md)
├── src/archie/                  # Unified Python CLI
│   ├── cli.py                   # Main CLI group + session commands
│   ├── config.py                # Config loading (~/.archie/config.yaml)
│   ├── docker.py                # Container operations
│   ├── output.py                # Rich terminal output
│   ├── errors.py                # JSON output + error handling for agent commands
│   ├── auth/                    # Credential management + OAuth
│   ├── brain/                   # Brain operations (search, index, git, refs)
│   ├── linear/                  # Linear integration
│   ├── jira/                    # Jira integration
│   ├── notion/                  # Notion integration
│   ├── slack/                   # Slack integration
│   ├── google/                  # Google Workspace integration
│   └── digest/                  # Digest generation
├── sandbox/                     # Docker image (Debian + dev tools)
├── tests/
├── docs/
├── plugin.json                  # Skill sharing manifest
└── pyproject.toml
```

## Documentation

- [Getting Started](docs/getting-started.md) — installation, credentials, brain setup, first run
- [Capabilities](docs/capabilities.md) — what Archie can do, with examples
- [Brain](docs/brain.md) — knowledge, memory, and the second brain
- [Sessions](docs/sessions.md) — project sessions, general sessions, and how they work
- [Vision & Architecture](docs/vision.md) — design rationale, principles, and phasing

## Development

```bash
git clone <repo-url>
cd archie
uv tool install -e .
archie init
archie build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions.
