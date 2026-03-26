# Milestone Planning Guide

## Purpose

Break work into incremental, testable deliverables with enough technical context that an
implementor in a fresh session can execute without re-discovering decisions.

## Milestone Structure

Each milestone has four sections:

**Approach** — technical context that shapes how the work is done:
- Which libraries, tools, or patterns to use
- Where in the codebase this work fits (modules, files, existing patterns to follow)
- Constraints from the existing system
- ⚠️ Gotchas that could cause problems if missed

Approach answers: "given these tasks, here's what you need to know to do them right."

**Tasks** — concrete units of work to complete:
- Specific enough to track progress against
- In roughly the order they should happen
- Each task should be completable on its own
- Should not duplicate what's in Approach

Tasks answer: "here's what actually needs to get built."

**Deliverable** — single testable outcome:
- What's true when this milestone is complete
- Must be observable and verifiable
- Exactly one per milestone

**Verify** — how to confirm the deliverable:
- A command to run, a test to pass, a behaviour to observe
- Specific enough that the implementor knows exactly how to check

## Format

```
1. [Milestone objective]
   Approach:
   - [technical context, guidance, pattern to follow]
   - [library/tool choice and why]
   - ⚠️ [gotcha or high-stakes item]
   Tasks:
   - [concrete unit of work]
   - [concrete unit of work]
   Deliverable: [single testable outcome]
   Verify: [how to confirm]
```

## Rules

1. **Each milestone has exactly ONE deliverable**
   - Avoid compound deliverables ("X works AND Y works")

2. **Prefer smaller milestones over large ones**
   - Each milestone should feel achievable in a single session
   - Better to have 5 small milestones than 2 large ones

3. **Order by dependency**
   - Foundational work before dependent work
   - Infrastructure before features
   - Core functionality before enhancements

4. **No unresolved decisions**
   - The implementor should never need to choose a library or tool
   - The implementor should never need to decide where new code lives
   - The implementor should never need to establish a new pattern
   - If any of these are unresolved, add them to Approach

5. **Approach and Tasks don't overlap**
   - Approach is context and guidance (how and why)
   - Tasks are units of work (what)
   - Don't restate approach items as tasks

## Validation Checklist

Before presenting milestones, audit each one:

- [ ] Would the implementor need to choose a library or tool? → resolve in Approach
- [ ] Would the implementor need to decide where new code lives? → resolve in Approach
- [ ] Would the implementor need to establish a new pattern? → resolve in Approach
- [ ] Are Tasks specific enough to track progress?
- [ ] Is the Deliverable a single testable outcome?
- [ ] Does Verify give a concrete way to confirm?

## Good Examples

### Example 1: Rate Limiting

```
1. Set up Redis rate limit storage
   Approach:
   - Use ioredis client (already in project, see src/config/redis.ts)
   - Key format: ratelimit:{api_key}:{minute_bucket}
   - TTL matches rate limit window — counters self-expire
   Tasks:
   - Add rate limit config to src/config/index.ts (RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_SECONDS)
   - Create rate limit storage module in src/services/rate-limit-store.ts
   - Add unit tests for counter increment and expiry logic
   Deliverable: Rate limit counters increment and expire correctly in Redis
   Verify: Run rate limit store tests — counters increment, expire after window

2. Implement rate limiting middleware
   Approach:
   - Follow existing middleware pattern in src/middleware/auth.ts
   - Token bucket algorithm — check counter, increment, reject if over limit
   - ⚠️ Middleware order matters — register after CORS, before auth
   - On Redis failure: fail open (allow request), log error at warn level
   Tasks:
   - Create src/middleware/rate-limit.ts with token bucket logic
   - Register middleware in src/app.ts pipeline
   - Add integration test for rate limit rejection
   Deliverable: API returns 429 when rate limit exceeded
   Verify: Run test suite; send 101 requests in under a minute, confirm 429 on 101st

3. Add rate limit response headers
   Approach:
   - Add headers in the rate limit middleware (not a separate middleware)
   - Include on all responses, not just 429s
   Tasks:
   - Add X-RateLimit-Remaining header to all responses
   - Add X-RateLimit-Reset header to all responses
   - Add Retry-After header to 429 responses
   - Update integration tests to verify headers
   Deliverable: All responses include rate limit headers
   Verify: Run test suite; check headers on both allowed and rejected requests
```

### Example 2: Database Migration

```
1. Create migration infrastructure
   Approach:
   - Use existing knex migration framework (already configured in src/db/)
   - ⚠️ Target table has ~10M rows — column addition must not lock table
   - Strategy: add nullable column first, backfill in batches, then add NOT NULL constraint
   Tasks:
   - Create migration file for adding nullable column
   - Create backfill script in scripts/backfill-user-status.ts
   - Create follow-up migration for NOT NULL constraint
   Deliverable: Migration adds column without table locks
   Verify: Run migration against test database copy; confirm no lock wait timeouts

2. Update application code for new column
   Approach:
   - Update User model in src/models/user.ts
   - New column has default value 'active' — existing code paths don't need changes
   - Only new feature code reads/writes the column
   Tasks:
   - Add status field to User model and types
   - Update user creation to set status explicitly
   - Add status filter to user listing endpoint
   Deliverable: Application reads and writes the new status column
   Verify: Run test suite; create user via API, confirm status field in response
```

## Bad Examples

### Too Vague — No Approach

```
1. Build the rate limiter
   Tasks:
   - Implement rate limiting
   - Add tests
   Deliverable: Rate limiting works
   Verify: Test it
```

*Why bad: No approach — implementor must decide everything. Tasks are vague. Deliverable
and verify are not specific.*

### Approach Duplicates Tasks

```
1. Add Redis storage
   Approach:
   - Add Redis client configuration
   - Create rate limit key schema
   - Add TTL management
   Tasks:
   - Add Redis client configuration
   - Create rate limit key schema
   - Add TTL management
   Deliverable: Redis stores counters
   Verify: Run tests
```

*Why bad: Approach and Tasks say the same thing. Approach should explain how/why
(which client, what key format, why TTL). Tasks should list what to build.*

### Unresolved Decisions

```
1. Add request validation
   Approach:
   - Choose a validation library
   - Decide on validation strategy
   Tasks:
   - Research validation options
   - Implement validation
   Deliverable: Requests are validated
   Verify: Send invalid request, confirm rejection
```

*Why bad: "Choose a validation library" is an unresolved decision — this should have been
resolved during planning. The implementor should never need to research options.*

## Tips

### Breaking Down Large Work

If a milestone feels too large, ask:
- Can this be split into infrastructure + implementation?
- Can this be split into core functionality + enhancements?
- Can this be split into happy path + error handling?

### Writing Good Deliverables

Good deliverables answer: "what observable behaviour changes?"

Avoid: "Code is written", "Feature is complete", "Everything works"
Prefer: "API returns 429 when rate limit exceeded", "Users can log in via GitHub"

### Writing Good Verify Steps

Good verify steps answer: "how do I prove this works?"

Avoid: "Test it", "Check it works"
Prefer: "Run test suite", "Send POST to /api/users with invalid email, confirm 400 response"
