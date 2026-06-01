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

Ensure distilled logs are up to date by running the digest tool (refer to `# Available Tools`).

## 2. Identify sessions and compute batches

Run the identification script (located alongside this skill):

```bash
uv run <skill-dir>/scripts/identify.py
```

Where `<skill-dir>` is the directory containing this SKILL.md file.

The script outputs JSON to stdout with pre-computed batches and a summary to stderr.
It also auto-skips trivial sessions (updating `.processed`).

If the output shows 0 actionable sessions, stop — nothing to do.

## 3. Dispatch subagents

Process batches in rounds of up to 4 parallel subagents. For each batch, use the
prompt template below.

**Do NOT** parse YAML, count turns, compute filenames, or decide batch sizes — the
script has already done this.

### Subagent prompt template

```
Read the "Processing Instructions" section of <skill-path>/SKILL.md — follow its
conventions exactly.

## Extracting session data

Use these yq commands to read log files:

Session metadata:
  yq '.session_id' <file>
  yq '.project' <file>
  yq '.started' <file>

All turns:
  yq '.turns' <file>

Turn count:
  yq '.turns | length' <file>

Turns after a timestamp (for delta mode):
  yq '[.turns[] | select(.when > "<timestamp>")]' <file>

## Sessions to process

<for each file in the batch>
- <path> | mode: <mode> | expected turns: <turns><if delta> | only after: <processed_at></if>
</for each>

## Validation

Before writing each memory file, confirm the actual turn count from the file is >=
the expected turns listed above. If fewer turns exist, report an error for that
session and do not write a memory file.

## Output

Write memory files to ~/.archie/brain/_archie/memory/

After processing all sessions, output a results line on its own starting with RESULTS:

RESULTS: {"results": [{"session_id": "...", "status": "written|skipped|error", "turns": <actual_count>, "file": "<filename or null>", "reason": "<if skipped/error>"}]}

Do NOT run brain reindex or commit. Just write the memory files and output results.
```

## 4. Update .processed

After each subagent completes, parse the `RESULTS:` line from its output. For each
result:

- `status: "written"` → add/update entry: `<session_id>\t<turns>\twritten\t<now>`
- `status: "skipped"` → add/update entry: `<session_id>\t<turns>\tskipped\t<now>`
- `status: "error"` → do not update `.processed` (will be retried next run)

The `.processed` file lives at `<logs_dir>/.processed` (same directory as the logs).

## 5. Commit

After all batches are processed, reindex the brain and commit the memory files
(refer to `# Available Tools`).

## 6. Report

Summarise: sessions processed, memory files written/updated, sessions skipped, errors.

---

# .processed File

Tracks all previously handled sessions. Tab-separated, one session per line:

```
<session_id>\t<turns>\t<status>\t<processed_at>
```

Fields:
- `session_id` — full UUID from the log's `session_id` field
- `turns` — turn count at time of processing
- `status` — `written` or `skipped`
- `processed_at` — ISO timestamp of when it was processed

The identification script reads this to determine what's new, what's a delta, and
what's already handled.

---

# Processing Instructions

This section is the single source of truth for how to produce memory files.
Subagents should read only this section.

## Input

Distilled session logs (YAML files). Each contains:
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

## Delta Mode

When processing a delta session (mode: `delta` with a `processed_at` timestamp):

1. Read the existing memory file at the output path above
2. Extract only turns with `when` after the `processed_at` timestamp
3. Append new topic sections or extend existing ones — do NOT rewrite existing content
4. Update the `CURRENT STATUS` section to reflect the latest state
5. If the new turns are trivial (greetings, no decisions/findings), skip the session

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
project_dir in ~/.archie/config.yaml.

Finding: brain.db stores watermarks as Unix milliseconds, not seconds.

CURRENT STATUS: All features implemented. Memory pipeline operational.
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
