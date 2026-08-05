<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: API Contracts Pass (AC.1–AC.5)

Standalone pass. Loaded only when `--api-contracts` flag is set. Requires core pass artifacts to exist first. Per-pass artifact isolation: RT-C2/RT-C3.

## Preflight

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the pass dependency chain).

**Requires:** Core pass promoted artifacts: `docs/generated/route-list.md`, `docs/generated/entities.md`, `docs/generated/api-map.md`, `docs/system/permissions.md` must exist (else ABORT).

```js
// Preflight — verify core pass prerequisites
const requiredUpstreams = [
  "docs/generated/route-list.md",
  "docs/generated/entities.md",
  "docs/generated/api-map.md",
  "docs/system/permissions.md",
]
for (const up of requiredUpstreams) {
  if (!existsNonEmpty(up)) {
    throw new Error(
      `ABORT — ${up} missing. Run /tkm:rebuild-spec (core pass) first, then re-run --api-contracts.`
    )
  }
}

// Detect API kind from scout report (if present from a prior core run)
const scoutReportPath = `plans/<active-plan>/artifacts/scout-report.md`
const scoutContent = existsNonEmpty(scoutReportPath) ? readFile(scoutReportPath) : ''
const apiKindMatch = scoutContent.match(/^## Detected API Kind:\s*(\S+)/m)
const apiKind = apiKindMatch ? apiKindMatch[1].trim() : 'rest'

// If no scout report, detect kind directly from file signals
if (!apiKindMatch) {
  // Read references/api-contract-source-patterns.md for detection patterns
  const hasGraphQL = glob("**/*.graphql", "**/*.graphqls", "**/*.gql").length > 0
  const hasProto = glob("**/*.proto").length > 0
  const detectedKind = (hasGraphQL && hasProto) ? 'mixed'
    : hasGraphQL ? 'graphql'
    : hasProto ? 'grpc'
    : 'rest'
  console.log(`[INFO] AC preflight: apiKind=${detectedKind} (detected from file signals, no scout-report)`)
  var apiKind = detectedKind
}

// Incremental cursor check
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const lastApiContractsSha = state.last_api_contracts_run_sha ?? null
const shouldResynth = flags.full || !lastApiContractsSha || sourceChangedSince(lastApiContractsSha)
if (flags.full) {
  console.log("[INFO] --full: api-contracts regenerating (cursor ignored)")
}
if (!shouldResynth) {
  console.log("[INFO] --api-contracts: no source changes since last run — nothing to do. Use --full to force.")
  process.exit(0)
}
```

---

## Wave AC.1 — API Contracts synthesis (with pre-gen estimate gate)

