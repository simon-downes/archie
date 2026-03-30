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

## Operations

Refer to Available Tools for the appropriate CLI commands for the issue tracker in use.

The key operations are:
- **Create issue** with title and description (plan content, piped via stdin for large plans)
- **Update issue description** (to revise the plan)
- **Read issue** (to load the plan for implementation)
- **Update issue status** (to reflect workflow progress: "In Progress", "In Review")
