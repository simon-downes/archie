# Org-Aware Agentic Workflows

## Objective

Decouple skills from specific providers (GitHub, Linear, Slack) so the same workflows work
across different organisations and tooling. Introduce a project config system that captures
org/project-level settings (source provider, issue tracker, Slack webhooks, conventions) and
refactor existing skills to dispatch on config rather than hardcoding providers.

The result: workflows remain generic, tool skills load provider-specific references based on
config, and adding a new provider means adding a reference file — not changing workflows.

## Requirements

- MUST introduce a project config file (`~/.archie/projects.yaml`) that maps org/project to
  provider settings and conventions
  - AC: Config is keyed by org with optional per-project overrides
  - AC: Config covers source provider, issue tracker, Slack, and extensible for future needs

- MUST create a `tool-project-config` skill that resolves the current project's config from
  the git remote
  - AC: Detects org and project from `git remote get-url origin`
  - AC: Merges org defaults with project-level overrides
  - AC: Returns structured config that other skills can consume
  - AC: Returns empty/null sections gracefully when no config exists for the current project

- MUST refactor `tool-git-github` into `tool-git` with GitHub-specific content in a
  provider reference file
  - AC: Core git operations (branch, commit, sync, rebase) remain in SKILL.md
  - AC: GitHub PR workflows move to `references/provider-github.md`
  - AC: Skill dispatches to the correct provider reference based on project config
  - AC: Existing behaviour is preserved for GitHub projects

- MUST create a `tool-issues` skill that provides a generic interface for issue tracking
  with provider-specific references
  - AC: Covers list, create, update, comment, and status transition operations
  - AC: Provider references map generic operations to CLI commands (e.g. `ak linear`, `gh issue`)
  - AC: Org/project-specific settings (team key, project name) come from project config
  - AC: Works without config — gracefully degrades (warns and continues)

- MUST create a `tool-slack` skill for sending PR notifications based on project config
  - AC: Sends a message via `ak slack send` when a PR is created and Slack is configured
  - AC: Message is a single line: PR title and link, no headers or blocks
  - AC: No-op when Slack is not configured — no errors, no warnings

- MUST update workflow skills (`workflow-implement`, `workflow-plan`, `workflow-review`) to
  use the new tool skills instead of directly referencing GitHub/Linear
  - AC: Workflows reference `tool-git`, `tool-issues`, `tool-slack` by name
  - AC: No provider-specific commands appear in workflow skills
  - AC: Existing workflow behaviour is preserved

- SHOULD update `action-create-skill` references to use `tool-git` instead of `tool-git-github`
  in examples
  - AC: LAYERS.md examples reference the new skill name

- SHOULD keep the project config schema simple and flat — avoid deep nesting
  - AC: Org-level config fits in ~10 lines of YAML per org

## Technical Design

### Project Config Schema

```yaml
orgs:
  my-org:
    source:
      provider: github           # github | bitbucket (future)
    issues:
      provider: linear           # linear | github | jira (future)
      team: PLAT                 # provider-specific default
    slack:
      webhook_env: SLACK_WEBHOOK_URL  # env var name holding the webhook URL

projects:
  my-org/special-project:
    issues:
      team: INFRA                # override org default
```

Config lives at `~/.archie/projects.yaml`. This is a new file — not part of Archie's
`config.yaml` (which is container/credential config, not agent behaviour config).

### Config Resolution

`tool-project-config` resolves config by:
1. Parsing `git remote get-url origin` to extract org and project name
2. Looking up `orgs.<org>` in `~/.archie/projects.yaml`
3. Merging `projects.<org>/<project>` overrides on top
4. Returning the merged config (or empty sections if no match)

The skill provides shell commands for resolution — no Python code needed. Skills that
consume config run these commands and parse the output.

### Skill Structure

```
skills/
  tool-project-config/
    SKILL.md                    # config resolution from git remote

  tool-git/
    SKILL.md                    # core git ops + provider dispatch
    references/
      provider-github.md        # GitHub: PRs, reviews, CI via gh CLI

  tool-issues/
    SKILL.md                    # generic issue interface
    references/
      provider-linear.md        # Linear: ak linear CLI commands
      provider-github.md        # GitHub Issues: gh issue CLI commands

  tool-slack/
    SKILL.md                    # notification patterns via ak slack

  (existing workflow skills updated to reference above)
```

### Provider Dispatch Pattern

Each tool skill follows the same pattern:
1. Instruct the agent to use `tool-project-config` to resolve config
2. Read the relevant config section (e.g. `source.provider`, `issues.provider`)
3. Load the matching `references/provider-<name>.md`
4. If no config or unknown provider, warn and skip provider-specific operations

### Workflow Updates

Workflows currently reference `tool-git-github` by name and use `gh` commands directly
in some places. Changes:

- `workflow-implement`: replace `tool-git-github` references with `tool-git`, replace
  direct issue tracker references with `tool-issues`, add Slack notification on completion
- `workflow-plan`: replace issue tracker assumptions with `tool-issues` dispatch, use
  `tool-project-config` for tracker discovery
- `workflow-review`: replace `gh pr` references with `tool-git` provider dispatch, replace
  issue status references with `tool-issues`

## Milestones

### 1. Project config skill

