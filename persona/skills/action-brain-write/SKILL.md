---
name: action-brain-write
description: >
  Write or update entities in Archie's second brain with deduplication, context routing,
  and index management. Handles creating knowledge, contacts, projects, goals, and other
  entities. Use when adding information to the brain, updating existing brain entities,
  recording decisions or learnings, or when asked to "remember this", "add to brain",
  "update brain", or "save to brain".
---

# Purpose

Write to the brain with deduplication checking, correct context routing, index updates,
and git commits. Ensures no duplicate entities and content goes to the right context.

---

# When to Use

- Adding new knowledge, contacts, projects, or goals to the brain
- Updating existing brain entities with new information
- Recording decisions, learnings, or context from conversations
- Any write operation to the brain

# When Not to Use

- Reading or querying the brain (use `action-brain-read`)
- Processing raw inbox items (use `action-brain-ingest`)

---

# Workflow

## 1. Determine target context

If the target context is explicit (user specifies, or session context is clear), use it.

If not, determine context from content:

1. Extract key entities from the content (people, companies, projects, topics)
2. Check the index of each context: `ak brain index <context>`
3. Match extracted entities against index entries across all contexts
4. Highest number of matches determines the context
5. Default to `shared` when no context scores

**Low-confidence routing:** if the top two contexts score similarly, or no context
has strong matches:
- Route to best guess
- Create an inbox note (see step 5)

## 2. Check for duplicates

Before creating any entity, check the index for existing matches:

```bash
# Check by slug
ak brain index <context> --slug <candidate-slug>

# Check by type for name similarity
ak brain index <context> --type <entity-type>
```

**If a match exists:** update the existing file rather than creating a new one.
Merge new information into the existing content — don't overwrite wholesale.

**If no match:** proceed to create a new entity.

## 3. Write the entity

### New entity

Create the file with appropriate format (see `tool-brain` for file formats):

- **Knowledge:** `<context>/knowledge/<slug>.md` with frontmatter (`tags`, `summary`)
- **Contacts:** `<context>/contacts/<slug>.yaml`
- **Projects:** `<context>/projects/<slug>/README.md` with frontmatter
- **Goals:** `<context>/goals/<slug>.yaml`
- **Journal:** `<context>/journal/<date>.md` (no index entry needed)
- **Inbox notes:** `<context>/inbox/<slug>.md` with frontmatter

### Knowledge structure

Place new knowledge files flat in `knowledge/` unless a relevant subdirectory
already exists:

```bash
ls ~/.archie/brain/<context>/knowledge/
```

If a subdirectory exists that clearly matches the topic (e.g. `aws/` for an AWS
topic), place the file there. Otherwise, create at the top level.

**Introduce a subdirectory** only when 5+ related files exist at the top level.
When creating a subdirectory, move the related files into it and update the index.

### Updated entity

Read the existing file, merge new information, write back. Preserve existing
content — add to it, don't replace unless the new information supersedes the old.

Update frontmatter if needed (e.g. new tags, updated summary).

## 4. Update the index

After writing, update `index.yaml` for the context:

```bash
ak brain reindex <context>
```

Or for a targeted update, edit `index.yaml` directly to add/update the entry.
`reindex` is simpler and safer for most cases.

## 5. Create inbox note (if needed)

When routing confidence is low, create a note in the target context's inbox:

```markdown
---
type: routing-flag
source: <what triggered this write>
context: <target context>
confidence: low
---

<Explanation of routing decision and what to check>
```

File: `<context>/inbox/routing-<slug>-<date>.md`

## 6. Commit

Commit all changes to the context in a single commit:

```bash
ak brain commit <context> -m "brain: <brief description>"
```

If writes span multiple contexts, commit each independently.

---

# Writing to Multiple Contexts

A single piece of information may produce writes to multiple contexts:

- Company-specific facts → work context
- General knowledge or insights → `shared`
- Personal reflections → `shared`

Process each context's writes separately: write files, update index, commit.

---

# Example

**User:** "Remember that Aurora PostgreSQL failover takes about 30 seconds and
the writer endpoint DNS TTL is 5 seconds."

1. **Context:** general knowledge, no company-specific entities → `shared`
2. **Dedup:** `ak brain index shared --type knowledge` → check for aurora-related slugs
3. **No match:** create `shared/knowledge/aurora-failover.md`:
   ```markdown
   ---
   tags: [aws, aurora, databases, failover]
   summary: Aurora PostgreSQL failover behaviour and timing
   ---

   # Aurora PostgreSQL Failover

   - Failover takes approximately 30 seconds
   - Writer endpoint DNS TTL is 5 seconds
   ```
4. **Index:** `ak brain reindex shared`
5. **Commit:** `ak brain commit shared -m "brain: add aurora failover knowledge"`
