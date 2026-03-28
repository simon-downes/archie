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

## Agent Kit (ak)

CLI toolkit for structured access to SaaS APIs. Outputs JSON to stdout, errors to stderr.
Credentials come from environment variables (e.g. `NOTION_TOKEN`).

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


