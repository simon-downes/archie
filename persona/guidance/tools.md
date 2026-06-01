# Available Tools

## Shell Usage Guidelines

1. Prefer structured output formats (`--json`, `--yaml`, `--porcelain`) and process them with `jq` or `yq`.

2. Compose tools with pipelines (`|`) instead of writing scripts whenever possible.

3. Use shell chaining for control flow:
   - `cmd1 && cmd2` (run on success)
   - `cmd1 || cmd2` (fallback on failure)

4. Use command grouping `{ ...; }` or `( ... )` when multiple commands share the same context.

5. Prefer modern CLI utilities for discovery and filtering:
   - `fd` for file discovery
   - `rg` for searching file contents
   - `jq` / `yq` for structured data processing.

## Standard Tools
**Code:** rg (ripgrep), fd, tree, shellcheck, shfmt
**Data:** jq, yq, sqlite3
**Cloud:** gh, aws, tofu, terraform-docs
**Database:** psql, mysql (mariadb), redis-cli
**Network:** curl, xh, nc (netcat), ping, dig/nslookup
**Python:** uv, python3

## Enhanced Tools

### difft (Difftastic)
Structural diff that understands code syntax. Use when comparing code files for better readability.

```bash
# Compare two files
difft file1.py file2.py

# Use with git
git diff | difft --color=always

# Compare directories
difft --display side-by-side old/ new/
```

**When to use:** Code reviews, refactoring verification, understanding complex changes.

### xh
HTTP client with better defaults for JSON APIs. Use over curl for quick API testing.

```bash
# GET request (auto-formats JSON)
xh https://api.example.com/users

# POST JSON (auto-detects)
xh POST https://api.example.com/users name=john email=john@example.com

# Headers
xh https://api.example.com/data Authorization:"Bearer token"

# Download file
xh --download https://example.com/file.zip
```

**When to use:** Testing APIs, quick HTTP requests with JSON, debugging endpoints.

## Database Clients

### psql
PostgreSQL client for querying RDS/Aurora Postgres instances.

**Use for:** Checking schemas, running diagnostic queries, verifying data migrations.

### mysql
MariaDB-compatible client for querying RDS MySQL/Aurora MySQL instances.

**Use for:** Checking schemas, running diagnostic queries, inspecting table structures.

### redis-cli
Redis client for inspecting ElastiCache instances.

```bash
# ElastiCache typically requires TLS
redis-cli -h <hostname> -p 6379 --tls
```

**Use for:** Checking ElastiCache health, inspecting key patterns, verifying TTLs.

## Network Diagnostics

`nc` (netcat) for TCP port checks, `ping` for ICMP reachability, `dig`/`nslookup` for DNS.
Most AWS services don't respond to ICMP — prefer `nc -zv <host> <port>` for connectivity testing.

## Scalr CLI

Terraform management platform CLI. Used for inspecting runs, debugging errors, and querying
environment/workspace configuration. Credentials via `SCALR_TOKEN` and `SCALR_HOSTNAME` env vars.

Output is JSON by default. Pipe to `jq` for filtering.

**Inspecting runs (most common use case):**
```bash
# List recent runs for a workspace
scalr get-runs -filter-workspace <workspace-id>

# List failed runs
scalr get-runs -filter-workspace <workspace-id> -filter-status errored

# Get run details (include plan and apply info)
scalr get-run -run <run-id> -include plan,apply

# View plan log (terraform plan output)
scalr get-plan-log -plan <plan-id>

# View apply log
scalr get-apply-log -apply <apply-id>
```

**Querying workspaces and environments:**
```bash
# List all workspaces (filter by name or environment)
scalr get-workspaces -filter-name "my-workspace"
scalr get-workspaces -filter-environment <env-id>

# Get workspace details
scalr get-workspace -workspace <workspace-id>

# List environments
scalr list-environments

# Get environment details
scalr get-environment -environment <env-id>

# Get workspace variables
scalr get-workspaces  # then inspect variables from workspace details
```

**Debugging workflow:** Find the workspace → list runs → get the failed run → read the plan/apply log.

**When to use:** Investigating failed Terraform runs, checking workspace configuration,
understanding environment structure. All creation and naming is managed via Terraform in a
separate repo — Scalr CLI is read-only inspection.

## Archie CLI — Service Integrations

Structured access to SaaS APIs. Outputs JSON to stdout, errors to stderr.
Credentials come from environment variables (e.g. `NOTION_TOKEN`, `LINEAR_TOKEN`).

