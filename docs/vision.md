# Vision

Archie is a personal AI platform that amplifies your effectiveness across all areas of your
life. It manages your knowledge, understands your context, and acts on your behalf — handling
operational overhead so you can focus on the work that matters.

## North Star

A single, integrated AI assistant that knows you, learns from every interaction, and can
extend its own capabilities. Not a collection of tools — one system that presents as one
entity, regardless of what's happening underneath.

## Principles

1. **Single integrated experience** — one assistant, not a collection of tools. Archie is
   Archie regardless of which session you're in or what you're doing.

2. **You set direction, Archie executes** — high-level intent in, completed work out.
   Discovery is brief and focused. Implementation is autonomous.

3. **Knowledge is the foundation** — everything builds on a well-maintained second brain.
   Without knowledge, there's no context. Without context, there's no intelligence.

4. **Human-in-the-loop where it matters** — inbox/outbox pattern. Archie processes, extracts,
   and drafts. You review and act. Autonomy increases as trust is established.

5. **Self-improving** — Archie can research, plan, implement, review, and ship new
   capabilities for itself. The most important capability is the ability to add capabilities.

6. **Layered implementation** — clean separation of concerns internally, unified externally.
   Separate repos and packages where it aids development and installation, but one platform
   to the user.

7. **Files over services** — markdown, YAML, SQLite, git. No running infrastructure required.
   The brain is files on disk. The index is a YAML file. Provenance tracking is SQLite.
   Everything works offline and in containers.

8. **Platform independence** — built on open formats and CLI tools. The AI harness (currently
   kiro-cli) is a replaceable component. The platform's value is in the brain, skills, and
   integrations, not in any specific LLM runtime. Prefer general approaches over
   harness-specific mechanisms where possible.

9. **Design for many, implement for one** — the codebase is generic and role-agnostic. All
   personalisation comes from the brain and config, not from the code. Anyone can run their
   own Archie.

## Architecture Decisions

Decisions made during the initial discovery phase. Each captures the options considered and
the rationale for the chosen approach.

### Unified UX, Layered Implementation

Archie presents as a single integrated system but is implemented as separable layers. Similar
to how agent-kit is a separate project for installation purposes but part of the archie
ecosystem. The brain contexts are separate git repos but part of the platform.

### Session Model

Two session types, distinguished by what's writable:

- **Project sessions** — project code read/write, brain read-only. For focused work on a
  specific codebase. Unchanged from current behaviour.
- **Archie session** — brain read/write. For knowledge work, ingestion, planning, summaries,
  and self-extension. Runs from the archie project directory.

The full brain is mounted read-only into every project session — it's context available if
needed, not loaded automatically. No per-project context filtering. The Archie session is
the single writer to the brain.

**Rejected alternatives:**
- Mounting only relevant contexts per project — too much config overhead for little benefit.
- Mixing Archie-level work into project sessions — muddies the concern, project sessions should be
  about the project.
- Mounting all projects into one session — too confusing, increases blast radius.

### Brain as Separate Git Repos

The brain lives at `~/.archie/brain/` and is composed of top-level context directories, each
a separate git repository:

```
~/.archie/brain/
├── shared/          # cross-cutting: identity, contacts, general knowledge
├── work-acme/       # company-specific: projects, team, knowledge, goals
├── personal/        # personal: projects, interests, goals
└── ...              # arbitrary additional contexts
```

Separate repos enable: different storage locations (company org vs personal org), different
availability per device, independent version history, and clear confidentiality boundaries.

**Rejected alternatives:**
- Flat structure with context tags — loses the confidentiality boundary and per-device
  flexibility.
- Shared-by-default with scoped exceptions — ambiguous, harder to reason about.

### Storage Format

Markdown for prose/notes, YAML for structured data, co-located where appropriate.

- **Standalone YAML** where structured data is the primary content: contact profiles, project
  status, goals, the brain index.
- **Markdown with YAML frontmatter** where prose is the primary content: knowledge entries,
  journal entries.
- **Plain markdown** where no structured metadata is needed: inbox, outbox, notes.

Source provenance is tracked in SQLite (`brain.db` per context), not in the content files.
The SQLite DB is gitignored — it's operational metadata for the ingestion pipeline.

**Rejected alternatives:**
- YAML everywhere — too heavy for knowledge/journal entries.
- Frontmatter for source tracking — clutters the content files with ingestion metadata that
  only the pipeline cares about.
