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
- **No memory file exists** → process (new session)
- **Memory file exists but distilled log is newer** → process only new turns
  (append content for turns with `when` after the memory file's mtime)
- **Memory file exists and is up to date** → skip

**Filtering:** Skip sessions that are clearly trivial:
- Total user content across all turns < 100 characters
- Sessions that are only test/debug commands ("what's 1+1", "exit", "tell me about yourself")

When in doubt, process it — a slightly redundant memory file costs nothing, but
missing a decision or finding is a real loss.

## 3. Batch and dispatch

Always delegate processing to subagents — even for a single session. This keeps
the main session context clean and avoids polluting interactive or background
sessions with log content.

Follow the Batching section below to size batches and dispatch.

## 4. Commit

After all sessions are processed:

```bash
ak brain reindex
ak brain commit "memory: <date range or summary>" --paths _archie/memory/ --paths index.yaml
```

## 5. Report

Summarise: sessions processed, memory files written/updated, sessions skipped.

---

# Batching

When processing many sessions, delegate to subagents to maintain quality. A single
agent processing too many sessions will compress output and lose detail.

## Sizing rules

| Session size | Batch strategy |
|---|---|
| Small (<10 turns) | 5 sessions per subagent |
| Medium/Large (10+ turns) | 1 session per subagent |

Group small sessions of similar size together so subagents take roughly equal time.

## Dispatch

Run up to 4 subagents in parallel. Each subagent gets this prompt:

```
Read the "Processing Instructions" section of the memory update skill at
<path-to-this-skill>/SKILL.md — follow its conventions exactly.

Process these session logs into memory files:
- <path/to/log1.yaml>
- <path/to/log2.yaml>

Write each memory file to ~/.archie/brain/_archie/memory/<date>-<project>-<session_id_short>.md
where session_id_short is the first 4 chars of the session_id field in the YAML.

Do NOT run ak brain reindex or commit. Just write the memory files.
```

Replace `<path-to-this-skill>` with the actual filesystem path to this skill file.

## Execution

1. Precompute all batches and group into rounds of 4
2. Execute each round (4 parallel subagents)
3. After all rounds complete, verify output (spot-check a few files)
4. Reindex and commit once

---

# Processing Instructions

This section is the single source of truth for how to produce memory files.
Subagents should read only this section.

## Input

Distilled session logs (YAML files in `~/.archie/brain/_archie/logs/`). Each contains:
- `session_id` — unique conversation identifier
- `project` — project name or "general"
- `started` — session start timestamp
- `turns` — list of turn objects with `when`, `user`, `assistant`, and `tools` fields

The assistant text has tool blocks already stripped. The `tools` list shows what was
called, whether it succeeded, and any errors — but not full tool output.

## Output

One memory file per session at `~/.archie/brain/_archie/memory/<date>-<project>-<session_id_short>.md`

Where:
- `date` — from the log's `started` field (YYYY-MM-DD)
- `project` — from the log's `project` field
- `session_id_short` — first 4 characters of `session_id`

## Format

**Frontmatter:**
```yaml
---
name: <Short descriptive title of the session>
summary: <One-line summary of key topics/decisions>
tags: [<project-name>, <domain>, <relevant-topics>]
---
```

**Body structure:**
```markdown
# Topic Heading

Discussed how to query the brain — two-step pattern: index lookup first,
grep fallback.

Decided context routing should be content-based, not source-tagged. Rejected
tag-based routing because tags are inconsistently applied and content analysis
is more reliable.

Action: changed commit_context() to accept explicit --paths flag. Previously
it staged everything, which swept up other sessions' uncommitted work.

Correction: initially hardcoded ~/dev as project root. Should resolve from
project_dir in ~/.agent-kit/config.yaml.

Finding: brain.db stores watermarks as Unix milliseconds, not seconds.

CURRENT STATUS: All features implemented. Memory pipeline operational.
Blocked on agent-kit release for the new search scoring.
```

## Conventions

**Structure:**
- Topic headings group related exchanges (not one heading per turn)
- Combine closely related turns into one paragraph
- Capture progression: who raised what, who pushed back, how it evolved
- End with `CURRENT STATUS` if work is in progress or unresolved

**Prefixes:**
- **Discussed** — topics explored, options considered
- **Decided** — choices made (include rejected alternatives and why)
- **Action** — concrete changes made (files written, commands run, PRs created)
- **Correction** — mistakes caught and fixed (what was wrong, what's correct)
- **Finding** — discovered facts worth remembering (specific, not obvious)

**What to capture (the memory file should answer most questions without needing
the original log):**
- Specific findings: exact numbers, names, IPs, ports, error messages, measurements
- Decisions AND rejected alternatives with reasoning
- Architecture choices and trade-offs discussed
- Open questions and unresolved items left for future sessions
- Dependencies and blockers
- External references: PR links, issue IDs, brain entries created/updated
- Configuration values, paths, commands that were non-obvious

**What to skip:**
- Step-by-step debugging sequences (unless the root cause is informative)
- Tool output details and file contents
- Routine file reads, greetings, small talk
- Intermediate failed attempts (unless the failure pattern is worth remembering)
- The agent's internal reasoning about how to respond

**Quality check — ask yourself:**
- Could someone reconstruct the key decisions from this file alone?
- Are specific values preserved (not "updated the config" but "set timeout to 30s")?
- Would a future session know what was tried and rejected?
- Are open threads clearly marked?