### archie brain — Brain Operations

```bash
# Search the brain (multi-term ranked search)
archie brain search "term1" "term2"
archie brain search "terraform" --limit 5
archie brain search "apps" --type memory

# Read a file by path
archie brain read "_archie/memory/2026-05-29-apps.md"

# Recent memories
archie brain memory --project apps
archie brain memory --limit 5

# Index
archie brain index
archie brain index --type people
archie brain index --slug alice

# Reindex and commit
archie brain reindex
archie brain commit "brain: <description>" --paths <file1> --paths index.yaml

# Reference tracking
archie brain ref <path>
archie brain refs --top 10
archie brain refs --stale --since 90d
```

**When to use:** Searching for prior decisions, reading brain entries, writing and committing
brain files, reindexing after changes, tracking references.

### archie project — Project Detection

```bash
archie project              # resolve current project
archie project --config     # project config (issues provider, slack, etc.)
```

**When to use:** Determining the current project, resolving project configuration
(issue tracker, Slack channel, team settings).

### archie digest — Session Log Digestion

```bash
archie digest
```

**When to use:** Ensuring distilled session logs are up to date before memory extraction
or self-review.

### archie notion — Notion Integration

Communicates via the Notion MCP proxy. Requires `NOTION_TOKEN` env var.

**Reading pages and content:**
```bash
# Search the workspace (unrestricted by scope)
archie notion search "project notes" --limit 5

# Fetch a page
archie notion page <page-id>
archie notion page <page-id> --markdown
archie notion page "https://www.notion.so/Page-Title-<id>"
```

**Querying databases:**
```bash
# List available views
archie notion db <database-id> --views

# Query rows from a view (defaults to first view)
archie notion query <database-id> --columns Title,Status,Owner --limit 10
archie notion query <database-id> --view "Overview" --filter "Status=Done"
archie notion query <database-id> --filter "Owner!=Platform" --sort "Delivery:desc"
archie notion query <database-id> --filter "Initiative~=GitHub"
```

Filter operators: `=` (equals), `!=` (not equals), `~=` (contains).
Filtering, sorting, and column selection are post-processing on view results.

**Comments:**
```bash
archie notion comments <page-id>
```

**When to use:** Reading Notion pages for context, querying databases for project status,
searching the workspace for documentation. Prefer `archie notion query` with `--columns` and
`--limit` to keep output concise.

**Access scoping:** Config may restrict access to specific page subtrees. Search is always
unrestricted but page/database content operations check the page's ancestor chain against
the allowlist. If a fetch is rejected with a scope error, the page is outside the configured
access boundary.




### archie linear — Linear Integration

Direct GraphQL API. Requires `LINEAR_TOKEN` env var.

**Structure and context:**
```bash
# List teams and their workflow states
archie linear teams
archie linear team PLAT

# List projects
archie linear projects --team PLAT
```

**Issues:**
```bash
# List issues with filters (names resolved to IDs automatically)
archie linear issues --team PLAT --status "In Progress" --limit 10
archie linear issues --team PLAT --assignee "Simon" --label "Bug"

# Get full issue detail
archie linear issue PLAT-123

# Create and update
archie linear create-issue --team PLAT --title "Fix bug" --status "Ready" --priority 2
archie linear update-issue PLAT-123 --status "Done"
```

**Comments:**
```bash
archie linear comments PLAT-123
archie linear comment PLAT-123 --message "Looks good"
```

**File upload:**
```bash
archie linear upload ./screenshot.png
# Returns asset URL for embedding in descriptions/comments
```

**When to use:** Managing Linear issues, checking issue status, creating/updating issues,
adding comments. Use `archie linear team <key>` to discover available statuses before filtering
or updating. Prefer `--limit` to keep output concise.

### archie jira — Jira Cloud Integration

REST API v3 with scoped API tokens. Requires `JIRA_EMAIL`, `JIRA_TOKEN`, `JIRA_CLOUD_ID` env vars.

**Structure and context:**
```bash
# List projects
archie jira projects

# Get project details with issue types
archie jira project PLAT

# List statuses for a project
archie jira statuses PLAT
```