```js
// --- Pre-gen estimate gate (the ONLY oversize safety) ---
// Runs BEFORE creating any research task. Over threshold → chunked path.
const estimateResult = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact api-contracts \
  --route-list docs/generated/route-list.md \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)

console.log(`[INFO] AC.1 pre-gen estimate: ${estimateResult.unit_count} endpoints, est_loc=${estimateResult.est_loc}, shard=${estimateResult.shard}`)

if (estimateResult.shard) {
  // --- SHARD BRANCH: shell → fan-out → merge ---
  // Read references/artifact-sharding.md for merge recipe + fragment contract.

  // AC.1-shell: write skeleton + Conventions + kind headers with {POPULATED_BY_FRAGMENTS} anchors + _slice-plan.json
  const shellTaskId = TaskCreate({
    subject: "WaveAC1-shell: api-contracts skeleton + slice plan",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

SHARD MODE — you are the SHELL researcher (1 of N+1).
Read: references/artifact-sharding.md (merge recipe + fragment contract).
CONTRACT: references/api-contract-researcher-contract.md § Fragment mode.
TEMPLATE: templates/api-contracts-template.md. Detected API Kind: ${apiKind}.

YOUR JOB (skeleton ONLY — do NOT write endpoint entries):
1. Read docs/generated/route-list.md. Group endpoints by resource namespace (first path segment after /api/).
2. Write plans/<active-plan>/artifacts/api-contracts.md with:
   - Full preamble (Project, Generated, Confidence legend)
   - ## Conventions (Shared Messages/Types table, Global Error Contract, Pagination) — populated from source code
   - Per-detected-kind headers (## REST Endpoints / ## GraphQL Operations / ## gRPC Methods) with \`kind:\` tag and \`{POPULATED_BY_FRAGMENTS}\` placeholder under each
3. Write plans/<active-plan>/artifacts/_fragments/api-contracts/_slice-plan.json:
   { "slices": [ {"ordinal": "01", "namespace": "<ns>", "kind": "rest", "endpoints": ["METHOD /path", ...]} ] }
4. mkdir -p plans/<active-plan>/artifacts/_fragments/api-contracts/

SOURCES: docs/generated/route-list.md, docs/generated/entities.md, docs/system/permissions.md.
SOURCE CODE: AUTHORIZED for shared types / error contracts / pagination.
Do NOT write any ### endpoint entries — those are written by fan-out researchers.
Call TaskUpdate(status=completed) BEFORE returning.`
  })

  // AC.1-fanout: one researcher per resource namespace, BATCHED.
  // Batch width clamped by the global cap; junk/0 env degrades to default, never disables the cap.
  const SHARD_BATCH = Math.max(1, Math.min(
    parseInt(process.env.REBUILD_SHARD_MAX_PARALLEL ?? '5') || 5,
    parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5))
  const slicePlan = JSON.parse(readFile("plans/<active-plan>/artifacts/_fragments/api-contracts/_slice-plan.json"))
  const slices = slicePlan.slices
  const allFragTaskIds = []

  const batches = chunk(slices, SHARD_BATCH)
  let prevBatchBlocker = [shellTaskId]
  for (const [bi, batch] of batches.entries()) {
    const batchFragIds = []
    for (const slice of batch) {
      const fragId = TaskCreate({
        subject: `WaveAC1-frag-${slice.ordinal}: api-contracts ${slice.namespace}`,
        description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

SHARD MODE — you are a FRAGMENT researcher.
Read: references/api-contract-researcher-contract.md § Fragment mode.

YOUR SLICE: namespace="${slice.namespace}", kind="${slice.kind}", ordinal=${slice.ordinal}.
Endpoints to document: ${JSON.stringify(slice.endpoints)}

RULES (fragment contract — references/artifact-sharding.md):
- Write ONLY ### entry blocks for your assigned endpoints. NO ## headers, NO ## Conventions.
- Reference shared types by name (defined once in Conventions by shell researcher). Never re-list fields.
- Every entry MUST have Source: file:line citation.
- OUTPUT: plans/<active-plan>/artifacts/_fragments/api-contracts/${slice.ordinal}-${slice.namespace}.md
- GATE: synchronous request/response only.
SOURCE CODE: AUTHORIZED.
Call TaskUpdate(status=completed) BEFORE returning.`,
        addBlockedBy: prevBatchBlocker  // shellTaskId for batch 0; ALL of batch i for batch i+1
      })
      batchFragIds.push(fragId)
      allFragTaskIds.push(fragId)
    }
    // Chain on ALL of the previous batch — blocking on just its last task would let
    // batches overlap and exceed the global 5-agent cap.
    prevBatchBlocker = batchFragIds
  }

  // AC.1-merge: orchestrator merges fragments into skeleton
  // After all fragment tasks complete:
  const fragDir = `plans/<active-plan>/artifacts/_fragments/api-contracts`
  const fragFiles = bash(`ls ${fragDir}/*.md 2>/dev/null | sort`).split('\n').filter(Boolean)
  const slicePlanMerge = JSON.parse(readFile(`${fragDir}/_slice-plan.json`))

  // Group fragments by kind using slice-plan
  const kindMap = {}
  for (const s of slicePlanMerge.slices) {
    kindMap[s.ordinal] = s.kind
  }

  const draft = readFile("plans/<active-plan>/artifacts/api-contracts.md")
  // For each kind, collect and join fragments belonging to that kind
  const kindFrags = {}
  for (const f of fragFiles) {
    const ordinal = f.split('/').pop().split('-')[0]
    const kind = kindMap[ordinal] ?? 'rest'
    kindFrags[kind] = (kindFrags[kind] ?? '') + '\n\n' + readFile(f)
  }
  let merged = draft
  // Replace each {POPULATED_BY_FRAGMENTS} in FIXED TEMPLATE ORDER (rest → graphql → grpc)
  // so fragment content lands under the correct kind header regardless of ordinal numbering.
  for (const kind of ['rest', 'graphql', 'grpc']) {
    const body = kindFrags[kind]
    if (body) {
      // .replace (NOT .replaceAll) — fills only the FIRST remaining placeholder, which is
      // the current kind's anchor because iteration order matches the skeleton's kind order.
      // Each iteration consumes exactly one anchor; the replaceAll below clears empty kinds.
      merged = merged.replace('{POPULATED_BY_FRAGMENTS}', body.trim())
    }
  }
  // Remove any remaining unfilled anchors (kinds with no endpoints)
  merged = merged.replaceAll('{POPULATED_BY_FRAGMENTS}', '')
  writeFile("plans/<active-plan>/artifacts/api-contracts.md", merged)
  bash(`rm -rf ${fragDir}`)

  // Write completion marker
  bash(`touch plans/<active-plan>/artifacts/.api-contracts.completed`)
  console.log(`[INFO] AC.1 shard merge complete: ${fragFiles.length} fragments merged`)

  var acTaskId = allFragTaskIds[allFragTaskIds.length - 1]  // last fragment as blocker for AC.2
} else {
  // --- SINGLE-TASK BRANCH (unchanged) ---
  var acTaskId = TaskCreate({
    subject: "WaveAC1: api-contracts",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST (or load docs/ directly if session context absent).

Synthesize API contracts. CONTRACT: references/api-contract-researcher-contract.md.
TEMPLATE: templates/api-contracts-template.md. SOURCE PATTERNS: references/api-contract-source-patterns.md.
Detected API Kind: ${apiKind}.

SOURCES (read from docs/, not artifacts/ — core pass already promoted):
1. docs/generated/entities.md — entity definitions (MODEL### for Backed-by cross-refs)
2. docs/system/permissions.md — PERM### codes (auth cross-refs)
3. docs/generated/route-list.md — REST endpoint identity (METHOD /path)
4. docs/generated/api-map.md — endpoint-to-handler mapping

SOURCE CODE: AUTHORIZED — FormRequest/Transformer/SDL/.proto via Grep/Read.

GATE (strict): synchronous request/response only; EXCLUDE FCM/WS/subscriptions/outbound gRPC (→ BL###/INT-###).

OUTPUT: plans/<active-plan>/artifacts/api-contracts.md. Empty surface → header + _(no synchronous API surface detected)_.
After completion (incl. empty), write plans/<active-plan>/artifacts/.api-contracts.completed.
Call TaskUpdate(status=completed) BEFORE returning.`
  })
} // end AC.1 estimate gate
```

## Wave AC.2 — Deterministic validator

After AC.1 completes (`.api-contracts.completed` marker present), run the deterministic validator. FAIL halts before AC.3.

```js
const completedMarker = `plans/<active-plan>/artifacts/.api-contracts.completed`
if (!exists(completedMarker)) {
  throw new Error("AC.2 HALT — .api-contracts.completed marker absent. AC.1 may not have completed.")
}

const validatorResult = bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_api_contracts.py \
  --plan-dir plans/<active-plan> \
  --project-root ${projectRoot} \
  --summary-out plans/<active-plan>/artifacts/validation/api-contracts-validation-summary.json`)

if (validatorResult.exitCode !== 0) {
  throw new Error(
    `AC.2 HALT — api-contracts validator found critical issues. ` +
    `Fix plans/<active-plan>/artifacts/api-contracts.md, then re-run (--api-contracts). ` +
    `Details: plans/<active-plan>/artifacts/validation/api-contracts-validation-summary.json`
  )
}
console.log(`[INFO] AC.2 passed — api-contracts validation OK`)
```

## Wave AC.3 — API Contracts reviewer

After AC.2 passes, spawn a single reviewer task. Checklist: `verification-checklist-core-artifacts.md § ApiContracts` (AC-S1..AC-S4).

```js
const ac3TaskId = TaskCreate({
  subject: "WaveAC3: api-contracts-review",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Review plans/<active-plan>/artifacts/api-contracts.md.
Load references/verification-checklist-universal.md + references/verification-checklist-core-artifacts.md.

CHECKLIST SECTION TARGETING: apply ONLY the ### ApiContracts section rules.
SKIP all other core artifact sections — those are handled by the core pass.

**Validator pre-check (auto-injected):**
AC.2 deterministic validator (validate_api_contracts.py) already checked:
  section presence, kind-tag validity, citation presence, duplicate keys,
  shared-type-defined-once, completed marker, empty-surface handling.
Mark all deterministic-pass rule_ids as [deterministic-pass] — skip them.
Focus semantic depth on AC-S1 (citation accuracy spot-check), AC-S2 (no fabricated request/response fields),
AC-S3 (auth norm accurate — gRPC trusted-internal note must be present),
AC-S4 (DRY — no re-listed entity columns).

Passed Checks: ONE LINE per rule (\`✓ <rule_id> @ api-contracts\`). NO prose.

Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/api-contracts-review-report.md`,
  addBlockedBy: [acTaskId]
})
```

## Wave AC.4 — Scoped fix loop (optional)

If `api-contracts-review-report.md` reports `failed > 0`, run a fix loop. Max 3 cycles.

```js
const MAX_FIX_CYCLES = 3
const acFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/api-contracts-review-report.md"))
let acFailed = parseInt(acFm.failed ?? 0)
let acFixCycle = 0
let acLastReviewId = ac3TaskId

while (acFailed > 0 && acFixCycle < MAX_FIX_CYCLES) {
  acFixCycle++
  const reportContent = readFile("plans/<active-plan>/artifacts/api-contracts-review-report.md")
  const issuesByFile = extractIssuesByFile(reportContent)

  const fixId = TaskCreate({
    subject: `WaveAC4.cycle-${acFixCycle}.fix-api-contracts`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Fix cycle ${acFixCycle}/${MAX_FIX_CYCLES} for api-contracts.md.
Issues: ${[...issuesByFile.values()].flat().join(' | ')}
Rules: fix ONLY the listed issues in api-contracts.md; do NOT alter other artifacts.
SCOPE: plans/<active-plan>/artifacts/api-contracts.md only.`,
    addBlockedBy: [acLastReviewId]
  })

  const reReviewId = TaskCreate({
    subject: `WaveAC4.cycle-${acFixCycle}: re-reviewer`,
    description: `Re-verify api-contracts.md after fix cycle ${acFixCycle}.
Load references/verification-checklist-universal.md + references/verification-checklist-core-artifacts.md (### ApiContracts only).
Overwrite plans/<active-plan>/artifacts/api-contracts-review-report.md with fresh content.`,
    addBlockedBy: [fixId]
  })

  const fresh = readFile("plans/<active-plan>/artifacts/api-contracts-review-report.md")
  acFailed = parseInt(parseFrontmatter(fresh).failed ?? 0)
  acLastReviewId = reReviewId
}

if (acFailed > 0) {
  throw new Error(`ESCALATE: api-contracts still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required.`)
}
```

## Wave AC.5 — Promote api-contracts

```js
// Pre-flight gate: reads api-contracts-validation-summary.json + api-contracts-review-report.md
const acvPath = `plans/<active-plan>/artifacts/validation/api-contracts-validation-summary.json`
let acValidatorOverall = "PASS"
if (existsNonEmpty(acvPath)) {
  acValidatorOverall = (JSON.parse(readFile(acvPath)).overall_status ?? "PASS")
} else {
  console.log("[INFO] no api-contracts-validation-summary.json — AC.5 gating on review-report only.")
}
const acFm2 = parseFrontmatter(readFile("plans/<active-plan>/artifacts/api-contracts-review-report.md"))
const acFailed2 = parseInt(acFm2.failed ?? 0)
if (acValidatorOverall === "FAIL" || acFailed2 > 0) {
  throw new Error(`AC.5 gate HALT — validator=${acValidatorOverall}, review failed=${acFailed2}. No docs/ writes.`)
}

// Promote api-contracts to docs/generated/
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode full \
  --scope api-contracts

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. Mirrors .nav-metadata.json precedent; see references/confidence-report-contract.md.
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
  --artifact ${docs_root}/generated/api-contracts.md --project-root .

// Update per-pass cursor
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor api-contracts

// Write pass-specific completion flag
bash: echo "# AC.5 complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/api-contracts-complete.flag
bash: echo "# Scope: api-contracts" >> plans/<active-plan>/artifacts/api-contracts-complete.flag
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/api-contracts-complete.flag

// [v5.3.3] Auto-sync secondary languages after api-contracts promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass api-contracts --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass api-contracts --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### API Contracts Pass-completion handoff prompt

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write `translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by `translation_sync_gate.py --mode finalize` — echo it VERBATIM. See `references/pipeline-translate.md § Auto-Sync Secondary Languages` for the full contract. DO NOT compose, paraphrase, or invent that line. The re-sync command is always `/tkm:rebuild-spec --lang <code>`.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass api-contracts` BEFORE writing the completion flag or printing this handoff. Exit 1 BLOCKS completion. See `references/pipeline-translate.md § Completion gate` for the full gate-run command and fix instructions.

```
--- api-contracts pass complete ---
Promoted: docs/generated/api-contracts.md (REST/GraphQL/gRPC request-response contracts)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Are the API contracts complete and accurate for the codebase?"
Next:
  /tkm:write-journal             # Record this milestone
```

## API Contracts Pass — Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | `plans/<active-plan>/artifacts/validation/api-contracts-validation-summary.json` |
| Review report | `plans/<active-plan>/artifacts/api-contracts-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/api-contracts-complete.flag` |

## AC retry note

On timeout of AC.1 (monolithic or shard), the orchestrator re-runs `estimate_artifact_loc.py --artifact api-contracts`. If `shard:true` and the prior run was monolithic, retry via the shard branch. If the prior run was already sharded and a fragment timed out, re-dispatch only the missing fragment then re-merge (idempotent). See `references/artifact-sharding.md § Idempotent Retry / Resume`.

## API Contracts Pass — Subagent contracts

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| AC.1 | `researcher` | core docs (docs/) + source code + api-contract-researcher-contract.md | `plans/<active>/artifacts/api-contracts.md` + `.api-contracts.completed` |
| AC.2 | orchestrator (`validate_api_contracts.py`) | `api-contracts.md` | `api-contracts-validation-summary.json`; exit 0/1 |
| AC.3 | `reviewer` | `api-contracts.md` + `verification-checklist-core-artifacts.md § ApiContracts` | `api-contracts-review-report.md` |
| AC.4 | `implementer` + `reviewer` | review report + api-contracts.md | fixed api-contracts.md |
| AC.5 | orchestrator (`promote_drafts.py`) | api-contracts.md | `docs/generated/api-contracts.md` + `api-contracts-complete.flag` |
