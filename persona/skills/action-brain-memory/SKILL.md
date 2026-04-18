---
name: action-brain-memory
description: >
  Summarise recent conversations into structured daily memory files in the brain.
  Uses a prep script to extract clean turn pairs from kiro-cli history, then
  summarises into categorised daily logs. Use when asked to "process conversations",
  "update memory", "summarise recent sessions", "what did we discuss", or
  "catch up on recent work".
---

# Purpose

Produce structured daily summaries of conversations so future sessions can quickly
answer: "what have we discussed recently?", "what did we do this week?", "what did
we decide about X?"

---

# When to Use

- Manually triggered to catch up on recent conversations
- After a series of work sessions
- When asked to process or summarise recent conversations

# When Not to Use

- Processing raw files from `_raw/inbox/` (use `action-brain-ingest`)
- Direct brain writes from the current conversation (use `action-brain-write`)

---

# Output Format

Memory files live at `<context>/projects/<project>/memory/<date>.md` for project
sessions, or `shared/memory/<date>.md` for general sessions.

Multiple sessions on the same day are appended to the same file as separate sections.

```markdown
# 2026-04-18

## Session: brain read/write capability

### Decisions
- Content-based context routing for brain writes, not source tagging
- Single commit per context per operation, not per entity
- Explicit path staging (--paths) for concurrent agent safety

### Changes
- Added brain read/write skills (tool-brain, action-brain-read, action-brain-write)
- Added ak brain reindex and commit commands to agent-kit
- Added per-context flock locking to reindex_context()

### Discussions
- How to handle concurrent brain writes from multiple agents
- Knowledge directory structure — flat by default, subdirectories at 5+ files

### Feedback
- Correction: hardcoded ~/dev path, should use project_dir from config
- Correction: prescribed context routing in script, should leave to agent
```

### Categories

- **Decisions** — choices made with rationale. The "we decided X because Y" moments.
- **Changes** — significant work completed, refactors, new features. What actually changed.
- **Discussions** — topics explored but not necessarily resolved. Context for future sessions.
- **Feedback** — corrections, pushback, praise. What went well or poorly.

Not every session will have entries in every category. Omit empty categories.

---

# Workflow

## 1. Gather conversations

Run the prep script to get clean turn pairs:

```bash
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py > /tmp/memory-payload.json
```

The script outputs conversations with parsed turns (user input + assistant response),
tool-use noise stripped, grouped by project and date.

Check what's available:
```bash
cat /tmp/memory-payload.json | python3 -c "
import json, sys
from collections import Counter
data = json.load(sys.stdin)
print(f'{len(data[\"conversations\"])} conversations')
projects = Counter()
for c in data['conversations']:
    p = c['project'] or '(general)'
    projects[p] += 1
for p, n in sorted(projects.items(), key=lambda x: -x[1]):
    print(f'  {p}: {n}')
"
```

If no conversations found, stop.

## 2. Summarise conversations

For each conversation in the payload:

1. Read the turns
2. Determine a short session title from the overall topic
3. Categorise the content into Decisions, Changes, Discussions, Feedback
4. Write concise bullet points — not full transcripts, not single words

**Be selective:** not every turn is worth capturing. Skip:
- Routine tool use and file operations
- Debugging steps and intermediate attempts
- Questions fully answered in the same conversation
- Small talk, greetings, acknowledgments
- Implementation details (the code is in git)

**Focus on:** what would help someone (including future-you) understand what happened
in this session without reading the full conversation.

## 3. Write memory files

Resolve the target location:
- If the conversation has a project name, look it up: `ak brain project <name>`
  - If found, write to `<context>/projects/<project>/memory/<date>.md`
  - If not found, write to `shared/memory/<date>.md`
- If no project (general session), write to `shared/memory/<date>.md`

Create the `memory/` directory if it doesn't exist.

If the file already exists (multiple sessions on the same day), append the new
session as a new `## Session:` section.

## 4. Commit

Commit with explicit paths per context:

```bash
ak brain commit <context> -m "brain: memory <date>" \
  --paths <memory-file-paths>
```

No reindex needed — memory files aren't indexed entities.

## 5. Update watermark

```bash
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py \
  --set-watermark <watermark_from_payload>
```

## 6. Report

Summarise: number of sessions processed, dates covered, projects touched.

---

# Batching

For many conversations, delegate to subagents. Group by project — one subagent
per project (or per batch of projects). Each subagent receives the turns and
writes the memory files.

Maximum 4 subagents concurrently. The orchestrating agent handles the watermark
update after all subagents complete.

---

# Example

```bash
# 1. Gather
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py > /tmp/memory-payload.json
# Found 5 conversations: 3 archie, 2 tillo-platform

# 2-3. Summarise and write
# archie conversations → shared/projects/archie/memory/2026-04-18.md
# tillo conversations → tillo/projects/tillo-platform/memory/2026-04-18.md

# 4. Commit
ak brain commit shared -m "brain: memory 2026-04-18" \
  --paths projects/archie/memory/2026-04-18.md
ak brain commit tillo -m "brain: memory 2026-04-18" \
  --paths projects/tillo-platform/memory/2026-04-18.md

# 5. Update watermark
python3 .../memory-prep.py --set-watermark 1713434567000
```