- SQLite as primary store — not human-readable, git diffs useless, LLMs can't read directly.

### Identity Layer

`shared/me/` is the single canonical source of who the user is — personality, communication
style, preferences, goals.

Context-specific information about the user's role (title, team, OKRs at a company) is
modelled as properties of the context itself (contacts, team structure, goals), not as
additional `me/` directories per context.

**Rejected alternatives:**
- `me/` directories in each context — most "me at work" data is actually about the role/context,
  not about the person. Creates ambiguity about where to look.

### Information Flow

The Archie session is the single writer to the brain. Unidirectional flow.

Project sessions signal changes through external systems (GitHub, Linear) and Archie
picks them up on the next sync. This avoids concurrent write conflicts and keeps the data
flow simple.

### Ingestion Pipeline

```
Raw Input → Extract + Summarise → Check Index → Create/Update Entities → Flag Conflicts → Auto-commit
```

- The LLM decides entity placement within a context, guided by the brain index and skills.
  No hardcoded routing rules.
- Conflicts (new data contradicts existing) are flagged to inbox, not silently overwritten.
- Source provenance tracked in SQLite for freshness checks and re-ingestion.
- Auto-commit after each ingestion run with descriptive messages. Git history is the audit
  trail; `git revert` is the rollback mechanism.
- Raw inputs land in `raw/` (gitignored) per context. Presence in `raw/` indicates
  unprocessed items.

### Inbox and Outbox

Human-in-the-loop checkpoints:

- **Inbox** — actionable items produced by ingestion (action items from meetings, flagged
  conflicts, suggested updates). User reviews and triggers actions (e.g. "create these as
  Linear tickets").
- **Outbox** — draft messages produced by Archie. User reviews, sends manually, deletes the
  draft. No automated sending initially.

### Memory

Day-0 capability. Kiro-cli persists conversation history in a SQLite database. A memory
ingestion pipeline reads conversations since the last ingestion, extracts notable decisions,
context, and learnings, and writes updates to the brain.

This closes the learning loop: work happens → conversation captured → memory ingestion
processes it → brain updated → next session has that context.

### Integrations

Current: `ak notion`, `ak linear`, `ak slack` (webhook), `gh` CLI, `web_fetch`/`web_search`.

Priority order for new integrations:
1. Google Drive/Meet — meeting transcripts, shared docs (highest impact)
2. Slack read — following channels, extracting updates (needs bot token)
3. Jira — issue management
4. Gmail — processing incoming mail
5. Google Calendar — event context

Google Drive, Gmail, and Calendar share Google Workspace OAuth.
GitHub stays on `gh` CLI. Web content via existing tools. YouTube via `yt-dlp`.

### Self-Extension

The `archie-add-capability` skill orchestrates autonomous capability delivery:

1. Brief discovery — user describes what they want, Archie asks clarifying questions
2. Research — web search, provided URLs, codebase investigation
3. Plan — via `workflow-plan`
4. Self-review plan — via `action-review-plan`
5. Implement — via `workflow-implement`
6. Self-review implementation — via `workflow-review`
7. Iterate — address review issues
8. Ship — branch, commit, PR via `tool-git`

Autonomy model: Archie makes reasonable decisions and flags uncertainty. PR descriptions
include what was built, decisions made, and open questions.

### Communication

Phase 1 is no automated comms. Slack webhook stays for notifications (new PR, etc). All
other communication goes through the outbox as drafts for manual sending.

## Phasing

### Phase 0: Self-Knowledge
- `docs/vision.md` — this document
- Update `README.md` — broaden from dev toolkit to personal AI platform
- Update `CONTRIBUTING.md` — add new conventions
- Update system prompt — complete assistant framing, first-person

### Phase 1: Foundation
- Brain directory structure and conventions
- `docs/brain.md` — brain structure reference
- Mount brain into sessions (config/docker changes)

### Phase 2: Self-Extension
- `archie-add-capability` skill

### Phase 3: Capabilities (delivered via archie-add-capability)
- Brain index and query skill
- Notion ingestion skill
- Memory ingestion (kiro DB → brain)
- Google Drive ingestion (new agent-kit module)
- Meeting transcript processing
- Slack read integration
- Jira integration
- Gmail / Calendar integration
- Reporting (daily/weekly summaries)
- People/relationship management (1:1 prep, contact maintenance)
- Planning (roadmap, issue creation)
- Communication style modelling
- Personality refinement
