# 009 — Brain Inbox/Raw Split

## Objective

Restructure the brain's ingestion and attention directories, split `action-brain-update`
into two focused skills, make memory files searchable with age-weighted scoring, and
remove hardcoded paths from the memory-prep script.

## Requirements

- MUST rename the current `_inbox/` (ingestion staging) to `_raw/`
- MUST create a new `_inbox/` as a user attention queue (decisions, conflicts, flagged items)
- MUST update all agent-kit code referencing `_inbox/` for ingestion to use `_raw/`
- MUST update `ak brain` search exclusions to exclude `_raw/` (but NOT `_inbox/` — attention items should be searchable)
- MUST add `_archie/memory/` to indexable directories with type `memory`
- MUST implement age-weighted scoring for memory type in search results
  - AC: recent memory matches rank higher than equivalent non-memory matches; old memory matches rank lower
- MUST create `action-memory-update` skill (batch memory extraction pipeline)
- MUST create `action-brain-ingest` skill (process files from `_raw/`)
- MUST remove `action-brain-update` skill
- MUST remove hardcoded `~/.archie/brain/` paths from memory-prep script
- MUST update memory file frontmatter to use `name`, `summary`, `tags` (no dedicated `project` field — project is a tag)
- MUST update BRAIN.md template with new directory semantics and memory conventions
- MUST update archie docs (`docs/brain.md`, `CONTRIBUTING.md`) and persona seeds
- MUST add memory structure/querying guidance to `persona/seeds/soul.md`
- SHOULD keep `--to-inbox` CLI flag name unchanged (muscle memory); update help text only
- SHOULD support `--type memory` filter on `ak brain search` and `ak brain index`

## Design

### Directory semantics

| Directory | Purpose | Managed by |
|-----------|---------|------------|
| `_raw/` | Ingestion staging — files awaiting processing into brain entities | Archie (via `action-brain-ingest`) |
| `_inbox/` | User attention queue — items needing human review/decision | Archie writes, Simon reads/clears |

`_raw/` is excluded from search (staging noise). `_inbox/` is searchable (attention items are meaningful content).

### Memory file format

```markdown
---
name: Brain restructure planning, inbox/raw split decision
summary: Decided to split _inbox into _raw (ingestion) and _inbox (attention), add memory indexing with age decay
tags: [archie, brain, architecture]
---

# Brain restructure planning

Discussed separating ingestion staging from user attention queue...
```

- `name` — short title (used in index)
- `summary` — one-line description (appears in search results)
- `tags` — universal relationship mechanism (replaces dedicated `project`/`person` fields)
- Date comes from filename (`2026-04-18-archie.md`), not frontmatter

### Search scoring changes

Current: `filename/title +3, tags +2, body +1`. Flat across types.

New: add type boost + age decay for memory:

| Age | Modifier |
|-----|----------|
| < 7 days | +2 |
| 7–30 days | +1 |
| 30–90 days | 0 |
| > 90 days | -1 |

Non-memory types: no age modifier (evergreen).

Final score: `base_score + age_modifier` (for memory type only).

Date extracted from filename pattern `YYYY-MM-DD-*`.

### Indexing changes

Refactor `INDEXABLE_DIRS` from a flat list to a dict mapping type → relative path:

```python
INDEXABLE_DIRS = {
    "people": "people",
    "projects": "projects",
    "knowledge": "knowledge",
    "memory": "_archie/memory",
}
```

This keeps the type name decoupled from directory location. `reindex()` iterates
`INDEXABLE_DIRS.items()` instead of the list. The index gains a `memory` key.

`--type memory` filter works on both `ak brain search` and `ak brain index` via
existing `query_index()` logic (filters by top-level key in index dict).

### Search path changes for content search (rg)

The `search()` method currently builds rg search paths via `brain_dir.iterdir()`
excluding `EXCLUDED_DIRS`. To include `_archie/memory/` without including all of
`_archie/`:

- Add `_archie` to `EXCLUDED_DIRS` (so the iterdir walk skips it)
- Explicitly append `_archie/memory` to the search paths list if it exists

