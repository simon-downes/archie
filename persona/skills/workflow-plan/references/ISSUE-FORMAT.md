# Issue Tracking Format

## Plan Storage

When an issue tracker is available, the plan lives in the issue description — no local
plan files are created. The issue identifier (e.g. PLAT-123, #42) is the plan identifier.

When no tracker is available, plans are stored as local files in `./plans/`.

## Issue Description as Plan

The full plan content (Objective, Requirements, Technical Design, Milestones) is written
as the issue description. The issue title is the plan title.

When updating an existing issue's description with a plan, the plan replaces the entire
description. If the original description contains important context, incorporate it into
the plan's Objective section.

## CLI Commands

**Linear:**
```bash
# Create issue with plan as description (pipe content via stdin for large plans)
echo "$PLAN_CONTENT" | ak linear create-issue --team PLAT --title "Plan title"

# Update existing issue description (stdin for large content)
echo "$PLAN_CONTENT" | ak linear update-issue PLAT-123

# Read issue (to load plan for implementation)
ak linear issue PLAT-123

# Update status during implementation
ak linear update-issue PLAT-123 --status "In Progress"
ak linear update-issue PLAT-123 --status "In Review"
```

**GitHub Issues:**
```bash
# Create issue with plan as description
gh issue create --title "Plan title" --body "$PLAN_CONTENT"

# Update existing issue
gh issue edit <number> --body "$PLAN_CONTENT"

# Read issue
gh issue view <number>
```
