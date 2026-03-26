---
name: action-project-docs
description: >
  Generate or update README.md, CONTRIBUTING.md, and AGENTS.md for projects using
  codebase analysis artifacts. Supports operating on individual files or the full set.
  Use this skill when creating project documentation from scratch, updating existing
  documentation after changes, adding missing documentation files, improving documentation
  quality, or when the user asks to "update the README", "create project docs", or
  "add a CONTRIBUTING file".
---

# Purpose

Generate and maintain high-quality project documentation (README.md, CONTRIBUTING.md, AGENTS.md) that is:

- Accurate to the actual codebase
- Appropriate for the project type
- Minimal and focused
- Free from duplication across files
- Useful for both humans and AI agents

---

# When to Use

- Creating documentation for a new project
- Updating documentation after significant changes
- Adding missing documentation files
- Improving documentation to follow best practices

# When Not to Use

- Minor typo fixes or small edits (handle directly)
- API documentation or code comments (different concern)
- Detailed architecture docs (belong in `/docs`)
- Release notes or changelogs (different format)

---

# Workflow

## 1. Determine scope

### Detect project structure

Check for `.git/` directories in immediate children of the project root. If any exist, this is
an **umbrella repo** — a top-level project that groups independent sub-projects together.

- **Umbrella repo docs**: describe the collection, relationships between sub-projects, and
  shared setup. Do not document sub-project internals — each sub-project owns its own docs.
- **Sub-project docs**: when the user specifies a sub-project ("update agent-kit's README"),
  scope analysis and documentation to that sub-directory. Treat it as an independent project.
- **Standard repo**: no nested git repos — treat as a single project.

### Determine which files to operate on

- **Individual file**: user specifies a file ("update the README") → operate on that file only
- **Full set**: user asks for "project docs" or doesn't specify → operate on README + CONTRIBUTING, add AGENTS.md only if warranted

Check which files already exist. For existing files, the goal is to improve and update — not replace.

## 2. Gather codebase understanding

Use `action-analyze-codebase` (surface mode) to understand the project. If analysis artifacts
already exist in `./analysis/`, use those.

For umbrella repos: analyse the top-level project only (shared config, relationships, install/setup).
For sub-projects: scope the analysis to the sub-project directory.

If the codebase analyzer is not available, read core docs and manifests directly as a fallback.

The key information needed:
- Project type (web app, CLI, library, collection, infrastructure, etc.)
- Primary languages and frameworks
- Build/test/lint tooling and commands
- Entry points and how to run the project
- Configuration approach
- Deployment approach (if applicable)

## 3. Read existing documentation

If updating existing files:

1. Read the current content in full
2. Identify what's accurate and should be preserved
3. Identify what's outdated or missing
4. Note the existing structure and style

**Preservation rule:** Do not discard existing information unless it's demonstrably incorrect
or the user explicitly asks for a rewrite. Existing docs may contain context that isn't
discoverable from code alone.

## 4. Identify gaps and ask questions

Before generating content, identify what's missing or ambiguous.

Ask the user about:
- Information that can't be determined from code (e.g., deployment targets, team conventions)
- Choices between alternatives (e.g., which installation method to feature)
- Whether existing content that looks outdated should be kept or removed

Ask one question at a time. Provide options when helpful.

## 5. Draft content

Generate content using the appropriate template as a starting point:
- [references/readme-template.md](references/readme-template.md)
- [references/contributing-template.md](references/contributing-template.md)
- [references/agents-template.md](references/agents-template.md)

**Content principles:**
- Document what exists, not preferences
- Extract actual patterns from the codebase
- Be specific and concrete — exact commands, actual paths
- Avoid generic advice
- Link to detailed docs (in `/docs` or external) rather than duplicating

**For updates:** merge new content into the existing structure. Match the existing style
and tone. Add new sections where appropriate rather than reorganising unless asked.

**For new files:** use the template structure, adapting sections to the project type.
The "Key Rules" pattern is recommended for new docs — a short list of 5-10 imperative
statements covering the most critical points for the file's audience.

## 6. Deduplicate (full-set mode only)

When operating on multiple files, ensure:
- Each piece of information appears once
- Information is in the most appropriate file
- Files reference each other where needed

**Distribution:**
- README: user-facing — what it is, how to use it, how to get started
- CONTRIBUTING: developer-facing — how to work on the project, conventions, testing
- AGENTS: agent-specific — non-obvious rules, safety constraints, automation hints

## 7. Present for approval

Show the complete content of all files to be created or updated.

For updates, highlight what changed from the existing content and why.

Wait for explicit approval before writing.

## 8. Write files

After approval:
- Write the file(s) to the project root
- Report what was created or updated

---

# AGENTS.md Guidance

Only create AGENTS.md when there are genuinely non-obvious rules for AI agents.

**Good candidates for AGENTS.md:**
- Safety constraints (e.g., "never modify state files directly")
- Required human approval points
- Non-obvious project structure (e.g., "core/ is stable API, experimental/ may change")
- Automation boundaries (e.g., "integration tests require Docker")
- Project-specific patterns that aren't obvious from code

**Don't create AGENTS.md for:**
- Information already clear from README/CONTRIBUTING
- Generic best practices
- Rules that are obvious from code structure

---

# Error Handling

- **No codebase analysis available**: fall back to reading manifests and project files directly
- **Existing docs have non-standard structure**: preserve the structure, add content within it
- **Conflicting information between docs and code**: flag to the user, don't silently override
