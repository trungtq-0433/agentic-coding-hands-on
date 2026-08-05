<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Design-Intent Pass (D.1–D.5) — EXPERIMENTAL, report-only first release

Standalone pass. Loaded only when `--design-intent` flag is set. Requires core pass artifacts
(architecture.md, business-rules.md, entities.md) to exist first. Per-pass artifact isolation:
RT-C2/RT-C3 (same isolation discipline as flows/glossary/jobs/test-cases).

**Single-file synthesis, NO fan-out** (mirrors GL.1–GL.3's glossary shape, the simplest 3-wave
precedent — design-intent is a single small artifact requiring one coherent, cross-cutting
judgment call rather than section-by-section expansion, so splitting it across researchers would
fragment the narrative without buying parallelism).

## EXPERIMENTAL status (F11) — read before wiring this pass into automation

This pass is NOT default-promote. It graduates in stages:
- **(a) Disclaimer header (F11a):** every draft opens with the EXPERIMENTAL/`[INFERRED]`-heavy
  banner from `templates/design-intent-template.md`. Never strip it.
- **(b) Report-only first release (F11b):** D.1–D.4 write and review the artifact ONLY inside
  `plans/<active-plan>/artifacts/`. **There is no auto-promote path in this pass.** Promotion to
  `docs/system/design-intent.md` happens ONLY via D.5, which requires an explicit user
  confirmation (`AskUserQuestion` when interactive, or the `--confirm-promote` flag on a
  subsequent invocation when not). D.4 STOPS after writing the report-only artifact — it never
  calls `promote_drafts.py`.
- **(c) Mode-agnostic density gate (F11c):** D.2 runs `validate_design_intent_density.py`
  unconditionally (not gated on `profile.re_contract` — distinct from
  `re-output-contract.md`'s RE-mode-only check).
- **(d) Go/no-go graduation (F11d):** see `CHANGELOG.md` v26.1.0 sub-entry 3 for the quantified
  criteria (3 pilot repos, differing stacks, `[INFERRED]` ≤25%, zero fabricated citations, human
  confirmation). Not evaluated automatically — recorded as a follow-up gate.

## Preflight

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the
> pass dependency chain).

**Requires:** `docs/system/architecture.md`, `docs/system/business-rules.md`, and
`docs/generated/entities.md` must all exist and be non-empty (else ABORT). No feature-specs
dependency (design-intent is system-level, unlike flows/glossary/test-cases).

**Optional enrichment (used if present, skipped if absent):** `docs/decisions/ADR-*.md`
(highest-trust — degrade gracefully when absent, see § ADR-Graceful Degradation in the
researcher contract), `docs/features/*/business-context.md`.

```js
// Preflight — verify core prerequisites
const corePrereqs = [
  "docs/system/architecture.md",
  "docs/system/business-rules.md",
  "docs/generated/entities.md",
]
for (const p of corePrereqs) {
  if (!existsNonEmpty(p)) {
    throw new Error(
      `ABORT — ${p} missing. Run /tkm:rebuild-spec (core pass) first, then re-run --design-intent.`
    )
  }
}

const adrFiles = glob("docs/decisions/ADR-*.md")
console.log(adrFiles.length === 0
  ? "[INFO] No ADRs found — design-intent will lean on business-rules.md/architecture.md/code-pattern inference (higher [INFERRED] ratio expected)."
  : `[INFO] ${adrFiles.length} ADR(s) found — cite directly, never override.`)

// Incremental cursor check
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const lastDesignIntentSha = state.last_design_intent_run_sha ?? null
const shouldResynth = flags.full || !lastDesignIntentSha || sourceChangedSince(lastDesignIntentSha)
if (flags.full) {
  console.log("[INFO] --full: design-intent regenerating (cursor ignored)")
}
if (!shouldResynth) {
  console.log("[INFO] --design-intent: no source changes since last run — nothing to do. Use --full to force.")
  process.exit(0)
}
```

## Wave D.1 — Design-intent synthesis (single task, no fan-out)

