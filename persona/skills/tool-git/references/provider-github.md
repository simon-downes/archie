# GitHub Provider

GitHub-specific operations using the `gh` CLI. Refer to Available Tools for CLI details.

## Prerequisites

- GitHub CLI (`gh`) MUST be installed and authenticated
- MUST be working in a git repository with a GitHub remote

## Creating a Pull Request

**After making changes:**

```bash
# Push your branch
git push -u origin feature-branch

# Create PR with title and description
gh pr create --title "Add user authentication" --body "PLAT-123\n\nImplements JWT-based auth"

# Or use interactive mode
gh pr create
```

**PR conventions:**
- Title SHOULD be descriptive but concise
- Description MUST outline what changed and why
- SHOULD list issue identifiers at top of body
- No specific label or format requirements

**Issue references in PR body:**
- For external trackers (Linear, JIRA): place the issue key at the top of the body
- For GitHub Issues: use closing keywords to auto-close: `Closes #42`

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

# Approve
gh pr review <number> --approve

# Approve with feedback
gh pr review <number> --approve --body "Consider caching this result"

# Request changes
gh pr review <number> --request-changes --body "Please add error handling"

# Comment without approval
gh pr review <number> --comment --body "Have you considered the existing utility?"
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

**PR authors MUST merge their own PRs once approved** — do not merge unapproved PRs.

```bash
# Always use squash merge (project convention)
gh pr merge <number> --squash
```

**Before merging, verify:**
- PR has required approvals
- All checks have passed
- No unresolved conversations
- Repo rulesets satisfied

## CI/CD Integration

**All checks MUST pass before merge** (enforced by repo rulesets)

**If checks fail:**
- Grab output from failed check
- Debug and fix the issue
- Push fix and wait for checks to re-run
- MUST NOT merge with failing checks

## Common Commands

```bash
# List open PRs
gh pr list

# Your PRs
gh pr list --author @me

# PRs awaiting your review
gh pr list --search "review-requested:@me"

# Check PR status
gh pr checks <number>

# Find your PRs across all repos
gh search prs --author @me --state open
```

### Cross-Repository PR Queries

```bash
# Specific repos defined in steering file
gh search prs --review-requested @me --repo org/repo1 --repo org/repo2
```

**Note:** Team repository lists are defined in steering files.

## Quick Reference

```bash
# Create PR from current branch
git push -u origin feature-branch
gh pr create --fill

# Quick review
gh pr diff 123
gh pr review 123 --approve

# Merge approved PR
gh pr checks 123
gh pr merge 123 --squash
```
