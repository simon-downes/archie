# Persona Restructure

## Objective

Restructure the archie repo into a shareable persona/skills library with a polished
installer, while migrating sandbox and session infrastructure to agent-kit. The result:
archie repo is the entrypoint for all users (skills-only through full sandbox experience),
agent-kit provides the runtime tooling, and the two are loosely coupled.

## Context

Archie's skills are valuable beyond the full archie experience — colleagues using Cursor,
Claude Code, and Codex could benefit from the workflow, policy, and action skills. However,
skills currently contain direct `ak` command references that make them archie-specific.
The repo structure (persona buried in a subdirectory, Python packaging for a CLI that
mostly copies files) adds friction to both sharing and development.

Key insights from the design discussion:
- Most people use MCP servers for integrations — `ak` commands are our implementation, not theirs
- Skills should describe intent; `# Available Tools` (a heading in the system prompt) provides tool-specific invocation
- "Brain" stays as the name (distinctive, unambiguous) but skills reference it generically
- tool-issues and tool-slack are routing layers with no logic — fold into workflow skills
- The sandbox is a generic capability (run any agent in a container) — belongs in agent-kit
- The archie repo's value is the content + a great onboarding experience

---

## Requirements

### R1: Skill portability
- MUST remove all direct `ak` command references from skill instruction text
- MUST replace with intent-based language referencing `# Available Tools` for specifics
- MUST preserve archie's execution reliability (agent resolves via tools.md in system prompt)
- SHOULD use the format: refer to `# Available Tools` to signal a heading lookup

### R2: tool-issues and tool-slack elimination
- MUST delete `tool-issues/` and `tool-slack/` skills
- MUST fold graceful degradation rules into workflow-implement and workflow-review
- MUST fold provider dispatch guidance into tools.md (`# Available Tools`)
- MUST fold slack notification as an inline post-action step in workflow-review

### R3: Brain references
- MUST remove direct `ak brain` command references from skill instruction text
- MUST replace with intent-based language: "search your brain for..." / "write to your brain..."
- MUST reference `# Available Tools` for implementation specifics
- MUST keep `ak brain` as the CLI command in agent-kit (unchanged)
- MUST keep brain guidance file describing structure and conventions

### R4: Agent definition and prompt assembly
- MUST create `agents/archie.md` with soul content + `@agent`, `@user`, `@script` directives
- MUST support progressive enhancement (static for Tier 1/2, dynamic for Tier 3)
- Install script MUST strip `@` directives for Tier 1 deployments
- Tier 3 install MUST seed `_archie/soul.md` in brain from `agents/archie.md`
- Entrypoint MUST read `_archie/soul.md` from brain as the live template
- Entrypoint MUST resolve `@agent` (brain/_<agent>/), `@user` (brain/<user>/), `@script` (config-defined)
- Brain's `_archie/soul.md` MUST be evolvable by the agent (self-improvement loop)

### R5: Repo restructure
- MUST move persona subdirectories (skills/, agents/, prompts/, guidance/) to repo root
- MUST add `plugin.json` manifest for marketplace discovery
- MUST update README and CONTRIBUTING to reflect new structure and purpose
- MUST preserve git history for persona/ files (use `git mv`)
- Python packaging removal happens AFTER sandbox migration to agent-kit

### R6: Installer
- MUST provide a polished installer script using Python with inline uv script dependencies (Rich, Click)
- MUST support tiered installation:
  - Tier 1: Skills only → deploy to tool-specific location (kiro, cursor, claude, codex)
  - Tier 2: Skills + agent-kit → tier 1 + install agent-kit via uv
  - Tier 3: Full archie → tier 2 + build sandbox image
- MUST detect existing tool installations and guide the user
- MUST present a clear, attractive interface (not a bare numbered menu)
- MUST be runnable with just `uv run install.py` (single dependency: uv)
- SHOULD support non-interactive mode for CI/scripting (`./install.py --tier cursor`)

### R7: Sandbox/session migration to agent-kit
- MUST move Dockerfile and entrypoint.sh to agent-kit
- MUST move session management (ls, rm, working dirs) to agent-kit
- MUST provide `ak run` command that launches an agent in a container
- MUST be tool-agnostic (not archie-specific — could run cursor CLI, kiro, etc.)
- MUST read persona location from agent-kit config (`persona_dir`)
- MUST preserve current container mount behaviour
- MUST provide `ak build` for building the sandbox image

