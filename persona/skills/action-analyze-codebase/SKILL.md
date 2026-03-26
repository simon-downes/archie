---
name: action-analyze-codebase
description: >
  Analyze codebases to understand structure, architecture, dependencies, entrypoints,
  and tooling. Produces structured analysis artifacts that other skills can consume to
  generate documentation or answer questions. Handles repositories of any size through
  intelligent partitioning and subagent delegation. Use this skill when you need to
  understand a codebase before making changes, answer questions about project structure
  or architecture, identify entrypoints and dependencies, assess build and test tooling,
  or produce analysis artifacts for documentation generation.
---

# Purpose

Understand the current state of a repository and produce structured analysis artifacts
under `./analysis/` that other skills can consume. Keeps the main agent's context clean
by delegating deep analysis to subagents.

---

# When to Use

- Need to understand a codebase before making changes
- Questions about project structure, architecture, or dependencies
- Identifying entrypoints, build/test/lint tooling
- Producing analysis artifacts for documentation generation
- Planning large refactoring or feature additions

# When Not to Use

- Simple questions answerable from a single file (just read it)
- Writing or updating documentation (use action-project-docs)
- Running QA checks (use qa-runner)

---

# Analysis Workflow

## 1. Determine scope

Assess what's needed based on the objective:

- **Surface**: docs + manifest files only — sufficient for most questions
- **Deep**: full partition-based analysis — needed for architectural understanding of large/unfamiliar repos

Default to surface. Escalate to deep only when surface analysis cannot answer the objective.

## 2. Surface analysis

Read core documentation and project manifests:

**Documentation** (version-controlled sources only):
- `README.md`, `CONTRIBUTING.md`, `AGENTS.md`
- `./docs/` (if present)

**Project manifests** (read whichever exist):

*Package manifests:*
`pyproject.toml`, `package.json`, `composer.json`, `Cargo.toml`, `go.mod`,
`pom.xml`, `build.gradle*`, `*.csproj`, `Gemfile`, `mix.exs`

*Workspace/monorepo manifests:*
`pnpm-workspace.yaml`, `nx.json`, `turbo.json`, `lerna.json`, `WORKSPACE`, `MODULE.bazel`

*Task/build manifests:*
`Makefile`, `Taskfile.yml`, `justfile`

*Container/deploy manifests:*
`Dockerfile*`, `docker-compose*.yml`, Helm charts, k8s manifests, `terraform/*.tf`

*CI manifests:*
`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`

*Toolchain:*
`.nvmrc`, `.tool-versions`, `.python-version`, lockfiles

**Structure:**
- Top-level directory tree (2 levels)
- Identify obvious architectural patterns (monorepo, single package, microservices, etc.)

If this is sufficient to answer the objective, respond directly — no need to write analysis artifacts.

## 3. Deep analysis

When surface analysis is insufficient, perform a full analysis using the partition strategy.

### Probe

1. Map the full directory structure
2. Identify architectural pattern (monorepo, microservices, layered, single package)
3. Identify logical partitions (services, modules, packages, layers)
4. Estimate repo size to determine if subagent delegation is needed

### Partition

Split the repo by its natural boundaries:
- Services/applications (microservices)
- Modules/packages (monorepo)
- Layers (frontend/backend/infrastructure)

For small repos (<50 files), skip partitioning — delegate the whole repo to a single subagent.

### Analyze partitions

Delegate analysis to the `codebase-analyzer` subagent to keep the main agent's context clean.

- Small repo (no partitions): 1 subagent analyzes the whole repo
- Larger repo: 1 subagent per partition, up to 4 in parallel
- Purpose and responsibility
- Entrypoints (how it's invoked/started)
- Internal structure and key files
- Dependencies (internal cross-references and external packages)
- Build/test/lint tooling
- Configuration approach

Delegate partition analysis to the `codebase-analyzer` subagent when:
- Deep analysis is needed (always — keeps main agent context clean)

Use up to 4 parallel subagents. Each subagent receives:
- The partition path(s)
- The overall objective
- Context about the repo's architectural pattern

### Synthesize

Merge partition results into a coherent whole:
- Repo-level summary addressing the objective
- Cross-partition dependencies and relationships
- Shared tooling and conventions
- Findings and open questions

## 4. Write analysis artifacts

Write structured output to `./analysis/`. The directory structure should mirror the repo's logical structure.

**Single package repo:**
```
./analysis/
  overview.md
```

**Monorepo / microservices:**
```
./analysis/
  overview.md
  services/
    auth/analysis.md
    api/analysis.md
  infrastructure/analysis.md
```

See [references/OUTPUT-FORMAT.md](references/OUTPUT-FORMAT.md) for the artifact schema.

`./analysis/` is a working directory — not a persistent cache. It represents the analysis state at the time it was produced. If the codebase changes significantly, re-run the analysis.

## 5. Respond to the objective

After analysis, answer the original question or confirm the artifacts are ready for consumption by other skills.

---

# Subagent Usage

The `codebase-analyzer` subagent handles partition-level analysis.

Invoke via `use_subagent` with:
- Agent name: `codebase-analyzer`
- Query: the partition-specific analysis objective
- Context: repo pattern, partition paths, what to analyze

The subagent has read-only access (read, glob, grep, shell, code) and returns structured analysis for its partition.

## Parent / Subagent Contract

**The parent skill (main agent) is responsible for:**
- Selecting analysis mode (surface vs deep)
- Partitioning the repo
- Passing objective and context to subagents
- Synthesizing cross-partition relationships
- Writing normalized artifacts to `./analysis/`

**The codebase-analyzer subagent is responsible for:**
- Read-only analysis of assigned partition paths
- Returning structured markdown (never writing files)
- Staying within token budget and assigned scope
- Identifying entrypoints, dependencies, tooling, and findings for its partition

---

# Error Handling

- **No documentation exists**: note in findings, proceed with manifest and structure analysis
- **No manifest files**: note in findings, infer from directory structure and file extensions
- **Subagent failure**: fall back to bounded direct analysis, note the limitation
- **Repo too large for direct analysis**: always partition, never attempt to read everything
