# 003 — Brain Read/Write

## Objective

Enable Archie to read from and write to the brain — querying existing knowledge, creating
and updating entities, managing the index, and ingesting raw content through the pipeline.
Currently the brain structure exists but has no content, no index, and no operational
read/write tooling beyond `ak brain init`.

## Requirements

### Reading

- MUST be able to query the brain index to find existing entities by type, slug, or keyword
  - AC: Given a populated index, querying by type returns matching entries
  - AC: Given a populated index, querying by slug returns the specific entry

- MUST be able to search brain content via full-text search (rg/grep)
  - AC: Searching for a term returns matching files across the target context(s)

- MUST read the index first, then fall back to full-text search when the index doesn't
  have a match
  - AC: A brain-read skill codifies this two-step lookup pattern

### Writing

- MUST check the index for existing entities before creating new ones to prevent duplication
  - AC: Attempting to write knowledge that matches an existing slug updates the existing
    file rather than creating a new one

- MUST update `index.yaml` whenever entities are created, updated, or moved
  - AC: After any write operation, `ak brain validate` reports no "not indexed" warnings
    for the affected context

- MUST commit all changes to a context in a single git commit after writes are complete
  - AC: A write operation that updates 3 files in the same context produces exactly 1 commit

- MUST write to the correct context based on content analysis, not source tagging
  - AC: A raw item mentioning company-specific people/projects is routed to the
    corresponding work context
  - AC: General knowledge or personal content is routed to `shared`

- MUST create an inbox note when context routing confidence is low
  - AC: Ambiguous items produce a note in the target context's `inbox/` explaining the
    routing decision

- SHOULD support writing to multiple contexts from a single raw item
  - AC: Meeting notes that contain both company-specific and general knowledge produce
    writes to both contexts

### Knowledge Structure

- MUST use markdown files with YAML frontmatter for all knowledge entities
  - AC: Knowledge files have `tags`, `summary` fields in frontmatter

- MUST use flat structure in `knowledge/` initially, introducing subdirectories only when
  a clear cluster of 5+ files emerges
  - AC: New knowledge files are created at `knowledge/<slug>.md` unless a relevant
    subdirectory already exists

- MUST use slugs as stable identifiers in the index, decoupled from file paths
  - AC: Moving a file to a subdirectory requires only an index path update, not a slug change

### Ingestion Pipeline

- MUST process items from `_raw/inbox/` through the `_raw/processing/` → `_raw/completed/` pipeline
  - AC: After ingestion, the raw item is in `_raw/completed/`, not `_raw/inbox/`

- MUST record provenance in `brain.db` (SQLite) per context
  - AC: After ingestion, `brain.db` contains a record linking the source file to the
    entities it produced or updated

- MUST auto-commit to git after each ingestion run (one commit per affected context)
  - AC: `git log` in the context shows a commit referencing the ingested source

### Agent-kit CLI

- MUST make existing `ak brain` commands operational (currently in source but not in
  installed CLI due to stale install)
  - AC: `ak brain index`, `ak brain status`, `ak brain validate`, `ak brain project`
    work from the command line

- MUST add `ak brain reindex <context>` to rebuild `index.yaml` from filesystem
  - AC: Running `reindex` on a context with unindexed entities produces a valid `index.yaml`

- MUST add `ak brain commit <context> -m <message>` to stage and commit all changes
  - AC: Running `commit` on a context with unstaged changes produces a single git commit

## Technical Design

### Overview

Three layers of capability:

1. **Agent-kit CLI** — mechanical operations: index rebuild, commit, validation. Already
   partially built, needs completion and installation.
2. **Archie skills** — LLM-driven operations: reading with context, writing with dedup
   and routing, ingestion pipeline. New skills in the archie persona.
3. **Shell tools** — `rg`, `cat`, `tree`, etc. used directly by the LLM during brain
   operations. No wrapping needed.

### Code Structure

**Agent-kit changes** (`agent-kit/` subdirectory):
- `src/agent_kit/brain/client.py` — add `reindex_context()`, `commit_context()` functions
- `src/agent_kit/brain/cli.py` — add `reindex` and `commit` commands
- Fix installation so `ak brain` is available (likely stale `uv tool install`)

**Archie skill changes** (`persona/skills/`):
- `tool-brain/SKILL.md` — operational guidance for brain CLI and shell tools
- `action-brain-read/SKILL.md` — codified read pattern (index → grep → read)
- `action-brain-write/SKILL.md` — codified write pattern (dedup → write → index → commit)
- `action-brain-ingest/SKILL.md` — full ingestion pipeline skill

### Index Format

`index.yaml` per context, keyed by entity type then slug:

