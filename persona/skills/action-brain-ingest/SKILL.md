---
name: action-brain-ingest
description: >
  Process content into structured brain entities. Handles files from _raw/inbox,
  _inbox, or a specific file path. Extracts information, routes to the correct
  context, creates/updates entities, tracks provenance, and commits. Use when
  asked to "process inbox", "ingest into brain", "ingest this file", or
  "process raw items".
---

# Purpose

Process content through the ingestion pipeline: extract structured information,
route to the correct context(s), create or update brain entities, record
provenance, and commit.

---

# When to Use

- Processing items in `_raw/inbox/`
- Ingesting a specific file (e.g. research output from `_inbox/`)
- User drops content for brain ingestion

# When Not to Use

- Direct brain reads (use `action-brain-read`)
- Direct brain writes from conversation (use `action-brain-write`)

---

# Workflow

## 1. Determine source

**Direct file path:** if the user specifies a file (e.g. "ingest `_inbox/research.md`"),
process that file directly — skip to step 3.

**Pipeline mode:** check `_raw/inbox/` for items to process:

```bash
ak brain status
```

Look at the `raw.inbox` list. If empty, report "nothing to ingest" and stop.

Process items one at a time, in order.

## 2. Pick and move item (pipeline mode only)

Move the item from inbox to processing:

```bash
mv ~/.archie/brain/_raw/inbox/<item> ~/.archie/brain/_raw/processing/<item>
```

## 3. Read and extract

Read the raw item:

```bash
cat ~/.archie/brain/_raw/processing/<item>
```

Extract structured information:

- **People** mentioned (names, roles, relationships)
- **Projects** referenced
- **Decisions** made
- **Action items** identified
- **Knowledge** — facts, insights, reference material
- **Goals** or priorities mentioned

Not every item will contain all types. Extract what's present.

## 4. Route to context(s)

For each extracted entity, determine the target context:

1. Check indexes across all contexts: `ak brain index <context>`
2. Match extracted entities against existing index entries
3. Entities that match a work context → route there
4. General knowledge, personal content, no matches → `shared`

A single raw item may produce writes to multiple contexts.

**Routing decision:** the LLM makes a best-guess decision. If confidence is low
(ambiguous content, entities matching multiple contexts), route to best guess and
create an inbox note in the target context flagging the decision.

## 5. Write entities

For each entity to create or update, follow the `action-brain-write` pattern:

1. Check index for duplicates
2. Create new or update existing entity file
3. Use appropriate file format (see `tool-brain`)

**Merging with existing entities:** when new information relates to an existing
entity, read the existing file, merge the new information in, and write back.
Don't create a second file for the same concept.

**Conflict detection:** if new data contradicts existing brain content (e.g.
different role for a contact, different status for a project), don't silently
overwrite. Create an inbox note flagging the conflict:

```markdown
---
type: conflict
source: <raw-item-filename>
entity: <path-to-entity>
---

New data says <X>, existing brain says <Y>. Review and resolve.
```

## 6. Update indexes

After all writes for a context are complete:

```bash
ak brain reindex <context>
```

## 7. Record provenance

For each affected context, record what was ingested:

```bash
sqlite3 ~/.archie/brain/<context>/brain.db "
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    entities_created TEXT,
    entities_updated TEXT
);
INSERT INTO provenance (source_file, ingested_at, entities_created, entities_updated)
VALUES ('<raw-item-filename>', datetime('now'), '<json-array-of-created>', '<json-array-of-updated>');
"
```

`entities_created` and `entities_updated` are JSON arrays of relative paths within
the context (e.g. `["knowledge/aurora-failover.md", "contacts/jane-smith.yaml"]`).

## 8. Commit

One commit per affected context, specifying the files you wrote:

```bash
ak brain commit <context> -m "brain: ingest <raw-item-filename>" \
  --paths <file1> --paths <file2> --paths index.yaml
```

Include all entity files created/updated plus `index.yaml`.

## 9. Complete

Move the raw item to completed:

```bash
mv ~/.archie/brain/_raw/processing/<item> ~/.archie/brain/_raw/completed/<item>
```

## 10. Next item

If more items remain in `_raw/inbox/`, return to step 2.

When all items are processed, report a summary:
- Number of items processed
- Entities created/updated per context
- Any inbox notes created (routing flags, conflicts)

---

# Handling Different Input Types

### Markdown files / notes
Read directly, extract entities from content.

### URLs
Fetch the URL content, then extract as with any other content.

### Meeting transcripts
Focus on: decisions made, action items, people mentioned, project context.
Action items → inbox notes in the relevant context.

### Documents (PDF, etc.)
If readable as text, process normally. If not, note the limitation and skip.

---

# Example

**Raw item:** `_raw/inbox/meeting-notes-2026-04-18.md`

Content mentions: Jane Smith (Tillo), Aurora failover discussion, decision to use
multi-AZ, personal goal to finish Archie v1.

1. Move to `_raw/processing/`
2. Read and extract:
   - Contact: Jane Smith (Tillo context — matches existing index)
   - Knowledge: Aurora multi-AZ decision (general — `shared`)
   - Goal update: Archie v1 progress (personal — `shared`)
3. Route: Jane-related updates → `tillo`, knowledge + goal → `shared`
4. Write:
   - Update `tillo/contacts/jane-smith.yaml` (add meeting context)
   - Create `shared/knowledge/aurora-multi-az.md`
   - Update `shared/goals/archie-v1.yaml` (if exists)
5. Reindex both contexts
6. Record provenance in both `tillo/brain.db` and `shared/brain.db`
7. Commit: `tillo` then `shared`
8. Move to `_raw/completed/`