### R8: Remove Python packaging from archie repo
- MUST remove `src/archie/`, `pyproject.toml`, `uv.lock`, `dist/`
- MUST remove `.venv/`, `tests/` (if only testing CLI)
- MUST update README installation instructions
- MUST clean up `.gitignore`

### R9: Backward compatibility
- MUST work on a branch — no disruption to current main
- MUST be implementable incrementally (content changes first, structural changes after)
- MUST maintain archie's current functionality throughout (old `archie` command works until migration complete)
- MUST do a documentation pass at the end for consistency

---

## Technical Design

### Skill rewrite pattern

All `ak` references become intent + heading reference:

```markdown
# Before
ak brain search "<topic>" --limit 5

# After
Search your brain for prior decisions on this topic (refer to `# Available Tools`).
```

```markdown
# Before
Use `ak project --config` to resolve the project config.

# After
Determine the project's issue tracker and configuration (refer to `# Available Tools`).
```

tools.md (injected into archie's system prompt as `# Available Tools`) already documents
all `ak` commands. No changes needed there — it's the implementation layer that archie's
agent resolves against.

### tool-issues/tool-slack folding

**Into workflow-implement:**
- "Post-start actions" section: update issue status to In Progress if tracker configured, skip silently if not

**Into workflow-review:**
- "Post-PR actions" section: notify slack channel with `<title> <url|#number>`, skip if unconfigured
- Include issue identifier in PR body if plan came from tracker

**Into tools.md:**
- Provider dispatch logic (how to determine Linear vs Jira vs GitHub)
- Provider-specific field mappings and semantics
- Project config lookup pattern

**Graceful degradation** (inline in workflow steps):
- Issue/slack operations are supportive, not blocking
- Skip silently if unconfigured, warn and continue on failure

### Agent definition and prompt assembly

**`agents/archie.md` in the repo** — the seed. Contains the full soul content (identity,
rules, behaviour) followed by `@` directives for dynamic sections:

```markdown
# Archie

[Full soul content — identity, rules, behaviour, communication style]

---

@agent brain.md
@agent memory.md
@script signals
@agent tools.md
@user profile.md
```

**Progressive enhancement by tier:**

| Tier | Install action | Runtime behaviour |
|------|---------------|-------------------|
| Tier 1 (Cursor/Claude) | Copy to tool location, strip `@` directives | Static soul prompt |
| Tier 2 (Kiro, no sandbox) | Copy to `~/.kiro/agents/archie.md` as-is | Static prompt (directives inert) |
| Tier 3 (full) | Copy to `~/.kiro/agents/` AND seed `_archie/soul.md` in brain | Dynamic prompt assembly |

**Tier 3 runtime flow:**
1. Entrypoint reads `_archie/soul.md` from brain (the live template — seeded from `agents/archie.md`)
2. Outputs all non-`@` lines (the soul content)
3. Resolves directives:
   - `@agent <file>` → read `<brain_dir>/_<agent>/<file>`, skip if missing
   - `@user <file>` → read `<brain_dir>/<user>/<file>`, skip if missing
   - `@script <alias>` → look up in agent-kit config, run, include stdout
4. Writes assembled result to `~/.kiro/agents/archie.md` (where kiro reads it)

**Self-improvement:** The brain's `_archie/soul.md` is the live template. Archie can
modify it — add directives, reorder sections, rewrite the soul. Changes take effect
next session. The repo version is just the seed/starting point.

**Agent-kit config (only scripts need config):**
```yaml
prompt:
  scripts:
    signals: "python3 ~/.kiro/prompts/build-signals.py"
```

**Directive resolution rules:**
- `@agent <file>` → `<brain_dir>/_<agent>/<file>` (agent-kit knows agent name from config)
- `@user <file>` → `<brain_dir>/<user>/<file>` (agent-kit knows user from config)
- `@script <alias>` → look up alias in `prompt.scripts` config, run command, include stdout
- All other lines → output as-is
- Missing files / empty script output → skip silently

**Other agents (e.g. "dave"):** Same pattern. `agents/dave.md` in their persona repo,
seeded to `_dave/soul.md` in their brain, resolved by agent-kit using `agent: dave`
from config. Different soul, different directives, same mechanism.

