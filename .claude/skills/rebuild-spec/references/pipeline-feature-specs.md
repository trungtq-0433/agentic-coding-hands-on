<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Feature-Specs Pass (FS.1–FS.7)
<!-- Updated: Validation 2026-06-01 - three-pass model; feature-specs is a standalone pass -->
Standalone pass. Loaded only when `--feature-specs` flag is set (or `--features F###` for a scoped subset). See `pipeline.md` for wave dep graph. Per-pass artifact isolation: RT-C2/RT-C3.

## Feature-Specs Pass (`--feature-specs`)

Standalone pass — runs independently of the main (core) pipeline.
**Requires:** `docs/generated/feature-list.md` present and non-empty (else ABORT — see preflight step 1 for the standardized message).

**`--features F###,...` (scoped subset):** [BEHAVIOR CHANGE v5] `--features` now runs this standalone feature-specs pass for the listed F### only (was: default-pipeline W6 narrowing). A one-time notice is emitted on each invocation: `[BEHAVIOR CHANGE v5] --features now runs the standalone feature-specs pass (was: default-pipeline W6 narrowing)`. Scoped runs do NOT synthesize flows or glossary — those are separate passes (`--flows`, `--glossary`). This dissolves RT-H3: no cross-feature work inside a subset run.

Invocation:
```
/tkm:rebuild-spec --feature-specs              # all F### from feature-list.md
/tkm:rebuild-spec --features F001,F002,F005    # scoped subset (warn + proceed)
```

### Preflight

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the pass dependency chain).

1. Verify `docs/generated/feature-list.md` exists and is non-empty. ABORT if missing:
   `"ABORT — docs/generated/feature-list.md missing. Run /tkm:rebuild-spec (core pass) first, then re-run --feature-specs."`
2. **[RT-C1] Resolve fcodes to process:** (evaluate in order — first match wins)
   - If `--features F###,...` arg present: emit `[BEHAVIOR CHANGE v5]` notice; use the listed fcodes as the target set. The explicit set is always fully regenerated (cursor ignored), so `--full` adds nothing here — `--features` wins over `--full` when both are passed.
   - Else if `--full` present: skip reverse-index resolution entirely — treat ALL fcodes as affected, ignoring the incremental cursor (pass-scoped `--full`). Log `[INFO] --full: feature-specs regenerating all outputs (cursor ignored)`.
   - Else if `docs/_source-to-fcode.json` present and `last_feature_spec_run_sha` set in state: read reverse-index and resolve affected fcodes from changed source since last run.
   - Else (first run OR index absent): treat ALL fcodes as affected — never halt. Log `[INFO] feature-specs: no reverse-index / first run — processing all fcodes`.
   - Slug source: `docs/_source-to-fcode.json` → `plans/<active-plan>/artifacts/_canonical-fcodes.json` → fallback parse `docs/generated/feature-list.md` hierarchy rows with `^\|\s*(F\d{3}_\w+)\s*\|`.
3. **[RT-M2] Hydrate canonical upstream paths** via `claude/skills/_shared/docs-canonical-mapping.md`:
   - data-model → `docs/generated/entities.md`
   - screen-list → `docs/generated/screen-list.md` (if present; optional for this pass)
   - feature-list → `docs/generated/feature-list.md`
   - business-rules → `docs/system/business-rules.md` (if present)
   - flows → `docs/flows/*.md` (if present; read-only context)
   ABORT if `docs/generated/entities.md` is missing (data-model is required for feature-spec depth).
4. Check sibling stale markers and emit nudge:
   - If `docs/flows/.stale` exists: `[NOTE] --flows also stale — run /tkm:rebuild-spec --flows after this pass.`
   - If `docs/system/.glossary.stale` exists: `[NOTE] --glossary also stale — run /tkm:rebuild-spec --glossary after this pass.`
5. Ensure output dirs exist: `plans/<active-plan>/artifacts/features/`, `plans/<active-plan>/artifacts/validation/`, `plans/<active-plan>/artifacts/_feature-entry-points/`.

### Wave FS.1 — Feature-spec fan-out (former W6)

