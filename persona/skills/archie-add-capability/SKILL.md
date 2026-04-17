---
name: archie-add-capability
description: >
  Autonomously add new capabilities to the Archie platform. Takes a capability brief,
  researches the problem space, produces a plan, self-reviews, implements, self-reviews
  again, and submits a PR. Use when adding a new feature or integration to Archie,
  extending Archie's skills or tooling, or when asked to "add capability", "implement
  feature for archie", or "extend archie".
---

# Purpose

End-to-end autonomous delivery of new Archie capabilities — from brief to PR.

---

# When to Use

- Adding a new capability to the Archie platform
- Extending Archie's skills, integrations, or tooling
- User says "add capability", "implement feature for archie", "extend archie"

# When Not to Use

- Work on projects other than Archie (use workflow-plan + workflow-implement)
- Bug fixes or small tweaks (handle directly)
- Exploratory research without implementation intent (discuss first)

---

# Archie Platform Context

Before starting, read these files to understand the platform:

- `README.md` — project overview, structure, configuration
- `CONTRIBUTING.md` — conventions, skill layers, extension patterns
- `docs/brain.md` — brain structure and conventions (if the capability touches the brain)

Archie has two codebases:

- **archie** (this repo) — persona, skills, prompts, sandbox, CLI, config
- **agent-kit** (`agent-kit/` subdirectory, separate git repo) — CLI toolkit for
  structured access to external services and data stores

Read agent-kit's `CONTRIBUTING.md` when the capability involves agent-kit changes.

---

# Where Does the Code Go?

When adding a capability, determine where it belongs:

**Agent-kit** — if the functionality is:
- Structured CLI access to an external service or data store
- Mechanical operations that don't require LLM reasoning
- Reusable by systems other than Archie
- Examples: SaaS API integrations, brain index queries, credential management

**Archie skills** — if the functionality is:
- LLM reasoning, extraction, or decision-making
- Archie-specific workflows or orchestration
- Prompt-driven behaviour
- Examples: ingestion pipelines, knowledge routing, summary generation

**Local scripts** — if the functionality is:
- One-off data processing or transformation
- Shell pipelines or simple automation
- Not reusable enough to warrant a CLI module

Many capabilities span both: agent-kit provides the data access, archie skills provide
the reasoning. For example, Notion ingestion uses `ak notion` for reading pages and an
archie skill for extracting and routing knowledge.

---

# Workflow

## 1. Discovery

Brief interactive phase to establish scope. Ask only what's needed:

- What is the capability? (may already be clear from the brief)
- What's the desired outcome? (what should Archie be able to do after?)
- Any specific constraints or preferences?

If the user provides a detailed brief, skip questions that are already answered.
Keep this phase short — 5 questions maximum, focus on the most impactful.

## 2. Research

Investigate before planning:

- **Codebase** — understand the relevant parts of both codebases. Read existing skills,
  config, CLI, and docker code as needed. Use `action-analyze-codebase` for unfamiliar areas.
- **Agent-kit patterns** — if the capability involves agent-kit, read its CONTRIBUTING.md
  for module structure, error handling, credential, and output conventions.
- **Web** — search for relevant documentation, APIs, libraries, or prior art if the
  capability involves external integrations or unfamiliar domains.
- **URLs** — if the user provides reference URLs, fetch and review them.

The goal is to have enough context to produce a good plan without asking the user
implementation questions.

## 3. Plan

Invoke `workflow-plan` to produce a structured plan. The plan should:

- Reference conventions and patterns discovered in research
- Specify which files need creating/modifying across both codebases
- Include updating relevant documentation (README, CONTRIBUTING, docs/)
- Identify which parts go in agent-kit vs archie skills vs scripts

## 4. Implement

Invoke `workflow-implement` to execute the plan.

## 5. Final Review

After all milestones complete, invoke `workflow-review` in implementation review mode
for a full pass across all changes.

Address any findings marked ❌. For ⚠️ and ℹ️ findings, use judgment — fix if
straightforward, otherwise note in the PR description.

Update documentation to reflect the implemented changes.

## 6. Ship

Create a branch, commit, push, and create a PR using `tool-git`. If changes span both
repos, commit and push each repo separately.

**Every step in this workflow is mandatory.** Do not skip steps, take shortcuts, or
rationalise deviations. The value of this workflow is its consistency.

---

# PR Format

```markdown
## Summary

<1-2 sentence description of the capability>

## What Changed

<bullet list of files/areas modified, grouped by concern>

## Decisions Made

<design decisions made during implementation with brief rationale>

## Open Questions

<decisions where uncertainty was flagged — things the reviewer should weigh in on>
```

---

# Decision Authority

During implementation, decisions will arise that weren't covered in the brief:

- **Make reasonable decisions and continue** — don't block on the user for every detail
- **Flag uncertainty** — if a decision could reasonably go either way, note it in the PR
  description under "Open Questions"
- **Prefer existing patterns** — when in doubt, follow how similar things are already done
  in the relevant codebase
- **Prefer simplicity** — choose the simpler approach unless there's a clear reason not to

---

# Key Principles

- **Archie-aware** — this skill has deep knowledge of Archie's architecture. Use it.
  Don't treat Archie as a generic project.
- **Autonomous but transparent** — minimise user interaction during execution, maximise
  visibility in the PR.
- **Documentation is part of the work** — every capability should update relevant docs.
- **Follow the process** — every step exists for a reason. Skipping steps erodes trust.
- **Self-improving** — the conversation from this session will be ingested into memory,
  informing future capability additions.
