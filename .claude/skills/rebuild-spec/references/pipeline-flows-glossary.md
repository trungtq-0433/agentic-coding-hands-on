<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Flows Pass (FL.1–FL.5) + Glossary Pass (GL.1–GL.3)
<!-- Updated: Validation 2026-06-01 - two synthesis passes sharing "features must exist" preflight -->
Standalone passes. Loaded only when `--flows` or `--glossary` flag is set. Both passes require feature specs to exist first (`--feature-specs` pass). See `pipeline.md` for wave dep graph. Per-pass artifact isolation: RT-C2/RT-C3.

## Shared Preflight (both `--flows` and `--glossary`)

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the pass dependency chain).

**Requires:** `docs/features/*/technical-spec.md` must exist for at least one feature (else ABORT).

```js
// Shared preflight — runs for both --flows and --glossary
const featureSpecFiles = glob("docs/features/*/technical-spec.md")
if (featureSpecFiles.length === 0) {
  throw new Error(
    `ABORT — No feature specs found under docs/features/. ` +
    `Run /tkm:rebuild-spec --feature-specs first, then re-run this pass.`
  )
}

// [RT-M2] Resolve canonical upstream paths via docs-canonical-mapping.md
const upstreams = {
  dataModel:      "docs/generated/entities.md",          // data-model canonical path
  screenFlow:     "docs/generated/screen-flow.md",       // for FL.1
  behaviorLogic:  "docs/system/business-rules.md",       // BL cross-ref source
  businessRules:  "docs/system/business-rules.md",
  featureSpecs:   "docs/features/*/technical-spec.md",   // FL.1 SM-### source
  businessContext:"docs/features/*/business-context.md", // GL.1 term source
}
// Verify mandatory upstreams for each pass (checked individually in each pass's section)

// Check sibling stale markers and emit sibling nudges
// (each pass nudges about the OTHER sibling if still stale)
```

---

## Flows Pass (`--flows`)

Synthesizes per-entity ProcessFlow files from feature specs + core artifacts.
**Requires (flows-specific):** `docs/generated/entities.md` present (data-model required for entity state analysis).

Invocation: `/tkm:rebuild-spec --flows`

### Flows Preflight (additional, after shared preflight)

```js
if (!existsNonEmpty("docs/generated/entities.md")) {
  throw new Error("ABORT — docs/generated/entities.md missing. Run /tkm:rebuild-spec (core pass) first, then re-run --flows.")
}
// Nudge about glossary sibling
if (existsNonEmpty("docs/system/.glossary.stale")) {
  console.log("[NOTE] docs/system/.glossary.stale detected — run /tkm:rebuild-spec --glossary to refresh glossary after this pass.")
}
// Incremental cursor check
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const lastFlowsSha = state.last_flows_run_sha ?? null
// Cross-feature pass: if anything changed since last_flows_run_sha → re-synth ALL flows (not a subset)
const systemFlowMissing = !existsNonEmpty("docs/flows/system-flow.md")
// --full forces re-synth of ALL flows, ignoring the incremental cursor (pass-scoped --full).
const shouldResynthFlows = flags.full || !lastFlowsSha || sourceChangedSince(lastFlowsSha) || systemFlowMissing
if (flags.full) {
  console.log("[INFO] --full: flows regenerating all outputs (cursor ignored)")
}
if (!shouldResynthFlows) {
  console.log("[INFO] --flows: no source changes since last run — nothing to do. Use --full to force.")
  process.exit(0)
}
```

### Wave FL.1 — ProcessFlow synthesis (former W6.8)

```js
// [RT-C3] Flows pass uses its own task naming (WaveFL1, not Wave6.8)
const flTaskId = TaskCreate({
  subject: "WaveFL1: process-flow",
  description: `${flags.system_flow ? 'NOTICE: --system-flow is deprecated and is an exact no-op alias for --flows. system-flow.md is emitted unconditionally as part of --flows; output contract is identical.\n\n' : ''}Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST (or load docs/generated/feature-list.md directly if session context absent).

Synthesize per-entity process-flows from promoted feature specs. CONTRACT: references/process-flow-researcher-contract.md.
TEMPLATES: templates/process-flow-template.md (Tier-1) + templates/system-flow-template.md (Tier-2).