Dispatches one `researcher` per F### in the resolved target set — ALWAYS bounded by the global 5-agent cap (SKILL.md § GLOBAL PARALLEL CAP). ≤20 F###: one task per feature dispatched in **chained waves of ≤`min(REBUILD_FS_BATCH_SIZE, REBUILD_MAX_PARALLEL)`** (both default 5; legacy `REBUILD_W6_BATCH_SIZE` still honored as a deprecated alias) — every task of wave i+1 is `addBlockedBy` ALL tasks of wave i, so at most 5 researchers are ever runnable at once; raising the batch-size env can never widen a wave past the global cap. >20 F###: batch tasks of 5 features each dispatched sequentially — bounds peak context and rate-limit pressure.

```js
const fsCodes = resolvedTargetFcodes  // from preflight step 2
// `|| 5` + Math.max(1, …) guard on every cap env: junk/NaN/0/negative degrades to the
// default — a broken env value must never silently disable the cap (unbounded fan-out).
const FS_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? process.env.REBUILD_W6_BATCH_SIZE ?? '5') || 5)
const MAX_PARALLEL = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)  // global cap — wave width may never exceed this
const FS_WAVE_WIDTH = Math.min(FS_BATCH_SIZE, MAX_PARALLEL)
const allFeatureTaskIds = []

if (fsCodes.length <= 20) {
  // Bounded-wave fan-out — one task per feature, chained waves of ≤FS_WAVE_WIDTH.
  // Wave i+1 is addBlockedBy ALL of wave i → never more than FS_WAVE_WIDTH researchers runnable at once.
  let prevWaveIds = [], waveIds = []
  for (const [idx, fcode] of fsCodes.entries()) {
    if (idx > 0 && idx % FS_WAVE_WIDTH === 0) { prevWaveIds = waveIds; waveIds = [] }
    const taskId = TaskCreate({
      subject: `WaveFS1: feature-spec ${fcode}`,
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate DETAILED spec for ${fcode} — 4 audience-aware files.

PRE-WRITE GUARD (idempotent):
bash: mkdir -p plans/<active-plan>/artifacts/features/${fcode}/

CONTRACT: Read references/feature-spec-researcher-contract.md for mandatory rules (includes § Decision Logic Extraction (DEC-###)).
TEMPLATES: technical-spec-template.md, business-context-template.md, screens-template.md, edge-cases-template.md.
DRAFT: plans/<active-plan>/artifacts/features/${fcode}/{technical-spec,business-context,screens,edge-cases}.md (ALL 4 required).
POST-WRITE: Run rm plans/<active-plan>/artifacts/features/${fcode}/.pending ONLY after ALL 4 files written and non-empty.

CONTEXT INPUTS (token-efficient — DO NOT load full artifacts):
1. Grep docs/generated/feature-list.md for ${fcode} entry. Extract US###, SCR###, ROUTE###, MODEL###, BL###, PERM###.
2. Grep each code's section from its canonical artifact (US→docs/generated/user-stories.md, SCR→docs/generated/screen-list.md, BL→docs/system/business-rules.md, MODEL→docs/generated/entities.md, ROUTE→docs/generated/route-list.md).
3. Read in full: docs/system/business-rules.md, any docs/flows/<slug>.md relevant to this feature.
4. DO NOT read full upstream artifacts — scoped sections only.

SOURCE CODE: Use Grep/Read to find real controller(s), model(s), job(s), service(s), policy(ies), page files. Extract paths, line ranges, method names, table names, HTTP codes, event names.

ALL TEMPLATE SECTIONS MANDATORY. DEPTH BAR enforced — see contract.

SIZE-ADAPTIVE DRAFTING: if technical-spec exceeds 400 lines after first pass → split into 2 focused passes (core logic first, then integration layer).
BUSINESS-CONTEXT CROSS-REFS: for business-context.md, cite the flow slugs from docs/flows/ this feature participates in.

FEATURE ENTRY POINTS (fragment file pattern — mandatory):
After writing all 4 files, emit fragment: bash: mkdir -p plans/<active-plan>/artifacts/_feature-entry-points/
Write to: plans/<active-plan>/artifacts/_feature-entry-points/${fcode}.md
Content (route-view / web stacks):
### ${fcode}_{name}

- **Entry screen**: {SCR###_Name} — \`{/initial/route}\`
- **Owned screens**:
  - {SCR###_Name} — \`{/route/path}\` (atomic | composite)
- **Exit screens**: {SCR###_Name} (on {action/completion})

STACK-AWARE (v21.0.0): when the profile's screen_source is NOT route-view (e.g. dfm-form / Delphi),
a screen has no route. Use the caller-based shape instead — source the caller + invocation from the
form-nav digest (_digest_extract_form_nav.json), and cite file:line:
### ${fcode}_{name}

- **Entry form**: {SCR###_Name} — invoked by {CALLER_FORM/UNIT} via {Show|ShowModal|CreateForm} — \`{file}:{line}\`
- **Owned forms**:
  - {SCR###_Name} (atomic | composite) — \`{file}:{line}\`
- **Exit forms**: {SCR###_Name} (on {action/completion})
DO NOT append directly to screen-flow.md — parallel tasks would race-write the same file.`,
      addBlockedBy: prevWaveIds  // [] for the first wave
    })
    waveIds.push(taskId)
    allFeatureTaskIds.push(taskId)
  }
} else {
  // Batched fan-out — groups of FS_BATCH_SIZE
  const batches = chunk(fsCodes, FS_BATCH_SIZE)
  let prevBatchId = null  // no blocker for first batch
  for (const [i, batch] of batches.entries()) {
    const batchTaskId = TaskCreate({
      subject: `WaveFS1.batch-${pad2(i+1)}: feature-specs (${batch[0]}..${batch.at(-1)})`,
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate DETAILED specs for ${batch.length} features in parallel: ${batch.join(', ')}.
Apply the same rules as the small-codebase WaveFS1 block to EACH feature in this batch:
- PRE-WRITE GUARD: \`mkdir -p plans/<active-plan>/artifacts/features/{slug}/\` per feature.
- Read researcher contract, scoped context loading (Grep per-feature codes), read real source code.
- Canonical upstreams: entities.md (data-model), feature-list.md, user-stories.md, screen-list.md, business-rules.md (if present), docs/flows/*.md relevant to each feature.
- TEMPLATES: technical-spec-template.md, business-context-template.md, screens-template.md, edge-cases-template.md (4 files per feature — ALL required).
- DRAFT: plans/<active-plan>/artifacts/features/{slug}/{technical-spec,business-context,screens,edge-cases}.md
- POST-WRITE: run \`rm plans/<active-plan>/artifacts/features/{slug}/.pending\` ONLY after ALL 4 files exist and non-empty.
- FEATURE ENTRY POINTS: emit plans/<active-plan>/artifacts/_feature-entry-points/{fcode}.md per feature.
On batch completion, write plans/<active-plan>/artifacts/fs1-batch-${pad2(i+1)}.flag listing completed F###.`,
      addBlockedBy: prevBatchId ? [prevBatchId] : []
    })
    allFeatureTaskIds.push(batchTaskId)
    prevBatchId = batchTaskId
  }
}
```

### Wave FS.1.5 — Feature Entry Points consolidation (former post-W6)

After ALL FS.1 tasks complete, consolidate `_feature-entry-points/` fragments into `screen-flow.md`.

```js
// Consolidate _feature-entry-points/ fragments into docs/generated/screen-flow.md § Feature Entry Points
// (or the artifact draft if screen-flow.md has not been promoted yet)
const fragmentDir = `plans/<active-plan>/artifacts/_feature-entry-points/`
const fragmentFiles = bash(`ls ${fragmentDir}*.md 2>/dev/null | sort`).split('\n').filter(Boolean)

