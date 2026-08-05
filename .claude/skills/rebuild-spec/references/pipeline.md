<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline — Wave Dependency Graph

Expresses rebuild-spec artifact generation order as `TaskCreate` chains.
Execution handled by TaskList — no custom orchestrator needed.

## Path resolution (v23.0.0 — `--root` + `primary_lang`)

All output paths come from ONE source: `_path_lib.resolve_component_paths(project_root, active_plan_dir,
root_arg, primary_lang)`. Resolve it ONCE at preflight and thread the result everywhere.
**Always pass `primary_lang`** (from `state.primary_lang` or `--primary-lang`); omitting it defaults
to `"en"` and will mis-place components on non-en primary repos (R1 risk).

- **No `--root`** (default, single-repo, en-primary): `docs_root = <cwd>/docs`,
  `state_file = docs/.rebuild-state.json`, `plan_dir` unchanged — byte-identical to the legacy
  layout (no regression).
- **No `--root`** (single-repo, non-en primary e.g. `vi`): `docs_root = <cwd>/docs/vi`,
  `state_file = docs/vi/.rebuild-state.json` — language-namespaced root.
- **`--root <subrepo>`** (en-primary monorepo): `docs_root = docs/components/<name>/`,
  `plan_dir = plans/<active>/components/<name>/`, `state_file = docs/components/<name>/.rebuild-state.json`
  (per-component → parallel-safe + resumable). `<name>` = sub-repo path `/`→`-` (RT2-F14). Guarded:
  the sub-repo must be under the project root. **Byte-identical to v22 for en-primary repos.**
- **`--root <subrepo>`** (non-en primary, e.g. `vi`): `docs_root = docs/vi/components/<name>/`,
  `plan_dir = plans/<active>/components/<name>/`, `state_file = docs/vi/components/<name>/.rebuild-state.json`.
  This is the v23 BREAKING change — non-en repos write/read source at the lang-namespaced location.

Scripts that write to docs (`promote_drafts.py --docs-root`, `build_source_to_fcode.py
--docs-root/--specs-root`) already take explicit paths — the orchestrator passes the resolved
`docs_root`; no script hard-codes CWD. Scout `TaskCreate` draft paths + the reconcile map under
`plans/<active>/...` follow `plan_dir` from the same resolver. `--root` is the foundation Phase D's
`--batch`/`--aggregate` build on (it does NOT re-implement path plumbing — RT2-F2).

## Waves

<!-- Updated: Phase-02 strip — W6/W6.5/W6.8/W6.85/W6.9/W7b removed from default; W7a is core-only -->

**Default (core) run:** W0–W5.6 → W7a (core only) → W7-merge → W7.5 → W8 → W9 (core promote) → W9.5

| Wave | Artifact(s) | Depends On | Parallel | Pass |
|------|-------------|------------|---------|------|
| -1 | Hydrate (incremental only) | planner mode | — | core |
| 0 | Scout discovery | — | yes | core |
| 1 | SystemOverview, RouteList, DataModel | W0 | yes | core |
| 1.5 | DataModel structural gate | W1 data-model | — | core |
| 2 | ScreenList + ScreenFlow | W1.5 (RouteList + DataModel) | — | core |
|   | BehaviorLogic | W2 (ScreenList + ScreenFlow) | — | core |
| 3 | Permissions | W2b BehaviorLogic | — | core |
| 4 | UserStories | W3 | — | core |
| 4.5 | UserStories quality gate | W4 | — | core |
| 5 | FeatureList | W4.5 | — | core |
| 5.5 | FeatureList existence gate | W5 | — | core |
| 5.6 | FeatureList sanity review (fast gate) | W5 + W5.5 | — | core |
| FS.1 | FeatureSpec × F### | W5.6 | yes (fan-out, wave-chained ≤5) | **feature-specs pass only** |
| FS.2 | Spec + citation validators | FS.1 | — | feature-specs pass only |
| FL.1 | ProcessFlow synthesis | FS.7 (feature specs promoted) | yes | **flows pass only** |
| FL.2 | ProcessFlow liveness validator | FL.1 | — | flows pass only |
| GL.1 | Glossary synthesis | FS.7 (feature specs promoted) | yes | **glossary pass only** |
| 7a | Core artifact reviewer *(Review zone)* | W5.6 | — | **core only** |
| FS.5 | Feature spec reviewer (batched 5/reviewer) *(Review zone)* | FS.1 | yes (batches wave-chained ≤5) | feature-specs pass only |
| 7-merge | Combine review reports *(Review zone)* | W7a (core); W7a+FS.5 (feature-specs) | — | core + each pass |
| 7.5 | Structural fixer — edge-case safety net *(Pre-fix zone)* | W7-merge | — | core |
| 8 | Implementer + Re-reviewer (fix cycles, max 3, conditional) | W7-merge | — | core |
| 9 | Doc-writer — core promote (`--scope core`) | W8 | — | **core** |
| 9.5 | Reverse-index refresh (`--cursor core`) | W9 | — | core |