```yaml
contacts:
  jane-smith:
    name: Jane Smith
    summary: Engineering Manager at Tillo
    path: contacts/jane-smith.yaml
projects:
  tillo-platform:
    name: Tillo Platform
    summary: Tillo's Internal Developer Platform
    path: projects/tillo-platform/
knowledge:
  aurora-failover:
    name: Aurora PostgreSQL Failover
    summary: Failover behaviour and gotchas for Aurora PostgreSQL
    path: knowledge/aws/aurora-failover.md
```

The `reindex` command scans entity directories, extracts name/summary from frontmatter
(or filename as fallback), and writes the index. Existing index entries for paths that
still exist are preserved (to keep manually curated summaries).

### Knowledge File Format

```markdown
---
tags: [aws, aurora, databases]
summary: Failover behaviour and gotchas for Aurora PostgreSQL
---

# Aurora PostgreSQL Failover

Content here...
```

Slug is derived from filename (without extension). Tags are free-form strings used for
search and clustering. Summary is a one-line description used in the index.

### Provenance Schema (brain.db)

```sql
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    entities_created TEXT,  -- JSON array of paths
    entities_updated TEXT   -- JSON array of paths
);
```

One `brain.db` per context (gitignored). Created on first ingestion.

### Context Routing Logic

The ingestion skill (LLM-driven) determines context by:

1. Extract entities mentioned in the content (people, companies, projects, topics)
2. For each context, check its index for matching entities
3. Score contexts by number of matches
4. Highest-scoring context wins; `shared` is the default when no context scores
5. If the top two contexts score similarly, route to best guess and create an inbox note

Content that produces knowledge relevant to multiple contexts is split: company-specific
facts go to the work context, general insights go to `shared`.

### Commit Convention

Ingestion commits: `brain: ingest <source-filename>`
Manual write commits: `brain: <brief description>`

### Key Decisions

- **No `ak brain write` command** — writing is LLM work (content decisions, dedup logic,
  routing). Agent-kit provides only mechanical helpers (reindex, commit).
- **Reindex preserves existing entries** — if a slug already has a curated summary in the
  index, reindex keeps it rather than overwriting from frontmatter. This allows manual
  curation of index entries.
- **Flat knowledge by default** — subdirectories are an evolution, not a starting point.
  The skill guides when to introduce them.
- **Context routing is content-based** — no source tagging required. The LLM analyses
  content and matches against existing brain entities.
- **Single commit per context per operation** — not per entity. Reduces noise in git history.

## Milestones

1. Fix `ak brain` CLI registration and add mechanical commands
   Approach:
   - `ak brain` is already coded in agent-kit source but not available in the installed
     CLI — likely a stale install. Reinstall with `uv tool install -e ./agent-kit`.
   - New commands (`reindex`, `commit`) follow the existing agent-kit pattern: client
     function in `client.py`, Click command in `cli.py` with `@handle_errors`.
   - `reindex_context()` scans the indexable entity directories: `contacts`, `projects`,
     `knowledge`, `goals`. Other entity dirs (`me`, `inbox`, `outbox`, `journal`,
     `archive`) are not indexed — they're operational, not lookup targets. Use a
     constant `INDEXABLE_DIRS` separate from the existing `ENTITY_DIRS`.
   - Frontmatter extraction: use file extension to determine format — `.yaml`/`.yml`
     files are loaded directly with `yaml.safe_load()`, `.md` files use the existing
     `_parse_frontmatter()`. Extract `name` and `summary` fields; fall back to
     titlecased filename for `name` if missing.
   - Merge logic: load existing `index.yaml`, overlay new entries, preserve existing
     entries whose paths still exist on disk (keeps curated summaries).
   - `commit_context()` runs `git add -A && git commit -m <message>` in the context dir.
     If nothing to commit, print a message and return cleanly.
   - ⚠️ Frontmatter extraction must handle both standalone YAML files (contacts, goals)
     and markdown files with YAML frontmatter (knowledge, projects). The existing
     `_parse_frontmatter()` handles markdown; add YAML file handling.
   Tasks:
   - Reinstall agent-kit with `uv tool install -e ./agent-kit` and verify `ak brain` works
   - Add `reindex_context()` to `client.py` — scan entity dirs, extract metadata, merge
     with existing index, write `index.yaml`
   - Add `commit_context()` to `client.py` — git add -A + commit with message
   - Add `reindex` and `commit` Click commands to `cli.py`
   - Run `ruff check` and `ruff format` on agent-kit
   Deliverable: `ak brain reindex shared` produces a valid `index.yaml` and
   `ak brain commit shared -m "test"` creates a git commit
   Verify: `ak brain reindex shared && cat ~/.archie/brain/shared/index.yaml` shows
   indexed entities; `ak brain commit shared -m "test" && git -C ~/.archie/brain/shared log --oneline -1`
   shows the commit

