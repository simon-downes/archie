---
name: policy-lang-terraform
description: Standards for writing maintainable Terraform/OpenTofu infrastructure code. Use when working with .tf files, creating infrastructure, or when Terraform/OpenTofu is mentioned.
---

# Terraform/OpenTofu Coding Standards

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in RFC 2119.

## Scope

This document defines code structure, naming conventions, formatting standards, and resource construction patterns for Terraform/OpenTofu.

The following organisation-specific requirements are defined in a separate steering file:
- Tagging policies
- State backend configuration
- Environment/account strategy
- CI/CD pipeline requirements
- Security baselines
- Preferred modules
- Repository layout beyond Terraform module structure
- Common patterns

## Toolchain

**Always use `tofu` command instead of `terraform`** for all operations. OpenTofu is the preferred implementation.

## Code Quality Commands

- **`tofu fmt`** - Format Terraform files. **MUST be run before committing** (workflows reject unformatted code)
- **`tofu fmt --check --diff`** - Check formatting without modifying files (useful for CI validation)
- **`tofu validate`** - Validate Terraform syntax and configuration

## File Organization

### File Naming

**All Terraform files MUST be named using lower-kebab-case.tf**

Examples: `main.tf`, `lambda-processor.tf`, `api-gateway.tf`

### Standard Files

**Core files (always present):**

**`providers.tf`** - MUST exist in every Terraform project
- MUST contain `terraform` and `provider` blocks
- MUST NOT contain any other block types
- MUST specify provider versions using `~> <MAJOR>.<MINOR>` constraint
- Always check web for latest _stable_ version (training data may be outdated)

**`README.md`** - MUST exist in every Terraform project
- Documents module/project purpose and usage

**Conditional files (only when needed):**

**`variables.tf`** - MUST exist if project has any variables
- MUST contain ALL `variable` blocks
- MUST NOT contain any other block types
- Use only for externally provided variables (from environment `TF_VAR_*` or tfvars files)
- Omit if project has no variables

**`outputs.tf`** - MUST exist if project has any outputs
- MUST contain ALL `output` blocks
- MUST NOT contain any other block types
- Omit if project has no outputs

**`locals.tf`** - MAY exist if project has locals
- MUST contain only a single `locals` block
- MUST NOT contain any other block types
- Omit if locals are defined inline in resource files

**`data.tf`** - MAY exist for organizing data sources
- MUST contain only `data` blocks
- MAY contain one `locals` block
- Use when you have many data sources; otherwise define inline

### Resource Files

**Small projects:** Use `main.tf` for all resources

**Larger projects:** Split by logical grouping — by service (`dynamodb.tf`, `lambda-processor.tf`),
by component (`api.tf`, `database.tf`, `monitoring.tf`), or by layer (`frontend.tf`, `backend.tf`).
Choose ONE strategy and apply consistently. Keep related resources together (e.g., IAM roles
with the resources they support). Prefix related files: `lambda-processor.tf`, `lambda-consumer.tf`.

## Code Structure

### Block Ordering

**Within any file:**
1. `locals` blocks MUST be placed first
2. Only one `locals` block per file

**Variable block attributes** (in order):
1. `description`
2. `type`
3. `default`
4. `validation`

All variables MUST include `type` and `description` attributes.

**Output blocks** MUST include `description` attribute.

### Meta-Arguments

**Resource/module blocks:**
1. `count` or `for_each` as first argument (separated by newline)
2. All real arguments
3. `tags` as last real argument (before meta-arguments)
4. Meta-arguments in order: `depends_on`, `lifecycle`, `provider`

**Example:**
```hcl
resource "aws_lambda_function" "processor" {
  for_each = var.environments

  function_name = "${local.namespace}-processor"
  runtime       = "python3.11"
  handler       = "main.handler"
  role          = aws_iam_role.processor.arn
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.events.name
      LOG_LEVEL  = var.log_level
    }
  }

  tags = local.common_tags

  depends_on = [aws_cloudwatch_log_group.processor]

  lifecycle {
    create_before_destroy = true
  }
}
```

