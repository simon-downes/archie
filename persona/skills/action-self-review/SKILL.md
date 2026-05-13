---
name: action-self-review
description: >
  Analyse distilled session logs to identify behavioural patterns, tool usage issues,
  knowledge gaps, and workflow improvements. Produces a concrete recommendations plan
  with proposed changes to skills, soul, guidance, or documentation. Use when asked to
  "review yourself", "self-improve", "analyse recent sessions", "what can you do better",
  or "run self-review".
---

# Purpose

Analyse recent session logs and produce actionable recommendations for improving
agent behaviour, skills, tool usage, and knowledge. The output is a plan of proposed
changes — not a report.

---

# When to Use

- Periodic self-improvement ("review yourself", "self-improve")
- After a series of work sessions
- When explicitly asked to analyse behaviour or performance
- Weekly/fortnightly maintenance

# When Not to Use

- Memory extraction (use `action-memory-update`)
- Code review (use `workflow-review`)
- Inline corrections during conversation (just adjust behaviour directly)

---

# Workflow

## 1. Gather distilled logs

```bash
ak digest  # ensure logs are up to date
```

Read distilled session logs from `_archie/logs/` for the analysis period.

Default period: last 7 days. Adjust with user input ("last 2 weeks", "since Monday").

## 2. Read existing signals

```bash
yq '.[] | select(.date >= "YYYY-MM-DD")' ~/.archie/brain/_archie/signals.yaml
```

Read signals from the analysis period and earlier — these are low-priority
observations from previous reviews that may have accumulated enough to promote.

## 3. Analyse each dimension

Read the logs and investigate each dimension below. For each finding, apply the
quality filters before including it.

### Quality Filters — apply to every finding

1. **Minimum occurrence:** Don't recommend based on a single occurrence unless it's
   an explicit user instruction to change behaviour. Require 2+ instances across
   different sessions for patterns.

2. **Not already resolved:** If the session shows the issue being fixed (brain entry
   created, code corrected, user provided answer and agent adapted), skip it.

3. **Within agent control:** Environmental issues (filesystem permissions, network
   errors, expired tokens) are not behaviour improvements. Exclude them — unless the
   finding is about how the agent *responded* to the environmental error (e.g.
   attempting workarounds instead of reporting).

4. **The "so what" test:** If this change is made, what specifically improves in
   future sessions? If the answer is vague, drop it.

5. **Not already covered:** If an existing soul rule, skill, or guidance already
   addresses this, don't recommend it again unless the existing coverage is
   demonstrably failing (in which case recommend strengthening it).

### A. User corrections and pushback

Look for:
- User saying "no", "that's wrong", "actually...", "I said..."
- User redirecting after agent went in wrong direction
- User expressing frustration or repeating themselves
- Agent self-corrections ("you're right, I should have...")

Ask: What caused the mistake? Is it a pattern across sessions? What structural
change prevents it?

### B. Tool errors (learnable only)

Look for:
- Tools with `success: false` where cause is bad input or wrong assumption
- Repeated errors of the same type across sessions
- Agent attempting workarounds for environmental errors instead of reporting them

Skip: environmental errors, one-off typos, errors immediately self-corrected.

### C. Repeated workflows and scripts

Look for:
- Multi-line shell scripts that appear across multiple sessions
- Similar tool sequences repeated across different sessions
- Improvised multi-step processes that follow a consistent pattern

Ask: Should this be a skill? A script in an existing skill? A documented pattern?

### D. Skill and workflow adherence

Look for:
- Explicit user instructions about how skills should work
- Deviations from prescribed skill workflows (skipped steps, different order)
- Skills that are never used despite relevant sessions

Ask: Is the skill wrong, or is the agent not following it? What change fixes this?

### E. Knowledge gaps (unresolved only)

Look for:
- Agent making incorrect assumptions that weren't corrected in-session
- Repeated questions about the same topic across sessions
- Information the user keeps providing that should be in brain/skills

Skip: gaps that were filled during the session (brain entry created, answer found).

### F. Tool efficiency patterns

Look for:
- Repeated multi-line Python scripts doing the same thing across sessions
- Consistent patterns of multiple tool calls where fewer would suffice
- Trial-and-error sequences that suggest a better first approach exists

Ask: Is there a concrete, teachable improvement? (Not vague "could be better".)

## 4. Produce output

### Recommendations (high/medium priority)

For findings that meet the quality filters and warrant immediate action:

```markdown
### <Short title>

**Evidence:** <Session(s), what happened — specific, traceable>
**Root cause:** <Why this happened>
**Recommendation:** <Specific change to make>
**Target:** <soul.md | skill:<name> | brain:<path> | new-skill:<name>>
```

Priority criteria:
- **High:** 3+ occurrences OR explicit user instruction to change behaviour
- **Medium:** 2+ occurrences with clear improvement path

Maximum 8 recommendations. If more qualify, keep only the highest priority.

### Signal updates (low priority — accumulate)

For findings that don't yet meet the threshold but are worth tracking:

Append to `_archie/signals.yaml`:

```yaml
- date: "2026-05-12"
  session: <conversation-session-id>
  category: <tool-efficiency | behaviour | knowledge-gap | workflow | environmental-response>
  summary: "<what happened> — <brief context>"
```

The summary must be specific enough to match against future occurrences.

### Signal promotions

Check existing signals for entries that now have enough occurrences (3+) to
warrant a recommendation. If found, include as a recommendation and note which
signals it consolidates.

## 5. Write the recommendations file

Write to `_archie/reviews/YYYY-MM-DD.md`:

```markdown
---
name: Self-Review <date>
summary: <One-line summary of key findings>
period: <start date> to <end date>
sessions_analysed: <count>
recommendations: <count>
signals_added: <count>
signals_promoted: <count>
tags: [self-improvement, review]
---

# Self-Review — <date>

## Recommendations

### ...

## Signals Added

<list of new signal summaries>

## Signals Promoted

<any signals that hit threshold — include the recommendation above>
```

## 6. Commit

```bash
ak brain reindex
ak brain commit "review: self-review <date>" --paths _archie/reviews/ --paths _archie/signals.yaml --paths index.yaml
```

## 7. Report

Summarise: sessions analysed, recommendations count, signals added/promoted.

---

# Examples

**User:** "review yourself"

**Agent:** Analyses last 7 days, produces 3-5 recommendations and 2-4 new signals.

**User:** "review yourself for the last 2 weeks"

**Agent:** Wider window, more data, may promote signals from earlier reviews.
