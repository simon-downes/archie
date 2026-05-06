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
│   └── memory/           # Raw session memories
├── _inbox/               # Ingestion staging
├── simon/                # User's personal space
│   ├── profile.md        # Structured profile (always-loaded)
│   ├── goals.md          # Current priorities
│   ├── inbox/            # Things needing attention
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
ak init
```

Prompts for user name and agent name, creates the full directory structure with
a templated `BRAIN.md` convention guide.

## CLI

| Command | Description |
|---------|-------------|
| `ak brain search <terms>` | Multi-term ranked search |
| `ak brain index` | Query the entity index |
| `ak brain reindex` | Rebuild index from filesystem |
| `ak brain commit <msg>` | Stage and commit changes |
| `ak brain ref <path>` | Record an access (reference tracking) |
| `ak brain refs` | Query reference data (--top, --stale) |
| `ak brain status` | Directory info and git status |

## What Lives Where

| Content | Location |
|---------|----------|
| Project architecture, decisions | In the repo (docs/, ADRs) |
| Personal goals, people, life context | Brain |
| Agent operational state (signals, memory, soul) | Brain (`_archie/`) |
| Project-specific context (not code) | Brain (`projects/<name>/`) |
| Durable reference knowledge | Brain (`knowledge/`) |

## Responsibility Split

- **Agent-kit** provides structure and mechanics: `ak init`, `ak brain search/ref/reindex`
- **Archie** provides intelligence and lifecycle: skills that decide what to write,
  memory consolidation, signal extraction, soul evolution
