---
name: action-create-terraform-module
description: >
  Guided workflow for creating new Terraform/OpenTofu modules within a module collection.
  Walks through requirements gathering, opinionated defaults, and code generation following
  collection conventions. Use when creating a new Terraform module, scaffolding a module
  for a specific AWS service, or when asked to "create a module", "scaffold a module",
  or "new Terraform module".
---

# Purpose

Create production-ready Terraform modules through a guided process that enforces
consistency with existing collection patterns and opinionated security defaults.

---

# When to Use

- Creating a new Terraform module from scratch
- Scaffolding a module for a specific AWS resource/service
- Adding a module to an existing module collection

# When Not to Use

- Modifying an existing module (handle directly following policy-lang-terraform)
- Writing standalone Terraform configurations (not modules)
- Reviewing Terraform code (use workflow-review)

---

# Workflow

## 1. Discover Module Collection

**Find the module collection location:**
- Check existing context for module collection references
- Read README.md in current directory for collection information
- If not found, ask user for collection location

**Read collection conventions:**
- Parse the collection's README for local patterns (naming, structure, versioning, etc.)
- Note existing module patterns for consistency

## 2. Gather Requirements

**Module focus** — confirm the primary resource/service (e.g., S3 bucket, Lambda function)

**Initial features** — user will specify starting feature set

**Suggest additional features** — based on the resource type, suggest up to 5 common
features the user may have missed:
- Focus on frequently needed capabilities for that resource type
- Present as optional additions
- Let user accept/reject before proceeding

**Secondary functionality** — ask about cross-cutting concerns:
- Monitoring/observability (CloudWatch, Datadog, etc.)
- Backup/disaster recovery
- Security integrations
- Cost optimization features

## 3. Establish Opinionated Defaults

Ask about non-negotiable settings and sensible defaults for this resource type:
- **Security baselines** — settings that enforce security (e.g., "Should S3 buckets allow public access?")
- **Best practices** — organizational standards to enforce (e.g., "Should Aurora always use IAM auth?")
- **Hardcoded vs. configurable** — which settings should be opinionated vs. exposed as variables

**Examples of opinionated settings:**
- S3: Public access block always enabled, versioning default
- Aurora: IAM auth enabled, copy tags to snapshots, use local port
- Lambda: Architecture (arm64 vs x86_64), runtime version policy

**Distinction:**
- **Opinionated/hardcoded** — security, compliance, organizational standards
- **Configurable** — legitimate use-case variations (retention periods, instance sizes, feature flags)

## 4. Present Approach Summary

Before generating code, present a concise summary covering:
- Module scope and primary resources
- Confirmed feature set
- Opinionated defaults and hardcoded settings
- Secondary functionality to include
- Key design decisions and service-specific best practices
- How it aligns with collection conventions

**Wait for approval before proceeding.**

## 5. Generate Module Code

Create module following:
- **YAGNI principle** — only implement the specific features discussed
- **Opinionated by default** — hardcode security and compliance settings, expose only legitimate variations
- **Collection consistency** — match existing modules' structure, naming, and patterns
- **Service best practices** — apply AWS/provider-specific recommendations
- **Coding standards** — follow policy-lang-terraform for file organization, naming, structure

## 6. Review and Iterate

Present summary of what was created:
- Files generated
- Key variables and outputs
- Notable implementation decisions

Ask: "Does this look correct?"

Iterate based on feedback until approved.

---

# Key Principles

- **Simplicity over generality** — build for the specific use case, not every possible scenario
- **Opinionated by default** — enforce security and standards, expose only necessary configuration
- **Consistency** — match existing collection patterns
- **Clarity** — clear variable names, comprehensive descriptions, usage examples