## Wave numbering — legacy map

The pass-specific waves were renumbered during the Phase-02 strip (monolith → standalone
passes). This is the **single** place old wave numbers are allowed as identifiers (besides
HTML history comments). Anywhere else, the new ids (`FS.*` / `FL.*` / `GL.*` / `SS.*`) are
the current identifiers.

| Old | New | Pass |
|-----|-----|------|
| W6 | FS.1 | feature-specs |
| post-W6 | FS.1.5 | feature-specs |
| W6.5 | FS.2 | feature-specs |
| W7b | FS.5 | feature-specs |
| W6.8 | FL.1 | flows |
| W6.85 | FL.2 | flows |
| W6.9 | GL.1 | glossary |

## Incremental orchestration (preamble)

When `docs/.rebuild-state.json` exists, the orchestrator runs the incremental planner before any wave dispatch. **Note:** Wave -2 may pre-create the state file via bootstrap; if so, the planner invocation below sees a freshly-created state and proceeds with normal incremental flow.

### v21.0.0 screen-artifact migration (BREAKING — Delphi/dfm-form docs-state predating v21)

Pre-v21 runs of a `screen_source: dfm-form` profile (Delphi) emitted NO screen artifact — the old
profile mapped `screen-list`/`screen-flow` to `class: web` and skipped them. After upgrade those two
artifacts are produced (`produce("screen-list")` is now driven by `screen_source`). A re-run must
backfill them. The orchestrator applies this rule BEFORE accepting an incremental plan (it is
`produce()`-aware, which the deterministic planner is not):

```js
// v21 migration backfill — fires only for a producing-but-absent screen artifact (pre-v21 docs-state).
const screenArtifactsMissing = produce("screen-list")
  && (!existsNonEmpty(`${docs_root}/generated/screen-list.md`)
      || !existsNonEmpty(`${docs_root}/generated/screen-flow.md`))
if (screenArtifactsMissing && existsNonEmpty(`${docs_root}/generated/feature-list.md`)) {
  // Core docs exist but the screen artifact does not → pre-v21 (or headless→screen-source) state.
  // Force the Wave 2 screen-list+screen-flow wave into the affected set (and its W2a.1 gate),
  // even if no source file changed this run. Downstream US/feature-list re-derive from the new SCRs.
  affected_waves = unique([...affected_waves, "Wave2: screen-list + screen-flow"])
  console.log("[INFO] v21 migration: screen-list/screen-flow absent under a screen_source profile — scheduling Wave 2 screen-artifact generation")
}
```

This is additive — it never deletes prior artifacts and never fires for a web profile (its screen
artifacts already exist) or a headless `screen_source: none` profile (`produce("screen-list")` false).

When an artifact's pre-gen estimate exceeds threshold: Read `references/artifact-sharding.md` (descriptor table, merge recipe, fragment contract).

### Wave -2 — Bootstrap detection (v2.x upgrade)

Fires BEFORE the planner invocation. Detects v2.x output without `.rebuild-state.json` and offers to bootstrap state from git history.

