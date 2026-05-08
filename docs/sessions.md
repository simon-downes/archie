# Sessions

Archie runs inside Docker containers. Each container is a session. The type of session
depends on where you run `archie` from and what flags you pass.

## Unnamed Sessions

### Project Session

Run `archie` from inside a project directory (a subdirectory of your configured
`project_dir`).

- Your project directory is mounted read-write
- The brain is mounted read-write
- Multiple unnamed project sessions can run simultaneously
- Container named `archie-shell-<project>-<hash>`

Use for: quick questions, debugging, reviews — anything where you want the agent
to see your current working state.

### General Session

Run `archie` from outside any project directory.

- A transient working directory is created at `~/.archie/sessions/general/<hash>/`
- Mounted at `~/workspace/` in the container — files written there are on the host
- The brain is mounted read-write
- Working directory is removed when the session exits
- Container named `archie-general-<hash>`

Use for: research, brain management, cross-project work, life admin.

## Named Sessions

Use `--name` to create an isolated, resumable session:

```bash
archie --name fix-auth
```

### Named Project Session

From inside a project directory, `--name` clones the project repos into an isolated
working directory:

- Clones the project repo and any immediate sub-repos (e.g. agent-kit)
- Working directory: `~/.archie/sessions/<project>/<name>/`
- Mounted at the container's project path (same as unnamed sessions)
- Persists between runs — `archie --name fix-auth` resumes where you left off
- Container named `archie-shell-<project>-<name>`

Use for: planned implementation work, long-running features, anything that benefits
from isolation.

### Named General Session

From outside a project directory:

- Working directory: `~/.archie/sessions/general/<name>/`
- Mounted at `~/workspace/` in the container
- Persists between runs
- Container named `archie-general-<name>`

### Qualified Names

Use `project/session` to target a specific project's session from anywhere:

```bash
archie --name archie/fix-auth
```

## Shell Mode

Use `--shell` to get bash instead of kiro-cli:

```bash
archie --shell                    # bash in unnamed container
archie --shell "ls -la"           # run command and exit
archie --shell --name foo         # bash in named session's working dir
archie --shell --name foo "ls"    # run command in named session, exit
```

## Prompts

Pass a prompt as a positional argument:

```bash
archie "explain the auth middleware"
```

This starts kiro-cli with that prompt as the first message, then continues as an
interactive chat. For longer prompts, pipe stdin:

```bash
echo "research xyz and put results in my inbox" | archie
```

## Managing Sessions

### List sessions

```bash
archie ls
```

Shows all running containers and inactive named session directories with their
git status (ahead/behind/modified).

### Remove sessions

```bash
archie rm              # remove all clean inactive sessions
archie rm fix-auth     # remove specific session (prompts if dirty)
archie rm --all        # remove all inactive (prompts for each dirty one)
archie rm -f fix-auth  # force remove without prompts
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `archie` | Interactive unnamed session |
| `archie "prompt"` | Session with initial prompt |
| `archie --name foo` | Named session (isolated) |
| `archie --shell` | Bash in sandbox |
| `archie ls` | List sessions |
| `archie rm [name]` | Remove sessions |
| `archie install` | Deploy persona and config |
| `archie build` | Build sandbox image |
| `archie status` | Check environment |
