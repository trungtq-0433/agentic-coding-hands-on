<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Waves W7–W9 (Review, Fix, Merge, Archive)
<!-- Updated: Phase-02 strip — W6.8/W6.85/W6.9 relocated to pipeline-flows-glossary.md; W7b relocated to pipeline-feature-specs.md; W7a is core-only; W9 gate uses allCoreDocsPromoted -->
Loaded by orchestrator before W7a/W7.5/W8/W9 dispatch (default/core run). See `pipeline.md` for wave dep graph + incremental preamble.

**Default run scope:** W7a reviews core artifacts ONLY (no process-flows, no glossary — those are not generated in the default run). W7b (feature spec reviewer) and W6.8/W6.85/W6.9 now live in their respective pass files (`pipeline-feature-specs.md`, `pipeline-flows-glossary.md`).

## Review + fix cycle (Waves 7-9)

```
// review-report.md format — markdown body with YAML frontmatter:
//
// ---
// failed: <number>      # count of critical-severity issues (0 = all pass)
// warnings: <number>    # count of warning-severity issues
// result: PASS | FAIL   # PASS iff failed === 0
// ---
// (markdown body follows — use templates/review-report-template.md as base)
//
// Reviewer MUST start from templates/review-report-template.md and fill in all fields.
// Orchestrator reads ONLY the frontmatter to branch on failed count.

/**
 * Parse review-report.md body and group critical issues by affected file path.
 * Returns: Map<filePath, issueList[]>
 *
 * Assumes review-report.md body format from review-report-template.md:
 *   ## Critical Issues
 *   ### {ArtifactName or F###_Slug}
 *   - **File:** `plans/.../artifacts/...`
 *   - **Issue:** [description]
 */
function extractIssuesByFile(reportContent) {
  const fileMap = new Map()  // filePath → issueText[]
  const lines = reportContent.split('\n')

  let currentFile = null
  let inCritical = false
  let skipFixed = false  // skip issues marked — FIXED

  for (const line of lines) {
    if (line.startsWith('## Critical Issues')) { inCritical = true; continue }
    if (line.startsWith('## ') && line !== '## Critical Issues') { inCritical = false; continue }
    if (!inCritical) continue

    if (line.startsWith('### ')) {
      // Skip issues already marked FIXED; only process OPEN ones
      skipFixed = !line.includes('— OPEN') && !line.includes('- OPEN')
      currentFile = null
      continue
    }
    if (skipFixed) continue

    // Match **Location**: `path:line` OR legacy **File:** `path`
    const locationMatch = line.match(/\*\*(?:Location|File):\*\*\s*`([^`]+)`/)
    if (locationMatch) {
      // Strip optional :line or :start-end suffix so key is a plain file path
      currentFile = locationMatch[1].trim().replace(/:[\d][\d\-]*$/, '')
      if (!fileMap.has(currentFile)) fileMap.set(currentFile, [])
      continue
    }
    if (!currentFile) continue

    // Capture **Description**: and **Fix**: fields (template format)
    const descMatch = line.match(/^\s*-\s+\*\*Description:\*\*\s*(.+)/)
    if (descMatch) { fileMap.get(currentFile).push(descMatch[1].trim()); continue }
    const fixMatch = line.match(/^\s*-\s+\*\*Fix:\*\*\s*(.+)/)
    if (fixMatch) { fileMap.get(currentFile).push(`Fix: ${fixMatch[1].trim()}`); continue }
    // Legacy: lines that explicitly mention Issue / CRITICAL / [critical]
    const issueMatch = line.match(/^\s*-\s+(.+)/)
    if (issueMatch && (line.includes('**Issue') || line.includes('CRITICAL') || line.includes('[critical]'))) {
      fileMap.get(currentFile).push(issueMatch[1].trim())
    }
  }

  // Fallback: if no structured file refs found, return single entry with full report path
  if (fileMap.size === 0) {
    fileMap.set('review-report.md', ['See full review-report.md for all issues'])
  }
  return fileMap
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/)
  if (!match) return {}
  return Object.fromEntries(
    match[1].split('\n')
      .filter(line => line.includes(':'))
      .map(line => { const [k, ...v] = line.split(':'); return [k.trim(), v.join(':').split('#')[0].trim()] })
  )
}

// ═══════════════════════════════════════════════════════
// API Contracts pass (AC.1–AC.5) is NOT dispatched in the default (core) run.
// It lives in pipeline-api-contracts.md (--api-contracts standalone pass).
// ═══════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════
// REVIEW ZONE (W7a | W7-merge)
// FL.1 (process-flow), FL.2 (flow validator), GL.1 (glossary) are NOT dispatched in the
// default (core) run. They live in pipeline-flows-glossary.md (--flows and --glossary passes).
// FS.5 (feature spec reviewer) is NOT dispatched in the default run.
// It lives in pipeline-feature-specs.md (--feature-specs pass, Wave FS.5).
// LLM reviewer passes — semantic quality checks.
// W7a reviews core artifacts (blocks on W5 FeatureList). W7-merge combines into review-report.md.
// ═══════════════════════════════════════════════════════

