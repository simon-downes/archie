---
name: action-brain-memory
description: >
  Extract decisions, knowledge, and progress from recent conversations and write them
  to the brain. Uses a prep script to gather transcripts and a subagent for extraction.
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

# Workflow

## 1. Gather conversations

Run the prep script to get transcripts ready for processing:

```bash
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py > /tmp/memory-payload.json
```

The script:
- Reads the watermark from `shared/brain.db` (0 if first run)
- Queries kiro-cli's database for conversations updated since the watermark
- Extracts transcripts from JSON
- Normalises project names from paths (handles macOS/Linux differences)
- Resolves brain context per project
- Outputs a JSON payload grouped by project

Options:
```bash
# Only a specific project
python3 .../memory-prep.py --project archie > /tmp/memory-payload.json

# Override the watermark (e.g. reprocess last 24h)
python3 .../memory-prep.py --since <unix_ms_timestamp> > /tmp/memory-payload.json
```

Check the output:
```bash
cat /tmp/memory-payload.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'{len(data[\"conversations\"])} conversations')
for c in data['conversations']:
    print(f'  {c[\"project\"]:20s} ctx={c[\"context\"]:8s} {len(c[\"transcript\"]):>6} chars')
"
```

If no conversations found, stop.

## 2. Process conversations

For each conversation in the payload, delegate extraction to a `general-purpose`
subagent. The subagent receives:

- The transcript text
- The target brain context
- The project name
- Instructions to extract and write to the brain

**Batching:** maximum 4 subagents run concurrently. If more than 4 conversations,
group them — either by context (all conversations for the same context in one
subagent) or in batches of 4.

**Grouping by context is preferred** — it reduces the number of reindex/commit
operations and lets the subagent deduplicate across conversations for the same
project.

### Subagent prompt template

```
Process these conversation transcripts and extract valuable information to the brain.

Target context: {context}
Project: {project}

For each transcript, extract:
- **Decisions** — choices made with rationale
- **Knowledge** — facts, patterns, technical information
- **Progress** — significant work completed, changes made

Skip: routine tool use, debugging steps, code (it's in git), small talk.

Write each extracted item to the brain following these rules:
1. Check the brain index for existing entities: `ak brain index {context} --type knowledge`
2. If an existing entity covers the same topic, update it — don't create a duplicate
3. New entities go to `{context}/knowledge/<slug>.md` with frontmatter:
   ```
   ---
   tags: [relevant, tags]
   summary: One-line description
   source: conversation
   ---
   ```
4. After all writes: `ak brain reindex {context}`
5. Commit with explicit paths:
   `ak brain commit {context} -m "brain: memory extraction" --paths <files> --paths index.yaml`

Transcripts:

{transcripts}
```

## 3. Update the watermark

After all subagents complete successfully:

```bash
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py \
  --set-watermark <watermark_from_payload>
```

The watermark value comes from the `watermark` field in the prep script output —
it's the highest `updated_at` from the processed conversations.

## 4. Report

Summarise what was extracted:
- Number of conversations processed
- Entities created/updated per context
- Key decisions and knowledge captured

---

# First Run

On first run, the watermark is 0 so all conversations are returned. This may be
a large volume. Options:

- Process everything (may take a while but captures full history)
- Use `--since` to limit to recent conversations
- Use `--project` to process one project at a time

---

# Example

```bash
# 1. Gather
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py > /tmp/memory-payload.json
# Output: 12 conversations, 3 for tillo (ctx=tillo), 9 for others (ctx=shared)

# 2. Process — spawn 2 subagents (one per context)
# Subagent 1: tillo context, 3 transcripts
# Subagent 2: shared context, 9 transcripts

# 3. Update watermark
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py --set-watermark 1713434567000

# 4. Report
# tillo: 2 knowledge entities created, 1 updated
# shared: 5 knowledge entities created, 3 updated
```