if (fragmentFiles.length > 0) {
  const consolidated = fragmentFiles.map(f => readFile(f)).join('\n\n')
  // Target: if draft screen-flow.md exists in artifacts, update it; else update docs/generated/screen-list.md entry points section
  const draftPath = `plans/<active-plan>/artifacts/screen-flow.md`
  const canonicalPath = `docs/generated/screen-flow.md`
  const targetPath = existsNonEmpty(draftPath) ? draftPath : canonicalPath
  if (existsNonEmpty(targetPath)) {
    const content = readFile(targetPath)
    const updated = content.replace('{POPULATED_BY_W6}', consolidated)
    writeFile(targetPath, updated)
    console.log(`[INFO] Feature Entry Points consolidated: ${fragmentFiles.length} features → ${targetPath}`)
  } else {
    console.log("[WARN] screen-flow.md not found in artifacts or docs/generated/ — Feature Entry Points section not updated. Run core rebuild first.")
  }
  bash(`rm -rf ${fragmentDir}`)
} else {
  console.log("[WARN] No _feature-entry-points/ fragments found — Feature Entry Points section not populated")
}
```

This is the ONLY step that writes to the `## Feature Entry Points` section of screen-flow.md. FS.1 researchers MUST NOT append to screen-flow.md directly.

### Wave FS.2 — Spec + citation validators (former W6.5) [RT-C2]

