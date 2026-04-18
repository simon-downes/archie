---
name: tool-brain
description: >
  Operational guidance for Archie's second brain — CLI commands, shell tools, file formats,
  and directory conventions. Use when reading from or writing to the brain, querying the
  brain index, managing brain contexts, or when brain operations are mentioned.
---

# Brain Operations

## Scope

CLI commands (`ak brain`), shell tools (`rg`, `cat`, `tree`, `sqlite3`), file format
conventions, and directory layout for Archie's second brain.

## Brain Location

Default: `~/.archie/brain`. Resolve with config if needed.

## Directory Layout

```
brain/
├── _raw/                    # Ingestion pipeline (outside contexts)
│   ├── inbox/               # Items to process
│   ├── processing/          # Currently being processed
│   └── completed/           # Done
├── _memory/                 # Conversation memory (device-local, no git)
│   ├── 2026-04-18-archie.md
│   ├── 2026-04-14-tillo-platform.md
│   └── 2026-04-18-c951.md  # General session
├── shared/                  # Personal/general context (git repo)
│   ├── me/                  # Identity, preferences
│   ├── contacts/            # People
│   ├── projects/            # Active work
│   ├── knowledge/           # Concepts, reference material
│   ├── goals/               # Priorities, OKRs
│   ├── inbox/               # Actionable items awaiting review
│   ├── outbox/              # Draft messages
│   ├── journal/             # Logs
│   ├── archive/             # Retired entities
│   ├── index.yaml           # Entity lookup index
│   └── brain.db             # Provenance tracking (gitignored)
└── <work-context>/          # Company/org context (git repo, same structure)
```

Each context is an independent git repo. `_raw/` sits outside contexts.

## CLI Commands

### `ak brain index [context]`

Query the brain index. Without context, lists available contexts.

```bash
ak brain index                          # list contexts
ak brain index shared                   # full index
ak brain index shared --type projects   # filter by type
ak brain index shared --slug my-app     # lookup by slug
```

### `ak brain reindex <context>`

Rebuild `index.yaml` from filesystem. Scans `contacts/`, `projects/`, `knowledge/`,
`goals/`. Preserves existing curated entries whose paths still exist.

```bash
ak brain reindex shared
ak brain reindex tillo
```

### `ak brain commit <context> -m <message> [--paths <file> ...]`

Stage and commit changes in a context. Use `--paths` to stage specific files only
(repeatable). Without `--paths`, stages all changes (`git add -A`).

Prefer `--paths` when multiple agents may write to the same context concurrently —
prevents one agent's commit from sweeping up another agent's uncommitted files.

```bash
# Commit specific files (preferred for concurrent safety)
ak brain commit shared -m "brain: add aurora knowledge" \
  --paths knowledge/aurora-failover.md --paths index.yaml

# Commit all changes (single-agent use)
ak brain commit shared -m "brain: bulk update"
```

`reindex` acquires a per-context file lock internally, so concurrent reindex calls
from different agents will queue rather than corrupt `index.yaml`.

### `ak brain status [context]`

Show brain status — raw pipeline state and git changes per context.

### `ak brain validate [context]`

Check structure and index integrity.

### `ak brain project [name]`

Get project config. Infers from cwd if no name given.

## Shell Tools for Brain Queries

### Full-text search

```bash
# Search across a specific context
rg "terraform" ~/.archie/brain/shared/knowledge/

# Search across all contexts
rg "jane smith" ~/.archie/brain/ --glob '!.git'

# Search with file type filter
rg "failover" ~/.archie/brain/shared/ -t md
```

### Browse structure

```bash
# Context overview
tree ~/.archie/brain/shared -L 2 --dirsfirst -I .git

# List knowledge files
ls ~/.archie/brain/shared/knowledge/

# Read a specific entity
cat ~/.archie/brain/shared/knowledge/aurora-failover.md
```

### Provenance queries

```bash
# Check what was ingested
sqlite3 ~/.archie/brain/shared/brain.db "SELECT * FROM provenance ORDER BY ingested_at DESC LIMIT 10"

# Find which entities came from a source
sqlite3 ~/.archie/brain/shared/brain.db "SELECT entities_created, entities_updated FROM provenance WHERE source_file LIKE '%meeting%'"
```

## File Formats

### Knowledge files (markdown with frontmatter)

```markdown
---
tags: [aws, aurora, databases]
summary: Failover behaviour and gotchas for Aurora PostgreSQL
---

# Aurora PostgreSQL Failover

Content here...
```

- `tags` — free-form strings for search and clustering
- `summary` — one-line description, used in the index

### Contact files (YAML)

```yaml
name: Jane Smith
summary: Engineering Manager at Tillo
email: jane@example.com
context: Met at platform team standup
```

### Project files (markdown with frontmatter)

```markdown
---
name: Tillo Platform
summary: Tillo's Internal Developer Platform
issues:
  provider: linear
  team: PLAT
slack: true
---

# Tillo Platform

Context and notes about the project...
```

### Goal files (YAML)

```yaml
name: Ship Archie v1
summary: Complete brain read/write and ingestion pipeline
status: in-progress
target: 2026-Q2
```

### Index format (`index.yaml`)

```yaml
contacts:
  jane-smith:
    name: Jane Smith
    summary: Engineering Manager at Tillo
    path: contacts/jane-smith.yaml
knowledge:
  aurora-failover:
    name: Aurora PostgreSQL Failover
    summary: Failover behaviour and gotchas
    path: knowledge/aws/aurora-failover.md
```

Keyed by entity type, then slug. Slug is the stable identifier — paths can change
(e.g. when knowledge files move into subdirectories).

### Inbox notes (markdown)

```markdown
---
type: routing-flag
source: meeting-notes-2026-04-18.md
context: tillo
confidence: low
---

Routed to tillo (mentions Tillo Platform project). Also references personal goals —
consider whether goal updates should go to shared.
```

## Provenance Schema

```sql
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    entities_created TEXT,  -- JSON array of paths
    entities_updated TEXT   -- JSON array of paths
);
```

## Memory Watermark Schema

Tracks the last conversation memory extraction. Stored in `shared/brain.db`.

```sql
CREATE TABLE IF NOT EXISTS memory_watermark (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_processed_at INTEGER NOT NULL  -- conversations_v2.updated_at value
);
```

## Conversation Data Source

Kiro-cli stores conversation history in:

```
~/.local/share/kiro-cli/data.sqlite3
```

Table `conversations_v2`: `key` (working directory), `conversation_id` (UUID),
`value` (JSON with `transcript` array), `updated_at` (Unix ms timestamp).

One `brain.db` per context, gitignored. Created on first use via `sqlite3`.

## Commit Conventions

- Ingestion: `brain: ingest <source-filename>`
- Manual writes: `brain: <brief description>`

## Key Rules

- Each context is a separate git repo — commit independently
- `brain.db` is gitignored — operational metadata, not knowledge
- `_raw/` sits outside context repos
- Slugs are stable identifiers; paths can change
- Run `ak brain reindex` after moving files to update paths in the index
