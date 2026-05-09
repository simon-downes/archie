# Archie — Observability

## Objective

Add lightweight instrumentation to capture session and tool usage data. Enables
the learning loop (signal effectiveness, pattern detection) and provides visibility
into how Archie is being used (session frequency, tool usage, error rates).

## Background

Kiro-cli supports hooks that fire at specific lifecycle points. Each hook receives
JSON via stdin containing session_id, tool_name, tool_input, and tool_response.
Hooks are configured in the agent JSON file.

Available hooks:
- **AgentSpawn** — session start (stdout added to context)
- **UserPromptSubmit** — each user message (stdout added to context)
- **PreToolUse** — before tool execution (can block)
- **PostToolUse** — after tool execution (has success/failure)
- **Stop** — end of each assistant turn

## Design Decisions

### What to log

**PostToolUse** — the highest-value hook. Captures:
- Which tools are used and how often
- Success/failure rates per tool
- Session context (which session used which tools)

**Stop** — end of turn. Captures:
- Turn count per session
- Session duration (first AgentSpawn to last Stop)

**AgentSpawn** — session start. Captures:
- Session start time
- Project context

We do NOT need PreToolUse or UserPromptSubmit for observability. PreToolUse is
for security/blocking. UserPromptSubmit would log user messages which is
unnecessary (conversations are already persisted by kiro-cli).

### Storage format

JSONL (one JSON object per line) in `~/.archie/logs/`. One file per day:
`~/.archie/logs/2026-05-09.jsonl`

JSONL because:
- Append-only (no corruption from concurrent writes)
- Easy to grep/filter with jq
- No schema migrations
- Trivial to rotate/clean (delete old files)

### Log schema

```json
{"ts": "2026-05-09T17:00:00Z", "event": "spawn", "session": "abc123", "project": "archie"}
{"ts": "2026-05-09T17:00:05Z", "event": "tool", "session": "abc123", "tool": "shell", "success": true}
{"ts": "2026-05-09T17:00:10Z", "event": "tool", "session": "abc123", "tool": "write", "success": true}
{"ts": "2026-05-09T17:05:00Z", "event": "stop", "session": "abc123"}
```

Minimal fields. No tool_input/tool_response (too large, already in kiro logs).
Just the facts needed for aggregation.

### Hook implementation

A single script handles all hook types. Reads JSON from stdin, extracts the
relevant fields, appends to the daily JSONL file.

```bash
#!/bin/bash
# ~/.archie/hooks/observe.sh
read -r EVENT
echo "$EVENT" | jq -c '{
  ts: (now | todate),
  event: .hook_event_name,
  session: .session_id,
  tool: .tool_name,
  success: (.tool_response.success // null),
  project: null
}' >> ~/.archie/logs/$(date +%Y-%m-%d).jsonl
```

Or a Python script for more control (project detection, filtering).

### Stats command

`archie stats` reads the JSONL files and prints a summary:

```
Sessions (last 7 days):
  Total: 23 (18 project, 5 general)
  Avg duration: 12m
  Avg tools/session: 34

Tool usage:
  shell     142  (98% success)
  write      89  (100% success)
  read       67  (100% success)
  grep       45  (100% success)
  web_search 12  (92% success)

Errors (last 7 days):
  shell: 3 failures
  web_search: 1 failure
```

### Hook configuration

Added to `archie.json` agent config:

```json
"hooks": {
  "PostToolUse": [
    {
      "command": "python3",
      "args": ["~/.archie/hooks/observe.py"],
      "timeout_ms": 5000
    }
  ],
  "AgentSpawn": [
    {
      "command": "python3",
      "args": ["~/.archie/hooks/observe.py"],
      "timeout_ms": 5000
    }
  ],
  "Stop": [
    {
      "command": "python3",
      "args": ["~/.archie/hooks/observe.py"],
      "timeout_ms": 5000
    }
  ]
}
```

### Log rotation

Simple age-based cleanup. `archie stats --clean` or a cron job removes files
older than 30 days. No compression needed at this scale.

## Requirements

### Hook Script

- MUST log PostToolUse, AgentSpawn, and Stop events to JSONL
  - AC: Each event appended as single JSON line to `~/.archie/logs/<date>.jsonl`
  - AC: PostToolUse logs: timestamp, session_id, tool_name, success boolean
  - AC: AgentSpawn logs: timestamp, session_id, project name (from cwd)
  - AC: Stop logs: timestamp, session_id
  - AC: Script completes within 5 seconds (hook timeout)
  - AC: Failures are silent (exit 0 always — observability must not break sessions)

### Agent Configuration

- MUST add hooks to archie.json agent config
  - AC: PostToolUse, AgentSpawn, and Stop hooks configured
  - AC: Hook script path resolves inside the container
  - AC: `archie install` deploys the hook script

### Stats Command

- MUST add `archie stats` command
  - AC: Reads JSONL from `~/.archie/logs/`
  - AC: Shows session count, duration, tool usage, error rates
  - AC: Default period: last 7 days
  - AC: `--days N` to adjust period
  - AC: `--clean` removes log files older than 30 days

### Log Directory

- MUST create `~/.archie/logs/` during `archie install`
  - AC: Directory exists after install
  - AC: Mounted into container (read-write) so hooks can write

## Milestones

1. **Hook script and log directory**
   Approach:
   - Create `persona/hooks/observe.py` — reads stdin JSON, extracts fields, appends to JSONL
   - Handle all three event types (spawn, tool, stop) in one script
   - Project detection from cwd for spawn events
   - Always exit 0 (observability must not break sessions)
   - Create `~/.archie/logs/` in `archie install`
   - Add logs directory to container mounts in `docker.py`
   Deliverable: Hook script exists and can be tested standalone with piped JSON.
   Verify: `echo '{"hook_event_name":"postToolUse","session_id":"test","tool_name":"shell","tool_response":{"success":true}}' | python3 persona/hooks/observe.py` creates a log entry.

2. **Agent configuration**
   Approach:
   - Add hooks section to `persona/agents/archie.json`
   - Hook command points to the script path inside the container
   - `archie install` deploys hook script to `~/.archie/hooks/observe.py`
   - Add hook script to `pyproject.toml` force-include for packaging
   Deliverable: Hooks fire during normal archie sessions.
   Verify: Run a session, use a tool, check `~/.archie/logs/<today>.jsonl` has entries.

3. **Stats command**
   Approach:
   - Add `stats` subcommand to `cli.py`
   - Read all JSONL files within the date range
   - Aggregate: session count (by project/general), tool usage counts, success rates
   - Calculate session duration (spawn to last stop with same session_id)
   - `--days N` flag (default 7)
   - `--clean` flag removes files older than 30 days
   - Add to BUILTIN_COMMANDS
   Deliverable: `archie stats` shows usage summary.
   Verify: After a few sessions, `archie stats` shows correct counts.

4. **Documentation**
   Approach:
   - Update `docs/sessions.md` or create `docs/observability.md`
   - Document log format, stats command, clean mechanism
   - Update README commands table
   Deliverable: Observability documented.
   Verify: Docs match implementation.
