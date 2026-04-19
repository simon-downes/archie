---
name: action-brain-update
description: >
  Batch update the brain from external sources — summarise recent conversations
  into memory and process pending raw/inbox files into brain entities. Use when
  asked to "update the brain", "process conversations", "update memory",
  "process inbox", "run brain update", or "catch up".
---

# Purpose

Autonomous batch pipeline that updates the brain from two input channels:
conversation history → memory files, and raw/inbox files → brain entities.

For direct brain writes from conversation ("remember this", "add to brain"),
no skill is needed — use the brain guidance directly.

---

# When to Use

- Periodic brain maintenance ("update the brain")
- After a series of work sessions ("catch up on recent work")
- When raw files are pending ("process inbox")

# When Not to Use

- Direct brain reads or writes during conversation (use brain guidance)
- Research tasks (use `action-research`)

---

# Workflow

## 1. Update conversation memory

### Gather conversations

```bash
python3 ~/.kiro/skills/action-brain-update/scripts/memory-prep.py > /tmp/memory-payload.json
```

Check what's available:
```bash
cat /tmp/memory-payload.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'{len(data[\"conversations\"])} conversations')
for c in data['conversations']:
    p = c['project'] or '(general)'
    print(f'  {c[\"date\"]} {p:20s} {len(c[\"turns\"]):>3} turns')
"
```

If no conversations, skip to step 2.

### Summarise

For each conversation, produce a memory file.

**File location:** `~/.archie/brain/_memory/`
- Project sessions: `<date>-<project>.md` (one file per day per project, append if exists)
- General sessions: `<date>-<first 4 chars of conversation_id>.md`

**Format:**
```markdown
---
date: 2026-04-18
project: archie
---

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
- One summary paragraph per turn pair (can combine closely related turns)
- Capture progression: who raised what, who pushed back, how it evolved
- Prefixes: **Discussed**, **Decided**, **Action**, **Correction**
- End with current status if work is in progress
- Skip: routine file reads, debugging steps, greetings, small talk

### Update watermark

```bash
python3 ~/.kiro/skills/action-brain-update/scripts/memory-prep.py \
  --set-watermark <watermark_from_payload>
```

### Batching

For many conversations, delegate to subagents grouped by project (max 4
concurrent). Update watermark after all complete.

---

## 2. Process raw and inbox files

### Check for pending items

```bash
ak brain status
ls ~/.archie/brain/_raw/inbox/ 2>/dev/null
ls ~/.archie/brain/_inbox/ 2>/dev/null
```

If nothing pending, skip to step 3.

### Process each item

For each file in `_raw/inbox/` (one at a time):

1. **Move to processing:**
   ```bash
   mv ~/.archie/brain/_raw/inbox/<item> ~/.archie/brain/_raw/processing/<item>
   ```

2. **Read and extract** — identify people, projects, decisions, action items,
   knowledge, goals. Not every item contains all types.

3. **Route, dedup, write** — follow the brain guidance for context routing,
   duplicate checking, entity creation/updates, and conflict detection.

4. **Record provenance:**
   ```bash
   sqlite3 ~/.archie/brain/<context>/brain.db "
   CREATE TABLE IF NOT EXISTS provenance (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       source_file TEXT NOT NULL,
       ingested_at TEXT NOT NULL,
       entities_created TEXT,
       entities_updated TEXT
   );
   INSERT INTO provenance (source_file, ingested_at, entities_created, entities_updated)
   VALUES ('<item>', datetime('now'), '<json-created>', '<json-updated>');
   "
   ```

5. **Reindex and commit** per the brain guidance.

6. **Move to completed:**
   ```bash
   mv ~/.archie/brain/_raw/processing/<item> ~/.archie/brain/_raw/completed/<item>
   ```

For files in `_inbox/` (user-reviewed research output, etc.): process the same
way but don't move the file — the user manages `_inbox/` contents.

---

## 3. Report

Summarise what was done:
- Conversations processed → memory files written
- Raw items processed → entities created/updated per context
- Inbox notes created (routing flags, conflicts)

---

# Memory Watermark

Tracks the last conversation extraction. Stored in `shared/brain.db`:

```sql
CREATE TABLE IF NOT EXISTS memory_watermark (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_processed_at INTEGER NOT NULL  -- conversations_v2.updated_at value
);
```

# Conversation Data Source

Kiro-cli stores history in `~/.local/share/kiro-cli/data.sqlite3`.
Table `conversations_v2`: `key`, `conversation_id`, `value` (JSON with
`transcript` array), `updated_at` (Unix ms). Also reads `.jsonl` session
files from `~/.kiro/sessions/cli/`.
