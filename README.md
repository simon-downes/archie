# Archie

Personal AI platform that amplifies your effectiveness across all areas of your life. Archie
manages your knowledge, understands your context, and acts on your behalf — handling
operational overhead so you can focus on the work that matters.

## What It Does

Archie is a single, integrated AI assistant built on three pillars:

- **Persona** — agent configurations, skills, prompts, and guidance that define how Archie behaves
- **Brain** — a persistent second brain that stores your knowledge, contacts, goals, and context
- **Sandbox** — Docker containers with a full development toolchain where Archie runs

## Quick Start

```bash
# Install archie and agent-kit
uv tool install git+https://github.com/simon-downes/archie.git
uv tool install git+https://github.com/simon-downes/agent-kit.git

# Deploy persona and default config
archie install

# Set up credentials (via agent-kit)
ak auth set github token
ak auth login notion

# Initialise the brain
ak brain init

# Build the sandbox
archie build

# Run Archie
archie
```

## Commands

| Command | Description |
|---------|-------------|
| `archie` | Run Archie (kiro-cli) in the sandbox |
| `archie shell` | Interactive shell in the sandbox |
| `archie install` | Deploy persona and default config to `~/.archie/` |
| `archie build` | Build the `archie-sandbox` Docker image |
| `archie status` | Check environment readiness |

## Configuration

Archie's config lives at `~/.archie/config.yaml`. Agent-kit's config (credentials, brain,
project directory) lives at `~/.agent-kit/config.yaml`.

### Archie Config (`~/.archie/config.yaml`)

```yaml
# Banner colour: blue, purple, green, orange, cyan, red
theme: blue

# Environment variables forwarded into containers
# Values starting with $ are resolved from the host
env:
  TERM: $TERM
  COLORTERM: $COLORTERM

# Credential mappings: ENV_VAR → agent-kit credential path
credentials:
  GH_TOKEN: ak.github.token
  NOTION_TOKEN: ak.notion.access_token
  AWS_ACCESS_KEY_ID: ak.aws.access_key_id

# Additional mounts into the container
mounts:
  - ~/.gitconfig:ro
  - [~/.ssh/id_ed25519, '~/.ssh/id_ed25519:ro']
```

### Agent-kit Config (`~/.agent-kit/config.yaml`)

See [agent-kit documentation](agent-kit/README.md) for full details.

```yaml
project_dir: ~/dev

brain:
  dir: ~/.archie/brain
  contexts:
    shared: null
    work-acme: git@github.com:you/brain-work-acme.git
```

## Sandbox

Debian-based Docker image with a full development toolchain:

- **Languages:** Python (via uv), PHP, Node.js
- **IaC:** OpenTofu, terraform-docs, Scalr CLI
- **Cloud:** AWS CLI v2, GitHub CLI
- **Tools:** ripgrep, fd, jq, yq, difftastic, xh, just, shfmt, shellcheck, sqlite3
- **Databases:** psql, mysql, redis-cli
- **AI:** Kiro CLI, Toad, agent-kit

The container runs as your host user (matching UID) with your project directory, brain,
and credentials mounted in.

## Persona

The persona defines Archie's identity — how the AI agent behaves, what it knows, and
what skills it has.

| Directory | Contents |
|-----------|----------|
| `agents/` | Agent configs — orchestrator (archie) and subagents |
| `prompts/` | System prompts defining behaviour and rules |
| `skills/` | Layered knowledge modules |
| `guidance/` | Steering files for tool usage and conventions |

The persona is deployed to `~/.archie/persona/` on `archie install` and mounted into
containers.

## Documentation

- [Vision & Architecture](docs/vision.md) — design rationale, principles, and phasing
- [Brain](docs/brain.md) — how Archie uses the second brain
- [Agent-kit](agent-kit/README.md) — CLI toolkit for SaaS APIs and brain management

## Development

```bash
uv tool install -e .
uv run archie --help
archie install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions.
