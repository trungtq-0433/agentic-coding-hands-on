---
name: processing-levels
description: "Canonical processing level spec — reference convention loaded by skills that accept --level low|medium|high|max."
type: reference
version: "1.0.0"
---

# Processing Levels (kit-internal reference)

Single source of truth for the `--level low|medium|high|max` parameter. Not a tool — a **reference convention** that other skills import, analogous to `confidence`. Loaded by every skill that accepts `--level`. Update this file FIRST when changing level semantics — drift here counts as a breaking change for every consumer.

## Overview

`low/medium/high` appears in two distinct, unrelated contexts. They MUST NOT be confused:

- **Processing level** (input `--level`): controls **how hard the skill works** — depth, agent count, validation passes. The subject of this file.
- **Finding severity** (output labels `[LOW]/[MEDIUM]/[HIGH]/[CRITICAL]`): classifies **how bad a discovered finding is**. Unrelated to processing effort.

## Canonical Level Table

| Level   | Effort     | Parallel agents | User gates | Typical use                       |
|---------|------------|-----------------|------------|-----------------------------------|
| low     | Minimal    | None            | None       | Quick iteration, draft review     |
| medium  | Balanced   | Optional        | None       | Standard (default for all skills) |
| high    | Thorough   | Yes             | Pre-final  | Pre-merge, important decisions    |
| max     | Exhaustive | Multiple        | Multiple   | Security audits, critical releases|

## Default Rule

`medium` is the default for **every** skill unless the user explicitly specifies `--level`.

## Behavior Guidelines per Category

**Discovery skills** (`research`, `scan-codebase`, `brainstorm`):

- `low` → reduce source/agent count, skip cross-validation
- `medium` → standard depth
- `high` → more sources/agents, cross-validate, spawn parallel subagents
- `max` → exhaustive, multiple parallel subagents, adversarial probing

**Analysis/validation skills** (`review-code`, `audit-security`, `debug-code`, `predict-risks`):

- `low` → run quick-pass only (Stage 1 or equivalent)
- `medium` → standard pipeline (Stages 1+2 or equivalent)
- `high` → full pipeline including edge-case scan
- `max` → full pipeline + adversarial/auto-fix layers

## Integration Guide

Each consuming skill adds this section (replace the bracketed table with skill-specific behavior):

```markdown
## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | [Skill-specific behavior columns] |
|-------|-----------------------------------|
| `low` | ... |
| `medium` *(default)* | ... |
| `high` | ... |
| `max` | ... |
```

The `argument-hint` in the skill's YAML frontmatter must also append `[--level low|medium|high|max]`.

## Naming Collision Warning

`--level` (processing effort, **input**) and severity labels (**output**) share the words low/medium/high. Keep them separate:

- `--level max` = processing effort (input) — highest computational depth.
- `[CRITICAL]` = finding severity (output) — highest severity label.
- `[HIGH]` severity (output) ≠ `--level high` processing effort (input). A `--level low` quick pass can still report a `[CRITICAL]` finding.

When writing skill docs and output, never let one shadow the other.
