---
name: action-brain-memory
description: >
  Extract decisions, knowledge, and progress from recent conversations and write them
  to the brain. Reads conversation transcripts from kiro-cli's SQLite database, processes
  all conversations since the last run, and updates the brain with extracted information.
  Use when asked to "process conversations", "update memory", "extract from sessions",
  "what did we discuss", or "catch up on recent work".
---

# Purpose

Close the learning loop: read recent conversation transcripts, extract valuable
information (decisions, knowledge, progress, significant changes), and write it to
the brain so future sessions have that context.

---

# When to Use

- Manually triggered to catch up on recent conversations
- After a series of work sessions to capture what was learned
- When asked to process or remember recent conversations

# When Not to Use

- Processing raw files from `_raw/inbox/` (use `action-brain-ingest`)
- Direct brain writes from the current conversation (use `action-brain-write`)

---

# Data Source

Conversation transcripts are stored in kiro-cli's SQLite database:

```
~/.local/share/kiro-cli/data.sqlite3
```

Table: `conversations_v2`
- `key` — working directory path (maps to project)
- `conversation_id` — unique conversation UUID
- `value` — JSON blob containing `transcript` (array of strings)
- `updated_at` — Unix timestamp in milliseconds

The `transcript` field is a compact, human-readable summary of each conversation
turn. User messages are prefixed with `>`. Much smaller than the full history.

---

# Workflow

## 1. Read the watermark

Check when memory was last processed:

```bash
sqlite3 ~/.archie/brain/shared/brain.db "
CREATE TABLE IF NOT EXISTS memory_watermark (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_processed_at INTEGER NOT NULL
);
SELECT last_processed_at FROM memory_watermark WHERE id = 1;
"
```

If no watermark exists, this is the first run. Process all conversations, or ask
the user how far back to go.

## 2. Query new conversations

Fetch conversations updated since the watermark:

```bash
sqlite3 ~/.local/share/kiro-cli/data.sqlite3 "
SELECT key, conversation_id, value, updated_at
FROM conversations_v2
WHERE updated_at > <watermark>
ORDER BY updated_at ASC
"
```

If no new conversations, report "nothing to process" and stop.

## 3. Process each conversation

For each conversation:

### a. Extract the transcript

Parse the JSON `value` and read the `transcript` array. Join into a single text
block for analysis.

### b. Resolve context

Map the conversation's `key` (working directory) to a brain context:

1. Extract the project name from the path (first directory under project_dir)
2. Look up the project in the brain: `ak brain project <name>`
3. If found, use the project's context
4. If not found (general session, unknown project), route to `shared`

### c. Extract information

From the transcript, identify and extract:

**Decisions** — choices made with rationale. Examples:
- "We decided to use content-based routing instead of source tagging"
- "Chose flock for per-context locking"
- "Will process raw items individually, not as a batch"

**Knowledge** — facts, patterns, technical information learned. Examples:
- "Aurora PostgreSQL failover takes ~30 seconds"
- "Git add with explicit paths is safe for concurrent agents"
- "kiro-cli stores transcripts in conversations_v2"

**Progress and changes** — significant work completed. Examples:
- "Added brain read/write skills (tool-brain, action-brain-read, action-brain-write, action-brain-ingest)"
- "Refactored commit_context to accept explicit paths for concurrent safety"

**Skip:** routine tool use, debugging steps, code that was written (it's in git),
small talk, questions that were answered in the same conversation.

Focus on information that would be valuable in a future session where the
conversation context is gone.

### d. Write to brain

For each extracted item, follow the `action-brain-write` pattern:

1. Check the brain index for existing entities on the same topic
2. If exists, update the existing entity with new information
3. If new, create a knowledge file with appropriate frontmatter

Knowledge files from memory extraction should include a `source` tag in frontmatter:

```markdown
---
tags: [aws, aurora, databases]
summary: Aurora PostgreSQL failover behaviour and timing
source: conversation
---

# Aurora PostgreSQL Failover

- Failover takes approximately 30 seconds
- Writer endpoint DNS TTL is 5 seconds
```

### e. Reindex and commit

After processing all extractions for a context:

```bash
ak brain reindex <context>
ak brain commit <context> -m "brain: memory extraction <date>" \
  --paths <file1> --paths <file2> --paths index.yaml
```

## 4. Update the watermark

After all conversations are processed:

```bash
sqlite3 ~/.archie/brain/shared/brain.db "
INSERT OR REPLACE INTO memory_watermark (id, last_processed_at)
VALUES (1, <highest_updated_at_processed>);
"
```

Use the highest `updated_at` value from the processed conversations, not the
current time — this avoids missing conversations that were updated during processing.

## 5. Report

Summarise what was extracted:
- Number of conversations processed
- Entities created/updated per context
- Key decisions and knowledge captured

---

# Handling Large Transcripts

Most transcripts are under 30K characters and fit in a single pass. For very long
conversations (60K+):

- Focus on the most recent portion if the conversation spans multiple days
- Extract the highest-value items first (decisions > knowledge > progress)
- It's better to capture the important things well than everything superficially

---

# Example

**Conversations since last run:**
1. `archie` project — discussed brain read/write design, decided on content-based
   routing, implemented skills and CLI commands
2. `tillo-platform` — debugged Aurora failover, decided on multi-AZ configuration

**Processing conversation 1 (archie):**
- Context: `shared` (archie project maps to shared context)
- Decisions extracted:
  - Content-based context routing (not source tagging)
  - Single commit per context per operation
  - Explicit path staging for concurrent safety
- Knowledge extracted:
  - Brain index structure and conventions
  - Reindex is self-healing (last reindex wins)
- Progress: brain read/write capability implemented

**Processing conversation 2 (tillo-platform):**
- Context: `tillo`
- Knowledge extracted:
  - Aurora failover timing and DNS TTL behaviour
- Decisions extracted:
  - Multi-AZ configuration for production Aurora clusters
