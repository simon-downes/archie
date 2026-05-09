# Brain Restructure

## Objective

Restructure the brain from a multi-context "Archie's operational store" into a single
unified knowledge base that serves both Simon (human retrieval) and Archie (programmatic
retrieval). Remove the context system, establish clear conventions via a `BRAIN.md` guide,
and improve search capabilities.

## Requirements

### Single Repository, No Contexts

- MUST collapse multiple contexts into a single flat structure
  - AC: No `contexts` configuration in agent-kit config
  - AC: All brain content lives under `~/.archie/brain/` directly
  - AC: `ak brain` commands work without `--context` flags

### Directory Structure

- MUST implement the following top-level layout:
  - AC: `_archie/` — Archie's operational state (signals, memory, logs, soul.md)
  - AC: `_inbox/` — ingestion staging (files = ready, subdirs = bulk processing)
  - AC: `simon/` — personal space (profile, goals, journal, inbox)
  - AC: `people/` — relationships and contacts
  - AC: `projects/` — lightweight project context (not code docs)
  - AC: `knowledge/` — durable reference knowledge grouped by domain

### BRAIN.md Convention Guide

- MUST include a `BRAIN.md` at the brain root describing structure and conventions
  - AC: Documents top-level directory purposes
  - AC: Documents where different content types belong
  - AC: Documents project directory conventions (journal/, decisions/, context.md)
  - AC: Documents file conventions (wikilinks, frontmatter)
  - AC: Referenced by brain-related skills and tool guidance

### Brain Initialisation

- MUST implement `ak init` as the top-level setup command (brain only for now)
  - AC: Prompts for user's first name (creates `<name>/` directory)
  - AC: Prompts for agent name (default: archie, creates `_<agent>/` directory)
  - AC: Persists `user` and `agent` names in `~/.agent-kit/config.yaml`
  - AC: Creates top-level directories: `<user>/`, `_<agent>/`, `_inbox/`, `people/`,
    `projects/`, `knowledge/`
  - AC: Copies default `BRAIN.md` template from agent-kit, substituting user/agent names
  - AC: Creates `<user>/profile.md` with placeholder structure
  - AC: Creates `_<agent>/memory.md` (empty)
  - AC: Creates `_<agent>/signals.yaml` (empty)
  - AC: Initialises a git repo in the brain directory
  - AC: Non-interactive mode: `ak init --user simon --agent archie`
- MUST remove `ak brain init` (replaced by `ak init`)
- MUST remove the old context-based init logic entirely

### Responsibility Split: Agent-Kit vs Archie

- Agent-kit provides the **structure and mechanics**:
  - `ak brain init` — creates the empty shell with directories and BRAIN.md
  - `ak brain search` — mechanical search/retrieval
  - `ak brain ref` — reference tracking
  - `ak brain reindex` — index maintenance
  - Default BRAIN.md template lives in agent-kit
- Archie provides the **intelligence and lifecycle**:
  - Skills that decide what to write and where (action-brain-update)
  - Memory consolidation (raw memories → `_archie/memory.md`)
  - Signal extraction and management
  - Soul evolution (`_archie/soul.md`)
  - Session digest hook (reads signals at spawn)
  - Guidance on how/when to use the brain

### Wikilinks

- MUST adopt `[[wikilinks]]` for associative links between entries
  - AC: Links use relative paths from brain root: `[[people/jane]]`, `[[projects/tillo]]`
  - AC: Obsidian-compatible format (no extension needed)
  - AC: No tooling enforcement — convention only

### Consolidated Memory

- MUST maintain `_archie/memory.md` as a promoted/curated memory file
  - AC: Contains the most valuable observations from session memories
  - AC: Small enough to be always-loadable (target: <100 lines)
  - AC: File created (empty) during `ak brain init`
  - AC: Consolidation logic (how memories are promoted into this file) is out of scope —
    addressed separately when refining the brain-update skill

### Reference Tracking

- SHOULD add `ak brain ref` command for logging and querying access
  - AC: `ak brain ref <path>` records a timestamped access in the brain SQLite database
  - AC: `ak brain refs --top N` shows most-referenced entries
  - AC: `ak brain refs --stale --since 90d` shows entries unreferenced in N days
  - AC: Non-critical — model can forget to record without consequence
  - AC: Provides signal for identifying high-value vs dead-weight entries

