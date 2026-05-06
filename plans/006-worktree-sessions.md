# Archie — Git Worktree Sessions

## Objective

Enable multiple concurrent project sessions by giving each session its own git worktree.
Remove the single-session-per-project restriction. Worktrees persist until explicitly
removed, with guardrails to prevent losing uncommitted or unpushed changes.

## Requirements

### Worktree Creation

- MUST create a worktree for each new project session (when the project has a git repo)
  - AC: `archie` in a project dir creates a worktree with a short hash name (e.g. `a3f9c`)
  - AC: `archie --session <name>` creates (or reattaches to) a named worktree
  - AC: Worktrees stored at `~/.archie/worktrees/<project>/<session>/`
  - AC: Branch created as `archie/<session>` based on the current HEAD of the main checkout
  - AC: Projects without a `.git` directory use direct mount (current behaviour, no worktree)
  - AC: General sessions are unchanged (no worktree)

### Multi-Session Support

- MUST remove the single-session-per-project restriction
  - AC: Multiple containers can run against the same project simultaneously
  - AC: Each gets its own worktree and container name (`archie-shell-<project>-<session>`)
  - AC: Reusing a session name with an active container still errors (container name conflict)
  - AC: Reusing a session name with no active container reattaches to the existing worktree

### Container Mounts

- MUST mount the worktree as the container's working directory
  - AC: Worktree mounted rw at the container path where the project would normally appear
  - AC: Main project's `.git/` mounted rw at its expected path (worktree needs write access to objects/refs)
  - AC: Main project source files are NOT mounted (only `.git/`)
  - AC: Container working directory (`-w`) set to the worktree mount path

### Worktree Persistence and Safety

- MUST NOT auto-remove worktrees
  - AC: Session exit (graceful or crash) leaves the worktree on disk
  - AC: Container is removed (`--rm`) but worktree persists
- MUST provide explicit worktree management commands
  - AC: `archie worktree ls` — lists worktrees per project, shows status (clean/dirty/unpushed, active session or orphaned)
  - AC: `archie worktree rm <project> <session>` — removes worktree only if clean and fully pushed
  - AC: `archie worktree rm <project> <session> --force` — removes regardless of state
  - AC: Status check: `git status --porcelain` for dirty, `git log @{upstream}..HEAD` for unpushed

### Project Resolution from Worktrees

- MUST update `ak project` to resolve correctly when cwd is a worktree
  - AC: Reads the worktree's `.git` file → follows `gitdir:` path → derives main repo location
  - AC: Resolves project name from main repo path against `project_dir`
  - AC: All downstream (brain, issues config, slack) works identically to main checkout

## Technical Design

### Worktree Layout

```
~/.archie/worktrees/
└── my-project/
    ├── a3f9c/          # anonymous session worktree
    │   ├── .git        # file: gitdir: /home/simon/dev/my-project/.git/worktrees/a3f9c
    │   └── <source>
    └── fix-auth/       # named session worktree
        ├── .git
        └── <source>
```

### Worktree Creation (host-side, in docker.py)

When launching a project session with git:

```python
worktree_dir = ARCHIE_HOME / "worktrees" / project.name / session_name
if not worktree_dir.exists():
    subprocess.run([
        "git", "-C", str(project), "worktree", "add",
        str(worktree_dir), "-b", f"archie/{session_name}"
    ], check=True)
```

If the worktree already exists (reattach), skip creation.

### Container Mount Strategy

```python
# Mount worktree as the project directory
args.extend(["-v", f"{worktree_dir}:{container_project}"])

# Mount main repo .git for shared object store (rw — worktree writes objects/refs)
args.extend(["-v", f"{project}/.git:{container_project}/.git-main"])
```

Wait — the worktree's `.git` file contains an absolute host path. Inside the container
that path must resolve. Simplest approach: mount the main `.git/` at the same absolute
path it has on the host:

```python
host_git_dir = project / ".git"
args.extend(["-v", f"{host_git_dir}:{str(host_git_dir)}"])
```

The worktree's `.git` file already points to the host path, which now resolves inside
the container too.

### Session Naming

- No `--session` flag: generate 5-char hex hash (same as current general session pattern)
- `--session <name>`: use as-is (sanitized for filesystem/docker)
- Container name: `archie-shell-<project>-<session>`

### Removing the Single-Session Restriction

Current code in `run_container()` checks for existing container by name. With session
names in the container name, each session is unique. The check remains (prevents
duplicate containers with the same name) but no longer blocks multiple project sessions.

### ak project Worktree Resolution

Add a resolution step before the existing `project_dir` check:

```python
def _resolve_from_worktree(cwd: Path) -> tuple[str, str] | None:
    """If cwd is inside a worktree, follow .git file back to main repo."""
    git_file = _find_git_file(cwd)
    if git_file and git_file.is_file():
        content = git_file.read_text().strip()
        if content.startswith("gitdir:"):
            # gitdir: /home/simon/dev/my-project/.git/worktrees/a3f9c
            git_dir = Path(content.split(":", 1)[1].strip())
            # Walk up: .git/worktrees/<name> → .git → project root
            main_repo = git_dir.parent.parent.parent
            return main_repo.name, str(main_repo)
    return None
```

This runs before the `project_dir` check. If it resolves, use that project name.
The git remote is still read from the worktree (it shares refs with main repo).

## Milestones

1. **Worktree creation and mount logic**
   Approach:
   - Add `_create_or_reuse_worktree(project: Path, session: str) -> Path` to `docker.py`
   - Modify `run_container()`: if project has `.git`, create worktree, mount it instead
     of the project directory. Mount main `.git/` at its host path.
   - Generate session name (hash or from `--session` flag).
   - Update container naming to include session: `archie-shell-<project>-<session>`.
   - Remove the "already running" error for project sessions (keep it for same session name).
   Deliverable: Multiple project sessions can run concurrently, each in its own worktree.
   Verify: Launch two sessions for the same project, verify separate worktrees and branches.

2. **Worktree management commands**
   Approach:
   - Add `archie worktree` command group to `cli.py` with `ls` and `rm` subcommands.
   - `ls`: scan `~/.archie/worktrees/`, for each run `git status --porcelain` and
     `git log @{upstream}..HEAD`, cross-reference with running containers.
   - `rm`: check clean + pushed, refuse unless `--force`. Run `git worktree remove`.
   Deliverable: `archie worktree ls` shows all worktrees with status.
   Verify: Create worktrees, dirty one, verify `ls` shows correct status, verify `rm` refuses.

3. **Update ak project for worktree resolution**
   Approach:
   - Add worktree detection to `resolve_project()` in agent-kit `project.py`.
   - If cwd contains a `.git` file (not directory), parse `gitdir:` line, resolve main repo.
   - Derive project name from main repo path against `project_dir`.
   - Org/remote still resolved from git remote (shared between worktree and main repo).
   Deliverable: `ak project` returns correct project info when run inside a worktree.
   Verify: Run `ak project` from inside a worktree, verify name/org/path match main project.

4. **Update CLI flags and session prompt**
   Approach:
   - Add `--session` option to `main()` in `cli.py` (already exists for general, extend to project).
   - Update `display_header` to show session name.
   Deliverable: `archie --session fix-auth` creates/reattaches named worktree session.
   Verify: Named session creates worktree, second invocation reattaches.
