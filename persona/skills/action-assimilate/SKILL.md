---
name: action-assimilate
description: >
  Analyse external skills, repos, or methodologies against our existing setup and extract
  meaningful improvements into brain improvement files. Use when the user wants to assimilate
  a skill, compare an external approach to ours, extract improvements from a repo or
  methodology, or update improvement tracking with new techniques from external sources.
---

# Purpose

Take an external source (skill, repo, methodology) and produce targeted updates to our
brain improvement files — only when the source offers something concretely better than
what we already have.

---

# When to Use

- User provides a URL, file path, or repo to assimilate
- User asks to compare an external approach against our setup
- Batch analysis of a skills repo or research directory

# When Not to Use

- Implementing improvements (that's workflow-implement)
- Original research or exploration (that's action-research)
- Creating new skills from scratch (that's action-create-skill)

---

# Quality Bar

Every proposed change MUST clear ALL four criteria:

1. **Concrete** — a specific technique, pattern, or procedure (not "consider doing X")
2. **Actionable** — implementable in our skill/setup without further research
3. **Differentiated** — we don't already do this, or our version is measurably weaker
4. **Impactful** — addresses a real gap, not a stylistic preference or cosmetic difference

If a source yields nothing that clears this bar, the outcome is "nothing to assimilate."
That's a valid and expected result. No filler updates.

---

# Workflow

## 1. Identify the source

Determine what the user wants assimilated:
- A single file/skill (URL or path)
- A directory of skills/capabilities
- A repo or large codebase

## 2. Read and decompose into capabilities

**Accessing the source:**
- Local path/directory → read directly
- GitHub URL → use `fetch` tool or clone if the repo is needed broadly
- Web URL → use `web_fetch` tool

**Single skill/file:** Skip decomposition — go directly to step 3.

**Multi-capability source (repo, skills directory, research file):**

1. Read at high level — README, directory structure, table of contents
2. Identify discrete, independently-analysable capabilities
3. For each capability, determine the minimal file set needed to understand it
4. Group interconnected capabilities (those that reference each other) into a single unit

Output: a list of capabilities, each with a name and file list.

## 3. Check provenance and find counterparts

For each capability, find our counterpart:

1. **Search the brain** for the improvement file — search for the capability domain
   (refer to `# Available Tools`).
   Look for results in `projects/archie/improvements/` — these are the improvement files.
   If no improvement file exists yet, one will be created in step 5.

2. **Identify the counterpart skill** — match by domain/purpose, not by name. Ask:
   "Which of our skills does the same job as this capability?" Check `./skills/` directory
   names and descriptions. A capability may have no counterpart skill (gap), one clear
   match, or touch multiple skills — in the last case, pick the primary one and note
   the others in the update.

3. **Check provenance** — read the improvement file's `sources` frontmatter:
   ```yaml
   sources:
     - name: example-org/planning-skill
       date: 2026-05-22
   ```
   **Skip** capabilities whose source name already appears — unless the user explicitly
   asked to re-analyse.

## 4. Assimilate (one subagent per capability)

For each capability that passes provenance check, spawn a subagent with:

**Context provided to subagent:**
- The source capability files (the external thing to analyse)
- Our counterpart skill (`./skills/<relevant>/SKILL.md`) if one exists
- Our counterpart improvement file from the brain if one exists
- The quality bar criteria (all four must be met)

**Subagent instructions:**

> Analyse the provided source against our existing skill and improvement file.
> Identify changes that are concrete, actionable, differentiated, and impactful.
>
> For each proposed change, state:
> - **What:** the specific technique or pattern
> - **Why better:** how it improves on what we have (or fills a gap)
> - **Where:** which section of the improvement file it belongs in
>
> If nothing clears the quality bar, say "Nothing to assimilate" and briefly explain why
> (e.g. "we already cover this", "too vague to be actionable", "stylistic not substantive").
>
> Do NOT propose:
> - Vague suggestions ("consider adding error handling")
> - Things we already do (check the existing skill/improvement file)
> - Cosmetic or naming-only changes
> - Incremental tweaks that don't meaningfully change outcomes
>
> Note: You have limited visibility into our full setup. If unsure whether we already
> do something, flag it as "possibly redundant — verify against <skill-name>" rather
> than asserting it's new.

## 5. Update brain improvement files

For each subagent that produced results:

1. **Existing file** — merge new insights into the appropriate sections. Preserve existing
   content. Add new techniques/patterns with clear headings. Don't reorganise existing
   material unless the new content makes the structure incoherent.

2. **No existing file** — create a new improvement file at
   `projects/archie/improvements/<domain>.md` following the established format:
   ```yaml
   ---
   name: <Domain> Improvements
   summary: <one-line description>
   tags: [archie, improvements, <relevant-tags>]
   status: proposed
   priority: <high|medium|low>
   sources:
     - name: <source-identifier>
       date: <today>
   ---
   ```

3. **Update provenance** — add the source to the `sources` frontmatter list with today's date.
   Evolve flat source lists (legacy format) to the name+date format on update.

4. **Commit:** Reindex the brain and commit the modified files
   (refer to `# Available Tools`).

## 6. Report

Summarise what was assimilated:
- Capabilities analysed vs skipped (provenance)
- Changes made per improvement file
- Capabilities that yielded nothing (and why)

---

# Batch Mode

When the source contains multiple capabilities:

- Use a subagent per capability for context isolation
- Steps 1-3 (decompose, provenance) run sequentially in the orchestrator
- Step 4 subagents run in parallel
- Each subagent gets only its capability's files + our counterpart — not the entire source
- Aggregate results in the report

---

# Source Identification

The source identifier for provenance tracking should be:
- **Skills repo:** `<repo-owner>/<skill-name>` (e.g. `acme-org/planning-skill`)
- **Research repos:** the repo/project name
- **Single files:** filename or URL basename
- **Local research:** `_research/<name>`

---

# Examples

**Single skill:**
```
User: assimilate https://github.com/example-org/skills/.../planning/SKILL.md
→ Read skill → find counterpart (workflow-plan improvement file)
→ Compare → update brain file if quality bar met
```

**Skills repo:**
```
User: assimilate the example-org skills repo
→ Decompose: identify 12 skills
→ Provenance: 4 already seen, 8 new
→ Spawn 8 subagents
→ 3 produce updates, 5 yield nothing
→ Update 3 improvement files, report
```

**Research directory:**
```
User: assimilate _research/agent-framework
→ Decompose: memory system, skill creation, channel routing, self-improvement
→ Spawn 4 subagents
→ Update relevant improvement files
```
