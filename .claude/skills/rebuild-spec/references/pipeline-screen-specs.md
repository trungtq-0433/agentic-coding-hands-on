<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Screen-Specs Pass (SS.1–SS.3)
Standalone pass. Loaded only when `--screen-specs` flag is set. See `pipeline.md` for wave dep graph.

## Screen-Specs Pass (`--screen-specs`)

Standalone pass — runs independently of the main pipeline.
**Requires:** `docs/generated/screen-list.md` present (main rebuild must complete first).

Invocation: `/tkm:rebuild-spec --screen-specs`

### Preflight

> Prerequisites: see SKILL.md § Pass ordering & prerequisites (single source of truth for the pass dependency chain).

1. Verify `docs/generated/screen-list.md` exists and is non-empty. ABORT if missing with: `"ABORT — docs/generated/screen-list.md missing. Run /tkm:rebuild-spec (core pass) first, then re-run --screen-specs."`
2. Read SCR### codes: `grep -oP 'SCR\d{3,4}[a-z]?' docs/generated/screen-list.md | sort -u`
3. Incremental check: if `--full` present → treat ALL screens as affected, ignoring `screen_spec_shas` (pass-scoped `--full`); log `[INFO] --full: screen-specs regenerating all outputs (cursor ignored)`. Else if `docs/.rebuild-state.json` exists and `screen_spec_shas` present, emit `affected_screens` list (screens whose SCR### section hash changed since last pass). If state absent → treat all screens as affected.

### Wave SS.1 — ScreenSpec fan-out (same logic as former W2.5)

```js
const scrCodes = bash(`grep -oP 'SCR\\d{3,4}[a-z]?' docs/generated/screen-list.md | sort -u`).split('\n').filter(Boolean)
// Pattern note: `[a-z]?` captures H4/H5 lettered variants (SCR006a, SCR006b).
// Base code (SCR006) captured separately when standalone in screen-list. sort -u treats SCR006 and SCR006a as distinct.
// Incremental filter: use affected_screens from state if available
const scrCodesToProcess = /* incremental filter applied here, same logic as former W2.5 incremental block */

const SCREEN_SPEC_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_SCREEN_SPEC_BATCH_SIZE ?? '5') || 5)  // junk/0 env → default, never cap-off
const scrBatches = chunk(scrCodesToProcess, SCREEN_SPEC_BATCH_SIZE)
const screenSpecTaskIds = []

// Bounded-wave dispatch (global 5-agent cap): batch tasks are wave-chained at ≤REBUILD_MAX_PARALLEL —
// without this, ceil(#SCR/5) batch agents would all be runnable at once.
// Wave width is the GLOBAL cap, NOT SCREEN_SPEC_BATCH_SIZE: batch size = screens per agent
// (workload knob); wave width = concurrent agents (concurrency knob). Never conflate them.
const MAX_PARALLEL = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
let prevSs1WaveIds = [], ss1WaveIds = []
for (const [i, batch] of scrBatches.entries()) {
  if (i > 0 && i % MAX_PARALLEL === 0) { prevSs1WaveIds = ss1WaveIds; ss1WaveIds = [] }
  const batchId = TaskCreate({
    subject: `WaveSS1.batch-${pad2(i+1)}: screen-specs (${batch[0]}..${batch.at(-1)})`,
    description: `Session context: read plans/<active-plan>/artifacts/_session-context.md if present; otherwise load docs/generated/screen-list.md + docs/generated/entities.md directly.
Generate ScreenSpec for ${batch.length} screens: ${batch.join(', ')}.
Template: templates/screen-spec-template.md. Contract: references/screen-spec-researcher-contract.md.
Write drafts to: plans/<active-plan>/artifacts/screens/{SCR###_Name}/spec.md`,
    addBlockedBy: prevSs1WaveIds  // [] for the first wave
  })
  ss1WaveIds.push(batchId)
  screenSpecTaskIds.push(batchId)
}
```

### Wave SS.2 — ScreenSpec reviewer (same logic as former W7c)

```js
const SCREEN_SPEC_REVIEW_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_SCREEN_SPEC_REVIEW_BATCH_SIZE || "5") || 5)
const reviewBatches = chunk(scrCodesToProcess, SCREEN_SPEC_REVIEW_BATCH_SIZE)
// Bounded-wave dispatch (global 5-agent cap): reviewer batch tasks wave-chained at
// ≤REBUILD_MAX_PARALLEL (concurrency knob) — NOT the review batch size (workload knob).
const MAX_PARALLEL = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)  // self-contained: re-declared per block
let prevSs2WaveIds = [], ss2WaveIds = []
for (const [i, batch] of reviewBatches.entries()) {
  if (i > 0 && i % MAX_PARALLEL === 0) { prevSs2WaveIds = ss2WaveIds; ss2WaveIds = [] }
  const ss2Id = TaskCreate({
    subject: `WaveSS2.batch-${pad2(i+1)}: screen-spec-review (${batch[0]}..${batch.at(-1)})`,
    description: `Review ScreenSpec files for [${batch.join(', ')}] using verification-checklist-screen-spec.md.
Input: plans/<active-plan>/artifacts/screens/{SCR###}/spec.md. Output: plans/<active-plan>/artifacts/screen-review-batch-${pad2(i+1)}.md`,
    addBlockedBy: [...screenSpecTaskIds, ...prevSs2WaveIds]
  })
  ss2WaveIds.push(ss2Id)
}
```

### Wave SS.3 — Promote

```js
// After all SS.2 reviewers pass:
// [v5.1.0] docs_root from language dispatch
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${docs_root} \
  --mode ${mode} \
  --affected-screens ${scrCodesToProcess.join(',')}

