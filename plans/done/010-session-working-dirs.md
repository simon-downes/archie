# Archie — Session Working Directories & CLI Redesign

## Objective

Redesign the CLI interface and session model. Named sessions get isolated working
directories with cloned repos. Multiple unnamed project sessions allowed. General
sessions get host-mounted working directories. Background mode deferred to a future plan.

## CLI Interface

```
archie                            # interactive unnamed session
archie "do xyz"                   # prompt passed to kiro-cli, then interactive chat
archie --name foo                 # interactive named session
archie --name foo "do xyz"        # prompt in named session, then interactive chat
archie --shell                    # bash in unnamed container
archie --shell "ls -la"           # run command in unnamed container, exit
archie --shell --name foo         # bash in named session's working dir
archie --shell --name foo "ls"    # run command in named session's working dir, exit
archie ls                         # list sessions and statuses
archie rm                         # remove inactive sessions with no uncommitted/unpushed changes
archie rm <name>                  # remove specific session
archie rm --all                   # remove all inactive sessions (prompts for dirty ones)
archie install                    # deploy persona and config
archie build                      # build sandbox image
archie status                     # environment readiness check
```

### Flags

- `--name <name>` — creates/resumes a named session (triggers clone for project sessions)
- `--shell` — run bash instead of kiro-cli. Prompt argument becomes a bash command.
- `--bg` — deferred to future plan (background/non-interactive mode)

### Prompt handling

- Positional argument: short prompt string (quoted)
- Piped stdin: if not a TTY and no positional prompt, read stdin as the prompt
- Prompt passed to kiro-cli which starts a chat session with that as the first message

### Constraints

- `--bg` requires a prompt (deferred)
- `--bg` on a project session requires `--name` (deferred)
- `--shell --bg` is invalid (deferred)

### Subcommands

- `ls` — list all sessions (active containers + inactive named session dirs)
- `rm` — remove session working directories
- `install`, `build`, `status` — unchanged

## Session Model

| Session type | Working directory | Container mount | Lifecycle |
|---|---|---|---|
| Unnamed project | None | Project dir mounted at container project path | Container removed on exit |
| Named project | `~/.archie/sessions/<project>/<name>/` | Session dir mounted at container project path | Persists until `rm` |
| Unnamed general | `~/.archie/sessions/general/<hash>/` | Mounted at `~/workspace/` in container | Removed on exit |
| Named general | `~/.archie/sessions/general/<name>/` | Mounted at `~/workspace/` in container | Persists until `rm` |

### Multiple unnamed project sessions

All unnamed project sessions get a hash suffix in the container name:
`archie-shell-<project>-<hash>`. No collision check, no "start general instead?" prompt.
Each mounts the same project directory — deconflicting is the user's responsibility.

### Named session isolation

`--name` triggers clone-based isolation for project sessions:
- Clone project repo + immediate sub-repos into session directory
- Session directory mounted at the container's project path
- Agent sees identical paths to a normal session — no resolution changes needed

### General session working directories

All general sessions get a host-mounted working directory at `~/workspace/` in the
container. Solves the data-passing problem (files written there are on the host).

## Design Decisions

### Clone strategy

- `git clone --single-branch <remote-url>` — full history, default branch only
- Remote URL read from the existing local repo (`git remote get-url origin`)
- No branching at clone time — agent/skill creates branches as needed
- Additional branches fetched on demand by the agent

### Sub-repo detection

