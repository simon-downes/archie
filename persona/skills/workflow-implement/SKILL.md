---
name: workflow-implement
description: >
  Execute approved implementation plans through milestone-based workflow with progress
  tracking. Use when implementing approved plans from local plan files or issue tracker.
---

# Purpose

Execute approved plans by working through milestones sequentially.

---

# When to Use

- User approves a plan and requests implementation
- Executing milestones from `./plans/<NNN>-<description>.md`

# When Not to Use

- Work that doesn't have an approved plan (use workflow-plan first)
- Reviewing completed work (use workflow-review)

---

# Workflow

## 1. Load Plan

The plan source depends on how it was created:

**From issue tracker:** the user provides an issue identifier (e.g. "implement PLAT-123").
Fetch the issue and read the plan from its description.

**From local file:** read from `./plans/<NNN>-<description>.md`. If no path specified,
list `./plans/` to show available plans and ask which one.

Verify the plan contains: Objective, Requirements, Technical Design, and Milestones.

If incomplete or unclear → ask for clarification before proceeding.

**Resuming:** If milestones are partially complete, check `git log`
to identify the last completed milestone. Confirm with the user, then continue from
the next one.

## 2. Execute Each Milestone

For each milestone, work through these steps:

### Setup (first milestone only)

If the plan came from an issue tracker (identifier format indicates the tracker:
`PLAT-123` → Linear via `ak linear`, `#42` → GitHub via `gh`):
- Update the issue status to "In Progress" (or nearest equivalent)
  - Linear: `ak linear update-issue PLAT-123 --status "In Progress"`
  - GitHub: handled automatically by branch/PR conventions
- Create a branch from the default branch: `<user>/<ISSUE-KEY>-<description>`

If the plan is a local file, create a branch: `<user>/<plan-number>-<description>`
(e.g. `simon/001-rate-limiting`).

If the tracker CLI is unavailable or the API call fails, warn and continue.

### A. Understand the Context

Read the milestone's Approach for technical direction, then investigate the relevant areas
of the codebase to understand implementation details. The Approach narrows where to look;
use judgment to explore adjacent code as needed.

Load any skills referenced or implied by the Approach (e.g., if it mentions Terraform
patterns, load the Terraform skill).

### B. Work Through Tasks

Implement each task from the milestone's Tasks list:

1. Perform the work following existing conventions and the Approach guidance
2. Stay focused on the current milestone — don't skip ahead or invent work

If a task is too coarse to implement directly, break it into sub-steps and work
through them.

### C. Verify Deliverable

Two checks:

1. **Review** — invoke `workflow-review` in milestone mode, which triages whether a
   full review is needed based on the milestone's scope and risk. This runs mechanical
   checks (qa-runner) and reasoning-level quality review (code-reviewer subagent).
   Fix any findings marked ❌ before proceeding.
2. **Milestone-specific** — use the milestone's Verify section to confirm the deliverable
   (a specific command, test, or observable behaviour).

If either check fails → attempt to fix. If three meaningfully different attempts fail,
stop, summarise what was tried, and ask the user for guidance.

### D. Commit

If in a git repository:
```bash
git add -A
git commit -m "<type>: <milestone description>"
```

Use conventional commit format (see tool-git-github skill).

### E. Report and Continue

After each milestone:
- Report completion to user with a brief summary
- Confirm before proceeding to next milestone

## 3. Complete Implementation

When all milestones are done:

1. Summarise deliverables to user
2. If the plan came from an issue tracker, update the issue status to "In Review"
   (or nearest equivalent):
   - Linear: `ak linear update-issue PLAT-123 --status "In Review"`
3. If the plan is a local file, move it to a `done/` subdirectory alongside it
   (e.g. `plans/done/`)
4. Ask: "Implementation complete. Would you like to enter Review Mode?"

---

# Handling Issues

## Unclear Requirements or Design

Stop immediately and ask for clarification.

## Discovered Work Not in Plan

Complete the current milestone as planned, then:

1. Report to user after milestone completion
2. Propose plan amendment if needed

**Never implement unplanned work without approval.**

## Plan Appears Flawed

Stop and discuss with user:

1. Explain the specific issue
2. Propose concrete amendments to the plan
3. Show changes in diff format
4. Wait for approval

**Never modify the plan without explicit approval.**

See [references/PROBLEM-HANDLING.md](references/PROBLEM-HANDLING.md) for detailed examples.

---

# Key Principles

- **Plan is the source of truth** — Approach gives direction, Tasks define the work,
  Verify confirms completion. Don't reinvent what the plan already provides.
- **Autonomy within bounds** — the plan sets direction, but use judgment for
  implementation-level details it doesn't specify.
- **Stay focused** — implement the current milestone, don't skip ahead.
- **Stop when unclear** — don't guess or improvise beyond the plan.

---

# Example

**User:** "Let's implement the plan"

1. Load `./plans/001-rate-limiting.md`
2. Milestone 1: Read Approach (use ioredis, key format, TTL strategy), explore
   existing Redis config and patterns, implement Tasks, run qa-runner, verify
3. Commit, report to user
4. Repeat for remaining milestones
5. Report completion, offer Review Mode

See [references/EXECUTION.md](references/EXECUTION.md) for a detailed walkthrough.
