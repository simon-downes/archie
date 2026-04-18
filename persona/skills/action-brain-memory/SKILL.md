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
    p = c['project'] or '(general)'
    print(f'  {p:20s} {len(c[\"transcript\"]):>6} chars')
"
```

The `project` field is the project name from the working directory, or empty string
for general (non-project) sessions. Context routing is determined by the agent during
extraction, not by the script.

If no conversations found, stop.

## 2. Process conversations

For each conversation in the payload, delegate extraction to a `general-purpose`
subagent. The subagent receives:

- The transcript text
- The target brain context
- The project name
- Instructions to extract and write to the brain

**Batching:** maximum 4 subagents run concurrently. Group conversations into
batches — by project if there are many, or simply by count. Each subagent can
handle multiple transcripts and write to multiple contexts as needed.

### Subagent prompt template

```
Process these conversation transcripts and extract valuable information to the brain.

Project: {project} (empty = general session)

For each transcript, extract:
- **Decisions** — choices made with rationale
- **Knowledge** — facts, patterns, technical information
- **Progress** — significant work completed, changes made
- **Feedback** — moments where the user pushed back, corrected a mistake,
  redirected the approach, or praised something that worked well. Capture
  what happened and what the takeaway is. Includes: incorrect assumptions,
  jumping to implementation without discussion, overcomplicating a solution,
  implementations that failed, and things that went particularly well.

**What to capture:**
- Decisions with rationale that affect future work
- Technical knowledge that would be useful in a future session
- Architectural patterns, conventions, and design principles established
- Feedback moments (positive, negative, corrections)
- Significant progress milestones

**What to skip:**
- Routine tool use and file operations (the code is in git)
- Debugging steps and intermediate attempts that didn't lead anywhere
- Code snippets and implementation details (git is the source of truth)
- Questions that were fully answered in the same conversation
- Small talk, greetings, acknowledgments
- Temporary workarounds that were immediately replaced
- Information that's already documented in project READMEs or docs
- Exploratory discussion that didn't result in a decision or insight

**Temporal awareness:** conversations are processed oldest-first. Later
conversations may supersede earlier ones. When extracting:
- If a decision in an older conversation was reversed in a later one,
  capture only the final decision (or note the evolution if the reasoning
  is valuable)
- Don't capture progress that was later undone or replaced
- Prefer the most recent understanding of a topic over earlier, potentially
  outdated information
- For the initial bulk import of historical conversations, be especially
  selective — focus on decisions and knowledge that are still relevant today

Write each extracted item to the brain following the `action-brain-write` pattern:
1. Determine the correct brain context for each item — use `ak brain index` to check
   where related entities already exist. The project name is a hint but not a hard rule;
   any conversation can produce writes to any context.
2. Check the brain index for existing entities on the same topic
3. If an existing entity covers the same topic, update it — don't create a duplicate
4. New entities go to `<context>/knowledge/<slug>.md` with frontmatter:
   ```
   tags: [relevant, tags]
   summary: One-line description
   source: conversation
   ```
5. After all writes per context: `ak brain reindex <context>`
6. Commit with explicit paths:
   `ak brain commit <context> -m "brain: memory extraction" --paths <files> --paths index.yaml`

Corrections go to `shared/knowledge/archie-feedback.md` — a single accumulating
file of behavioural observations. Append new entries, don't overwrite existing
ones. Format each entry as:

```markdown
## <date> — <short description>
**What happened:** <description of the event>
**Takeaway:** <the lesson or reinforcement>
**Type:** positive | negative | correction
```

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

# First Run / Initial Import

On first run, the watermark is 0 so all conversations are returned. This is a
one-time bulk import that needs special handling.

**Volume:** use `--project` to process one project at a time, or batch by project
name from the payload.

**Precursor projects:** some projects may be predecessors of current ones (e.g.
early prototypes that evolved into the current codebase). When spawning subagents,
tell them which projects are precursors and what they became:

> "The following projects are precursors to archie and should be treated as
> archie context: ai-config, agent-workspace, ax, cli-tools, agent-executor"

**Anchor against current state:** before extracting from historical conversations,
read the current project documentation (README, CONTRIBUTING, docs/) and provide
it to the subagent as context. The agent should only extract information that is
still relevant to the current state. Anything that contradicts current docs or
code is dead history — skip it.

**Be highly selective:** the initial import will contain a lot of noise —
dead-end explorations, reversed decisions, superseded designs. Extract only:
- Decisions and rationale that are still reflected in the current codebase
- Knowledge that remains true and useful
- Feedback patterns that are still relevant
- Design principles that carried forward

After the initial import, subsequent runs will be incremental and much simpler —
just new conversations since the last watermark.

---

# Example

```bash
# 1. Gather
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py > /tmp/memory-payload.json
# Output: 12 conversations — 3 for tillo-platform, 7 for archie, 2 general

# 2. Process — spawn subagents with batches of transcripts
# Subagent 1: tillo-platform conversations (3 transcripts)
# Subagent 2: archie conversations (7 transcripts)
# Subagent 3: general conversations (2 transcripts)
# Each subagent determines context routing per extracted item

# 3. Update watermark
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py --set-watermark 1713434567000

# 4. Report
# 5 knowledge entities created across shared and tillo contexts
# 3 existing entities updated
```
