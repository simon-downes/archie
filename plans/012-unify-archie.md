# Unify Archie

## Objective

Merge agent-kit into archie as a single project. Eliminate the artificial separation
between "persona + orchestration" and "CLI toolkit" — they're one system with one user.
Simplify config, remove indirection, and make the development loop frictionless.

## Context

The agent-kit separation was premature abstraction. In practice:
- There's one agent (archie), one user (simon), one system
- Config is split across `~/.archie/config.yaml` and `~/.agent-kit/config.yaml` for no benefit
- Brain structure lives in archie but brain CLI lives in agent-kit
- The Slack OAuth token refresh needs write access to credentials on the host side, but
  the current architecture makes this awkward across the boundary
- Cross-cutting changes require coordinated branches across two repos
- `ak init` asks for agent/user names that are always "archie"/"simon"
- The "reusable by other agents" story never materialised and adds complexity everywhere

The persona restructure plan (011) identified real problems (skill portability, prompt
assembly, repo structure) but solved them by moving more into agent-kit — deepening the
split. This plan takes the opposite approach: fold everything into one repo, then do the
content improvements (skill portability, prompt assembly) in that simpler context.

---

## Requirements

### R1: Merge agent-kit source into archie
- MUST move all agent-kit modules into `src/archie/` under appropriate subpackages
- MUST unify the CLI: `archie brain`, `archie linear`, `archie slack`, etc.
- MUST preserve all existing `ak` functionality under the new namespace
- MUST remove the `agent-kit/` subdirectory and its separate git repo

### R2: Unified config
- MUST merge into a single config at `~/.archie/config.yaml`
- MUST combine: brain dir, project dir, auth providers, service scopes, mounts, env, networks
- MUST eliminate `~/.agent-kit/` directory entirely (config, credentials, projects.yaml all move)
- MUST store credentials at `~/.archie/credentials.yaml` (0600 permissions)
- MUST store project config at `~/.archie/projects.yaml`
- MUST remove `ak.service.field` dotpath indirection for credential injection

### R3: Simplified init
- `archie init` MUST create `~/.archie/config.yaml`, `~/.archie/credentials.yaml`
- `archie init` MUST initialise the brain (directories, BRAIN.md, profile, git repo, db)
- MUST hardcode agent name as "archie" and user name as "simon" (no prompts)
- MUST be idempotent — safe to re-run without destroying existing data

### R4: Container workflow
- Host-side `archie` command MUST mount the archie repo into the container (read-write)
- Entrypoint MUST run `uv tool install -e /opt/archie` for CLI availability
- Entrypoint MUST symlink persona dirs to kiro-cli expected paths
- No version bumping or `archie install` required for container workflow
- `~/.archie/` MUST be mounted read-write
- Credentials MUST be injected as env vars (not mounted as files)

### R5: Host install (optional, for local/non-container use)
- `archie install` deploys persona to `~/.kiro/` paths (symlinks in dev, copies if installed from wheel)
- Only needed when running kiro-cli locally without the container

### R6: Skill portability
- MUST remove direct command references from skill instruction text
- MUST replace with intent-based language referencing `# Available Tools`
- MUST fold tool-issues and tool-slack into workflow skills
- MUST add `plugin.json` for skill sharing/discovery

### R7: Prompt assembly
- MUST create `persona/agents/archie.md` with soul content + `@` directives
- Entrypoint MUST resolve directives (bash, extending current approach)
- Brain's `_archie/soul.md` is the live template (evolvable)
- `@agent <file>` → read from `<brain>/_archie/<file>`
- `@user <file>` → read from `<brain>/simon/<file>`
- `@script <alias>` → run command from config, include stdout

### R8: Backward compatibility
- MUST work on a feature branch — main remains functional throughout
- MUST provide `ak` as a temporary entry point (pyproject.toml scripts alias)
- MUST update all brain-resident files that reference `ak` commands
- Container MUST still work throughout migration (incremental milestones)

---

## Technical Design

### Unified config schema

`~/.archie/config.yaml`:

