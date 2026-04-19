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

## Agent Kit (ak)

CLI toolkit for structured access to SaaS APIs. Outputs JSON to stdout, errors to stderr.
Credentials come from environment variables (e.g. `NOTION_TOKEN`, `LINEAR_TOKEN`).

### ak brain — Second Brain Management

> The brain is always available. Check it for domain context before relying on
> general knowledge. Check `_memory/` for recent conversation history.

Query and manage the brain. No credentials required.

```bash
# List contexts
ak brain index

# Query a context's index
ak brain index shared
ak brain index shared --type knowledge
ak brain index shared --slug aurora-failover

# Rebuild index from filesystem
ak brain reindex shared

# Stage and commit specific files (preferred)
ak brain commit shared -m "brain: add aurora knowledge" \
  --paths knowledge/aurora-failover.md --paths index.yaml

# Stage and commit all changes
ak brain commit shared -m "brain: bulk update"

# Show status (raw pipeline + git changes)
ak brain status

# Validate structure and index integrity
ak brain validate

# Get project config
ak brain project my-app
```

**When to use:** Querying the brain index, rebuilding indexes after writes, committing
changes, checking brain status. For full-text search, use `rg` directly. For reading
and writing brain content, use the brain skills (`action-brain-read`, `action-brain-write`,
`action-brain-ingest`).

### ak notion — Notion Integration

Communicates via the Notion MCP proxy. Requires `NOTION_TOKEN` env var.

**Reading pages and content:**
```bash
# Search the workspace (unrestricted by scope)
ak notion search "project notes" --limit 5

# Fetch a page
ak notion page <page-id>
ak notion page <page-id> --markdown
ak notion page "https://www.notion.so/Page-Title-<id>"
```

**Querying databases:**
```bash
# List available views
ak notion db <database-id> --views

# Query rows from a view (defaults to first view)
ak notion query <database-id> --columns Title,Status,Owner --limit 10
ak notion query <database-id> --view "Overview" --filter "Status=Done"
ak notion query <database-id> --filter "Owner!=Platform" --sort "Delivery:desc"
ak notion query <database-id> --filter "Initiative~=GitHub"
```

Filter operators: `=` (equals), `!=` (not equals), `~=` (contains).
Filtering, sorting, and column selection are post-processing on view results.

**Comments:**
```bash
ak notion comments <page-id>
```

**When to use:** Reading Notion pages for context, querying databases for project status,
searching the workspace for documentation. Prefer `ak notion query` with `--columns` and
`--limit` to keep output concise.

**Access scoping:** Config may restrict access to specific page subtrees. Search is always
unrestricted but page/database content operations check the page's ancestor chain against
the allowlist. If a fetch is rejected with a scope error, the page is outside the configured
access boundary.




### ak linear — Linear Integration

Direct GraphQL API. Requires `LINEAR_TOKEN` env var.

**Structure and context:**
```bash
# List teams and their workflow states
ak linear teams
ak linear team PLAT

# List projects
ak linear projects --team PLAT
```

**Issues:**
```bash
# List issues with filters (names resolved to IDs automatically)
ak linear issues --team PLAT --status "In Progress" --limit 10
ak linear issues --team PLAT --assignee "Simon" --label "Bug"

# Get full issue detail
ak linear issue PLAT-123

# Create and update
ak linear create-issue --team PLAT --title "Fix bug" --status "Ready" --priority 2
ak linear update-issue PLAT-123 --status "Done"
```

**Comments:**
```bash
ak linear comments PLAT-123
ak linear comment PLAT-123 --message "Looks good"
```

**File upload:**
```bash
ak linear upload ./screenshot.png
# Returns asset URL for embedding in descriptions/comments
```

**When to use:** Managing Linear issues, checking issue status, creating/updating issues,
adding comments. Use `ak linear team <key>` to discover available statuses before filtering
or updating. Prefer `--limit` to keep output concise.

### ak jira — Jira Cloud Integration

REST API v3 with scoped API tokens. Requires `JIRA_EMAIL`, `JIRA_TOKEN`, `JIRA_CLOUD_ID` env vars.

**Structure and context:**
```bash
# List projects
ak jira projects

# Get project details with issue types
ak jira project PLAT

# List statuses for a project
ak jira statuses PLAT
```

**Issues:**
```bash
# List issues with filters (composed into JQL)
ak jira issues --project PLAT --status "In Progress" --limit 10
ak jira issues --project PLAT --assignee "Simon" --type "Bug"

# Raw JQL for complex queries
ak jira issues --jql 'project = PLAT AND sprint in openSprints()'

# Get full issue detail
ak jira issue PLAT-123

# Create and update
ak jira create-issue --project PLAT --summary "Fix bug" --type Task
ak jira update-issue PLAT-123 --priority High

# Transition status (uses workflow transitions, not direct field update)
ak jira transition PLAT-123 --status "In Progress"
```

**Comments:**
```bash
ak jira comments PLAT-123
ak jira comment PLAT-123 --message "Looks good"
```

**Attachments:**
```bash
ak jira attach PLAT-123 ./screenshot.png
```

**When to use:** Managing Jira issues, checking issue status, creating/updating issues,
adding comments and attachments. Use `ak jira statuses <project>` to discover available
statuses before filtering or transitioning. Status changes use `transition`, not
`update-issue`. Prefer `--limit` to keep output concise.

### ak slack — Slack Integration

Send messages via incoming webhooks. Requires `SLACK_WEBHOOK_URL` env var.

```bash
# Simple text message (supports mrkdwn)
ak slack send "Deploy complete :white_check_mark:"

# With header and fields
ak slack send "All checks passed" --header "Deploy Complete" --field "App=my-app" --field "Env=prod"

# Pipe text from another command
echo "Build finished" | ak slack send

# Raw Block Kit JSON from stdin
echo '{"text":"fallback","blocks":[...]}' | ak slack send --json
```

**When to use:** Sending notifications, alerts, and status updates to Slack channels.
Use `--header` and `--field` for structured messages, `--json` for full Block Kit control.
