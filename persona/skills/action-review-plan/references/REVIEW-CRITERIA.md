# Plan Review Criteria

## Purpose

Defines what the plan-reviewer subagent checks and how it reports findings.

## Review Dimensions

Work through each dimension in order. Skip dimensions that don't apply to the plan
(e.g., skip Data Model checks if the plan has no data model section).

---

### 1. Objective and Requirements

- Is the objective clear and specific?
- Are requirements testable (do acceptance criteria exist)?
- Are RFC 2119 keywords used consistently (MUST/SHOULD/MAY)?
- Are there requirements that contradict each other?

---

### 2. Technical Design — Decisions

For each design section present in the plan:

- Are technology choices explicit (named libraries, tools, versions)?
- Are alternatives acknowledged for non-obvious choices?
- Is rationale provided for significant decisions?
- Are there vague references that need specifics? (e.g., "use a caching solution" — which one?)

---

### 3. Technical Design — Codebase Claims

Verify claims against the actual codebase:

- Referenced files exist (e.g., "follows pattern in src/middleware/auth.ts")
- Referenced directories exist (e.g., "add to src/services/")
- Referenced patterns are accurate (e.g., "existing middleware uses Express pattern")
- Referenced dependencies are actually in the project

Flag claims that cannot be verified (file not found, pattern doesn't match).

---

### 4. Milestones — Completeness

For each milestone:

- Does it have all required sections? (Approach, Tasks, Deliverable, Verify)
- Is the Deliverable a single testable outcome (not compound)?
- Does Verify give a concrete way to confirm (command, test, observable behaviour)?
- Are Tasks specific enough to track progress?

---

### 5. Milestones — Unresolved Decisions

The core check. For each milestone, ask:

- Would the implementor need to **choose a library or tool** not specified in the plan?
- Would the implementor need to **decide where new code lives** (file, module, directory)?
- Would the implementor need to **establish a new pattern** not referenced in the plan?
- Would the implementor need to **look up how something works** that the plan could have explained?

Each "yes" is a finding.

---

### 6. Milestones — Structure

- Do milestones follow dependency order (foundational before dependent)?
- Does Approach contain only context/guidance (not tasks)?
- Do Tasks contain only work items (not context/guidance)?
- Is there overlap between Approach and Tasks within the same milestone?
- Is there overlap between milestones (same work appearing in multiple milestones)?

---

### 7. Coherence

Cross-cutting checks across the whole plan:

- Do milestones cover all requirements? (trace each MUST requirement to at least one milestone)
- Does the design support the requirements? (no requirements left unaddressed by design)
- Are there milestones that don't trace back to any requirement?
- Are there contradictions between design decisions and milestone approach?

---

## Output Format

```
## Plan Review: <plan name or objective>

### Verdict: ✅ Clean | ⚠️ Findings | ❌ Significant gaps

### Findings

#### <Dimension name>

- **<Location>**: <finding>
  <brief explanation of why this is a problem>

- **<Location>**: <finding>
  <brief explanation>

...
```

**Location format:**
- `Objective` / `Requirements` / `Design: <section>` / `Milestone N` / `Milestone N, Approach` / `Milestone N, Task M`

**Finding severity:**
- ❌ **Gap**: missing information the implementor will need
- ⚠️ **Concern**: ambiguity or potential issue worth flagging
- ℹ️ **Note**: minor observation, not blocking

**Rules:**
- Only report actual findings — omit dimensions with no issues
- Be specific: quote the problematic text, name the missing decision
- Don't suggest fixes — just identify the problem
- Don't rewrite plan content
- Keep findings concise (one finding = one problem)

**Clean plan example:**
```
## Plan Review: API Rate Limiting

### Verdict: ✅ Clean

No findings. All decisions resolved, milestones trace to requirements,
codebase references verified.
```

**Findings example:**
```
## Plan Review: User Authentication

### Verdict: ⚠️ Findings

### Findings

#### Unresolved Decisions

- ❌ **Milestone 2, Approach**: "use a session store" — which session store?
  Redis, database-backed, in-memory? Not specified in Design: Technical Stack.

- ❌ **Milestone 3, Task 2**: "add validation" — no validation library chosen.
  Design should specify whether to use zod, joi, or manual validation.

#### Codebase Claims

- ⚠️ **Design: Code Structure**: references src/middleware/auth.ts but file
  does not exist. Closest match: src/auth/middleware.ts.

#### Structure

- ⚠️ **Milestone 1, Approach**: "Create the user model and add password hashing"
  is a task, not approach context. Move to Tasks.

#### Coherence

- ℹ️ **Requirement 4** (SHOULD support OAuth): not addressed in any milestone.
  Intentional deferral should be noted.
```
