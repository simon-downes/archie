---
name: action-brain-read
description: >
  Query Archie's second brain to retrieve relevant knowledge, contacts, projects, goals,
  or other entities. Uses index lookup with grep fallback for comprehensive retrieval.
  Use when answering questions that may be in the brain, looking up contacts or project
  context, searching for knowledge on a topic, or when asked to "check the brain",
  "what do I know about", or "find in brain".
---

# Purpose

Retrieve information from the brain using a two-step pattern: index lookup first, then
full-text search as fallback. Synthesise findings into a useful response.

---

# When to Use

- Answering questions where the brain may have relevant context
- Looking up contacts, projects, goals, or knowledge
- Searching for information on a topic across contexts
- Providing context before making decisions

# When Not to Use

- Writing or updating brain content (use `action-brain-write`)
- Processing raw inbox items (use `action-brain-ingest`)

---

# Workflow

## 1. Determine search scope

Decide which context(s) to search:

- **Specific context known** — search only that context (e.g. user asks about a
  company-specific topic, search the work context)
- **Unknown or cross-cutting** — search all contexts
- **Project session** — start with the project's context, expand if not found

Use `ak brain index` (no arguments) to list available contexts if needed.

## 2. Index lookup

Check the brain index for matching entities:

```bash
# Full index for a context
ak brain index <context>

# Filter by entity type
ak brain index <context> --type knowledge
ak brain index <context> --type contacts

# Lookup specific slug
ak brain index <context> --slug <slug>
```

Scan index entries for name/summary matches against the query. If matches found,
read the matched files directly.

## 3. Full-text search (if index insufficient)

When the index doesn't have a match, or the query is broad:

```bash
# Search across a context
rg "<search-term>" ~/.archie/brain/<context>/ -t md -t yaml --glob '!.git' -l

# Search across all contexts
rg "<search-term>" ~/.archie/brain/ --glob '!.git' --glob '!_raw' -l

# Case-insensitive search
rg -i "<search-term>" ~/.archie/brain/<context>/ --glob '!.git' -l
```

Use `-l` (files only) first to identify relevant files, then read the specific files.

## 4. Read matched files

Read the content of matched files:

```bash
cat ~/.archie/brain/<context>/<path>
```

For multiple matches, read the most relevant ones (based on filename/path relevance
to the query). Don't read everything — be selective.

## 5. Synthesise

Combine findings into a response:

- State what was found and which context(s) it came from
- If nothing found, say so clearly
- If partial matches, present what exists and note gaps

---

# Multi-context Search Order

When searching across contexts:

1. If in a project session, start with the project's context
2. Then search `shared` (general knowledge)
3. Then search remaining contexts

Stop early if a definitive answer is found — don't search exhaustively unless the
query warrants it.

---

# Example

**User:** "What do I know about Aurora failover?"

1. `ak brain index shared --type knowledge` → scan for aurora-related entries
2. Found `aurora-failover` slug → `cat ~/.archie/brain/shared/knowledge/aurora-failover.md`
3. Present the content

**User:** "Who is Jane?"

1. `ak brain index shared --type contacts` → no match
2. `ak brain index tillo --type contacts` → found `jane-smith`
3. `cat ~/.archie/brain/tillo/contacts/jane-smith.yaml`
4. Present contact info, noting it's from the tillo context
