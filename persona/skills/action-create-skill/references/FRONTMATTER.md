# Frontmatter Specification

All skills require YAML frontmatter at the top of SKILL.md.

## Required Fields

### name

- 1-64 characters
- Lowercase letters, numbers, and hyphens only
- Must not start or end with a hyphen
- Must not contain consecutive hyphens (`--`)
- Must match the parent directory name

### description

- 1-1024 characters
- Primary mechanism for skill activation
- Target 100-200 words for optimal matching
- See SKILL.md step 8 for writing guidance

## Optional Fields

### license

License name or reference to a bundled license file.

```yaml
license: Apache-2.0
```

### compatibility

Environment requirements. Max 500 characters.

```yaml
compatibility: Requires git, docker, jq, and access to the internet
```

### metadata

Arbitrary key-value mapping. Use unique key names to avoid conflicts.

```yaml
metadata:
  author: your-name
  version: "1.0.0"
```

### allowed-tools (experimental)

Space-delimited list of pre-approved tools.

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

## Example Frontmatter

```yaml
---
name: action-create-skill
description: >
  Create, improve, or refactor Kiro/Agent skills by generating complete skill
  folders with SKILL.md, references, examples, and clear workflows. Use this
  skill when creating a new skill, improving an existing SKILL.md, or fixing
  a skill that does not trigger reliably.
---
```
