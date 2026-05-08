# Archie — Named Sessions with Worktrees

## Objective

Add named sessions with git worktree backing. Named sessions are resumable — the
worktree persists between container runs, enabling long-running work across multiple
invocations. Unnamed sessions remain ephemeral (current behaviour).

## Concepts

- **Session** — a named, resumable workspace. The worktree is the durable state;
  the container is the ephemeral runtime.
- **Unnamed session** — current behaviour. Anonymous container, project mounted
  directly, no worktree. Multiple can run against the same project (deconflicting
  is the user's problem).
- **Named session without git** — just a stable container name. No worktree, no
  persistence beyond the container lifetime. Errors if already running.

## Requirements

### Session Creation and Resume

- `archie session <name>` creates or resumes a named session
  - AC: If project has `.git`, creates worktree at `~/.archie/worktrees/<project>/<name>/`
  - AC: Worktree created on branch `archie/<name>` (new branch from HEAD, or existing branch if it already exists)
  - AC: If worktree already exists, reattaches (mounts existing worktree)
  - AC: Enables reviewing existing branches — `archie session feature-x` checks out `archie/feature-x` if it exists
  - AC: If container with session name is already running, errors
  - AC: Projects without `.git` get a stable container name only (no worktree)
  - AC: General sessions (outside project dir) get a stable container name only

### Session Resolution

- Session name resolves based on context:
  - AC: In a project dir → scoped to that project (create or resume)
  - AC: Outside any project → search all worktrees, error if ambiguous, resume if unique
  - AC: Qualified name (`project/session`) works from anywhere

### Container Mounts (named session with worktree)

- MUST mount the worktree as the container's working directory
  - AC: Worktree mounted rw at the container path where the project would normally appear
  - AC: Main project's `.git/` mounted at its host path (worktree's `gitdir:` resolves)
  - AC: Container working directory (`-w`) set to the worktree mount path
  - AC: Assumption: project lives under `$HOME` (host path = container path since
    container username matches host username)

### Unnamed Sessions (no change)

- `archie` with no subcommand behaves exactly as today
  - AC: Project directory mounted directly
  - AC: Container named `archie-{tool_name}-<project>` (or `archie-general-<hash>`)
  - AC: Multiple unnamed sessions can run against the same project

### Session Cleanup

- `archie session --rm <name>` removes a named session
  - AC: Cannot remove if a container is running for that session (error)
  - AC: Removes immediately if worktree is clean and fully pushed (or no worktree)
  - AC: Prompts for confirmation if uncommitted changes or unpushed commits exist
  - AC: `archie session --rm -f <name>` forces removal regardless of state
  - AC: Non-interactive (piped/CI): refuses dirty removal unless `-f` is passed
  - AC: Runs `git worktree remove` to clean up

### Status

- `archie status` shows all sessions
  - AC: Running containers (active sessions — named and unnamed)
  - AC: Worktrees with no container (inactive named sessions)
  - AC: Git state for worktrees: ahead/behind, modified files count
  - AC: Example output:
    ```
    Sessions:
      archie  fix-auth   ● running    3 ahead, clean
      archie  refactor   ○ inactive   1 ahead, 2 modified
      tillo   (unnamed)  ● running    —
      general research   ● running    —
    ```

### Project Resolution from Worktrees

- MUST update `ak project` to resolve correctly when cwd is a worktree
  - AC: Reads `.git` file → follows `gitdir:` path → derives main repo location
  - AC: Resolves project name from main repo path
  - AC: All downstream (brain, issues config, slack) works identically

### CLI Changes

- Remove existing `--session` flag from the main command
- Add `session` subcommand

## Technical Design

### Current State

- `run_container()` in `docker.py` handles project and general sessions
- Container naming: `archie-{tool_name}-{project}` for project, `archie-general-{suffix}` for general
- `tool_name` defaults to `"shell"` — only differs if a dynamic tool command is configured
- `--session` flag exists on main command, applies only to general sessions (being removed)
- `resolve_project()` in `config.py` resolves from cwd relative to `project_dir`
- Brain mount is always read-write

### Worktree Layout

```
~/.archie/worktrees/
└── my-project/
    ├── fix-auth/       # named session
    │   ├── .git        # file: gitdir: /home/simon/dev/my-project/.git/worktrees/fix-auth
    │   └── <source>
    └── refactor/       # another named session
        ├── .git
        └── <source>
```

### Session Command (cli.py)

```python
@main.command()
@click.argument("name")
@click.option("--rm", "remove", is_flag=True, help="Remove an inactive session")
@click.option("-f", "force", is_flag=True, help="Force removal even if dirty/unpushed")
def session(name: str, remove: bool, force: bool) -> None:
    if remove:
        _remove_session(name, force=force)
    else:
        _start_session(name)
```

### Worktree Creation (docker.py)

```python
def _create_or_reuse_worktree(project: Path, session_name: str) -> Path:
    worktree_dir = ARCHIE_HOME / "worktrees" / project.name / session_name
    if worktree_dir.exists():
        return worktree_dir  # reattach

    branch = f"archie/{session_name}"
    # Check if branch already exists
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--verify", branch],
        capture_output=True,
    )
    if result.returncode == 0:
        # Branch exists — create worktree using it
        subprocess.run(
            ["git", "-C", str(project), "worktree", "add", str(worktree_dir), branch],
            check=True,
        )
    else:
        # New branch from HEAD
        subprocess.run(
            ["git", "-C", str(project), "worktree", "add", str(worktree_dir), "-b", branch],
            check=True,
        )
    return worktree_dir
```