```yaml
# Directories
brain_dir: ~/.archie/brain
project_dir: ~/dev
archie_repo: ~/dev/archie

# Container
theme: blue
env:
  TERM: $TERM
  COLORTERM: $COLORTERM
  EDITOR: $EDITOR
networks: []
mounts:
  - [~/.archie, ~/.archie]
  - [~/.kiro/sessions, ~/.kiro/sessions]
  - [~/.local/share/kiro-cli, ~/.local/share/kiro-cli]
  - ~/.toad
  - [~/.archie/aws.config, ~/.aws/config:ro]
  - ~/.gitconfig:ro
  - [~/.ssh/id_ed25519, ~/.ssh/id_ed25519:ro]
  - [~/.ssh/id_ed25519.pub, ~/.ssh/id_ed25519.pub:ro]

# Auth provider config (OAuth endpoints, scopes)
auth:
  notion:
    authorization_endpoint: https://api.notion.com/v1/oauth/authorize
    token_endpoint: https://api.notion.com/v1/oauth/token
  slack:
    authorization_endpoint: https://slack.com/oauth/v2/authorize
    token_endpoint: https://slack.com/api/oauth.v2.access
    token_path: authed_user.access_token
    refresh_token_path: authed_user.refresh_token
    extra_params:
      user_scope: "channels:history channels:read groups:history groups:read users:read search:read im:history mpim:history"
  google:
    authorization_endpoint: https://accounts.google.com/o/oauth2/v2/auth
    token_endpoint: https://oauth2.googleapis.com/token
    scopes:
      - https://www.googleapis.com/auth/gmail.readonly
      - https://www.googleapis.com/auth/calendar.readonly
      - https://www.googleapis.com/auth/drive.readonly
      - https://www.googleapis.com/auth/userinfo.email
    extra_params:
      access_type: offline
      prompt: consent

# Service scopes
notion:
  read:
    enabled: true
    scope: {pages: [], databases: []}
  write:
    enabled: false
    scope: {pages: [], databases: []}
google:
  mail: {enabled: true}
  calendar: {enabled: true}
  drive: {enabled: true}
slack:
  read:
    enabled: true
    scope: {channels: [], include_dms: false, include_group_dms: false}
  write: {enabled: true}

# Project config (same schema as current ~/.agent-kit/projects.yaml)
projects:
  defaults: {}
  # <org>:
  #   issues: {provider: linear, team: PLAT}
  #   slack: "#platform"
  # <org>/<repo>:
  #   issues: {provider: jira, project: PLAT}

# Prompt assembly
prompt:
  scripts:
    signals: "python3 ~/.kiro/prompts/build-signals.py"
```

`~/.archie/credentials.yaml` (0600 permissions, separate file):

```yaml
github:
  token: ghp_xxx
notion:
  access_token: ntn_xxx
  refresh_token: xxx
  expires_at: "2026-06-01T12:00:00+00:00"
linear:
  token: lin_xxx
slack:
  access_token: xoxp_xxx
  refresh_token: xxx
  expires_at: "2026-06-01T12:00:00+00:00"
  webhook_url: https://hooks.slack.com/xxx
jira:
  email: simon@example.com
  token: xxx
  cloud_id: xxx
google:
  access_token: ya29_xxx
  refresh_token: xxx
  expires_at: "2026-06-01T12:00:00+00:00"
aws:
  access_key_id: AKIA_xxx
  secret_access_key: xxx
  session_token: xxx
scalr:
  token: xxx
  hostname: xxx.scalr.io
```

Container injection uses a hardcoded mapping (no config indirection):

```python
CREDENTIAL_ENV_MAP = {
    ("github", "token"): "GH_TOKEN",
    ("notion", "access_token"): "NOTION_TOKEN",
    ("linear", "token"): "LINEAR_TOKEN",
    ("slack", "webhook_url"): "SLACK_WEBHOOK_URL",
    ("slack", "client_id"): "SLACK_CLIENT_ID",
    ("slack", "client_secret"): "SLACK_CLIENT_SECRET",
    ("jira", "email"): "JIRA_EMAIL",
    ("jira", "token"): "JIRA_TOKEN",
    ("jira", "cloud_id"): "JIRA_CLOUD_ID",
    ("google", "client_id"): "GOOGLE_CLIENT_ID",
    ("google", "client_secret"): "GOOGLE_CLIENT_SECRET",
    ("aws", "access_key_id"): "AWS_ACCESS_KEY_ID",
    ("aws", "secret_access_key"): "AWS_SECRET_ACCESS_KEY",
    ("aws", "session_token"): "AWS_SESSION_TOKEN",
    ("scalr", "token"): "SCALR_TOKEN",
    ("scalr", "hostname"): "SCALR_HOSTNAME",
}
```

