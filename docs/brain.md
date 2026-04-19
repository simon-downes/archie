# Brain

The brain is Archie's persistent knowledge store — a second brain that grows from
conversations, ingested documents, and manual curation. Everything Archie learns
persists here, so context carries across sessions and projects.

## Contexts

The brain is divided into contexts — separate areas for different parts of your life.
Each context is an independent git repository, so changes are versioned and reversible.

- **shared** — personal knowledge, general contacts, cross-cutting projects, goals.
  The default when information doesn't belong to a specific work context.
- **Work contexts** (e.g. `tillo`) — company-specific knowledge, colleagues, projects,
  and goals. One context per organisation.

Archie routes information to the right context automatically based on content. If it
mentions your company's projects or people, it goes to the work context. General
knowledge goes to `shared`. When routing is uncertain, Archie makes its best guess
and flags the decision for your review.

## What's Stored

Each context contains the same directory structure:

| Directory | Contents | Format |
|-----------|----------|--------|
| `me/` | Your identity, preferences, communication style | Markdown |
| `contacts/` | People — names, roles, context on how you know them | YAML |
| `projects/` | Active work — each project gets a directory with a README | Markdown + YAML frontmatter |
| `knowledge/` | Facts, reference material, decisions, learnings | Markdown + YAML frontmatter |
| `goals/` | Priorities, OKRs, targets | YAML |
| `journal/` | Date-based logs and notes | Markdown |
| `archive/` | Retired entities | Mixed |

The `shared/me/` directory is special — it's the canonical source of who you are.
Archie uses it to understand your communication style, preferences, and priorities.
Work-specific role information (your title, team, OKRs at a company) lives in the
work context, not in `me/`.

## Memory

Conversation memory lives in `_memory/` at the brain root. After work sessions,
Archie can summarise what happened into structured memory files — capturing what was
discussed, decided, and done.

Memory files are organised by date and project:
- `2026-04-18-archie.md` — work on the Archie project that day
- `2026-04-14-tillo-platform.md` — work on the Tillo platform
- `2026-04-18-c951.md` — a general (non-project) conversation

Each file groups conversation summaries under topic headings with prefixes that make
scanning easy:
- **Discussed** — explored a topic, considered options
- **Decided** — made a choice with rationale
- **Action** — implemented something, completed work
- **Correction** — fixed a mistake, changed direction

At the start of each session, Archie silently checks recent memory for relevant
context. You don't need to re-explain what you were working on yesterday — it already
knows.

**Trigger memory processing:** say "process recent conversations" or "update memory"
to summarise sessions that haven't been captured yet.

## Inbox and Outbox

Two operational queues at the brain root:

- **`_inbox/`** — items for you to read. Research output, generated reports, analysis
  documents. Review them and optionally ingest into the brain for permanent storage.
- **`_outbox/`** — items for you to act on. Draft messages, action items. Review,
  send manually, delete when done.

These are working directories, not permanent storage. Process items and clear them out.

## Ingestion

The brain grows through three channels:

### Conversations
When you tell Archie something worth remembering — a decision, a fact, a preference —
it writes directly to the brain. No special command needed. Archie mentions when it
saves something.

### Raw Inbox
Drop files into `_raw/inbox/` for batch processing. Meeting notes, article exports,
transcripts, Notion exports — anything with information worth extracting. Say "process
the inbox" and Archie will:

1. Read each item and extract structured information (people, projects, decisions, knowledge)
2. Route entities to the correct context
3. Deduplicate against existing brain content
4. Flag conflicts (new data contradicts existing) for your review
5. Commit changes to git

### Research
Ask Archie to research a topic and it produces a document in `_inbox/`. Review it,
then optionally ingest it into the brain for permanent storage.

## How Archie Uses the Brain

**Session start:** Archie checks `_memory/` for recent entries related to the current
project or topic. This happens silently — it uses the context to inform responses
without dumping contents at you.

**Domain questions:** When you ask about people, projects, decisions, or anything that
could be in the brain, Archie checks the brain before falling back to general knowledge.
It searches the index first, then does full-text search if needed.

**Persisting decisions:** When you make a decision or state a fact worth keeping, Archie
writes it to the brain automatically. It deduplicates against existing entries and routes
to the correct context.

**Not everything goes in the brain.** Simple coding questions, general knowledge, and
transient debugging don't trigger brain reads or writes. The brain is for durable
context — decisions, domain knowledge, people, project context.

## Brain Commands

Agent-kit provides CLI commands for brain management:

| Command | What it does |
|---------|-------------|
| `ak brain status` | Show brain state — raw pipeline, git changes per context |
| `ak brain index [context]` | Query the brain index (list contexts, search entities) |
| `ak brain reindex <context>` | Rebuild the index from filesystem state |
| `ak brain validate [context]` | Check structure and index integrity |
| `ak brain commit <context> -m "..."` | Commit changes in a context |

You rarely need these directly — Archie manages the brain through its own workflows.
They're useful for manual inspection or troubleshooting.

---

## Technical Details

This section covers internals for contributors. Users can stop reading here.

### Directory Layout

```
brain/
├── _raw/                    # Ingestion pipeline (device-local)
│   ├── inbox/               # Items to process
│   ├── processing/          # Currently being processed
│   └── completed/           # Done
├── _inbox/                  # Items for user to read
├── _outbox/                 # Items for user to act on
├── _memory/                 # Conversation memory (device-local)
├── shared/                  # Personal/general context (git repo)
│   ├── me/
│   ├── contacts/
│   ├── projects/
│   ├── knowledge/
│   ├── goals/
│   ├── journal/
│   ├── archive/
│   ├── index.yaml
│   └── brain.db             # Provenance tracking (gitignored)
└── <work-context>/          # Same structure, separate git repo
```

`_raw/`, `_inbox/`, `_outbox/`, and `_memory/` are device-local directories outside
any context's git repo.

### Session Access

- **Project sessions** mount the brain read-only
- **Archie sessions** (archie project) and **general sessions** mount read-write

### Index Format

`index.yaml` per context, keyed by entity type then slug:

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

Slugs are stable identifiers. Paths can change when files are reorganised —
run `ak brain reindex` to update.

### File Formats

- **Knowledge:** Markdown with YAML frontmatter (`tags`, `summary`)
- **Contacts:** YAML (`name`, `summary`, `email`, `context`)
- **Projects:** `README.md` with YAML frontmatter (`name`, `summary`, issue tracker config)
- **Goals:** YAML (`name`, `summary`, `status`, `target`)
- **Inbox notes:** Markdown with YAML frontmatter (`type`, `source`, `context`, `confidence`)

### Provenance Tracking

Each context has a `brain.db` (SQLite, gitignored) that records which source documents
were ingested, when, and which entities they produced or updated. Used for conflict
detection, freshness checks, and re-ingestion. If lost, it can be rebuilt with loss
of ingestion history.

### Knowledge Structure

Knowledge files live in `<context>/knowledge/` as markdown. Start flat — introduce
subdirectories only when 5+ related files cluster on a topic.

### Git Conventions

- Each context is a separate git repo, committed independently
- Ingestion commits: `brain: ingest <source-filename>`
- Manual write commits: `brain: <brief description>`
- `brain.db` is gitignored
- `git revert` is the rollback mechanism for bad ingestions
- One commit per context per operation

### Memory Watermark

Conversation memory processing uses a watermark in `shared/brain.db` to track the
last processed conversation timestamp, ensuring conversations are only summarised once.
