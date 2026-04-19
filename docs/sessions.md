# Sessions

Archie runs inside Docker containers. Each container is a session. The type of session
depends on where you run `archie` from.

## Project Sessions

Run `archie` from inside a project directory (a subdirectory of your configured
`project_dir`).

- Your project directory is mounted read-write
- The brain is mounted read-only — available as context, not for editing
- Container is named `archie-shell-<project>` (e.g. `archie-shell-my-app`)
- Only one session per project at a time — starting a second is blocked

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

Use `--session` to give a general session a stable name:

```bash
archie --session research
# → container: archie-general-research
```

Named sessions follow the same one-at-a-time rule — you can't start two sessions
with the same name. Without `--session`, each session gets a unique hash suffix and
there's no conflict.

## Archie Development

Running `archie` from inside the `archie` project is a project session with one
exception: the brain is mounted read-write instead of read-only.

This is because improving Archie often involves brain operations — ingestion, curation,
skill development — that require write access.

## Shell Sessions

`archie shell` drops you into an interactive bash shell in the sandbox. It follows
the same session type rules — project or general — based on your current directory.

## Checking Sessions

`archie status` shows all running sessions along with environment readiness:

```bash
archie status
```

Running containers appear under the Sessions heading with their name, status, and image.