// --- Wave 7a: Core artifact review (default/core run — core artifacts only) ---
// Blocks only on W5 (FeatureList). Reviews core doc artifacts ONLY.
// Process-flows and glossary are NOT reviewed here (those are separate passes).
// Incremental mode: skip W7a if no core wave re-ran.
// [RT-C6] Wave6.8/Wave6.9 removed from re_generated_artifacts mapping — default run never generates them.
const re_generated_artifacts = (mode === "incremental")
    ? affected_waves.map(w => {
        // Reverse-map wave subjects to filenames (core waves only — no Wave6.8/Wave6.9)
        const mapping = {
          "Wave1: route-list": ["route-list.md"],
          "Wave1: data-model": ["data-model.md"],
          "Wave2: screen-list + screen-flow": ["screen-list.md", "screen-flow.md"],
          "Wave2: behavior-logic": ["behavior-logic.md"],
          "Wave2.9: api-map": ["api-map.md"],
          "Wave3: permissions": ["permissions.md", "permissions-matrix.md"],
          "Wave4: user-stories": ["user-stories.md"],
          "Wave5: feature-list": ["feature-list.md"],
        }
        return mapping[w] ?? []
      }).flat()
    : ["all"]

// [#8 v21.0.0] Full-run review list built from produce()-true artifacts, NOT a fixed string.
// Universal artifacts are always reviewed; route-list / screen-list / screen-flow are included only
// when the profile produces them — a Delphi run reviews screen-list/screen-flow but NOT route-list,
// so the reviewer is never told to review an artifact that was intentionally skipped.
const fullRunReviewArtifacts = [
  "system-overview", "architecture", "data-model", "behavior-logic",
  "permissions", "permissions-matrix", "user-stories", "feature-list",
  ...(produce("route-list")  ? ["route-list"]  : []),
  ...(produce("screen-list") ? ["screen-list"] : []),
  ...(produce("screen-flow") ? ["screen-flow"] : []),
].join(", ")