Approach:
- Create `tool-project-config` skill with config schema and resolution workflow
- Config file is `~/.archie/projects.yaml` — agent reads it via `yq`
- Resolution pipeline: `git remote get-url origin` → extract org/project with
  `sed 's|.*[:/]\([^/]*\)/\([^/.]*\).*|\1 \2|'` → look up `orgs.<org>` → merge
  `projects.<org>/<project>` overrides using `yq '.orgs."ORG" * (.projects."ORG/PROJECT" // {})'`
- Output is the merged config for the current project as YAML
- Shell-based resolution using `git`, `yq` — both available in the sandbox, no fallback needed
- Include the config schema definition in the skill so agents know the structure

Tasks:
- Define the config schema in SKILL.md with all supported sections
- Write the resolution workflow (git remote → org lookup → project merge)
- Include examples of config files and resolution output
- Document graceful handling when no config exists

Deliverable: `tool-project-config` skill that resolves org/project config from git remote
Verify: Skill file exists with schema, resolution workflow, and examples

### 2. Refactor git skill

Approach:
- Rename `tool-git-github` to `tool-git`
- Extract GitHub-specific content (PR creation, review, merge, CI, cross-repo queries)
  into `references/provider-github.md`
- Keep core git operations in SKILL.md (branching, commits, sync, rebase, cleanup)
- Add provider dispatch: skill instructs agent to check `source.provider` from project
  config and load the matching reference
- Branch naming and commit conventions stay in the main skill (they're provider-agnostic)
- Issue key integration in branch names stays in main skill (format is universal)

Tasks:
- Create `tool-git/SKILL.md` with core git operations and provider dispatch section
- Create `tool-git/references/provider-github.md` with all GitHub-specific content
- Delete `tool-git-github/` directory
- Update `action-create-skill/references/LAYERS.md` examples
- Update `policy-lang-terraform/SKILL.md` reference from `tool-git-github` to `tool-git`

Deliverable: `tool-git` skill with GitHub content in a provider reference
Verify: No GitHub-specific commands in SKILL.md; all GitHub content in provider-github.md

### 3. Issues skill

Approach:
- Create `tool-issues` with a generic interface covering: list, get, create, update,
  comment, and status transitions
- Provider references map each operation to specific CLI commands
- `provider-linear.md` uses `ak linear` commands
- `provider-github.md` uses `gh issue` commands
- Org/project-specific settings (team key, project name) come from project config
  resolved via `tool-project-config`
- Skill instructs agent to check `issues.provider` from config and load the matching
  reference, passing through config values (e.g. team key) as parameters
- Provider references define the structure and semantics for each provider (field names,
  status models, issue structure) and defer to "Available Tools" for actual CLI invocation
- This keeps skills decoupled from specific CLI tooling — users with different tools
  (MCP servers, native CLIs) only need to update TOOLS.md

Tasks:
- Create `tool-issues/SKILL.md` with generic interface and provider dispatch
- Create `tool-issues/references/provider-linear.md` with `ak linear` mappings
- Create `tool-issues/references/provider-github.md` with `gh issue` mappings
- Include examples showing config-driven dispatch

Deliverable: `tool-issues` skill with Linear and GitHub Issues provider references
Verify: Skill covers all operations; each provider reference maps to concrete CLI commands

### 4. Slack skill

Approach:
- Create `tool-slack` for notifying about raised PRs via `ak slack send`
- Skill checks project config for `slack.webhook_env` — if not set, skip silently
- Single use case: after a PR is created, send a one-line message with title and link
- Message format: `"PR title <url|#number>"` — plain mrkdwn, no headers or blocks
- The webhook URL comes from the env var named in config (typically `SLACK_WEBHOOK_URL`)
- Skill defers to "Available Tools" for the actual `ak slack send` invocation

Tasks:
- Create `tool-slack/SKILL.md` with PR notification pattern and config check
- Document no-op behaviour when unconfigured

Deliverable: `tool-slack` skill that sends a PR notification when Slack is configured
Verify: Skill file exists with PR notification pattern, config check, and no-op documentation

### 5. Update workflow skills

Approach:
- Update all three workflow skills to use the new tool skills
- Replace direct `tool-git-github` references with `tool-git`
- Replace direct issue tracker references/assumptions with `tool-issues`
- Add `tool-slack` notifications at appropriate points
- Workflows should instruct the agent to resolve project config once at the start
  (via `tool-project-config`) and pass relevant sections to tool skills
- Keep changes minimal — only replace provider-specific references, don't restructure
  the workflows themselves
- Update `workflow-plan/references/ISSUE-FORMAT.md` to reference `tool-issues`

Tasks:
- Update `workflow-implement/SKILL.md`: replace git/issue references
- Update `workflow-plan/SKILL.md`: replace tracker discovery with `tool-project-config` +
  `tool-issues`, update Phase 1 investigation and Phase 4 persistence
- Update `workflow-review/SKILL.md`: replace `gh pr` references with `tool-git` dispatch,
  replace issue status references with `tool-issues`
- Update `workflow-plan/references/ISSUE-FORMAT.md` to reference `tool-issues`

Deliverable: Workflow skills reference tool skills generically, no provider-specific commands
Verify: No `gh pr`, `gh issue`, `ak linear`, or `tool-git-github` references in workflow skills