### Installer (install.py)

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["rich", "click"]
# ///
```

Features:
- Detects installed tools (checks for ~/.cursor/, ~/.kiro/, ~/.claude/, etc.)
- Detects agent-kit (`which ak`)
- Detects Docker (`which docker`)
- Presents tier options with clear explanations
- Tier 1: symlinks skills/ to tool-specific location, copies agents/ with directives stripped
- Tier 2: runs `uv tool install agent-kit`, then tier 1 (with directives intact) + configures agent-kit
- Tier 3: tier 2 + seeds brain + `ak build`
- Non-interactive: `./install.py --tier cursor` / `./install.py --tier full`

### Repo structure (final state)

```
archie/
├── skills/                  # shareable — all skills
├── agents/                  # agent definitions (archie.md, subagent configs)
├── prompts/                 # subagent prompts + build-signals.py
├── guidance/                # brain.md (structure docs), tools.md (reference only)
├── plugin.json              # marketplace manifest
├── install.py               # polished tiered installer
├── README.md
├── CONTRIBUTING.md
├── docs/
│   ├── vision.md
│   └── capabilities.md
└── sandbox/                 # TEMPORARY — removed after migration to agent-kit
    ├── Dockerfile
    └── entrypoint.sh
```

Note: `guidance/brain.md` and `guidance/tools.md` are reference copies / seeds.
The live versions are in the brain at `_archie/brain.md` and `_archie/tools.md`.

### Agent-kit additions

- `ak run [--agent <name>]` — launch container with persona + project + brain
- `ak session ls` / `ak session rm [name]` — session management
- `ak build [--quick]` — build sandbox image
- Config additions: `persona_dir`, `sandbox.image_name`, `prompt.scripts`
- Package data: Dockerfile, entrypoint.sh

### Development workflow (post-migration)

```bash
# Persona changes (skills, prompts, guidance):
# Edit files directly. If symlinked by installer, changes are live immediately.
# If copied, re-run: ./install.py --tier kiro

# Agent-kit changes:
cd agent-kit
uv tool install -e --force .    # reinstall locally
ak build                         # rebuild sandbox if needed

# Full test:
ak run                           # launches with local persona + local agent-kit
```



## Milestones

### 1. Fold tool-issues and tool-slack into workflow skills

Approach:
- Read tool-issues graceful degradation rules and provider dispatch pattern
- Read tool-slack message format and skip-if-unconfigured logic
- Add inline post-action sections to workflow-implement and workflow-review
- Provider-specific guidance (Linear/Jira/GitHub field mappings) moves to tools.md
- ⚠️ Keep the language intent-based in the workflow skills — specifics go in tools.md
- ⚠️ Check reference files (LAYERS.md, ISSUE-FORMAT.md) for stale references to deleted skills

Tasks:
- Add "Post-start actions" section to workflow-implement
- Add "Post-PR actions" section to workflow-review
- Move provider dispatch and field mappings to guidance/tools.md
- Delete persona/skills/tool-issues/ and persona/skills/tool-slack/
- Update workflow-plan/references/ISSUE-FORMAT.md (references tool-issues)
- Update action-create-skill/references/LAYERS.md (uses tool-issues as example)
- Update any other skills that reference tool-issues or tool-slack by name

Deliverable: Workflow skills handle issue/slack operations inline without separate tool-* skills.

Verify: `grep -r "tool-issues\|tool-slack" persona/skills/` returns zero matches.

---

### 2. Remove `ak` command references from skills

Approach:
- Replace `ak brain search/reindex/commit` with "search/write to your brain (refer to `# Available Tools`)"
- Replace `ak project --config` with "determine project configuration (refer to `# Available Tools`)"
- Keep language natural and specific — the intent must be unambiguous
- ⚠️ Don't genericise so much that instructions become vague

Tasks:
- Update workflow-plan (3 `ak project` references)
- Update workflow-implement (1 `ak project` reference)
- Update action-brain-ingest (4 `ak brain` references)
- Update action-memory-update (3 `ak brain` references)
- Update action-assimilate (3 `ak brain` references)
- Update action-self-review (2 `ak brain` references)
- Update archie-add-capability (1 `ak notion` reference in example text)

Deliverable: No skill contains a direct `ak` command invocation.

Verify: `grep -rP "\`ak " persona/skills/` returns zero matches.

---

### 3. Create agents/archie.md and update prompt assembly

