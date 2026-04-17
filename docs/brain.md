# Brain

The brain is Archie's persistent knowledge store. It lives at `~/.archie/brain/` and is
composed of context directories, each a separate git repository.

## Structure

```
~/.archie/brain/
├── _raw/            # processing pipeline (inbox → processing → completed)
├── shared/          # cross-cutting: identity, shared contacts, general knowledge
├── work-acme/       # company-specific: projects, team, knowledge, goals
├── personal/        # personal: projects, interests, goals
└── ...              # arbitrary additional contexts
```

Each context is an independent git repo stored in your personal GitHub org. This enables:
- Different availability per device (clone only what you need)
- Independent version history
- Clear confidentiality boundaries

Setup and management is via agent-kit: `ak brain init` creates the brain structure and
initialises contexts. See [agent-kit brain docs](../agent-kit/docs/brain.md) for CLI reference.

## Entity Types

Each context directory contains whichever of these subdirectories are relevant:

| Directory     | Purpose                                          | Format                          |
|---------------|--------------------------------------------------|---------------------------------|
| `me/`         | Identity, personality, preferences (shared only) | Markdown + YAML                 |
| `contacts/`   | People and relationships                         | `profile.yaml` + `notes.md`    |
| `projects/`   | Active work                                      | `status.yaml` + `context.md`   |
| `knowledge/`  | Concepts, topics, reference material             | Markdown with YAML frontmatter  |
| `goals/`      | OKRs, priorities, roadmap items                  | YAML                            |
| `inbox/`      | Actionable items awaiting review                 | Markdown                        |
| `outbox/`     | Draft messages awaiting manual send              | Markdown                        |
| `journal/`    | Daily/weekly logs                                | Markdown with YAML frontmatter  |
| `archive/`    | Retired entities                                 | Same as source                  |

## Storage Conventions

- **Markdown** is the default. Knowledge, journal entries, inbox/outbox items are markdown
  files with optional YAML frontmatter for metadata.
- **Standalone YAML** only where structured data is the primary content: contact profiles,
  project status, goals, the brain index.
- **No duplication** between the index and entity files. The index is a lookup table, not a
  cache.

### Contacts

A directory per person with structured profile and freeform notes:

```
contacts/jane-smith/
├── profile.yaml      # role, company, relationship, communication prefs
└── notes.md          # observations, meeting notes, context
```

### Projects

A directory per project with structured status and freeform context:

```
projects/acme-api/
├── status.yaml       # current sprint, team, key dates, links
└── context.md        # architecture decisions, recent changes, notes
```

### Knowledge

A single markdown file per topic with optional frontmatter:

```markdown
---
tags: [database, infrastructure]
---

# Aurora Migration

We migrated from self-managed Postgres to Aurora in Q1 2025...
```

### Journal

Daily or weekly markdown files:

```
journal/2026-04-16.md
journal/2026-w16.md
```

## Brain Index

Each context has an `index.yaml` — a compact representation of what's in the brain, used as
LLM context during ingestion to guide entity placement decisions.

```yaml
contacts:
  jane-smith:
    name: Jane Smith
    summary: Engineering Lead, Platform team
    path: contacts/jane-smith/

projects:
  acme-api:
    name: Acme API
    summary: Core REST API, Python/FastAPI
    path: projects/acme-api/

knowledge:
  aurora-migration:
    name: Aurora Migration
    summary: Migration from self-managed Postgres to Aurora, Q1 2025
    path: knowledge/aurora-migration.md
```

Keyed by slug for direct lookup. Minimal fields: name, summary, path. The index is maintained
by the ingestion pipeline and can be regenerated from the entity files if it drifts.

## Source Tracking

Ingestion provenance is tracked in a SQLite database (`brain.db`) per context. This records
which source documents were ingested, when, and which brain entities they produced or updated.
Used for conflict detection, freshness checks, and re-ingestion.

The SQLite DB is gitignored — it's operational metadata, not knowledge. If lost, it can be
rebuilt (with loss of ingestion history).

## Information Flow

The life OS session is the single writer to the brain. Project sessions mount the brain
read-only.

```
Raw Input (Notion, Google Drive, transcripts, articles, conversations)
    │
    ▼
_raw/inbox/ — content dropped here for processing
    │
    ▼
Life OS Session — ingestion pipeline
    │
    ├── Move item to _raw/processing/
    ├── Extract structured data + summary
    ├── Check brain index for existing entities
    ├── LLM decides: create new entity or update existing
    ├── Flag conflicts to inbox (new data contradicts existing)
    ├── Update brain entities + index
    ├── Record provenance in SQLite
    ├── Auto-commit to git
    └── Move item to _raw/completed/
    │
    ▼
Brain (readable by all sessions)
```

The LLM decides entity placement within a context, guided by the brain index and ingestion
skills. The only hard routing is which context the input belongs to.

Conflicts — where new data contradicts existing brain content — are flagged to inbox rather
than silently overwriting.

## Inbox and Outbox

Human-in-the-loop checkpoints:

- **Inbox** — actionable items produced by ingestion (action items from meetings, flagged
  conflicts, suggested updates). Review and trigger actions (e.g. "create these as Linear
  tickets").
- **Outbox** — draft messages produced by Archie. Review, send manually, delete the draft.

## Git Conventions

- Auto-commit after each ingestion run with descriptive messages
- `brain.db` is gitignored per context
- `_raw/` sits outside context repos — no git concerns
- `git revert` is the rollback mechanism for bad ingestions
- Each context is committed independently (separate repos)
