---
name: action-research
description: >
  Research a topic by finding, reading, and synthesising information from multiple
  sources. Produces a single markdown document in _inbox. Use when asked to "research",
  "investigate", "deep dive into", "find out about", "what are the best practices for",
  or when a question requires consulting multiple external sources rather than a quick
  answer. Not for simple factual questions answerable from a single search.
---

# Purpose

Go out, find the latest information on a topic from multiple sources, and produce
a single well-structured document ready for the user to read.

---

# When to Use

- User explicitly asks for research or investigation
- A question requires consulting multiple sources for a thorough answer
- User wants to understand a topic in depth before making a decision
- Comparing approaches, tools, or strategies

# When Not to Use

- Simple factual questions ("what's the default timeout?") — just search and answer
- Questions about the current codebase — read the code
- Questions about past conversations — use `action-brain-read`
- Writing or updating brain content — use `action-brain-write`

---

# Workflow

## 1. Clarify scope

Determine from the user's request:

- **Topic** — what to research
- **Sources** — specific sources to consult (optional)
- **Depth** — surface (3-5 sources, key findings) or deep (8-12 sources,
  comprehensive analysis). Default: surface.
- **Questions** — specific questions to answer (optional, helps focus)

If the request is clear, proceed. If ambiguous, ask one clarifying question
(e.g. "should I focus on AWS-specific approaches or general patterns?").

## 2. Find sources

If sources are provided, use them. If not, discover sources:

1. Web search for the topic — look for official docs, recent blog posts,
   authoritative guides
2. Prefer recent content (last 1-2 years) over older material
3. Prefer official documentation over community content
4. Aim for the target number of sources based on depth

### Source format

Sources can be specified as:

- **URLs** — fetch directly: `https://docs.aws.amazon.com/...`
- **`web:`** — web search: `web: "aurora postgresql failover best practices"`
- **`notion:`** — search Notion: `notion: "platform architecture"`
- **`linear:`** — fetch issue: `linear: PLAT-123`
- **`youtube:`** — search/fetch: `youtube: "aurora failover" channel:@BeABetterDev`

Dispatch based on the prefix using the corresponding tool from TOOLS.md.
If a source type isn't available (no credentials, tool not installed), skip
it and note the gap.

## 3. Read and analyse

Delegate the heavy reading to a `general-purpose` subagent. Provide:

- The topic and specific questions
- The list of source URLs/references to read
- Instructions to produce a structured markdown document

The subagent reads each source, extracts relevant information, and synthesises
into a coherent document.

### Subagent prompt template

```
Research the following topic and produce a structured markdown document.

Topic: {topic}
Questions to answer: {questions}

Sources to consult:
{sources}

For each source:
1. Read/fetch the content
2. Extract information relevant to the topic
3. Note the source URL and date for citation

Produce a single markdown document with:
- Title and one-paragraph summary at the top
- Sections organised by subtopic (not by source)
- Key findings, recommendations, or comparisons
- Citations: link back to sources inline or in a references section
- Note any conflicting information between sources
- Note when sources are dated and findings may be stale

Be thorough but concise. Aim for a document readable in 5-10 minutes.
Skip boilerplate and marketing language from sources — extract the substance.
```

## 4. Write output

Write the document to `~/.archie/brain/_inbox/<slug>.md` with frontmatter:

```markdown
---
topic: <topic>
date: <today>
depth: surface | deep
sources: <number of sources consulted>
---

# <Title>

<content>
```

Report to the user: topic, number of sources consulted, output location.
The user can then read it and optionally ingest it into the brain.

---

# Scoping Guidelines

Research is open-ended by nature. These constraints keep it focused:

- **Surface depth (default):** 3-5 sources, answer the core question, identify
  key trade-offs. Suitable for "I need to understand X before deciding."
- **Deep depth:** 8-12 sources, comprehensive analysis, compare approaches.
  Suitable for "I need to make an informed architectural decision about X."
- **Stop when the question is answered.** Don't keep searching for more sources
  once the core findings are clear and consistent across sources.
- **Note gaps rather than filling them endlessly.** "No authoritative source
  found for X" is a valid finding.

---

# Source Credibility

Not all sources are equal. Prefer:

1. Official documentation (AWS docs, language specs, tool docs)
2. Official blog posts (AWS blog, engineering blogs from known companies)
3. Recent conference talks and tutorials (last 1-2 years)
4. Well-regarded community content (high-quality blog posts, detailed guides)
5. Stack Overflow / forum answers (use for specific gotchas, not architecture)

Note when sources conflict. Note when content is dated (>2 years old).

---

# Example

**User:** "Research Aurora PostgreSQL failover strategies for multi-region"

1. Scope: surface depth, no specific sources provided
2. Web search: "aurora postgresql multi-region failover strategies 2025"
3. Find 4-5 sources: AWS docs on Global Database, AWS blog on failover,
   a re:Invent talk, a well-regarded engineering blog post
4. Subagent reads all sources, synthesises
5. Output: `_inbox/aurora-multi-region-failover.md`
6. Report: "Researched Aurora multi-region failover. 5 sources consulted.
   Document at `_inbox/aurora-multi-region-failover.md`."
