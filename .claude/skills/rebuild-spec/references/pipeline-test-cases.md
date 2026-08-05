<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Test-Cases Pass (TC.1–TC.5)

Standalone pass. Loaded only when `--test-cases` flag is set. Requires feature specs to exist
first (same prerequisite class as `--flows`/`--glossary` — "feature specs must exist", identical
ABORT message pattern), but the fan-out shape is **per-feature, identical to FS.1** (one
researcher per F###, wave-chained ≤5) — NOT the cross-feature single-synthesis shape of
flows/glossary. Per-pass artifact isolation: RT-C2/RT-C3 (mirrors FS.2/FS.5 isolation).

Derives UT/IT/UAT test-case lists from each feature's ALREADY-CITED `technical-spec.md` +
`edge-cases.md` (+ optional `screens.md`/`business-context.md` for UAT) — an EXPAND-DETAILS pass,
not a new detection surface (mirrors `--jobs`' "re-projection, not re-detection" framing). Output
is a 5th per-feature file, `docs/features/{slug}/test-cases.md`, **SIDECAR** — never joins the
hard-gated `FEATURE_FILES` 4-tuple or the promotion gate (see `references/feature-spec-researcher-contract.md`
§ Sidecar Files).

## Preflight

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the
> pass dependency chain).

**Requires:** `docs/features/*/technical-spec.md` must exist for at least one feature (else
ABORT). `edge-cases.md` is promoted alongside `technical-spec.md` by the same FS.7 promote unit,
so its presence is implied — not re-checked independently.

```js
// Preflight — verify feature specs exist (shared ABORT class with flows/glossary)
const featureSpecFiles = glob("docs/features/*/technical-spec.md")
if (featureSpecFiles.length === 0) {
  throw new Error(
    "ABORT — No feature specs found under docs/features/. " +
    "Run /tkm:rebuild-spec --feature-specs first, then re-run --test-cases."
  )
}

// Incremental cursor check — pass-level, mirrors --jobs (NOT FS.1's per-fcode reverse-index;
// test-cases deliberately re-synthesizes ALL eligible features on any source change rather than
// tracking per-fcode affected-sets — a scope simplification, same class as flows'/glossary's
// "re-synth ALL on any change" behavior, not a regression from FS.1).
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const lastTestCasesSha = state.last_test_cases_run_sha ?? null
const shouldResynth = flags.full || !lastTestCasesSha || sourceChangedSince(lastTestCasesSha)
if (flags.full) {
  console.log("[INFO] --full: test-cases regenerating all outputs (cursor ignored)")
}
if (!shouldResynth) {
  console.log("[INFO] --test-cases: no source changes since last run — nothing to do. Use --full to force.")
  process.exit(0)
}

// Target set = every F### with a promoted technical-spec.md (full resynth this run).
const targetFcodes = featureSpecFiles
  .map(p => p.split("/")[2])   // docs/features/{fcode}/technical-spec.md → fcode
  .sort()
```

---

## Wave TC.1 — Test-cases fan-out (identical shape to FS.1)

Dispatches one `researcher` per F### in `targetFcodes` — ALWAYS bounded by the global 5-agent cap
(SKILL.md § GLOBAL PARALLEL CAP). ≤20 F###: one task per feature dispatched in chained waves of
≤`min(REBUILD_FS_BATCH_SIZE, REBUILD_MAX_PARALLEL)` (reuses the existing env — F10/YAGNI, no new
`REBUILD_TESTCASES_BATCH_SIZE`). >20 F###: batch tasks of `REBUILD_FS_BATCH_SIZE` features each,
dispatched sequentially.

```js
const TC_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? '5') || 5)
const MAX_PARALLEL = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
const TC_WAVE_WIDTH = Math.min(TC_BATCH_SIZE, MAX_PARALLEL)
const allTcTaskIds = []

if (targetFcodes.length <= 20) {
  let prevWaveIds = [], waveIds = []
  for (const [idx, fcode] of targetFcodes.entries()) {
    if (idx > 0 && idx % TC_WAVE_WIDTH === 0) { prevWaveIds = waveIds; waveIds = [] }
    const taskId = TaskCreate({
      subject: `WaveTC1: test-cases ${fcode}`,
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Derive UT/IT/UAT test cases for ${fcode} from its ALREADY-PROMOTED feature spec. CONTRACT:
references/test-cases-researcher-contract.md. TEMPLATE: templates/test-cases-template.md.

PRE-WRITE GUARD (idempotent):
bash: mkdir -p plans/<active-plan>/artifacts/features/${fcode}/

SOURCES (read from docs/, not artifacts/ — feature-specs pass already promoted these):
1. docs/features/${fcode}/technical-spec.md — BR-###/SM-###/DEC-###/DISC-### codes → UT/IT
2. docs/features/${fcode}/edge-cases.md — already test-case-shaped negative-path rows → UT/IT
3. docs/features/${fcode}/screens.md + docs/features/${fcode}/business-context.md (optional) —
   User Journey / What They Do → UAT scenarios

EXPAND, do NOT re-detect: every test case traces to a code/citation already present in the
sources above. NEVER invent a scenario with no upstream basis.

OUTPUT: plans/<active-plan>/artifacts/features/${fcode}/test-cases.md (ONLY this one file — do
NOT touch the other 4 files already in that folder). Zero derivable test cases for this feature
(rare) → still emit the file with an empty Test Cases note (never omit the file).
After completion, write plans/<active-plan>/artifacts/features/${fcode}/.test-cases-completed.
Call TaskUpdate(status=completed) on this task id BEFORE returning.`,
      addBlockedBy: prevWaveIds
    })
    waveIds.push(taskId)
    allTcTaskIds.push(taskId)
  }
} else {
  const batches = chunk(targetFcodes, TC_BATCH_SIZE)
  let prevBatchId = null
  for (const [i, batch] of batches.entries()) {
    const batchTaskId = TaskCreate({
      subject: `WaveTC1.batch-${pad2(i+1)}: test-cases (${batch[0]}..${batch.at(-1)})`,
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Derive UT/IT/UAT test cases for ${batch.length} features in parallel: ${batch.join(', ')}.
Apply the same rules as the small-codebase WaveTC1 block to EACH feature in this batch.
CONTRACT: references/test-cases-researcher-contract.md. TEMPLATE: templates/test-cases-template.md.
DRAFT (per feature): plans/<active-plan>/artifacts/features/{fcode}/test-cases.md ONLY.
On batch completion, write plans/<active-plan>/artifacts/tc1-batch-${pad2(i+1)}.flag listing completed F###.`,
      addBlockedBy: prevBatchId ? [prevBatchId] : []
    })
    allTcTaskIds.push(batchTaskId)
    prevBatchId = batchTaskId
  }
}
```

## Wave TC.2 — Deterministic validator

After ALL TC.1 tasks complete, run the deterministic validator. Own summary file
(`tc-validation-summary.json`, DISTINCT from `fs-validation-summary.json` — a test-cases FAIL
never masks a feature-specs FAIL, per RT-C2).

```js
// Preflight — every targetFcode must have produced its TC.1 completion sentinel before the
// validator runs (mirrors J.2's .job-list.completed marker-check style, applied per-feature).
const missingTcSentinels = targetFcodes.filter(
  fcode => !exists(`plans/<active-plan>/artifacts/features/${fcode}/.test-cases-completed`)
)
if (missingTcSentinels.length > 0) {
  throw new Error(
    `TC.2 HALT — .test-cases-completed sentinel absent for: ${missingTcSentinels.join(', ')}. ` +
    `TC.1 may not have completed for these feature(s). Re-run the missing WaveTC1 task(s) before retrying.`
  )
}

bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_test_cases.py \
  --plan-dir plans/<active-plan> \
  --project-root ${projectRoot} \
  --fcodes ${targetFcodes.join(',')} \
  --summary-out plans/<active-plan>/artifacts/validation/tc-validation-summary.json

read plans/<active-plan>/artifacts/validation/tc-validation-summary.json:
  if overall_status === "FAIL":
    for each fcode where validators.test_cases.{fcode}.status === "FAIL":
      spawn implementer task: "Fix validator issues in features/{fcode}/test-cases.md per tc-validation-summary.json"
      re-run validator for that fcode only
  // coverage_gap issues are WARN-only — they do NOT halt TC.3
```

## Wave TC.3 — Test-cases reviewer

After TC.2 passes (no FAIL), spawn reviewer batches — 5 features per reviewer, wave-chained ≤5,
mirroring FS.5.

```js
const TC_REVIEW_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? '5') || 5)
const reviewBatches = chunk(targetFcodes, TC_REVIEW_BATCH_SIZE)
const allTc3TaskIds = []
const TC3_WAVE_WIDTH = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
let prevTc3WaveIds = [], tc3WaveIds = []

for (const [i, batch] of reviewBatches.entries()) {
  if (i > 0 && i % TC3_WAVE_WIDTH === 0) { prevTc3WaveIds = tc3WaveIds; tc3WaveIds = [] }
  const tc3TaskId = TaskCreate({
    subject: `WaveTC3.batch-${pad2(i+1)}: test-cases-review (${batch[0]}..${batch.at(-1)})`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Review ${batch.length} test-cases.md drafts: ${batch.join(', ')}.
Load references/verification-checklist-universal.md + references/verification-checklist-test-cases.md.

CHECKLIST SECTION TARGETING: apply ONLY the TestCases rules (TC-S1..TC-S6). SKIP core/feature-spec
sections — those are handled by their own passes.

**TestCases validator pre-check (auto-injected):** TC.2 already checked TC### regex/uniqueness
(per-feature reset), Type∈{UT,IT,UAT}, Traces-to presence + citation-source-family match, coverage
gap (WARN). Mark deterministic-pass rule_ids [deterministic-pass] — skip them. Focus: semantic depth
(does the Given/When/Then actually match the cited code's behavior; UAT citation genuinely a
screens.md/business-context.md section, not a smuggled code-only citation).

Passed Checks: ONE LINE per rule (\`✓ <rule_id> @ <fcode>\`). NO prose.
Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/test-cases-review-batch-${pad2(i+1)}.md`,
    addBlockedBy: [...allTcTaskIds, ...prevTc3WaveIds]
  })
  tc3WaveIds.push(tc3TaskId)
  allTc3TaskIds.push(tc3TaskId)
}

// Merge batches → single review report (RT-M1 shape)
const mergedTcReport = mergeReviewBatches(
  `plans/<active-plan>/artifacts/test-cases-review-batch-*.md`,
  `plans/<active-plan>/artifacts/test-cases-review-report.md`
)
```

## Wave TC.4 — Scoped fix loop (optional)

If `test-cases-review-report.md` reports `failed > 0`, run a fix loop scoped to the affected
`test-cases.md` files only. Max 3 cycles — mirrors FS.6/J.4.

```js
const MAX_FIX_CYCLES = 3
let tcFailed = parseInt(parseFrontmatter(readFile("plans/<active-plan>/artifacts/test-cases-review-report.md")).failed ?? 0)
let tcFixCycle = 0
let lastTcReviewId = null  // set to the merge step above

while (tcFailed > 0 && tcFixCycle < MAX_FIX_CYCLES) {
  tcFixCycle++
  const issuesByFile = extractIssuesByFile(readFile("plans/<active-plan>/artifacts/test-cases-review-report.md"))
  const fixId = TaskCreate({
    subject: `WaveTC4.cycle-${tcFixCycle}.fix-test-cases`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Fix cycle ${tcFixCycle}/${MAX_FIX_CYCLES}. Issues: ${[...issuesByFile.values()].flat().join(' | ')}
Fix ONLY the listed test-cases.md files for the listed issues. Do NOT alter the other 4 feature files.`,
    addBlockedBy: lastTcReviewId ? [lastTcReviewId] : allTc3TaskIds
  })
  const reReviewId = TaskCreate({
    subject: `WaveTC4.cycle-${tcFixCycle}: re-reviewer`,
    description: `Re-verify fixed test-cases.md files after fix cycle ${tcFixCycle}.
Load references/verification-checklist-universal.md + references/verification-checklist-test-cases.md.
Overwrite plans/<active-plan>/artifacts/test-cases-review-report.md with fresh content.`,
    addBlockedBy: [fixId]
  })
  tcFailed = parseInt(parseFrontmatter(readFile("plans/<active-plan>/artifacts/test-cases-review-report.md")).failed ?? 0)
  lastTcReviewId = reReviewId
}

if (tcFailed > 0) {
  throw new Error(`ESCALATE: test-cases still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required.`)
}
```

## Wave TC.5 — Promote test-cases (SIDECAR — folds into `--scope features`)

**Promote scoping (verified, no new `--scope` literal needed):** `promote_drafts.py`'s Step 1.5
(`--scope features`) walks the ENTIRE `artifacts/features/{fcode}/` source directory with
`os.walk` and copies whatever files are present — it is **directory-scoped, not a fixed
filename list**. Since TC.1 writes ONLY `test-cases.md` into that per-feature draft folder (the
other 4 files are not re-drafted this pass), an incremental `--scope features` promote for the
affected fcodes copies test-cases.md into `docs/features/{fcode}/` alongside the pre-existing 4
files — additive, non-destructive. No `--scope test-cases` was added; F13/F15-class YAGNI.

```js
// Pre-flight gate
const tcvPath = `plans/<active-plan>/artifacts/validation/tc-validation-summary.json`
let tcValidatorOverall = "PASS"
if (existsNonEmpty(tcvPath)) {
  tcValidatorOverall = (JSON.parse(readFile(tcvPath)).overall_status ?? "PASS")
}
const tcFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/test-cases-review-report.md"))
const tcFailed2 = parseInt(tcFm.failed ?? 0)
if (tcValidatorOverall === "FAIL" || tcFailed2 > 0) {
  throw new Error(`TC.5 gate HALT — validator=${tcValidatorOverall}, review failed=${tcFailed2}. No docs/ writes.`)
}

// Actual promoted count for the completion handoff below — sourced from the validation summary
// (totals.passed_specs: specs that validated non-FAIL) rather than the naive targetFcodes.length.
// The gate above already guarantees zero FAIL specs by this point, but reading the real count
// off tc-validation-summary.json (the source of truth for what was actually validated and
// promoted) is more honest than assuming the pre-computed target list stayed accurate.
const tcPromotedCount = existsNonEmpty(tcvPath)
  ? (JSON.parse(readFile(tcvPath)).totals?.passed_specs ?? targetFcodes.length)
  : targetFcodes.length

// Promote — folds into the existing "features" scope (directory-scoped, additive).
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode incremental \
  --scope features \
  --affected-fcodes ${targetFcodes.join(',')}

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always.
for (const fcode of targetFcodes) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
    --artifact ${docs_root}/features/${fcode}/test-cases.md --project-root .
}

// Update per-pass cursor (--cursor test-cases advances last_test_cases_run_sha ONLY)
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor test-cases

// [F9] Write pass-specific completion flag — enumerated in SKILL.md Resume & Reconcile
bash: echo "# TC.5 complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/test-cases-complete.flag
bash: echo "# Scope: test-cases (docs/features/{slug}/test-cases.md)" >> plans/<active-plan>/artifacts/test-cases-complete.flag
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/test-cases-complete.flag

// [v5.3.3] Auto-sync secondary languages. docs/features/ already covered by
// _translation_sync_lib.py::_DOC_AREAS ("features", "*/*.md") — no registry change needed (F2).
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass test-cases --plan-dir plans/<active-plan>
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass test-cases --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Test-Cases Pass-completion handoff prompt

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write
`translation-sync-report.json` before this handoff. Echo the `Secondary languages:` line
VERBATIM — see `references/pipeline-translate.md § Auto-Sync Secondary Languages`.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass test-cases` BEFORE writing
the completion flag or printing this handoff. Exit 1 BLOCKS completion.

```
─── test-cases pass complete ───
Promoted: docs/features/{F###}/test-cases.md (UT/IT/UAT scenarios) for ${tcPromotedCount} feature(s)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Do the test cases actually cover the feature's business rules and edge cases?"
Next:
  /tkm:write-journal             # Record this milestone
```

## Test-Cases Pass — Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | `plans/<active-plan>/artifacts/validation/tc-validation-summary.json` |
| Review report | `plans/<active-plan>/artifacts/test-cases-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/test-cases-complete.flag` |

## Test-Cases Pass — Reconcile `expectedOutput` (F9)

Resume/reconcile preflight for this pass checks: `test-cases-complete.flag` present OR at least
one `docs/features/*/test-cases.md` exists and non-empty. `expectedOutput` =
`docs/features/{slug}/test-cases.md` (per-feature; no single canonical path — mirrors FS.7's
per-fcode reconcile shape, not J.5's single-file shape).

## Test-Cases Pass — Subagent contracts

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| TC.1 | `researcher` (1/feature in chained waves of ≤5, or 5/batch sequential) | `docs/features/{fcode}/{technical-spec,edge-cases}.md` (+ optional screens/business-context) + `test-cases-researcher-contract.md` + `test-cases-template.md` | `plans/<active>/artifacts/features/{fcode}/test-cases.md` + `TaskUpdate(status=completed)` |
| TC.2 | orchestrator (`validate_test_cases.py`) | `test-cases.md` drafts | `tc-validation-summary.json` |
| TC.3 | `reviewer` (5/batch, wave-chained ≤5) | `test-cases.md` batches + `verification-checklist-test-cases.md` | `test-cases-review-batch-NN.md` → merged into `test-cases-review-report.md` |
| TC.4 | `implementer` + `reviewer` | review report + affected `test-cases.md` | fixed `test-cases.md` |
| TC.5 | orchestrator (`promote_drafts.py --scope features`) | `test-cases.md` drafts | `docs/features/{fcode}/test-cases.md` + `test-cases-complete.flag` + state update (`last_test_cases_run_sha`) |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input
happen afterward.