Approach:
- agents/archie.md becomes the soul content + `@agent`, `@user`, `@script` directives
- This file is the seed for `_archie/soul.md` in the brain (Tier 3 install seeds it)
- Eliminates persona/seeds/ directory — tools.md moves to persona/guidance/ as reference
- Update entrypoint.sh to read `_archie/soul.md` from brain as template, resolve directives,
  write assembled prompt to `~/.kiro/agents/archie.md`
- archie.json `"prompt"` field points to the assembled output path
- Move `BRAIN.md` from brain root to `_archie/brain.md` — installer handles for new installs;
  entrypoint checks both locations for backward compat (prefers `_archie/brain.md`)
- ⚠️ Directive syntax must be simple line-based (bash-parseable, no nesting)
- ⚠️ persona/guidance/LOCAL.md stays as-is (steering for local/non-sandbox mode)
- ⚠️ `@script` aliases defined in agent-kit config (`prompt.scripts`)

**@script contract:**
- Config defines the full command (e.g. `python3 ~/.kiro/prompts/build-signals.py`)
- Script receives no arguments beyond what's in the config command
- Script stdout → included in assembled prompt
- Empty stdout → skip (no blank section)
- Non-zero exit → skip silently (prompt assembles without that section)
- Scripts execute inside the container during entrypoint, with access to brain and agent-kit

Tasks:
- Create persona/agents/archie.md with soul content + directives at end
- Move persona/seeds/tools.md to persona/guidance/tools.md (reference copy)
- Remove persona/seeds/soul.md and persona/seeds/ directory
- Update sandbox/entrypoint.sh:
  - Read `_archie/soul.md` from brain (not from persona dir)
  - Parse `@agent <file>` → read `<brain>/_archie/<file>`
  - Parse `@user <file>` → read `<brain>/<user>/<file>`
  - Parse `@script <alias>` → look up in agent-kit config, run, include stdout
  - Skip missing files and failed/empty scripts silently
  - Write assembled result to `~/.kiro/agents/archie.md`
- Update archie.json prompt path if needed
- Update install logic to seed `_archie/soul.md` in brain from agents/archie.md
- Move `BRAIN.md` to `_archie/brain.md` (installer for new; entrypoint fallback for existing)

Deliverable: agents/archie.md is a standalone agent definition. Entrypoint resolves directives from brain's soul.md to produce the full dynamic prompt.

Verify: Launch archie, `diff` assembled prompt against snapshot of current output. Content should be identical (same sections, same order).

---

### 4. Restructure repo — persona directories to root

