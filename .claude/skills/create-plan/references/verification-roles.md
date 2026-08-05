# Verification Roles

Roles for checking a plan's claims against the actual codebase — not against how convincing the
prose reads.

**Loaded by:** `red-team-workflow.md` (the Evidence Filter needs somewhere to send reviewers for
method) and `validate-workflow.md` (the Verification Pass, run before the interview opens).

**Principle:** a plan earns trust by pointing at real files, not by sounding right.

## Claim Outcomes

Every claim a role checks lands in exactly one of these:

| Outcome | Meaning |
|---------|---------|
| `GROUNDED — file:line` | Search confirmed the claim; citation attached |
| `UNSUPPORTED — no match` | Search turned up nothing, or found something that contradicts the claim |
| `INCONCLUSIVE — needs a human call` | A mechanical check can't confirm or deny it |

## Role: Citation Checker

**Checks:** every file path, symbol, function, endpoint, or config key the plan cites.

**Method:**
- Sample a handful of claims per phase — start around 5-10, widen it if a phase leans heavily on
  external references
- Search the tree for the symbol (`rg "<symbol>"` or equivalent) to confirm it exists
- Glob the cited path to confirm it's real
- For endpoints, search the route table
- For config keys, search env files and config objects

**Watch for:** a name that reads plausibly (`AuthValidator`, `RequestManager`) but the search
returns nothing for; a "centralized" module that's actually scattered across the tree; a path the
plan cites that moved since whatever scouting pass produced it.

**Output:** `GROUNDED — file:line` | `UNSUPPORTED — no match` | `INCONCLUSIVE` per claim.

## Role: Consumer Auditor

**Checks:** interface changes (endpoints, function signatures, config schemas, exports) account
for every consumer, not just the ones the plan remembered.

**Method:**
- Search for the symbol (`rg "<function_name>"`) and list every caller by name — never write
  "update the callers," name them
- More than 10 callers → list the first 10 with `file:line`, state the total count
- Check downstream: tests that call it, imports, re-exports
- Check upstream: config files, env vars, CI scripts, CLI help text

**Watch for:** the plan claims 3 callers, the search finds 7; a re-exported type nobody updated;
CLI help text still naming a parameter the plan renames.

**Output:** caller list with `file:line`, a compatibility read, or `UNSUPPORTED` naming the callers
the plan missed.

## Role: Behavior Path Tracer

**Checks:** behavioral claims — "X triggers Y," "A runs before B," "the middleware guards the
handler" — the ones that sound obviously true and are wrong half the time.

**Method:**
- Start at the claimed entry point
- Read the actual path: entry → guard → branch → target
- Note every early return, chained callback, or event listener sitting in that path
- For async code, check the real ordering guarantee instead of assuming it resolves synchronously

**Watch for:** X and Y sharing no call path at all; a hop the plan skipped over (A calls C which
calls B, not A straight to B); async code the plan treats as if it resolves in order.

**Output:** the traced path with `file:line` citations, or `UNSUPPORTED` with the path that
actually runs instead.

## Cross-Phase Claim Reconciliation

**Purpose:** a validate or red-team pass fixes the phase it was looking at. This reconciliation
catches the phases it wasn't — the rename that only got applied once, the assumption reversed in
Phase 2 that Phase 5 still quotes.

Run it after any session that edits `plan.md` or a `phase-*.md` file.

**Procedure:**
1. Re-read `plan.md` and every `phase-*.md` after the edits land.
2. Build a short delta list from the session: renamed fields/APIs/files, reversed assumptions,
   reordered phases, changed dependencies or success criteria.
3. Search the plan directory for each delta's old name or term — a rename that only touched the one
   phase leaves the rest of the plan quoting the ghost.
4. Reconcile every section that references the changed item: the overview summary, phase
   requirements, implementation steps, success criteria, risk notes, and prior validation/red-team
   logs.
5. If the same draft (query, contract, command) appears embedded in more than one place, update
   every copy, not just the one the finding pointed at.
6. Anything that can't be reconciled with current evidence goes on an unresolved list. The plan
   does not clear for `takumi` while that list is non-empty.

**Output format** — append to the active `## Validation Log` or `## Red Team Review` section:

```markdown
### Cross-Phase Claim Reconciliation
- Files reread: plan.md, phase-01-..., phase-02-...
- Deltas checked: N
- Stale references reconciled: N
- Unresolved contradictions: N
```

## Wiring

- **Planner (self-check):** while drafting a phase, run the Citation Checker method inline; tag
  anything you can't confirm `[UNVERIFIED]` instead of guessing and moving on.
- **`validate-workflow.md`:** the Verification Pass runs the roles relevant to the plan's claims
  before the interview opens; `UNSUPPORTED` results turn into interview questions, and every
  `[UNVERIFIED]` tag gets resolved before the plan seals.
- **`red-team-workflow.md`:** each reviewer's findings need a `file:line` citation to survive the
  Evidence Filter; Cross-Phase Claim Reconciliation runs after accepted findings land.
