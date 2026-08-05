---
name: tkm:research
description: "Weigh the options before committing to one — multi-source technical research that ranks candidates and puts numbers on the trade-offs. Reach for it when sizing up a technology, hunting established practice, or stress-testing an architecture for scale, security, or longevity."
license: MIT
argument-hint: "[topic] [--level low|medium|high|max]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: implementation
triggers: ["research", "evaluate", "compare libraries", "best practice for", "what technology", "investigate options"]
---

# Studying the Material

A craftsman who cannot read the material cannot shape it.
Before any decision is made, the material must be understood —
its properties, its limits, its grain, and what others have learned working with it.

**Principles:** YAGNI, KISS, DRY | Honest findings over comfortable ones | Concise, actionable reports

## Study Methodology

### Stage 1: Define the Scope

Pin down the question before chasing answers:
- Name the terms and concepts the study turns on
- Decide how fresh the evidence has to be
- Settle on the bar a source must clear to count
- Draw the edges so the study stays as deep as it needs and no deeper

### Stage 2: Gather from Multiple Sources

No single source earns trust on its own. Pull from several and let them check each other.

1. **Search Strategy**:
   - **Gemini Toggle**: Check `.claude/.tkm.json` (or `~/.claude/.tkm.json`) for `skills.research.useGemini` (default: `false`). If `false` or absent, skip Gemini and use WebSearch directly.
   - **Gemini Model**: Read from `.claude/.tkm.json`: `gemini.model` (default: `gemini-3-flash-preview`)
   - If `useGemini` is `true`: first validate Gemini CLI works by running `command -v gemini && echo "ping" | timeout 15 gemini -y -m <gemini.model>`. If validation fails or times out, fall back to WebSearch and warn: "Gemini CLI unavailable, falling back to WebSearch. Set `skills.research.useGemini: false` in `.claude/.tkm.json` to suppress this check."
   - If validation passes, execute `echo "...your search prompt..." | timeout 180 gemini -y -m <gemini.model>` (timeout: 3 minutes) and save the output using `Report:` path from `## Naming` section (including all citations). If execution times out, fall back to WebSearch for that query.
   - If `useGemini` is disabled or `gemini` bash command is not available, use `WebSearch` tool.
   - Run multiple `gemini` bash commands or `WebSearch` tools in parallel to search for relevant information.
   - Write queries that bite — sharp keywords, not vague phrases
   - Salt them with terms like "best practices", "2024", "latest", "security", "performance"
   - Aim at the primary record: official docs, the source repositories on GitHub, writing that carries weight
   - Trust the sources others trust — maintainers' own docs, established organizations, practitioners with a track record
   - **IMPORTANT:** Perform at most **5 researches (max 5 tool calls)**. Respect any lower limit the user sets. Think carefully before each query.

2. **Deep Content Analysis**:
   - When a potential GitHub repository URL is found, use `tkm:search-docs` skill to read it
   - Go straight to the authoritative layer: official docs, API references, technical specs
   - Mine the README of repositories that show signs of active care
   - Walk the changelog and release notes to catch what changed between versions

3. **Video Content Study**:
   - Favor official channels, named practitioners, and the talks given at serious conferences
   - Watch for the hands-on demo and the production story over the slideware

4. **Cross-Reference Validation**:
   - Hold each claim up against sources that arrived at it independently
   - Read the dates — stale guidance reads like current guidance
   - Separate what the field agrees on from what it still argues about
   - Flag the contradictions and the debates that remain open

### Stage 3: Analyze and Synthesize

Turn the raw gathering into judgment:
- Spot the patterns that keep recurring and the practices that have settled into consensus
- Weigh each approach for what it costs against what it returns
- Gauge how mature and how stable each technology really is
- Surface the security exposure and the performance ceilings
- Work out what it takes to make the pieces fit together

### Stage 4: Produce the Study Report

**Notes:**
- Reports are saved using `Report:` path from `## Naming` section.
- If `## Naming` section is not available, ask the main agent to provide the output path.

Produce a comprehensive markdown report with this structure:

```markdown
# Study Report: [Topic]

## Summary
[2-3 paragraph overview of key findings and recommendations]

## Study Methodology
- Sources consulted: [number]
- Date range of materials: [earliest to most recent]
- Key search terms used: [list]

## Key Findings

### 1. Technology Overview
[Comprehensive description of the technology/topic]

### 2. Current State & Trends
[Latest developments, version information, adoption trends]

### 3. Established Practices
[Detailed list of recommended practices with explanations]

### 4. Security Considerations
[Security implications, vulnerabilities, and mitigation strategies]

### 5. Performance Characteristics
[Performance properties, optimization techniques, benchmarks]

## Comparative Analysis
[If applicable, comparison of different solutions/approaches]

## Recommendations

### Getting Started
[Step-by-step getting started instructions]

### Code Examples
[Relevant code snippets with explanations]

### Common Mistakes
[Errors to avoid and their remedies]

## Sources & References

### Official Documentation
- [Linked list of official docs]

### Recommended Reading
- [Curated list with descriptions]

### Community Resources
- [Forums, Discord servers, Stack Overflow tags]

### Further Study
- [Advanced topics and deep dives]

## Appendices

### A. Glossary
[Technical terms and definitions]

### B. Version Compatibility
[If applicable]

### C. Raw Study Notes
[Optional: detailed notes from the study process]
```

## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | Max searches | Cross-validation | Sub-agents | Deep content |
|-------|-------------|-----------------|-----------|-------------|
| `low` | 2 | No | None | No |
| `medium` *(default)* | 5 | Light | None | Optional |
| `high` | 8 | Full | Optional | Yes |
| `max` | Unlimited | Exhaustive | Parallel | Forced |

> The `IMPORTANT: Perform at most 5 researches` rule in Stage 2 applies at `medium`.
> `--level high` raises the cap to 8; `--level max` removes it.

## Standards of Study

Every piece of material that makes it into the report must clear these:
- **Accuracy**: Verified across multiple independent sources
- **Currency**: Prioritize information from the last 12 months unless historical context is needed
- **Completeness**: Cover all aspects requested
- **Actionability**: Provide practical, implementable recommendations
- **Clarity**: Clear language, defined terms, concrete examples
- **Attribution**: Always cite sources and provide links for verification

## Domain-Specific Considerations

- Security work: pull the recent CVEs and advisories before drawing conclusions
- Performance work: insist on benchmarks and real deployments, not claims
- Anything new: read the adoption curve and the support commitment before betting on it
- APIs: confirm the endpoints exist and the auth story is what the docs say
- Aging technology: never omit the deprecation notices and the migration path out

## Output Requirements

**IMPORTANT:** Invoke "/tkm:organize-files" skill to organize the outputs.

The study report must:
1. Be saved using the `Report:` path from `## Naming` section with a descriptive filename
2. Include a timestamp of when the study was conducted
3. Provide clear section navigation for longer reports
4. Use code blocks with appropriate syntax highlighting
5. Include diagrams or architecture descriptions where helpful (Mermaid or ASCII)
6. Conclude with specific, actionable next steps

**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.

The craftsman's report is not a data dump — it is strategic intelligence that shapes decisions.
Anticipate the follow-up questions. Cover the material completely. Stay focused and practical.
