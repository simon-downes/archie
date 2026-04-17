---
name: tool-slack
description: >
  Send Slack notifications for pull requests based on project config. Posts a message
  when a PR is created if Slack is configured for the project. No-op when unconfigured.
  Use after creating a pull request to notify the team.
---

# Purpose

Notify a Slack channel when a pull request is created, if the project has Slack configured.

---

# When to Use

- After creating a pull request (typically at the end of workflow-review)

# When Not to Use

- For general messaging or alerts unrelated to PRs
- When Slack is not configured for the project (the skill handles this — just call it)

---

# Workflow

## 1. Check config

Use `ak project --config` to resolve the current project's config. Check `brain.slack`.

If `brain.slack` is not `true`, stop — no notification needed. This is not an error.

## 2. Send notification

Post a single-line message with the PR title and link using mrkdwn format.

Refer to Available Tools for the Slack CLI command.

**Message format:**
```
<PR title> <<url>|#<number>>
```

**Example:**
```
Add user authentication <https://github.com/acme-corp/platform/pull/42|#42>
```

No headers, no blocks, no fields — just a single line of text.

---

# Graceful Handling

| Condition                    | Behaviour          |
|------------------------------|--------------------|
| `brain.slack` not true       | Skip silently      |
| Webhook not configured       | Skip silently      |
| Message send fails           | Warn and continue  |

Slack notifications are informational. Workflow progress MUST NOT be blocked by
notification failures.
