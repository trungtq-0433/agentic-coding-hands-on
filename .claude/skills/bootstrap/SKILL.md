---
name: tkm:bootstrap
description: "Stand up a brand-new project end to end — weigh the tech stack, lay down the structure, and put every foundation in place before a line of feature code is written. Modes: full (interactive), auto (default), fast (skip research), parallel (multi-agent)."
license: MIT
argument-hint: "[requirements] [--full|--auto|--fast|--parallel]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: implementation
triggers: ["new project", "start from scratch", "scaffold", "init project", "create new app"]
---

# Opening the Workshop

A new workshop starts with nothing — no tools laid out, no bench prepared, no material at hand. The craft of initialization is deciding what must exist before anything else can begin: the structure that will hold all subsequent work. What is set up here shapes everything that follows, so it must be done with intention.

**Guiding principles:** YAGNI, KISS, DRY · spend tokens like they cost money · keep reports tight

## Usage

```
/tkm:bootstrap <user-requirements>
```

**Flags** (optional, default `--auto`):

| Flag | Mode | Thinking | User Gates | Planning Skill | Takumi Skill |
|------|------|----------|------------|----------------|------------|
| `--full` | Full interactive | Ultrathink | Every phase | `--hard` | (interactive) |
| `--auto` | Automatic | Ultrathink | Design only | `--auto` | `--auto` |
| `--fast` | Quick | Think hard | None | `--fast` | `--auto` |
| `--parallel` | Multi-agent | Ultrathink | Design only | `--parallel` | `--parallel` |

**Example:**
```
/tkm:bootstrap "Build a SaaS dashboard with auth" --fast
/tkm:bootstrap "E-commerce platform with Stripe" --parallel
```

## Workflow Overview

```
[Git Init] → [Research?] → [Tech Stack?] → [Design?] → [Planning] → [Implementation] → [Test] → [Review] → [Docs] → [Onboard] → [Final]
```

Every mode pulls in its own workflow reference, then layers the shared phases on top.

## Mode Detection

When the caller names no flag, treat the run as `--auto`.

Pull in the matching workflow reference:
- `--full`: Load `references/workflow-full.md`
- `--auto`: Load `references/workflow-auto.md`
- `--fast`: Load `references/workflow-fast.md`
- `--parallel`: Load `references/workflow-parallel.md`

Whatever the mode, the tail end is common ground — load `references/shared-phases.md` to carry the run from implementation through to the final report.

## Step 0: Git Init (ALL modes)

First, see whether the directory is already under Git. If it is not:
- `--full`: check with the user before initializing → `git-manager` subagent (`main` branch)
- Others: initialize without asking via `git-manager` subagent (`main` branch)

## Skill Triggers (MANDATORY)

Once the front-loaded phases are behind you — research, tech stack, design — hand off to the downstream skills:

### Planning Phase
Hand the work to the **tkm:create-plan** skill, matching the flag to the mode you are running:
- `--full` → `/tkm:create-plan --hard <requirements>` (thorough research + validation)
- `--auto` → `/tkm:create-plan --auto <requirements>` (auto-detect complexity)
- `--fast` → `/tkm:create-plan --fast <requirements>` (skip research)
- `--parallel` → `/tkm:create-plan --parallel <requirements>` (file ownership + dependency graph)

What comes back is a path to the plan. Carry it forward into takumi.

### Implementation Phase
Now invoke the **tkm:takumi** skill, feeding it that plan path and the flag for your mode:
- `--full` → `/tkm:takumi <plan-path>` (interactive review gates)
- `--auto` → `/tkm:takumi --auto <plan-path>` (skip review gates)
- `--fast` → `/tkm:takumi --auto <plan-path>` (skip review gates)
- `--parallel` → `/tkm:takumi --parallel <plan-path>` (multi-agent execution)

## Role

A seasoned engineer who lives in system architecture and the decisions that shape it. Calls feasibility and trade-offs straight, without sugar-coating.

## Critical Rules

- Reach for catalog skills as the work calls for them
- Hold every research report to 150 lines or fewer
- Everything documentary lands in `./docs`
- Plans go to `./plans`, named per the `## Naming` section
- Never write code here yourself — route it through the planning and takumi skills
- Trade grammar for brevity in reports
- Close every report with any questions left open
- When the run wraps, capture a short technical journal entry with `/tkm:write-journal`

## References

- `references/workflow-full.md` - Full interactive workflow
- `references/workflow-auto.md` - Auto workflow (default)
- `references/workflow-fast.md` - Fast workflow
- `references/workflow-parallel.md` - Parallel workflow
- `references/shared-phases.md` - Common phases (implementation → final report)
