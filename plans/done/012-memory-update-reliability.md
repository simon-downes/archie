# 012: Memory Update Reliability

## Objective

Improve the `action-memory-update` skill to eliminate ad-hoc shell scripting during
execution. The current skill leaves identification, filtering, batching, and session
comparison to the orchestrating agent's interpretation — leading to unreliable grep/regex
attempts on YAML files and inconsistent naming logic.

Replace with: a deterministic script that handles all mechanical work, a `.processed`
state file that tracks what's been handled, and a precise subagent contract with
extraction commands and structured output.

## Context

During a memory-update run (2026-05-26), the orchestrating agent:
- Tried grep to count turns (failed due to YAML indentation)
- Got the memory filename convention wrong (extracted wrong part of UUID)
- Had to iterate multiple times before finding `yq` as the right tool
- Manually inspected trivial sessions one by one
- Revisited all 100+ logs every run because there's no state tracking

The skill's current language is vague enough that each run re-invents the discovery
logic. The batching rules are simple arithmetic but still require the agent to
implement them from scratch.

## Requirements

1. A Python script MUST handle session identification, trivial filtering, and batch
   computation — the orchestrating agent MUST NOT parse YAML or compute batches itself.

2. A `.processed` file MUST track all previously handled sessions with turn count,
   status (written/skipped), and processed_at timestamp.

3. Sessions in `.processed` with unchanged turn counts MUST be skipped entirely.

4. Sessions in `.processed` with increased turn counts MUST be flagged as `delta` —
   only turns after `processed_at` are processed.

5. Sessions not in `.processed` with total user content < 100 characters MUST be
   auto-skipped and recorded in `.processed` as status `skipped`.

6. The script MUST output JSON with pre-computed batches following the sizing rules:
   <10 turns → up to 5 per batch, 10+ turns → 1 per batch.

7. Each file entry in the batch output MUST include: path, mode (new/delta), turns,
   and processed_at (for delta mode).

8. The skill MUST define the exact subagent prompt template including yq extraction
   commands for session metadata and turn filtering.

9. Subagents MUST validate that actual turn count >= expected turns before writing.
   If fewer, report an error for that session.

10. Subagents MUST output a structured results line (`RESULTS: {...}`) with session_id,
    status, actual turn count, and output filename.

11. The orchestrating agent MUST update `.processed` only after confirming subagent
    results — not speculatively.

12. Delta processing MUST append to existing memory files (read existing + new turns)
    rather than rewriting from scratch.

## Design

### Script location

Python script at `persona/skills/action-memory-update/identify.py`. Bundled with the
skill, not in agent-kit — this is skill-specific logic, not a general-purpose tool.

### .processed format

```
# Tab-separated: session_id, turns, status, processed_at
7d19ff6a	56	written	2026-05-26T11:00:00
3aeb9424	1	skipped	2026-05-26T11:00:00
04db6be3	7	written	2026-05-16T11:00:00
```

Lives at `~/.archie/brain/_archie/logs/.processed`. Plain text, easy to inspect/edit.

### Script output (JSON to stdout)

```json
{
  "batches": [
    [
      {"path": "/full/path/to/log.yaml", "mode": "new", "turns": 56}
    ],
    [
      {"path": "/full/path/to/log.yaml", "mode": "delta", "turns": 12, "processed_at": "2026-05-16T11:00:00"},
      {"path": "/full/path/to/log.yaml", "mode": "new", "turns": 3},
      {"path": "/full/path/to/log.yaml", "mode": "new", "turns": 5},
      {"path": "/full/path/to/log.yaml", "mode": "new", "turns": 2},
      {"path": "/full/path/to/log.yaml", "mode": "new", "turns": 4}
    ]
  ],
  "skipped": 3,
  "up_to_date": 87,
  "summary": "5 to process (4 new, 1 delta), 3 trivial skipped, 87 up-to-date"
}
```

### Subagent results contract

```
RESULTS: {"results": [
  {"session_id": "7d19ff6a", "status": "written", "turns": 56, "file": "2026-05-19-archie-7d19.md"},
  {"session_id": "3465f816", "status": "skipped", "turns": 2, "reason": "trivial after reading"}
]}
```

### Delta mode processing

Subagent receives the existing memory file path and `processed_at` timestamp. It:
1. Reads the existing memory file for context
2. Extracts only turns after `processed_at` using yq
3. Appends new topic sections or extends existing ones
4. Updates `CURRENT STATUS` section
5. Does not rewrite existing content

---

## Milestones

1. **Identification script**

   Approach:
   - Python script using uv inline dependency metadata (`# /// script` block with
     `pyyaml` dependency). Executed via `uv run identify.py` — no pre-installed
     packages required.
   - Resolves paths dynamically: reads `~/.agent-kit/config.yaml` for `brain.dir`
     and `agent` name, derives logs dir as `<brain_dir>/_<agent>/logs/` and memory
     dir as `<brain_dir>/_<agent>/memory/`.
   - Reads all `.yaml` files in logs dir, parses session_id, project, started,
     turn count, and total user content length.
   - Compares against `.processed` file.
   - Applies trivial filter, computes batches, writes newly-skipped to `.processed`.
   - ⚠️ Must handle hyphenated project names in filenames (don't parse filename for
     session_id — read it from the YAML).

   Tasks:
   - Write `identify.py` with CLI interface (no args needed, paths are conventional)
   - Parse `.processed` file (create if missing)
   - Iterate log files, extract metadata via PyYAML
   - Classify each session: up-to-date / new / delta / trivial
   - Auto-skip trivial sessions (update `.processed`)
   - Compute batches from actionable sessions
   - Output JSON to stdout, summary to stderr

   Deliverable: Running `python identify.py` outputs correct JSON batches and updates
   `.processed` for trivial sessions.

   Verify: Run against current logs directory — should show 0 new (since we just
   processed everything) and the previously-skipped trivials in `.processed`.

2. **Rewrite skill workflow**

   Approach:
   - Replace steps 2-3 (identification + batching) with "run the script"
   - Define exact subagent prompt template with yq commands
   - Define results contract
   - Add delta mode to Processing Instructions
   - Remove all vague language about listing/comparing files

   Tasks:
   - Rewrite Workflow section (steps 1-5 become: digest, run script, dispatch, update .processed, commit, report)
   - Write subagent prompt template with: skill path, extraction commands, file list,
     validation rules (turn count >= expected, error if fewer), output format
   - Include exact yq commands in the prompt template for: reading metadata, filtering
     turns by timestamp, counting turns
   - Add "Delta Mode" subsection to Processing Instructions
   - Update Batching section to reference script output (remove manual sizing logic)
   - Document `.processed` format and location

   Deliverable: Skill is self-contained — an agent following it produces reliable
   results without improvising shell commands.

   Verify: Read the skill end-to-end and confirm no step requires the agent to
   parse YAML, compute filenames, or decide batch sizes.

3. **Integration test**

   Approach:
   - Run the full updated workflow against current state
   - Seed `.processed` from the sessions we just processed (bootstrap step)
   - Verify the script correctly identifies everything as up-to-date

   Tasks:
   - Bootstrap `.processed` from existing memory files (one-time script or manual)
   - Run `ak digest` + `identify.py` and confirm empty batch output
   - Manually add a test log or wait for a new session, re-run, confirm it appears

   Deliverable: End-to-end run completes with correct identification and no
   manual intervention.

   Verify: Script output shows 0 actionable sessions after bootstrap.