```js
const d1TaskId = TaskCreate({
  subject: "WaveD1: design-intent",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Synthesize inferred "why built this way" architectural narrative.
CONTRACT: references/design-intent-researcher-contract.md (READ IN FULL — the citation-or-
[INFERRED] gate is load-bearing, not optional).
TEMPLATE: templates/design-intent-template.md (EXPERIMENTAL disclaimer banner — do NOT remove).

SOURCES (read in order — highest-trust first, all from docs/, not artifacts/):
1. docs/decisions/ADR-*.md — human-authored, quote directly, never override
2. docs/system/architecture.md + docs/system/business-rules.md
3. source code — AUTHORIZED for cross-cutting pattern detection (CQRS, event-sourcing,
   soft-delete, config-driven flags), cite file:line
4. docs/features/*/business-context.md — optional enrichment

GATE (citation-or-[INFERRED], STRICT): every claim cites an ADR, business-rules.md,
architecture.md, or a file:line, OR is tagged [INFERRED] with a one-clause reason. An unsourced,
untagged assertion is a contract violation.

NON-DUPLICATION BOUNDARY: do not re-narrate business-rules.md's As-Is/To-Be content or
architecture.md's structure description — cite them, never restate them.

Zero distinctive signal (no ADRs, no notable patterns) → still emit the file with an honest
"## Open Questions" zero-signal note. NEVER fabricate architectural narrative to fill space.

OUTPUT: plans/<active-plan>/artifacts/design-intent.md (single file).
After completion, write plans/<active-plan>/artifacts/.design-intent.completed.
Call TaskUpdate(status=completed) on this task id BEFORE returning.`
})
```

## Wave D.2 — Deterministic density validator (F11c)

After D.1 completes (`.design-intent.completed` marker present), run the mode-agnostic density
gate. FAIL halts before D.3.

```js
const d1CompletedMarker = `plans/<active-plan>/artifacts/.design-intent.completed`
if (!exists(d1CompletedMarker)) {
  throw new Error("D.2 HALT — .design-intent.completed marker absent. D.1 may not have completed.")
}

const validatorResult = bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/validate_design_intent_density.py \
  --plan-dir plans/<active-plan> \
  --project-root ${projectRoot} \
  --summary-out plans/<active-plan>/artifacts/validation/design-intent-validation-summary.json`)

if (validatorResult.exitCode !== 0) {
  throw new Error(
    `D.2 HALT — design-intent density gate found uncited, untagged assertions. ` +
    `Fix plans/<active-plan>/artifacts/design-intent.md (cite the source OR tag [INFERRED]), ` +
    `then re-run (--design-intent). ` +
    `Details: plans/<active-plan>/artifacts/validation/design-intent-validation-summary.json`
  )
}
console.log(`[INFO] D.2 passed — design-intent citation density OK`)
```

## Wave D.3 — Design-intent reviewer

After D.2 passes, spawn a single reviewer task. Checklist:
`verification-checklist-design-intent.md` (DI-S1..DI-S6).

```js
const d3TaskId = TaskCreate({
  subject: "WaveD3: design-intent-review",
  description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Review plans/<active-plan>/artifacts/design-intent.md.
Load references/verification-checklist-universal.md + references/verification-checklist-design-intent.md.

CHECKLIST SECTION TARGETING: apply ONLY the DesignIntent section rules from
references/verification-checklist-design-intent.md (DI-S1..DI-S6). SKIP all core artifact
sections — those are handled by their own passes.

**Design-intent validator pre-check (auto-injected):**
D.2 deterministic validator (validate_design_intent_density.py) already checked:
  paragraph-level citation-or-[INFERRED] density (mode-agnostic), disclaimer-banner fence-skip,
  .design-intent.completed marker.
Mark all deterministic-pass rule_ids as [deterministic-pass] — skip them. Focus on semantic
depth (see verification-checklist-design-intent.md § DI-S1..DI-S6): citation accuracy, ADR
fidelity, DRY boundary, disclaimer-banner integrity, zero-signal honesty.

Passed Checks: ONE LINE per rule (\`✓ <rule_id>\`). NO prose.

Use templates/review-report-template.md as base.
Output: plans/<active-plan>/artifacts/design-intent-review-report.md`,
  addBlockedBy: [d1TaskId]
})
```

## Wave D.3.5 — Scoped fix loop (optional)

If `design-intent-review-report.md` reports `failed > 0`, run a fix loop. Max 3 cycles (same
convention as every other pass's fix loop — see `pipeline-flows-glossary.md` § Wave FL.4 for the
canonical shape). Single file, so no per-file wave-chaining is needed — one fix task per cycle.

```js
const MAX_FIX_CYCLES = 3
const diFm = parseFrontmatter(readFile("plans/<active-plan>/artifacts/design-intent-review-report.md"))
let diFailed = parseInt(diFm.failed ?? 0)
let diFixCycle = 0
let diLastReviewId = d3TaskId

