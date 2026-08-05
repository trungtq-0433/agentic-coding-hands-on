---
name: tkm:debug-code
description: "Locate the fault before you reach for a tool. Reach for this on bugs, failing tests, behavior that surprises you, slowdowns, call-stack tracing, layered validation, reading logs, broken CI/CD runs, database trouble, and wider system investigation."
languages: all
argument-hint: "[error or issue description] [--level low|medium|high|max]"
metadata:
  author: takumi-agent-kit
  version: "4.0.0"
module: bug-fixing-debugging
triggers: ["investigate", "why is X happening", "root cause", "strange behavior", "unexpected", "trace", "diagnose"]
---

# Finding the Flaw

Sand over a crack and the crack comes back — every time, until you chase it to where it began.
Each repair that misses the origin only leaves the work more brittle than you found it.

What this skill gives you is a disciplined hunt for that origin: follow the symptom back to its
source, prove the failure at each layer it passes through, and earn the word "fixed" with evidence.

## The Debug Law

**Prove the root cause before you change a single line.**

Guessing burns hours and seeds fresh defects. Pin down where the failure is actually born.
Repair it there. Confirm it holds at every layer. Show the evidence before you call it done.

## When to Use

**Code-level:** Failing tests, defects, behavior that surprises you, broken builds, integration snags
**System-level:** Server faults, broken CI/CD runs, things getting slower, database trouble, log reading
**Always:** Before you call any work finished

## Processing Level

Takes `--level low|medium|high|max` (default: `medium`).
Global semantics live in `_shared/processing-levels.md`.

| Level | Investigation depth | Task tracking | Parallel collection |
|-------|--------------------|--------------|--------------------|
| `low` | Root cause only (Phase 1) | No | No |
| `medium` *(default)* | Phase 1–2 + root cause tracing | No | No |
| `high` | Full 4-phase + defense-in-depth | Yes (3+ steps) | No |
| `max` | All techniques + perf diagnostics | Yes | Yes |

## Techniques

### 1. Systematic Debugging (`references/systematic-debugging.md`)

A four-phase discipline: Root Cause Investigation → Pattern Analysis → Hypothesis Testing → Implementation. Finish each phase before you move on. Nothing gets fixed until Phase 1 is done.

**Load when:** Any defect or issue that needs investigating and repairing

### 2. Root Cause Tracing (`references/root-cause-tracing.md`)

Walk the bug backward up the call stack until you reach the trigger that started it. Mend the source, never the symptom. Ships with `scripts/find-polluter.sh` to bisect test pollution.

**Load when:** Error buried deep in the stack, or you can't tell where bad data came from

### 3. Defense-in-Depth (`references/defense-in-depth.md`)

Check the data at every layer it crosses: Entry validation → Business logic → Environment guards → Debug instrumentation

**Load when:** Root cause is known and you want validation spanning all layers

### 4. Verification (`references/verification.md`)

**Iron law:** NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE. Run the command. Read what it prints. Then — and only then — state the result.

**Load when:** You're about to call work done, fixed, or passing

### 5. Investigation Methodology (`references/investigation-methodology.md`)

A five-step approach for system-level trouble: Initial Assessment → Data Collection → Analysis → Root Cause Identification → Solution Development

**Load when:** Server incidents, shifts in system behavior, failures crossing several components

### 6. Log & CI/CD Analysis (`references/log-and-ci-analysis.md`)

Pull and read logs from servers, CI/CD pipelines (GitHub Actions), and application layers. Tools: `gh` CLI, structured log queries, correlation across sources.

**Load when:** Broken CI/CD pipelines, server faults, deployment problems

### 7. Performance Diagnostics (`references/performance-diagnostics.md`)

Find the bottleneck, measure query cost, and shape an optimization plan. Covers database queries, API response times, and resource use.

**Load when:** Things getting slower, sluggish queries, high latency, resources running out

### 8. Reporting Standards (`references/reporting-standards.md`)

Diagnostic reports with a fixed shape: Executive Summary → Technical Analysis → Recommendations → Evidence

**Load when:** You need to write up an investigation or diagnostic summary

### 9. Task Management (`references/task-management-debugging.md`)

Track investigation pipelines through Claude Native Tasks (TaskCreate, TaskUpdate, TaskList). A hydration pattern for multi-step investigations with dependency chains and parallel evidence gathering. **Fallback:** Task tools run CLI-only — where they're missing (VSCode extension), fall back to `TodoWrite`. The debug workflow keeps working either way.

**Load when:** Investigation spans 3+ steps, parallel log collection, coordinating debugger subagents

### 10. Frontend Verification (`references/frontend-verification.md`)

Eyeball frontend work through Chrome MCP (Claude Chrome Extension), falling back to the `tkm:automate-browser` skill. Decide whether it's frontend → check Chrome MCP availability → screenshot plus console-error sweep → report. Not frontend? Skip it.

**Load when:** Work touches frontend files (tsx/jsx/vue/svelte/html/css), UI defects, visual regressions

## Quick Reference

```
Code bug       → systematic-debugging.md (Phase 1-4)
  Deep in stack  → root-cause-tracing.md (trace backward)
  Found cause    → defense-in-depth.md (add layers)
  Claiming done  → verification.md (verify first)

System issue   → investigation-methodology.md (5 steps)
  CI/CD failure  → log-and-ci-analysis.md
  Slow system    → performance-diagnostics.md
  Need report    → reporting-standards.md

Frontend fix   → frontend-verification.md (Chrome/devtools)
```

## Tools Integration

- **Database:** `psql` for PostgreSQL queries and diagnostics
- **CI/CD:** `gh` CLI for GitHub Actions logs and pipeline debugging
- **Codebase:** `tkm:search-docs` skill for package/plugin docs; `tkm:pack-codebase` skill for a codebase summary
- **Survey:** `/tkm:scan-codebase` or `/tkm:scan-codebase ext` to locate the files that matter
- **Frontend:** Chrome browser or the `tkm:automate-browser` skill for visual checks (screenshots, console, network)
- **Skills:** Reach for the `tkm:solve-problem` skill when a hard problem has you stuck

## Warning Signs

Catch any of these thoughts and walk back to the structured process:
- "Quick patch now, I'll dig in later"
- "Let me just tweak X and watch what happens"
- "Probably X — I'll change that"
- "Should be working now" / "Looks fixed"
- "Tests are green, call it done"

**Every one is the same signal:** return to systematic investigation. The shortcut that skips the process is exactly what plants the next defect.
