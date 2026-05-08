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
    session_dir.mkdir(parents=True, exist_ok=True)

    # Clone top-level repo
    remote = _get_remote_url(project)
    subprocess.run(
        ["git", "clone", "--single-branch", remote, str(session_dir)],
        check=True,
    )

    # Clone sub-repos (one level deep)
    for child in sorted(project.iterdir()):
        if child.is_dir() and (child / ".git").is_dir() and child != project:
            sub_remote = _get_remote_url(child)
            sub_dest = session_dir / child.name
            subprocess.run(
                ["git", "clone", "--single-branch", sub_remote, str(sub_dest)],
                check=True,
            )

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
   - Remove single-session restriction (hash suffix for all unnamed project sessions)
   - Create working directory for all general sessions
   - Mount general session working dir at `~/workspace/`
   - Clean up unnamed general dirs on exit
   Deliverable: Multiple unnamed project sessions coexist. General sessions have writable host dir.
   Verify: Launch two unnamed project sessions simultaneously. Write a file in general session, confirm visible on host.

2. **Named session clone creation**
   Approach:
   - Replace worktree creation with clone logic
   - Detect sub-repos (one level deep, `.git/` dirs)
   - Clone top-level + sub-repos using `git clone --single-branch <remote>`
   - Mount session dir at container's project path
   - Reattach if session dir exists
   Deliverable: `archie session fix-auth` clones repos, launches container with correct mounts.
   Verify: Create named session, verify clones exist, verify container sees correct paths. Resume session, verify no re-clone.

3. **Remove worktree code**
   Approach:
   - Remove `create_or_reuse_worktree`, worktree-specific mount logic, `.git` file mount
   - Remove `ak project` worktree resolution (no longer needed — container paths match)
   - Update `worktree_status` → `session_status` (reads git state from session dir clones)
   - Update status display
   Deliverable: No worktree references remain. Sessions use clones only.
   Verify: Full test of session create/resume/status/remove cycle.

4. **Documentation**
   Approach:
   - Update `docs/sessions.md` — new session model, working dirs, clones
   - Update `README.md` commands table
   Deliverable: Documentation reflects final session model.
   Verify: All flows documented.