// [v25.2.0] A1 confidence-report sidecar — best-effort, advisory, exit 0 always; NEVER gates
// promotion. Mirrors .nav-metadata.json precedent; see references/confidence-report-contract.md.
// Directory may or may not carry the SCR###_Name suffix — try both, first match wins.
bash: for scr in ${scrCodesToProcess.join(' ')}; do \
  for f in ${docs_root}/screens/${scr}_*/spec.md ${docs_root}/screens/${scr}/spec.md; do \
    [ -f "$f" ] && .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
      --artifact "$f" --project-root . && break; \
  done; \
done

// Then update screen_spec_shas in .rebuild-state.json
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
  --specs-root ${docs_root}/features --docs-root ${docs_root} \
  --state-out docs/.rebuild-state.json \
  --index-out docs/_source-to-fcode.json \
  --mode ${mode}

// [v24.0.0] Refresh navigation so the just-promoted docs/screens/SCR###/ specs surface in the
// reading-order README (layer-4 screens entry) and so the per-feature README screen tables pick up
// the SCR### links. Mirrors the core-pass W9.6 nav step. PRIMARY root only — secondary-lang mirrors
// are refreshed by the translation auto-sync Step 3.5 below. Advisory, exit 0 always.
// docs_root is mode-aware (single-lang "docs" → no --lang/en labels; per-lang "docs/<primary>" →
// --lang <primary>). Derive the lang from docs_root's last segment — no separate primary_lang var needed.
const navLangFlag = (docs_root === "docs") ? "" : `--lang ${docs_root.split("/").pop()}`
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_navigation.py \
  --docs-root ${docs_root} ${navLangFlag} --pass-complete

// [v5.3.3] Auto-sync secondary languages after screen-specs promote.
// See pipeline-translate.md § "Auto-Sync Secondary Languages" for the full plan→translate→finalize contract.
//
// Step 1: get worklist
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan --pass screen-specs --plan-dir plans/<active-plan>
// Step 2: for each lang in worklist, translate listed artifacts (TR.2) + promote to docs/<lang>/ (TR.4)
// Step 3: finalize — verifies docs/<lang>/, updates cursors, writes translation-sync-report.json,
//         prints "Secondary languages: ..." as its LAST stdout line
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize --pass screen-specs --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status> ...
```

### Screen-specs Pass-completion handoff prompt [Validation V3]

After Wave SS.3 promote closes, the orchestrator prints the handoff below. Best-effort UX, non-blocking — it mirrors the core/feature-specs/flows/glossary handoffs so the pass never ends silently. Screen-specs is the optional terminal pass, so there is no next pass to chain.

**[lang-sync-fix] Auto-sync gate:** the translation sync script MUST run and MUST write `translation-sync-report.json` before this handoff. The `Secondary languages:` line is emitted by `translation_sync_gate.py --mode finalize` — echo it VERBATIM. See `references/pipeline-translate.md § Auto-Sync Secondary Languages` for the full contract. DO NOT compose, paraphrase, or invent that line. The re-sync command is always `/tkm:rebuild-spec --lang <code>`.

**[v5.3.3] Completion gate:** run `check_translation_gate.py --pass screen-specs` BEFORE writing the completion flag or printing this handoff. Exit 1 BLOCKS completion. See `references/pipeline-translate.md § Completion gate` for the full gate-run command and fix instructions.

```
─── screen-specs pass complete ───
Promoted: docs/screens/{SCR###}/spec.md
Secondary languages: <echo translation_sync_gate.py finalize stdout VERBATIM>
Review (optional): /ask-expert "Are the screen specs complete and consistent with the screen list and feature specs?"
Next:
  /tkm:write-journal           # Record this milestone
```
