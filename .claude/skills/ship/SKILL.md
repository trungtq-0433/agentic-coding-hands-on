---
name: tkm:ship
description: "Send finished work out the door in one move — sync with the base branch, temper with tests, lint, audit licenses, inspect, commit, push, and open the PR. Carries a feature branch all the way to a PR URL. Reach for this once the work is done and earns its place in main."
argument-hint: "[official|beta] [--dry-run] [--skip-tests|review|journal|docs]"
license: MIT
metadata:
  author: takumi-agent-kit
  version: "2.0.0"
module: deployment-infrastructure
triggers: ["ship", "merge feature", "open PR", "feature is done", "ready to merge"]
---

# Ship: The Final Act of Craft

Nothing leaves the bench until it has earned its way past every checkpoint.
Ship is that last slow lap around the work before you hand it over.

One invocation takes a feature branch the whole distance. It runs on its own and only pauses when something genuinely needs your call — a broken test, a critical finding, or a version decision it shouldn't make alone.

**Lineage:** the `/ship` idea from Garry Tan's gstack, reworked here to run against any language or framework.

## Arguments

| Flag | Effect |
|------|--------|
| `official` | Aim at the project's main line (main/master). Runs everything, including docs and the session record |
| `beta` | Aim at a dev/beta line. Trims the pipeline and leaves docs untouched |
| (none) | Let the skill decide: base is main/master means official, anything else means beta |
| `--skip-tests` | Walk past the tempering pass — for when the suite already came back green |
| `--skip-review` | Walk past the pre-landing inspection |
| `--skip-journal` | Walk past the session record |
| `--skip-docs` | Leave the project docs as they are |
| `--dry-run` | Narrate each step but touch nothing |

## Ship Mode Detection

```
If argument = "official" → target = main/master (auto-detect default branch)
If argument = "beta"     → target = dev/beta (auto-detect dev branch)
If no argument           → infer from current branch naming:
  - feature/* hotfix/* bugfix/* → official (target main)
  - dev/* beta/* experiment/*  → beta (target dev/beta)
  - unclear                    → AskUserQuestion
```

## Where it hands the call back to you (blocking)

- Already standing on the target branch → bail out
- Merge conflicts it can't settle on its own → halt and lay the conflicts out
- A failing test → halt and surface what broke
- A lint error, license violation, policy deny, or official licenseal gap → halt and surface the report
- A critical finding from inspection → one AskUserQuestion per finding
- A bump that reaches into minor/major territory → AskUserQuestion

## Where it just keeps going

- Loose uncommitted work → folded into the ship every time
- A patch-level bump → decided on the spot
- The changelog entry → drafted for you
- The commit message → written for you
- No version file in sight → version step quietly skipped
- No changelog in sight → changelog step quietly skipped

## Pipeline

```
Step 1:  Pre-flight      → Read the branch, settle the mode, take stock, study the diff
Step 2:  Link Issues      → Track down or open the matching GitHub issues
Step 3:  Merge target     → Pull and fold in origin/<target-branch>
Step 4:  Temper           → Sniff out the test runner, run it, weigh the results (emit temper-results.json)
Step 5:  Lint code        → Run /tkm:lint-code and keep the SunLint report
Step 6:  Audit licenses   → Run /tkm:audit-licenses and keep JSON/Markdown reports
Step 7:  Inspect          → Walk the checklist twice (critical, then informational) (emit inspection-verdict.json)
Step 8:  Version bump     → Locate the version file, nudge patch/minor
Step 9:  Changelog        → Draft the entry from commits + diff
Step 10: Record           → Lay down a technical journal via /tkm:write-journal
Step 11: Docs update      → Refresh project docs via /tkm:manage-docs update (official only)
Step 12: Evidence gate    → Run the gate (hard stage) over {plan}/evidence — block the push if unproven
Step 13: Commit           → Conventional commit carrying version/changelog
Step 14: Push             → git push -u origin <branch>
Step 15: Create PR        → gh pr create with a structured body and linked issues
```

