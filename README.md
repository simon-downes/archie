# Archie

Personal AI-assisted development toolkit. Manages Docker sandbox environments where AI coding agents (Kiro, Toad) run with project files, credentials, and configuration mounted from the host.

## What It Does

Archie consolidates three concerns into one tool:

- **Persona** — agent configurations, skills, prompts, and guidance that define how Archie behaves
- **Sandbox** — Docker containers with a full development toolchain where agents run
- **Credentials** — secure storage and injection of API tokens and OAuth credentials into containers

## Quick Start

```bash
# Install the CLI (editable for development)
uv tool install -e .

# Set up ~/.archie/ (persona + default config)
archie install

# Build the sandbox Docker image
archie build

# Run an AI agent in the sandbox
archie kiro

# Or just get a shell
archie shell
```

## Commands

| Command | Description |
|---------|-------------|
| `archie install` | Deploy persona and default config to `~/.archie/` |
| `archie build` | Build the `archie-sandbox` Docker image |
| `archie shell` | Interactive shell in the sandbox |
| `archie kiro` | Run Kiro CLI in the sandbox |
| `archie toad` | Run Toad in the sandbox |
| `archie list` | Show running archie sessions |
| `archie status` | Check environment readiness |
| `archie auth set` | Store static credentials |
| `archie auth import` | Import credentials from environment variables |
| `archie auth login` | OAuth2 browser-based authentication |
| `archie auth refresh` | Refresh OAuth tokens |
| `archie auth status` | Show credential status for all services |

Tool commands (`kiro`, `toad`) are defined in config and can be extended without code changes.

## Project Structure

```
archie/
├── persona/                 # Who Archie is
│   ├── agents/              # Agent configs (JSON)
│   ├── skills/              # Layered knowledge modules
│   ├── prompts/             # System prompts
│   └── guidance/            # Steering files (tool usage, conventions)
├── src/archie/              # What Archie can do
│   ├── cli.py               # Click CLI with dynamic tool commands
│   ├── config.py            # Config loading, project discovery, status checks
│   ├── docker.py            # Container operations (build, run, list)
│   ├── output.py            # Rich terminal output, themed banner
│   └── auth/                # Credential management
│       ├── __init__.py      # Credential store (YAML I/O, permissions)
│       ├── cli.py           # Auth subcommands
│       ├── oauth.py         # OAuth2 + PKCE flow
│       ├── inject.py        # Credential → env var resolution for containers
│       └── providers.yaml   # Bundled OAuth provider definitions
├── sandbox/                 # Where Archie runs
│   └── Dockerfile           # Sandbox image (Debian + dev tools)
├── tests/
└── pyproject.toml
```

## Configuration

All configuration lives in `~/.archie/config.yaml`, created by `archie install` with sensible defaults.

### `project_dir`

Root directory for project discovery. When you run `archie shell` or any tool command, Archie resolves the current project as the first subdirectory under `project_dir` that contains your working directory.

```yaml
project_dir: ~/dev
```

Running `archie shell` from `~/dev/my-app/src/` mounts `~/dev/my-app` into the container.

### `theme`

Colour theme for the startup banner. Options: `blue`, `purple`, `green`, `orange`, `cyan`, `red`.

```yaml
theme: blue
```

### `env`

Environment variables forwarded into containers. Values starting with `$` are resolved from the host environment. Plain values are set directly.

```yaml
env:
  TERM: $TERM           # Forward from host
  COLORTERM: $COLORTERM
  EDITOR: nano          # Set explicitly
```

Unset host variables are silently skipped.

### `tools`

External tools that run in the sandbox. Each tool becomes a CLI command (`archie <name>`). Define the command to run and optional default arguments.

```yaml
tools:
  kiro:
    command: kiro-cli
    args: [chat, --agent, archie]
  toad:
    command: toad
```

Extra CLI arguments replace the defaults: `archie kiro chat --agent other` runs `kiro-cli chat --agent other` instead of the configured defaults.

### `mounts`

Directories and files mounted into the container. Two formats:

```yaml
mounts:
  # Auto-mapped: host home → container home
  - ~/.toad

  # Explicit mapping: [host_path, container_path]
  - [~/.archie/persona/agents, ~/.kiro/agents]

  # With Docker options (e.g. read-only)
  - [~/.gitconfig, '~/.gitconfig:ro']
  - [~/.ssh, '~/.ssh:ro']
```

Non-existent host paths are silently skipped.

### `auth`

