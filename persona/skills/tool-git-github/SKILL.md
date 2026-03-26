---
name: tool-git-github
description: Git and GitHub workflows for version control and pull requests. Use when working with git operations, branches, commits, or GitHub PRs.
---

# Git and GitHub Workflows

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in RFC 2119.

## Scope

This document defines git version control workflows and GitHub pull request operations, following project conventions.

Git workflows (branching, syncing, rebasing) follow standard patterns. GitHub PR workflows follow project conventions. Team repository lists for cross-repo queries are defined in steering files.

## Prerequisites

- Git MUST be installed and configured
- GitHub CLI (`gh`) MUST be installed and authenticated
- MUST be working in a git repository with GitHub remote

## Workflow Model

**Trunk-based development:**
- Branch from `main`
- Create PR to `main` on completion
- Squash merge via GitHub (not local)

Unless steering file specifies otherwise, always use trunk-based workflow.

## JIRA Integration

**Branch naming includes JIRA key:**

**Format:** `<user>/<JIRA-KEY>-<description>`

**Rules:**
- JIRA issue key MUST be UPPERCASE
- Description MUST be lowercase with hyphens
- User prefix SHOULD be your GitHub username

**Examples:**
```
simon/PLAT-123-add-user-auth
simon/PLAT-456-fix-memory-leak
```

**PR body SHOULD list related JIRA tickets at the top:**

```
JIRA: PLAT-123, PLAT-124

[rest of PR description]
```

## Git Workflows

### Commit Messages

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

**Note:** Some repos enforce conventional commits via CI checks. Using this format consistently avoids issues.

### Syncing with Origin

**Standard sync workflow:**

```bash
git stash
git pull
git stash pop
```

### Updating Feature Branch

**Rebase feature branch on latest main:**

```bash
# Save your work
git stash  # or commit if ready

# Update main
git checkout main
git pull

# Rebase feature branch
git checkout feature-branch
git rebase main

# Push rebased branch (required after rebase)
git push --force-with-lease

# Restore stashed work if needed
git stash pop
```

### Branch Cleanup

**Clean up merged local branches:**

```bash
# List merged branches (safe to delete)
git branch --merged main | grep -v "main"

# Delete merged local branches
git branch --merged main | grep -v "main" | xargs git branch -d

# Prune remote tracking branches
git fetch --prune
```

**SHOULD clean up branches regularly to avoid clutter.**

### Branch Lifecycle

**Syncing with main:**
- SHOULD sync daily to minimize conflicts
- Use rebase workflow (see "Updating Feature Branch")

**Branch deletion:**
- Typically handled automatically by repo rulesets after merge
- Check repo settings if unsure

### Conflict Resolution

**During rebase conflicts:**
- Resolve independently if straightforward
- Ask for help if:
  - Complex conflicts across multiple files
  - Risk of breaking functionality
  - Uncertain about correct resolution

## GitHub Workflows

### Creating a Pull Request

**After making changes:**

```bash
# Push your branch
git push -u origin feature-branch

# Create PR with title and description
gh pr create --title "Add user authentication" --body "JIRA: PLAT-123\n\nImplements JWT-based auth with password hashing and session management"

# Or use interactive mode (prompts for title, body, etc.)
gh pr create
```

**PR conventions:**
- Title SHOULD be descriptive but concise
- Description MUST outline what changed and why
- SHOULD list JIRA tickets at top of body
- No specific label or format requirements

**Draft PRs:**
- Default to regular PRs unless explicitly requested to create draft
- Use draft PRs when seeking input from team members on work in progress
- Mark ready for review when all checks passing and ready for formal review

## Reviewing a Pull Request

**Review workflow:**

```bash
# View PR details
gh pr view <number>

# View PR diff without checking out
gh pr diff <number>

# Check out PR locally to test (optional)
gh pr checkout <number>

# Approve (no comment needed unless providing feedback)
gh pr review <number> --approve

# Approve with relevant feedback (not blockers)
gh pr review <number> --approve --body "Consider caching this result for better performance"

# Request changes with specific feedback
gh pr review <number> --request-changes --body "Please add error handling for invalid input"

# Comment without approval (for questions or non-blocking suggestions)
gh pr review <number> --comment --body "Have you considered using the existing utility function for this?"
```

**Review conventions:**
- SHOULD use `gh pr diff` to review changes without checking out
- SHOULD check out locally only if you need to test/run the code
- SHOULD approve without comment if no feedback needed
- SHOULD add comments only when providing relevant (non-blocking) feedback
- MUST NOT add "LGTM" or similar approval-only comments

**Reviewer selection:**
- Check for `CODEOWNERS` or `.github/CODEOWNERS` file (defines required reviewers)
- GitHub automatically requests these reviewers when PR is created
- If no CODEOWNERS, request team review

**Handling feedback:**
- New commits dismiss existing review comments (repo rulesets enforce this)
- Create new commits addressing feedback rather than amending

## Merging Pull Requests

**PR authors MUST merge their own PRs once approved** - Do not merge unapproved PRs.

**When merging your approved PR:**

```bash
# Always use squash merge (project convention)
gh pr merge <number> --squash

# Branches are automatically deleted on merge (no --delete-branch needed)
```

**Before merging, verify:**
- PR has required approvals
- All checks have passed
- No unresolved conversations

**Ready to merge when:**
- All required approvals received (check CODEOWNERS)
- All CI checks passing
- No unresolved conversations
- Repo rulesets satisfied

## CI/CD Integration

**All checks MUST pass before merge** (enforced by repo rulesets)

**If checks fail:**
- Grab output from failed check
- Debug and fix the issue
- Push fix and wait for checks to re-run
- MUST NOT merge with failing checks

**Pre-push validations:**
- Some repos may add pre-push hooks in future
- Follow any validation requirements specified in repo documentation

## Common Commands

**List PRs:**

```bash
# Open PRs
gh pr list

# Your PRs
gh pr list --author @me

# PRs awaiting your review
gh pr list --search "review-requested:@me"
```

**Check PR status:**

```bash
# View status checks
gh pr checks <number>
```

### Cross-Repository PR Queries

**Find your PRs across all repos:**

```bash
gh search prs --author @me --state open
```

**Find PRs awaiting your review across team repos:**

```bash
# Specific repos defined in steering file
gh search prs --review-requested @me --repo org/repo1 --repo org/repo2 --repo org/repo3
```

**Note:** Team repository lists are defined in steering files.

## Quick Reference

**Create PR from current branch:**
```bash
git push -u origin feature-branch
gh pr create --fill  # Uses commit messages for title/body
```

**Quick review:**
```bash
gh pr diff 123
gh pr review 123 --approve
```

**Merge approved PR:**
```bash
gh pr checks 123  # Verify checks passed
gh pr merge 123 --squash
```
