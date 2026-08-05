---
name: tkm:manage-docs
description: "Keep the blueprint in sync with what was built — analyze codebase and manage project documentation. Use for init, update, and summarize workflows."
argument-hint: "init|update|summarize"
metadata:
  author: takumi-agent-kit
  version: "4.1.0"
module: documentation-knowledge
triggers: ["update docs", "document this", "README", "codebase summary", "sync docs"]
---

# Keeping the Ledger

A workshop without records is a workshop that cannot teach, cannot be handed over, and cannot recover from loss.
The ledger records what was built, why it was built that way, and what changed — so the next craftsman does not start blind.

Three moves on the same workbench: read the code, weigh what it tells you, then set down docs that hold. Scout, judge, write — in that order.

**IMPORTANT:** Invoke "/tkm:organize-files" skill to organize the outputs.

## Default (No Arguments)

When no argument arrives, the operation is ambiguous — so don't pick one for the user. Surface the choices through `AskUserQuestion`:

| Operation | Description |
|-----------|-------------|
| `init` | Analyze codebase & create initial docs |
| `update` | Analyze changes & update docs |
| `summarize` | Quick codebase summary |

Render those rows as `AskUserQuestion` options — header "Documentation Operation", prompt "What would you like to do?".

## Subcommands

| Subcommand | Reference | Purpose |
|------------|-----------|---------|
| `/tkm:manage-docs init` | `references/init-workflow.md` | Analyze codebase and create initial documentation |
| `/tkm:manage-docs update` | `references/update-workflow.md` | Analyze codebase and update existing documentation |
| `/tkm:manage-docs summarize` | `references/summarize-workflow.md` | Quick analysis and update of codebase summary |

## Routing

Take the first word of `$ARGUMENTS` and branch on it:
- `init` → Load `references/init-workflow.md`
- `update` → Load `references/update-workflow.md`
- `summarize` → Load `references/summarize-workflow.md`
- empty/unclear → AskUserQuestion (never silently fall through to `init`)

## Shared Context

The canonical home for documentation is the `./docs` directory:
```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
├── design-guidelines.md
├── deployment-guide.md
├── system-architecture.md
└── project-roadmap.md
```

Treat `docs/` as the single source of truth — everything else defers to it.

**IMPORTANT**: **Do not** start implementing code.

## References

- `references/init-workflow.md` — first-pass documentation creation
- `references/update-workflow.md` — refresh flow (Phase 2 picks up the layered `docs/` spec layer)
- `references/summarize-workflow.md` — fast codebase summary
- Canonical docs mapping: `claude/skills/_shared/docs-canonical-mapping.md` — layered model (`docs/system/`, `docs/generated/`, `docs/features/`, `docs/flows/`) and surgical-edit policy <!-- layout-exempt: reference to the canonical mapping itself -->
- Shared `doc-writer` prompt template: `claude/skills/takumi/references/subagent-patterns.md` → `## Documentation`
