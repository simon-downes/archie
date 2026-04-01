# GitHub Issues Provider

GitHub Issues via the GitHub CLI. Refer to Available Tools for CLI details.

## Config

GitHub Issues does not require additional config beyond `issues.provider: github`.
Issues are scoped to the current repository automatically.

## Issue Identifiers

GitHub uses `#<number>` format (e.g. `#42`). The number is repository-scoped.

## Operations

### List Issues

Filter by state (open/closed), assignee, label, or milestone.

### Get Issue

Fetch by number. Returns title, body, status, assignee, labels, and comments.
The body field contains the plan when issues are used for plan storage.

### Create Issue

Requires title. Optional: body, assignee, labels, milestone.

For plan storage, pipe the plan content as the body via stdin.

### Update Issue

Update by number. Fields: title, body, state, assignee, labels, milestone.

**Status transitions:** GitHub Issues has two states: `open` and `closed`.
For workflow tracking, use labels to indicate progress (e.g. "in-progress",
"in-review") or rely on PR linking for status.

### Comment

Add a comment by issue number. Provide the message body.

## PR Integration

GitHub Issues can be auto-closed by PRs using closing keywords in the PR body:

```
Closes #42
Fixes #42
Resolves #42
```

This is the preferred way to transition issues to "done" on GitHub.

## Status Model

GitHub Issues has only two native states: `open` and `closed`. Richer workflow
states are typically modelled with labels. Check the repository's existing label
conventions before creating new ones.