const w7aTaskId = (mode === "incremental" && re_generated_artifacts.length === 0)
  ? `SKIPPED:W7a`
  : TaskCreate({ subject: "Wave7a: core-artifact-review",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Review ${mode === "incremental" ? "re-generated core" : "core"} artifacts: ${mode === "incremental" ? re_generated_artifacts.join(', ') : fullRunReviewArtifacts}.
${mode === "incremental" ? `\nINCREMENTAL MODE: Only the above artifacts were re-generated this run. Remaining artifacts are unchanged from prior rebuild — read them as upstream context (read-only) but do not review them for compliance.\n` : ''}
Detected stack: ${stackNote} — when applying composite detection rules from verification-checklist-core-artifacts.md, select per-stack signals from the row matching this stack value (see composite-screen-detection.md § Stack Probe).

CHECKLIST SECTION TARGETING — load references/verification-checklist-universal.md + references/verification-checklist-core-artifacts.md.
SKIP the "### FeatureSpec" section entirely (handled by --feature-specs pass FS.5).
SKIP the "### ProcessFlow" section entirely (handled by --flows pass FL.3).
SKIP the "### ApiContracts" section entirely (handled by --api-contracts pass AC.3).
Do NOT review flows/*.md or glossary.md — neither is generated in the default (core) run.

BEHAVIOR LOGIC CARDINALITY CHECK — for the behavior-logic artifact: load plans/<active-plan>/artifacts/_scout-bl-inventory.md (pre-extracted BL fragment), then apply all 4 rules from verification-checklist-core-artifacts.md § BehaviorLogic "Cardinality Cross-Check" (total count gap per stack + MAX, category drop, Source File check, orphan file check). Emit the "### BehaviorLogic Cardinality" output block in the review report.

Passed Checks: ONE LINE per rule (\`✓ <rule_id> @ <artifact>\`). NO prose. NO grouping under headings.

Use templates/review-report-template.md as base. Output: plans/<active-plan>/artifacts/core-review-report.md`,
  addBlockedBy: [featureListTaskId] })

// FS.5 (Feature spec reviewer) is NOT dispatched in the default (core) run.
// It runs as Wave FS.5 inside the --feature-specs standalone pass (pipeline-feature-specs.md).
// W7c (ScreenSpec reviewer) removed from main pipeline (2026-05-25).
// ScreenSpec review runs in standalone --screen-specs pass (Wave SS.2).

// --- Wave 7-merge: Combine core review report ---
// Default (core) run: W7-merge merges only core-review-report.md (FS.5 absent).
// Incremental mode: if prior review reports exist in docs/.review-archive/<latest>/,
// merge prior sections for untouched core artifacts with new sections from W7a.
const w7MergeBlockedBy = [w7aTaskId].filter(id => !id.startsWith("SKIPPED:"))
const w7MergeTaskId = TaskCreate({ subject: "Wave7-merge: combine review reports",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Merge core-review-report.md into a single review-report.md (default/core run — no feature-review-batch-*.md present).
Set result = PASS iff failed === 0.
${mode === "incremental" ? `\nINCREMENTAL CARRY-FORWARD: If docs/.review-archive/ exists, read the latest archived review reports. Carry forward review sections for untouched core artifacts (those NOT in the current run's re-generated set). Merge with new W7a sections. Only new + carry-forward sections count toward failed/warnings totals.\n` : ''}
When merging Passed Checks: if same rule_id appears for ≥3 consecutive artifacts, collapse to \`✓ <rule_id> @ <artifact>..<artifact> (<N>/<N>)\`. Drop any line under Passed Checks not matching \`^✓ \` pattern (post-filter for compliance).

Use templates/review-report-template.md format with combined YAML frontmatter.
Output: plans/<active-plan>/artifacts/review-report.md`,
  addBlockedBy: w7MergeBlockedBy })

// --- W7a.cite: RE-mode citation-density check (v11.2.0, RT-F / re-output-contract) ---
// ONLY when the active profile enforces the RE output contract (delphi/oracle, or --legacy).
// Advisory WARN, never a HALT — a legacy codebase legitimately has un-citable inferred content.
// In normal (web) mode this does NOT run → zero regression / no false positives.
if (profile.re_contract === true) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_source_citations.py \
    --plan-dir plans/<active-plan> --re-mode \
    --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  // exit 0 — `citation_density_low` is a WARN appended to the summary; reviewer surfaces it.
  console.log(`[INFO] W7a.cite: RE-mode citation-density checked (profile ${profile.id}, re_contract)`)
}

// ═══════════════════════════════════════════════════════
// PRE-FIX ZONE (W7.5)
// Deterministic structural fixer — stdlib only, no LLM.
// Edge-case safety net: expected near-no-op when FS.2
// FeatureSpec.linked_fr_missing validator is active.
// W7.6 removed 2026-05-25 (root cause fixed at FS.2).
// ═══════════════════════════════════════════════════════

// --- Wave 7.5: Structural fixer (regex-based, no LLM) ---
// Inserts placeholder `**Linked FR:** FR-???` into BR/SM/ALG/INT blocks missing it.
// Decrements `failed` count in review-report.md by resolved structural-only issues.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/structural_fixer.py \
  --plan-dir plans/<active-plan> \
  --incremental-plan-json plans/<active-plan>/artifacts/.incremental-plan.json

// Wave 7.6 removed (2026-05-25): FeatureSpec.linked_fr_missing validator in FS.2
// catches missing Linked FR before W7. W7.5 is retained as edge-case safety net
// for legacy plans and resume scenarios where the FS.2 gate was not present.

// After Wave 7.5, re-read frontmatter to determine branch.
const reportContent = readFile("plans/<active-plan>/artifacts/review-report.md")
const report = parseFrontmatter(reportContent)
if (!report.result) throw new Error("review-report.md missing YAML frontmatter — reviewer must use review-report-template.md")
let currentFailed = parseInt(report.failed ?? 0)

const MAX_FIX_CYCLES = 3
// Clamped by the global cap — fix cycles are NOT exempt (SKILL.md § GLOBAL PARALLEL CAP).
// `|| 5` + Math.max(1, …) guard: junk/0/negative env degrades to the default, never disables the cap.
const MAX_PARALLEL = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
const REBUILD_W8_MAX_PARALLEL = Math.max(1, Math.min(parseInt(process.env.REBUILD_W8_MAX_PARALLEL ?? '5') || 5, MAX_PARALLEL))
let fixCycle = 0
let lastReviewTaskId = w7MergeTaskId

// If W7.5 resolved all issues, this loop is naturally skipped (currentFailed === 0)
while (currentFailed > 0 && fixCycle < MAX_FIX_CYCLES) {
  fixCycle++

  // Extract issues grouped by file from review-report.md
  const reportContent = readFile("plans/<active-plan>/artifacts/review-report.md")
  const issuesByFile = extractIssuesByFile(reportContent)
  const affectedFiles = [...issuesByFile.keys()]

  console.log(`[INFO] W8 cycle ${fixCycle}: ${currentFailed} critical issues across ${affectedFiles.length} file(s)`)

  // Chunk files into batches (cap: REBUILD_W8_MAX_PARALLEL) — batches are CHAINED, not concurrent:
  // every task of batch bi+1 is addBlockedBy ALL tasks of batch bi, so at most
  // REBUILD_W8_MAX_PARALLEL fixers are ever runnable at once (global 5-agent cap).
  const fileBatches = chunk(affectedFiles, REBUILD_W8_MAX_PARALLEL)
  const allFixTaskIds = []
  let prevBatchFixIds = []

  for (const [bi, batch] of fileBatches.entries()) {
    const batchFixIds = []
    for (const filePath of batch) {
      const fileIssues = issuesByFile.get(filePath)
      const fixTaskId = TaskCreate({
        subject: `Wave8.cycle-${fixCycle}.fix-${filePath.split('/').pop().replace('.md', '')}`,
        description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Fix cycle ${fixCycle}/${MAX_FIX_CYCLES} — targeted fix for ONE file.

**File to fix:** \`${filePath}\`

**Issues to resolve (fix ALL of these):**
${fileIssues.map((issue, i) => `${i + 1}. ${issue}`).join('\n')}

Rules:
- Fix ONLY the listed issues in ONLY this file
- Do NOT alter other files or passing sections
- Re-read the file before editing to get current state
- After fixing, verify: each listed issue is addressed

Detected stack: ${stackNote}`,
        addBlockedBy: [lastReviewTaskId, ...prevBatchFixIds]
      })
      batchFixIds.push(fixTaskId)
      allFixTaskIds.push(fixTaskId)
    }
    prevBatchFixIds = batchFixIds  // chain: batch bi+1 waits for ALL of batch bi
  }

  // Single re-reviewer after ALL per-file fixes complete
  const reReviewTaskId = TaskCreate({
    subject: `Wave8.cycle-${fixCycle}: re-reviewer`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Re-verify all fixed files after fix cycle ${fixCycle}.

CHECKLIST LOADING — load references/verification-checklist-universal.md ALWAYS, then:
- If any OPEN issue was in a core artifact (route-list, data-model, screen-list, screen-flow, behavior-logic, permissions, permissions-matrix, user-stories, feature-list, system-overview, architecture): load references/verification-checklist-core-artifacts.md
NOTE: flows/ and features/F###/ are NOT reviewed in the default (core) run — do not load flow or feature-spec checklists here.

Re-read each file that had OPEN issues and verify each issue is resolved. Do NOT re-review files that had no OPEN issues.

Detected stack: ${stackNote}

Overwrite plans/<active-plan>/artifacts/review-report.md with fresh content (frontmatter + markdown body using review-report-template.md).`,
    addBlockedBy: allFixTaskIds
  })

  const freshContent = readFile("plans/<active-plan>/artifacts/review-report.md")
  currentFailed = parseInt(parseFrontmatter(freshContent).failed ?? 0)
  lastReviewTaskId = reReviewTaskId
}

if (currentFailed > 0) {
  // Escalate — do NOT create Wave 9; leave drafts in artifacts/ for manual inspection
  throw new Error(`ESCALATE: ${currentFailed} artifacts still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required. Drafts preserved in plans/<active-plan>/artifacts/.`)
}

// --- Post-W8 contiguity re-check (F9) — report-only, never halts ---
// W8 fix agents may DELETE duplicate entries (SCR###/BL###/etc.) to resolve other validators
// → can reintroduce a gap in an artifact that passed contiguity earlier in the pipeline.
// W9 pre-flight reads the stale PASS from validation-summary.json and would promote a gapped artifact.
// Fix: re-check ALL core artifacts unconditionally in report-only mode.
//
// NOTE on fine-grained flagging: validation-summary.json stores a single shared "id_contiguity"
// slot (last-write-wins across artifacts), so there is no per-artifact slot to query.
// Re-checking all core artifacts is cheap and avoids false negatives from the shared-slot limitation.
{
  const coreArtifacts = [
    "data-model", "screen-list", "behavior-logic", "permissions-matrix",
    "user-stories", "feature-list",
    // NOTE: process-flows is intentionally excluded — it is a multi-file artifact managed
    // by its own --flows pass (FL.1.5 gate). Re-checking it here would require multi-file
    // logic and is out of scope for the core post-W8 sweep.
  ]

  // Re-check all core artifacts unconditionally — cheap and avoids missed gaps.
  const flaggedArtifacts = coreArtifacts

  console.log(`[INFO] Post-W8 contiguity re-check (report-only) over: ${flaggedArtifacts.join(', ')}`)

  for (const artifact of flaggedArtifacts) {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact ${artifact} --plan-dir plans/<active-plan> --report-only \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    // report-only → exit always 0; gaps emitted as warnings in JSON; NEVER halts.
    // WARNING in output → prompt user: re-run the owning wave (e.g. --artifact ${artifact}) to fix the gap.
  }
  console.log("[INFO] Post-W8 contiguity re-check complete. If warnings appeared, re-run the flagged wave before promoting.")
}

// --- Wave 9 pre-flight gate ---
// Runs UNCONDITIONALLY before W9 dispatch. Reads validation-summary.json (core, [RT-C2]) AND
// review-report frontmatter; HALTS pipeline if either signals failure.
//
// [RT-C2] Default run reads ONLY validation-summary.json (core). NEVER reads fs-validation-summary.json
// (that belongs to the --feature-specs pass gate in FS.7 — a FAIL there never blocks the core run).
//
// Halt conditions (any one of these halts; orchestrator surfaces issues, no docs/ writes):
//   - validation-summary.json overall_status === "FAIL"
//   - review-report.md frontmatter `failed > 0`
//   - review-report.md frontmatter `missing > 0` (from .pending markers; not expected in core-only run)
//
// [RT-M3] allCoreDocsPromoted invariant: after gate passes and promote runs, assert all canonical
// core-artifact paths (system/ + generated/ minus glossary — glossary is a --glossary-pass artifact)
// exist AND are non-empty. A silently-empty artifact still HALTs after promotion.
//
// Legacy plans without validation-summary.json: gate on review frontmatter alone; log [INFO].
const summaryPath = `plans/<active-plan>/artifacts/validation/validation-summary.json`
let validatorOverall = "PASS"
if (existsNonEmpty(summaryPath)) {
  const s = JSON.parse(readFile(summaryPath))
  validatorOverall = s.overall_status ?? "PASS"
} else {
  console.log("[INFO] no validation-summary.json — Wave 9 gating on review frontmatter only (legacy plan).")
}
const fm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/review-report.md"))
const reviewFailed = parseInt(fm.failed ?? 0)
const reviewMissing = parseInt(fm.missing ?? 0)
if (validatorOverall === "FAIL" || reviewFailed > 0 || reviewMissing > 0) {
  throw new Error(`Wave 9 gate HALT — validator=${validatorOverall}, review failed=${reviewFailed}, missing=${reviewMissing}. No docs/ writes. Resolve before re-running. Drafts preserved in plans/<active-plan>/artifacts/.`)
}

// Wave 9 — only reached when gate passes (validator !== FAIL AND failed === 0 AND missing === 0)
// Default (core) run promotes system/ + generated/ core docs only (no flows/, no features/, no glossary).
// Incremental mode: promote ONLY re-generated core artifacts. Leave others byte-identical.
const affected_artifacts = (mode === "incremental") ? re_generated_artifacts : ["all"]

// [RT-SC7/FM5] Replace {POPULATED_BY_W6} token in screen-flow.md draft BEFORE promotion so the
// published docs/generated/screen-flow.md never contains a raw template token.
// The --feature-specs pass (FS.1.5) fills real content; default run leaves an HTML comment.
// Stack-neutral (v21.0.0): the `includes('{POPULATED_BY_W6}')` guard means an ALREADY-populated
// section (web OR dfm-form caller-based entries from FS.1.5) is never stubbed — only a still-raw
// placeholder is replaced. Delphi runs go through this path identically to web.
const screenFlowDraft = `plans/<active-plan>/artifacts/screen-flow.md`
if (existsNonEmpty(screenFlowDraft)) {
  const sfContent = readFile(screenFlowDraft)
  if (sfContent.includes('{POPULATED_BY_W6}')) {
    writeFile(screenFlowDraft, sfContent.replace(
      '{POPULATED_BY_W6}',
      '<!-- Feature Entry Points: run /tkm:rebuild-spec --feature-specs to populate -->'
    ))
    console.log('[INFO] W9 pre-promote: {POPULATED_BY_W6} token replaced with HTML comment in screen-flow.md draft')
  }
}

// Wave 9 pre-promote: pure file-ops via script (cp, stub, archive, GC, sha256 manifest)
// [Phase-03] --scope core promotes system/ + generated/ only (no flows/, no features/, no glossary).
// [v5.1.0] docs_root threaded from language dispatch (mode-aware via resolve_docs_root: single-lang en→"docs"; per-lang/non-en→"docs/<primary_lang>").
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --scope core \
  --mode ${mode} \
  --affected-artifacts ${affected_artifacts.join(',') || 'all'} \
  ${mode === "incremental" && flags.with_screen_specs ? `--affected-screens ${(planJson.affected_screens || []).join(',')}` : ""}

// [RT-M3] allCoreDocsPromoted invariant — assert all canonical core-artifact paths exist and non-empty.
// Canonical core paths: system/(overview, architecture, permissions, business-rules) +
// generated/(route-list, api-map, permissions-matrix, entities, user-stories, feature-list, screen-list, screen-flow, behavior-logic)
// NOTE: glossary.md is excluded (--glossary pass artifact). Feature dirs excluded (--feature-specs pass).
// [v5.1.0] docs_root from language dispatch (mode-aware via resolve_docs_root: single-lang en→"docs"; per-lang/non-en→"docs/<primary_lang>")
// [v21.0.0 — profile-aware] Assert a generated artifact ONLY when the profile produces it (produce()).
//   A non-web profile (Delphi/Oracle) maps route-list/api-map → skip, so asserting them
//   unconditionally would HALT a perfect Delphi run at Wave 9. screen-list/screen-flow are gated by
//   screen_source (true for web+Delphi, false for Oracle/generic). The system/ docs + the universal
//   generated docs (entities, user-stories, feature-list, permissions-matrix, behavior-logic) are
//   produced by every profile and stay unconditional.
const coreDocsToAssert = [
  `${docs_root}/system/overview.md`, `${docs_root}/system/architecture.md`,
  `${docs_root}/system/permissions.md`, `${docs_root}/system/business-rules.md`,
  `${docs_root}/generated/permissions-matrix.md`, `${docs_root}/generated/entities.md`,
  `${docs_root}/generated/user-stories.md`, `${docs_root}/generated/feature-list.md`,
  `${docs_root}/generated/behavior-logic.md`,
  ...(produce("route-list")  ? [`${docs_root}/generated/route-list.md`]  : []),
  ...(produce("api-map")     ? [`${docs_root}/generated/api-map.md`]     : []),
  ...(produce("screen-list") ? [`${docs_root}/generated/screen-list.md`] : []),
  ...(produce("screen-flow") ? [`${docs_root}/generated/screen-flow.md`] : []),
]
const missingCoreDocs = coreDocsToAssert.filter(p => !existsNonEmpty(p))
if (missingCoreDocs.length > 0) {
  throw new Error(
    `[RT-M3] allCoreDocsPromoted FAILED — these core artifacts are absent or empty after promotion:\n` +
    missingCoreDocs.map(p => `  - ${p}`).join('\n') + '\n' +
    `Fix: re-run the failed artifact's wave, then re-promote.`
  )
}
console.log(`[INFO] RT-M3 allCoreDocsPromoted: all ${coreDocsToAssert.length} core docs present and non-empty.`)

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. One companion per just-promoted core artifact. Mirrors .nav-metadata.json
// precedent; see references/confidence-report-contract.md.
for (const docPath of coreDocsToAssert) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
    --artifact ${docPath} --project-root .
}

// [GRAPHIFY-INTEGRATION] Advisory spec-coverage check against graph ground truth.
// Runs right after promotion, ONLY when graphify-out/graph.json exists. Never blocks
// (always exit 0): it prints machine-verified completeness (every model class in code
// mentioned in entities.md; every route file mentioned in route-list.md). Echo its
// WARNING lines (if any) in the completion handoff so the user can review.
if (existsNonEmpty("graphify-out/graph.json")) {
  bash: .claude/skills/.venv/bin/python3 \
    .claude/skills/rebuild-spec/scripts/graph_spec_coverage.py \
    --graph graphify-out/graph.json --repo . --docs ${docs_root}
}

// [RT-C5] Wave 9.5 — reverse-index refresh.
// Default (core) run does NOT produce docs/features/ — skip build_source_to_fcode.py when empty.
// The --cursor core flag (Phase-03) advances ONLY last_rebuild_sha (not feature-spec or flows cursors).
// Script safety net: even if invoked, Phase-03 makes it emit empty-but-valid index + exit 0 on no features.
// Double guard: skip here in prose AND rely on the script safety net.
const featureSpecsExist = glob("docs/features/*/technical-spec.md").length > 0
if (featureSpecsExist) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
    --specs-root ${docs_root}/features \
    --docs-root ${docs_root} \
    --state-out docs/.rebuild-state.json \
    --index-out docs/_source-to-fcode.json \
    --cursor core \
    --mode ${mode} \
    --incremental-plan-json plans/<active-plan>/artifacts/.incremental-plan.json
} else {
  // [RT-C5] Core-only run: no feature specs present — advance core cursor only (no index rebuild).
  // build_source_to_fcode.py would emit empty-but-valid index even if called; we skip for clarity.
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
    --specs-root ${docs_root}/features \
    --docs-root ${docs_root} \
    --state-out docs/.rebuild-state.json \
    --index-out docs/_source-to-fcode.json \
    --cursor core \
    --mode ${mode} \
    --incremental-plan-json plans/<active-plan>/artifacts/.incremental-plan.json
  console.log("[INFO] W9.5: docs/features/ absent (core-only run) — reverse-index is empty-but-valid. wave9-complete.flag will still be written.")
}
// NOTE: wave9-complete.flag is written AFTER W9.5, by the doc-writer task below.
// Flag existence ↔ both W9 promote AND W9.5 cursor update completed.

// --- W9.6: Navigation layer (v11.2.0, updated v15.0.0) — runs at pass completion, after promote + W9.5 ---
// Deterministic, stdlib, reads docs/ only. Writes README per docs/ subdir (2-zone — preserves
// user content below <!-- end-generated -->). DOCUMENT-MAP no longer written (v15.0.0: removed;
// was write-only, no reader; META_FILES still recognizes it for deletion of stale copies).
// --pass-complete is retained as an accepted no-op argument for backward compatibility.
// [v13.1.0] This same call also writes the top-level reading-order docs/README.md index for the
// primary root (en labels; no --lang) — single-lang only. In per-lang mode (v18.0.0) there is NO
// root docs/README.md: a purely-generated one is removed (hand-written left untouched); the single
// entry point is docs/<primary>/README.md.
// Per-lang mirror READMEs are written later at
// pipeline-translate.md § Auto-Sync "Step 3.5 — Mirror navigation README" (synced langs only).
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_navigation.py --pass-complete
// All writes go through _path_lib._resolve_guarded (RT-F14): a path escaping docs_root raises.

// [v5.3.3] Auto-sync secondary languages after core promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass core --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass core --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...

// Doc-writer agent: only writes completion flag + self-closes (all file-ops already done, W9.5 already ran)
TaskCreate({ subject: "Wave9: doc-writer — finalize",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Read plans/<active-plan>/artifacts/_promoted-sha256.txt.

Promote passing drafts to layered docs/ paths per claude/skills/_shared/docs-canonical-mapping.md
(profile-conditional, v21.0.0: only artifacts the profile produced have a draft — `promote_drafts.py`
is screen_source/produce()-aware and silently skips absent ones; the authoritative promoted set is
`_promoted-sha256.txt`. A Delphi run promotes screen-list/screen-flow but NOT route-list/api-map; a
headless run promotes neither — do not treat an absent draft as an error):
  system/    ← overview.md, architecture.md, permissions.md, business-rules.md
  generated/ ← route-list.md, api-map.md (web/route-view only), permissions-matrix.md, entities.md, user-stories.md, feature-list.md, screen-list.md, screen-flow.md (when screen_source≠none), behavior-logic.md

NOTE: glossary.md is promoted by the --glossary pass (GL.3), NOT by this task.
NOTE: flows/ is promoted by the --flows pass (FL.5), NOT by this task.
NOTE: features/{slug}/ is promoted by the --feature-specs pass (FS.7), NOT by this task.

Write plans/<active-plan>/artifacts/wave9-complete.flag with this body:
  # Wave 9 complete — <ISO-8601 UTC>
  # Wave 9.5 complete (core cursor advanced by orchestrator)
  # Scope: core
  # Mode: ${mode}
  # Affected artifacts: ${affected_artifacts.join(', ') || 'all'}
  <contents of _promoted-sha256.txt, one line per file>
Call TaskUpdate(status=completed) on this task id BEFORE returning.`,
  addBlockedBy: [lastReviewTaskId] })
```


## Wave 9 completion flag format

`plans/<active>/artifacts/wave9-complete.flag` is the single source of truth that the pipeline finished. Plain text, one line per promoted file. Header lines start with `#` (backward-compatible — existing parsers ignore them).

**Full mode flag (core pass — no feature dirs, no flows, no glossary):**

```
# Wave 9 complete — 2026-05-20T08:34:00Z
# Wave 9.5 complete (core cursor advanced by orchestrator)
# Scope: core
# Mode: full
# Affected artifacts: all
docs/system/overview.md           <sha256>
docs/system/architecture.md       <sha256>
docs/system/permissions.md        <sha256>
docs/system/business-rules.md     <sha256>
docs/generated/route-list.md      <sha256>
docs/generated/api-map.md         <sha256>
docs/generated/permissions-matrix.md <sha256>
docs/generated/entities.md        <sha256>
docs/generated/user-stories.md    <sha256>
docs/generated/feature-list.md    <sha256>
docs/generated/screen-list.md     <sha256>
docs/generated/screen-flow.md     <sha256>
docs/generated/behavior-logic.md  <sha256>
```

NOTE: `docs/system/glossary.md` is written by the `--glossary` pass (GL.3).
NOTE: `docs/flows/` is written by the `--flows` pass (FL.5).
NOTE: `docs/features/` is written by the `--feature-specs` pass (FS.7).

**Incremental mode flag (lists ONLY promoted core files — untouched files omitted):**

```
# Wave 9 complete — 2026-05-20T08:34:00Z
# Wave 9.5 complete (core cursor advanced by orchestrator)
# Scope: core
# Mode: incremental
# Affected artifacts: route-list.md, user-stories.md, feature-list.md
# OOB warnings: 0
# Archive GC: kept latest 5, removed 0 older
docs/generated/route-list.md       <sha256>
docs/generated/user-stories.md     <sha256>
docs/generated/feature-list.md     <sha256>
```

SHA is recorded for audit trail only — reconcile does NOT verify SHA programmatically.
To manually verify integrity: `sha256sum -c wave9-complete.flag` (strip comment lines first).

### Review archive (incremental carry-forward)

W9 doc-writer also archives review reports to `docs/.review-archive/<ISO-timestamp>/` containing `core-review-report.md`, `feature-review-batch-*.md`, `review-report.md`. Next incremental run's W7-merge reads the latest archive to carry forward review sections for untouched artifacts. Archive directory is committed (lightweight markdown).

Archive GC: after writing the new archive subdir, W9 enumerates `docs/.review-archive/*` sorted by name (ISO-8601, lexicographically sortable). If count > 5, delete the oldest (`count - 5`) subdirs. Policy noted in flag header `# Archive GC: kept latest 5, removed N older`.

## Wave 9.5 — reverse-index refresh (core cursor only)

Embedded in the Wave 9 orchestrator dispatch block, **between `promote_drafts.py` and the doc-writer `TaskCreate`** (see Wave 9 block above). This placement guarantees it runs while the orchestrator context is still alive — after the long pipeline, the orchestrator's context window may be exhausted by the time the doc-writer task self-closes, so a post-task bash step would never execute.

**[RT-C5] Core-only behavior:** the default run may not have produced `docs/features/` (if `--feature-specs` has never run). W9.5 uses `--cursor core` (Phase-03) so it advances ONLY `last_rebuild_sha` and leaves `last_feature_spec_run_sha`/`last_flows_run_sha`/`last_glossary_run_sha` untouched. The script also emits an empty-but-valid `_source-to-fcode.json` and exits 0 when `docs/features/` is absent. `wave9-complete.flag` is still written after W9.5 in all cases.

Stdlib-only; no LLM call. Updates `last_rebuild_sha`, `fcode_index_sha`, `doc_shas`, `screen_spec_shas` (when `--screen-specs` standalone pass was run). Does NOT update `last_feature_spec_run_sha`, `last_flows_run_sha`, or `last_glossary_run_sha` — each pass advances its own cursor.

## Core Pass-completion handoff prompt [Validation V3]

After the W9 doc-writer task closes (i.e. `wave9-complete.flag` confirmed on disk), the orchestrator prints the handoff below. Best-effort UX, non-blocking — it mirrors the feature-specs/flows/glossary handoffs so the core pass never ends silently. The next-pass ordering is NOT arbitrary: `--feature-specs` runs first because `--flows` and `--glossary` both require `docs/features/*`.

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write `translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by `translation_sync_gate.py --mode finalize` — echo it VERBATIM. See `references/pipeline-translate.md § Auto-Sync Secondary Languages` for the full plan→translate→finalize contract.

Run after W9 promote, before printing this handoff:

```
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass core --plan-dir plans/<active-plan>
# For each lang in worklist: translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass core --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
# Echo the last stdout line of finalize VERBATIM as the "Secondary languages:" line below.
# DO NOT compose, paraphrase, or invent that line. The re-sync command is always
# /tkm:rebuild-spec --lang <code> — never append a pass suffix.
```

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass core` BEFORE writing the completion flag or printing this handoff. Exit 1 BLOCKS completion. See `references/pipeline-translate.md § Completion gate` for the full gate-run command and fix instructions.

```
─── core pass complete ───
Promoted: docs/system/*.md + docs/generated/*.md (11 core artifacts)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Is the core architecture & data-model documentation accurate and complete?"
Parity (optional): /tkm:audit-doc-parity sweep  # blind-regen semantic parity check (docs ↔ code) — OFF by default, non-blocking
Soundness (optional): /tkm:audit-synthesis-judgment --scope user-stories  # judges US partition/merge soundness (IPE conformance) — non-blocking. NOTE: coverage FAIL (orphans/phantoms) needs --feature-specs first; before that it reports UNVERIFIABLE, not FAIL.
Next (run --feature-specs first — flows & glossary depend on docs/features/*):
  /tkm:rebuild-spec --feature-specs  # Per-feature 4-file specs (run this next)
  /tkm:rebuild-spec --flows          # Process-flows   (requires docs/features/*)
  /tkm:rebuild-spec --glossary       # Glossary        (requires docs/features/*)
  /tkm:rebuild-spec --api-contracts  # API contracts   (core-tier; parallel-safe)
  /tkm:rebuild-spec --screen-specs   # Screen specs    (requires docs/generated/screen-list.md)
  /tkm:write-journal                 # Record this milestone
```

Sibling stale-marker nudges (incremental core run only — `promote_drafts.py --scope core` / the incremental planner writes these markers when the diff touched a downstream area; a full run has none). For each marker still present, append:

```
Note: docs/features/.stale detected — run /tkm:rebuild-spec --feature-specs to refresh.
Note: docs/flows/.stale detected — run /tkm:rebuild-spec --flows to refresh.
Note: docs/system/.glossary.stale detected — run /tkm:rebuild-spec --glossary to refresh.
```

**[optional] Post-merge parity gate.** W7a verifies citation *existence* + wording + structure, but
trusts the cited line — it never re-derives what the code does (anchoring bias). `tkm:audit-doc-parity`
is the code-anchored safety net that does: it blind-regenerates the cited code into the doc's schema
and field-diffs for DRIFT/FABRICATED/MISSING. It is **optional, non-blocking, OFF by default** — it does
NOT change W9 pass/fail. rebuild-spec stays the authority; audit-doc-parity is the after-the-fact check.
Run `/tkm:audit-doc-parity sweep` (or `--feature F###`) any time after a core/feature-spec pass merges.