SOURCES (read in order — all from docs/, not artifacts/):
1. docs/generated/entities.md — entity state fields, enums, relationships
2. docs/generated/screen-flow.md — user-action trigger source
3. docs/system/business-rules.md — scheduled jobs, events (BL### trigger source), guards, invariants
4. docs/features/*/technical-spec.md — per-feature SM-###, source citations

SOURCE CODE: AUTHORIZED — read enum definitions, transition guards, job handlers via Grep/Read.

GATE (strict hard-omit): only entities whose state field has >=2 transitions AND >=2 distinct trigger types (user-action | scheduled | event | derived). Below threshold → emit zero files for that entity. No partial flows.

EVERY transition row MUST carry source file:line. Unsourced claim → Open Questions, NOT a transition row.

OUTPUT: plans/<active-plan>/artifacts/flows/<slug>.md (one per qualifying entity, FLOW### code).
Collision: human-curated (docs/flows/<slug>.md with \`status: human-curated\`) → preserve; ai-draft → overwrite. Name collision → suffix -2/-3.
After completion (including zero-output), write plans/<active-plan>/artifacts/flows/.completed marker.
THEN, when ≥2 Tier-1 flows were emitted, also emit plans/<active-plan>/artifacts/flows/system-flow.md per templates/system-flow-template.md.
Call TaskUpdate(status=completed) on this task id BEFORE returning.`
})
```

### Wave FL.1.5 — process-flows FLOW### renumber + contiguity gate

After FL.1 completes (`.completed` marker present), before FL.2 liveness validator.
Ensures FLOW### codes are contiguous before downstream promotion.

See `references/pipeline-w0-w5.md` § "Renumber+Contiguity Gate (canonical)" for the full gate logic.
Delta for process-flows:
- Completion guard: check for `flows/.completed` marker (FL.1 writes it on success); absent → HALT.
- `--artifact process-flows` resolves to `artifacts/flows/*.md` (multi-file). Zero files → no-op exit 0 (valid: project had no qualifying entities).
- `--summary-out` uses `flow-validation-summary.json` (not `validation-summary.json`) per RT-C3.

```js
// F2: async-TaskCreate guard — FL.1 task must have written the .completed marker
const fl1CompletedMarker = `plans/<active-plan>/artifacts/flows/.completed`
if (!exists(fl1CompletedMarker)) {
  throw new Error("FL.1.5 HALT — flows/.completed marker absent. FL.1 may not have completed.")
}
// Apply "Renumber+Contiguity Gate (canonical)" with artifact=process-flows
// Delta: --summary-out targets flow-validation-summary.json (RT-C3 isolation)
const isFull = mode === "full"
if (isFull) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
    --artifact process-flows --plan-dir plans/<active-plan>
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
    --artifact process-flows --plan-dir plans/<active-plan> \
    --summary-out plans/<active-plan>/artifacts/validation/flow-validation-summary.json
  // exit 1 → FAIL → HALT; exit 2 → internal error → halt  [HALT scoped to FULL mode]
} else {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
    --artifact process-flows --plan-dir plans/<active-plan> --report-only \
    --summary-out plans/<active-plan>/artifacts/validation/flow-validation-summary.json
  console.log("[INFO] FL.1 process-flows renumber skipped (incremental: IDs frozen)")
}
```

### Wave FL.2 — Liveness validator (former W6.85)

After FL.1 completes (`.completed` marker present), run the deterministic validator. FAIL halts before FL.3.

```js
// [RT-C3] Flows pass uses flow-validation-summary.json (not validation-summary.json)
const flowsCompletedMarker = `plans/<active-plan>/artifacts/flows/.completed`
if (!exists(flowsCompletedMarker)) {
  throw new Error("FL.2 HALT — flows/.completed marker absent. FL.1 may not have completed.")
}

const validatorResult = bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_process_flow.py \
  --plan-dir plans/<active-plan> \
  --project-root ${projectRoot} \
  --summary-out plans/<active-plan>/artifacts/validation/flow-validation-summary.json`)

if (validatorResult.exitCode !== 0) {
  throw new Error(
    `FL.2 HALT — process-flow validator found critical issues. ` +
    `Fix plans/<active-plan>/artifacts/flows/*.md, then re-run (--flows). ` +
    `Details: plans/<active-plan>/artifacts/validation/flow-validation-summary.json`
  )
}
console.log(`[INFO] FL.2 passed — process-flow validation OK`)
```

### Wave FL.3 — ProcessFlow reviewer [RT-C3]

After FL.2 passes, spawn a single reviewer task for all flow files. Checklist: `verification-checklist-flows.md` (PF-S1..PF-S6, carved from W7a core checklist in Phase-02).

```js
// [RT-C3] Flows pass uses flow-review-report.md (not review-report.md or feature-review-report.md)
const fl3TaskId = TaskCreate({
  subject: "WaveFL3: process-flow-review",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Review ALL flow files in plans/<active-plan>/artifacts/flows/*.md.
Load references/verification-checklist-universal.md + references/verification-checklist-flows.md.

CHECKLIST SECTION TARGETING: apply ONLY the ProcessFlow section rules from references/verification-checklist-flows.md (PF-S1..PF-S6).
SKIP all core artifact sections and FeatureSpec section — those are handled by their own passes.

**Flow validator pre-check (auto-injected):**
FL.2 deterministic validator (validate_process_flow.py) already checked:
  citation presence, FLOW### regex/uniqueness, state-in-enum-or-derived, .completed marker,
  strict gate (>=2 transitions AND >=2 trigger types), possible_stuck_state (liveness backstop, warning),
  sm_crossref_missing (SM/FLOW DRY, warning),
  SystemFlow.composes_missing, SystemFlow.composes_insufficient, SystemFlow.handoffs_missing, SystemFlow.handoff_citation_missing, SystemFlow.inventory_missing, SystemFlow.inventory_incomplete, SystemFlow.phantom_flow_ref.
Mark all deterministic-pass rule_ids as [deterministic-pass] — skip them. Focus on semantic depth (see verification-checklist-flows.md § Semantic review rules PF-S1..PF-S6).

Passed Checks: ONE LINE per rule (\`✓ <rule_id> @ <flow-slug>\`). NO prose.

Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/flow-review-report.md`,
  addBlockedBy: [flTaskId]
})
```

### Wave FL.4 — Scoped fix loop (optional, same pattern as FS.6)

If `flow-review-report.md` reports `failed > 0`, run a fix loop. Max 3 cycles.

```js
const MAX_FIX_CYCLES = 3
const flFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/flow-review-report.md"))
let flFailed = parseInt(flFm.failed ?? 0)
let flFixCycle = 0
let flLastReviewId = fl3TaskId

while (flFailed > 0 && flFixCycle < MAX_FIX_CYCLES) {
  flFixCycle++
  const reportContent = readFile("plans/<active-plan>/artifacts/flow-review-report.md")
  const issuesByFile = extractIssuesByFile(reportContent)
  const affectedFiles = [...issuesByFile.keys()]
  const allFlFixIds = []

  // Bounded-wave dispatch (global 5-agent cap): one fix task per flagged flow file,
  // wave-chained at ≤min(REBUILD_W8_MAX_PARALLEL, REBUILD_MAX_PARALLEL) — fix cycles are not
  // exempt from the global cap. Guards degrade junk/0 env to defaults, never disable the cap.
  const FL_FIX_CAP = Math.max(1, Math.min(
    parseInt(process.env.REBUILD_W8_MAX_PARALLEL ?? '5') || 5,
    parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5))
  let prevFlWaveIds = [], flWaveIds = []
  for (const [fi, filePath] of affectedFiles.entries()) {
    if (fi > 0 && fi % FL_FIX_CAP === 0) { prevFlWaveIds = flWaveIds; flWaveIds = [] }
    const fileIssues = issuesByFile.get(filePath)
    const fixId = TaskCreate({
      subject: `WaveFL4.cycle-${flFixCycle}.fix-${filePath.split('/').pop().replace('.md', '')}`,
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Fix cycle ${flFixCycle}/${MAX_FIX_CYCLES} for flow file: \`${filePath}\`
Issues: ${fileIssues.join(' | ')}
Rules: fix ONLY the listed issues; do NOT alter other flow files; re-read before editing.
SCOPE: flow files only (plans/<active-plan>/artifacts/flows/*.md). Do NOT edit feature specs or core artifacts.`,
      addBlockedBy: [flLastReviewId, ...prevFlWaveIds]
    })
    flWaveIds.push(fixId)
    allFlFixIds.push(fixId)
  }

  const reReviewId = TaskCreate({
    subject: `WaveFL4.cycle-${flFixCycle}: re-reviewer`,
    description: `Re-verify all fixed flow files after fix cycle ${flFixCycle}.
Load references/verification-checklist-universal.md + references/verification-checklist-flows.md (PF-S1..PF-S6).
Overwrite plans/<active-plan>/artifacts/flow-review-report.md with fresh content.`,
    addBlockedBy: allFlFixIds
  })

  const fresh = readFile("plans/<active-plan>/artifacts/flow-review-report.md")
  flFailed = parseInt(parseFrontmatter(fresh).failed ?? 0)
  flLastReviewId = reReviewId
}

if (flFailed > 0) {
  throw new Error(`ESCALATE: ${flFailed} flow(s) still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required. Drafts preserved in plans/<active-plan>/artifacts/flows/.`)
}
```

### Wave FL.5 — Promote flows [RT-C3, RT-C4]

```js
// [RT-C3] Flows pass pre-flight gate: reads flow-validation-summary.json + flow-review-report.md
const flvPath = `plans/<active-plan>/artifacts/validation/flow-validation-summary.json`
let flValidatorOverall = "PASS"
if (existsNonEmpty(flvPath)) {
  flValidatorOverall = (JSON.parse(readFile(flvPath)).overall_status ?? "PASS")
} else {
  console.log("[INFO] no flow-validation-summary.json — FL.5 gating on flow-review-report.md only.")
}
const flFm2 = parseFrontmatter(readFile("plans/<active-plan>/artifacts/flow-review-report.md"))
const flFailed2 = parseInt(flFm2.failed ?? 0)
if (flValidatorOverall === "FAIL" || flFailed2 > 0) {
  throw new Error(`FL.5 gate HALT — validator=${flValidatorOverall}, review failed=${flFailed2}. No docs/ writes.`)
}

// Promote flows to docs/flows/
// [v5.1.0] docs_root from language dispatch (mode-aware via resolve_docs_root: single-lang en→"docs"; per-lang/non-en→"docs/<primary_lang>")
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode full \
  --scope flows

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. One companion per just-promoted flow file (Tier-1 entity flows + system-flow.md).
// Mirrors .nav-metadata.json precedent; see references/confidence-report-contract.md.
bash: for f in ${docs_root}/flows/*.md; do \
  case "$(basename "$f")" in confidence-report_*) continue ;; esac; \
  .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
    --artifact "$f" --project-root . ; \
done

// [RT-C4 + V7] Clear the flows stale marker on successful promote
bash: rm -f docs/flows/.stale

// Update per-pass cursor (--cursor flows advances last_flows_run_sha ONLY — does NOT touch last_rebuild_sha or last_feature_spec_run_sha)
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor flows

// [RT-C3] Write pass-specific completion flag
bash: echo "# FL.5 complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/flows-complete.flag
bash: echo "# Scope: flows (all entities)" >> plans/<active-plan>/artifacts/flows-complete.flag
// [item ④ / RT-C3] Embed this pass's OWN promote manifest (docs/flows/*) for independent `sha256sum -c` audit.
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/flows-complete.flag

// [v5.3.3] Auto-sync secondary languages after flows promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass flows --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass flows --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Flows Pass-completion handoff prompt [Validation V3]

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write `translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by `translation_sync_gate.py --mode finalize` — echo it VERBATIM. See `references/pipeline-translate.md § Auto-Sync Secondary Languages` for the full contract. DO NOT compose, paraphrase, or invent the `Secondary languages:` line — copy it byte-for-byte from script stdout. Same gate applies to the glossary handoff below.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass flows` BEFORE writing the completion flag or printing this handoff. Exit 1 BLOCKS completion. See `references/pipeline-translate.md § Completion gate` for the full gate-run command and fix instructions.

```
─── flows pass complete ───
Promoted: docs/flows/*.md (per-entity process-flow files)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Are the process-flows complete and consistent with the feature specs?"
Soundness (optional): /tkm:audit-synthesis-judgment --scope all  # judges partition/US/inference soundness — non-blocking
Next:
  /tkm:rebuild-spec --glossary   # Synthesize glossary (if not yet done)
  /tkm:write-journal             # Record this milestone
```

If `docs/system/.glossary.stale` still set: `Note: --glossary also stale — run /tkm:rebuild-spec --glossary.`

## Flows Pass — Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | `plans/<active-plan>/artifacts/validation/flow-validation-summary.json` |
| Review report | `plans/<active-plan>/artifacts/flow-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/flows-complete.flag` |

## Flows Pass — Subagent contracts

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| FL.1 | `researcher` | `docs/generated/entities.md` + `docs/generated/screen-flow.md` + `docs/system/business-rules.md` + `docs/features/*/technical-spec.md` + `process-flow-researcher-contract.md` + `process-flow-template.md` | `plans/<active>/artifacts/flows/*.md` (FLOW### per qualifying entity) + `flows/.completed` + `flows/system-flow.md` (Tier-2, when ≥2 Tier-1 flows) |
| FL.2 | orchestrator (`validate_process_flow.py`) | `flows/*.md` | `flow-validation-summary.json` |
| FL.3 | `reviewer` | `flows/*.md` + `verification-checklist-flows.md` (PF-S1..PF-S6) | `flow-review-report.md` |
| FL.4 | `implementer` (per-file, max 3 cycles) | `flow-review-report.md` + affected flow drafts | updated flow drafts → re-reviewer |
| FL.5 | `promote_drafts.py` + orchestrator | approved flow drafts | `docs/flows/*.md` + `flows-complete.flag` + state update |

---

## Glossary Pass (`--glossary`)

Synthesizes the project glossary from data-model entity names + feature business-context prose.
**Requires (glossary-specific):** `docs/features/*/business-context.md` must exist (business-context needed for term sourcing).

Invocation: `/tkm:rebuild-spec --glossary`

### Glossary Preflight (additional, after shared preflight)

```js
const businessContextFiles = glob("docs/features/*/business-context.md")
if (businessContextFiles.length === 0) {
  throw new Error(
    `ABORT — No business-context.md files found under docs/features/. ` +
    `Run /tkm:rebuild-spec --feature-specs first, then re-run --glossary.`
  )
}
if (!existsNonEmpty("docs/generated/entities.md")) {
  throw new Error("ABORT — docs/generated/entities.md missing. Run /tkm:rebuild-spec (core pass) first, then re-run --glossary.")
}
// Nudge about flows sibling
if (existsNonEmpty("docs/flows/.stale")) {
  console.log("[NOTE] docs/flows/.stale detected — run /tkm:rebuild-spec --flows to refresh process-flows.")
}
// Incremental cursor check
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const lastGlossarySha = state.last_glossary_run_sha ?? null
// --full forces re-synth of the glossary, ignoring the incremental cursor (pass-scoped --full).
const shouldResynthGlossary = flags.full || !lastGlossarySha || sourceChangedSince(lastGlossarySha)
if (flags.full) {
  console.log("[INFO] --full: glossary regenerating all outputs (cursor ignored)")
}
if (!shouldResynthGlossary) {
  console.log("[INFO] --glossary: no source changes since last run — nothing to do. Use --full to force.")
  process.exit(0)
}
```

### Wave GL.1 — Glossary synthesis (former W6.9)

```js
// [RT-C3] Glossary pass uses its own task naming (WaveGL1, not Wave6.9)
const gl1TaskId = TaskCreate({
  subject: "WaveGL1: glossary",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST (or load docs/generated/feature-list.md directly if session context absent).

Synthesize Glossary from docs/generated/entities.md + business-context files across all feature specs.
Output: plans/<active-plan>/artifacts/glossary.md

SOURCES (read in order — all from docs/, not artifacts/):
1. docs/generated/entities.md — entity names, field names, technical terms
2. docs/features/*/business-context.md — plain-language term usage

FORMAT (one entry per term, sorted alphabetically):
# Glossary

## <Term>
**Definition:** <1-2 sentence plain-language definition>
**Technical alias:** <entity/field name from entities.md if different>
**Used in:** <comma-separated list of F### codes where the term appears>

RULES:
- Include every entity from docs/generated/entities.md
- Include domain terms that appear in >=2 business-context files
- No technical jargon in definitions (target: non-developer reader)
- Do NOT duplicate entries; prefer the most user-facing term as the heading
Call TaskUpdate(status=completed) on this task id BEFORE returning.`
})
```

### Wave GL.2 — Glossary reviewer [RT-C3]

After GL.1 completes, spawn a single reviewer task. No deterministic validator for glossary (no exit-code gate).

```js
// [RT-C3] Glossary pass uses glossary-review-report.md (not review-report.md)
const gl2TaskId = TaskCreate({
  subject: "WaveGL2: glossary-review",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Review the synthesized glossary at plans/<active-plan>/artifacts/glossary.md.
Load references/verification-checklist-universal.md + references/verification-checklist-glossary.md.

CHECKLIST SECTION TARGETING: apply the Glossary rules from references/verification-checklist-glossary.md (GL-R1..GL-R6) ONLY.
SKIP all core artifact sections and FeatureSpec/ProcessFlow sections — handled by their own passes.

See verification-checklist-glossary.md for all GL-R1..GL-R6 semantic review rules and critical edge cases.

Passed Checks: ONE LINE per rule (`✓ <rule_id>`). NO prose.

Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/glossary-review-report.md`,
  addBlockedBy: [gl1TaskId]
})
```

### Wave GL.3 — Promote glossary [RT-C3, RT-C4]

```js
// [RT-C3] Glossary pass pre-flight gate: reads glossary-review-report.md
// Note: no deterministic validator for glossary — gate on review report alone
const glFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/glossary-review-report.md"))
const glFailed = parseInt(glFm.failed ?? 0)
if (glFailed > 0) {
  throw new Error(`GL.3 gate HALT — review failed=${glFailed}. No docs/ writes. Fix issues and re-run.`)
}

// Promote glossary to docs/system/glossary.md via promote_drafts.py (consistent with other passes)
// [RT-H2] scope=glossary promotes ONLY glossary.md; does not touch core artifacts or features.
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode full \
  --scope glossary

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. Mirrors .nav-metadata.json precedent; see references/confidence-report-contract.md.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
  --artifact ${docs_root}/system/glossary.md --project-root .

// [RT-H1] Refresh doc_shas for glossary.md (the only synthesis artifact tracked in doc_shas)
// This prevents permanent forced-full on the next core run due to doc_shas desync
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor glossary

// [RT-C4 + V7] Clear the glossary stale marker on successful promote
bash: rm -f docs/system/.glossary.stale

// [RT-C3] Write pass-specific completion flag
bash: echo "# GL.3 complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/glossary-complete.flag
bash: echo "# Promoted: docs/system/glossary.md" >> plans/<active-plan>/artifacts/glossary-complete.flag
// [item ④ / RT-C3] Embed this pass's OWN promote manifest (docs/system/glossary.md) for independent `sha256sum -c` audit.
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/glossary-complete.flag

// [v5.3.3] Auto-sync secondary languages after glossary promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass glossary --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass glossary --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Glossary Pass-completion handoff prompt [Validation V3]

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write `translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by `translation_sync_gate.py --mode finalize` — echo it VERBATIM. DO NOT compose, paraphrase, or invent that line. The re-sync command is always `/tkm:rebuild-spec --lang <code>`.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass glossary` BEFORE writing the completion flag or printing this handoff. Exit 1 BLOCKS completion. See `references/pipeline-translate.md § Completion gate` for the full gate-run command and fix instructions.

```
─── glossary pass complete ───
Promoted: docs/system/glossary.md
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Is the glossary terminology consistent with the codebase and business domain?"
Soundness (optional): /tkm:audit-synthesis-judgment --scope system  # judges system-tier artifact soundness — non-blocking
Next:
  /tkm:rebuild-spec --flows    # Synthesize process-flows (if not yet done)
  /tkm:write-journal           # Record this milestone
```

If `docs/flows/.stale` still set: `Note: --flows also stale — run /tkm:rebuild-spec --flows.`

## Glossary Pass — Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | (none — no deterministic validator for glossary) |
| Review report | `plans/<active-plan>/artifacts/glossary-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/glossary-complete.flag` |

## Glossary Pass — Subagent contracts

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| GL.1 | `researcher` | `docs/generated/entities.md` + `docs/features/*/business-context.md` | `plans/<active>/artifacts/glossary.md` + `TaskUpdate(status=completed)` |
| GL.2 | `reviewer` | `glossary.md` + `verification-checklist-glossary.md` (GL-R1..GL-R6) | `glossary-review-report.md` |
| GL.3 | orchestrator | approved `glossary.md` | `docs/system/glossary.md` + `glossary-complete.flag` + state update (last_glossary_run_sha) |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input happen afterward.

---

## Cross-pass notes

- Both passes read feature specs from `docs/features/` (the promoted canonical path), NOT from `plans/<active-plan>/artifacts/features/`. This means the `--feature-specs` pass (or a prior core run that generated feature specs) must have successfully promoted before these passes can run.
- The `--flows` and `--glossary` passes are independent of each other — they may run in either order or in parallel sessions.
- Neither pass re-generates or modifies feature specs, core artifacts, or state cursors owned by other passes.