This gives: `EXCLUDED_DIRS = {"_raw", "_archie", ".git"}` and search paths include
`_archie/memory/` as a special case.

### Age decay: date extraction

Date extracted from filename via regex `^(\d{4}-\d{2}-\d{2})`. If a memory file
doesn't match this pattern, it receives `age_modifier = 0` (neutral — no boost, no penalty).

### Skill split

| Old | New | Purpose |
|-----|-----|---------|
| `action-brain-update` (part 1) | `action-memory-update` | Batch pipeline: read conversations → write memory files → update signals |
| `action-brain-update` (part 2) | `action-brain-ingest` | Process files from `_raw/` → analyse → route to brain locations |

### Memory-prep script

Relocate to `persona/scripts/memory-prep.py`. Remove hardcoded brain path — resolve from
`~/.agent-kit/config.yaml` nested key `brain.dir` (same as agent-kit itself).

## Milestones

1. Agent-kit: directory rename and search exclusions
   Approach:
   - `src/agent_kit/init.py` — create `_raw/` and `_inbox/` (replacing single `_inbox`)
   - `src/agent_kit/brain/client.py` — change `EXCLUDED_DIRS` to `{"_raw", ".git"}` (remove `_inbox` from exclusions so attention items are searchable)
   - `src/agent_kit/google/cli.py` — `_resolve_inbox()` resolves to `_raw/` instead of `_inbox/`; update help text
   - `src/agent_kit/brain/templates/BRAIN.md` — update structure table, conflict handling (conflicts go to `_inbox/`)
   - `agent-kit/docs/brain.md` — update ingestion section (agent-kit's own docs)
   - ⚠️ `--to-inbox` flag name stays unchanged
   Tasks:
   - Update `init.py` to create both `_raw/` and `_inbox/`
   - Change `EXCLUDED_DIRS` to `{"_raw", ".git"}` (removing `_inbox` so attention items are searchable)
   - Update `_resolve_inbox()` to resolve to `_raw/`
   - Update BRAIN.md template
   - Update agent-kit `docs/brain.md`
   - Run `uv run pytest tests/brain/`
   Deliverable: `ak init` creates both directories; `--to-inbox` writes to `_raw/`; search excludes `_raw/` but not `_inbox/`
   Verify: `uv run pytest tests/brain/` passes; `rg 'EXCLUDED_DIRS' src/` shows `_raw` replacing `_inbox`

2. Agent-kit: memory indexing and age-weighted search
   Approach:
   - `src/agent_kit/brain/index.py` — refactor `INDEXABLE_DIRS` from list to dict: `{"people": "people", "projects": "projects", "knowledge": "knowledge", "memory": "_archie/memory"}`. Update `reindex()` to iterate `.items()` using the value as the relative path and the key as the type name.
   - `src/agent_kit/brain/client.py` — change `EXCLUDED_DIRS` to `{"_raw", "_archie", ".git"}`. In `search()`, after building search paths from iterdir, explicitly append `_archie/memory/` if it exists. After scoring, apply age modifier to results with type `memory`: extract date from filename regex `^(\d{4}-\d{2}-\d{2})`, compute age, apply modifier (+2/+1/0/-1). Files without a date match get modifier 0.
   - `--type memory` filter: works automatically via `query_index()` once the index has a `memory` key.
   Tasks:
   - Refactor `INDEXABLE_DIRS` to dict mapping type → path
   - Update `reindex()` to use the dict
   - Add `_archie` to `EXCLUDED_DIRS`, append `_archie/memory/` to rg search paths
   - Implement age decay in `search()` for memory-type results
   - Add tests for memory indexing, age-weighted scoring, and `--type memory` filter
   Deliverable: Memory files appear in index as type `memory`; `ak brain search` applies age decay; `--type memory` filters correctly
   Verify: `uv run pytest tests/brain/` passes; manual test with a memory file shows it indexed and searchable with age weighting

3. Archie docs and persona updates
   Approach:
   - `docs/brain.md` (archie repo) — update structure diagram, directory descriptions
   - `CONTRIBUTING.md` — update brain structure reference in repo layout
   - `persona/seeds/tools.md` — update brain section (ak brain reference, directory descriptions)
   - `persona/seeds/soul.md` — add section on memory structure: where memory lives, how to query it (`ak brain search --type memory`), that updates are handled by `action-memory-update` skill
   Tasks:
   - Update `docs/brain.md`
   - Update `CONTRIBUTING.md` brain structure
   - Update `persona/seeds/tools.md` brain references
   - Add memory guidance to `persona/seeds/soul.md`
   Deliverable: All docs consistently describe `_raw/` for ingestion, `_inbox/` for attention, memory structure and querying
   Verify: `rg '_inbox' docs/ persona/ CONTRIBUTING.md` shows only attention-queue references

4. Create `action-memory-update` skill
   Approach:
   - New skill at `persona/skills/action-memory-update/SKILL.md`
   - Covers the batch pipeline: invoke memory-prep script → summarise conversations → write memory files with proper frontmatter (name, summary, tags) → update signals → set watermark
   - Memory file conventions: filename `<date>-<project-or-id>.md`, frontmatter with name/summary/tags, topic headings, prefixes (Discussed, Decided, Action, Correction)
   - Script reference: `persona/scripts/memory-prep.py`
   - ⚠️ This is a specific process invoked manually ("update memory", "catch up") — not inline persistence (which stays in soul)
   Tasks:
   - Write `persona/skills/action-memory-update/SKILL.md`
   - Include memory file format conventions and examples
   - Reference the memory-prep script location
   Deliverable: Skill provides clear workflow for batch memory extraction
   Verify: Skill file exists; covers script invocation, summarisation conventions, frontmatter format, signal handling

5. Create `action-brain-ingest` skill
   Approach:
   - New skill at `persona/skills/action-brain-ingest/SKILL.md`
   - Focused on file-by-file processing from `_raw/`
   - Workflow: list `_raw/` → for each file: read → analyse → decompose into topics/entities → search for duplicates → create/merge brain entries → provenance → remove source → reindex → commit
   - Handles multi-topic files (meeting transcripts, document dumps) — decompose into separate brain entries
   - References brain writing conventions (frontmatter, wikilinks, dedup) rather than repeating them
   - No helper script — LLM does the analysis and routing
   Tasks:
   - Write `persona/skills/action-brain-ingest/SKILL.md`
   - Include decomposition strategies for different file types (transcripts, notes, documents)
   - Include examples of single-topic and multi-topic processing
   Deliverable: Skill provides clear workflow for processing `_raw/` files into brain entities
   Verify: Skill file exists; covers single-topic files, multi-topic decomposition, provenance, cleanup

6. Remove `action-brain-update` and relocate script
   Approach:
   - Source lives at `persona/skills/action-brain-update/` in this repo. Deployed copy at `~/.kiro/skills/` gets removed on next `archie install`.
   - Move `persona/skills/action-brain-update/scripts/memory-prep.py` to `persona/scripts/memory-prep.py`
   - Fix hardcoded `BRAIN_DB` path — resolve brain dir from `~/.agent-kit/config.yaml` using nested key `brain.dir` (i.e. `config["brain"]["dir"]`). Script already reads this file for `project_dir` — extend the same pattern.
   - Delete `persona/skills/action-brain-update/`
   - Rename internal function `_resolve_inbox()` in google CLI to `_resolve_raw_dir()` for clarity (internal only, no user-facing change)
   Tasks:
   - Move memory-prep.py to `persona/scripts/`
   - Remove hardcoded brain path from script (use `config["brain"]["dir"]` with fallback `~/.archie/brain`)
   - Rename `_resolve_inbox()` → `_resolve_raw_dir()` in google CLI
   - Delete `persona/skills/action-brain-update/`
   - Run `archie install` to verify clean deployment
   Deliverable: Old skill removed; script relocated with configurable brain path; internal naming consistent
   Verify: `archie install` succeeds; no `action-brain-update` in `~/.kiro/skills/`; `rg '\.archie/brain' persona/scripts/memory-prep.py` returns no matches