After ALL FS.1 tasks (or batches) complete, run deterministic validators. Output → `fs-validation-summary.json` (DISTINCT from core `validation-summary.json` — a feature-specs-pass result can never mask a core FAIL).

```js
// [RT-C2] Feature-specs pass uses its own validator summary file
// In incremental / scoped mode: pass --spec flags for touched F### only.
const specFlags = (resolvedTargetFcodes.length < allFcodes.length)
    ? resolvedTargetFcodes.map(f => `--spec ${f}`).join(' ')
    : ''

bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_feature_spec.py \
  --plan-dir plans/<active-plan> \
  --summary-out plans/<active-plan>/artifacts/validation/fs-validation-summary.json \
  ${specFlags}

bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_source_citations.py \
  --plan-dir plans/<active-plan> \
  --summary-out plans/<active-plan>/artifacts/validation/fs-validation-summary.json \
  ${specFlags}

// v24.0.0 — feature↔screen ID-link validator (WARN-capable, NON-halting). Checks the
// screens.md SCR### column resolves to screen-list.md, and (once screen-specs exist) the
// screen-spec **Feature** backlink resolves to feature-list.md. Pre-migration docs (no
// column / no backlink) emit WARN `link.pre_migration` and exit 0 — never block a build.
// A NON-zero exit means real drift (a code that does not resolve) → fix before promote.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_feature_screen_link.py \
  --plan-dir plans/<active-plan> \
  --summary-out plans/<active-plan>/artifacts/validation/fs-validation-summary.json

// v25.0.0 — feature↔API/route ID-link validator (WARN-capable, NON-halting). Checks
// technical-spec.md/behavior-logic.md {ROUTE###} citations resolve to route-list.md's
// Code column, route-list.md's Owner F### cell(s) resolve to feature-list.md, and
// twin-consistency (a feature's ROUTE### citation must appear in that route's Owner
// F### set). Pre-migration docs (no Code/Owner columns) emit WARN `link.pre_migration`
// and exit 0 — never block a build. A NON-zero exit means real drift → fix before promote.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_feature_api_link.py \
  --plan-dir plans/<active-plan> \
  --summary-out plans/<active-plan>/artifacts/validation/fs-validation-summary.json

// v26.0.0 — A3 Source Walkthrough + B4 DB Impact per Event validator (WARN-capable,
// NON-halting). Covers BOTH families from this ONE invocation (technical-spec.md's A3+B4,
// AND screen-spec spec.md's A3) — mirrors validate_feature_screen_link.py's FS.2-only wiring
// shape exactly, including its scope limitation (a --screen-specs-only run without ever
// running --feature-specs never exercises this gate; same as the v24 precedent). Absent
// section on an un-migrated doc emits WARN `*.pre_migration` and exits 0 — never blocks a
// build. A non-zero exit means a present-but-malformed section → fix before promote.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_reading_guide_db_impact.py \
  --plan-dir plans/<active-plan> \
  --summary-out plans/<active-plan>/artifacts/validation/fs-validation-summary.json

read plans/<active-plan>/artifacts/validation/fs-validation-summary.json:
  if overall_status === "FAIL":
    for each fcode in validators.specs where status === "FAIL":
      spawn implementer task: "Fix validator issues in {spec_path} per fs-validation-summary.json validators.specs.{fcode}.issues"
      on implementer return: re-run BOTH validators for that fcode only (--spec arg)
      if still FAIL after 2 implementer cycles: spawn fresh researcher re-draft for that fcode
  else (PASS or WARN):
    dispatch FS.5 reviewer batches; inject per-fcode slot into reviewer prompt
```