### CLI namespace

```
archie                    # launch session (default)
archie "prompt"           # launch with prompt
archie --name foo         # named session
archie --shell            # bash in sandbox
archie ls                 # list sessions
archie rm [name]          # remove sessions

archie brain search       # brain operations
archie brain read
archie brain memory
archie brain index
archie brain commit
archie brain ref

archie auth login <svc>   # credential management
archie auth status

archie linear issues      # service integrations
archie linear issue
archie linear create-issue
archie jira issues
archie notion search
archie notion query
archie slack send
archie slack history
archie google mail
archie google calendar
archie google drive

archie project            # project detection
archie digest             # digest generation

archie init               # one-time setup
archie install            # deploy persona to ~/.kiro/ (optional, for local use)
archie build [--quick]    # build sandbox image
archie status             # environment check
```

Inside the container, the same `archie` binary is available. The `# Available Tools`
section in the system prompt references `archie brain`, `archie linear`, etc.

### Output design

Two output modes coexist in one CLI, determined by audience:

**Human-focused commands** — Rich terminal output (colours, tables, banners, progress):

```
archie                    # session launch
archie ls                 # session list
archie rm                 # session removal
archie init               # setup
archie install            # persona deployment
archie build              # image build
archie status             # environment check
archie auth login         # OAuth flow (interactive)
archie auth status        # credential overview
```

**Agent-focused commands** — JSON to stdout, errors to stderr, `@handle_errors` decorator:

```
archie brain search       # brain operations
archie brain read
archie brain memory
archie brain index
archie brain commit
archie brain ref
archie linear *           # all Linear subcommands
archie jira *             # all Jira subcommands
archie notion *           # all Notion subcommands
archie slack *            # all Slack subcommands
archie google *           # all Google subcommands
archie project            # project detection
archie digest             # digest generation
```

**Rule:** If the primary consumer is the AI agent (called from within a session), it outputs
JSON via `output()`. If the primary consumer is the human at a terminal, it uses Rich.

**Architecture implications:**
- `src/archie/output.py` — Rich helpers (existing, for human commands)
- `src/archie/errors.py` — `output()`, `@handle_errors`, exception hierarchy (from agent-kit, for agent commands)
- Service client classes never format output or call `sys.exit()` — they raise exceptions
- CLI commands are thin: construct client → call method → `output()` or Rich formatting
- `--json` flag on human commands where dual-use is useful (e.g. `archie status --json`)

### Container entrypoint

```bash
#!/bin/bash
# The archie repo is mounted at /opt/archie (read-write) from the host.
# ~/.archie/ is mounted read-write for config and service caches.
# Brain dir is mounted read-write (separate mount).
# Credentials are injected as env vars — not mounted as files.

# Install archie CLI from mounted repo (editable — imports resolve from /opt/archie/src)
# Only needed once per container lifecycle. Fast for editable installs (~1-2s).
# Only re-run needed if pyproject.toml changes (new deps/entry points).
uv tool install -e /opt/archie --quiet

# Symlink persona to kiro-cli paths
ln -sfn /opt/archie/persona/skills ~/.kiro/skills
ln -sfn /opt/archie/persona/agents ~/.kiro/agents
ln -sfn /opt/archie/persona/prompts ~/.kiro/prompts
ln -sfn /opt/archie/persona/guidance ~/.kiro/steering

# Assemble system prompt from brain-resident sources (extends current bash approach)
# Read _archie/soul.md as the live template, resolve @ directives inline
brain_dir=$(yq -r '.brain_dir // "~/.archie/brain"' ~/.archie/config.yaml)
brain_dir="${brain_dir/#\~/$HOME}"
agent_dir="$brain_dir/_archie"
user_dir="$brain_dir/simon"
prompt_out="$HOME/.kiro/prompts/archie.prompt.md"

if [ -d "$brain_dir" ] && [ -f "$agent_dir/soul.md" ]; then
    > "$prompt_out"

    # Process soul.md line by line, resolving @ directives
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            @agent\ *)
                file="${line#@agent }"
                if [ -f "$agent_dir/$file" ] && [ -s "$agent_dir/$file" ]; then
                    cat "$agent_dir/$file" >> "$prompt_out"
                    printf '\n\n' >> "$prompt_out"
                fi
                ;;
            @user\ *)
                file="${line#@user }"
                if [ -f "$user_dir/$file" ] && [ -s "$user_dir/$file" ]; then
                    sed '1{/^---$/!b};1,/^---$/d' "$user_dir/$file" >> "$prompt_out"
                    printf '\n\n' >> "$prompt_out"
                fi
                ;;
            @script\ *)
                alias="${line#@script }"
                cmd=$(yq -r ".prompt.scripts.$alias // \"\"" ~/.archie/config.yaml)
                if [ -n "$cmd" ]; then
                    output=$(eval "$cmd" 2>/dev/null)
                    if [ -n "$output" ]; then
                        echo "$output" >> "$prompt_out"
                        printf '\n\n' >> "$prompt_out"
                    fi
                fi
                ;;
            *)
                echo "$line" >> "$prompt_out"
                ;;
        esac
    done < "$agent_dir/soul.md"
fi

# Set terminal title
if [ -n "$ARCHIE_TITLE" ]; then
    printf '\033]0;%s\007' "$ARCHIE_TITLE"
fi

exec "$@"
```