### Improved Search

- MUST improve `ak brain search` with multi-term support and ranked results
  - AC: Accepts multiple search terms: `ak brain search "terraform" "module" "vpc"`
  - AC: Terms act as OR with scoring (more matches = higher rank)
  - AC: Scoring weights: title/filename match > frontmatter/tags > body content
  - AC: Output includes: path, score, match count, title (from frontmatter or filename),
    excerpt with context
  - AC: `--limit` controls max results (default 10)
  - AC: Excludes `_inbox/` subdirectories and `_archie/logs/` from results

### Inbox Simplification

- MUST simplify the ingestion pipeline
  - AC: Files directly in `_inbox/` are ready for ingestion
  - AC: Subdirectories in `_inbox/` are staging areas for bulk/multi-step processing
  - AC: No `_raw/_processing/_completed` pipeline
  - AC: Ingested files are removed after processing

### Remove Context System

- MUST remove context-related code from agent-kit
  - AC: Remove `contexts` from agent-kit config schema
  - AC: Remove `--context` options from CLI commands
  - AC: Remove `init_context`, `list_contexts`, `configured_contexts` from client
  - AC: `ak brain index` works against the single brain root
  - AC: `ak brain search` searches the entire brain (no context scoping)
  - AC: `ak brain status` reports on the single brain
  - AC: `ak brain reindex` rebuilds index for the entire brain

## Technical Design

### New Structure

```
~/.archie/brain/
├── BRAIN.md              # Convention guide (created by ak brain init)
├── _<agent>/             # Agent's operational state (default: _archie/)
│   ├── soul.md           # Live personality (evolves over time)
│   ├── memory.md         # Consolidated observations (always-loadable)
│   ├── signals.yaml      # Learning signals
│   ├── memory/           # Raw session memories
│   └── logs/             # Observability data (future)
├── _inbox/               # Ingestion staging
│   ├── some-file.md      # Ready for ingestion
│   └── bulk-data/        # Staging subdirectory
├── <user>/               # User's personal space (default: simon/)
│   ├── profile.md        # Structured profile (always loaded as guidance)
│   ├── goals.md          # Current priorities
│   ├── inbox/            # Things needing user's attention
│   └── journal/          # Personal dated entries
├── people/               # Relationships and contacts
│   ├── jane.md
│   └── ...
├── projects/             # Lightweight project context
│   ├── tillo/
│   │   ├── context.md    # Current focus, status
│   │   ├── journal/      # Weekly updates, meeting notes
│   │   └── decisions/    # Key decisions
│   ├── archie.md
│   └── ...
└── knowledge/            # Durable reference knowledge
    ├── aws/
    ├── terraform/
    └── ...
```

### Search Improvements

Replace single-query ripgrep with multi-term scoring:

```python
def search(terms: list[str], limit: int = 10) -> list[dict]:
    """Search brain with multiple terms, return ranked results."""
    results = {}

    for term in terms:
        # Index matches (title, tags, summary)
        for entry in index_matches(term):
            key = entry["path"]
            if key not in results:
                results[key] = {"path": key, "score": 0, "matches": 0, **entry}
            # Filename/title: +3, tags: +2, summary: +1
            results[key]["score"] += entry["weight"]
            results[key]["matches"] += 1

        # Ripgrep content matches: +1
        for hit in rg_search(term):
            key = hit["path"]
            if key not in results:
                results[key] = {"path": key, "score": 0, "matches": 0, **hit}
            results[key]["score"] += 1
            results[key]["matches"] += 1

    ranked = sorted(results.values(), key=lambda r: (-r["matches"], -r["score"]))
    return ranked[:limit]
```

Scoring weights:
- Filename/title contains term: +3
- Frontmatter tags contain term: +2
- Body content contains term: +1
- Multiple terms matching same file: multiplicative boost via match count sort

### Reference Tracking

Stored in the brain SQLite database (`brain.db`) alongside the index:

```sql
CREATE TABLE refs (
    path TEXT NOT NULL,
    ts INTEGER NOT NULL
);
CREATE INDEX idx_refs_path ON refs(path);
```

