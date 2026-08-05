# Red Team Review

Put the plan in front of parallel reviewer subagents whose only job is to break it. Each one wears a different hostile lens. You then weigh what they found, and the user calls which fixes land.

**Mindset:** like paying someone who can't stand the implementer to take their work apart.

## Plan Resolution

1. `$ARGUMENTS` given → use that path
2. Otherwise read the `## Plan Context` section → use the active plan path
3. Still nothing → ask the user for a path, or to run `/tkm:create-plan` first

## Workflow

### Step 1: Read Plan Files
Read the whole plan directory:
- `plan.md` — overview, phases, dependencies
- `phase-*.md` — every phase file, in full

### Step 2: Scale Reviewer Count

| Phase Count | Reviewers | Lenses Selected |
|-------------|-----------|-----------------|
| 1-2 phases | 2 | Security Adversary + Assumption Destroyer |
| 3-5 phases | 3 | + Failure Mode Analyst |
| 6+ phases | 4 | + Scope & Complexity Critic (all lenses) |

### Step 3: Define Adversarial Lenses
Load: `references/red-team-personas.md`

### Step 4: Spawn Reviewers
Fire the reviewers off at once through the Task tool with `subagent_type: "reviewer"`.
Every reviewer prompt has to carry the override, the persona, the plan file paths, and the hostile instructions.
Load: `references/red-team-personas.md` for the reviewer prompt template.

**Codex companion reviewer (opt-in, `--codex-companion` only):**
When the flag is set, add a second, independent model (OpenAI Codex) as an extra red-team reviewer running
alongside the persona reviewers — an outside, different-model lens on the same plan.
- Probe: `claude/skills/_shared/scripts/codex-companion.sh probe plan-review`.
- `AVAILABLE` → `claude/skills/_shared/scripts/codex-companion.sh plan-review {plan-dir}`. Codex reads the plan
  files + the actual repo (read-only) and returns findings in the **same persona finding schema** (the
  `## Finding N:` block with a `**Evidence:** file:line` field), so they merge without conversion. The helper
  validates each citation **points at a real location** (file exists, line/range in bounds) and a valid severity,
  dropping the rest. This is a LOCATION check only — it does NOT prove the cited code supports the claim.
- Its findings join the persona findings at Step 5, tagged `[codex]`. They are NOT privileged — Step 6 (evidence
  present) and especially **Step 7 adjudication must still judge whether the cited lines actually back the claim**
  (a valid-but-unrelated citation is rejected there), and Step 8 gives the user the final call.
- **Degrade on ANY non-AVAILABLE signal** (`UNAVAILABLE:*` — missing/timeout/codex-failed/empty/no-grounded-findings):
  emit one warning line and run persona-only. Never block create-plan on a companion failure.
- Full contract (probe/degradation/discipline): `../_shared/codex-companion.md`.

### Step 5: Collect, Deduplicate & Cap
1. Gather every finding (persona reviewers + the Codex companion, if it ran)
2. Merge the ones that overlap — a finding raised by BOTH a persona and Codex is higher-confidence: keep it,
   note "confirmed by persona+codex". Tag each surviving finding with its source (`[claude]` / `[codex]`).
3. Order them by severity: Critical → High → Medium
4. Stop at 15

### Step 6: Evidence Filter
Before anyone weighs a finding's merit, check its `Evidence:` field for a `file:line` citation
(shaped like `src/auth/guard.ts:42` or a range `src/auth/guard.ts:42-58`). No citation → the
finding never reaches adjudication. Set its disposition to **Reject**, note it as "not grounded in
code", and move on — a hostile reviewer's opinion doesn't get graded on how persuasive it sounds,
only on what a search of the tree can confirm.

### Step 7: Adjudicate
Take each finding that cleared the Evidence Filter and call it: **Accept** or **Reject**.

### Step 8: User Review
Put it to the user through `AskUserQuestion`:
- "Looks good, apply accepted findings"
- "Let me review each one"
- "Reject all, plan is fine"

**If "Let me review each one":**
Walk every finding you marked Accept back through `AskUserQuestion`:
- Options: "Yes, apply" | "No, reject" | "Modify suggestion"

**If "Modify suggestion":**
Ask through `AskUserQuestion`: "Describe your modification to this finding's suggested fix:"
(the user types it in via the "Other" option)
Capture their version, and mark the disposition "Accept (modified)" in the Red Team Review table.

### Step 9: Apply to Plan
For the findings that land, edit the target phase files inline and drop a marker.
Add a `## Red Team Review` section to `plan.md`.

### Step 10: Cross-Phase Claim Reconciliation
See `references/verification-roles.md` — the "Cross-Phase Claim Reconciliation" procedure.

Applying accepted findings tends to fix the one phase a reviewer was looking at. This sweep
catches the phases nobody was looking at — re-read `plan.md` and every `phase-*.md`, build the
delta list from what just got accepted, and hunt down any stale term, superseded assumption, or
duplicate embedded draft the edit left behind elsewhere. Append the sweep's output to `## Red
Team Review`. If a contradiction survives the sweep, list it as unresolved — don't wave the plan
through to implementation with it still open.

## Output
- Findings counted by severity
- How many accepted versus rejected
- Which files changed
- Whole-plan consistency sweep results
- The key risks you closed off
- When the Codex companion ran: note each finding's source (`[claude]`/`[codex]`) in the `## Red Team Review`
  table, and flag any "confirmed by persona+codex" overlaps

## Next Steps (MANDATORY)
Point the user at `/tkm:create-plan validate`, then `/tkm:takumi --auto`.

## Important Notes
- Reviewers stay HOSTILE — they're not here to help
- Merge duplicates without mercy
- A finding with no `file:line` citation is dead on arrival — Step 6 rejects it before anyone
  argues its merit
- Every adjudication that survives the filter still rests on evidence
- Reviewers read the plan files for themselves
- Don't call the plan ready for `takumi` while the consistency sweep still has unresolved
  contradictions
