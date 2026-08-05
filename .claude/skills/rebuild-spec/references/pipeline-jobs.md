<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Jobs Pass (J.1–J.5)

Standalone pass. Loaded only when `--jobs` flag is set. Requires core pass artifacts to exist
first (same prerequisite class as `--screen-specs` — core only, parallel-safe with other
standalone passes). Per-pass artifact isolation: RT-C2/RT-C3 (same isolation discipline as
flows/glossary/api-contracts).

## Preflight

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the
> pass dependency chain).

**Requires:** `docs/generated/behavior-logic.md` must exist and be non-empty (else ABORT).
Optional enrichment: `docs/generated/entities.md` (data-touched cross-refs).

```js
// Preflight — verify core pass prerequisite
if (!existsNonEmpty("docs/generated/behavior-logic.md")) {
  throw new Error(
    "ABORT — docs/generated/behavior-logic.md missing. Run /tkm:rebuild-spec (core pass) first, " +
    "then re-run --jobs."
  )
}

// Incremental cursor check
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const lastJobsSha = state.last_jobs_run_sha ?? null
const shouldResynth = flags.full || !lastJobsSha || sourceChangedSince(lastJobsSha)
if (flags.full) {
  console.log("[INFO] --full: jobs regenerating (cursor ignored)")
}
if (!shouldResynth) {
  console.log("[INFO] --jobs: no source changes since last run — nothing to do. Use --full to force.")
  process.exit(0)
}
```

---

## Wave J.1 — Jobs synthesis (with bounded-wave fan-out, F10)

