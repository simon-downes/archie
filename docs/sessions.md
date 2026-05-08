# Sessions

Archie runs inside Docker containers. Each container is a session. The type of session
depends on where you run `archie` from.

## Project Sessions

Run `archie` from inside a project directory (a subdirectory of your configured
`project_dir`).

- Your project directory is mounted read-write
- The brain is mounted read-write
- Container is named `archie-shell-<project>` (e.g. `archie-shell-my-app`)
- Only one session per project at a time — starting a second prompts to start a
  general session instead

Use for: working on a specific project — coding, debugging, planning, reviewing.

## General Sessions

Run `archie` from outside any project directory.

- No project directory is mounted
- The brain is mounted read-write
- Container is named `archie-general-<hash>` by default
- Multiple general sessions can run simultaneously

Use for: research, brain management, cross-project work, life admin — anything not
tied to a single project.

### Named Sessions

Use `archie session` to create a named, resumable session:

```bash
archie session research
# → container: archie-general-research
```

For project sessions with a git repo, named sessions get their own worktree:

```bash
cd ~/dev/my-project
archie session fix-auth
# → worktree: ~/.archie/worktrees/my-project/fix-auth/
# → branch: archie/fix-auth
# → container: archie-shell-my-project-fix-auth
```

Running the same command again resumes the session (reattaches to the existing worktree).

Named sessions follow the one-at-a-time rule — you can't start two sessions with the
same name. Use `archie session --rm <name>` to remove an inactive session.

### Qualified Names

Use `project/session` to target a specific project's session from anywhere:

```bash
archie session archie/fix-auth
```

## Archie Development

Running `archie` from inside the `archie` project is a standard project session.

## Shell Sessions

`archie shell` drops you into an interactive bash shell in the sandbox. It follows
the same session type rules — project or general — based on your current directory.

## Checking Sessions

`archie status` shows all running sessions along with environment readiness:

```bash
archie status
```

Running containers appear under the Sessions heading with their name, status, and image.