while (diFailed > 0 && diFixCycle < MAX_FIX_CYCLES) {
  diFixCycle++
  const issues = extractIssues(readFile("plans/<active-plan>/artifacts/design-intent-review-report.md"))

  const fixId = TaskCreate({
    subject: `WaveD3.5.cycle-${diFixCycle}.fix-design-intent`,
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Fix cycle ${diFixCycle}/${MAX_FIX_CYCLES} for design-intent.md.
Issues: ${issues.join(' | ')}
Rules: fix ONLY the listed issues; preserve the EXPERIMENTAL disclaimer banner verbatim.
SCOPE: plans/<active-plan>/artifacts/design-intent.md only.`,
    addBlockedBy: [diLastReviewId]
  })

  const reReviewId = TaskCreate({
    subject: `WaveD3.5.cycle-${diFixCycle}: re-reviewer`,
    description: `Re-verify design-intent.md after fix cycle ${diFixCycle}.
Load references/verification-checklist-universal.md + references/verification-checklist-design-intent.md (DI-S1..DI-S6).
Overwrite plans/<active-plan>/artifacts/design-intent-review-report.md with fresh content.`,
    addBlockedBy: [fixId]
  })

  const fresh = readFile("plans/<active-plan>/artifacts/design-intent-review-report.md")
  diFailed = parseInt(parseFrontmatter(fresh).failed ?? 0)
  diLastReviewId = reReviewId
}

if (diFailed > 0) {
  throw new Error(`ESCALATE: design-intent still failing after ${MAX_FIX_CYCLES} fix cycles. Manual review required.`)
}
```

## Wave D.4 — Report-only completion (F11b — STOPS here, no docs/ write)

```js
// Pre-flight gate: reads design-intent-validation-summary.json + design-intent-review-report.md
const dvPath = `plans/<active-plan>/artifacts/validation/design-intent-validation-summary.json`
let dValidatorOverall = "PASS"
if (existsNonEmpty(dvPath)) {
  dValidatorOverall = (JSON.parse(readFile(dvPath)).overall_status ?? "PASS")
}
const dFm2 = parseFrontmatter(readFile("plans/<active-plan>/artifacts/design-intent-review-report.md"))
const dFailed2 = parseInt(dFm2.failed ?? 0)
if (dValidatorOverall === "FAIL" || dFailed2 > 0) {
  throw new Error(`D.4 gate HALT — validator=${dValidatorOverall}, review failed=${dFailed2}. No completion flag written.`)
}

// [F9] Write pass-specific completion flag. expectedOutput = the PLAN-DIR artifact, NOT
// docs/system/design-intent.md — this pass has not promoted anything yet (F11b).
bash: echo "# D.4 complete (report-only) — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/design-intent-complete.flag
bash: echo "# Status: EXPERIMENTAL, report-only — NOT promoted to docs/system/design-intent.md" >> plans/<active-plan>/artifacts/design-intent-complete.flag
bash: echo "# Artifact: plans/<active-plan>/artifacts/design-intent.md" >> plans/<active-plan>/artifacts/design-intent-complete.flag

// NO promote_drafts.py call here. NO docs/ write. This is the deliberate F11b stop point.
```

### Confirmation gate (interactive)

```
─── design-intent pass complete (EXPERIMENTAL, report-only) ───
Draft: plans/<active-plan>/artifacts/design-intent.md
Review: plans/<active-plan>/artifacts/design-intent-review-report.md (PASS)

This artifact infers "why" the system was built this way — read it carefully before trusting it.
It has NOT been promoted to docs/system/design-intent.md. Promotion requires your explicit
confirmation (there is no auto-promote path for this pass).

Promote now? [AskUserQuestion: Yes, promote to docs/system/design-intent.md (Recommended if you
have read and agree with the draft) | No, keep as a plan-dir draft only | Not yet — I want to
edit it first]
```

If the user answers **Yes** (interactively) → proceed to Wave D.5 in this same invocation.
If **No** / **Not yet**, or running non-interactively without a prior confirmation → STOP here
and print the non-interactive re-run instruction below. There is no timer, no default-yes, no
silent promotion path.

```
Non-interactive re-run (after you've read the draft and want to promote it):
  /tkm:rebuild-spec --design-intent --confirm-promote
```

## Wave D.5 — Confirmed promote (ONLY on explicit confirmation — `AskUserQuestion` Yes OR `--confirm-promote`)

```js
// D.5 NEVER runs implicitly. It runs only when:
//  (a) the interactive confirmation gate above returned "Yes, promote", OR
//  (b) this invocation was called with --confirm-promote (the deterministic, non-interactive path).
if (!(confirmedInteractively || flags.confirm_promote)) {
  throw new Error("D.5 should not have been reached without explicit user confirmation — this is a contract bug, not a valid path.")
}

// Re-check the gate by re-reading BOTH sources from disk (mirrors J.5's pattern in
// pipeline-jobs.md). D.4's dValidatorOverall/dFailed2 are NOT reused here — on a fresh
// `--confirm-promote` invocation (a separate process from the one that ran D.4), those
// in-memory consts are empty/undefined, which would silently pass an empty-string check.
const dvPathAtD5 = `plans/<active-plan>/artifacts/validation/design-intent-validation-summary.json`
let dValidatorOverallAtD5 = "PASS"
if (existsNonEmpty(dvPathAtD5)) {
  dValidatorOverallAtD5 = (JSON.parse(readFile(dvPathAtD5)).overall_status ?? "PASS")
} else {
  console.log("[INFO] no design-intent-validation-summary.json — D.5 gating on review-report only.")
}
const dFmAtD5 = parseFrontmatter(readFile("plans/<active-plan>/artifacts/design-intent-review-report.md"))
const dFailedAtD5 = parseInt(dFmAtD5.failed ?? 0)
if (dValidatorOverallAtD5 === "FAIL" || dFailedAtD5 > 0) {
  throw new Error(`D.5 gate HALT — validator=${dValidatorOverallAtD5}, review failed=${dFailedAtD5}. No docs/ writes.`)
}

// Promote design-intent to docs/system/design-intent.md — the ONLY place this call appears.
// docs_root from language dispatch (mode-aware via resolve_docs_root).
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode full \
  --scope design-intent

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. Emitted only now, post-promotion (mirrors the "advisory sidecar" note in the
// researcher contract).
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
  --artifact ${docs_root}/system/design-intent.md --project-root .

// Update per-pass cursor (--cursor design-intent advances last_design_intent_run_sha ONLY)
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features \
  --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --cursor design-intent

// Overwrite the completion flag to reflect the now-promoted state.
bash: echo "# D.5 complete (PROMOTED) — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > plans/<active-plan>/artifacts/design-intent-complete.flag
bash: echo "# Promoted: docs/system/design-intent.md (user-confirmed)" >> plans/<active-plan>/artifacts/design-intent-complete.flag
bash: cat plans/<active-plan>/artifacts/_promoted-sha256.txt >> plans/<active-plan>/artifacts/design-intent-complete.flag

// Auto-sync secondary languages after design-intent promote (only reachable post-confirmation).
// See pipeline-translate.md § "Auto-Sync Secondary Languages".
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass design-intent --plan-dir plans/<active-plan>
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass design-intent --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Design-Intent Pass-completion handoff prompt (post-promotion, D.5 only)

```
─── design-intent pass complete (promoted) ───
Promoted: docs/system/design-intent.md (EXPERIMENTAL — still subject to the F11d graduation gate)
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Does design-intent.md's stated rationale match what the ADRs and code actually show?"
Soundness (optional): /tkm:audit-synthesis-judgment --scope design-intent --plan-dir plans/<active-plan>  # judges inference validity (Toulmin) — WARN-only, EXPERIMENTAL, non-blocking
Next:
  /tkm:write-journal             # Record this milestone
```

## Design-Intent Pass — Per-pass artifact isolation (RT-C2 / RT-C3)

| Artifact | Path |
|----------|------|
| Validator summary | `plans/<active-plan>/artifacts/validation/design-intent-validation-summary.json` |
| Review report | `plans/<active-plan>/artifacts/design-intent-review-report.md` |
| Completion flag | `plans/<active-plan>/artifacts/design-intent-complete.flag` (report-only shape until D.5) |

## Design-Intent Pass — Reconcile `expectedOutput` (F9)

Resume/reconcile preflight for this pass checks: `design-intent-complete.flag` present OR
`plans/<active-plan>/artifacts/design-intent.md` exists and non-empty. **`expectedOutput` =
`plans/<active-plan>/artifacts/design-intent.md` (the plan-dir draft) until the user has
confirmed promotion** — NOT `docs/system/design-intent.md`. Once D.5 has run,
`docs/system/design-intent.md` additionally exists, but reconcile does not require it (a
never-promoted, report-only run is a complete, valid pass state — this is the whole point of
F11b).

## Design-Intent Pass — Subagent contracts

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| D.1 | `researcher` | `docs/decisions/ADR-*.md` (optional) + `docs/system/architecture.md` + `docs/system/business-rules.md` + `docs/features/*/business-context.md` (optional) + `design-intent-researcher-contract.md` + `design-intent-template.md` | `plans/<active>/artifacts/design-intent.md` + `.design-intent.completed` |
| D.2 | orchestrator (`validate_design_intent_density.py`) | `design-intent.md` | `design-intent-validation-summary.json`; exit 0/1 |
| D.3 | `reviewer` | `design-intent.md` + `verification-checklist-design-intent.md` (DI-S1..DI-S6) | `design-intent-review-report.md` |
| D.3.5 | `implementer` + `reviewer` | review report + `design-intent.md` | fixed `design-intent.md` |
| D.4 | orchestrator | approved `design-intent.md` | `design-intent-complete.flag` (report-only) + confirmation-gate prompt. **No docs/ write.** |
| D.5 | `promote_drafts.py` + orchestrator (ONLY on explicit confirmation) | confirmed `design-intent.md` | `docs/system/design-intent.md` + updated `design-intent-complete.flag` + state update (`last_design_intent_run_sha`) |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input
happen afterward.
