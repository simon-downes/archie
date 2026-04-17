# Brain

The brain is Archie's persistent knowledge store — a second brain that grows from
conversations, ingested documents, and manual curation.

For the structural details (contexts, entity directories, index format, CLI commands),
see the [agent-kit brain documentation](../agent-kit/docs/brain.md). This document
covers how Archie uses the brain.

## Sessions and Access

- **Project sessions** mount the brain read-only — it's context available if needed
- **Archie session** (archie project) mounts the brain read-write — this is where
  ingestion, updates, and curation happen

The Archie session is the single writer. Project sessions are consumers.

## Identity

`shared/me/` is the single canonical source of who the user is — personality,
communication style, preferences, goals. It informs how Archie communicates, drafts
messages, and prioritises work.

Context-specific information about the user's role (title, team, OKRs at a company)
is modelled as properties of the context (contacts, team structure, goals), not as
additional `me/` directories.

## Storage Conventions

- **Markdown** is the default for content. Knowledge, journal entries, inbox/outbox
  items are markdown files with optional YAML frontmatter for metadata.
- **Standalone YAML** only where structured data is the primary content: contact
  profiles, goals, the brain index.
- **Projects** use `README.md` with YAML frontmatter — renders on GitHub, co-locates
  metadata with content.
- **No duplication** between the index and entity files. The index is a lookup table.

## Information Flow

```
Raw Input (Notion, Google Drive, transcripts, articles, conversations)
    │
    ▼
_raw/inbox/ — content dropped here for processing
    │
    ▼
Archie session — ingestion pipeline
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

The LLM decides entity placement within a context, guided by the brain index and
ingestion skills. The only hard routing is which context the input belongs to.

Conflicts — where new data contradicts existing brain content — are flagged to the
context's inbox rather than silently overwriting.

## Source Tracking

Ingestion provenance is tracked in a SQLite database (`brain.db`) per context. This
records which source documents were ingested, when, and which brain entities they
produced or updated. Used for conflict detection, freshness checks, and re-ingestion.

The SQLite DB is gitignored — it's operational metadata, not knowledge. If lost, it
can be rebuilt (with loss of ingestion history).

## Memory

Archie's session memory is built on the brain. Kiro-cli persists conversation history
in a SQLite database. A memory ingestion pipeline reads conversations since the last
ingestion, extracts notable decisions, context, and learnings, and writes updates to
the brain (journal entries, project context, knowledge, inbox items).

This closes the learning loop: work happens → conversation captured → memory ingestion
processes it → brain updated → next session has that context.

## Inbox and Outbox

Human-in-the-loop checkpoints:

- **Inbox** — actionable items produced by ingestion (action items from meetings,
  flagged conflicts, suggested updates). Review and trigger actions (e.g. "create
  these as Linear tickets").
- **Outbox** — draft messages produced by Archie. Review, send manually, delete
  the draft.

## Git Conventions

- Auto-commit after each ingestion run with descriptive messages
- `brain.db` is gitignored per context
- `_raw/` sits outside context repos — no git concerns
- `git revert` is the rollback mechanism for bad ingestions
- Each context is committed independently (separate repos)
