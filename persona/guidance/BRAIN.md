# Brain

Operational guidance for the second brain — how to read, write, and manage content.

## Location

Default: `~/.archie/brain/`. A single git repo.

## Directory Layout

```
brain/
├── BRAIN.md              # Convention guide (structure, interaction patterns)
├── _archie/              # Agent operational state
│   ├── soul.md           # Personality (evolves)
│   ├── memory.md         # Consolidated observations
│   ├── signals.yaml      # Learning signals
│   └── memory/           # Raw session memories
├── _inbox/               # Ingestion staging
├── simon/                # User's personal space
│   ├── profile.md        # Structured profile
│   ├── goals.md          # Current priorities
│   ├── inbox/            # Things needing user's attention
│   └── journal/          # Personal dated entries
├── people/               # Relationships and contacts
├── projects/             # Lightweight project context
└── knowledge/            # Durable reference knowledge
```

---

## Reading

Primary command: `ak brain search` — searches index metadata and file content,
returning ranked results.

```bash
ak brain search "aurora"                    # single term
ak brain search "terraform" "module" "vpc"  # multiple terms (OR, ranked)
ak brain search "aurora" --limit 5          # fewer results
```

Results are ranked by match quality:
- **+3** — term in filename/title
- **+2** — term in tags
- **+1** — term in body content

Multiple terms matching the same file boost its rank.

Each result includes `path` (relative to brain root), `score`, `matches`, and `name`.
Read a result with `cat ~/.archie/brain/{path}`.

### Direct index lookup

```bash
ak brain index                        # full index
ak brain index --type people          # filter by type
ak brain index --slug alice           # lookup by slug
```

### Record access (reference tracking)

```bash
ak brain ref <path>
```

Non-critical — helps identify high-value vs stale entries over time.

---

## Writing

### Determine location

Follow the conventions in `BRAIN.md` at the brain root:
- People → `people/<slug>.md`
- Projects → `projects/<name>/` (with `context.md`, `journal/`, `decisions/`)
- Knowledge → `knowledge/<domain>/<slug>.md`
- Personal → `simon/journal/`, `simon/goals.md`
- Agent state → `_archie/`

### Check for duplicates

Before creating any entity:

```bash
ak brain search "<name>"
ak brain index --slug <candidate-slug>
```

**Match exists:** update the existing file — merge new information, don't overwrite.
**No match:** create a new entity.

### Conflict detection

If new data contradicts existing brain content, don't silently overwrite. Create
a note in `simon/inbox/`:

```markdown
---
type: conflict
entity: <path-to-entity>
---

New data says <X>, existing brain says <Y>. Review and resolve.
```

### Entity formats

**Knowledge** — `knowledge/<domain>/<slug>.md`
```markdown
---
tags: [aws, aurora, databases]
summary: One-line description
---

# Title

Content...
```

**People** — `people/<slug>.md`
```markdown
---
name: Jane Smith
summary: Engineering Manager at Tillo
tags: [tillo, engineering]
---

Context and notes...
```

**Projects** — `projects/<name>/context.md`
```markdown
---
name: Project Name
summary: One-line description
---

Current focus, status, key links...
```

**Journal** — `simon/journal/<date>.md` or `projects/<name>/journal/<date>.md`

Use `[[wikilinks]]` for associative links: `[[people/jane]]`, `[[projects/tillo]]`.

### Index and commit

After writing:

```bash
ak brain reindex
ak brain commit "brain: <description>" --paths <file1> --paths <file2> --paths index.yaml
```

Always include `index.yaml` if you ran reindex.

---

## CLI Reference

### `ak brain search <term> [<term>...] [--limit N]`
Search across index metadata and file content. Returns ranked results.

### `ak brain index [--type <type>] [--slug <slug>]`
Query the brain index.

### `ak brain reindex`
Rebuild `index.yaml` from filesystem.

### `ak brain commit <message> [--paths <file> ...]`
Stage and commit.

### `ak brain ref <path>`
Record an access for reference tracking.

### `ak brain refs [--top N] [--stale --since Nd]`
Query reference tracking data.

### `ak brain status`
Brain directory info and git status.

### `ak brain project [name]`
Get project info from the brain.

---

## Key Rules

- Single git repo — one commit covers all changes
- `brain.db` is gitignored — operational metadata, not knowledge
- `_inbox/` files = ready for processing, subdirs = staging
- Use `[[wikilinks]]` for links between entries
- Run `ak brain reindex` after creating/moving files
