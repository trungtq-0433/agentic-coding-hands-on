---
name: tkm:search-docs
description: Read what the makers wrote before you lean on their work — pull API references and framework documentation through context7. Reach for it when you need current library features, an API reference, a GitHub repository read, or any technical documentation lookup.
argument-hint: "[library-name] [topic]"
metadata:
  author: takumi-agent-kit
  version: "3.1.0"
module: documentation-knowledge
triggers: ["docs for X", "API reference", "how does X work in library Y", "latest docs"]
---

# Consulting the Guild Records

Behind any mature library sits a quiet archive: the makers' own specifications, the corner cases someone hit and wrote down, the working patterns handed down by the people who got there first. Skip that archive and you end up rebuilding what exists and re-learning what was already painful.

This skill runs **scripts first** to find documentation against the llms.txt standard. Let the scripts run — you do not assemble URLs by hand.

## Primary Workflow

**Run the scripts in this sequence, every time:**

```bash
# 1. Work out what kind of query this is (a single topic, or the whole library)
node scripts/detect-topic.js "<user query>"

# 2. Pull the docs, feeding in what the first script returned
node scripts/fetch-docs.js "<user query>"

# 3. Sort the results when more than one URL comes back
cat llms.txt | node scripts/analyze-llms-txt.js -
```

The scripts assemble the URLs, walk the fallback chain, and handle errors for you.

## Scripts

**`detect-topic.js`** — sorts the query
- Decides whether the ask is one feature or a whole library
- Pulls out the library name and the topic keyword
- Returns JSON: `{topic, library, isTopicSpecific}`
- Costs no tokens to run

**`fetch-docs.js`** — fetches the documentation
- Builds context7.com URLs on its own
- Walks the fallback: topic → general → error
- Prints the llms.txt content, or an error message
- Costs no tokens to run

**`analyze-llms-txt.js`** — reads through the llms.txt
- Buckets URLs as critical/important/supplementary
- Suggests how many agents to fan out (1 agent, 3 agents, 7 agents, phased)
- Returns JSON with the strategy
- Costs no tokens to run

## Workflow References

**[Topic-Specific Search](./workflows/topic-search.md)** — quickest route (10-15s)

**[General Library Search](./workflows/library-search.md)** — full coverage (30-60s)

**[Repository Analysis](./workflows/repo-analysis.md)** — what to do when llms.txt is missing

## References

**[context7-patterns.md](./references/context7-patterns.md)** — URL shapes and the repositories already mapped

**[errors.md](./references/errors.md)** — handling failures and walking the fallback chain

**[advanced.md](./references/advanced.md)** — corner cases, version pinning, multiple languages

## Execution Principles

1. **Let scripts go first** — run them rather than hand-build URLs
2. **No context tax** — scripts run without loading anything into context
3. **Fallback is built in** — scripts walk topic → general → error on their own
4. **Open references only as needed** — pull workflows and references when the task calls for them
5. **Fan-out advice** — scripts tell you how many agents to run in parallel

## Quick Start

**One feature:** "How do I use date picker in shadcn?"
```bash
node scripts/detect-topic.js "<query>"  # → {topic, library, isTopicSpecific}
node scripts/fetch-docs.js "<query>"    # → 2-3 URLs
# Read URLs with WebFetch
```

**Whole library:** "Documentation for Next.js"
```bash
node scripts/detect-topic.js "<query>"         # → {isTopicSpecific: false}
node scripts/fetch-docs.js "<query>"           # → 8+ URLs
cat llms.txt | node scripts/analyze-llms-txt.js -  # → {totalUrls, distribution}
# Fan out agents as the script suggests
```

## Environment

The scripts read `.env` in this order of precedence: `process.env` > `.claude/skills/docs-seeker/.env` > `.claude/skills/.env` > `.claude/.env`

The `.env.example` file lists what you can configure.
