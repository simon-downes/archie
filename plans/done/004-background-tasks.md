# Archie — Background Task Support

## Objective

Enable Archie to dispatch and execute background tasks by extending `archie shell` to
accept arbitrary commands, adding an `archie task` convenience command for creating
tasks via `ak tasks`, and documenting usage in the agent guidance. Depends on agent-kit
task runner (`ak tasks` branch).

## Requirements

### Shell Command Enhancement

- MUST extend `archie shell` to accept an optional command after `--`
  - AC: `archie shell` with no args starts interactive bash (current behaviour preserved)
  - AC: `archie shell -- <command> [args...]` runs the command in the sandbox and exits
  - AC: Non-interactive invocations skip the header display
  - AC: Exit code from the container command is propagated

### Container Naming for Tasks

- MUST support a `--name` option on `archie shell` for custom container naming
  - AC: `archie shell --name my-task -- command` creates container `archie-task-my-task`
  - AC: Without `--name`, current naming behaviour preserved (project-based or general)
  - AC: Named containers skip the duplicate session check (multiple task containers allowed)

### Task Convenience Command

- MUST add `archie task` command that creates an `ak tasks` entry
  - AC: `archie task --name <name> -- kiro-cli chat --no-interactive --trust-all-tools "<prompt>"`
    creates a task with command `archie shell` and appropriate args
  - AC: The stored command is `archie` with args
    `["shell", "--name", "<name>", "--", "kiro-cli", "chat", "--no-interactive", "--trust-all-tools", "<prompt>"]`
  - AC: Prints the task ID returned by `ak tasks create`
  - AC: Requires `ak` to be available on the host (already a prerequisite)

### Agent-Kit Guidance Update

- MUST document `ak tasks` usage in the tool guidance
  - AC: Added to `_archie/tools.md` in the brain (Agent Kit section)
  - AC: Covers: `ak tasks create`, `ak tasks list`, `ak tasks status`, `ak tasks log`
  - AC: Includes the convention for sandbox tasks:
    `ak tasks create --name <name> -- archie shell --name <name> -- <command>`
  - AC: Guidance on when to create background tasks vs use subagents
  - AC: Guidance on checking task status on demand (not injected at session start)

## Technical Design

### Shell Enhancement

Minimal change to `cli.py` shell command: add `click.argument('command', nargs=-1)` and
`click.option('--name')`. If command args provided, pass them to `run_container()` instead
of `["/bin/bash"]`. If `--name` provided, pass to `run_container()` as a new
`container_name` parameter.

`run_container()` in `docker.py` needs a new optional `container_name` parameter. When
provided, it overrides the auto-generated name and skips the duplicate session check.
Non-interactive invocations (no tty) already skip `-it` — no change needed there.
Skip `display_header()` when `container_name` is provided (task mode).

### Task Command

Thin wrapper in `cli.py`. Constructs the `ak tasks create` shell command and runs it
via `subprocess.run`. Does not import agent-kit — calls it as a CLI tool, keeping the
dependency boundary clean.

### No Automatic Readback

Background task results are not injected at session start. The agent checks task status
on demand via `ak tasks list`/`ak tasks status` when relevant (e.g. user asks about a
previous task, or the agent recalls dispatching one). This avoids wasting tokens on
sessions that don't care about background tasks.

### No New Agent Config

Background tasks use the existing agent configurations. The `kiro-cli chat --agent <name>`
flag in the task prompt selects the agent. No dedicated background-task agent needed
initially — the caller specifies which agent to use.

## Milestones

1. **Extend `archie shell` to accept commands and custom names**
   Approach:
   - Modify `shell` command in `cli.py`: add `click.argument('cmd', nargs=-1, required=False)`
     and `click.option('--name', default=None)`. If `cmd` provided, use it; otherwise
     default to `["/bin/bash"]`.
   - Add `container_name: str | None = None` parameter to `run_container()` in `docker.py`.
     When set: use `archie-task-{container_name}` as the container name, skip duplicate
     check, skip `display_header()`.
   - ⚠️ Click's `nargs=-1` argument consumes everything after `--`. Ensure `--name` option
     is parsed before the variadic argument.
   - Tests: verify interactive shell still works, verify command passthrough, verify custom
     naming, verify exit code propagation.
   Deliverable: `archie shell -- echo hello` runs in sandbox and exits;
   `archie shell --name test -- echo hello` uses `archie-task-test` as container name.
   Verify: Manual test — run both forms and check container names via `docker ps`.

2. **Add `archie task` command**
   Approach:
   - New Click command in `cli.py`: `--name` required option, variadic args for the command.
   - Constructs: `ak tasks create --name <name> -- archie shell --name <name> -- <args...>`
   - Runs via `subprocess.run(["ak", "tasks", "create", ...])`, captures stdout, prints
     the task ID.
   - ⚠️ `ak` must be on the host PATH. If not found, print actionable error.
   Deliverable: `archie task --name research-x -- kiro-cli chat --no-interactive --trust-all-tools "research X"`
   creates a task in the agent-kit database.
   Verify: `ak tasks list` shows the created task as pending.

3. **Update guidance and documentation**
   Approach:
   - Add `ak tasks` section to the Available Tools / Agent Kit guidance (the context
     entry that documents `ak` commands). Cover create, list, status, log, cancel.
   - Include the sandbox task convention:
     `ak tasks create --name <name> -- archie shell --name <name> -- <command>`
   - Add guidance on when to use background tasks vs subagents: background for
     fire-and-forget work (research, memory, ingestion), subagents for work needed
     in the current conversation.
   - Add guidance on checking task status: do it when the user asks, or when you
     recall dispatching a task in a previous session. Don't check proactively.
   - Update `docs/capabilities.md` with background task capability.
   - Update `README.md` commands table with `archie task`.
   Deliverable: Guidance and docs are complete.
   Verify: `uv run ruff check src/ && uv run ruff format --check src/`