```js
// Wave -2 — Bootstrap detection (only fires when state is missing)
const stateFile = "docs/.rebuild-state.json"
const v2EvidenceFiles = ["docs/system/overview.md", "docs/generated/feature-list.md"]
const hasState = existsNonEmpty(stateFile)
const hasV2Evidence = v2EvidenceFiles.some(f => existsNonEmpty(f))

let bootstrapped = false
if (!hasState && hasV2Evidence) {
  const derivedSha = bashOutput("git log -1 --format=%H -- docs/").trim()
  const headSha = bashOutput("git rev-parse HEAD").trim()

  if (!derivedSha) {
    console.log("[INFO] docs/ not in git history — skipping bootstrap. Will fall back to full rebuild.")
  } else if (derivedSha === headSha) {
    console.log(`[INFO] derived baseline SHA = HEAD (${headSha.slice(0,7)}); bootstrap would produce empty diff. Falling back to full rebuild.`)
  } else {
    // Prompt user — Claude tool: AskUserQuestion
    const answer = await AskUserQuestion({
      header: "v2.x Upgrade",
      question: `Detected v2.x rebuild-spec output without state file. Baseline SHA derived from git log of docs/ = ${derivedSha.slice(0,7)} (≠ HEAD). Bootstrap state from git and run incremental, OR force full rebuild?`,
      options: [
        {label: "Bootstrap from git (fast, ~2-3min)",
         description: "Treat docs/ as canonical baseline at git SHA " + derivedSha.slice(0,7) + ". Diff source files from that SHA to HEAD. ⚠ If you hand-edited docs/ since the last rebuild, those edits become the implicit baseline and pre-handedit source changes will be missed."},
        {label: "Full rebuild (slow, safe)",
         description: "Re-generate all artifacts + feature specs from scratch. 15-30 min for a 60-feature project but guaranteed correct."},
      ],
    })

    if (answer.startsWith("Bootstrap")) {
      bash(`.claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/build_source_to_fcode.py \
        --specs-root docs/features \
        --docs-root docs \
        --state-out docs/.rebuild-state.json \
        --index-out docs/_source-to-fcode.json \
        --mode full \
        --last-rebuild-sha "${derivedSha}"`)
      bootstrapped = true
      console.log(`[BOOTSTRAP] Emitted state file with last_rebuild_sha=${derivedSha.slice(0,7)}. Proceeding with incremental flow.`)
    } else {
      console.log("[INFO] User chose full rebuild — falling through to state_missing path.")
    }
  }
}
// If bootstrapped=true, state file now exists → planner below runs incremental as usual.
```

### Planner invocation

```
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/incremental_planner.py \
  --plan-dir plans/<active-plan> \
  --docs-root docs \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  [--full] [--since <sha>] [--dry-run] [--features F###,...] \
  [--threshold 0.30]
```

Exit 0 → `.incremental-plan.json` written; exit 1 → hard halt; exit 2 → arg error.

### Decision JSON shape

See `references/incremental-state-schema.md § .incremental-plan.json`.

### resolveWaveTaskId helper

Centralizes "create new task OR return prior-completed-task ID for blockedBy chains":

```
function resolveWaveTaskId(subject, dispatchFn) {
  if (mode === "full" || affected_waves.includes(subject)) {
    return dispatchFn()  // TaskCreate → returns new task ID
  }
  // Incremental: wave skipped → return sentinel for downstream blockedBy
  // Downstream waves see this as "already completed" and proceed.
  return `HYDRATED:${subject}`
}
```

### Branch on mode

```
const planJson = JSON.parse(readFile("plans/<active>/artifacts/.incremental-plan.json"))
const mode = planJson.mode
const affected_waves = planJson.affected_waves ?? []
const affected_fcodes = planJson.affected_fcodes ?? []
const w5_reran = planJson.w5_reran ?? false

if (mode === "incremental") {
  // Run hydrate
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/incremental_planner.py \
    --hydrate --plan-dir plans/<active-plan> --docs-root docs
  // Capture stderr → surface [OUT_OF_BAND_EDIT] warnings to user
}
// Then proceed to Wave 0+ dispatch (full or selective)
```


## Language dispatch (v5.1.0)

Runs in SKILL.md preflight BEFORE any wave dispatch. Determines `docs_root` and whether to take the inline-generation path (Path A) or the translate-from-primary path (Path B).

```
eff_lang   = normalize_lang(--lang) or state.primary_lang or "en"   # de-aliases jp→ja, cn→zh, …
first_run  = state.primary_lang is absent
if first_run:  state.primary_lang = eff_lang   # this run becomes primary
is_primary = (eff_lang == state.primary_lang)
mode       = detect_layout_mode(state.primary_lang, "docs", state)   # "single" | "per-lang"
docs_root  = resolve_docs_root(eff_lang, state.primary_lang, multilang=(mode=="per-lang"))
```