### Container Mount Strategy

```python
# Named session with worktree
args.extend(["-v", f"{worktree_dir}:{container_project}", "-w", container_project])

# Mount main .git at its host path so worktree's gitdir: reference resolves
host_git_dir = project / ".git"
args.extend(["-v", f"{host_git_dir}:{str(host_git_dir)}"])
```

Note: this relies on project living under `$HOME` and the container username matching
the host username (both true in our setup — container user is `HOST_USERNAME`).

### Session Resolution Logic

```python
def _resolve_session(name: str, project: Path | None) -> tuple[Path | None, Path | None]:
    """Resolve session name to (project_path, worktree_dir | None).

    Returns (project, None) for non-git or general sessions.
    """
    # Qualified name: "project/session"
    if "/" in name:
        proj_name, session_name = name.split("/", 1)
        proj_path = project_dir / proj_name
        worktree = ARCHIE_HOME / "worktrees" / proj_name / session_name
        return proj_path, worktree if worktree.exists() else None

    # In a project dir — scope to this project
    if project:
        worktree = ARCHIE_HOME / "worktrees" / project.name / name
        return project, worktree if worktree.exists() else None

    # Outside project — search all worktrees
    matches = list((ARCHIE_HOME / "worktrees").glob(f"*/{name}"))
    if len(matches) == 1:
        proj_name = matches[0].parent.name
        return project_dir / proj_name, matches[0]
    elif len(matches) > 1:
        raise click.UsageError(
            f"Ambiguous session '{name}' — exists in: {[m.parent.name for m in matches]}"
        )
    return None, None  # new general session
```

### Container Naming

- Named project session: `archie-{tool_name}-<project>-<session>`
- Unnamed project session: `archie-{tool_name}-<project>` (current)
- Named general session: `archie-general-<session>`
- Unnamed general session: `archie-general-<hash>` (current)

### Session Removal Logic

```python
def _remove_session(name: str, force: bool) -> None:
    # Resolve session
    project, worktree = _resolve_session(name, resolve_project())

    # Check for running container
    container_name = _session_container_name(project, name)
    if _docker_output("ps", "-q", "--filter", f"name=^/{container_name}$"):
        print_error("Cannot remove — session is running")
        sys.exit(1)

    if not worktree or not worktree.exists():
        print_info("No worktree to remove")
        return

    # Check dirty/unpushed state
    dirty = _worktree_is_dirty(worktree)
    if dirty and not force:
        if not sys.stdin.isatty():
            print_error("Worktree has uncommitted/unpushed changes. Use -f to force.")
            sys.exit(1)
        reply = input(f"  Session has {dirty}. Remove anyway? [y/N] ")
        if reply.strip().lower() != "y":
            sys.exit(0)

    subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], check=True)
```

### ak project Worktree Resolution (agent-kit/project.py)

```python
def _resolve_from_worktree(cwd: Path) -> tuple[str, str] | None:
    """If cwd is inside a worktree, follow .git file back to main repo."""
    git_path = _find_git_marker(cwd)
    if git_path and git_path.is_file():
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            git_dir = Path(content.split(":", 1)[1].strip())
            # .git/worktrees/<name> → .git → project root
            main_repo = git_dir.parent.parent.parent
            return main_repo.name, str(main_repo)
    return None
```

Runs before the existing `project_dir` resolution in `resolve_project()`.

### Status Display

Merge two data sources:
1. Running containers (`docker ps --filter name=archie-`)
2. Worktree directories (`~/.archie/worktrees/`)

For each worktree, run:
- `git -C <worktree> status --porcelain` → modified count
- `git -C <worktree> log @{upstream}..HEAD 2>/dev/null` → ahead count

## Milestones

1. **Session command and worktree creation**
   Approach:
   - Add `archie session <name>` command to `cli.py`
   - Remove `--session` flag from main command
   - Add `_create_or_reuse_worktree()` to `docker.py`
   - Modify `run_container()` to accept a worktree path and mount accordingly
   - Implement session resolution logic (project-scoped, qualified, search)
   - Update container naming to include session suffix for named sessions
   Deliverable: `archie session fix-auth` creates worktree, launches container, reattaches on second run.
   Verify: Create session, exit, resume. Verify worktree persists. Verify two named sessions coexist.

2. **ak project worktree resolution**
   Approach:
   - Add `.git` file detection to agent-kit `project.py`
   - Parse `gitdir:` line, walk up to main repo
   - Run before existing `project_dir` resolution
   Deliverable: `ak project` works correctly inside a worktree container.
   Verify: Run `ak project` from worktree, confirm project name matches.

3. **Status and cleanup**
   Approach:
   - Update `archie status` to show sessions (running containers + inactive worktrees with git state)
   - Implement `archie session --rm <name>` with safety checks (running container, dirty/unpushed, force flag)
   - Non-interactive: refuse dirty removal unless `-f`
   Deliverable: `archie status` shows full session picture. Cleanup works safely.
   Verify: Create sessions, stop some, verify status output. Remove clean session. Verify prompt on dirty. Verify `-f` forces. Verify refusal when container running.

4. **Documentation**
   Approach:
   - Rewrite `docs/sessions.md` — named sessions, worktrees, resume, cleanup
   - Update `README.md` commands table
   Deliverable: Documentation reflects new session model.
   Verify: Commands table matches implementation. Sessions doc covers all flows.