Approach:
- Use `git mv` to preserve history
- Move persona/* to repo root (skills/, agents/, prompts/, guidance/ become top-level)
- Add plugin.json and install.py
- Update pyproject.toml force-include paths as a temporary measure (removed in milestone 6)
- The installer strips `@` directive lines when deploying to non-kiro tools
- ⚠️ Relative paths in agent JSON configs and entrypoint will need updating
- ⚠️ sandbox/ stays temporarily until migrated to agent-kit

Tasks:
- `git mv persona/skills skills` (etc. for agents, prompts, guidance)
- Remove empty persona/ directory
- Update pyproject.toml force-include paths to match new locations
- Create plugin.json following the agentskills.io/GitHub Copilot schema:
  ```json
  {
    "name": "archie",
    "description": "...",
    "version": "1.0.0",
    "skills": ["./skills/workflow-plan/", "./skills/policy-general-coding/", ...]
  }
  ```
- Create install.py (Rich/Click, tiered installer) with target paths:
  - kiro: `~/.kiro/skills/`, `~/.kiro/agents/`, `~/.kiro/prompts/`, `~/.kiro/steering/`
  - cursor: `~/.cursor/skills/` (skills only, `@` directives stripped from agents/)
  - claude: `~/.claude/skills/` (skills only)
  - codex: `~/.agents/skills/` (skills only)
  - Tier 3 (full) prints "requires agent-kit — run milestone 5 first" until ak build exists
- Update CONTRIBUTING.md repo layout
- Update README.md for new structure and purpose
- Update relative paths in agent JSON configs
- Update entrypoint.sh to reference new persona paths (skills at root, not persona/skills)
- Update archie CLI config DEFAULT_CONFIG mount paths

Deliverable: Repo root contains skills/, agents/, prompts/, guidance/ directly. Installer handles multi-tool deployment.

Verify: `./install.py --tier kiro` deploys correctly. `archie` still launches and works (via updated paths).

---

### 5. Migrate sandbox and sessions to agent-kit

Approach:
- Add sandbox/ to agent-kit with Dockerfile and entrypoint.sh
- Add `ak run`, `ak session ls`, `ak session rm`, `ak build` commands
- Add `persona_dir` config field pointing to the archie repo checkout
- Entrypoint reads persona from configured location
- Work on a feature branch in agent-kit (coordinate with archie branch)
- ⚠️ Container mounts change — persona read from `persona_dir` config
- ⚠️ `ak run` should be tool-agnostic (configurable agent/tool to launch)
- ⚠️ Gate: `ak run` must fully replicate `archie` behaviour BEFORE milestone 6 removes the archie CLI

**Host vs container execution:**
- Host: `ak run`, `ak build`, `ak session ls/rm`, `ak auth` — orchestration and credentials
- Container: `ak brain`, `ak linear`, `ak jira`, `ak notion`, `ak slack`, `ak google`, `ak project` — tools the agent uses during sessions

**Dev mode (automatic):**
- If the detected project is the archie repo (contains `agent-kit/` + `skills/`), automatically:
  - Mount local `agent-kit/` into container, editable install at start
  - Mount persona from repo rather than installed copy
- No flags needed — "working on archie" implies dev mode
- Only need `ak build` when Dockerfile itself changes (new system packages/tools)

Tasks:
- Add sandbox/ directory to agent-kit (Dockerfile, entrypoint.sh)
- Implement `ak run` command (with automatic dev mode detection)
- Implement `ak session ls` and `ak session rm`
- Implement `ak build` command
- Add `persona_dir` and `sandbox` section to agent-kit config schema
- Add `prompt.scripts` to agent-kit config schema (with DEFAULT_CONFIG defaults)
- Update entrypoint to read persona from config path
- Update container mount logic (dev mode: mount local agent-kit + persona)
- Entrypoint: if local agent-kit mounted, `uv tool install -e` at start
- Test full session lifecycle via `ak run`
- Verify parity: `ak run` and `archie` produce identical behaviour
- Update install.py tier 3 to use `ak build`

Deliverable: `ak run` launches archie identically to current `archie` command. Dev mode auto-detected when working on archie.

Verify: `ak run` starts a session, `ak session ls` shows it, `ak session rm` cleans up. Side-by-side test with `archie` command confirms identical behaviour. Edit agent-kit code → `ak run` (from archie project) → changes are live without push/rebuild.

---

### 6. Remove Python packaging from archie repo

Approach:
- Sandbox and sessions now live in agent-kit — archie has no Python runtime code
- Remove all Python packaging artifacts
- Update installer tier 3 to use `ak build` instead of `archie build`
- ⚠️ Ensure install.py still works (it uses inline uv deps, not the project's pyproject.toml)

Tasks:
- Remove src/archie/ directory
- Remove pyproject.toml, uv.lock, dist/
- Remove .venv/, tests/
- Remove sandbox/ directory (now in agent-kit)
- Update install.py tier 3 to call `ak build`
- Clean up .gitignore

Deliverable: Repo contains no Python runtime code or packaging. Only install.py (standalone script).

Verify: No pyproject.toml. `uv run install.py --tier full` works end-to-end.

---

### 7. Documentation pass

Approach:
- Ensure all docs reflect the new architecture
- Remove docs that are now agent-kit's responsibility
- Add clear explanation of the archie ↔ agent-kit relationship
- ⚠️ Don't leave stale references to `archie` CLI, `persona/` prefix, or old structure
- ⚠️ Getting Started doc is critical — covers prerequisites (including kiro-cli), credentials,
  brain init, first run, verification. This is the primary onboarding path.

Tasks:
- Update README.md (tiers, installation, structure, relationship to agent-kit)
- Update CONTRIBUTING.md (repo layout, dev workflow, how to add skills)
- Update/create docs/getting-started.md (prerequisites, credentials, first run, verification)
- Update/remove docs/ as needed (sessions → agent-kit, vision updated)
- Document that non-kiro users need `# Available Tools` in their system prompt/rules
- Verify plugin.json is complete and accurate
- Read through every doc, confirm no stale references

Deliverable: All documentation accurately reflects the new architecture.

Verify: `grep -r "archie install\|archie build\|persona/" *.md docs/` returns no stale references.
