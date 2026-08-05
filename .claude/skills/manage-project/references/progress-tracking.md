# Progress Tracking

## Plan Analysis Workflow

1. **Read plans directory:** Glob `./plans/*/plan.md` to find every plan
2. **Parse YAML frontmatter:** Lift out status, priority, effort, branch, tags
3. **Scan phase files:** Tally `[x]` (done) against `[ ]` (still owed) in each phase
4. **Reconcile completed tasks:** Make sure every completed task's metadata shows up in the phase files — catch up the stale earlier phases first
5. **Calculate progress:** `completed / total * 100` per plan
6. **Cross-reference:** Hold the plan's tasks against what's actually been built

## Status Update Protocol

### CLI-First Status Updates (Preferred)

Lean on the `tkm plan` CLI commands — they change status deterministically and never mangle the format:

```bash
# Mark phase completed
tkm plan check <phase-id>

# Mark phase in-progress
tkm plan check <phase-id> --start

# Revert phase to pending
tkm plan uncheck <phase-id>

# Add new phase or sub-phase
tkm plan add-phase "Phase Name" [--after <id>]
```

The CLI rewrites both the `plan.md` table AND the phase file frontmatter in one move.
Plan-level status follows on its own: everything completed → `completed`, anything mid-flight → `in-progress`.

**Fallback:** No `tkm` CLI on hand? Edit `plan.md` by hand — touch only the Status column cell and leave the table structure untouched.

### Plan-Level Status

Set the `status` field in the `plan.md` frontmatter:

| Condition | Status |
|-----------|--------|
| No phases started | `pending` |
| Any phase in progress | `in-progress` |
| All phases complete | `completed` |

### Phase-Level Status

Every `phase-XX-*.md` keeps its state in checkboxes:
- `[ ]` = pending
- `[x]` = completed
- The ratio between them is the progress percentage

### Task-Level Status

Claude Tasks, session-scoped: `pending` → `in_progress` → `completed`

### Reconciliation Rule

When a later phase reads done but earlier phases still hold stale, unchecked-yet-completed items, catch those earlier phases up in the same sync pass — before you report any final status.

## Verification Checklist (evidence-backed)

Before you call a task complete, check against the **artifacts in `{plan}/evidence/`**, not against a prose promise. When a plan carries an `evidence/` dir, `task-completed-handler.cjs` already runs the validator (advisory) on `TaskUpdate(status: completed)` and surfaces any gaps — this checklist mirrors what that deterministic hook checks:

1. **Acceptance criteria met?** — `inspection-verdict.json` `acceptanceCovered` maps to the plan's criteria
2. **Code quality validated?** — `inspection-verdict.json` `decision == "SEALED"` (not just a high `score` — score never seals on its own)
3. **Tests passing?** — `temper-results.json` shows ≥1 command `status: "pass"` and **0** `status: "fail"`
4. **Documentation updated?** — Do the docs match what got built?
5. **No regressions?** — `inspection-verdict.json` `regressionChecked` non-empty, `reachableRegressions` empty

The hard block lives at the ship/Deliver gate (`evidence-gate.cjs --stage hard`); the completion hook is **advisory** — it informs, it does not stall task tooling. Artifact contract: `claude/skills/_shared/references/evidence-artifacts.md`.

## Report Generation

### Status Summary Template

```markdown
## Project Status: [Date]

### Active Plans
| Plan | Progress | Priority | Status | Branch |
|------|----------|----------|--------|--------|
| [name] | [X]% | P[N] | [status] | [branch] |

### Completed This Session
- [x] [description]

### Blockers & Risks
- [ ] [description] — [mitigation]

### Next Steps
1. [Priority action]
2. [Follow-up]
```

### Detailed Report Template

```markdown
## [Plan Name] - Detailed Status

### Achievements
- Completed features, resolved issues, delivered value

### Testing Status
- Components needing validation, test scenarios, quality gates

### Risk Assessment
- Potential blockers, technical debt, mitigation strategies

### Recommendations
- Prioritized next steps, resource needs, timeline projections
```

## Metrics to Track

- **Phase completion %** — How far each phase has gotten
- **Blocker count** — Open blockers holding progress back
- **Dependency chain health** — Any loops or stale links in the chain
- **Time since last update** — Which plans have gone quiet and need a look
- **Test coverage** — Test pass rates, feature by feature