Host-side `docker run` mounts:
- `archie_repo` config value → `/opt/archie` (read-write — allows git pull, edits from sessions)
- `~/.archie/` → `~/.archie/` (read-write — config, service caches)
- Brain dir → same path in container (read-write)
- Project dir → same path in container (read-write)
- Plus user-configured mounts from config (gitconfig, ssh keys, etc.)

Credentials are injected as `-e` env vars by the host CLI, not mounted as files.

### Prompt assembly (directive resolution)

`persona/agents/archie.md` in the repo is the seed for `_archie/soul.md` in the brain.
It contains the full soul content followed by `@` directives:

```markdown
# Archie

[Full soul content — identity, rules, behaviour, communication style]

---

@agent brain.md
@agent memory.md
@script signals
@agent tools.md
@user profile.md
```

The brain's `_archie/soul.md` is the live template — seeded from `persona/agents/archie.md`
during `archie init`, but evolvable by archie over time (add directives, reorder, rewrite).
The seed includes the `@` directives so the brain copy can resolve them.

Resolution rules (bash, in entrypoint):
- `@agent <file>` → read `<brain_dir>/_archie/<file>`, skip if missing/empty
- `@user <file>` → read `<brain_dir>/simon/<file>`, strip YAML frontmatter, skip if missing
- `@script <alias>` → look up in config `prompt.scripts`, run, include stdout, skip if empty/failed
- All other lines → output as-is

### Repo structure (final state)

