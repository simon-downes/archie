---
name: action-memory-update
description: >
  Batch extract conversation memories from distilled session logs into brain
  memory files. Use when asked to "update memory", "catch up", "process conversations",
  or "run memory update".
---

# Purpose

Extract conversation history into structured memory files. This is a batch process —
not inline persistence (which happens naturally during conversation via the brain
guidance).

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

## 1. Ensure logs are up to date

```bash
ak digest
```

## 2. Identify sessions to process

List distilled logs and compare against existing memory files:

```bash
ls ~/.archie/brain/_archie/logs/
ls ~/.archie/brain/_archie/memory/
```

Memory files use the format `<date>-<project>-<session_id_short>.md` where
`session_id_short` is the first 4 characters of the conversation session ID.

For each distilled log, check the corresponding memory file:
- **No memory file exists** → process all turns (new session)
- **Memory file exists but distilled log is newer** → process only turns with
  `when` timestamp after the memory file's modification time (append new content)
- **Memory file exists and is up to date** → skip

Skip sessions with very few turns (1-2) unless they contain decisions or actions.

## 3. Summarise into memory files

For each session to process, read the distilled log (or just the new turns for
append) and produce/update a memory file.

The distilled log contains: user messages (verbatim), assistant reasoning text
(tool blocks already stripped), and tool call metadata. This is the input for
summarisation — no need to process raw conversation files.

**For new sessions:** read all turns, produce the full memory file.

**For appending:** read only turns after the memory file's mtime, produce a summary
of the new content, and append it to the existing file under new topic headings.

**Location:** `_archie/memory/` in the brain

**Filename:** `<date>-<project>-<session_id_short>.md`

Where:
- `date` is from the log's `started` field (YYYY-MM-DD)
- `project` is from the log's `project` field
- `session_id_short` is the first 4 characters of the `session_id`

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

**What to preserve (memory should answer most questions without needing logs):**
- Specific findings: exact numbers, names, IPs, error messages, measurements
- Decisions AND rejected alternatives with reasoning ("considered X, rejected because Y")
- Open questions and unresolved items left for future sessions
- Dependencies and blockers ("blocked on X", "needs Y merged first")
- External references: PR links, issue IDs, Notion pages, brain entries created

**What to skip (available in logs if ever needed):**
- Step-by-step debugging sequences
- Tool usage details and file contents
- Routine file reads, greetings, small talk
- Intermediate attempts that led nowhere (unless the failure itself is informative)

## 4. Commit

```bash
ak brain reindex
ak brain commit "memory: <date range or summary>" --paths _archie/memory/ --paths index.yaml
```

## 5. Report

Summarise: sessions processed, memory files written, sessions skipped (already processed
or too short).

---

# Batching

For many conversations, delegate to subagents grouped by project (max 4 concurrent).