2. Create `tool-brain` skill
   Approach:
   - Tool-layer skill providing operational guidance for brain CLI commands and shell
     tools used during brain operations. Follows the pattern of `tool-git`.
   - Covers: `ak brain` commands (index, reindex, status, validate, commit, project),
     shell tools for brain queries (`rg`, `cat`, `tree`), brain directory layout,
     file format conventions (frontmatter, index structure).
   - This skill is referenced by the action skills — it's the "how to use the tools"
     layer that the "what to do" skills build on.
   Tasks:
   - Create `persona/skills/tool-brain/SKILL.md` with command reference, file format
     conventions, and shell tool patterns for brain operations
   Deliverable: `tool-brain` skill exists with complete operational guidance
   Verify: Read `persona/skills/tool-brain/SKILL.md` and confirm it covers all `ak brain`
   commands, file formats, and shell tool patterns

3. Create `action-brain-read` skill
   Approach:
   - Action-layer skill codifying the two-step read pattern: index lookup → grep fallback
     → read files. Produces a summary of what was found.
   - The skill guides the LLM through: determine which context(s) to search, check the
     index first, fall back to `rg` if no index match, read matched files, synthesise.
   - References `tool-brain` for command specifics.
   Tasks:
   - Create `persona/skills/action-brain-read/SKILL.md` with the read workflow
   Deliverable: `action-brain-read` skill exists with the complete read pattern
   Verify: Read `persona/skills/action-brain-read/SKILL.md` and confirm it covers index
   lookup, grep fallback, multi-context search, and result synthesis

4. Create `action-brain-write` skill
   Approach:
   - Action-layer skill codifying the write pattern: check index for duplicates → create
     or update entity file → update index → commit.
   - Covers: dedup logic (check index by slug and by name similarity), file creation
     with correct frontmatter, index update, single commit per context.
   - Context routing: when the target context isn't explicit, the skill guides the LLM
     to determine context from content (match entities against all context indexes).
   - Inbox notes for low-confidence routing: create a markdown file in `<context>/inbox/`
     explaining the routing decision.
   - Knowledge structure guidance: flat by default, subdirectory when 5+ related files exist.
   - References `tool-brain` for command specifics.
   Tasks:
   - Create `persona/skills/action-brain-write/SKILL.md` with the write workflow
   Deliverable: `action-brain-write` skill exists with the complete write pattern
   including dedup, routing, and index management
   Verify: Read `persona/skills/action-brain-write/SKILL.md` and confirm it covers
   dedup checking, entity creation/update, index update, context routing, inbox notes,
   and knowledge structure guidance

5. Create `action-brain-ingest` skill
   Approach:
   - Action-layer skill for the full ingestion pipeline: pick from `_raw/inbox/`, move
     to `_raw/processing/`, extract information, route to context(s), write entities
     (using `action-brain-write` patterns), record provenance, commit, move to
     `_raw/completed/`.
   - Provenance tracking uses SQLite (`brain.db` per context, gitignored). The skill
     instructs the LLM to use `sqlite3` CLI commands directly — no agent-kit wrapper
     needed. The skill includes the exact SQL for table creation (idempotent
     `CREATE TABLE IF NOT EXISTS`) and insert statements.
   - The skill handles multiple raw items in sequence (process all of `_raw/inbox/`).
   - Each raw item is fully processed before moving to the next.
   - References `action-brain-write` for the write pattern and `tool-brain` for commands.
   Tasks:
   - Create `persona/skills/action-brain-ingest/SKILL.md` with the ingestion workflow
   Deliverable: `action-brain-ingest` skill exists with the complete ingestion pipeline
   Verify: Read `persona/skills/action-brain-ingest/SKILL.md` and confirm it covers
   the full pipeline from raw pickup to provenance recording

6. Update documentation
   Approach:
   - Update `docs/brain.md` to reflect the implemented capabilities and any design
     decisions that evolved during implementation.
   - Update agent-kit `docs/brain.md` with the new CLI commands.
   - Update the Available Tools context (in `persona/guidance/`) to include `ak brain`
     commands if a guidance file for agent-kit exists.
   Tasks:
   - Update `docs/brain.md` with operational details for read/write/ingest
   - Update `agent-kit/docs/brain.md` with `reindex` and `commit` command docs
   - Check for and update any guidance files that reference brain or agent-kit commands
   Deliverable: All documentation reflects the new brain read/write capabilities
   Verify: `grep -r "reindex\|brain-read\|brain-write\|brain-ingest" docs/ persona/` shows
   references in the appropriate documentation files
