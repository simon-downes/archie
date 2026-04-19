# Capabilities

What you can ask Archie to do, organised by what you're trying to achieve.

## Planning & Implementation

### Structured Planning

Tell Archie what you want to build and it will walk you through a structured planning
process: clarifying requirements, designing the technical approach, and breaking work
into milestones with testable deliverables. Plans are stored in your issue tracker
(Linear, GitHub Issues) or as local files in `./plans/`.

Archie investigates the codebase before asking you questions, so most of the back-and-forth
is about intent and preferences — not things it could have looked up itself.

**Example prompts:**
- "Plan the rate limiting feature"
- "I need to add OAuth support — let's plan it out"
- "Plan for PLAT-123" (loads context from the issue)

### Milestone-Based Implementation

Once a plan is approved, Archie implements it milestone by milestone. Each milestone
is verified before moving on — mechanical checks (formatting, linting, tests) and
a reasoning-level code review. Archie creates branches, commits with conventional
messages, and tracks progress against the plan.

**Example prompts:**
- "Let's implement the plan"
- "Implement PLAT-123"
- "Resume implementation from milestone 3"

### Code Review

Archie reviews code changes at three levels: during implementation (per-milestone),
after implementation (full pass), or standalone (ad-hoc or PR review). Reviews cover
coding standards, error handling, security, performance, and plan alignment. Findings
are graded by severity — issues that must be fixed vs. suggestions for improvement.

After a successful review, Archie creates a PR and sends a Slack notification (if
configured).

**Example prompts:**
- "Review the changes"
- "Is this ready to merge?"
- "Review PR #42"

### Plan Review

Before implementation begins, Archie can audit a plan for completeness — checking for
unresolved decisions, ambiguous requirements, and gaps that would block an implementor.

**Example prompts:**
- "Review this plan before we start"
- "Check the plan for gaps"
- "Is this plan ready to implement?"

## Knowledge & Memory

### Brain Queries

Archie checks its brain before answering questions about people, projects, decisions,
or domain knowledge. You don't need to tell it to look — it does this automatically
when the question might have a brain answer.

You can also ask directly.

**Example prompts:**
- "What do I know about Aurora failover?"
- "Who is Jane?"
- "What did we decide about the auth approach?"
- "Check the brain for anything on Kubernetes networking"

### Remembering Things

When you make a decision, state a fact worth keeping, or ask Archie to remember
something, it writes to the brain automatically. Information is routed to the right
context (personal, work, shared) and deduplicated against existing entries.

**Example prompts:**
- "Remember that Aurora failover takes about 30 seconds"
- "Save this: our SLA target is 99.95%"
- "Add Jane Smith as a contact — she's the EM at Tillo"

### Conversation Memory

Archie can summarise recent conversations into structured memory files. These capture
what was discussed, decided, and done — so future sessions can pick up where you left
off without re-explaining context.

**Example prompts:**
- "Process recent conversations"
- "Update memory"
- "Catch up on recent work"

### Research

For questions that need more than a quick search, Archie researches a topic across
multiple sources — official docs, blog posts, conference talks — and produces a
single document with findings, comparisons, and citations. Output goes to `_inbox/`
for you to review.

**Example prompts:**
- "Research Aurora multi-region failover strategies"
- "Deep dive into Kubernetes RBAC best practices"
- "What are the best practices for Terraform state management?"

### Ingestion

Drop files into `_raw/inbox/` (meeting notes, articles, transcripts, exports) and
Archie processes them into structured brain entities — extracting people, projects,
decisions, and knowledge, then routing each to the right context.

**Example prompts:**
- "Process the inbox"
- "Ingest this file into the brain"
- "Process raw items"

## Project Work

### Codebase Analysis

Archie can analyse a codebase to understand its structure, architecture, dependencies,
and tooling. For small repos it reads directly; for large ones it partitions the work
across subagents. Analysis artifacts are written to `./analysis/` for other workflows
to consume.

**Example prompts:**
- "Analyse this codebase"
- "What's the architecture of this project?"
- "How is this repo structured?"

### Documentation Generation

Archie generates and updates README.md, CONTRIBUTING.md, and AGENTS.md based on
actual codebase analysis — not templates. It reads your code, identifies patterns,
and writes documentation that reflects what exists. For updates, it preserves existing
content and merges in new information.

**Example prompts:**
- "Update the README"
- "Create project docs"
- "Add a CONTRIBUTING file"

### Terraform Modules

A guided workflow for creating new Terraform/OpenTofu modules. Archie walks through
requirements, suggests features you might have missed, establishes opinionated security
defaults, and generates code that matches your module collection's conventions.

**Example prompts:**
- "Create a Terraform module for S3"
- "Scaffold a Lambda module"
- "New Terraform module for Aurora"

## Integrations

Archie connects to external services through agent-kit. Available integrations depend
on which credentials are configured.

| Service | What Archie Can Do |
|---------|--------------------|
| **GitHub** | Create PRs, review PRs, branch management, CI status |
| **Linear** | Create/update issues, track status, load plans from issues |
| **Notion** | Search and read pages (used as a research source) |
| **Slack** | Send PR notifications to a channel |
| **AWS** | Credentials forwarded into the sandbox for infrastructure work |

Issue tracking (Linear or GitHub Issues) is configured per-project. Archie detects
the provider from project config and adapts automatically. If no tracker is configured,
issue operations are skipped silently — nothing breaks.

**Example prompts:**
- "Create an issue for this work"
- "What's the status of PLAT-123?"
- "Move PLAT-123 to In Review"

## Development Standards

Archie follows coding standards automatically when writing code. You don't need to
invoke these — they're applied during implementation and review.

### General

Core principles applied across all languages: SOLID, DRY, YAGNI, KISS. Type hints
on all function signatures. Docstrings on public interfaces. Specific exceptions over
broad catches. Secure defaults.

### Python

PEP 8 with Black formatting and Ruff linting. Google-style docstrings. Type hints
everywhere. uv for dependency management. pytest for testing. Click + Rich for CLI
tools.

### Terraform/OpenTofu

`tofu` over `terraform`. Kebab-case file names. Standard file layout (providers.tf,
variables.tf, outputs.tf). RFC 2119 keywords for variable requirements. Inline IAM
policies with `jsonencode()`. Semantic versioning for modules.

### Git

Conventional commits. Trunk-based development. Branch naming: `<user>/<ISSUE-KEY>-<description>`.
Rebase workflow for syncing with main.

## Extending Archie

### Add a Capability

For adding new features to the Archie platform itself. Archie reads its own architecture,
plans the work, implements across both codebases (archie + agent-kit), reviews, and
submits a PR — end to end.

**Example prompts:**
- "Add a capability for Google Calendar integration"
- "Extend Archie to support Jira"

### Create a Skill

For creating new skills or improving existing ones. Archie handles naming conventions,
layer classification, collision checking against existing skills, and activation phrase
optimisation.

**Example prompts:**
- "Create a skill for database migrations"
- "Improve the brain-write skill"
- "This skill doesn't trigger reliably — fix it"
