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
ingestion skills. Context routing is content-based — the LLM analyses the content,
matches entities against existing brain indexes, and routes to the context with the
most matches. No source tagging is required. `shared` is the default when no context
scores.

When routing confidence is low, the LLM routes to its best guess and creates an
inbox note flagging the decision for review.

Conflicts — where new data contradicts existing brain content — are flagged to the
context's inbox rather than silently overwriting.

## Source Tracking

Ingestion provenance is tracked in a SQLite database (`brain.db`) per context. This
records which source documents were ingested, when, and which brain entities they
produced or updated. Used for conflict detection, freshness checks, and re-ingestion.

The SQLite DB is gitignored — it's operational metadata, not knowledge. If lost, it
can be rebuilt (with loss of ingestion history).

## Memory

Conversation memory lives in `_memory/` at the brain root — a device-local directory
outside any context's git repo, alongside `_raw/`.

Files are named `<date>-<identifier>.md`: project sessions use the project name
(`2026-04-18-archie.md`), general sessions use a conversation ID prefix
(`2026-04-18-c951.md`). One file per day per project; one file per general session.

Each file contains turn-by-turn summaries grouped under topic headings, with prefixes
(Discussed, Decided, Action, Correction) to make scanning easy.

The `action-brain-memory` skill processes conversations: a prep script extracts clean
turn pairs from kiro-cli's SQLite database, then the LLM summarises them into memory
files. Watermark tracking ensures conversations are only processed once.

## Inbox and Outbox

Global operational queues at the brain root — device-local, not in any context's
git repo.

- **`_inbox/`** — items for the user to read. Research output, reports, generated
  documents. Review and optionally ingest into the brain.
- **`_outbox/`** — items for the user to act on. Draft messages, action items.
  Review, send manually, delete when done.

## Git Conventions

- Auto-commit after each ingestion run with descriptive messages
- Ingestion commits: `brain: ingest <source-filename>`
- Manual write commits: `brain: <brief description>`
- `brain.db` is gitignored per context
- `_raw/` sits outside context repos — no git concerns
- `git revert` is the rollback mechanism for bad ingestions
- Each context is committed independently (separate repos)
- One commit per context per operation (not per entity)

## Skills

Brain operations are driven by four skills:

| Skill | Layer | Purpose |
|-------|-------|---------|
| `tool-brain` | Tool | CLI commands, file formats, shell tool patterns |
| `action-brain-read` | Action | Query brain and memory via index lookup + grep |
| `action-brain-write` | Action | Write with dedup, routing, index update, commit |
| `action-brain-ingest` | Action | Ingestion pipeline from `_raw/inbox/` or direct path |
| `action-brain-memory` | Action | Summarise conversations into memory files |
| `action-research` | Action | Research a topic, produce document in `_inbox/` |

## Knowledge Structure

Knowledge files live in `<context>/knowledge/` as markdown with YAML frontmatter
(`tags`, `summary`). Start flat — introduce subdirectories only when a clear cluster
of 5+ related files emerges. Slugs are the stable identifier in the index; paths can
change when files are reorganised.