CLI interface:
- `ak brain ref <path>` — record access
- `ak brain refs --top N` — most referenced entries
- `ak brain refs --stale --since 90d` — unreferenced entries (candidates for review/archival)

### BRAIN.md

Default template lives in agent-kit (`src/agent_kit/brain/templates/BRAIN.md`). Copied
to brain root during `ak brain init` with `{{USER}}` and `{{AGENT}}` placeholders
substituted.

Referenced by:
- `action-brain-update` skill (where to put things)
- Tool guidance (how to search/navigate)
- `docs/brain.md` in archie repo

### Brain Initialisation (`ak init`)

Top-level setup command. Currently only handles brain; future phases will add config
and projects setup.

Interactive setup:
```
$ ak init
User name [simon]: simon
Agent name [archie]: archie
Initialising brain at ~/.archie/brain/...
  Created BRAIN.md
  Created simon/
  Created simon/profile.md
  Created _archie/
  Created _archie/memory.md
  Created _archie/signals.yaml
  Created _inbox/
  Created people/
  Created projects/
  Created knowledge/
  Initialised git repo
Done.
```

Template files in agent-kit:
- `templates/BRAIN.md` — convention guide with `{{USER}}` / `{{AGENT}}` placeholders
- `templates/profile.md` — user profile skeleton

Templates are packaged via `importlib.resources` (same pattern archie uses for
`sandbox/Dockerfile`). Add a `force-include` entry in agent-kit's `pyproject.toml`.

Non-interactive mode for scripting: `ak init --user simon --agent archie`

Implementation: new `init` command registered on the top-level CLI group (not under
`brain`). The old `brain init` command and all context-based init logic are removed.

### Agent-Kit Changes

- Remove `contexts` from `DEFAULT_CONFIG`
- Remove `list_contexts()`, `init_context()`, `configured_contexts()` from client
- Simplify `init_brain()` to just ensure the directory exists with BRAIN.md
- Update `search()` to search entire brain root
- Update `reindex()` to index entire brain root
- Remove `--context` from all CLI commands
- Add `ref` command
- Rewrite `search` with multi-term scoring

## Milestones

1. **Implement `ak init` with brain setup**
   Approach:
   - Create `src/agent_kit/brain/templates/BRAIN.md` and `templates/profile.md`
   - Add `force-include` entry in `pyproject.toml` for templates
   - Add top-level `init` command to `cli.py` (prompts for user/agent, creates structure)
   - Support `--user` and `--agent` flags for non-interactive use
   - Initialise git repo in brain directory
   - Remove `ak brain init` command and old `init_brain()`/`init_context()` logic
   Deliverable: `ak init` creates the full brain structure with templated BRAIN.md.
   Verify: Run init, verify directories and files created with correct substitutions.

2. **Remove context system from agent-kit**
   Approach:
   - Remove context-related config, client methods, CLI options
   - Simplify `init_brain()`, `search()`, `reindex()`, `status()`
   - Update `brain` CLI commands (remove `--context`, update `index`, etc.)
   - Update tests
   Deliverable: Agent-kit works against single brain root.
   Verify: All brain tests pass, `ak brain search/index/status` work.

3. **Improve search**
   Approach:
   - Rewrite `search()` in client to accept multiple terms
   - Implement scoring (filename > tags > body, match count boost)
   - Update CLI to accept multiple arguments
   - Structured output with path, score, matches, title, excerpt
   Deliverable: `ak brain search "term1" "term2"` returns ranked results.
   Verify: Test with known content, verify ranking makes sense.

4. **Add reference tracking**
   Approach:
   - Add `refs` table to brain SQLite database
   - Add `ak brain ref <path>` command (record access)
   - Add `ak brain refs` command (query: `--top N`, `--stale --since Nd`)
   - Update brain-related skills/guidance to mention `ak brain ref`
   Deliverable: Reference tracking available via SQLite.
   Verify: Record refs, query top/stale, verify correct results.

5. **Update skills and guidance**
   Approach:
   - Update `action-brain-update` skill to reference BRAIN.md conventions
   - Update tool guidance (Available Tools section) for new `ak brain` interface
   - Update `docs/brain.md` in archie repo
   - Remove references to contexts throughout
   Deliverable: All documentation and skills reflect new structure.
   Verify: Grep for "context" references in skills/guidance.