- Scan the project directory for immediate subdirectories containing `.git/`
- Clone each sub-repo into the same relative path within the session directory
- Sub-repos that are gitignored in the parent (e.g. `agent-kit` in archie's `.gitignore`)
  remain gitignored in the clone automatically — the parent's `.gitignore` is part of
  the cloned content

### Working directory layout (named project session)

Mirrors the host project structure:

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

`ak project`, brain resolution, and all tools work identically. No special resolution
logic needed inside the container.

### Session resume

If the session directory already exists, skip cloning — just mount and launch.
No automatic fetch/pull. Agent handles sync if needed.

### Cleanup (`archie rm`)

- `archie rm` (no args) — removes all inactive session dirs that are clean (no
  uncommitted changes, no unpushed commits across all repos in the session)
- `archie rm <name>` — removes specific session. Prompts if dirty, errors if running.
- `archie rm --all` — removes all inactive sessions. Prompts for each dirty one.
- `-f` flag forces removal without prompts.
- Non-interactive: refuses dirty removal unless `-f`.

### Status (`archie ls`)

Shows all sessions:
- Running containers (active — named and unnamed)
- Session directories with no container (inactive named sessions)
- For sessions with git repos: ahead/behind, modified count (aggregated across all repos)
- For sessions without git: file count and total size

Example:
```
Sessions:
  archie  fix-auth   ● running    3 ahead, clean
  archie  refactor   ○ inactive   1 ahead, 2 modified
  archie  (unnamed)  ● running    —
  general research   ○ inactive   12 files, 48KB
```

## Technical Design

### Click structure

```python
@click.group(cls=ArchieCLI, invoke_without_command=True)
@click.option("--name", default=None, help="Named session (isolated working directory)")
@click.option("--shell", is_flag=True, help="Run bash instead of kiro-cli")
@click.argument("prompt", required=False)
@click.pass_context
def main(ctx, name, shell, prompt):
    if ctx.invoked_subcommand is None:
        # Read piped input if no prompt and not a TTY
        if not prompt and not sys.stdin.isatty():
            prompt = sys.stdin.read().strip() or None
        _run_session(name=name, shell=shell, prompt=prompt)
```

### Clone creation

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

### Container mount (named project session)

```python
container_project = str(project).replace(host_home, container_home)
args.extend(["-v", f"{session_dir}:{container_project}", "-w", container_project])
```

### Container mount (general session)

```python
container_workspace = f"{container_home}/workspace"
args.extend(["-v", f"{session_dir}:{container_workspace}", "-w", container_workspace])
```

### Container naming

- Unnamed project: `archie-shell-<project>-<hash>`
- Named project: `archie-shell-<project>-<name>`
- Unnamed general: `archie-general-<hash>`
- Named general: `archie-general-<name>`

### Session status (multi-repo)

```python
def session_status(session_dir: Path) -> str:
    """Aggregate git status across all repos in a session directory."""
    parts = []
    total_ahead = 0
    total_modified = 0

    # Find all git repos in the session dir
    repos = [session_dir] if (session_dir / ".git").is_dir() else []
    for child in sorted(session_dir.iterdir()):
        if child.is_dir() and (child / ".git").is_dir():
            repos.append(child)

    for repo in repos:
        # Ahead count
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "@{upstream}..HEAD"],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            total_ahead += len(result.stdout.strip().splitlines())

        # Modified files
        result = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            total_modified += len(result.stdout.strip().splitlines())

    if total_ahead:
        parts.append(f"{total_ahead} ahead")
    if total_modified:
        parts.append(f"{total_modified} modified")
    return ", ".join(parts) if parts else "clean"
```

### Unnamed general session cleanup

```python
# After container exits, clean up transient working dir
returncode = _docker(*args).returncode
if not named and session_dir and session_dir.exists():
    shutil.rmtree(session_dir, ignore_errors=True)
return returncode
```

## What changes from plan 006

- **Remove**: worktree creation, `.git` file mount logic, worktree status checks,
  `ak project` worktree resolution, `archie session` subcommand, `archie shell` subcommand
- **Keep**: session name validation, container naming logic, status display concept
- **Replace**: worktree mount → clone mount, `session` subcommand → `--name` flag
- **Add**: clone creation, sub-repo detection, general working dirs, `archie ls`,
  `archie rm`, prompt argument, `--shell` flag, piped input, multi-repo status

## Milestones

1. **CLI restructure + multiple unnamed sessions**
   Approach:
   - Restructure main command: add `--name`, `--shell`, positional `prompt` argument
   - Remove `session` subcommand and `shell` subcommand (replaced by `--shell` flag)
   - Remove `BUILTIN_COMMANDS` entry for `session` and `shell`
   - Add `ls` and `rm` subcommands
   - All unnamed project sessions get hash suffix (same pattern as general sessions:
     `hashlib.sha1(str(time.time_ns()).encode()).hexdigest()[:5]`) — remove collision
     check and "start general instead?" prompt entirely
   - Piped stdin detection: if not TTY and no prompt arg, read stdin
   - `rm` operates globally (all projects) — uses same resolution logic as session
     creation: scoped to current project if in one, qualified names from anywhere,
     search with ambiguity error
   Deliverable: New CLI interface works for unnamed sessions (current behaviour preserved
   with new flags). `archie ls` shows running containers.
   Verify: `archie` launches interactive session. `archie "hello"` passes prompt.
   `archie --shell "ls"` runs bash command. Two unnamed project sessions coexist.
   `archie ls` shows both.

2. **General session working directories**
   Approach:
   - Create `~/.archie/sessions/general/<suffix>/` for all general sessions
   - Mount at `~/workspace/` in container, set as `-w`
   - Named general: suffix is the name, persists
   - Unnamed general: suffix is hash, removed after container exits
   - Cleanup in `run_container` after docker returns (try/except shutil.rmtree)
   Deliverable: General sessions have writable host-mounted working directory.
   Verify: Write file in general session, confirm on host. Exit unnamed, confirm dir removed.
   Exit named, confirm dir persists. `archie ls` shows named general sessions.

3. **Named project session clones**
   Approach:
   - Implement `_create_session_clone`: clone top-level + sub-repos (one level deep)
   - `--name` on a project session triggers clone into `~/.archie/sessions/<project>/<name>/`
   - Mount session dir at container's project path
   - Resume: if session dir exists, skip clone, just mount and launch
   - Error if container with that name is already running
   Deliverable: `archie --name fix-auth` clones repos, launches with correct mounts.
   Verify: Create named session, verify clones with correct remotes. Resume, verify no
   re-clone. `ak project` resolves correctly inside container.

4. **Session cleanup (`archie rm`)**
   Approach:
   - Session resolution for `rm` uses same logic as creation: project-scoped if in a
     project dir, qualified names (`project/session`) from anywhere, search with
     ambiguity error if outside a project
   - `archie rm` (no args): remove all inactive clean sessions globally
   - `archie rm <name>`: remove specific session, prompt if dirty
   - `archie rm --all`: remove all inactive, prompt for each dirty one
   - `-f` forces without prompts
   - Dirty check: for sessions with git repos, aggregate across all repos (reuse
     `session_status`). For non-git sessions (general), always considered clean —
     just remove.
   - Non-interactive: refuse dirty git sessions unless `-f`
   - Remove session directory (`shutil.rmtree`) after checks pass
   Deliverable: `archie rm` safely cleans up sessions.
   Verify: Create sessions, dirty one. `archie rm` removes clean ones only.
   `archie rm <dirty>` prompts. `archie rm -f <dirty>` forces. Running session refuses.
   Non-git general session removed without prompt.

5. **Remove worktree code + documentation**
   Approach:
   - Remove `create_or_reuse_worktree`, worktree mount logic, `.git` file mount
   - Remove `_resolve_name_from_worktree` from agent-kit `project.py` (cross-repo,
     committed on matching branch). After removal, `ak project` resolves via the
     existing `relative_to(project_dir)` path — this works because clone-based sessions
     mount at the original project path (e.g. `~/dev/archie`).
   - Update `docs/sessions.md` — new CLI, working dirs, clones
   - Update `README.md` commands table
   - Update `CONTRIBUTING.md` if needed (container mounts section)
   Deliverable: No worktree references remain. Documentation reflects final model.
   Verify: Full session lifecycle test. `ak project` resolves in all session types.
   Docs match implementation.
