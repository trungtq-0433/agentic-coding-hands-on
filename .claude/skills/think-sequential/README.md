# Sequential Thinking Agent Skill

A reflective, step-by-step way of working a problem — lifted out of the sequential-thinking MCP server and rebuilt as a native Agent Skill.

## Overview

The skill hands Claude a discipline for hard problems, with no external MCP tool in the loop. It covers:
- Splitting a tangled problem into a chain of thoughts you can reason about one at a time
- Letting the total thought count flex as the work tells you more
- Rewriting an earlier thought when a new insight breaks it
- Forking into parallel lines of reasoning when more than one route exists
- Floating a hypothesis and then testing whether it holds

## Skill Structure

```
sequential-thinking/
├── SKILL.md
│   The method, when it applies, how the scripts fit in
│
├── package.json
│   Test dependencies (jest)
│
├── .env.example
│   Configuration options
│
├── scripts/
│   ├── process-thought.js (executable)
│   │   Check a thought's structure and keep its history
│   │
│   └── format-thought.js (executable)
│       Render a thought for display (box/simple/markdown)
│
├── tests/
│   ├── process-thought.test.js
│   │   Validation, tracking, history tests
│   │
│   └── format-thought.test.js
│       Formatting tests (all formats)
│
└── references/
    ├── core-patterns.md
    │   The everyday revision & branching shapes
    │
    ├── examples-api.md
    │   API design example walkthrough
    │
    ├── examples-debug.md
    │   Performance debugging example
    │
    ├── examples-architecture.md
    │   Architecture decision example
    │
    ├── advanced-techniques.md
    │   Spiral refinement, hypothesis loops, branch convergence
    │
    └── advanced-strategies.md
        Working under uncertainty, cascading rewrites, meta-checks
```

**Scripts**: two executable Node.js helpers, each with tests.

## Key Features

### Progressive Disclosure Design
Every file owns one slice of the topic and is read only when that slice is needed:
- **SKILL.md**: the quick reference and the core method
- **core-patterns.md**: the moves you reach for daily
- **examples-*.md**: worked-through cases to learn from
- **advanced-*.md**: the heavier techniques for thorny problems

### Token Efficiency
- Explanations stay terse — grammar gives way to brevity
- Examples show the pattern instead of narrating it
- Files cross-link rather than repeat each other

### Methodology Conversion
Pulled out of the MCP server's design and recast as plain instructions:
- The MCP tool gave you an **interface** for sequential thinking
- This skill gives you the **method** for thinking sequentially
- Nothing external is required — it is instruction, not tooling

## Usage Modes

**Explicit Mode**: show the thought markers
```
Thought 1/5: [Analysis]
Thought 2/5: [Further analysis]
```

**Implicit Mode**: run the method in your head, no scaffolding in the output

## When Claude Should Use This Skill

Kicks in on its own for:
- Splitting a complex problem into parts
- Planning where you expect to backtrack
- Debugging and root-cause work
- Architecture and design calls
- Problems whose scope is still taking shape
- Long, context-heavy solutions

## Scripts Usage

### process-thought.js — checking and recording

```bash
# Process a thought
node scripts/process-thought.js --thought "Initial analysis" --number 1 --total 5 --next true

# Process with revision
node scripts/process-thought.js --thought "Corrected analysis" --number 2 --total 5 --next true --revision 1

# Process with branching
node scripts/process-thought.js --thought "Branch A" --number 2 --total 5 --next true --branch 1 --branchId "branch-a"

# View history
node scripts/process-thought.js --history

# Reset history
node scripts/process-thought.js --reset
```

### Format Thought (Display)

```bash
# Box format (default)
node scripts/format-thought.js --thought "Analysis" --number 1 --total 5

# Simple text format
node scripts/format-thought.js --thought "Analysis" --number 1 --total 5 --format simple

# Markdown format
node scripts/format-thought.js --thought "Analysis" --number 1 --total 5 --format markdown

# With revision
node scripts/format-thought.js --thought "Revised" --number 2 --total 5 --revision 1

# With branch
node scripts/format-thought.js --thought "Branch" --number 2 --total 5 --branch 1 --branchId "a"
```

### Running Tests

```bash
# Install dependencies (first time only)
npm install

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

## When to Use Scripts

**Reach for the scripts when**:
- You want each thought's structure checked deterministically
- You need the thought history kept on record
- You want formatted output for a document
- You are wiring sequential thinking into other tooling

**Skip them when**:
- You are just applying the method inline in a reply
- You want lightweight thinking with no overhead
- There is nothing to validate or persist

The scripts are **optional** — the method stands on its own without them.

## Source

Converted from: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking

Original MCP server by Anthropic (MIT License).
What the conversion does:
- Lifts the methodology out as instructions
- Adds executable scripts for deterministic validation
- Drops the external-tool dependency while keeping the behavior intact
