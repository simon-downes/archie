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
python3 ~/.archie/persona/scripts/memory-prep.py > /tmp/memory-payload.json
```

Check what's available:
```bash
cat /tmp/memory-payload.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'{len(data[\"conversations\"])} conversations, {len(data[\"signals\"])} signals')
for c in data['conversations']:
    p = c['project'] or '(general)'
    print(f'  {c[\"date\"]} {p:20s} {len(c[\"turns\"]):>3} turns')
"
```

If no conversations, skip to signals or finish.

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
python3 ~/.archie/persona/scripts/memory-prep.py \
  --set-watermark <watermark_from_payload>
```

## 4. Process signals

The payload includes a `signals` array with mechanically-detected corrections,
failures, and successes. Review each and write meaningful ones to the signals file.

For each signal worth keeping:
1. Read the signal's `message` field and surrounding context
2. Write a concise, actionable summary (not the raw user message)
3. Assign a category

Append to `_archie/signals.yaml`:

```yaml
- timestamp: 2026-04-19
  project: archie
  type: correction
  category: api-integration
  summary: "Jira scoped tokens use Basic auth at api.atlassian.com, not Bearer"
```

Skip signals that are:
- False positives
- Trivial (typo corrections, minor clarifications)
- Duplicates of existing signals

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