`docs_root` is computed by the resolver, NOT a hand-rolled `en→docs` literal: that literal is en-only
and breaks for non-en primaries / per-lang repos (see `_lang_lib.py` and the C2 note in
`pipeline-translate.md`). single-lang en-primary → `docs/`; per-lang → `docs/<primary>` (and each
secondary → `docs/<code>`). The single source of truth for the layout rule is
`_shared/docs-canonical-mapping.md` § Language layout.

- **Path A (`is_primary`):** Run normal pipeline with `--docs-root <docs_root>` threaded into all promote calls. Session context carries generation-language directive (prose in `eff_lang`, English skeleton). `build_session_context.py --mode generate --lang <eff_lang>`.
- **Path B (secondary):** Load `pipeline-translate.md`. Run TR.0–TR.5 (translate from primary). Session context: `--mode translate --lang <eff_lang>`.
- **Auto-sync:** After any Path A pass promotes, `translation_sync_gate.py --mode plan` + `--mode finalize` (from `pipeline-translate.md` contract) syncs all existing secondary mirrors. Guarded by `REBUILD_AUTO_SYNC_TRANSLATIONS` env var. The `Secondary languages:` handoff line is emitted by the script — echo it VERBATIM.

## On-demand loading
The wave dispatch bodies live in companion files. Load them just-in-time:
- Before W0–W5 dispatch → `pipeline-w0-w5.md`
- Before W5.5/W5.6 dispatch → `pipeline-w5x-w6.md` (default/core run — FS.1/FS.2 removed)
- Before W7a/W7.5/W8/W9 dispatch → `pipeline-w7-w9.md` (default/core run — FL.1/FL.2/GL.1/FS.5 removed)
- When `--feature-specs` flag is set → `pipeline-feature-specs.md` (FS.1–FS.7 waves)
- When `--flows` or `--glossary` flag is set → `pipeline-flows-glossary.md` (FL.1–FL.5 / GL.1–GL.3 waves)
- When `--screen-specs` flag is set → `pipeline-screen-specs.md`
- When `--lang <code>` targets a secondary language → `pipeline-translate.md` (TR.0–TR.5 waves)
- **[lang-sync-fix]** On ANY primary pass when `docs/.rebuild-state.json`'s `translations` object is non-empty → ALSO load `pipeline-translate.md`. Primary passes run `translation_sync_gate.py` (plan + finalize) in post-promote/handoff steps and echo the finalize stdout line VERBATIM; skipping the load leaves that contract undefined and mirrors silently primary-only.

## Reconcile pattern (run on every invocation)

Before dispatching any new wave, sync TaskList with disk. Closes tasks whose previous session died after the subagent wrote its output but before `TaskUpdate` fired. On resume, also re-read `plans/<active-plan>/artifacts/validation/validation-summary.json` if present — it is the source of truth for W5.5 / FS.2 state and feeds the Wave 9 pre-flight gate.

Note: `.incremental-plan.json` (if present) lists intentionally-skipped waves — reconcile naturally ignores them because no TaskCreate was issued for skipped waves.