Validator output schema mirrors the core `validation-summary.json` schema (see `pipeline-w5x-w6.md § Wave 5.5`), but written to `fs-validation-summary.json`.

### Wave FS.5 — Feature-spec reviewer (former W7b) [RT-C3]

After FS.2 passes, spawn reviewer batches — 5 features per reviewer.

```js
// [RT-C3] Feature-specs pass uses feature-review-report.md (not review-report.md)
const FS_REVIEW_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? process.env.REBUILD_W6_BATCH_SIZE ?? '5') || 5)
const reviewTargets = resolvedTargetFcodes
const reviewBatches = chunk(reviewTargets, FS_REVIEW_BATCH_SIZE)
const allFS5TaskIds = []

// Read fs-validation-summary.json for per-batch prompt injection
const fsSummaryPath = `plans/<active-plan>/artifacts/validation/fs-validation-summary.json`
const fsSummary = existsNonEmpty(fsSummaryPath) ? JSON.parse(readFile(fsSummaryPath)) : null

function buildFsValidatorPreamble(batchFcodes) {
  if (!fsSummary) return `## Validator pre-check\n[validator-summary-absent] — apply full checklist (legacy plan).\n`
  const overall = fsSummary.overall_status ?? 'PASS'
  const lines = [`## Validator pre-check (auto-injected)`, `overall_status: ${overall}`]
  for (const fcode of batchFcodes) {
    const slot = fsSummary.validators?.specs?.[fcode]
    if (!slot) { lines.push(`- ${fcode}: no validator data`); continue }
    const { status, summary, issues } = slot
    lines.push(`- ${fcode}: ${status} (${summary.critical} critical, ${summary.warning} warning)`)
    for (const i of issues || []) {
      lines.push(`  - [${i.severity}] ${i.rule_id} @ ${i.location.file}:${i.location.line ?? '?'} — ${i.message}`)
    }
  }
  lines.push(`Skip rules listed in verification-checklist-feature-spec.md § Deterministic Validator Coverage that report PASS; mark them [deterministic-pass] in the review report.`)
  lines.push(`.pending marker rule: if plans/<active-plan>/artifacts/features/{slug}/.pending exists, emit MISSING for that fcode in review-report frontmatter (counts toward failed for FS.7 gate).`)
  lines.push(`Focus: semantic depth (BR/FR coverage, fabricated citations, cross-ref accuracy, edge case sufficiency).`)
  return lines.join('\n') + '\n'
}

