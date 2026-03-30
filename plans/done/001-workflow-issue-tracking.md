# Issue Tracking Integration for Workflow Skills

## Objective

Add issue tracker integration to the planning, implementation, and review workflow skills.
The tracker is discovered from project documentation (README, CONTRIBUTING, AGENTS.md) — no
per-project config files, no tool dependencies baked into the skills. Supports Linear, GitHub
Issues, or no tracker. Plans are linked to issues bidirectionally: the plan file references
the issue identifier, and the issue description embeds the plan content.

## Requirements

### Discovery

- MUST discover the issue tracker from project documentation during investigation
  - AC: If README/CONTRIBUTING/AGENTS.md mentions Linear with a team key, use Linear
  - AC: If docs mention GitHub Issues, use GitHub Issues
  - AC: If no tracker mentioned, skip issue tracking silently
  - AC: Discovery happens once per workflow invocation, not per-step

- MUST NOT require per-project config files or specific tools to be installed
  - AC: Skills work without any tracker — issue tracking is additive
  - AC: If the tracker CLI is unavailable, warn and continue without tracking

### Plan ↔ Issue Linkage

- MUST support creating a new issue from a plan
  - AC: Issue is created with the plan title as issue title
  - AC: Plan content is embedded in the issue description between markers
  - AC: Plan file includes the issue identifier in a header comment

- MUST support linking a plan to an existing issue
  - AC: "Create a plan for PLAT-123" reads the issue for context
  - AC: Issue description is updated with the embedded plan
  - AC: Plan file includes the existing issue identifier

- MUST use boundary markers for embedded plans in issue descriptions
  - AC: Markers are `<!-- plan:start -->` and `<!-- plan:end -->`
  - AC: Content outside markers is preserved when updating
  - AC: Plan updates replace only the content between markers

### Plan File Format

- MUST include issue identifier in plan files when linked
  - AC: First line of plan file is `<!-- issue: PLAT-123 -->` (or equivalent)
  - AC: Implementor can read this to find the linked issue

### Workflow Touchpoints

- MUST update issue status at implementation start
  - AC: Issue moves to "In Progress" (or nearest equivalent) when first milestone begins
  - AC: Branch is created from default branch using issue identifier in name

- MUST update issue status at implementation end
  - AC: Issue moves to "In Review" (or nearest equivalent) when all milestones complete

- MUST create PR at end of review
  - AC: PR is created linking to the issue
  - AC: Issue remains in "In Review" status (PR merge handles final transition)

### Error Handling

- MUST handle tracker unavailability gracefully
  - AC: If CLI tool not found, warn and skip tracking steps
  - AC: If API call fails, warn and continue — never block the workflow
  - AC: All tracker operations are best-effort, not blocking

## Technical Design

### Overview

Changes to four existing workflow skills (plan, implement, review, git-github) plus a new
reference doc. No new code — just skill document updates that add tracker-aware steps at
specific points. The skills remain fully functional without a tracker.

### Prerequisite

`ak linear update-issue` needs a `--description` flag to support embedding plan content
in issue descriptions. This is a small addition to agent-kit's Linear CLI — add before
implementing milestone 1. For GitHub Issues, `gh issue edit --body` already supports this.

### Tracker Discovery

Added as a sub-step within workflow-plan Phase 1 step 3 (Investigate the Codebase). The
agent checks project docs for mentions of issue tracking. The result is one of:

- `linear` with a team key (e.g. "PLAT") — uses `ak linear` commands
- `github` — uses `gh issue` commands
- `none` (skip tracking)

