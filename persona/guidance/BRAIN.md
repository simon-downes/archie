# Brain

Operational guidance for Archie's second brain — how to read, write, and manage
brain content. This is always-loaded knowledge, not a triggered skill.

## Location

Default: `~/.archie/brain/`. Each context is an independent git repo.

## Directory Layout

```
brain/
├── _raw/                    # Ingestion pipeline (outside contexts)
│   ├── inbox/               # Items to process
│   ├── processing/          # Currently being processed
│   └── completed/           # Done
├── _inbox/                  # Items for user to read (research output, reports)
├── _outbox/                 # Items for user to act on (drafts, action items)
├── _memory/                 # Conversation memory (device-local, no git)
├── shared/                  # Personal/general context (git repo)
│   ├── me/                  # Identity, preferences
│   ├── contacts/            # People
│   ├── projects/            # Active work
│   ├── knowledge/           # Concepts, reference material
│   ├── goals/               # Priorities, OKRs
│   ├── journal/             # Logs
│   ├── archive/             # Retired entities
│   ├── index.yaml           # Entity lookup index
│   └── brain.db             # Provenance tracking (gitignored)
└── <work-context>/          # Company/org context (git repo, same structure)
```

`_raw/`, `_inbox/`, `_outbox/`, `_memory/` sit outside contexts — device-local.

---

## Reading

Primary command: `ak brain search` — searches index metadata, file content, and
conversation memory in one call, returning ranked results.

```bash
ak brain search "aurora"                    # search everything
ak brain search "aurora" --context shared   # limit to one context
ak brain search "aurora" --limit 5          # fewer results
```

Results are ranked by match quality:
1. **name** — query appears in entity name
2. **tag** — query matches a tag
3. **summary** — query appears in summary
4. **content** — query found in file content (via rg)
5. **memory** — query found in conversation memory

Within the same weight, results are sorted by most recently modified.

Each result includes `path` (relative to brain root), `match` type, and metadata.
Read a result with `cat ~/.archie/brain/{path}`.

### Direct index/search when needed

For browsing the full index or targeted lookups:

```bash
ak brain index                              # list contexts
ak brain index <context>                    # full index
ak brain index <context> --type knowledge   # filter by type
ak brain index <context> --slug <slug>      # lookup by slug
```

For broad text search across content:

```bash
rg "<term>" ~/.archie/brain/<context>/ -t md -t yaml --glob '!.git' -l
rg -i "<term>" ~/.archie/brain/ --glob '!.git' --glob '!_raw' -l
```

---

## Writing

### Determine target context

1. Extract key entities from the content (people, companies, projects, topics)
2. Check indexes: `ak brain index <context>` across contexts
3. Highest entity match count determines the context
4. Default to `shared` when no context scores

**Low-confidence routing:** route to best guess, create an inbox note flagging it.

### Check for duplicates

Before creating any entity, check the index:

```bash
ak brain index <context> --slug <candidate-slug>
ak brain index <context> --type <entity-type>
```

**Match exists:** update the existing file — merge new information, don't overwrite.
**No match:** create a new entity.

### Conflict detection

If new data contradicts existing brain content, don't silently overwrite. Create
an inbox note:

```markdown
---
type: conflict
source: <source>
entity: <path-to-entity>
---

New data says <X>, existing brain says <Y>. Review and resolve.
```

### Entity types and formats

**Knowledge** — `<context>/knowledge/<slug>.md`
```markdown
---
tags: [aws, aurora, databases]
summary: One-line description
---

# Title

Content...
```

Place flat in `knowledge/` unless a relevant subdirectory exists. Introduce a
subdirectory only when 5+ related files cluster at the top level. When creating
one, move related files and reindex.

**Contacts** — `<context>/contacts/<slug>.yaml`
```yaml
name: Jane Smith
summary: Engineering Manager at Tillo
email: jane@example.com
context: Met at platform team standup
```

**Projects** — `<context>/projects/<slug>/README.md`
```markdown
---
name: Project Name
summary: One-line description
issues:
  provider: jira
  project: PLAT
slack: true
---

# Project Name

Context and notes...
```

**Goals** — `<context>/goals/<slug>.yaml`
```yaml
name: Ship Archie v1
summary: Complete brain read/write and ingestion pipeline
status: in-progress
target: 2026-Q2
```

**Journal** — `<context>/journal/<date>.md` (no index entry needed)

**Inbox notes** — `<context>/inbox/<slug>.md` with frontmatter

### Index and commit

After writing:

```bash
ak brain reindex <context>
ak brain commit <context> -m "brain: <description>" \
  --paths <file1> --paths <file2> --paths index.yaml
```

Always include `index.yaml` if you ran reindex. Only commit files you wrote —
prevents sweeping up another agent's uncommitted work.

If writes span multiple contexts, commit each independently.

### Commit conventions

- Ingestion: `brain: ingest <source-filename>`
- Manual writes: `brain: <brief description>`

---

## CLI Reference

### `ak brain search <query> [--context <name>] [--limit N]`
Search across index metadata, file content, and memory. Returns ranked results.

### `ak brain index [context]`
Query the brain index. Without context, lists available contexts.

### `ak brain reindex <context>`
Rebuild `index.yaml` from filesystem. Acquires a file lock for concurrent safety.

### `ak brain commit <context> -m <message> [--paths <file> ...]`
Stage and commit. Use `--paths` for concurrent safety.

### `ak brain status [context]`
Raw pipeline state and git changes per context.

### `ak brain validate [context]`
Check structure and index integrity.

### `ak brain project [name]`
Get project config. Infers from cwd if no name given.

---

## Index Format

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

Keyed by entity type, then slug. Slugs are stable identifiers — paths can change.

---

## Provenance

Tracked in `brain.db` (SQLite, gitignored) per context:

```sql
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    entities_created TEXT,  -- JSON array of paths
    entities_updated TEXT   -- JSON array of paths
);
```

---

## Key Rules

- Each context is a separate git repo — commit independently
- `brain.db` is gitignored — operational metadata, not knowledge
- `_raw/`, `_inbox/`, `_outbox/`, `_memory/` sit outside context repos
- Slugs are stable identifiers; paths can change
- Run `ak brain reindex` after moving files
