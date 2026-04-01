# Skill Layers

Skills follow a layered naming convention. Each skill should fit clearly into one layer.

## policy-\<scope\>-\<name\>

Defines standards, preferences, heuristics, and conventions.

**Purpose:** Guide how decisions should be made.

**Characteristics:**
- Provides standards and best practices
- Defines conventions and preferences
- Includes heuristics for decision-making
- Does not execute operations or orchestrate workflows

**Scope:** One domain or language (e.g., Python standards, not "all language standards")

**Examples:** `policy-general-coding`, `policy-lang-python`, `policy-lang-terraform`

---

## workflow-\<scope\>-\<name\>

Defines the core agentic orchestration chain.

**Purpose:** Coordinate multi-step processes that form the primary development workflow.

**Characteristics:**
- Orchestrates multiple steps in a defined sequence
- Forms part of the core workflow chain (plan → implement → review)
- References tool and policy guidance
- May delegate to actions for specific tasks

**Scope:** One process (e.g., planning, not "planning and implementation")

**Examples:** `workflow-plan`, `workflow-implement`, `workflow-review`

---

## tool-\<tool\>

Provides operational guidance for using a specific CLI tool or system.

**Purpose:** Capture local expectations and conventions for tool usage.

**Characteristics:**
- Preferred commands and patterns
- Guardrails and safety checks
- Repository/environment assumptions
- Covers the full surface area of a tool or closely related tool family

**Scope:** One tool or closely related tool family (e.g., git + source provider, not "all version control")

**Examples:** `tool-git`, `tool-issues`, `tool-aws`

---

## action-\<name\>

A task that produces a defined outcome.

**Purpose:** Encapsulate domain expertise and a repeatable process for a specific task.

**Characteristics:**
- Produces a concrete outcome (artifact, state change, or verified result)
- May involve multiple steps and meaningful decision-making
- May reference other skills (policy, tool) and use subagents
- Not part of the core workflow chain — invoked independently or on demand

**Scope:** One cohesive task (e.g., "create skill" not "manage all skills")

**Examples:** `action-create-skill`, `action-project-docs`, `action-create-terraform-module`

---

## Choosing the Right Layer

1. **Does it define standards or conventions?** → `policy-*`
2. **Is it part of the core workflow chain (plan → implement → review)?** → `workflow-*`
3. **Does it guide usage of a specific CLI tool or system?** → `tool-*`
4. **Does it produce a defined outcome as a standalone task?** → `action-*`

If a skill spans multiple layers, consider splitting it into separate skills.
