# Org-Aware Agentic Workflows

## Problem

Agentic workflows (skills, agents, prompts) need to interact with org/project-specific tooling — issue trackers, source control, Slack, naming conventions — without hardcoding provider-specific logic into the core workflow.

## Solution: Layered Config + Provider Adapters

### Org Config File

Store org-level defaults in a central config file (`~/.kiro/orgs.yaml`), keyed by org name. Per-project overrides only where needed.

```yaml
orgs:
  my-org:
    source:
      provider: github
      base_url: github.com/my-org
      branches: "{type}/{issue_key}-{description}"
    issues:
      provider: linear
    slack:
      webhook: https://hooks.slack.com/xxx

projects:
  my-org/my-project:
    issues:
      project: PLAT
```

### Config Resolution

1. Detect org from git remote: `git remote get-url origin | sed 's|.*[:/]\([^/]*\)/[^/]*$|\1|'`
2. Look up org profile in `~/.kiro/orgs.yaml`
3. Merge any project-level overrides on top using `yq`:
   ```bash
   yq ".orgs.\"$org\" * (.projects.\"$org/$project\" // {})" ~/.kiro/orgs.yaml
   ```

### Skill Structure: Single Skill, Provider Reference Files

Keep one skill per domain with separate reference files for each provider:

```
skills/
  tool-project-config/        # resolves org + project config from git remote
  tool-git/
    SKILL.md                  # core git ops + provider dispatch
    references/
      provider-github.md      # gh CLI: PRs, reviews, actions
      provider-bitbucket.md   # Bitbucket API: PRs, pipelines
  tool-issues/
    SKILL.md                  # common interface: get, create, transition, comment
    references/
      provider-linear.md      # Linear GraphQL API
      provider-jira.md        # Jira REST API
      provider-github.md      # GitHub Issues
```

Each `SKILL.md` detects the provider from the resolved config and loads the matching reference file. Pure git operations (branch, commit, push) live in the main skill — only platform-specific features (PRs, CI checks) go in reference files.

### Workflow Skills Stay Generic

Workflows reference tool skills by name, never by provider:

```markdown
1. Use `tool-project-config` to resolve the org/project config
2. Use `tool-issues` to fetch issue details
3. Use `tool-git` to create a branch following the config's pattern
4. ... implementation ...
5. Use `tool-git` to create a PR
6. Use `tool-issues` to transition the issue status
7. If `slack.webhook` is set, post a notification
```

The same workflow works across GitHub+Linear, Bitbucket+Jira, or any other combination — driven entirely by the org config.

## Key Principles

- **Structured config over prose** — machine-readable YAML, not ambiguous instructions
- **Org-level defaults, project-level overrides** — most projects need zero config
- **Skills dispatch on config values** — provider logic lives in reference files, not workflows
- **Adding a new provider = one reference file** — no changes to workflows or core skills
