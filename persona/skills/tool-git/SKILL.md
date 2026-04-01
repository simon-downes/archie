---
name: tool-git
description: >
  Git version control workflows and source provider operations. Covers branching, commits,
  syncing, rebasing, and provider-specific operations (PRs, reviews, CI) via dispatch to
  provider references. Use when working with git operations, branches, commits, or pull requests.
---

# Git Workflows

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED,
MAY, and OPTIONAL in this document are to be interpreted as described in RFC 2119.

## Scope

Core git version control workflows (branching, commits, syncing, rebasing) and dispatch to
provider-specific operations (PRs, reviews, CI) based on project config.

## Prerequisites

- Git MUST be installed and configured
- MUST be working in a git repository

## Workflow Model

**Trunk-based development:**
- Branch from `main`
- Create PR to `main` on completion
- Squash merge via the source provider (not local)

Unless steering file specifies otherwise, always use trunk-based workflow.

## Issue Integration

**Branch naming includes issue key:**

**Format:** `<user>/<ISSUE-KEY>-<description>`

**Rules:**
- Issue key MUST match the tracker's format (e.g. PLAT-123 for Linear/JIRA, 42 for GitHub)
- Description MUST be lowercase with hyphens
- User prefix SHOULD be your source provider username

**Examples:**
```
simon/PLAT-123-add-user-auth       # Linear or JIRA
simon/42-fix-memory-leak            # GitHub Issues
```

**PR body SHOULD reference related issues at the top.**

## Commit Messages

**MUST use conventional commit format unless repo documentation specifies otherwise:**

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks
- `major:` - Breaking changes

**Examples:**
```
feat: add user authentication endpoint
fix: resolve memory leak in event processor
docs: update API documentation for v2
refactor: extract validation logic to separate module
```

**Note:** Some repos enforce conventional commits via CI checks. Using this format
consistently avoids issues.

## Syncing with Origin

**Standard sync workflow:**

```bash
git stash
git pull
git stash pop
```

## Updating Feature Branch

**Rebase feature branch on latest main:**

```bash
git stash  # or commit if ready
git checkout main
git pull
git checkout feature-branch
git rebase main
git push --force-with-lease
git stash pop  # if needed
```

## Branch Cleanup

**Clean up merged local branches:**

```bash
git branch --merged main | grep -v "main" | xargs git branch -d
git fetch --prune
```

**SHOULD clean up branches regularly to avoid clutter.**

## Branch Lifecycle

**Syncing with main:**
- SHOULD sync daily to minimize conflicts
- Use rebase workflow (see "Updating Feature Branch")

**Branch deletion:**
- Typically handled automatically by repo rulesets after merge
- Check repo settings if unsure

## Conflict Resolution

**During rebase conflicts:**
- Resolve independently if straightforward
- Ask for help if:
  - Complex conflicts across multiple files
  - Risk of breaking functionality
  - Uncertain about correct resolution

---

# Source Provider Operations

Provider-specific operations (pull requests, reviews, CI, merging) are defined in
provider reference files.

## Dispatch

1. Use `tool-project-config` to resolve the current project's config
2. Read `source.provider` from the config
3. Load `references/provider-<name>.md` for the matching provider
4. If no config or no source provider is set, check the git remote URL to infer the
   provider (e.g. `github.com` → github)
5. If the provider cannot be determined, warn and skip provider-specific operations

## Available Providers

| Provider | Reference | Remote pattern |
|----------|-----------|----------------|
| GitHub   | [provider-github.md](references/provider-github.md) | `github.com` |