**Evidence gate (Step 12 — pre-push hard stage):** push is the true point of no return, so it is the hard stage. When an active plan with `{plan}/evidence/` exists, Steps 4 and 7 emit `temper-results.json` (code-constructed from `tester`'s raw runs) and `inspection-verdict.json` (`reviewer`, single writer) into that dir, then:

```bash
node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir "<abs {plan}/evidence>" --stage hard
# exit 2 → BLOCKED: surface the reasons, halt the push (do not commit/push unproven work)
```

If there is no active plan to gate, the evidence gate is skipped (note it in the output). Contract + artifacts: `claude/skills/_shared/references/evidence-artifacts.md`. `--skip-tests`/`--skip-review` downgrade the gate to advisory (warns, never blocks) since their artifacts are intentionally absent.

**Detailed steps:** Load `references/ship-workflow.md`
**Auto-detection:** Load `references/auto-detect.md`
**PR template:** Load `references/pr-template.md`

## Spending Tokens Wisely

- Steps 4 (temper) and 7 (inspect): hand off to the `tester` and `reviewer` subagents rather than doing the work in line
- Steps 10 (record) and 11 (docs): push them to the **background** so the pipeline keeps moving
- Step 2 (issues): roll the lookups into one `gh` call instead of a string of API hits
- Let the skip flags prune work you already know you don't need
- Beta mode drops the docs update (Step 11) without being asked
- Reuse what each step already printed — don't re-open files that are still in context

## Quick Start

`/tkm:ship` → run the whole pipeline, end on a PR URL.
`/tkm:ship beta` → aim at the dev branch with the trimmed pipeline.
`/tkm:ship official` → aim at main with the full docs and journal pass.

## Output Format

```
✓ Pre-flight: branch feature/search-filters, 4 commits, +180/-30 lines (mode: official)
✓ Issues: linked #71, created #72
✓ Merged: origin/main (up to date)
✓ Tempered: 58 passed, 0 failed
✓ Linted: SunLint grade A, 0 errors, 2 warnings
✓ Licenses: 124 dependencies, 0 violations, 0 policy denies
✓ Inspected: 0 critical, 1 informational
✓ Version: 2.4.0 → 2.4.1
✓ Changelog: updated
✓ Recorded: session journal written (background)
✓ Docs: updated (background)
✓ Evidence gate: SEALED (hard stage, 3 artifacts verified)
✓ Committed: feat(search): add faceted result filters
✓ Pushed: origin/feature/search-filters
✓ PR: https://github.com/org/repo/pull/210 (linked: #71, #72)
```

## House Rules

- **Tempering is not optional** unless `--skip-tests` says so. A red suite stops the line.
- **Quality gates run before inspection.** `/tkm:lint-code` blocks on lint errors. `/tkm:audit-licenses` blocks on license violations and policy denies in both beta and official modes.
- **Official is stricter.** In `official`, licenseal gaps block. In `beta`, lint warnings stay advisory, but license violations and policy denies still stop the line.
- **Evidence over promises.** When a plan is being shipped, the evidence gate (Step 12, hard stage) must exit 0 before the push. Unproven work — missing artifact, failed temper, a verdict that is not `SEALED` — halts the line the same way a red suite does.
- **No force pushing — ever.** Plain `git push` and nothing more.
- **Don't interrupt for confirmation** beyond critical findings and minor/major bumps.
- **Read the project, don't ask.** Test runner, version file, changelog shape, target branch — all inferred from the files on disk.
- **No language allegiance.** Node, Python, Rust, Go, Ruby, Java — anything with a test command is fair game.
- **Lean on the specialists.** `tester` does the tempering, `reviewer` does the inspection, `journal-writer` writes the record, `doc-writer` handles docs. Keep that work out of the main thread.
- **Off to the background.** The record and docs passes run async so they never hold up the ship.
