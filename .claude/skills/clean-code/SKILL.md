---
name: tkm:clean-code
description: "Refine code for clarity without changing behaviour — extract repetition, rename for intent, drop dead code, flatten nesting. Reach for it after a feature lands and before review, to leave the work cleaner than the rush left it."
argument-hint: "[scope: recent|file-path|function]"
license: MIT
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: testing-code-quality
triggers: ["clean up code", "simplify", "refactor for clarity", "reduce complexity", "tidy this", "code smell"]
---

# Clean Code (匠)

The craftsman does not leave chisel marks. Once a feature works, there is a second
pass — make the code read the way it should have been written if there had been
no rush. Behaviour stays exactly the same; only the shape improves.

## When to reach for this

After implementation, before review. The work runs, the tests pass — now sand it
down. Not a rewrite, not a redesign: a clarity pass over what was just changed.

## How it runs

Hand the job to the `code-simplifier` subagent, scoped to what changed:

```
Task(subagent_type="code-simplifier",
     prompt="Simplify <scope> for clarity. Preserve ALL behaviour. ...")
```

Default scope is the recent changes; pass a file path or function name to narrow it.

`$ARGUMENTS` → scope (defaults to "recent changes").

## What to sharpen

- **Extract** repeated blocks into one named place (DRY).
- **Rename** variables/functions so intent reads off the name.
- **Delete** dead code, unused vars, commented-out husks.
- **Flatten** nested conditionals — early returns over arrow code.
- **Consolidate** duplicated logic into a single source of truth.

## The one rule

**Behaviour is frozen.** Every test that passed before must pass after, unchanged.
If a simplification would alter output, it is not a simplification — stop and flag
it. Report before/after complexity (lines, nesting depth, duplication) so the gain
is visible, not asserted.
