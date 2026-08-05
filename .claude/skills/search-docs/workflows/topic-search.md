# Searching for One Feature's Docs

**Reach for this when:** the user is after a single feature, component, or concept

**Speed:** ⚡ Fastest (10-15s)
**Token usage:** 🟢 Minimal
**Accuracy:** 🎯 Highly targeted

## Trigger Patterns

- "How do I use [FEATURE] in [LIBRARY]?"
- "[LIBRARY] [COMPONENT] documentation"
- "Implement [FEATURE] with [LIBRARY]"
- "[LIBRARY] [CONCEPT] guide"

## Workflow (Script-First)

```bash
# STEP 1: Execute detect-topic.js script
node scripts/detect-topic.js "<user query>"
# Returns: {"topic": "X", "library": "Y", "isTopicSpecific": true}

# STEP 2: Execute fetch-docs.js script (handles URL construction automatically)
node scripts/fetch-docs.js "<user query>"
# Script constructs: context7.com/{library}/llms.txt?topic={topic}
# Script handles fallback if topic URL fails
# Returns: llms.txt content with 1-5 URLs

# STEP 3: Process results based on URL count
# - 1-3 URLs: Read directly with WebFetch tool
# - 4-5 URLs: Deploy 2-3 Explorer agents in parallel

# STEP 4: Present findings
# Focus on specific feature: installation, usage, examples
```

## Examples

**The shadcn date picker:**
```bash
# Execute script (automatic URL construction)
node scripts/detect-topic.js "How do I use date picker in shadcn?"
# {"topic": "date", "library": "shadcn/ui", "isTopicSpecific": true}

node scripts/fetch-docs.js "How do I use date picker in shadcn?"
# Script fetches: context7.com/shadcn-ui/ui/llms.txt?topic=date
# Returns: 2-3 date-specific URLs

# Read URLs directly with WebFetch
# Present date picker documentation
```

**Next.js caching:**
```bash
# Execute scripts (no manual URL needed)
node scripts/detect-topic.js "Next.js caching strategies"
# {"topic": "cache", "library": "next.js", "isTopicSpecific": true}

node scripts/fetch-docs.js "Next.js caching strategies"
# Script fetches: context7.com/vercel/next.js/llms.txt?topic=cache
# Returns: 3-4 URLs

# Process URLs via 2 Explorer agents
# Present caching strategies
```

## Why It's Worth It

✅ Roughly 10x faster than pulling the full docs
✅ Nothing to filter out afterward
✅ Barely touches the context window
✅ The smoothest experience for the user

## Fallback

If the topic URL answers with a 404:
→ Drop down to [General Library Search](./library-search.md)
