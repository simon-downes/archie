# Agent-Kit — Project Configuration

## Objective

Replace the brain-based project config with a declarative `~/.agent-kit/projects.yaml`
file. Project resolution (`ak project`) becomes a single call that returns name, org,
path, and resolved config (issues, slack) — no `--config` flag, no brain dependency.

## Requirements

### Project Config File

- MUST support `~/.agent-kit/projects.yaml` with hierarchical resolution
  - AC: `defaults` key provides base values for all projects
  - AC: `<org>` key overrides defaults for all repos in that org
  - AC: `<org>/<repo>` key overrides org-level for a specific repo
  - AC: `<org>/<prefix>-*` glob patterns match repo names by prefix
  - AC: Resolution order (most specific wins): exact repo → glob → org → defaults
  - AC: Each level merges over the one above (only specified fields override)

### Org Resolution from Git Remote

- MUST extract org from git remote URL
  - AC: SSH format `git@github.com:my-org/my-repo.git` → org: `my-org`, name: `my-repo`
  - AC: HTTPS format `https://github.com/my-org/my-repo.git` → org: `my-org`, name: `my-repo`
  - AC: No remote → org: `null`, name from project_dir or cwd (existing behaviour)

### Unified `ak project` Output

- MUST return all project info in a single call (no `--config` flag)
  - AC: Output includes: `name`, `org`, `path`, `issues`, `slack`
  - AC: `issues` is `null` or `{provider, project?}` based on resolved config
  - AC: `slack` is `null` or the resolved value
  - AC: `path` is the absolute path to the project directory
  - AC: Projects with no remote and no matching config return defaults

### Issues Provider Schema

- MUST support provider-specific config:
  - AC: `provider: github` — no additional fields needed (org/repo from remote)
  - AC: `provider: linear` — requires `project` field (team/project key)
  - AC: `provider: jira` — requires `project` field (project key)
  - AC: `issues: null` — issues disabled for this project

### Remove Brain Project Config

- MUST remove `--config` flag from `ak project`
- MUST remove `find_project` brain lookup from project resolution
- SHOULD remove brain project files if they exist (or leave for manual cleanup)

## Technical Design

### Config File Format

```yaml
# ~/.agent-kit/projects.yaml
defaults:
  issues: null
  slack: null

my-org:
  issues:
    provider: linear
    project: PLAT
  slack: "#platform"

my-personal-org:
  issues:
    provider: github
  slack: null

my-org/special-repo:
  issues:
    provider: github

my-org/infra-*:
  issues:
    provider: linear
    project: INFRA
```

### Resolution Logic

```python
def resolve_project_config(org: str | None, name: str, config: dict) -> dict:
    """Resolve project config with hierarchical merge."""
    result = config.get("defaults") or {}

    if org:
        org_config = config.get(org)
        if org_config:
            result = {**result, **org_config}

        # Glob patterns: <org>/<pattern>
        for key, value in config.items():
            if "/" in key and "*" in key:
                pattern_org, pattern_name = key.split("/", 1)
                if pattern_org == org and fnmatch(name, pattern_name):
                    result = {**result, **value}

        # Exact match
        exact = config.get(f"{org}/{name}")
        if exact:
            result = {**result, **exact}

    return result
```

### Org Extraction

Extend `resolve_project_name` to also return org and remote repo name. Parse the git
remote URL to extract the org and repo (for config matching only). The project `name`
in output is always the local directory name — the remote org/repo is used solely for
resolving config in `projects.yaml`.

```
git@github.com:my-org/my-repo.git     → org=my-org, remote_repo=my-repo
https://github.com/my-org/my-repo.git → org=my-org, remote_repo=my-repo
```

Config matching uses `org/remote_repo` (not the local directory name) so that projects
cloned to non-standard directory names still resolve correctly.

### Output Format

```json
{
  "name": "my-repo",
  "org": "my-org",
  "path": "/home/simon/dev/my-repo",
  "source": "git@github.com:my-org/my-repo.git",
  "issues": {"provider": "linear", "project": "PLAT"},
  "slack": "#platform"
}
```

When there's no remote:

```json
{
  "name": "my-project",
  "org": null,
  "path": "/home/simon/dev/my-project",
  "source": "local",
  "issues": null,
  "slack": null
}
```

### Backward Compatibility

The `--config` flag is removed. Brain project config files are left in place but no
longer read by `ak project`. The `source` field is retained but simplified: either the
git remote URL or `"local"` (when detected from project_dir/cwd with no remote).

## Milestones

1. **Extract org from git remote**
   Approach:
   - Modify `resolve_project_name()` in `project.py` to return `(name, org, source)`.
   - Parse remote URL: split on `:` (SSH) or `/` (HTTPS) to get org and repo.
   - Update callers (the click command, archie's `config.py` if it calls this).
   Deliverable: `ak project` output includes `org` field.
   Verify: Test with SSH and HTTPS remotes, and with no remote.

2. **Add projects.yaml config loading and resolution**
   Approach:
   - New function `load_projects_config()` reads `~/.agent-kit/projects.yaml`.
   - New function `resolve_project_config(org, name, projects_config)` implements
     hierarchical merge: defaults → org → glob → exact.
   - Glob matching via `fnmatch` on the repo name portion.
   - Returns dict with `issues` and `slack` keys.
   Deliverable: Config resolution works with all specificity levels.
   Verify: Unit tests covering defaults, org override, glob, exact match, and no-match.

3. **Unify `ak project` output and remove brain dependency**
   Approach:
   - Rewrite the `project` click command to call both resolution functions.
   - Output: `name`, `org`, `path`, `issues`, `slack`.
   - Remove `--config` flag and `find_project` brain import.
   - `path` is resolved from `project_dir / name` (if detected via project_dir) or cwd.
   Deliverable: `ak project` returns complete project info in one call.
   Verify: Manual test in a project directory; verify output matches expected config.

4. **Update archie and guidance**
   Approach:
   - Update archie's `config.py` if it references the old `resolve_project_name` signature.
   - Update tool-issues skill to use new `ak project` output format.
   - Update any guidance that references `ak project --config`.
   Deliverable: All references updated, no broken integrations.
   Verify: `archie status` works; skill references are correct.