// Bounded-wave dispatch: reviewer tasks themselves are wave-chained at ≤REBUILD_MAX_PARALLEL (global cap) —
// without this, ceil(N/5) reviewers would all unblock at once when FS.1 completes.
// Wave width is the GLOBAL cap, NOT FS_REVIEW_BATCH_SIZE: batch size = features per reviewer
// (workload knob); wave width = concurrent reviewers (concurrency knob). Never conflate them.
const FS5_WAVE_WIDTH = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
let prevFs5WaveIds = [], fs5WaveIds = []
for (const [i, batch] of reviewBatches.entries()) {
  if (i > 0 && i % FS5_WAVE_WIDTH === 0) { prevFs5WaveIds = fs5WaveIds; fs5WaveIds = [] }
  const fs5TaskId = TaskCreate({
    subject: `WaveFS5.batch-${pad2(i+1)}: feature-spec-review (${batch[0]}..${batch.at(-1)})`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Review ${batch.length} feature specs: ${batch.join(', ')}.

${buildFsValidatorPreamble(batch)}
CHECKLIST SECTION TARGETING — load references/verification-checklist-universal.md + references/verification-checklist-feature-spec.md.
- "## Failure Trap Assertions"
- "## Deterministic Validator Coverage" (rule_ids to mark [deterministic-pass] on PASS)
SKIP all core artifact sections (handled by the core pass W7a).

For each spec, cross-ref against its F### entry in docs/generated/feature-list.md.
For each features/{slug}/ folder: if .pending present, emit MISSING in frontmatter for that fcode.

Passed Checks: ONE LINE per rule (\`✓ <rule_id> @ <fcode>\`). NO prose.
Scout-report not needed for this task — do NOT read scout-report.md.

Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/feature-review-batch-${pad2(i+1)}.md`,
    addBlockedBy: [...allFeatureTaskIds, ...prevFs5WaveIds]
  })
  fs5WaveIds.push(fs5TaskId)
  allFS5TaskIds.push(fs5TaskId)
}
```

After all FS.5 batch reports return, the orchestrator merges them:

```js
// [RT-M1] Single review report per pass — no cross-pass merge needed
// Merge all feature-review-batch-*.md into feature-review-report.md
// Sum failed/warnings counts. Set result = PASS iff combined failed === 0.
const mergedReport = mergeReviewBatches(
  `plans/<active-plan>/artifacts/feature-review-batch-*.md`,
  `plans/<active-plan>/artifacts/feature-review-report.md`
)
```

### Wave FS.6 — Auto-fix loop (scoped to feature files) [Validation V2: KEEP]

After FS.5 review report is merged, run the fix cycle. Max 3 cycles; escalate on overflow.

```js
// [RT-M1] FS.6 blocks on FS.5 (feature-review-report.md), not on core review-report.md
const MAX_FIX_CYCLES = 3
// Clamped by the global cap — fix cycles are NOT exempt; junk/0 env degrades to default.
const REBUILD_W8_MAX_PARALLEL = Math.max(1, Math.min(
  parseInt(process.env.REBUILD_W8_MAX_PARALLEL ?? '5') || 5,
  parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5))
let currentFailed = parseInt(parseFrontmatter(readFile("plans/<active-plan>/artifacts/feature-review-report.md")).failed ?? 0)
let fixCycle = 0
let lastReviewTaskId = null  // set to last FS.5 merge task

while (currentFailed > 0 && fixCycle < MAX_FIX_CYCLES) {
  fixCycle++

  const reportContent = readFile("plans/<active-plan>/artifacts/feature-review-report.md")
  const issuesByFile = extractIssuesByFile(reportContent)  // same helper as pipeline-w7-w9.md
  const affectedFiles = [...issuesByFile.keys()]

  console.log(`[INFO] FS.6 cycle ${fixCycle}: ${currentFailed} critical issues across ${affectedFiles.length} file(s)`)

  // Batches CHAINED (global 5-agent cap): every task of batch bi+1 is addBlockedBy ALL of batch bi.
  const fileBatches = chunk(affectedFiles, REBUILD_W8_MAX_PARALLEL)
  const allFixTaskIds = []
  let prevBatchFixIds = []

  for (const [bi, batch] of fileBatches.entries()) {
    const batchFixIds = []
    for (const filePath of batch) {
      const fileIssues = issuesByFile.get(filePath)
      const fixTaskId = TaskCreate({
        subject: `WaveFS6.cycle-${fixCycle}.fix-${filePath.split('/').pop().replace('.md', '')}`,
        description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Fix cycle ${fixCycle}/${MAX_FIX_CYCLES} — targeted fix for ONE file.

**File to fix:** \`${filePath}\`

**Issues to resolve (fix ALL of these):**
${fileIssues.map((issue, i) => `${i + 1}. ${issue}`).join('\n')}

Rules:
- Fix ONLY the listed issues in ONLY this file
- Do NOT alter other files or passing sections
- Re-read the file before editing to get current state
- After fixing, verify each listed issue is addressed
- SCOPE: feature spec files only (features/F###/*.md). Do NOT edit core artifacts.`,
        addBlockedBy: [lastReviewTaskId ?? allFS5TaskIds.at(-1), ...prevBatchFixIds]
      })
      batchFixIds.push(fixTaskId)
      allFixTaskIds.push(fixTaskId)
    }
    prevBatchFixIds = batchFixIds  // chain: batch bi+1 waits for ALL of batch bi
  }

  // Single re-reviewer after ALL per-file fixes
  const reReviewTaskId = TaskCreate({
    subject: `WaveFS6.cycle-${fixCycle}: re-reviewer`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Re-verify all fixed feature spec files after fix cycle ${fixCycle}.
Load references/verification-checklist-universal.md + references/verification-checklist-feature-spec.md.
Re-read each feature spec that had OPEN issues and verify each issue is resolved.
Do NOT re-review files that had no OPEN issues.
Overwrite plans/<active-plan>/artifacts/feature-review-report.md with fresh content (frontmatter + markdown body using review-report-template.md).`,
    addBlockedBy: allFixTaskIds
  })

  const freshContent = readFile("plans/<active-plan>/artifacts/feature-review-report.md")
  currentFailed = parseInt(parseFrontmatter(freshContent).failed ?? 0)
  lastReviewTaskId = reReviewTaskId
}

if (currentFailed > 0) {
  throw new Error(`ESCALATE: ${currentFailed} feature spec(s) still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required. Drafts preserved in plans/<active-plan>/artifacts/features/.`)
}
```

### Wave FS.7 — Promote feature dirs [RT-C3, RT-C4]

After FS.6 passes (or FS.5 if no failures), run the pre-flight gate, promote, and update state.

```js
// [RT-C3] FS.7 pre-flight gate reads fs-validation-summary.json + feature-review-report.md
// A feature-specs FAIL never affects the core pass gate (separation enforced here).
const fsSummaryPath = `plans/<active-plan>/artifacts/validation/fs-validation-summary.json`
let fsValidatorOverall = "PASS"
if (existsNonEmpty(fsSummaryPath)) {
  const s = JSON.parse(readFile(fsSummaryPath))
  fsValidatorOverall = s.overall_status ?? "PASS"
} else {
  console.log("[INFO] no fs-validation-summary.json — FS.7 gating on feature-review-report.md only.")
}
const fsFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/feature-review-report.md"))
const fsFailed = parseInt(fsFm.failed ?? 0)
const fsMissing = parseInt(fsFm.missing ?? 0)
if (fsValidatorOverall === "FAIL" || fsFailed > 0 || fsMissing > 0) {
  throw new Error(`FS.7 gate HALT — validator=${fsValidatorOverall}, review failed=${fsFailed}, missing=${fsMissing}. No docs/ writes. Resolve before re-running.`)
}

// Promote feature dirs only (not core artifacts; --scope features = only docs/features/*)
// [v5.1.0] docs_root from language dispatch (mode-aware via resolve_docs_root: single-lang en→"docs"; per-lang/non-en→"docs/<primary_lang>")
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode incremental \
  --scope features \
  --affected-fcodes ${resolvedTargetFcodes.join(',')}

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. Mirrors .nav-metadata.json precedent; see references/confidence-report-contract.md.
for (const fcode of resolvedTargetFcodes) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
    --artifact ${docs_root}/features/${fcode}/technical-spec.md --project-root .
}

// [RT-C4 + V7] Clear the features stale marker on successful promote
bash: rm -f docs/features/.stale

// Update per-pass cursor (--cursor feature-specs advances last_feature_spec_run_sha ONLY — does NOT advance last_rebuild_sha)
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor feature-specs

// [RT-C3] Write pass-specific completion flag (not wave9-complete.flag)
bash: echo "# FS.7 complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/fs7-complete.flag
bash: echo "# Scope: feature-specs" >> plans/<active-plan>/artifacts/fs7-complete.flag
bash: echo "# F###: ${resolvedTargetFcodes.join(', ')}" >> plans/<active-plan>/artifacts/fs7-complete.flag
// [item ④ / RT-C3] Embed this pass's OWN promote manifest snapshot so `sha256sum -c` can audit the
// feature dirs independently of the core flag. promote_drafts.py wrote _promoted-sha256.txt for THIS pass.
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/fs7-complete.flag

// [v24.0.0] Refresh navigation so the just-promoted docs/features/F###/ dirs surface in the
// reading-order README (the "how to read a feature" traversal block + layer-4), and so each
// feature dir gets its per-feature README (A4) + docs/features/README.md index (A5). Mirrors the
// core-pass W9.6 nav step. PRIMARY root only — secondary-lang mirrors are refreshed by the
// translation auto-sync Step 3.5 below (pipeline-translate.md § Auto-Sync). Advisory, exit 0 always.
// docs_root is mode-aware (single-lang "docs" → no --lang/en labels; per-lang "docs/<primary>" →
// --lang <primary>). Derive the lang from docs_root's last segment — no separate primary_lang var needed.
const navLangFlag = (docs_root === "docs") ? "" : `--lang ${docs_root.split("/").pop()}`
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_navigation.py \
  --docs-root ${docs_root} ${navLangFlag} --pass-complete

// [v5.3.3] Auto-sync secondary languages after feature-specs promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass feature-specs --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass feature-specs --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Pass-completion handoff prompt [Validation V3]

After FS.7 completes, the orchestrator prints the handoff below.

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write `translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by `translation_sync_gate.py --mode finalize` — echo it VERBATIM. Feature specs are the most common pass to silently skip secondary sync, so a missing/partial sync MUST surface as ⚠. See `references/pipeline-translate.md § Auto-Sync Secondary Languages` for the full contract. DO NOT compose, paraphrase, or invent the `Secondary languages:` line — copy it byte-for-byte from script stdout.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass feature-specs` BEFORE writing the completion flag or printing this handoff. Exit 1 BLOCKS completion. See `references/pipeline-translate.md § Completion gate` for the full gate-run command and fix instructions.

```
─── feature-specs pass complete ───
Promoted: docs/features/{F###}/ (technical-spec, business-context, screens, edge-cases) for ${resolvedTargetFcodes.length} feature(s)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Are the feature specs for [domain] coherent and complete?"
Soundness (optional): /tkm:audit-synthesis-judgment --scope all  # judges partition/US/inference soundness incl. full code-level coverage (orphans/phantoms now that docs/features/ exists) — non-blocking
Next options (run in any order — they are independent):
  /tkm:rebuild-spec --flows       # Synthesize process-flows (requires docs/features/* just promoted)
  /tkm:rebuild-spec --glossary    # Synthesize glossary     (requires docs/features/* just promoted)
  /tkm:rebuild-spec --screen-specs # Generate screen specs  (requires docs/generated/screen-list.md)
```

If sibling stale markers are still set, include nudge:
```
Note: docs/flows/.stale detected — run /tkm:rebuild-spec --flows to refresh.
Note: docs/system/.glossary.stale detected — run /tkm:rebuild-spec --glossary to refresh.
```

## Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | `plans/<active-plan>/artifacts/validation/fs-validation-summary.json` |
| Review report | `plans/<active-plan>/artifacts/feature-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/fs7-complete.flag` |

These are DISTINCT from core pass artifacts (`validation-summary.json`, `review-report.md`, `wave9-complete.flag`). A FAIL in either direction is isolated.

## Subagent contracts (feature-specs pass)

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| FS.1 | `researcher` (1/feature in chained waves of ≤5, or 5/batch sequential) | scoped artifact sections (Grep per F###) + `feature-spec-researcher-contract.md` + 4 audience templates + canonical upstreams | `plans/<active>/artifacts/features/{slug}/{technical-spec,business-context,screens,edge-cases}.md` (4 files) + `TaskUpdate(status=completed)` |
| FS.1.5 | orchestrator | `_feature-entry-points/` fragments | updated `## Feature Entry Points` in screen-flow.md |
| FS.2 | orchestrator (`validate_feature_spec.py` + `validate_source_citations.py`) | feature spec drafts | `fs-validation-summary.json` |
| FS.5 | `reviewer` (5/batch) | feature spec batches + `verification-checklist-feature-spec.md` | `feature-review-batch-NN.md` → merged into `feature-review-report.md` |
| FS.6 | `implementer` (per-file, max 3 cycles) | `feature-review-report.md` + affected drafts | updated drafts → re-reviewer |
| FS.7 | `promote_drafts.py` + orchestrator | approved drafts | `docs/features/{slug}/*` + `fs7-complete.flag` + state update |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input happen afterward.
