# Config Propagation & Dynamic Prompt Assembly

## Objective

Enable self-improvement foundations by implementing dynamic system prompt assembly from
brain-resident files, and fix config propagation so new defaults reach existing
installations without manual intervention. All prompt sources are evolvable — the archie
repo provides seeds, the brain holds the live versions.

## Requirements

### Dynamic Prompt Assembly

- MUST assemble the system prompt at session start from brain-resident sources
  - AC: Entrypoint script concatenates sources into the final prompt file before kiro-cli
    launches
  - AC: Agent config points to the assembled file
  - AC: Missing files are skipped gracefully (session still starts)
  - AC: Paths resolved from agent-kit config (no env vars beyond `ARCHIE_TITLE`)
  - AC: Assembly order:
    1. Soul (`_archie/soul.md`) — identity, personality, rules, opinions
    2. Brain guide (`BRAIN.md`) — knowledge structure, conventions, interaction patterns
    3. Memory (`_archie/memory.md`) — consolidated durable observations
    4. Signals (computed from `_archie/signals.yaml`) — recent corrections/failures
    5. Tools (`_archie/tools.md`) — available tools and usage patterns
    6. User profile (`<user>/profile.md`) — who the user is

### Seed Deployment

- MUST provide seed files in the archie repo that are copied to the brain on install
  - AC: `persona/seeds/soul.md` → `brain/_archie/soul.md` (only if not present)
  - AC: `persona/seeds/tools.md` → `brain/_archie/tools.md` (only if not present)
  - AC: Seeds are never overwritten — brain versions are the live, evolvable copies
  - AC: `archie install` handles seed deployment

### Signal Processing

- MUST compute signal injection as part of prompt assembly
  - AC: Entrypoint runs signal filtering (recent corrections/failures, pattern detection)
  - AC: Filters by type (correction, failure) and recency (most recent N)
  - AC: No project filtering — signals are system-wide
  - AC: No promotion mechanism — simple recency window
  - AC: agentSpawn hook removed (signals now handled by entrypoint)

### Config Propagation

- MUST merge new defaults into existing config during `archie install`
  - AC: New keys from `DEFAULT_CONFIG` are added to existing config
  - AC: Existing user overrides are preserved
  - AC: Removed defaults are NOT removed from user config (no destructive changes)
  - AC: Deep merge (nested dicts merged recursively, scalars/lists preserved if present)

### No Static Base Prompt

- MUST NOT have a static prompt file that Archie cannot modify
  - AC: All prompt content lives in brain-resident files
  - AC: Critical rules (countering kiro biases) live in `_archie/soul.md`
  - AC: The archie repo contains only seeds, not the live prompt

## Technical Design

### Entrypoint Assembly

Extend `sandbox/entrypoint.sh`:

```bash
#!/bin/bash
# Set terminal title
if [ -n "$ARCHIE_TITLE" ]; then
    printf '\033]0;%s\007' "$ARCHIE_TITLE"
fi

# Resolve paths from agent-kit config
ak_config="$HOME/.agent-kit/config.yaml"
brain_dir=$(yq -r '.brain.dir // "~/.archie/brain"' "$ak_config")
brain_dir="${brain_dir/#\~/$HOME}"
agent_name=$(yq -r '.agent // "archie"' "$ak_config")
user_name=$(yq -r '.user // "simon"' "$ak_config")
agent_dir="$brain_dir/_${agent_name}"
user_dir="$brain_dir/${user_name}"
prompt_out="$HOME/.kiro/prompts/archie.prompt.md"

# Assemble system prompt (writes to the path agent config already references)
> "$prompt_out"

for file in \
    "$agent_dir/soul.md" \
    "$brain_dir/BRAIN.md" \
    "$agent_dir/memory.md"; do
    [ -f "$file" ] && cat "$file" >> "$prompt_out" && printf '\n\n' >> "$prompt_out"
done

# Computed signals
if [ -f "$agent_dir/signals.yaml" ]; then
    signals=$(python3 "$HOME/.kiro/prompts/build-signals.py" "$agent_dir/signals.yaml")
    [ -n "$signals" ] && echo "$signals" >> "$prompt_out" && printf '\n\n' >> "$prompt_out"
fi

for file in \
    "$agent_dir/tools.md" \
    "$user_dir/profile.md"; do
    [ -f "$file" ] && cat "$file" >> "$prompt_out" && printf '\n\n' >> "$prompt_out"
done

exec "$@"
```

