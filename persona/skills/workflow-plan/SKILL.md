---
name: workflow-plan
description: >
  Guide complete planning workflow from vague intent to executable implementation plan
  through structured requirements gathering, technical design, milestone breakdown, and
  automated plan review. Use when starting projects that need comprehensive planning
  before implementation, creating detailed plans for complex features, or turning
  high-level ideas into actionable work with clear deliverables.
---

# Purpose

Guide the complete planning process from vague intent to a self-contained plan artifact
that can be implemented in a future session with zero existing context.

---

# When to Use

- Starting new projects or features that need planning before implementation
- User provides initial direction but needs structured planning
- Work requires investigation and design before implementation

# When Not to Use

- Simple bug fixes or trivial changes
- Work that's already well-defined with clear requirements
- Quick exploratory tasks

---

# Planning Artifacts

Plans are stored in one of two places depending on whether an issue tracker is available:

**With issue tracker:** the plan lives in the issue description. The issue identifier
(e.g. PLAT-123, #42) is the plan identifier. No local plan files are created.

**Without issue tracker:** plans are stored as local files in `./plans/` relative to the
project root.

## Local Plan Files (no tracker)

**File naming:** `<NNN>-<description>.md` where `<NNN>` is a zero-padded incrementing number.
To determine the next number, check both `./plans/` and `./plans/done/` for the highest
existing number and increment.

**Completed plans:** move to `./plans/done/` when fully implemented. The number is preserved.

**Determining the project root:**
1. The nearest ancestor directory containing `.git` (handles sub-projects with own repos)
2. The `ARCHIE_PROJECT_ROOT` environment variable (handles new projects without git)
3. If neither is available, ask the user

When working in a sub-project (e.g. `agent-kit/` inside `archie/`), the sub-project's
`.git` takes precedence — plans go in the sub-project's `./plans/`.

**Confirm the plan location** before writing when the project root is ambiguous or when
working in a sub-project.

Examples:
- `./plans/001-rate-limiting.md`
- `./plans/002-agent-kit-linear.md`

---

# Four-Phase Planning Process

## Phase 1: Objective + Requirements

**Goal:** Transform vague intent into clear, testable requirements with all ambiguity resolved.

1. **Write Objective** — concise problem description and desired outcome (2-4 sentences)

2. **Analyse Initial Input** — identify core objective, what's stated, what's implied, obvious gaps.
   If the user references an existing issue (e.g. "plan for PLAT-123"), fetch the issue to use
   its title, description, and comments as additional context for planning.

3. **Investigate the Codebase** — before asking the user anything, explore the codebase to answer
   discoverable questions: existing patterns, conventions, dependencies, relevant modules.
   Use `action-analyze-codebase` for unfamiliar repos.
   Also check project documentation (README, CONTRIBUTING, AGENTS.md) and any available
   context for issue tracking conventions. If a tracker is identified (Linear, GitHub
   Issues, etc.) with configuration details (e.g. team key), note it for use after plan
   approval. If no tracker is mentioned anywhere, skip issue tracking silently.

   If multiple sources indicate different trackers, prefer: the user's explicit instruction,
   then project documentation, then defaults from context.

4. **Resolve the Decision Tree** — systematically walk through each branch of the design space.
   For each open question:
   - If answerable from the codebase → resolve it, state what you found
   - If a preference or intent question → ask the user, ONE question at a time, with your
     recommended answer and alternatives
   - Build on previous answers — each resolution may open new branches

5. **Draft Requirements** — use RFC 2119 keywords (MUST/SHOULD/MAY), focus on observable
   behaviour, add testable acceptance criteria, group logically

6. **Iterate Until Approved** — present to user, incorporate feedback, refine until confirmed

**Approval Gate:** "Do the objective and requirements look correct?"

See [references/REQUIREMENTS.md](references/REQUIREMENTS.md) for format rules and examples.

---

## Phase 2: Technical Design

**Goal:** Resolve all cross-cutting technical decisions so the implementor never needs to choose
a dependency, decide where code lives, or establish a new pattern.

1. **Identify Cross-Cutting Decisions** — review the requirements and determine what needs
   resolving at the project/feature level:
   - Technology choices (libraries, frameworks, tools)
   - Structural decisions (where new code lives, module boundaries)
   - Patterns and conventions (especially for greenfield work)
   - Infrastructure and deployment considerations
   - Non-functional concerns (security, observability, performance)

2. **Resolve from Codebase First** — for existing projects, many decisions are already made.
   Reference existing patterns rather than re-deciding. Call out where this work deviates
   from established patterns and why.

3. **Draft Design** — document resolved decisions with rationale. Focus on choices and their
   reasoning, not system descriptions. Keep it concise.

4. **Review with User** — present design, iterate based on feedback

**After approval, automatically proceed to Phase 3.**

See [references/DESIGN.md](references/DESIGN.md) for decision categories and examples.

---

## Phase 3: Milestones

**Goal:** Break work into incremental, testable deliverables with enough technical context
that an implementor in a fresh session can execute without re-discovering decisions.

Each milestone has four sections:

- **Approach** — technical context that shapes how the work is done: which libraries/patterns
  to use, where in the codebase this fits, constraints, and ⚠️ gotchas. The "how and why."
- **Tasks** — concrete units of work to complete, in roughly the order they should happen.
  The "what gets done."
- **Deliverable** — single testable outcome. What's true when this milestone is complete.
- **Verify** — how to confirm the deliverable. A command to run, a test to pass, a behaviour
  to observe.

**Format:**
```
1. [Milestone objective]
   Approach:
   - [technical context, guidance, constraints]
   - ⚠️ [gotchas or high-stakes items]
   Tasks:
   - [concrete unit of work]
   - [concrete unit of work]
   Deliverable: [single testable outcome]
   Verify: [how to confirm]
```

**Before presenting milestones, audit each one:**
- Would the implementor need to choose a library or tool? → resolve in Approach
- Would the implementor need to decide where new code lives? → resolve in Approach
- Would the implementor need to establish a new pattern? → resolve in Approach
- Are Tasks specific enough to track progress but not so detailed they prescribe code?
- Does Verify give a concrete way to confirm the deliverable?

**After completing milestones, automatically proceed to Phase 4.**

See [references/MILESTONES.md](references/MILESTONES.md) for detailed rules and examples.

---

## Phase 4: Review

**Goal:** Verify the plan is complete and implementable before presenting to the user.

1. **Run review** — invoke `action-review-plan` with the draft plan. The reviewer audits
   against quality criteria in a clean context window.

2. **Resolve findings** — for each finding:
   - Check the codebase first (can you answer it from code?)
   - If not, ask the user (one question at a time)
   - Update the plan to address the finding

3. **Re-review if needed** — if findings were resolved, run the review again. Maximum 2
   review passes. If findings persist after 2 passes, note them when presenting the plan.

4. **Present complete plan** — show all four phases together.

**Approval Gate:** "Here is the complete plan. Shall we move to Implementation Mode?"

5. **Persist the plan:**
   - **With tracker:** if a tracker was discovered in Phase 1, create or update the issue
     with the full plan as the issue description. If an existing issue was referenced,
     update its description. If no existing issue, create one with the plan title.
     The issue identifier is the plan identifier — no local file is created.
     If the tracker CLI is unavailable or the API call fails, fall back to a local file.
   - **Without tracker:** write the plan to a local file in `./plans/` (see Planning
     Artifacts above).

---

## Key Principles

- **Plan as artifact** — the plan must be self-contained. An implementing agent in a fresh
  session with zero context should be able to execute it.
- **Resolve decisions, don't defer them** — the plan must resolve all dependency, tooling,
  and structural decisions. The implementor should never need to choose a library, decide
  where new code lives, or establish a new pattern.
- **Codebase first** — before asking the user a question, check if the answer is discoverable
  from existing code, docs, or manifests.
- **One question at a time** — when you do need user input, ask one focused question with
  your recommended answer and alternatives.

---

## Quick Reference

### Requirement Format

```
- MUST / SHOULD / MAY <clear requirement>
  - AC: <testable acceptance criteria>
  - Why: <optional context>
```

### Design Focus

Resolve cross-cutting decisions:
- Technology choices and rationale
- Structural decisions (where code lives)
- Patterns and conventions to follow
- Non-functional concerns

### Milestone Sections

| Section     | Purpose                                    |
|-------------|--------------------------------------------|
| Approach    | How and why — context, guidance, constraints |
| Tasks       | What — concrete units of work              |
| Deliverable | Done when — single testable outcome        |
| Verify      | Proof — how to confirm                     |

### Milestone Rules

- Exactly ONE deliverable per milestone
- Deliverables must be testable
- Prefer smaller over larger
- Order by dependency
- No unresolved decisions left for the implementor
