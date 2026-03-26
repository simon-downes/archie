---
name: action-review-plan
description: >
  Review implementation plans for completeness, unresolved decisions, and implementability.
  Spawns a subagent with a clean context window to audit the plan against quality criteria.
  Use this skill when reviewing a plan before implementation, checking a plan for gaps or
  unresolved decisions, validating that a plan is ready to hand off to an implementor, or
  when asked to "review this plan", "check the plan", or "is this plan ready".
---

# Purpose

Audit an implementation plan for completeness and implementability. Surface gaps, unresolved
decisions, and ambiguities so they can be resolved before the plan reaches an implementor.

---

# When to Use

- Before presenting a plan to the user for approval
- When the user asks to review an existing plan
- When validating a plan created by someone else
- Before handing a plan to workflow-implement

# When Not to Use

- Reviewing code or pull requests (use workflow-review)
- Creating or modifying plans (use workflow-plan)

---

# Workflow

## 1. Locate the plan

Determine the plan file to review:
- User specifies a path → use that
- Plan was just drafted in the current session → use the draft content
- Ambiguous → ask which plan to review

## 2. Spawn reviewer subagent

Delegate the review to the `plan-reviewer` subagent with:
- The complete plan content
- The review criteria from [references/REVIEW-CRITERIA.md](references/REVIEW-CRITERIA.md)
- The project's codebase root path (for verifying codebase claims)

The subagent has read-only codebase access to verify claims like "follows pattern in auth.ts"
or "add to existing services/ directory".

## 3. Return findings

The subagent returns structured findings. Present them to the caller as-is.

The caller decides what to do with findings:
- **workflow-plan** (automatic mode): resolves findings, re-reviews if needed
- **User** (standalone mode): reads findings, decides what to fix

---

# Integration with workflow-plan

When consumed by workflow-plan as an automatic quality gate:

1. Planner completes Phase 3 (milestones)
2. Invoke this skill with the draft plan
3. If findings exist: planner resolves what it can from codebase/context, asks the user
   for anything it genuinely cannot answer
4. Re-run review (max 2 review passes to avoid infinite loops)
5. Present the clean plan to the user

The user should never see a plan with unresolved decisions that could have been caught.

---

# Subagent Contract

**Agent:** `plan-reviewer`

**Input:**
- Complete plan content (objective, requirements, design, milestones)
- Review criteria
- Codebase root path

**Output:** Structured findings (see [references/REVIEW-CRITERIA.md](references/REVIEW-CRITERIA.md)
for output format)

**Access:** Read-only (read, glob, grep, shell, code)

**Constraint:** The reviewer surfaces findings. It does not rewrite the plan or suggest fixes.
