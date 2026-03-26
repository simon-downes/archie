# Analysis Output Format

Analysis artifacts are structured markdown files written to `./analysis/`.

## Overview File (overview.md)

Always produced for deep analysis. Contains the repo-level synthesis.

```markdown
# Codebase Analysis: <repo-name>

**Objective**: <what was analyzed and why>
**Pattern**: <monorepo | single-package | microservices | layered | other>
**Analyzed**: <date>

## Summary

2-4 sentence overview addressing the analysis objective.

## Structure

Top-level organisation and key directories. Include a tree diagram if helpful.

## Entrypoints

How to run, build, test, and deploy. Concrete commands where known.

## Modules / Services

Brief description of each logical unit and its responsibility.
For repos with partition-level analysis files, reference them here.

## Dependencies

Key external dependencies and their purposes.
Internal cross-module dependencies if applicable.

## Tooling

Build system, test framework, linter, formatter, CI/CD.
Include the actual commands (e.g., `make test`, `uv run pytest`).

## Findings

Notable observations: patterns, inconsistencies, risks, technical debt.

## Open Questions

Things that could not be determined from analysis alone.
```

## Partition Analysis Files

Produced per-partition during deep analysis of multi-module repos.

```markdown
# <Partition Name>

**Path**: <relative path from repo root>
**Purpose**: <1-2 sentence description>

## Structure

Key files and directories within this partition.

## Entrypoints

How this module/service is invoked or started.

## Dependencies

External packages and internal cross-references.

## Tooling

Partition-specific build/test/lint commands (if different from repo-level).

## Findings

Partition-specific observations.
```

## Guidelines

- Keep individual files focused — one partition per file
- Use concrete paths and commands, not abstractions
- Note uncertainty explicitly ("appears to be", "could not determine")
- Reference specific files when making claims (e.g., "defined in `src/main.py:45`")
- Omit empty sections rather than writing "N/A"
