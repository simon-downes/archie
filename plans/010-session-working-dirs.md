# Archie — Session Working Directories

## Objective

Evolve the named session model to use isolated working directories with cloned repos.
Enable multiple concurrent unnamed project sessions. Provide a host-mounted working
directory for general sessions (solving the data-passing problem). Replace worktree
backing with full clones.

## Background

Plan 006 implemented named sessions with single-repo worktree backing. This plan
replaces worktrees with clones to handle multi-repo projects and simplify the model.

## Session Model

| Session type | Working directory | Container mount | Lifecycle |
|---|---|---|---|
| Unnamed project | None (project dir mounted directly) | `~/dev/<project>` → same path in container | Container removed on exit |
| Named project | `~/.archie/sessions/<project>/<name>/` | Mounted at container's project path (e.g. `~/dev/<project>`) | Persists until `--rm` |
| Unnamed general | `~/.archie/sessions/general/<hash>/` | Mounted at a fixed path (e.g. `~/workspace/`) | Removed on exit |
| Named general | `~/.archie/sessions/general/<name>/` | Mounted at a fixed path (e.g. `~/workspace/`) | Persists until `--rm` |

## Design Decisions

### Clone strategy

- `git clone --single-branch <remote-url>` — full history, default branch only
- Remote URL read from the existing local repo (`git remote get-url origin`)
- No branching at clone time — agent/skill creates branches as needed
- Additional branches fetched on demand

### Sub-repo detection

- Scan the project directory one level deep for immediate subdirectories containing `.git/`
- Clone each sub-repo into the same relative path within the session directory
- Sub-repos that are gitignored in the parent (e.g. `agent-kit` in archie) remain
  gitignored in the clone — no interference

### Working directory layout

The session directory mirrors the host project structure:

```
~/.archie/sessions/archie/fix-auth/
├── .git/                 ← clone of archie
├── src/
├── persona/
├── agent-kit/            ← clone of agent-kit (sub-repo)
│   ├── .git/
│   └── src/
└── ...
```

### Container mount strategy

Named project sessions mount the session directory at the same container path as
the project would normally appear:

```
Host:      ~/.archie/sessions/archie/fix-auth/
Container: ~/dev/archie/
```

This means `ak project`, brain resolution, and all tools work identically to an
unnamed session. No special resolution logic needed inside the container.

### Multiple unnamed project sessions

Remove the single-session restriction. Container name includes a hash suffix:
`archie-shell-<project>-<hash>`. No prompt to switch to general. Each mounts the
same project directory — deconflicting is the user's responsibility.

### General session working directories

All general sessions get a host-mounted working directory:
- Named: `~/.archie/sessions/general/<name>/` — persists
- Unnamed: `~/.archie/sessions/general/<hash>/` — removed on exit

Mounted at a fixed container path (e.g. `~/workspace/`). Solves the data-passing
problem — files written there are accessible on the host.

### Cleanup

- Named sessions: `archie session --rm <name>` removes the directory
- Unnamed general sessions: CLI removes the directory after container exits
- Orphaned dirs (crash): `archie status` shows them, `archie session --rm` cleans up

### What changes from plan 006

- **Remove**: worktree creation, `.git` mount logic, worktree status checks,
  `ak project` worktree resolution, branch creation
- **Keep**: session command, name resolution (project-scoped, qualified, search),
  status display, cleanup, name validation
- **Change**: mount strategy (clone dir at project path instead of worktree + .git),
  session creation (clone instead of worktree add)
- **Add**: sub-repo detection and cloning, general session working dirs, multiple
  unnamed project sessions, unnamed dir cleanup

## Requirements

### Named Project Sessions

- `archie session <name>` creates or resumes a named project session
  - AC: Clones project repo into `~/.archie/sessions/<project>/<name>/`
  - AC: Detects and clones immediate sub-repos into relative paths
  - AC: Clone uses `git clone --single-branch <remote-url>`
  - AC: Remote URL read from existing local repo
  - AC: If session directory exists, reattaches (no re-clone)
  - AC: Session directory mounted at container's project path
  - AC: No automatic branching — agent handles this

### Multiple Unnamed Project Sessions

- `archie` allows multiple concurrent project sessions
  - AC: Container name includes hash: `archie-shell-<project>-<hash>`
  - AC: No "already running" prompt — just launches
  - AC: Each mounts the project directory directly (shared)

### General Session Working Directories

- All general sessions get a host-mounted working directory
  - AC: Named: `~/.archie/sessions/general/<name>/` — persists
  - AC: Unnamed: `~/.archie/sessions/general/<hash>/` — removed after exit
  - AC: Mounted at `~/workspace/` in the container
  - AC: Container `-w` set to the workspace mount

### Session Resolution

- Same as plan 006:
  - AC: In a project dir → scoped to that project
  - AC: Outside any project → search all sessions, error if ambiguous
  - AC: Qualified name (`project/session`) works from anywhere

### Session Cleanup

- `archie session --rm <name>` removes a named session
  - AC: Cannot remove if container is running (error)
  - AC: Prompts if repos have uncommitted/unpushed changes
  - AC: `-f` forces removal
  - AC: Removes the entire session directory

