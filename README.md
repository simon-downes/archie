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
uv tool install git+https://github.com/simon-downes/agent-kit.git
archie install
archie build
```

See [Getting Started](docs/getting-started.md) for credentials, brain setup, and first run.

## Commands

| Command | Description |
|---------|-------------|
| `archie` | Run Archie in the sandbox |
| `archie shell` | Interactive shell in the sandbox |
| `archie install` | Deploy persona and default config to `~/.archie/` |
| `archie build` | Build the sandbox Docker image |
| `archie build --quick` | Rebuild using Docker cache |
| `archie status` | Check environment readiness |

## Documentation

- [Getting Started](docs/getting-started.md) — installation, credentials, brain setup, first run
- [Capabilities](docs/capabilities.md) — what Archie can do, with examples
- [Brain](docs/brain.md) — knowledge, memory, and the second brain
- [Sessions](docs/sessions.md) — project sessions, general sessions, and how they work
- [Vision & Architecture](docs/vision.md) — design rationale, principles, and phasing
- [Agent-kit](agent-kit/README.md) — CLI toolkit for SaaS APIs and brain management

## Development

```bash
git clone <repo-url>
cd archie
uv tool install -e .
archie install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions.