```js
// Count qualifying entries directly (no estimate_artifact_loc.py wiring needed — this is a
// cheap count over an already-promoted, already-small artifact, not a fresh LOC estimate).
const blText = readFile("docs/generated/behavior-logic.md")
const jobTypeRe = /\*\*Type\*\*:\s*(scheduled-job|queue-worker|custom-command)\b/gi
const jobEntryCount = (blText.match(jobTypeRe) || []).length

console.log(`[INFO] J.1 pre-count: ${jobEntryCount} job-type BL### entries`)
```

**≤5 qualifying entries — SINGLE-TASK BRANCH** (the common case — research: job counts are
structurally small):

```js
if (jobEntryCount <= 5) {
  var j1TaskId = TaskCreate({
    subject: "WaveJ1: job-list",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST (or load docs/generated/behavior-logic.md directly if session context absent).

Synthesize the job inventory from docs/generated/behavior-logic.md. CONTRACT: references/jobs-researcher-contract.md.
TEMPLATE: templates/job-list-template.md.

SOURCES (read from docs/, not artifacts/ — core pass already promoted):
1. docs/generated/behavior-logic.md — filter to **Type** ∈ {scheduled-job, queue-worker, custom-command}
2. docs/generated/entities.md — Data Touched cross-refs
3. references/bl-source-patterns.md — per-stack detection convention (incl. systemd-timer row)

SOURCE CODE: AUTHORIZED for read-only static detail (schedule config, handler body, systemd unit
files). NEVER execute target tooling (rake -T / crontab -l / systemctl) — read-only static scan
contract (references/jobs-researcher-contract.md § Read-Only Static Scan Contract).

GATE (strict hard-omit): only behavior-logic.md entries matching the type filter AND carrying a
real (non-stub) Source File + Source Symbol. Below threshold → zero output for that entry.

EVERY JOB### section MUST carry a **Source** file:line citation. Unsourced claim → omit the
field content, write "N/A — not found in source." NEVER echo a secret/credential literal.

OUTPUT: plans/<active-plan>/artifacts/job-list.md (one JOB### section per qualifying BL### entry,
JOB### codes file-global, sequential). Zero qualifying entries → still emit the file with an
empty Job Index note (never omit the file).
After completion (including zero-output), write plans/<active-plan>/artifacts/.job-list.completed.
Call TaskUpdate(status=completed) on this task id BEFORE returning.`
  })
}
```

**>5 qualifying entries — BOUNDED-WAVE FAN-OUT BRANCH** (rare — F10: reuse
`REBUILD_FS_BATCH_SIZE`, clamped by `REBUILD_MAX_PARALLEL`, per the v25.1.2 guard formula):

```js
if (jobEntryCount > 5) {
  // J.1-shell: write skeleton (preamble + Job Index anchor) + one BL### assignment per fragment.
  const shellTaskId = TaskCreate({
    subject: "WaveJ1-shell: job-list skeleton + slice plan",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

SHARD MODE — you are the SHELL researcher.
Read: docs/generated/behavior-logic.md. List every BL### entry whose **Type** ∈
{scheduled-job, queue-worker, custom-command} (${jobEntryCount} total).

YOUR JOB (skeleton ONLY — do NOT write JOB### sections):
1. Write plans/<active-plan>/artifacts/job-list.md with the preamble (per templates/job-list-template.md)
   and a {POPULATED_BY_FRAGMENTS} placeholder where the Job Index + per-job sections go.
2. Write plans/<active-plan>/artifacts/_fragments/job-list/_slice-plan.json:
   { "slices": [ {"ordinal": "01", "bl_ref": "BL###", "expected_count": 1}, ... ] }
   — one slice per qualifying BL### entry (assign JOB### codes sequentially here, file-global).
3. mkdir -p plans/<active-plan>/artifacts/_fragments/job-list/
Call TaskUpdate(status=completed) BEFORE returning.`
  })

  const JOB_FAN_CAP = Math.max(1, Math.min(
    parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? '5') || 5,
    parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5))
  const slicePlan = JSON.parse(readFile("plans/<active-plan>/artifacts/_fragments/job-list/_slice-plan.json"))
  const allFragTaskIds = []
  const batches = chunk(slicePlan.slices, JOB_FAN_CAP)
  let prevBatchBlocker = [shellTaskId]
  for (const batch of batches) {
    const batchIds = []
    for (const slice of batch) {
      const fragId = TaskCreate({
        subject: `WaveJ1-frag-${slice.ordinal}: job-list ${slice.bl_ref}`,
        description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

SHARD MODE — you are a FRAGMENT researcher.
CONTRACT: references/jobs-researcher-contract.md (READ-ONLY static scan, F7 — never execute
target tooling). TEMPLATE: templates/job-list-template.md § per-job section shape.

YOUR SLICE: expand BL### entry "${slice.bl_ref}" (docs/generated/behavior-logic.md) into ONE
JOB### section using ordinal ${slice.ordinal} for the JOB### number.
RULES: write ONLY the JOB### heading block (index row + detail section) for this one entry.
NO preamble, NO other JOB### entries. Every field needs a **Source** file:line citation.
OUTPUT: plans/<active-plan>/artifacts/_fragments/job-list/${slice.ordinal}-job.md
Call TaskUpdate(status=completed) BEFORE returning.`,
        addBlockedBy: prevBatchBlocker
      })
      batchIds.push(fragId)
      allFragTaskIds.push(fragId)
    }
    prevBatchBlocker = batchIds  // chain wave i+1 on ALL of wave i, never just the last
  }

  // J.1-merge: orchestrator merges fragments into the skeleton, numerically by ordinal.
  const fragDir = "plans/<active-plan>/artifacts/_fragments/job-list"
  const fragFiles = bash(`ls ${fragDir}/*.md 2>/dev/null | sort -t- -k1,1n`).split('\n').filter(Boolean)

  // Merge-gate: re-read the slice plan from disk (robust to ordering vs the L116 read) and
  // require every slice to have produced a fragment BEFORE touching the fragment dir or
  // writing the completion marker. A partial fragment set must never look complete.
  const slicePlanAtMerge = JSON.parse(readFile(`${fragDir}/_slice-plan.json`))
  if (fragFiles.length !== slicePlanAtMerge.slices.length) {
    const gotOrdinals = new Set(fragFiles.map(f => f.match(/(\d+)-job\.md$/)?.[1]))
    const missing = slicePlanAtMerge.slices
      .filter(s => !gotOrdinals.has(s.ordinal))
      .map(s => `${s.ordinal} (${s.bl_ref})`)
    throw new Error(
      `J.1-merge HALT — expected ${slicePlanAtMerge.slices.length} fragments, found ${fragFiles.length}. ` +
      `Missing ordinals: ${missing.join(', ')}. NOT merging, NOT deleting ${fragDir}, NOT writing ` +
      `.job-list.completed — re-run the missing WaveJ1-frag task(s) before retrying merge.`
    )
  }

  const merged = fragFiles.reduce(
    (draft, f) => draft.replace('{POPULATED_BY_FRAGMENTS}', readFile(f).trim() + '\n\n{POPULATED_BY_FRAGMENTS}'),
    readFile("plans/<active-plan>/artifacts/job-list.md")
  ).replace('{POPULATED_BY_FRAGMENTS}', '')
  writeFile("plans/<active-plan>/artifacts/job-list.md", merged)
  bash(`rm -rf ${fragDir}`)
  bash(`touch plans/<active-plan>/artifacts/.job-list.completed`)

  var j1TaskId = allFragTaskIds[allFragTaskIds.length - 1]  // last fragment as blocker for J.2
}
```

Zero qualifying entries (either branch) → still emit `job-list.md` with the header/preamble
intact and an empty Job Index note (never omit the file) — see
`references/jobs-researcher-contract.md`.

## Wave J.2 — Deterministic validator

After J.1 completes (`.job-list.completed` marker present), run the deterministic validator.
FAIL halts before J.3.

```js
const j1CompletedMarker = `plans/<active-plan>/artifacts/.job-list.completed`
if (!exists(j1CompletedMarker)) {
  throw new Error("J.2 HALT — .job-list.completed marker absent. J.1 may not have completed.")
}

const validatorResult = bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_job_list.py \
  --plan-dir plans/<active-plan> \
  --project-root ${projectRoot} \
  --summary-out plans/<active-plan>/artifacts/validation/job-list-validation-summary.json`)

if (validatorResult.exitCode !== 0) {
  throw new Error(
    `J.2 HALT — job-list validator found critical issues (incl. possible secret leak). ` +
    `Fix plans/<active-plan>/artifacts/job-list.md, then re-run (--jobs). ` +
    `Details: plans/<active-plan>/artifacts/validation/job-list-validation-summary.json`
  )
}
console.log(`[INFO] J.2 passed — job-list validation OK`)
```

> [INFO] The validator also emits a `JobList.bl_uncovered` WARN rule (informational, does not
> fail the pass) when a qualifying `behavior-logic.md` entry has no corresponding JOB### section
> — reverse-coverage signal, not a merge-completeness check (that is the J.1-merge gate above).

## Wave J.3 — JobList reviewer

After J.2 passes, spawn a single reviewer task. Checklist: `verification-checklist-jobs.md`
(JOB-S1..JOB-S6).

```js
const j3TaskId = TaskCreate({
  subject: "WaveJ3: job-list-review",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Review plans/<active-plan>/artifacts/job-list.md.
Load references/verification-checklist-universal.md + references/verification-checklist-jobs.md.

CHECKLIST SECTION TARGETING: apply ONLY the JobList section rules from
references/verification-checklist-jobs.md (JOB-S1..JOB-S6). SKIP all core artifact sections —
those are handled by their own passes.

**JobList validator pre-check (auto-injected):**
J.2 deterministic validator (validate_job_list.py) already checked:
  citation presence, JOB### regex/uniqueness (file-global), BL Ref presence + resolution,
  .job-list.completed marker, secrets gate (assert_no_secrets, CRITICAL).
Mark all deterministic-pass rule_ids as [deterministic-pass] — skip them. Semantic dedup vs
behavior-logic.md is NOT covered by the validator — that stays a reviewer responsibility, see
JOB-S4 in verification-checklist-jobs.md. Focus on semantic depth
(see verification-checklist-jobs.md § JOB-S1..JOB-S6).

Passed Checks: ONE LINE per rule (\`✓ <rule_id> @ <job-slug>\`). NO prose.

Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/job-list-review-report.md`,
  addBlockedBy: [j1TaskId]
})
```

## Wave J.4 — Scoped fix loop (optional)

If `job-list-review-report.md` reports `failed > 0`, run a fix loop. Max 3 cycles.

```js
const MAX_FIX_CYCLES = 3
const jFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/job-list-review-report.md"))
let jFailed = parseInt(jFm.failed ?? 0)
let jFixCycle = 0
let jLastReviewId = j3TaskId

while (jFailed > 0 && jFixCycle < MAX_FIX_CYCLES) {
  jFixCycle++
  const reportContent = readFile("plans/<active-plan>/artifacts/job-list-review-report.md")
  const issuesByFile = extractIssuesByFile(reportContent)

  const fixId = TaskCreate({
    subject: `WaveJ4.cycle-${jFixCycle}.fix-job-list`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Fix cycle ${jFixCycle}/${MAX_FIX_CYCLES} for job-list.md.
Issues: ${[...issuesByFile.values()].flat().join(' | ')}
Rules: fix ONLY the listed issues in job-list.md; do NOT alter other artifacts.
SCOPE: plans/<active-plan>/artifacts/job-list.md only.`,
    addBlockedBy: [jLastReviewId]
  })

  const reReviewId = TaskCreate({
    subject: `WaveJ4.cycle-${jFixCycle}: re-reviewer`,
    description: `Re-verify job-list.md after fix cycle ${jFixCycle}.
Load references/verification-checklist-universal.md + references/verification-checklist-jobs.md (JOB-S1..JOB-S6).
Overwrite plans/<active-plan>/artifacts/job-list-review-report.md with fresh content.`,
    addBlockedBy: [fixId]
  })

  const fresh = readFile("plans/<active-plan>/artifacts/job-list-review-report.md")
  jFailed = parseInt(parseFrontmatter(fresh).failed ?? 0)
  jLastReviewId = reReviewId
}

if (jFailed > 0) {
  throw new Error(`ESCALATE: job-list still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required.`)
}
```

## Wave J.5 — Promote job-list

```js
// Pre-flight gate: reads job-list-validation-summary.json + job-list-review-report.md
const jvPath = `plans/<active-plan>/artifacts/validation/job-list-validation-summary.json`
let jValidatorOverall = "PASS"
if (existsNonEmpty(jvPath)) {
  jValidatorOverall = (JSON.parse(readFile(jvPath)).overall_status ?? "PASS")
} else {
  console.log("[INFO] no job-list-validation-summary.json — J.5 gating on review-report only.")
}
const jFm2 = parseFrontmatter(readFile("plans/<active-plan>/artifacts/job-list-review-report.md"))
const jFailed2 = parseInt(jFm2.failed ?? 0)
if (jValidatorOverall === "FAIL" || jFailed2 > 0) {
  throw new Error(`J.5 gate HALT — validator=${jValidatorOverall}, review failed=${jFailed2}. No docs/ writes.`)
}

// Promote job-list to docs/generated/job-list.md (F13 — no docs/jobs/ namespace)
// docs_root from language dispatch (mode-aware via resolve_docs_root)
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode full \
  --scope jobs

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. See references/confidence-report-contract.md.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
  --artifact ${docs_root}/generated/job-list.md --project-root .

// Update per-pass cursor (--cursor jobs advances last_jobs_run_sha ONLY)
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor jobs

// [F9] Write pass-specific completion flag — enumerated in SKILL.md Resume & Reconcile
bash: echo "# J.5 complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/jobs-complete.flag
bash: echo "# Scope: jobs (docs/generated/job-list.md)" >> plans/<active-plan>/artifacts/jobs-complete.flag
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/jobs-complete.flag

// [v5.3.3] Auto-sync secondary languages after job-list promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
// docs/generated/ is already covered by _translation_sync_lib.py::_DOC_AREAS — no registry change needed (F2).
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass jobs --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass jobs --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Jobs Pass-completion handoff prompt

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write
`translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by
`translation_sync_gate.py --mode finalize` — echo it VERBATIM. See
`references/pipeline-translate.md § Auto-Sync Secondary Languages` for the full contract. DO NOT
compose, paraphrase, or invent that line. The re-sync command is always
`/tkm:rebuild-spec --lang <code>`.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass jobs` BEFORE writing the
completion flag or printing this handoff. Exit 1 BLOCKS completion. See
`references/pipeline-translate.md § Completion gate` for the full gate-run command and fix
instructions.

```
─── jobs pass complete ───
Promoted: docs/generated/job-list.md (batch/background-job inventory)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Is the job inventory complete and accurate for the codebase?"
Soundness (optional): /tkm:audit-synthesis-judgment --scope system  # judges system-tier artifact soundness — non-blocking
Next:
  /tkm:write-journal             # Record this milestone
```

## Jobs Pass — Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | `plans/<active-plan>/artifacts/validation/job-list-validation-summary.json` |
| Review report | `plans/<active-plan>/artifacts/job-list-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/jobs-complete.flag` |

## Jobs Pass — Reconcile `expectedOutput` (F9)

Resume/reconcile preflight for this pass checks: `jobs-complete.flag` present OR
`docs/generated/job-list.md` exists and non-empty. `expectedOutput` =
`docs/generated/job-list.md`.

## Jobs Pass — Subagent contracts

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| J.1 | `researcher` | `docs/generated/behavior-logic.md` (type-filtered) + `docs/generated/entities.md` + `jobs-researcher-contract.md` + `job-list-template.md` | `plans/<active>/artifacts/job-list.md` + `.job-list.completed` |
| J.2 | orchestrator (`validate_job_list.py`) | `job-list.md` | `job-list-validation-summary.json`; exit 0/1 |
| J.3 | `reviewer` | `job-list.md` + `verification-checklist-jobs.md` (JOB-S1..JOB-S6) | `job-list-review-report.md` |
| J.4 | `implementer` + `reviewer` | review report + `job-list.md` | fixed `job-list.md` |
| J.5 | orchestrator (`promote_drafts.py`) | `job-list.md` | `docs/generated/job-list.md` + `jobs-complete.flag` + state update (`last_jobs_run_sha`) |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input
happen afterward.
