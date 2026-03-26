---
name: action-create-skill
description: >
  Create, improve, or refactor Kiro/Agent skills by generating complete skill folders
  with SKILL.md, references, examples, and clear workflows. Use this skill when creating
  a new skill, improving an existing SKILL.md, fixing a skill that does not trigger reliably,
  refactoring large skills into maintainable structures, or ensuring a skill library follows
  consistent conventions and avoids overlap between skills.
---

# Purpose

Design and maintain high-quality Kiro-compatible skills that trigger reliably, have clear scope,
avoid overlap, and remain maintainable.

---

# When to Use

- Creating a new skill from scratch
- Improving or refactoring an existing SKILL.md
- Fixing a skill that does not trigger reliably
- Auditing a skill library for overlap or consistency issues

# When Not to Use

- Minor typo fixes or small wording tweaks (handle directly)
- Changing skill behaviour that requires domain expertise you don't have (ask the user)

---

# Skill Layers

Skills follow a layered naming convention. See [references/LAYERS.md](references/LAYERS.md) for
full definitions and guidance on choosing the right layer.

| Prefix       | Purpose                                              |
|--------------|------------------------------------------------------|
| `policy-*`   | Standards, conventions, heuristics                   |
| `workflow-*` | Core agentic orchestration (plan → implement → review) |
| `tool-*`     | Operational guidance for CLI tools and systems       |
| `action-*`   | Self-contained tasks that produce a defined outcome  |

---

# Creation Workflow

Follow this process when creating a new skill.

## 1. Determine operation mode

1. Check if a skill name is provided
2. Check if `./skills/<skill-name>/SKILL.md` exists
3. If exists → enter **modification mode** (see Modification Workflow below)
4. If not → continue with creation

## 2. Understand the intent

Determine:
- What the skill helps the user achieve
- Whether it generates an artifact or provides guidance
- Expected inputs and outputs
- Typical user requests that should activate the skill

**You must clarify before proceeding if:**
- The primary outcome is unclear (what does the skill produce?)
- It's unclear whether this is create vs modify
- The appropriate layer is ambiguous
- Multiple candidate skills could be the target
- It's unclear whether the skill should produce an artifact or provide guidance

If none of these apply, proceed with reasonable assumptions and state them.

## 3. Collision check

Before building the skill, check for overlap with existing skills.

1. Read skill names and descriptions from `./skills/**/SKILL.md`
2. Look for exact or near-exact matches
3. Identify similar skills that might overlap

**Decision points:**
- Exact match → switch to modification mode
- Similar skills exist → note them for distinctiveness optimisation (step 9)
- Unique → proceed

**When overlap is found, apply these rules:**
- Same intent + same output → modify the existing skill instead of creating a new one
- Same intent + different output shape → split clearly by output type, or merge if the outputs are complementary
- Substantial overlap in trigger phrases but different domains → rewrite descriptions until activation surfaces diverge
- Partial overlap → narrow the new skill's scope to the non-overlapping area

## 4. Classify the skill

Determine the appropriate layer using [references/LAYERS.md](references/LAYERS.md).

If the skill spans multiple layers, consider splitting it into separate skills.

## 5. Structure the SKILL.md

**Token budget:** Metadata ~100 tokens, SKILL.md body <5000 tokens / <500 lines.

**Standard sections:**
```
Purpose
When to Use / When Not to Use
Workflow (numbered steps)
Output Format (if artifact-producing)
Examples
```

Use numbered workflows — they make skills significantly more reliable.

If SKILL.md grows large, extract supporting material to `references/`.

See [references/FRONTMATTER.md](references/FRONTMATTER.md) for field specifications.

## 6. Define output format (artifact-producing skills only)

If the skill generates artifacts, define the output structure explicitly.

Guidance-focused skills do not need a strict output schema.

## 7. Include at least one example

Examples significantly improve reliability. Show a realistic user request and the expected output or behaviour.

## 8. Write the description

The `description` field is the primary mechanism for skill activation.

**Structure:**
- Sentence 1: What the skill does and what it produces
- Sentence 2+: "Use this skill when…" followed by common user intents

**Guidelines:**
- Target 100-200 words
- Use clear verbs (generate, gather, review, analyze, scaffold)
- Include multiple natural phrasings of the same intent
- Avoid vague verbs (help, assist, support) and implementation details

## 9. Distinctiveness optimisation

Compare the description against skills noted in the collision check (step 3).

Look for identical user intents, similar verbs/domains, or descriptions that would trigger on the same prompts.

If overlap exists:
- Emphasise unique aspects of the skill's workflow or outputs
- Narrow scope or use more specific domain keywords
- Every skill should own a distinct activation surface

## 10. Validate

Before presenting to the user, verify:
- Frontmatter name matches the directory name
- Frontmatter name meets constraints (1-64 chars, lowercase, hyphens, no leading/trailing/consecutive hyphens)
- Description is 1-1024 characters
- SKILL.md is under 500 lines
- All referenced files exist

## 11. Present for approval

1. Show the complete folder structure
2. Display full content of all files
3. Wait for explicit approval before writing

## 12. Write to ./skills/

After approval:
1. Create `./skills/<skill-name>/` if needed
2. Write SKILL.md
3. Create subdirectories only if they contain files (`references/`, `scripts/`, `assets/`)
4. Set executable permissions on scripts (`chmod +x`)

## 13. Confirm installation

Report:
- Skill location and files created/modified
- 6-10 positive activation phrases (should trigger the skill)
- 4 negative phrases (should not trigger the skill)
- 2-3 ambiguous phrases with explanation of which skill should win and why

---

# Modification Workflow

Follow this process when improving an existing skill.

## 1. Load and understand

1. Read the existing SKILL.md and any references
2. Understand the current structure, scope, and intent
3. Identify what the user wants changed

## 2. Assess the change

Determine if this is:
- **Targeted update** — change specific sections, preserve everything else
- **Restructure** — significant reorganisation (treat as creation with existing content as input)

For targeted updates, preserve existing structure and only modify affected sections.

## 3. Apply changes

Make the requested changes. For restructures, follow the creation workflow from step 5 onwards, using existing content as the starting point.

## 4. Validate

Run the same validation checks as creation step 10.

## 5. Present for approval

Show the updated content. For restructures, include a change summary:
- Files changed, added, or removed
- Sections modified and why
- Any activation behaviour changes (description or trigger phrase changes)
- Compatibility risks (renamed references, changed output format, narrowed scope)

For targeted updates, highlight the specific changes.

Wait for explicit approval before writing.

---

# Supporting Directories

### scripts/

Executable code that agents can run.

- MUST use Python or Bash
- Python scripts MUST use uv inline dependency format if dependencies are needed
- Include shebang line, helpful error messages, and edge case handling

### references/

Additional documentation loaded on demand. Keep files focused — smaller files mean less context usage.

### assets/

Static resources: templates, images, data files, schemas.

---

# Output Format

When creating or modifying a skill, provide:

1. **Folder structure** — directories that contain files
2. **Complete file contents** — all files as fenced code blocks with paths
3. **Activation phrases** — 6-10 phrases that should trigger the skill
4. **Collision report** (if applicable) — overlapping skills and what was changed to differentiate
