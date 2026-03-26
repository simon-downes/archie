# AGENTS.md Template

Only create AGENTS.md when there are genuinely non-obvious rules for AI agents.
If everything an agent needs is already in README and CONTRIBUTING, skip this file.

---

## Structure

```markdown
# Agent Guidelines

[1-2 sentence project context]

## Rules

- [Non-obvious constraint 1]
- [Non-obvious constraint 2]

## Safety Constraints

- [Required human approval points]
- [Dangerous operations to avoid]

## Hints

- [Useful context about project structure]
- [Common pitfalls]
- [Effective automation approaches]
```

---

## What Belongs Here

**Safety constraints:**
```markdown
- Never modify Terraform state files directly
- Database migrations require human review before execution
- Production deployments require manual approval
```

**Non-obvious structure:**
```markdown
- `core/` contains stable APIs; `experimental/` may change without notice
- Configuration is validated against JSON schema in `schemas/`
- Each module in `modules/` is independently versioned
```

**Automation boundaries:**
```markdown
- Integration tests require Docker and take ~5 minutes
- `make validate` runs all pre-commit checks
- Test fixtures are generated from `scripts/generate-fixtures.py`
```

**Project-specific patterns:**
```markdown
- All HTTP handlers follow the pattern in `handlers/example_handler.py`
- Environment variables are loaded via `config/settings.py`, never read directly
- Database queries go through the repository pattern in `repos/`
```

---

## What Does NOT Belong Here

- Information already in README or CONTRIBUTING (don't duplicate)
- Generic best practices ("write clean code", "follow SOLID")
- Rules obvious from code structure
- Detailed API documentation
- Setup instructions (those go in CONTRIBUTING)

---

## Tone

Write for an AI agent that is competent but unfamiliar with the project.
Be direct and imperative. Skip explanations unless the rule would seem arbitrary without context.

```markdown
❌ It would be advisable to run the linter before committing changes.
✅ Run `make lint` before committing. CI will reject unlinted code.

❌ The project uses a microservices architecture.
✅ Services communicate via SQS queues defined in `infrastructure/queues.tf`. Do not add direct HTTP calls between services.
```
