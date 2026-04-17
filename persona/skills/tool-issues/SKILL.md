---
name: tool-issues
description: >
  Generic interface for issue tracking operations with provider-specific references.
  Covers listing, creating, updating, commenting on, and transitioning issues. Dispatches
  to the correct provider (Linear, GitHub Issues) based on project config. Use when working
  with issues, tickets, or tasks in any tracker.
---

# Purpose

Provide a consistent interface for issue tracking operations across providers. The skill
defines what operations are available; provider references define the semantics and structure
for each provider; Available Tools provides the actual CLI commands.

---

# When to Use

- Creating, updating, or querying issues
- Transitioning issue status (e.g. "In Progress", "In Review")
- Adding comments to issues
- Loading a plan from an issue description
- Any workflow step that interacts with an issue tracker

# When Not to Use

- When no issue tracker is configured (check project config first)
- For operations that don't involve issue tracking

---

# Provider Dispatch

1. Use `ak project --config` to resolve the current project's config
2. Read `brain.issues.provider` from the output
3. Load `references/provider-<name>.md` for the matching provider
4. Pass provider-specific settings (e.g. `brain.issues.team`) to the operations
5. If no issues config exists, skip issue operations silently — this is not an error

## Available Providers

| Provider | Reference | Config key |
|----------|-----------|------------|
| Linear   | [provider-linear.md](references/provider-linear.md) | `linear` |
| GitHub   | [provider-github.md](references/provider-github.md) | `github` |

---

# Operations

These are the generic operations. Each provider reference maps them to provider-specific
semantics and field names. Refer to Available Tools for the actual CLI commands.

## List Issues

Retrieve issues matching filters. Common filters: status, assignee, label, project.

**Config inputs:** `issues.team` (if the provider uses team/project scoping)

## Get Issue

Fetch a single issue by identifier. Returns title, description, status, assignee, and
comments. Used to load plans stored in issue descriptions.

## Create Issue

Create a new issue with title and description. Optionally set status, assignee, priority,
and labels.

**Config inputs:** `issues.team` (target team/project for the new issue)

## Update Issue

Modify an existing issue's fields: title, description, status, assignee, priority, labels.
Most commonly used for status transitions during workflows.

**Common transitions:**
- Start of implementation → "In Progress"
- Implementation complete → "In Review"

## Comment

Add a comment to an issue. Used for progress updates and review feedback.

## Status Transition

A specialised form of update that changes only the issue status. Provider references
document the available statuses and any constraints on transitions.

---

# Graceful Handling

| Condition                          | Behaviour                           |
|------------------------------------|-------------------------------------|
| No issues config in project config | Skip all issue operations silently  |
| Unknown provider                   | Warn and skip issue operations      |
| CLI tool unavailable               | Warn and continue without tracking  |
| API call fails                     | Warn and continue                   |

Issue tracking is supportive, not blocking. Workflow progress MUST NOT be blocked by
issue tracker failures.
