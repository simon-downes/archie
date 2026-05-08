# Archie — Session Working Directories

## Objective

Evolve the named session model (plan 006) to support isolated working directories
with cloned repos. Enable multiple concurrent unnamed project sessions. Provide a
uniform working directory for all session types (solving the general session
data-passing problem).

## Background

Plan 006 implemented named sessions with single-repo worktree backing. This plan
extends that work to handle:
- Multi-repo projects (archie + agent-kit, tillo-platform + core/modules/security)
- Background sessions (future — same isolation model)
- General session working directories (data in/out without workarounds)
- Multiple unnamed project sessions

## Concepts

- **Working directory** — a host-mounted directory that persists across container
  restarts. Every session gets one. For named project sessions, it contains cloned
  repos. For general sessions, it starts empty.
- **Named session** — `archie session <name>`. Gets an isolated working directory
  with cloned repos (project) or empty dir (general). Resumable.
- **Unnamed session** — `archie` with no session name. Project sessions mount the
  project directory directly. General sessions get a transient working directory.

## Session Model

| Session type | Working directory | Mount | Lifecycle |
|---|---|---|---|
| Unnamed project | `~/.archie/sessions/<project>/<hash>/` | Project dir mounted directly at container project path | Removed on exit |
| Named project | `~/.archie/sessions/<project>/<name>/` | Working dir mounted, repos cloned inside | Persists until `--rm` |
| Unnamed general | `~/.archie/sessions/general/<hash>/` | Working dir mounted (empty) | Removed on exit |
| Named general | `~/.archie/sessions/general/<name>/` | Working dir mounted (empty) | Persists until `--rm` |

## Open Questions

These need resolution before implementation:

1. **Unnamed session working directories** — do unnamed sessions really need a
   host-mounted working dir? Current unnamed project sessions mount the project
   dir directly and work fine. Unnamed general sessions are ephemeral. Adding a
   working dir for unnamed sessions adds cleanup complexity (remove on exit) for
   unclear benefit. Alternative: only named sessions get working dirs.

2. **Multiple unnamed project sessions** — currently blocked by container name
   collision. Fix is simple (add hash to container name). But do we actually need
   this? When would you run two unnamed sessions against the same project? If the
   answer is "rarely", maybe named sessions are the right tool for concurrency.

3. **Clone depth and scope** — `git clone --local` is fast (hardlinks) but still
   copies the full working tree. For large repos with many branches, even local
   clone takes time. Options: `--depth 1 --single-branch`, full clone, or
   `--local` (fast, shares objects). Leaning toward `--local` for project-dir
   repos (same machine, instant) but need to verify behaviour with sub-repos.

4. **Branch strategy for clones** — should the clone start on a new branch
   (`archie/<session-name>`), detached HEAD, or the same branch as the source?
   Plan 006 used `archie/<name>` branches. Same logic applies here but across
   multiple repos. What if one sub-repo doesn't have the branch?

5. **Sub-repo detection** — scan one level deep for `.git` directories? Or
   recurse? One level covers known cases (agent-kit under archie, core/modules
   under tillo-platform). Recursing risks finding vendored repos, test fixtures,
   or deeply nested things we don't want.

6. **Working dir layout** — should cloned repos mirror the project directory
   structure exactly? e.g.:
   ```
   ~/.archie/sessions/archie/fix-auth/
   ├── archie/          ← clone of ~/dev/archie
   └── archie/agent-kit/ ← clone of ~/dev/archie/agent-kit
   ```
   Or flatten:
   ```
   ~/.archie/sessions/archie/fix-auth/
   ├── archie/          ← top-level
   └── agent-kit/       ← sibling
   ```
   The nested layout preserves the relationship. The flat layout is simpler but
   loses the "agent-kit is inside archie" context.

7. **Interaction with existing worktree implementation** — plan 006 already
   implements worktree creation for the top-level repo. Do we keep worktrees
   (faster, shares objects, proper git integration) and add clone only for
   sub-repos? Or switch entirely to clones for uniformity?

8. **Container working directory (`-w`)** — with cloned repos inside the working
   dir, what's the container's cwd? The top-level repo clone? The session root?
   Needs to feel natural for the agent.

9. **How does `ak project` resolve inside a clone?** — currently it uses
   `project_dir` or worktree detection. A clone in `~/.archie/sessions/` is
   neither under `project_dir` nor a worktree. Need a resolution mechanism
   (env var? marker file? path convention?).

10. **Cleanup of unnamed session dirs** — if unnamed sessions get working dirs,
    they need cleanup on container exit. Docker `--rm` removes the container but
    not the host directory. Options: post-exit hook, trap in entrypoint, or just
    don't give unnamed sessions working dirs.

## Requirements (pending open question resolution)

TBD — requirements depend on answers to open questions above.

## Relationship to Plan 006

Plan 006 is complete and merged. This plan builds on it:
- Keeps: session command, resolution logic, status display, cleanup, ak project resolution
- Extends: working directory creation, multi-repo support, clone strategy
- Changes: mount strategy for named sessions (clone instead of single worktree)
- Adds: multiple unnamed project sessions, general session working dirs

## Next Steps

1. Resolve open questions (discussion)
2. Write requirements and design based on decisions
3. Implement incrementally on top of plan 006