## Naming Conventions

### Resource Names

**Format:** `<namespace>-<purpose>`

Where `<namespace>` consists of:
- `<application>-<environment-key>-` for resources in default region (eu-west-1)
- `<application>-<environment-key>-<region-key>-` for resources outside default region

**Components:**
- `<application>` - Application name (from organizational standards)
- `<environment-key>` - 3-letter environment key (e.g., `dev`, `stg`, `prd`)
- `<region-key>` - 4-letter region code (e.g., `use1` for us-east-1, `euw2` for eu-west-2)
- `<purpose>` - Resource name/purpose in relation to the application

**Examples:**
```hcl
# Default region (eu-west-1) — no region key
resource "aws_s3_bucket" "uploads" {
  bucket = "${local.application}-${local.environment_key}-uploads"
  # Result: myapp-dev-uploads
}

# Non-default region — include region key
resource "aws_s3_bucket" "uploads_us" {
  bucket = "${local.application}-${local.environment_key}-use1-uploads"
  # Result: myapp-dev-use1-uploads
}
```

**Use kebab-case** for resource names. Use shorter alternatives when AWS service length restrictions apply.

Log groups follow AWS conventions: `/aws/lambda/${local.application}-${local.environment_key}-<name>`

### Variables and Locals

**Use snake_case** for variable and local names. Use descriptive names that clearly indicate purpose.

## Resource Tagging

**All resources MUST be tagged** according to the tagging policy defined in steering files.

**Always include:**
- `terraform` — repo and path to the Terraform source (e.g., `platform-core/my-service`).
  No org prefix.

**Additional required tags** (e.g., service/application, owner/team, environment/env) are
defined in steering files. If no steering file is loaded, ask the user about required tags.

**Tagging implementation:**
- Tag names MUST use lower-kebab-case (e.g., `environment`, `cost-center`)
- Tag values SHOULD be lower-case
- Define tags in `locals` and apply via provider `default_tags` for AWS resources
- Explicitly tag non-AWS provider resources

**Example:**
```hcl
locals {
  common_tags = {
    terraform = "platform-core/my-service"
    # Additional tags from steering file or user
  }
}

provider "aws" {
  default_tags {
    tags = local.common_tags
  }
}

# Non-AWS resources need explicit tags
resource "datadog_monitor" "api_errors" {
  # ... configuration ...
  tags = values(local.common_tags)
}
```

## IAM Policies

**Prefer inline policies on roles** via `aws_iam_role_policy`. Only create separate
`aws_iam_policy` resources when the policy will be attached to multiple roles.

**Prefer `jsonencode({})`** over `aws_iam_policy_document` data sources for policy documents.

**Example — role with inline policy:**
```hcl
resource "aws_iam_role" "processor" {
  name = "${local.namespace}-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "processor" {
  name = "processor-permissions"
  role = aws_iam_role.processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem"
      ]
      Resource = aws_dynamodb_table.events.arn
    }]
  })
}
```

When a policy is shared across multiple roles, extract to `aws_iam_policy` +
`aws_iam_role_policy_attachment`.

## Module Creation

For creating new Terraform modules, use the `action-create-terraform-module` skill which
provides a guided workflow for requirements gathering, opinionated defaults, and code
generation following collection conventions.

## Module Versioning

Terraform modules MUST follow semantic versioning (semver: MAJOR.MINOR.PATCH).

**Version bumps based on conventional commit types:**
- `major:` → MAJOR version bump (breaking changes)
- `feat:` → MINOR version bump (new functionality, backward compatible)
- `fix:` → PATCH version bump (bug fixes, backward compatible)
- `refactor:`, `docs:`, `chore:` → PATCH version bump (if released)

**Commit format follows tool-git-github skill conventions.**
