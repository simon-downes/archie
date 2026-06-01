---
name: action-brain-ingest
description: >
  Process files from the brain's _raw/ directory into structured brain entities.
  Analyses content, decomposes multi-topic files, and routes information to the
  correct brain locations. Use when asked to "process raw", "ingest files",
  "process inbox", or when files are waiting in _raw/.
---

# Purpose

Transform unstructured files in `_raw/` into properly structured brain entities —
creating new entries or merging into existing ones. Handles single-topic files
(a contact card) and multi-topic files (a meeting transcript touching 5 subjects).

---

# When to Use

- Files are waiting in `_raw/` (check with `ls`)
- User asks to process raw files or ingest content
- After `--to-inbox` sends files to the raw directory

# When Not to Use

- Conversation memory extraction (use `action-memory-update`)
- Direct brain writes during conversation (use brain guidance directly)

---

# Workflow

## 1. List pending files

```bash
ls ~/.archie/brain/_raw/
```

If empty, report and finish.

## 2. Process each file

For each file in `_raw/` (one at a time):

### a. Read and analyse

Read the file content. Determine:
- **Source type**: meeting transcript, document, notes, contact info, email, etc.
- **Topics/entities**: what distinct pieces of information does this contain?
- **Routing**: where does each piece belong in the brain?

### b. Decompose (if multi-topic)

A meeting transcript might produce:
- Updates to `people/jane.md` (new role mentioned)
- A new entry in `knowledge/aws/aurora-migration.md` (technical decision)
- An update to `projects/platform/README.md` (timeline change)
- A note in `_inbox/` if there's a conflict or decision needed

Identify each discrete piece of information and its destination.

### c. Check for duplicates

For each identified entity, search your brain for existing entries on that topic
(refer to `# Available Tools`).

If a match exists → merge new information into the existing file.
If no match → create a new file.

### d. Write brain entries

Follow brain writing conventions:
- YAML frontmatter with `name`, `summary`, `tags`
- Use `[[wikilinks]]` for cross-references
- One file per entity
- Knowledge grouped by domain: `knowledge/<domain>/<topic>.md`

### e. Handle conflicts

If the source contains information that contradicts existing brain content:
- If the source is clearly newer → update the existing entry
- If unclear or the source is older → create a note in `_inbox/` flagging the
  discrepancy for user review

### f. Record provenance

```bash
sqlite3 ~/.archie/brain/brain.db "
INSERT INTO provenance (source_file, ingested_at, entities_created, entities_updated)
VALUES ('<filename>', datetime('now'), '<json-list>', '<json-list>');
"
```

### g. Remove source file

```bash
rm ~/.archie/brain/_raw/<filename>
```

## 3. Reindex and commit

After processing all files, reindex the brain and commit all modified files
(refer to `# Available Tools`).

## 4. Report

Summarise:
- Files processed
- Entities created (with paths)
- Entities updated (with paths)
- Items flagged in `_inbox/` (if any)

---

# Decomposition strategies

## Meeting transcripts / notes

Look for:
- **People**: new contacts, role changes, preferences mentioned
- **Decisions**: architectural choices, process changes, agreements
- **Action items**: tasks assigned, deadlines set
- **Knowledge**: technical details, domain information worth preserving
- **Project updates**: timeline changes, status updates, blockers

## Documents / articles

- Extract the core knowledge into `knowledge/<domain>/`
- Note any people or projects referenced
- Preserve source attribution in the body

## Contact information

- Route to `people/<name>.md`
- Merge with existing if the person already exists

## Email threads

- Extract decisions and action items
- Update relevant project or person entries
- Discard transient back-and-forth

---

# Key principles

- **Analyse before writing** — understand the full file before creating any entries
- **Merge over create** — always search for existing entries first
- **One entity per file** — don't combine unrelated topics in a single brain file
- **Preserve context** — include enough context that the entry is useful standalone
- **Flag uncertainty** — if unsure where something belongs, put a note in `_inbox/`
