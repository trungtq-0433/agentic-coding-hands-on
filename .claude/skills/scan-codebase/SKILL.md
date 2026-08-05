---
name: tkm:scan-codebase
description: "Read and map the codebase quickly using parallel agents — file discovery, context gathering, and cross-directory searches. Activate before any significant feature or investigation to understand what exists before changing it."
argument-hint: "[search-target] [ext] [--level low|medium|high|max]"
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
module: project-context-management
triggers: ["find files", "where is X", "what files do I need", "scan code", "map the codebase"]
---

# Reading the Workshop

Before shaping anything, the craftsman walks the workshop.
They read the layout — where materials are stored, how pieces relate, what tools are already in use.
This skill is that walk: fast, parallel, complete.

## Arguments

- Default: Survey using built-in Explore subagents in parallel (`./references/internal-scouting.md`)
- `ext`: Survey using external Gemini/OpenCode CLI tools in parallel (`./references/external-scouting.md`)

## When to Use

- Beginning work on a feature that spans multiple directories
- User mentions needing to "find", "locate", or "search for" files
- Starting a debugging session that requires understanding file relationships
- User asks about project structure or where functionality lives
- Before changes that might affect multiple parts of the codebase

## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | Parallel agents | Coverage | Cross-ref | Output |
|-------|----------------|----------|----------|--------|
| `low` | 2 | Key dirs | No | File list |
| `medium` *(default)* | 4 | Standard | Light | File + summary |
| `high` | 6 | Full | Yes | File + relationships |
| `max` | All dirs | Exhaustive | Dep graph | Full report |

## Quick Start

1. Analyze the user's prompt to identify what to look for
2. If `graphify-out/graph.json` exists (Knowledge Graph is on by default), read `../_shared/graphify-code-graph.md` and use graph-first discovery before broad Grep/Glob
3. Use Grep/Glob to confirm graph leads, fill gaps, and estimate codebase scale
4. Spawn parallel agents across divided directories when graph + local search are not enough
5. Collect results into a concise report

## Graph-Aware Discovery

When an existing Graphify graph is present, use it as the first-pass map:

- Read `graphify-out/GRAPH_REPORT.md` for corpus freshness, god nodes, import cycles, and communities
- Use `graphify query`, `graphify explain`, `graphify path`, and `graphify affected` to identify candidate files and relationships
- Then read source or run targeted grep to verify important claims
- If the graph is missing, stale, incomplete, or unavailable, continue with the normal scouting workflow

Load `../_shared/graphify-code-graph.md` for the exact command and verification rules.

## Configuration

Read from `.claude/.tkm.json`:
- `gemini.model` — Gemini model (default: `gemini-3-flash-preview`)

## Workflow

### 1. Analyze the Task

- Parse user prompt for search targets
- Identify key directories, patterns, file types, lines of code
- Determine the optimal number of subagents to spawn
- If `graphify-out/graph.json` exists (Knowledge Graph is on by default), derive the first candidate file/symbol set from graph queries before broad text search

### 2. Divide and Survey

- Split the codebase into logical segments per agent
- Assign each agent specific directories or patterns
- Ensure no overlap, maximize coverage
- For graph-derived scopes, assign agents by graph communities, affected files, or source directories, then ask them to verify with source reads

### 3. Register Survey Tasks

- **Skip if:** Agent count ≤ 2 (overhead exceeds benefit)
- **Skip if:** Task tools unavailable (VSCode extension) — use `TodoWrite` instead
- `TaskList` first — check for existing survey tasks in the session
- If not found, `TaskCreate` per agent with scope metadata
- See `references/task-management-scouting.md` for patterns and examples

### 4. Spawn Parallel Agents

Load the appropriate reference based on the decision tree:
- **Internal (Default):** `references/internal-scouting.md` (Explore subagents)
- **External:** `references/external-scouting.md` (Gemini/OpenCode)

**Notes:**
- `TaskUpdate` each task to `in_progress` before spawning its agent (skip if Task tools unavailable)
- Prompt detailed instructions for each subagent with exact directories or files it should read
- Each subagent has less than 200K tokens of context window — scope carefully
- Number of subagents depends on available system resources and file count
- Each subagent must return a detailed summary to the main agent

### 5. Collect Results

**IMPORTANT:** Invoke "/tkm:organize-files" skill to organize the outputs.

- Timeout: 3 minutes per agent (skip non-responders)
- `TaskUpdate` completed tasks; log timed-out agents in report (skip if Task tools unavailable)
- Aggregate findings into a single report
- List unresolved questions at end

## Report Format

```markdown
# Workshop Survey Report

## Relevant Files
- `path/to/file.ts` - Brief description
- ...

## Unresolved Questions
- Any gaps in findings
```

## References

- `../_shared/graphify-code-graph.md` — Existing Graphify graph consumption rules
- `references/internal-scouting.md` — Using Explore subagents
- `references/external-scouting.md` — Using Gemini/OpenCode CLI
- `references/task-management-scouting.md` — Claude Task patterns for survey coordination
