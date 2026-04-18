---
name: action-brain-memory
description: >
  Summarise recent conversations into structured memory files in the brain.
  Uses a prep script to extract clean turn pairs from kiro-cli history, then
  produces turn-by-turn summaries grouped by topic. Use when asked to "process
  conversations", "update memory", "summarise recent sessions", "what did we
  discuss", or "catch up on recent work".
---

# Purpose

Produce structured summaries of conversations so future sessions can quickly
answer: "what have we discussed recently?", "what did we do this week?", "what
did we decide about X?"

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

## File Location

All memory files live in `~/.archie/brain/_memory/` — a top-level directory
alongside `_raw/`, outside any context's git repo. Device-local, not portable.

**Naming:** `<date>-<identifier>.md`
- Project sessions: `2026-04-18-archie.md`, `2026-04-14-tillo-platform.md`
- General sessions: `2026-04-18-c951.md` (first 4 chars of conversation_id)

One file per day per project. Multiple sessions on the same project in one day
append to the same file. General sessions are always one file per conversation.

Create the `_memory/` directory if it doesn't exist.

## File Structure

```markdown
---
date: 2026-04-18
project: archie
---

# Brain Read/Write Capability

Discussed how to query the brain — two-step pattern: index lookup first, grep
fallback. Index is the entry point for known entities, rg for broad searches
across content.

Discussed how to prevent duplicate entities when writing. Index is the dedup
mechanism — check before creating. Reindex rebuilds from filesystem state so
is self-healing.

Decided context routing should be content-based, not source-tagged. Raw items
dropped in _raw/inbox should be zero-friction — no tagging required. The LLM
analyses content and matches against existing brain indexes to determine context.

# Concurrent Brain Access

Discussed risks of multiple agents writing to the same context simultaneously.
Main concerns: git add -A sweeping up other agents' files, and two reindexes
clobbering index.yaml.

Decided to add flock locking to reindex_context() — invisible to the LLM,
prevents index corruption.

Action: changed commit_context() to accept explicit --paths instead of git
add -A. Each agent commits only the files it wrote.

Correction: initially hardcoded ~/dev in memory-prep.py. Should use project_dir
from agent-kit config.

# Knowledge Directory Structure

Discussed how to organise knowledge/. Start flat, introduce subdirectories only
when 5+ related files cluster. Slugs are stable identifiers in the index — paths
can change when files are reorganised.
```

## Conventions

**Headings** break the conversation into topic sections. A long conversation may
have several topics; a short one may have just one.

**Turn summaries** are short paragraphs — one to three sentences each. Produce
one summary per turn (user input + assistant response pair). Closely related
turns on the same micro-topic can be combined, but don't collapse an entire
topic into a single bullet.

Capture the **progression** — who raised what, who pushed back, how the approach
evolved. "Initially planned X, user pushed back on complexity, landed on Y" is
much more useful than just "Decided Y."

**Prefixes** indicate the nature of each entry:
- **Discussed** — explored a topic, considered options, analysed tradeoffs
- **Decided** — made a choice with rationale
- **Action** — implemented something, made a change, completed work
- **Correction** — user pushed back, fixed a mistake, redirected approach

Not every paragraph needs a prefix — use them when they add clarity.

**End with current status** — if work is in progress, note where things stand:
what's done, what's next, what's blocked. This is the most useful part for
picking up work in a future session.

---

# Workflow

## 1. Gather conversations

```bash
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py > /tmp/memory-payload.json
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

## 2. Summarise

For each conversation, read the turns and produce the memory file content.

**Be selective:** not every turn is worth capturing. Skip:
- Routine file reads and tool operations
- Debugging steps and intermediate attempts
- Questions fully answered in the same exchange
- Greetings, acknowledgments, small talk

**Preserve progression:** the summary should read top-to-bottom as a narrative
of what happened. Someone reading it should understand the arc of the conversation.

**Group related turns** under topic headings. Don't create a heading per turn —
group exchanges about the same topic together.

## 3. Write files

Write to `~/.archie/brain/_memory/`:
- Project conversation → `<date>-<project>.md`
- General conversation → `<date>-<first 4 chars of conversation_id>.md`

If a project file for that date already exists, append the new session's content
as additional topic sections.

No git commit needed — `_memory/` is outside context repos.

## 4. Update watermark

```bash
python3 ~/.kiro/skills/action-brain-memory/scripts/memory-prep.py \
  --set-watermark <watermark_from_payload>
```

## 5. Report

Summarise: number of sessions processed, dates covered, files written.

---

# Batching

For many conversations, delegate to subagents grouped by project. Each subagent
receives the turns for its conversations and writes the memory files.

Maximum 4 subagents concurrently. The orchestrating agent updates the watermark
after all subagents complete.
