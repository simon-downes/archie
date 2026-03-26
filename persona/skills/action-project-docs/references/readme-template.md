# README.md Template

Adapt sections based on project type. Omit sections that don't apply.
The "Key Rules" section is recommended for new docs but not required for updates to existing files.

---

## Structure

```markdown
# Project Name

Brief description (1-2 sentences).

## Key Rules

- [Most critical rule for users/contributors]
- [Second most important rule]
- [Up to 5-10 imperative statements]

## [Getting Started / Installation]

## [Usage]

## [Configuration]

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## [Additional sections as needed]
```

---

## Key Rules Guidelines

- Write in imperative mood
- Focus on non-obvious or critical points
- Useful for both humans and AI agents
- Avoid stating the obvious
- Keep to 5-10 items maximum

---

## Sections by Project Type

### Web App / API

- **Installation/Setup**: prerequisites, dependencies, database setup, environment config
- **Configuration**: environment variables (required and optional with defaults)
- **Usage**: how to access, key endpoints or UI
- **Deployment**: brief instructions or link to deployment docs

### CLI Tool

- **Installation**: package manager install + from-source option
- **Usage**: command syntax, common commands with examples
- **Configuration**: config file location, environment variables

### Library / Package

- **Installation**: package manager install, version requirements
- **Usage**: import statements, basic API usage, common patterns
- **Compatibility**: language/runtime versions, platform requirements

### Collection / Monorepo

- **Repository Structure**: directory layout with brief descriptions
- **Getting Started**: which package to use when, installation options
- **Development**: workspace setup, cross-package workflow

### Umbrella Repo (independent sub-projects)

- **Overview**: what the umbrella groups together and why
- **Repository Structure**: sub-projects with one-line descriptions, note they are independent repos
- **Getting Started**: shared setup (if any), then point to each sub-project's own README
- **Related Projects**: links to sub-project READMEs with brief descriptions
- Do NOT document sub-project internals — each sub-project owns its own docs

### Infrastructure (Terraform/CloudFormation)

- **Usage**: module invocation example with key variables
- **Requirements**: provider versions, backend configuration
- **Inputs/Outputs**: key variables and outputs (or link to generated docs)

---

## Anti-Patterns

```markdown
❌ Follow Python PEP 8 style guide
✅ Uses Black formatter with line length 100 (configured in pyproject.toml)

❌ Write good commit messages
✅ Uses conventional commits — see CONTRIBUTING.md

❌ [Repeating detailed dev setup that belongs in CONTRIBUTING]
✅ See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
```