Defines authentication providers and their type. Used by `archie auth` commands to determine how credentials are acquired.

```yaml
auth:
  # Static: store tokens directly via `archie auth set`
  github:
    type: static
    fields: [token]

  # Static with multiple fields
  aws:
    type: static
    fields: [access_key_id, secret_access_key, session_token]

  # OAuth: browser-based auth via `archie auth login`
  notion:
    type: oauth
    # Populated automatically on first login:
    # client_id: ...
    # authorization_endpoint: ...
    # token_endpoint: ...
```

For OAuth providers, endpoint URLs and client IDs are discovered automatically on first `archie auth login` and written back to config for reuse.

### `credentials`

Maps credential fields to container environment variables. Each entry is `ENV_VAR_NAME: service.field` where the dotpath resolves against `~/.archie/credentials.yaml`.

```yaml
credentials:
  GH_TOKEN: github.token
  NOTION_TOKEN: notion.access_token
  AWS_ACCESS_KEY_ID: aws.access_key_id
  AWS_SECRET_ACCESS_KEY: aws.secret_access_key
  AWS_SESSION_TOKEN: aws.session_token
```

At container launch, each mapping is resolved. If the credential exists, it's injected as an environment variable. Missing credentials are silently skipped — you only need to configure the services you use.

## Credential Management

Credentials are stored separately from config in `~/.archie/credentials.yaml` (mode `0600`). The config file defines *what gets injected and how to authenticate*; the credentials file holds *the actual secrets*.

### Static Credentials

For API tokens and keys:

```bash
# Interactive prompt (value hidden)
archie auth set github token

# Pipe from stdin
echo "ghp_xxx" | archie auth set github token

# Import from environment variables (e.g. via aws-vault)
aws-vault exec my-profile -- archie auth import aws \
  AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

The `import` command strips the service name prefix from env var names: `AWS_ACCESS_KEY_ID` becomes field `access_key_id` under the `aws` service.

### OAuth Credentials

For services requiring browser-based authentication:

```bash
# First login — discovers endpoints, registers client, opens browser
archie auth login notion

# Manual refresh
archie auth refresh notion
```

OAuth tokens with `expires_at` are automatically refreshed at container launch if expired.

### How It Fits Together

```
~/.archie/config.yaml          ~/.archie/credentials.yaml
┌─────────────────────┐        ┌──────────────────────────┐
│ auth:                │        │ github:                  │
│   github:            │        │   token: ghp_xxx         │
│     type: static     │        │                          │
│                      │        │ notion:                  │
│ credentials:         │───────>│   access_token: secret_x │
│   GH_TOKEN:          │ reads  │   refresh_token: ...     │
│     github.token     │        │   expires_at: ...        │
│   NOTION_TOKEN:      │        │                          │
│     notion.access_   │        │ aws:                     │
│       token          │        │   access_key_id: AKIA... │
└─────────────────────┘        └──────────────────────────┘
         │
         │ injects as -e flags
         ▼
   ┌──────────────┐
   │  Container   │
   │  GH_TOKEN=…  │
   │  NOTION_…=…  │
   └──────────────┘
```

## Sandbox

The sandbox is a Debian-based Docker image with a full development toolchain:

- **Languages:** Python (via uv), PHP, Node.js
- **IaC:** OpenTofu, terraform-docs, Scalr CLI
- **Cloud:** AWS CLI v2, GitHub CLI
- **Tools:** ripgrep, fd, jq, yq, difftastic, xh, just, shfmt, shellcheck, sqlite3
- **Databases:** psql, mysql, redis-cli
- **AI:** Kiro CLI, Toad, agent-kit

The container runs as your host user (matching UID) with your project directory, config, and credentials mounted in.

## Persona

The persona defines Archie's identity — how the AI agent behaves, what it knows, and what skills it has.

| Directory | Contents |
|-----------|----------|
| `agents/` | Agent configs — one orchestrator (archie) and five subagents |
| `prompts/` | System prompts defining behaviour and rules |
| `skills/` | Layered knowledge modules (policy → workflow → tool → action) |
| `guidance/` | Steering files for tool usage and conventions |

The persona is bundled into the Python package and deployed to `~/.archie/persona/` on `archie install`. From there it's mounted into containers at the paths the AI tools expect.

## Development

```bash
# Editable install — code changes picked up immediately
uv tool install -e .

# Run from the project venv
uv run archie --help

# Lint and format
uv run ruff check src/
uv run ruff format src/

# After changing persona files, re-deploy
archie install
```
