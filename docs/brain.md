# Brain

A persistent knowledge base that serves both Simon (human retrieval) and Archie
(programmatic retrieval). Single git repo at `~/.archie/brain/`.

## Structure

```
brain/
├── BRAIN.md              # Convention guide
├── _archie/              # Agent operational state
│   ├── soul.md           # Live personality (evolves)
│   ├── memory.md         # Consolidated observations (always-loaded)
│   ├── signals.yaml      # Learning signals
│   └── memory/           # Session memories (indexed, searchable)
├── _raw/                 # Ingestion staging (files awaiting processing)
├── _inbox/               # User attention queue (needs human review)
├── simon/                # User's personal space
│   ├── profile.md        # Structured profile (always-loaded)
│   ├── goals.md          # Current priorities
│   └── journal/          # Personal dated entries
├── people/               # Relationships and contacts
├── projects/             # Lightweight project context
└── knowledge/            # Durable reference knowledge
```

## Principles

- **Simon's knowledge base, Archie-accessible** — not "Archie's brain that Simon can read"
- **Project docs live in repos** — brain holds lightweight pointers/summaries, not code docs
- **Single repo, no contexts** — one place to look, one commit covers all changes
- **Wikilinks** — `[[people/jane]]`, `[[projects/tillo]]` for associative navigation

## Setup

```bash
archie init
```

Creates the brain directory structure with a templated `BRAIN.md` convention guide.

## CLI

| Command | Description |
|---------|-------------|
| `archie brain search <terms>` | Multi-term ranked search |
| `archie brain read <path>` | Read a brain file |
| `archie brain memory` | Recent session memories |
| `archie brain index` | Query the entity index |
| `archie brain reindex` | Rebuild index from filesystem |
| `archie brain commit <msg>` | Stage and commit changes |
| `archie brain ref <path>` | Record an access (reference tracking) |
| `archie brain refs` | Query reference data (--top, --stale) |

## What Lives Where

| Content | Location |
|---------|----------|
| Project architecture, decisions | In the repo (docs/, ADRs) |
| Personal goals, people, life context | Brain |
| Agent operational state (signals, memory, soul) | Brain (`_archie/`) |
| Project-specific context (not code) | Brain (`projects/<name>/`) |
| Durable reference knowledge | Brain (`knowledge/`) |
