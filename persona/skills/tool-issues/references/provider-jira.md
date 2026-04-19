# Jira Provider

Jira Cloud issue tracking via the Jira CLI. Refer to Available Tools for CLI details.

## Config

| Config key       | Usage                                    |
|------------------|------------------------------------------|
| `issues.project` | Project key (e.g. `PLAT`) — used for default project scoping |

## Issue Identifiers

Jira uses `<PROJECT>-<NUMBER>` format (e.g. `PLAT-123`).

## Operations

### List Issues

Filter by project, optionally by status, assignee, issue type, or label. Filters are
composed into JQL. Use `--jql` for complex queries.

### Get Issue

Fetch by key (e.g. `PLAT-123`). Returns full detail including description and comments.
The description field contains the plan when issues are used for plan storage.

### Create Issue

Requires project, summary, and issue type. Optional: description, priority, assignee, labels.

For plan storage, pipe the plan content as the description via stdin.

### Update Issue

Update by key. Summary, description, priority, assignee, and labels can be updated.

**Status transitions:** use the `transition` command, not `update-issue`. Jira status
changes go through workflow transitions — the available transitions depend on the issue's
current state. Use `ak jira statuses <project>` to discover available statuses.

### Comment

Add a comment by key. Provide the message body.

### Attach

Files can be attached directly to issues.

## Status Model

Jira uses customisable workflows per project and issue type. Common statuses:

- To Do
- In Progress
- In Review
- Done

Use the project's actual status names. Refer to Available Tools to discover available
statuses for a project. Note that available transitions depend on the current status —
not all statuses are reachable from every state.
