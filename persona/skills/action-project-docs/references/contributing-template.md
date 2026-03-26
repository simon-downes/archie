# CONTRIBUTING.md Template

Adapt sections based on project type. Omit sections that don't apply.

---

## Structure

```markdown
# Contributing

## Key Rules

- [Most critical rule for contributors]
- [Up to 5-10 imperative statements]

## Development Setup

## Project Conventions

## Testing

## Submitting Changes
```

---

## Development Setup

Be specific — exact commands, expected output, verification steps.

```markdown
## Development Setup

### Prerequisites

- [Runtime/tool with version]
- [Other requirements]

### Setup

1. Clone the repository
2. `[install command]`
3. `[setup command]`
4. Verify: `[verification command]`
```

---

## Project Conventions

Document actual patterns extracted from the codebase, not generic standards.

```markdown
## Project Conventions

### Code Organisation

- `[dir]/` — [what lives here and why]
- `[dir]/` — [what lives here and why]

### Code Style

[Formatter/linter used and how to run it]

### Naming Conventions

- [Actual patterns used in the codebase]
```

Link to external standards rather than duplicating them.

---

## Testing

Concrete commands and project-specific patterns.

```markdown
## Testing

### Running Tests

```bash
[test command]
```

### Test Organisation

- Tests live in `[path]`
- [Naming convention]
- [Coverage expectations if any]

### Writing Tests

- [Project-specific patterns, fixtures, mocks]
```

---

## Submitting Changes

Project-specific process. Link to external conventions.

```markdown
## Submitting Changes

1. Create a branch: `[branching convention]`
2. Make changes
3. Run checks: `[command]`
4. Push and create PR

### Commit Messages

[Format or link to convention]

### Pull Requests

- [Description requirements]
- [Review process]
- [Merge approach]
```

---

## Additional Sections by Project Type

### Web App

- **Database Changes**: migration commands, seeding approach
- **Environment Variables**: how to add new ones, where they're documented

### CLI Tool

- **Adding Commands**: where command code lives, structure pattern, how to test

### Library

- **API Design**: public API conventions, backward compatibility, deprecation
- **Documentation**: docstring format, example requirements

### Infrastructure

- **Module Development**: variable conventions, output patterns, example structure
- **Testing**: plan validation, integration test approach

---

## Anti-Patterns

```markdown
❌ Follow PEP 8
✅ Uses ruff for linting (configured in pyproject.toml). Run `make lint`.

❌ Write tests for your code
✅ Tests live in tests/ mirroring src/ structure. Run `make test`. See tests/conftest.py for shared fixtures.

❌ [Copying entire Git commit message guide]
✅ Uses conventional commits (https://conventionalcommits.org). Project-specific: use `feat`, `fix`, `chore`, `docs` types.
```
