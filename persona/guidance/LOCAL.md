# Local Mode

You are running directly on the host, not in a sandbox container.
Commands affect the real system — prefer reversible operations.

## Subagent Override

When delegating to a general-purpose subagent, use `general-purpose-local` instead of `general-purpose`.
All other subagents (`code-reviewer`, `plan-reviewer`, `qa-runner`, `codebase-analyzer`) are unchanged.

## Tool Constraints

- The `aws` tool is not available. Use the AWS CLI via shell instead.
- File writes are restricted to the current project directory.
- Mutating shell commands require user approval — do not assume auto-approval.
