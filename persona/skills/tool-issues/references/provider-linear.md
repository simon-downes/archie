# Linear Provider

Linear issue tracking via the Linear CLI. Refer to Available Tools for CLI details.

## Config

| Config key     | Usage                                    |
|----------------|------------------------------------------|
| `issues.team`  | Team key (e.g. `PLAT`) — required for most operations |

## Issue Identifiers

Linear uses `<TEAM>-<NUMBER>` format (e.g. `PLAT-123`).

## Operations

### List Issues

Filter by team (required), optionally by status, assignee, label, or project.

### Get Issue

Fetch by identifier (e.g. `PLAT-123`). Returns full detail including description
and comments. The description field contains the plan when issues are used for
plan storage.

### Create Issue

Requires team and title. Optional: description, status, assignee, priority, labels.

For plan storage, pipe the plan content as the description via stdin.

### Update Issue

Update by identifier. Any field can be updated independently.

**Status transitions:** use the status name directly (e.g. "In Progress", "In Review",
"Done"). The CLI resolves names to IDs automatically.

### Comment

Add a comment by identifier. Provide the message body.

### Upload

Files can be uploaded and the resulting URL embedded in descriptions or comments.

## Status Model

Linear uses customisable workflow states per team. Common states:

- Backlog
- Ready (or "Todo")
- In Progress
- In Review
- Done
- Cancelled

Use the team's actual state names. Refer to Available Tools to discover available
states for a team.
