---
name: action-memory-update
description: >
  Batch extract conversation memories and signals from session history into brain
  memory files. Use when asked to "update memory", "catch up", "process conversations",
  or "run memory update".
---

# Purpose

Extract conversation history into structured memory files and learning signals.
This is a batch process — not inline persistence (which happens naturally during
conversation via the brain guidance).

---

# When to Use

- Periodic memory maintenance ("update memory", "catch up")
- After a series of work sessions
- When explicitly asked to process recent conversations

# When Not to Use

- Inline persistence during conversation (just write to brain directly)
- Processing raw files from `_raw/` (use `action-brain-ingest`)

---

# Workflow

## 1. Gather conversations

```bash
python3 ~/.kiro/skills/action-memory-update/scripts/memory-prep.py > /tmp/memory-payload.json
```

The script prints a summary to stderr showing conversation count and breakdown by
date/project/turns. If no conversations are found, stop here.

## 2. Summarise into memory files

For each conversation, produce or update a memory file.

**Location:** `_archie/memory/` in the brain

**Filename:** `<date>-<project>.md` (one file per day per project, append if exists).
For general (non-project) sessions: `<date>-<first 4 chars of conversation_id>.md`.

**Frontmatter:**
```yaml
---
name: <Short descriptive title of the session>
summary: <One-line summary of key topics/decisions>
tags: [<project-name>, <domain>, <relevant-topics>]
---
```

**Body format:**
```markdown
# Topic Heading

Discussed how to query the brain — two-step pattern: index lookup first,
grep fallback.

Decided context routing should be content-based, not source-tagged.

Action: changed commit_context() to accept explicit --paths.

Correction: initially hardcoded ~/dev. Should use project_dir from config.

CURRENT STATUS: All features implemented. Memory pipeline operational.
```

**Conventions:**
- Topic headings group related exchanges
- One summary paragraph per turn pair (combine closely related turns)
- Capture progression: who raised what, who pushed back, how it evolved
- Prefixes: **Discussed**, **Decided**, **Action**, **Correction**
- End with current status if work is in progress
- Skip: routine file reads, debugging steps, greetings, small talk
- Tags should include the project name, relevant domains, and key topics

## 3. Update watermark

After all conversations are processed:

```bash
python3 ~/.kiro/skills/action-memory-update/scripts/memory-prep.py \
  --set-watermark <watermark_from_payload>
```

## 4. Detect and record signals

While summarising each conversation, identify learning signals — moments where:
- The user corrected a mistake or misunderstanding
- An approach failed and required a different strategy
- A tool or API behaved unexpectedly
- An assumption proved wrong

For each signal worth recording:
1. Determine the type: `correction`, `failure`, or `pattern` (recurring issue)
2. Write a concise, actionable summary — what went wrong and what the correct approach is
3. Assign a category (api-integration, configuration, implementation, architecture, behaviour, etc.)

Append to `_archie/signals.yaml`:

```yaml
- timestamp: 2026-04-19
  project: archie
  type: correction
  category: api-integration
  summary: "Jira scoped tokens use Basic auth at api.atlassian.com, not Bearer"
```

**What makes a good signal:**
- Specific and actionable (not "made an error")
- Captures the correct approach, not just the failure
- Would prevent the same mistake in future sessions

**Skip:**
- Trivial corrections (typos, minor naming preferences)
- One-off debugging steps that aren't generalisable
- Signals already present in the file

## 5. Commit

```bash
ak brain reindex
ak brain commit "memory: <date range or summary>" --paths _archie/memory/ --paths _archie/signals.yaml --paths index.yaml
```

## 6. Report

Summarise: conversations processed, memory files written/updated, signals added.

---

# Batching

For many conversations, delegate to subagents grouped by project (max 4 concurrent).
Update watermark only after all complete.
