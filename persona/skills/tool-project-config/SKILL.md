---
name: tool-project-config
description: >
  Resolve org and project configuration from the git remote. Provides project-level
  settings for source control, issue tracking, Slack notifications, and other conventions.
  Use when you need to determine which provider or settings apply to the current project,
  before performing git operations, issue tracking, or sending notifications.
---

# Purpose

Resolve the current project's configuration from `~/.archie/projects.yaml` based on the
git remote origin. Other skills consume this config to dispatch to the correct provider
and apply org/project-specific settings.

---

# When to Use

- Before performing provider-specific operations (PRs, issues, notifications)
- When a skill needs to know which source provider, issue tracker, or Slack config applies
- At the start of a workflow that involves multiple provider-dependent steps

# When Not to Use

- When working outside a git repository
- For operations that don't depend on org/project context

---

# Config File

Location: `~/.archie/projects.yaml`

## Schema

```yaml
orgs:
  <org-name>:
    source:
      provider: <github|bitbucket>    # source control platform
    issues:
      provider: <linear|github>       # issue tracker
      team: <team-key>                # provider-specific default (e.g. Linear team key)
    slack:
      webhook_env: <ENV_VAR_NAME>     # env var holding the webhook URL

projects:
  <org-name>/<project-name>:          # optional per-project overrides
    issues:
      team: <team-key>                # override org default
    # any org-level key can be overridden here
```

## Sections

| Section  | Purpose                              | Required |
|----------|--------------------------------------|----------|
| `source` | Source control provider               | No       |
| `issues` | Issue tracker provider and settings   | No       |
| `slack`  | Slack notification configuration      | No       |

All sections are optional. Missing sections mean that capability is not configured
for the org/project — consuming skills should treat this as a no-op.

## Example

```yaml
orgs:
  acme-corp:
    source:
      provider: github
    issues:
      provider: linear
      team: PLAT
    slack:
      webhook_env: SLACK_WEBHOOK_URL

  personal-org:
    source:
      provider: github

projects:
  acme-corp/infrastructure:
    issues:
      team: INFRA
```

---

# Resolution Workflow

## 1. Extract org and project from git remote

```bash
git remote get-url origin | sed 's|.*[:/]\([^/]*\)/\([^/.]*\).*|\1 \2|'
```

This handles both SSH (`git@github.com:org/repo.git`) and HTTPS
(`https://github.com/org/repo.git`) formats. Output: `<org> <project>`.

If not in a git repository or no origin remote exists, stop — no config to resolve.

## 2. Look up org config

```bash
ORG="<org>"
PROJECT="<project>"
CONFIG=~/.archie/projects.yaml

yq ".orgs.\"${ORG}\"" "$CONFIG"
```

If the org is not found or the config file doesn't exist, return empty config.
This is not an error — it means no org-specific settings apply.

## 3. Merge project overrides

```bash
yq ".orgs.\"${ORG}\" * (.projects.\"${ORG}/${PROJECT}\" // {})" "$CONFIG"
```

Project-level keys override org-level keys. Sections not overridden are inherited
from the org config.

## 4. Return merged config

The output is the merged YAML for the current project. Example output for
`acme-corp/infrastructure`:

```yaml
source:
  provider: github
issues:
  provider: linear
  team: INFRA
slack:
  webhook_env: SLACK_WEBHOOK_URL
```

---

# Graceful Handling

| Condition                        | Behaviour                              |
|----------------------------------|----------------------------------------|
| Not in a git repository          | No config — skip provider operations   |
| No origin remote                 | No config — skip provider operations   |
| Config file doesn't exist        | No config — skip provider operations   |
| Org not found in config          | No config — skip provider operations   |
| Section missing (e.g. no slack)  | That capability is unconfigured — no-op|

Skills consuming this config MUST handle missing sections gracefully. A missing section
means "not configured" — not an error.

---

# Example: Full Resolution

**Config file** (`~/.archie/projects.yaml`):
```yaml
orgs:
  acme-corp:
    source:
      provider: github
    issues:
      provider: linear
      team: PLAT
    slack:
      webhook_env: SLACK_WEBHOOK_URL

projects:
  acme-corp/infrastructure:
    issues:
      team: INFRA
```

**Git remote:** `git@github.com:acme-corp/infrastructure.git`

**Resolution:**
```bash
# Step 1: Extract org and project
git remote get-url origin | sed 's|.*[:/]\([^/]*\)/\([^/.]*\).*|\1 \2|'
# Output: acme-corp infrastructure

# Step 2+3: Look up and merge
yq '.orgs."acme-corp" * (.projects."acme-corp/infrastructure" // {})' ~/.archie/projects.yaml
```

**Result:**
```yaml
source:
  provider: github
issues:
  provider: linear
  team: INFRA
slack:
  webhook_env: SLACK_WEBHOOK_URL
```

Note: `issues.team` is `INFRA` (project override) not `PLAT` (org default).