**Issues:**
```bash
# List issues with filters (composed into JQL)
archie jira issues --project PLAT --status "In Progress" --limit 10
archie jira issues --project PLAT --assignee "Simon" --type "Bug"

# Raw JQL for complex queries
archie jira issues --jql 'project = PLAT AND sprint in openSprints()'

# Get full issue detail
archie jira issue PLAT-123

# Create and update
archie jira create-issue --project PLAT --summary "Fix bug" --type Task
archie jira update-issue PLAT-123 --priority High

# Transition status (uses workflow transitions, not direct field update)
archie jira transition PLAT-123 --status "In Progress"
```

**Comments:**
```bash
archie jira comments PLAT-123
archie jira comment PLAT-123 --message "Looks good"
```

**Attachments:**
```bash
archie jira attach PLAT-123 ./screenshot.png
```

**When to use:** Managing Jira issues, checking issue status, creating/updating issues,
adding comments and attachments. Use `archie jira statuses <project>` to discover available
statuses before filtering or transitioning. Status changes use `transition`, not
`update-issue`. Prefer `--limit` to keep output concise.

### archie google — Google Workspace Integration

Read-only access to Gmail, Calendar, and Drive. Requires Google OAuth (`archie auth login google`).

**Mail:**
```bash
# Search emails (Gmail query syntax)
archie google mail search "from:jane subject:platform"
archie google mail recent --hours 8
archie google mail unread --limit 10

# Read and download an email
archie google mail read <message-id>
archie google mail read <message-id> --to-inbox
archie google mail read <message-id> --stdout
```

**Calendar:**
```bash
archie google calendar today
archie google calendar upcoming --days 3
archie google calendar event <event-id>
```

**Drive:**
```bash
# Search and list files
archie google drive search "roadmap"
archie google drive recent --days 1
archie google drive list --folder <folder-id>

# Fetch files (Docs → markdown, Sheets → CSV, binary → download)
archie google drive fetch <file-id>
archie google drive fetch <file-id> --to-inbox
archie google drive fetch <file-id> --stdout
archie google drive fetch <file-id> --format pdf
```

**When to use:** Reading emails for context, checking calendar for scheduling, fetching
documents and meeting transcripts for brain ingestion. Use `--to-inbox` to send files
directly to the brain raw ingestion directory for processing.

### archie slack — Slack Integration

Read channels and search messages via user token. Send messages via webhooks.
Requires `SLACK_WEBHOOK_URL` env var for sending. User token via `archie auth login slack` for reading.

**Reading channels:**
```bash
# List channels
archie slack channels

# Read recent messages
archie slack history "#platform" --since 24
archie slack history "#platform" --limit 20

# Read a thread
archie slack thread "#platform" 1776709000.123456

# Search messages (Slack query syntax, sorted by date)
archie slack search "from:jane aurora"
archie slack search "in:#platform after:2026-04-01"
```

**Users:**
```bash
archie slack users
archie slack users "simon"
```

**Sending messages:**
```bash
# Simple text message (supports mrkdwn)
archie slack send "Deploy complete :white_check_mark:"

# With header and fields
archie slack send "All checks passed" --header "Deploy Complete" --field "App=my-app" --field "Env=prod"

# Pipe text from another command
echo "Build finished" | archie slack send

# Raw Block Kit JSON from stdin
echo '{"text":"fallback","blocks":[...]}' | archie slack send --json
```

**When to use:** Sending notifications, alerts, and status updates to Slack channels.
Use `--header` and `--field` for structured messages, `--json` for full Block Kit control.

---

# Subagents

Prefer your own tools for small, direct operations such as reading a file, listing a
directory, viewing a directory tree, or running a single command. Do not delegate these.

Delegate only when delegation clearly improves execution quality, context hygiene, or task
separation. Typical reasons to delegate:
- the task is multi-step or open-ended
- the investigation will generate substantial output that would clutter the main context
- the work benefits from an isolated pass with a concise summary returned
- a specialised named agent is explicitly a better fit than the current agent

Use `general-purpose` for broad investigative work that does not match a specialised agent.

| Agent               | Use for |
|---------------------|---------|
| `general-purpose`   | Multi-step investigation, broad research, large-output analysis, summarised findings |
| `code-reviewer`     | Code quality review via `workflow-review` |
| `plan-reviewer`     | Plan quality review via `action-review-plan` |
| `qa-runner`         | Formatting, linting, and tests via `workflow-review` |
| `codebase-analyzer` | Deep codebase analysis via `action-analyze-codebase` |

Always set `agent_name: "general-purpose"` for non-specialised delegation.
Omitting `agent_name` defaults to `kiro-default`, which has restricted tool access
and may fail or underperform.