### Status

- `archie status` shows all sessions
  - AC: Running containers (active — named and unnamed)
  - AC: Session directories with no container (inactive named sessions)
  - AC: Git state for session repos: ahead/behind, modified count

## Technical Design

### Clone Creation

```python
def _create_session_clone(project: Path, session_name: str) -> Path:
    """Clone project and sub-repos into a session directory."""
    session_dir = ARCHIE_HOME / "sessions" / project.name / session_name

    # Clone top-level repo (git clone creates the target directory)
    remote = _get_remote_url(project)
    result = subprocess.run(
        ["git", "clone", "--single-branch", remote, str(session_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print_error(f"Failed to clone {project.name}: {result.stderr.strip()}")
        raise SystemExit(1)

    # Clone sub-repos (immediate subdirectories with .git/)
    for child in sorted(project.iterdir()):
        if child.is_dir() and (child / ".git").is_dir():
            sub_remote = _get_remote_url(child)
            sub_dest = session_dir / child.name
            result = subprocess.run(
                ["git", "clone", "--single-branch", sub_remote, str(sub_dest)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print_error(f"Failed to clone {child.name}: {result.stderr.strip()}")
                raise SystemExit(1)

    return session_dir


def _get_remote_url(repo: Path) -> str:
    """Get origin remote URL from a local repo."""
    result = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()
```

### Container Mount (named project session)

```python
# Session dir mounted at the container's project path
container_project = str(project).replace(host_home, container_home)
args.extend(["-v", f"{session_dir}:{container_project}", "-w", container_project])
```

### Container Mount (general session)

```python
container_workspace = f"{container_home}/workspace"
args.extend(["-v", f"{session_dir}:{container_workspace}", "-w", container_workspace])
```

### Multiple Unnamed Project Sessions

```python
# Always add hash suffix for unnamed project sessions
import hashlib, time
suffix = hashlib.sha1(str(time.time_ns()).encode()).hexdigest()[:5]
container_name = f"{CONTAINER_PREFIX}shell-{_sanitize_name(project.name)}-{suffix}"
# No collision check needed — hash is unique
```

### Unnamed General Session Cleanup

```python
# After container exits
returncode = _docker(*args).returncode
if not session and session_dir and session_dir.exists():
    shutil.rmtree(session_dir)
return returncode
```

## Milestones

1. **Multiple unnamed project sessions + general working dirs**
   Approach:
   - Remove single-session restriction: all unnamed project sessions get a hash suffix
     in the container name. Remove the "Start a general session instead?" prompt entirely.
   - General session working dir creation lives in `run_container()`: when no project and
     no worktree, create `~/.archie/sessions/general/<suffix>/` and mount it. The dir path
     is stored in a local variable and passed to cleanup after the container exits.
   - Cleanup: after `_docker(*args)` returns, if the session was unnamed general,
     `shutil.rmtree(session_dir)`. Wrap in try/except (dir may already be gone).
   Deliverable: Multiple unnamed project sessions coexist. General sessions have writable host dir.
   Verify: Launch two unnamed project sessions simultaneously — both start without error.
   Write a file in a general session, confirm visible on host at `~/.archie/sessions/general/<hash>/`.
   Exit the general session, confirm the directory is removed.

2. **Named session clone creation**
   Approach:
   - Replace worktree creation with clone logic in `docker.py`
   - Detect sub-repos (one level deep, immediate subdirs with `.git/`)
   - Clone top-level + sub-repos using `git clone --single-branch <remote>`
   - Mount session dir at container's project path
   - Reattach: if session dir exists, skip cloning — just mount and launch (identical
     to fresh session). No automatic fetch/pull — agent handles sync if needed.
   Deliverable: `archie session fix-auth` clones repos, launches container with correct mounts.
   Verify: Create named session, verify clones exist with correct remotes, verify container
   sees correct paths and `ak project` resolves. Resume session, verify no re-clone.

3. **Remove worktree code + multi-repo status/cleanup**
   Approach:
   - Remove `create_or_reuse_worktree`, worktree-specific mount logic, `.git` file mount
   - Remove `_resolve_name_from_worktree` from agent-kit `project.py` (cross-repo change,
     committed to agent-kit's `feat/named-sessions` branch alongside archie changes)
   - Rename `worktree_status` → `session_status`: iterate all `.git/` dirs in the session
     directory (top-level + sub-repos), aggregate modified/ahead counts across all repos
   - Update `_remove_session` cleanup: check all repos in the session dir for dirty/unpushed
     state before prompting. Report which repos have uncommitted work.
   - Update status display to show aggregated state
   Deliverable: No worktree references remain. Sessions use clones only. Status and cleanup
   handle multi-repo sessions correctly.
   Verify: Full test of session create/resume/status/remove cycle. Verify `ak project`
   resolves correctly inside a clone-based session (path-based resolution, no worktree
   logic needed). Verify cleanup prompts when any sub-repo is dirty.

4. **Documentation**
   Approach:
   - Update `docs/sessions.md` — new session model, working dirs, clones
   - Update `README.md` commands table
   Deliverable: Documentation reflects final session model.
   Verify: All flows documented.
