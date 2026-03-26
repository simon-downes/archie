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