This is noted internally and used by subsequent steps. Not persisted — rediscovered if
needed in a new session (the plan file's issue identifier is the persistent link).

### Existing Issue Entry Point

When the user says "create a plan for PLAT-123" or similar, the issue is fetched in
Phase 1 step 2 (Analyse Initial Input) as additional context. The issue title, description,
and comments inform the planning process alongside the user's intent.

### Plan File Header

```markdown
<!-- issue: PLAT-123 -->
# Plan Title
...
```

The comment is invisible in rendered markdown but machine-readable. The implement skill
reads this to know which issue to update.

### Issue Description Format

When creating or updating an issue, the plan is embedded between markers:

```markdown
Original issue description or summary here.

<!-- plan:start -->
## Objective
...
## Requirements
...
## Milestones
...
<!-- plan:end -->
```

When updating an existing issue:
1. Read the current description
2. If markers exist, replace content between them
3. If no markers, append the markers and plan content
4. Write the updated description back

For Linear: `ak linear update-issue PLAT-123 --description "..."`
For GitHub: `gh issue edit <number> --body "..."`

Reference doc with full format: `workflow-plan/references/ISSUE-FORMAT.md`

### Branch Naming

Generalize the git-github skill's branch naming to support any issue tracker:

- Format: `<user>/<ISSUE-KEY>-<description>`
- Linear: `simon/PLAT-123-rate-limiting`
- GitHub Issues: `simon/42-rate-limiting`

The git-github skill's current "JIRA Integration" section becomes a general
"Issue Integration" section.

### Status Mapping

Use common status names and let the CLI error guide correction:
- Start of implementation: "In Progress"
- End of implementation: "In Review"

If the exact name doesn't exist, the CLI returns available options in the error message.

### Changes by Skill

**workflow-plan:**
- Phase 1 step 2 (Analyse Initial Input): if user references an existing issue, fetch it
  for context
- Phase 1 step 3 (Investigate the Codebase): add tracker discovery as a sub-step
- After Phase 4 approval: create/update issue with embedded plan, add identifier to plan file

**workflow-implement:**
- Step 1 (Load Plan): read issue identifier from plan header
- New sub-step before 2A (first milestone only): update issue to "In Progress", create branch
- Step 3 (Complete): update issue to "In Review"

**workflow-review:**
- New step after presenting review verdict: if verdict is approve and issue identifier
  exists, create PR linking to the issue

**tool-git-github:**
- Rename "JIRA Integration" to "Issue Integration"
- Generalize branch naming to support any issue key format

## Milestones

### 1. Add --description flag to ak linear update-issue

Approach:
- The `issueUpdate` GraphQL mutation already accepts `description` in its input.
  Just need to add a `--description` CLI flag and pass it through.
- Follow the existing pattern for `--title` in `update_issue()`.

Tasks:
- Add `description` parameter to `update_issue()` in `client.py`
- Add `--description` flag to `update-issue` CLI command
- Support stdin for description (same pattern as create-issue)

Deliverable: `ak linear update-issue PLAT-1 --description "new description"` updates
the issue description.

Verify: Update PLAT-1's description, fetch the issue, confirm description changed.

### 2. Create reference doc and update workflow-plan

Approach:
- Create `workflow-plan/references/ISSUE-FORMAT.md` documenting the plan file header
  format and issue description marker format.
- Add tracker discovery as a sub-step within Phase 1 step 3.
- Add existing issue handling to Phase 1 step 2.
- Add issue creation/update step after Phase 4 approval.
- All additions are conditional — guarded by "if tracker discovered".

Tasks:
- Create `workflow-plan/references/ISSUE-FORMAT.md` with header and marker formats
- Add tracker discovery sub-step to Phase 1 step 3
- Add existing issue fetch to Phase 1 step 2
- Add issue linkage step after Phase 4 approval
- Update Planning Artifacts section with plan file header format

Deliverable: workflow-plan skill includes tracker discovery, existing issue support,
and issue linkage steps.

Verify: Read the updated skill. Tracker discovery is in Phase 1 step 3, existing issue
handling is in step 2, issue creation is after approval, all guarded by conditionals.

### 3. Update workflow-implement with status updates and branching

Approach:
- Read issue identifier from plan file header comment in step 1 (Load Plan).
- Add a new sub-step before the existing "A. Understand the Context" that runs only
  for the first milestone: update issue status to "In Progress" and create branch.
- Add issue status update to "In Review" in step 3 (Complete Implementation).
- All tracker operations guarded — no identifier means skip.

Tasks:
- Add issue identifier reading to step 1 (Load Plan)
- Add new first-milestone sub-step for status update and branch creation
- Add status update to step 3 (Complete Implementation)

Deliverable: workflow-implement updates issue status at start and end, creates branch
from issue identifier on first milestone.

Verify: Read the updated skill. Identifier is read from plan, status updates at
start/end, branch naming uses the identifier, all conditional.

### 4. Update workflow-review and tool-git-github

Approach:
- Add a conditional step to workflow-review after the review verdict is presented:
  if verdict is approve and an issue identifier is present, create a PR linking to
  the issue. This is a new step at the end of the review flow.
- Generalize tool-git-github's "JIRA Integration" section to "Issue Integration"
  supporting any issue key format (JIRA, Linear, GitHub Issues).

Tasks:
- Add PR creation step to workflow-review after verdict presentation
- Rename and generalize git-github's JIRA section to Issue Integration
- Update branch naming examples to include Linear and GitHub Issues formats

Deliverable: Review completion creates a PR when appropriate. Git-github skill supports
any issue tracker's key format for branch naming.

Verify: Read both updated skills. PR creation is conditional on approve + identifier.
Branch naming section is generalized with multiple tracker examples.