```
// Mapping: task subject pattern → expected output path (relative to plans/<active>/artifacts/)
// null = not reconcilable (no single output file); skip in reconcile loop
//
// [Phase-02] Default (core) run reconcile map — FS.1/FL.1/GL.1/FS.5 entries REMOVED.
// Those entries live in pipeline-feature-specs.md § reconcile and pipeline-flows-glossary.md § reconcile.
// [RT-C6] FL.1/GL.1 purged from default reconcile map to prevent STUCK tasks on core-only runs.
const expectedOutput = {
  "Scout: discovery scan":               "scout-report.md",
  "Wave1: system-overview":              "system-overview.md",
  "Wave1: architecture":                 "architecture.md",
  "Wave1: route-list":                   "route-list.md",
  "Wave1: data-model":                   "data-model.md",
  "Wave1.5: data-model-review":          "data-model-review.md",
  "Wave2: screen-list + screen-flow":    ["screen-list.md", "screen-flow.md"],
  "Wave2: behavior-logic":               "behavior-logic.md",
  "Wave2: combined-screen-bg":           ["screen-list.md", "screen-flow.md", "behavior-logic.md"],
  "Wave2.9: api-map":                    "api-map.md",
  "Wave3: permissions":                  ["permissions.md", "permissions-matrix.md"],
  "Wave4: user-stories":                 "user-stories.md",
  "Wave4.5: user-stories-review":        "user-stories-review.md",
  "Wave5: feature-list":                 "feature-list.md",
  "Wave5.6: feature-list-review":        "feature-list-review.md",
  "Wave7a: core-artifact-review":        "core-review-report.md",
  "Wave7-merge: combine review reports": "review-report.md",
  "Wave8.*":                             null,  // fix cycles: no single output file — skip auto-close
  "Wave8.review-*":                      null,  // re-reviewer tasks: same — skip auto-close
  "Wave9: doc-writer — persist":         "wave9-complete.flag",
  "Wave9: doc-writer — finalize":        "wave9-complete.flag"
}

// [RT-M3] Core docs for Wave 9 reconcile check — system/ + generated/ MINUS glossary (--glossary pass)
// Feature dirs are NOT checked here (--feature-specs pass). Flows are NOT checked (--flows pass).
const coreSystemDocs = [
  "system/overview.md", "system/architecture.md",
  "system/permissions.md", "system/business-rules.md"
]
const coreGeneratedDocs = [
  "generated/route-list.md", "generated/api-map.md", "generated/permissions-matrix.md",
  "generated/entities.md", "generated/user-stories.md", "generated/feature-list.md",
  "generated/screen-list.md", "generated/screen-flow.md", "generated/behavior-logic.md"
]

const rebuildTasks = TaskList({ filter: /^(Scout:|Wave\d+(\.\d+)?|Wave7[a\-])/ })
for (const task of rebuildTasks.filter(t => t.status === "in_progress")) {
  const paths = resolveExpected(task.subject, expectedOutput)
  if (paths === null) continue  // Wave 8 tasks: not auto-closeable — require manual resolution

  const allExist = paths.every(p => existsNonEmpty(`plans/<active>/artifacts/${p}`)
                               && !containsPlaceholder(`plans/<active>/artifacts/${p}`))

  // [RT-M3] Wave 9 reconcile check: flag present OR allCoreDocsPromoted (no anyFeatureDirPromoted)
  const allCoreDocsPromoted = [...coreSystemDocs, ...coreGeneratedDocs]
    .every(f => existsNonEmpty(`docs/${f}`))
  const wave9Ok = task.subject.startsWith("Wave9") &&
                  (existsNonEmpty("plans/<active>/artifacts/wave9-complete.flag")
                   || allCoreDocsPromoted)

  if (allExist || wave9Ok) {
    TaskUpdate({ id: task.id, status: "completed",
                 note: "auto-reconciled from disk — output present, session likely died before TaskUpdate" })
  }
}
```

**With `--resume`:** run the block above, then STOP.
- Tasks closed: report subject + output path
- Tasks still `in_progress` AND output not yet written (STUCK): report as STUCK — user must manually reset to `pending` or `cancelled` before re-running without `--resume`
- Wave 8 tasks (`null` in map): always reported as STUCK if `in_progress` — cannot auto-close
- No new `TaskCreate` calls in resume mode

**Without `--resume` (default no-args):** run reconcile, then dispatch next pending wave.
- STUCK tasks (`in_progress`, no output) are left as-is — orchestrator does NOT re-create them to avoid duplicates
- If a task is STUCK, use `--resume` first to diagnose, then manually reset before re-running

### Translation staleness check [lang-sync-fix]

Runs on EVERY invocation, right after the reconcile loop (both `--resume` and default), before dispatching any new wave. The reconcile loop above only closes tasks + checks core-doc promotion — it is blind to secondary languages. This block detects mirrors behind the primary (per `incremental-state-schema.md`: a lang L is stale when a primary pass produced docs that `translations[L].passes_translated` does not cover, OR `translations[L].translated_from_sha` is behind the primary cursor). Emit a nudge so a new session warns the user instead of silently leaving `docs/<lang>/` primary-only. Non-blocking — never halts dispatch.