```
archie/
├── persona/                     # all persona content (skills, agents, prompts, guidance)
│   ├── skills/                  # shareable skill modules
│   ├── agents/                  # agent definitions (archie.md, subagent JSONs)
│   ├── prompts/                 # subagent prompts + build-signals.py
│   └── guidance/                # steering files (brain.md, tools.md, LOCAL.md)
├── src/archie/                  # unified Python CLI
│   ├── cli.py                   # main CLI group
│   ├── config.py                # unified config (~/.archie/config.yaml)
│   ├── docker.py                # container operations
│   ├── output.py                # Rich terminal output
│   ├── auth/                    # credential management + OAuth
│   │   ├── __init__.py          # credential store (read/write credentials.yaml)
│   │   ├── cli.py               # archie auth login/status
│   │   ├── oauth.py             # OAuth flow
│   │   └── inject.py            # credential → env var mapping for containers
│   ├── brain/                   # brain operations
│   │   ├── cli.py               # archie brain search/read/memory/index/commit/ref
│   │   ├── client.py            # brain client (search, index, git, refs)
│   │   ├── search.py            # search implementation
│   │   ├── index.py             # indexing
│   │   └── git.py               # brain git operations
│   ├── linear/                  # Linear integration
│   ├── jira/                    # Jira integration
│   ├── notion/                  # Notion integration
│   ├── slack/                   # Slack integration
│   ├── google/                  # Google Workspace integration
│   ├── digest/                  # digest generation
│   └── project.py               # project detection
├── sandbox/
│   ├── Dockerfile
│   └── entrypoint.sh
├── plugin.json                  # skill sharing manifest
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

### Credential flow (simplified)

Current: archie config maps env vars → `ak.*` dotpaths → agent-kit reads credentials.yaml → resolves

New: archie reads `~/.archie/credentials.yaml` directly → maps to env vars via `CREDENTIAL_ENV_MAP` → injects into container as `-e` flags

Inside container: env vars are set. `archie linear`, `archie slack` etc. read from env vars
(same as today — the clients already use env vars). No credential file needed inside the container.

---

## Milestones

### 1. Merge agent-kit source into archie

Approach:
- Copy agent-kit modules into `src/archie/`, rename imports, merge CLI
- agent-kit has bundled data files (`auth/providers.yaml`, `brain/templates/`) — these
  become package data in archie's pyproject.toml via `force-include`
- Keep `ak` as a temporary entry point for transition (pyproject.toml scripts alias)
- Don't change config paths yet — both `~/.archie/` and `~/.agent-kit/` configs still
  work in this milestone to avoid breaking the running system
- Keep `{{USER}}`/`{{AGENT}}` template placeholders working in M1 (removed in M3)
- Preserve the output pattern split: agent-kit's `errors.py` (`output()`, `@handle_errors`,
  exception hierarchy) stays intact for agent-facing commands; archie's `output.py` (Rich)
  stays for human-facing commands

Tasks:
- Copy `agent-kit/src/agent_kit/*` to `src/archie/` (brain/, linear/, jira/, notion/,
  slack/, google/, digest/, auth/, project.py, config.py → ak_config.py, init.py, errors.py, mcp.py)
- Rename all `agent_kit` imports to `archie`
- Merge agent-kit's `force-include` entries into archie's pyproject.toml:
  `"src/archie/auth/providers.yaml"` and `"src/archie/brain/templates"`
- Add `mcp` to project dependencies
- Register subcommands in `src/archie/cli.py`: brain, linear, jira, notion, slack, google,
  digest, project, auth, init
- Add `ak = "archie.cli:main"` to `[project.scripts]` as temporary alias
- Copy `agent-kit/tests/` to `tests/`, update imports
- Remove `workspace.exclude` from `[tool.uv]` in pyproject.toml
- Update `.gitignore`

Deliverable: Single Python package with all functionality. Both `archie` and `ak` commands work.

Verify: `uv run ruff check src/` passes. `uv run pytest` passes. `uv run archie brain search "test"` works. `uv run ak brain search "test"` works (alias).

---

### 2. Unify config and credentials

Approach:
- Create new unified config schema at `~/.archie/config.yaml`
- Move credentials to `~/.archie/credentials.yaml`
- Move projects config into main config under `projects:` key
- Write a one-time migration that reads `~/.agent-kit/` and writes to `~/.archie/`
- Simplify credential injection: hardcoded `CREDENTIAL_ENV_MAP`, no dotpath resolution
- `docker.py` reads `archie_repo` from config to determine what to mount at `/opt/archie`

Tasks:
- Rewrite `src/archie/config.py`:
  - New `DEFAULT_CONFIG` with unified schema (as shown in Technical Design)
  - `ARCHIE_HOME = ~/.archie/`, `CONFIG_PATH`, `CREDENTIALS_PATH`
  - `load_config()`, `save_config()`, `load_credentials()`, `save_credentials()`
  - Remove `_read_ak_config()` helper from docker.py — config is now unified
- Write migration function in `config.py`:
  - Read `~/.agent-kit/config.yaml` → merge `brain.dir`, `project_dir`, `user`, `agent`,
    auth providers, service scopes into unified config
  - Read `~/.agent-kit/credentials.yaml` → write to `~/.archie/credentials.yaml`
  - Read `~/.agent-kit/projects.yaml` → merge into config under `projects:` key
  - Only runs if `~/.agent-kit/config.yaml` exists and `~/.archie/config.yaml` doesn't
    have a `brain_dir` key (migration marker)
- Auto-migrate on `archie init` and `archie status`
- Rewrite `src/archie/auth/inject.py`:
  - `CREDENTIAL_ENV_MAP` dict (hardcoded, as shown in Technical Design)
  - `resolve_credentials()` reads `~/.archie/credentials.yaml`, maps via table, returns env dict
  - OAuth refresh logic reads/writes `~/.archie/credentials.yaml` directly
- Update `docker.py`:
  - Read `archie_repo` from config, mount at `/opt/archie` (read-write)
  - Mount `~/.archie/` read-write (no more `~/.agent-kit/` mount)
  - Remove `_read_ak_config()` and `_AK_CONFIG_PATH`
- Update `project.py` to read `project_dir` and `projects` from unified config
- Update brain client to read `brain_dir` from unified config
- Update entrypoint.sh to read from `~/.archie/config.yaml`
- Remove old `ak_config.py` (the renamed copy from M1)

Deliverable: Single config location at `~/.archie/`. No references to `~/.agent-kit/` in code.

Verify: `archie status` shows all config from `~/.archie/`. Container launches with correct env vars. `grep -r "agent-kit\|agent_kit" src/` returns only the migration function.

---

### 3. Simplify init and install

Approach:
- `archie init` creates config + credentials + brain in one step
- Hardcode "archie"/"simon" — remove `{{AGENT}}`/`{{USER}}` template placeholders
- `archie install` symlinks persona dirs to `~/.kiro/` paths (for local kiro-cli use)
- Make init idempotent: skip existing files, merge config additions

Tasks:
- Rewrite `archie init` command:
  - Create `~/.archie/config.yaml` (merge with existing if present)
  - Create `~/.archie/credentials.yaml` (empty structure if not present, 0600)
  - Create brain directory structure: `_archie/`, `_archie/memory/`, `_raw/`, `_inbox/`,
    `simon/`, `people/`, `projects/`, `knowledge/`
  - Deploy `persona/agents/archie.md` → `_archie/soul.md` (only if not present)
  - Deploy `persona/guidance/tools.md` → `_archie/tools.md` (only if not present)
  - Write `BRAIN.md` from template (hardcoded "archie"/"simon")
  - Write `simon/profile.md` from template
  - Init brain git repo + sqlite db (refs, provenance tables)
  - Skip all steps where target already exists
- Rewrite `archie install` command:
  - Symlink `<repo>/persona/skills` → `~/.kiro/skills`
  - Symlink `<repo>/persona/agents` → `~/.kiro/agents`
  - Symlink `<repo>/persona/prompts` → `~/.kiro/prompts`
  - Symlink `<repo>/persona/guidance` → `~/.kiro/steering`
  - Detect repo location from package metadata (editable install → source dir)
- Remove `{{USER}}`/`{{AGENT}}` placeholders from brain templates
- Remove old seed deployment logic from install
- Move `persona/seeds/tools.md` to `persona/guidance/tools.md`
- Remove `persona/seeds/` directory

Deliverable: `archie init` is the single setup command. `archie install` handles local kiro deployment.

Verify: Delete `~/.archie/`, run `archie init` → `archie status` shows green. Run `archie install` → `ls -la ~/.kiro/skills` shows symlink to repo.

---

### 4. Skill portability

Approach:
- Remove command references from skill instruction text (currently `ak` commands)
- Replace with intent-based language + "refer to `# Available Tools`"
- Fold tool-issues and tool-slack into workflow skills
- Update `persona/guidance/tools.md` to reference `archie` subcommands (the implementation layer)

Tasks:
- Fold tool-issues into workflow-implement:
  - Add "Post-start actions" section: update issue status if tracker configured, skip if not
  - Graceful degradation: issue operations are supportive, not blocking
- Fold tool-slack into workflow-review:
  - Add "Post-PR actions" section: notify slack channel, skip if unconfigured
- Delete `persona/skills/tool-issues/` and `persona/skills/tool-slack/`
- Update all skills that reference commands directly:
  - workflow-plan (3 `ak project` references)
  - workflow-implement (1 `ak project` reference)
  - action-brain-ingest (4 `ak brain` references)
  - action-memory-update (3 `ak brain` references)
  - action-assimilate (3 `ak brain` references)
  - action-self-review (2 `ak brain` references)
  - archie-add-capability (1 `ak notion` reference)
- Replace with intent language: "search your brain for..." / "determine project configuration..."
  followed by "(refer to `# Available Tools`)"
- Update `persona/guidance/tools.md` to document `archie` subcommands
- Update workflow-plan/references/ISSUE-FORMAT.md (references tool-issues)
- Update action-create-skill/references/LAYERS.md (uses tool-issues as example)

Deliverable: Skills are tool-agnostic in their instruction text. tools.md is the single implementation reference.

Verify: `grep -rP "\`ak |\`archie " persona/skills/` returns zero matches. Only `persona/guidance/tools.md` contains command references.

---

### 5. Prompt assembly and container workflow

Approach:
- Create `persona/agents/archie.md` with soul content + `@` directives at the end
- Rewrite entrypoint.sh to resolve `@` directives (line-by-line bash, as shown in Technical Design)
- Update container launch in `docker.py` to mount archie repo at `/opt/archie`
- `archie init` seeds `_archie/soul.md` from `persona/agents/archie.md` (already done in M3)
- Add `prompt.scripts` to config schema (already in DEFAULT_CONFIG from M2)

Tasks:
- Create `persona/agents/archie.md`:
  - Move content from `persona/seeds/soul.md` (the soul)
  - Add directive footer: `@agent brain.md`, `@agent memory.md`, `@script signals`,
    `@agent tools.md`, `@user profile.md`
- Rewrite `sandbox/entrypoint.sh`:
  - `uv tool install -e /opt/archie --quiet`
  - Symlink persona dirs from `/opt/archie/persona/` to `~/.kiro/`
  - Read `_archie/soul.md` from brain, process line-by-line resolving `@` directives
  - Write assembled output to `~/.kiro/prompts/archie.prompt.md`
  - Set terminal title, exec `$@`
- Update `docker.py` `run_container()`:
  - Read `archie_repo` from config
  - Add mount: `archie_repo` → `/opt/archie` (read-write)
  - Remove old persona mounts (no longer needed — entrypoint symlinks from /opt/archie)
- Remove `persona/seeds/soul.md` (content moved to `persona/agents/archie.md`)
- Verify `persona/seeds/` directory is empty and remove it

Deliverable: Container uses mounted repo directly. Entrypoint resolves `@` directives from brain's soul.md.

Verify: `archie build && archie --shell` → inside container: `cat ~/.kiro/prompts/archie.prompt.md` contains assembled prompt with all sections. `diff` against snapshot of current prompt output — same content, same order.

---

### 6. Cleanup and documentation

Approach:
- Remove `ak` alias from pyproject.toml
- Update all documentation
- Update brain-resident files to reference `archie` commands
- Add `plugin.json`
- Final test pass

Tasks:
- Remove `ak` entry point from pyproject.toml `[project.scripts]`
- Create `plugin.json` at repo root (list of skill paths for sharing/discovery)
- Update README.md (installation, commands, structure, relationship to brain)
- Update CONTRIBUTING.md (repo layout, dev workflow, architecture, adding skills,
  output design — document human vs agent command patterns, when to use Rich vs JSON,
  client class conventions, `@handle_errors` usage, adding new services)
- Update docs/ (vision, brain, capabilities, getting-started)
- Update `_archie/tools.md` in brain (`ak` → `archie` commands)
- Update `_archie/soul.md` in brain if it references `ak`
- Update `BRAIN.md` template (hardcoded paths)
- Grep for remaining references: `grep -r "agent.kit\|~/.agent-kit\|\bak " . --include="*.py" --include="*.md" --include="*.yaml" --include="*.sh"`
- Run full test suite

Deliverable: Clean, unified project with no legacy references.

Verify: Grep returns zero matches (excluding git history and this plan file). Full test suite passes. `archie init` on fresh system → `archie build` → `archie` launches successfully.

---

## Migration Notes

### Branch strategy
All work happens on a feature branch (`unify-archie` or similar). Main remains untouched
and fully functional throughout. Merge to main only after M5 is verified end-to-end
(container launches, prompt assembles correctly, all commands work).

### Transition period
Between M1 and M6, the `ak` alias exists in pyproject.toml. Brain-resident `_archie/tools.md`
still references `ak` commands until M6. Nothing breaks during incremental implementation.

### Container continuity
- M1-M2: Container still works with old entrypoint (reads from both config locations)
- M3-M4: Content changes only, container unaffected
- M5: Entrypoint rewritten — this is the switchover point. `archie build` required.
- M6: Cleanup only

### Git history
Prefer `git subtree merge` to bring agent-kit history into archie. If too complex,
a clean copy with a commit message crediting the source is acceptable — the agent-kit
repo remains available for historical reference.

### What gets deleted
- `~/.agent-kit/` directory (after M2 migration, user deletes manually when satisfied)
- `persona/seeds/` directory (M3/M5)
- `persona/skills/tool-issues/` and `persona/skills/tool-slack/` (M4)
- `ak` entry point (M6)
- `agent-kit/` subdirectory (manually, once everything is confirmed working)
