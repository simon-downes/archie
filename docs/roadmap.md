# Archie — Roadmap

The next evolution of Archie, informed by research into PAI v5, OpenClaw, and Archon.

## Phase 1: Clarity & Immediate Benefit

Persona and config improvements that deliver value immediately with no infrastructure
dependencies.

1. **SOUL.md** — Extract personality/voice from `archie.prompt.md` into an evolvable file.
   Opinions, tone, writing style, relationship dynamic. Loaded as system prompt.

2. **ME.md** — Structured user profile. Communication preferences, role, priorities,
   decision-making style. Loaded as guidance/steering.

3. **Core facts file** — Small always-injected durable facts (project conventions, key
   references, tool preferences). Avoids repeated brain lookups for constant context.

4. **Config propagation** — `archie install` merges new defaults into existing config
   rather than skip-if-exists. New mounts and credentials propagate automatically.

## Phase 2: Infrastructure

Foundation for multi-session and autonomous work.

5. **Worktree sessions** (plan 006) — Multiple concurrent project sessions, each in its
   own git worktree. Remove single-session-per-project restriction.

6. **Background tasks** (plan 004) — `archie shell` accepts commands, `archie task` for
   fire-and-forget work via `ak tasks`.

## Phase 3: Observability

Cheap instrumentation that enables the learning loop later.

7. **PostToolUse + Stop hooks** — Log tool name, success/failure, timestamp to JSONL.
   Session end metadata (duration, tool count).

8. **`archie stats` command** — Read JSONL logs, print summary (sessions this week,
   tool usage, error rates).

## Phase 4: Automation

Depends on Phase 2 (background tasks).

9. **Background agent config** — Non-interactive prompt, auto-approve tools, no
   clarification questions, write results to discoverable location.

10. **Heartbeats / scheduled tasks** — Cron triggers `archie task` with maintenance
    prompts. Daily/weekly admin, brain processing, inbox triage.

11. **Automated session analysis** — First scheduled task. Processes session logs since
    last run, extracts corrections/failures/patterns, writes to `signals.yaml`.

## Phase 5: Learning Loop

Depends on Phase 3 (observability data) + Phase 4 (automation to run analysis).

12. **Signal effectiveness tracking** — Tag signals with dates, track whether same error
    category recurs. Surface ineffective signals for rewording/removal.

13. **Cross-session pattern aggregation** — Identify patterns across sessions (tool
    failure rates, recurring mistakes, behavioural trends).

## QoL (slot in anywhere)

- **`archie --general`** — Force general session regardless of cwd.
- **Live config/mount updates** — Avoid session restarts when mounts or config change.