### Signal Builder (`build-signals.py`)

Extracted from current `session-digest.py`. Same logic:
- Parse signals.yaml (no PyYAML dependency)
- Filter to `correction` and `failure` types
- Take most recent 7
- Detect category patterns (2+ occurrences)
- Output markdown section to stdout

Deployed alongside prompts in `persona/prompts/build-signals.py`.

### Config Propagation

Update `install()` in `config.py`:

```python
def install() -> None:
    # ... existing persona deployment ...

    if CONFIG_PATH.exists():
        existing = load_config()
        merged = _deep_merge(DEFAULT_CONFIG, existing)
        _write_config(merged)
    else:
        _write_config(DEFAULT_CONFIG)
```

`_deep_merge(base, override)` — base provides defaults, override (existing user config)
takes precedence. New keys from base fill gaps.

### Seed Deployment

During `archie install`:
```python
# Deploy seeds to brain (only if not present)
brain_dir = _resolve_brain_dir()
seeds = {
    "persona/seeds/soul.md": brain_dir / "_archie" / "soul.md",
    "persona/seeds/tools.md": brain_dir / "_archie" / "tools.md",
}
for src, dest in seeds.items():
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
```

### What Lives Where

| Content | Repo (seeds) | Brain (live) | In prompt |
|---------|-------------|--------------|-----------|
| Soul (identity, rules, personality) | `persona/seeds/soul.md` | `_archie/soul.md` | Yes |
| Tools guidance | `persona/seeds/tools.md` | `_archie/tools.md` | Yes |
| Brain conventions | agent-kit templates | `BRAIN.md` (root) | Yes |
| Memory | — | `_archie/memory.md` | Yes |
| Signals | — | `_archie/signals.yaml` | Yes (computed) |
| User profile | — | `<user>/profile.md` | Yes |
| Skills | `persona/skills/` | — | No (discoverable) |
| Agent configs | `persona/agents/` | — | No (kiro-cli) |
| Hooks | `persona/hooks/` | — | No (removed) |

## Milestones

1. **Config propagation**
   Approach:
   - Add `_deep_merge()` to `config.py` (base provides defaults, override wins)
   - Update `install()` to merge when config exists
   Deliverable: `archie install` adds new defaults to existing config.
   Verify: Add a test key to DEFAULT_CONFIG, run install, verify it appears while
   existing values are preserved.

2. **Create seed files**
   Approach:
   - Create `persona/seeds/soul.md` — the entire current `archie.prompt.md` becomes the
     soul. This includes: identity, personality, critical rules, interpreting user intent,
     subagent usage, planning workflow. Everything is evolvable.
   - Create `persona/seeds/tools.md` — current `persona/guidance/TOOLS.md` content
   - Create `persona/prompts/build-signals.py` — extract logic from `session-digest.py`
   Deliverable: Seed files exist and cover all current prompt/guidance content.
   Verify: Diff combined seeds against current prompt + guidance — nothing lost.

3. **Implement entrypoint prompt assembly**
   Approach:
   - Extend `sandbox/entrypoint.sh` with assembly logic
   - Resolve paths from `~/.agent-kit/config.yaml` using `yq` (user, agent, brain.dir)
   - Write assembled prompt to `~/.kiro/prompts/archie.prompt.md` — this is intentionally
     the same path the agent config references, so no agent config changes needed
   - Deploy `build-signals.py` alongside prompts (reaches container via existing
     `~/.archie/persona/prompts` → `~/.kiro/prompts` mount)
   - Ensure `yq` is available in the sandbox image (already installed)
   Deliverable: Entrypoint assembles prompt from brain sources before kiro-cli starts.
   Verify: Start a session, check assembled prompt contains all expected sections.

4. **Update install and deploy flow**
   Approach:
   - Add seed deployment to `install()` (copy to brain if not present)
   - Remove `session-digest.py` from `persona/hooks/`
   - Remove agentSpawn hook from `archie.json` agent config
   - Remove `persona/guidance/TOOLS.md` and `persona/guidance/BRAIN.md` (now brain-resident)
   - Remove `persona/prompts/archie.prompt.md` (replaced by entrypoint assembly —
     the assembled file is written to the same path the agent config references)
   Deliverable: Fresh install + session start works end-to-end with assembled prompt.
   Verify: `archie install` on a clean system, then start a session — prompt contains
   all expected sections from brain sources.
