# Issue Tracking Format

## Plan File Header

When a plan is linked to an issue, the first line of the plan file is a comment with the
issue identifier:

```markdown
<!-- issue: PLAT-123 -->
# Plan Title

## Objective
...
```

This allows the implement skill to find the linked issue without parsing the plan content.

## Issue Description Embedding

Plan content is embedded in the issue description between boundary markers:

```markdown
Original issue description or summary here.

<!-- plan:start -->
## Objective
...
## Requirements
...
## Milestones
...
<!-- plan:end -->
```

### Updating an Existing Issue

When updating an issue that already has content:

1. Read the current description
2. If `<!-- plan:start -->` and `<!-- plan:end -->` markers exist, replace everything
   between them (preserving content before and after the markers)
3. If no markers exist, append the markers and plan content after the existing description
4. Write the updated description back

### CLI Commands

**Linear:**
```bash
# Create with description
ak linear create-issue --team PLAT --title "Plan title" --description "content"

# Update description (flag or stdin for large content)
ak linear update-issue PLAT-123 --description "content"
cat description.md | ak linear update-issue PLAT-123
```

**GitHub Issues:**
```bash
gh issue create --title "Plan title" --body "content"
gh issue edit <number> --body "content"
```