```
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const translations = state.translations ?? {}
const primaryCursor = state.last_rebuild_sha || ""

// Primary docs live at docs/ root (single-lang en) OR docs/<primary>/ (per-lang) —
// resolve it, NEVER hardcode "docs/...". A hardcoded root makes every check below
// return false in per-lang mode → missingPasses always empty → the staleness nudge
// goes silent and secondary mirrors drift unnoticed (matches pipeline-translate.md TR.5).
const primary_lang = state.primary_lang || "en"
const mode = detect_layout_mode(primary_lang, "docs", state)   // "single" | "per-lang"
const primary_docs_root = resolve_docs_root(primary_lang, primary_lang, multilang=(mode=="per-lang"))

// A pass is "present in primary" when its promoted docs exist on disk.
// dirHasChildren(p) ≝ p is a directory containing ≥1 non-empty file (e.g. <root>/features/F001/…).
const passPresent = {
  "core":          () => existsNonEmpty(`${primary_docs_root}/system/overview.md`),
  "feature-specs": () => dirHasChildren(`${primary_docs_root}/features`),
  "flows":         () => dirHasChildren(`${primary_docs_root}/flows`),
  "glossary":      () => existsNonEmpty(`${primary_docs_root}/system/glossary.md`),
  "api-contracts": () => existsNonEmpty(`${primary_docs_root}/generated/api-contracts.md`),
  "screen-specs":  () => dirHasChildren(`${primary_docs_root}/screens`),
  "jobs":          () => existsNonEmpty(`${primary_docs_root}/generated/job-list.md`),
  // test-cases.md is a per-feature SIDECAR (5th file) — presence signal is "at least
  // one feature has one", not a single top-level artifact path (v26.1.0 B6 pass).
  "test-cases":    () => globAny(`${primary_docs_root}/features/*/test-cases.md`),
  // design-intent.md is EXPERIMENTAL/report-only (F11b, v26.1.0 B5 pass) — this check only
  // ever fires true AFTER a user has explicitly confirmed promotion (D.5); a never-promoted
  // report-only run legitimately leaves this false forever, which is correct (no nudge for
  // content that was never meant to auto-sync).
  "design-intent": () => existsNonEmpty(`${primary_docs_root}/system/design-intent.md`),
}

for (const [lang, t] of Object.entries(translations)) {
  const done = new Set(t.passes_translated ?? [])
  const missingPasses = Object.keys(passPresent).filter(p => passPresent[p]() && !done.has(p))
  if (missingPasses.length) {
    console.log(`[WARN] translation_stale:${lang} — primary has [${missingPasses.join(", ")}] not yet mirrored to docs/${lang}/. ` +
                `Run /tkm:rebuild-spec --lang ${lang} to sync (or it auto-syncs after the next primary pass unless REBUILD_AUTO_SYNC_TRANSLATIONS=0).`)
  }
  // Content drift: same passes covered but primary advanced since last translate.
  if (t.translated_from_sha && primaryCursor && t.translated_from_sha !== primaryCursor && missingPasses.length === 0) {
    console.log(`[WARN] translation_stale:${lang} — content drift: translated_from_sha=${t.translated_from_sha.slice(0,7)} behind primary cursor=${primaryCursor.slice(0,7)}. ` +
                `Re-run /tkm:rebuild-spec --lang ${lang} for an accurate mirror.`)
  }
}
```

## Artifact paths

| Stage | Draft path | Persistent path | Pass |
|-------|-----------|-----------------|------|
| System docs (core) | `plans/<active-plan>/artifacts/<name>.md` | `docs/system/<name>.md` | core |
| Generated docs (core) | `plans/<active-plan>/artifacts/<name>.md` | `docs/generated/<name>.md` | core |
| Feature specs | `plans/<active-plan>/artifacts/features/<F###>/{technical-spec,business-context,screens,edge-cases}.md` | `docs/features/<F###>/{...}.md` | **(feature-specs pass)** |
| Process flows | `plans/<active-plan>/artifacts/flows/<slug>.md` | `docs/flows/<slug>.md` | **(flows pass)** |
| Glossary | `plans/<active-plan>/artifacts/glossary.md` | `docs/system/glossary.md` | **(glossary pass)** |
| Core review report | `plans/<active-plan>/artifacts/core-review-report.md` | ephemeral (W7a output) | core |
| Feature review batches | `plans/<active-plan>/artifacts/feature-review-batch-NN.md` | ephemeral (FS.5 output) | feature-specs pass |
| Merged review report | `plans/<active-plan>/artifacts/review-report.md` | ephemeral (W7-merge output) | core |
| Wave 9 completion flag | `plans/<active-plan>/artifacts/wave9-complete.flag` | ephemeral (reconcile signal + audit) | core |

Doc-writer (Wave 9) promotes core drafts only after reviewer passes (`failed === 0`).
Each pass (feature-specs/flows/glossary) has its own completion flag and review report (see respective pass files).
