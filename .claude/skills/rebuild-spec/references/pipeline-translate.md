# Pipeline: Translate Pass (TR.0–TR.5) + Auto-Sync Entry

Standalone pass. Loaded when `--lang <code>` targets a secondary language (i.e. `eff_lang != primary_lang`). Also invoked automatically by the auto-sync hook after any primary pass promotes. See `pipeline.md` for dispatch block.

## Language Dispatch (preflight — runs BEFORE any pass)

```js
// Language resolution — runs in SKILL.md preflight, before any wave dispatch.
// _lang_lib.py is AUTHORITATIVE; orchestrator mirrors the logic here. The actual
// path/mode decisions are computed by normalize_lang / detect_layout_mode /
// resolve_docs_root in _lang_lib.py — mirror them, do NOT hand-roll an `en→docs`
// literal (that is the bug the resolver exists to prevent — see C2).
const state = existsNonEmpty("docs/.rebuild-state.json")
  ? JSON.parse(readFile("docs/.rebuild-state.json"))
  : {}

// normalize_lang() de-aliases (jp→ja, cn→zh, kr→ko, vn→vi) and rejects path-unsafe codes.
const rawLang = flags.lang ?? null  // --lang <code> or null
const eff_lang = rawLang ? normalize_lang(rawLang) : (state.primary_lang || "en")
const first_run = !state.primary_lang

if (first_run) {
  // This run becomes the primary — record it in state
  state.primary_lang = eff_lang
  // State will be persisted by build_source_to_fcode.py at W9.5 / pass cursor write
  console.log(`[INFO] first run — primary_lang set to "${eff_lang}"`)
}

const primary_lang = state.primary_lang
const is_primary = (eff_lang === primary_lang)

// Layout mode (single-lang vs per-lang). Signal = a secondary is registered in
// state.translations OR the sentinel docs/<primary>/.layout-migrated exists — NEVER
// bare docs/<primary>/ directory existence (misfires for non-en primaries, C2).
const mode = detect_layout_mode(primary_lang, "docs", state)   // "single" | "per-lang"
const multilang = (mode === "per-lang")

// resolve_docs_root(lang, primary_lang, multilang): en-primary single → "docs";
// everything else → "docs/<lang>". This is the ONLY place docs roots are computed.
const docs_root = resolve_docs_root(eff_lang, primary_lang, multilang)

// Unusual code warning (non-standard format), AFTER de-aliasing.
if (rawLang && !/^[a-z]{2,3}(-[a-z0-9]{2,8})*$/.test(eff_lang)) {
  console.log(`[WARN] unusual language code "${eff_lang}" — proceeding anyway`)
}

if (is_primary) {
  // Path A — INLINE GENERATION: run the normal pipeline with docs_root override
  // Session context carries generation-language directive (prose in eff_lang, English skeleton)
  // All promote calls use --docs-root <docs_root>
  // Continue to the requested pass (core / --feature-specs / --flows / etc.)
} else {
  // Path B — TRANSLATE FROM PRIMARY: load pipeline-translate.md (this file)
  // FIRST, if this run adds the first secondary to an en-primary-at-root repo,
  // run the one-time layout flip (TR.-1 below) so primary content moves to
  // docs/en/ and the new secondary lands at docs/<code>/ as a sibling.
  // Then run TR.0–TR.5 below.
}
```

**Decision table:**

| Condition | Path | Action |
|-----------|------|--------|
| `first_run` (no `primary_lang` in state) | A (inline) | Set `primary_lang = eff_lang`; generate inline |
| `eff_lang == primary_lang` | A (inline) | Generate inline (normal pipeline + docs_root) |
| `eff_lang != primary_lang` | B (translate) | Translate from primary's docs |

---

## Translate Pass (Path B) — TR.-1 through TR.5

### TR.-1 — Layout flip (one-time, first secondary on an en-primary-at-root repo)

When `mode` was `single` at dispatch AND `primary_lang === "en"` AND content is still at the
`docs/` root, adding the first secondary triggers the one-time flip: primary English content moves
`docs/{system,generated,flows,features,screens}/` → `docs/en/...`, and `docs/jp/`→`docs/ja/` (+ the
`translations.jp`→`translations.ja` state key) is renamed if present. The migration is atomic +
idempotent (sentinel `docs/en/.layout-migrated`), serialized by an exclusive lock, and invalidates
the reverse-index so a later run regenerates it. **Non-en primaries are already per-lang shaped → the
migration is a no-op.** Run it BEFORE computing `primary_docs_root`:

```
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/migrate_docs_layout.py --primary ${primary_lang} --docs-base docs
```

A non-zero exit (e.g. `docs/jp/` + `docs/ja/` coexistence) ABORTS — resolve it (re-run with
`--force-rename-alias` to merge) before continuing. After the flip the repo is per-lang: re-read state
and recompute `mode`/`docs_root` via `detect_layout_mode` / `resolve_docs_root` (now `multilang=true`).

### TR.0 — Preflight Guards

```js
// Guard 1: Missing primary — primary docs root via the resolver (post-flip: docs/<primary>/).
const primary_docs_root = resolve_docs_root(state.primary_lang, state.primary_lang, multilang)
if (!existsNonEmpty(`${primary_docs_root}/system/overview.md`)) {
  throw new Error(
    `ABORT — No ${state.primary_lang} primary docs to translate from. ` +
    `Run /tkm:rebuild-spec first to generate the primary, then re-run --lang ${eff_lang}.`
  )
}

// Guard 2: Outdated primary (non-blocking warning)
const translationEntry = (state.translations ?? {})[eff_lang]
if (translationEntry) {
  const primaryCursorSha = state.last_rebuild_sha || ""
  if (translationEntry.translated_from_sha && translationEntry.translated_from_sha !== primaryCursorSha) {
    console.log(
      `[WARN] primary_ahead_of_translation — Primary (${state.primary_lang}) changed since ` +
      `docs/${eff_lang}/ was last translated (translated_from_sha=${translationEntry.translated_from_sha.slice(0,7)}, ` +
      `primary cursor=${primaryCursorSha.slice(0,7)}). For an accurate mirror, run ` +
      `/tkm:rebuild-spec (primary incremental) first, then re-run --lang ${eff_lang}.`
    )
  }
}

console.log(`[INFO] TR.0: translating ${state.primary_lang} → ${eff_lang}`)
```

### TR.1 — Scope: artifacts to translate

```js
// Determine which artifacts to translate from the primary
const isFirstTranslateForLang = !translationEntry
const staleFile = `plans/<active-plan>/artifacts/translation-stale.json`
let artifactsToTranslate = []

if (isFirstTranslateForLang || flags.full) {
  // Full translate: all primary artifacts
  artifactsToTranslate = discoverAllPrimaryArtifacts(primary_docs_root)
  console.log(`[INFO] TR.1: full translate — ${artifactsToTranslate.length} artifacts`)
} else if (existsNonEmpty(staleFile)) {
  // Incremental: use the stale file from the just-completed primary pass
  const staleData = JSON.parse(readFile(staleFile))
  artifactsToTranslate = staleData.changed_artifacts ?? []
  console.log(`[INFO] TR.1: incremental translate — ${artifactsToTranslate.length} changed artifacts from ${staleData.pass} pass`)
} else {
  // Fallback: full re-translate (safe default)
  artifactsToTranslate = discoverAllPrimaryArtifacts(primary_docs_root)
  console.log(`[INFO] TR.1: no stale file — falling back to full translate`)
}

// discoverAllPrimaryArtifacts walks (ALL primary doc areas — keep in sync with the
// passPresent map in pipeline.md § Translation staleness check):
//   <primary_docs_root>/system/*.md         (includes design-intent.md — EXPERIMENTAL,
//                                            report-only (F11b, v26.1.0 B5 pass); only present
//                                            on disk after an explicit user-confirmed promote,
//                                            same _DOC_AREAS glob as glossary.md — no registry
//                                            change needed, F2)
//   <primary_docs_root>/generated/*.md      (includes api-contracts.md and job-list.md —
//                                            _translation_sync_lib.py::_DOC_AREAS already
//                                            globs "generated/*.md"; no registry change
//                                            needed for the v26.1.0 jobs pass, F2)
//   <primary_docs_root>/features/*/*.md   (includes test-cases.md — the v26.1.0 B6 sidecar
//                                          rides the SAME glob as the mandatory 4 files; no
//                                          registry change needed, F2)
//   <primary_docs_root>/flows/*.md
//   <primary_docs_root>/screens/*/*.md      // [lang-sync-fix] was missing — full translate skipped screen-specs
// Returns list of relative paths from primary_docs_root.
```

### TR.2 — Translation fan-out

**Output-size guard (v11.2.0):** before translating an artifact, estimate its output LOC — a
whole-file translation can otherwise blow the 32K output-token ceiling on a large doc. For each
artifact run `estimate_artifact_loc.py --op translate --file <artifact> --max-loc ${docs_maxLoc ?? 800}`;
if it returns `chunk: true`, split that artifact by top-level heading and translate the chunks
separately (then concatenate), instead of one monolithic translate call. Same guard applies to any
rewrite-whole-file operation (`--op rewrite`).

```js
// Build session context with translate-mode directive
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_session_context.py \
  --plan-dir plans/<active-plan> \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --stack-note "${stackNote}" \
  --mode translate \
  --lang ${eff_lang}

// Junk/0/negative env degrades to the default — a broken env value must never produce
// NaN batch math (empty/broken batches) or an unbounded agent count.
const BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_TRANSLATE_BATCH_SIZE ?? process.env.REBUILD_FS_BATCH_SIZE ?? '5') || 5)
// Hard cap on spawned batch sub-agents (token-cost guard): NEVER spawn more than MAX_AGENTS
// translate tasks. When artifact count would exceed the cap, grow the per-batch size so the
// number of batches stays ≤ MAX_AGENTS instead of letting ceil(N/BATCH_SIZE) run unbounded.
const MAX_AGENTS = Math.max(1, parseInt(process.env.REBUILD_TRANSLATE_MAX_AGENTS ?? '5') || 5)
const effBatchSize = Math.max(BATCH_SIZE, Math.ceil(artifactsToTranslate.length / MAX_AGENTS))
const translateBatches = chunk(artifactsToTranslate, effBatchSize)  // translateBatches.length ≤ MAX_AGENTS
const draftRoot = `plans/<active-plan>/artifacts/translations/${eff_lang}`

// [C4] Translation MUST run on Haiku. TaskCreate has NO model parameter — a task
// inherits the orchestrator's session model, so a bare TaskCreate would silently run
// translation on the session model and the cost goal would be unmet with no error.
// The ONLY enforceable binding is the translator agent def (model: haiku).
// Spawn each batch as an Agent(subagent_type="translator") — the model is bound
// by the agent definition, the single source of truth. (Where a direct Agent call is
// used instead, pass model="haiku".)
for (const [i, batch] of translateBatches.entries()) {
  Agent({
    subagent_type: "translator",   // model: haiku — bound by claude/agents/translator.md
    description: `TR.2.batch-${pad2(i+1)}: translate ${state.primary_lang}→${eff_lang}`,
    prompt: `Session context: read plans/<active-plan>/artifacts/_session-context.md FIRST.

Translate ${batch.length} artifacts from ${state.primary_lang} to ${eff_lang}.
CONTRACT: references/translation-contract.md (MUST read before translating).

SOURCE (primary docs): ${primary_docs_root}/
TARGET (draft): ${draftRoot}/

Artifacts to translate:
${batch.map(a => `- ${a}`).join('\n')}

For each artifact:
1. Read the primary file at ${primary_docs_root}/<artifact-path>
2. Translate ONLY prose to ${eff_lang}; copy skeleton byte-identical (headings, the ID tokens F###/US###/SCR###/BL### and similar, field labels, table headers, fenced code, frontmatter, paths, enums)
3. Write draft to ${draftRoot}/<artifact-path> (same relative path). Keep one source line → one output line; do NOT drop or pad prose.
VALIDATOR: your output is checked by scripts/validate_translation_skeleton.py — skeleton drift OR a body more than ±30% shorter/longer than the source body FAILS and forces a re-translate (max 3 attempts, then escalation).`
  })
}
```

### TR.3 — Skeleton-identity gate

```js
// After all TR.2 batches complete, validate each translated draft
const translationIssues = []

for (const artifact of artifactsToTranslate) {
  const primaryFile = `${primary_docs_root}/${artifact}`
  const mirrorFile = `${draftRoot}/${artifact}`

  if (!existsNonEmpty(mirrorFile)) {
    translationIssues.push({ artifact, issue: "draft missing" })
    continue
  }

  const result = bash(`.claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_translation_skeleton.py \
    --primary ${primaryFile} \
    --mirror ${mirrorFile}`)

  if (result.exitCode !== 0) {
    translationIssues.push({ artifact, issue: result.stderr })
  }
}

// Retry failed translations (max 3 attempts per artifact)
const MAX_RETRIES = 3
for (const failed of translationIssues) {
  let retries = 0
  let resolved = false
  while (retries < MAX_RETRIES && !resolved) {
    retries++
    console.log(`[INFO] TR.3: re-translating ${failed.artifact} (attempt ${retries}/${MAX_RETRIES})`)
    // [C4] Single-artifact re-translate on Haiku — same translator agent as TR.2.
    Agent({
      subagent_type: "translator",   // model: haiku
      description: `TR.3.retry: ${failed.artifact}`,
      prompt: `Re-translate ${failed.artifact}: skeleton drift OR body-size drift detected.
Read references/translation-contract.md. Source: ${primary_docs_root}/${failed.artifact}
Previous issue: ${failed.issue}
Output: ${draftRoot}/${failed.artifact}
PAY EXTRA ATTENTION to preserving headings, code tokens (the ID tokens F###/US###/SCR###/BL### and similar), and table headers byte-identical, and to NOT dropping or padding prose paragraphs (one source line → one output line).`
    })
    // Re-validate
    const recheck = bash(`.claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_translation_skeleton.py \
      --primary ${primary_docs_root}/${failed.artifact} \
      --mirror ${draftRoot}/${failed.artifact}`)
    if (recheck.exitCode === 0) resolved = true
  }
  if (!resolved) {
    throw new Error(`TR.3 ESCALATE — skeleton drift unresolved for ${failed.artifact} after ${MAX_RETRIES} retries.`)
  }
}

console.log(`[INFO] TR.3: all ${artifactsToTranslate.length} translations pass skeleton-identity check`)
```

### TR.4 — Promote translations

```js
// Promote translation drafts to the secondary's docs root (always docs/<eff_lang>
// in per-lang mode). Resolve via the resolver — never a hand-rolled literal.
const targetDocsRoot = resolve_docs_root(eff_lang, state.primary_lang, multilang)  // docs/<eff_lang>

bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/promote_drafts.py \
  --plan-dir plans/<active-plan> \
  --docs-root ${targetDocsRoot} \
  --scope all \
  --mode full
```

### TR.5 — Update translation state

```js
// Write translation cursor into .rebuild-state.json
// State file stays at docs/.rebuild-state.json (language-independent location)
const currentState = JSON.parse(readFile("docs/.rebuild-state.json"))
if (!currentState.translations) currentState.translations = {}

const primaryCursorSha = currentState.last_rebuild_sha || ""

// [lang-sync-fix] Derive passes_translated from what the PRIMARY actually has on disk —
// NOT a hardcoded all-4 list. A hardcoded list falsely claims passes the primary lacks,
// which would defeat the reconcile staleness detector (pipeline.md § Translation staleness check).
// Keep this map identical to passPresent there.
const passPresent = {
  "core":          () => existsNonEmpty(`${primary_docs_root}/system/overview.md`),
  "feature-specs": () => dirHasChildren(`${primary_docs_root}/features`),
  "flows":         () => dirHasChildren(`${primary_docs_root}/flows`),
  "glossary":      () => existsNonEmpty(`${primary_docs_root}/system/glossary.md`),
  "api-contracts": () => existsNonEmpty(`${primary_docs_root}/generated/api-contracts.md`),
  "screen-specs":  () => dirHasChildren(`${primary_docs_root}/screens`),
}
const passesTranslated = Object.keys(passPresent).filter(p => passPresent[p]())

currentState.translations[eff_lang] = {
  translated_from_sha: primaryCursorSha,
  last_translate_run_sha: primaryCursorSha,
  passes_translated: passesTranslated  // reflects primary's actual doc areas at translate time
}

atomicWriteJson("docs/.rebuild-state.json", currentState)
console.log(`[INFO] TR.5: translations.${eff_lang} cursor updated (translated_from_sha=${primaryCursorSha.slice(0,7)})`)
```

### Translate Pass-completion handoff prompt

```
─── translate pass complete ───
Promoted: docs/${eff_lang}/ (translated mirror of ${state.primary_lang} primary)
Skeleton-identity: PASS (all artifacts verified)
Next:
  /tkm:rebuild-spec --lang <another-code>   # Add another language mirror
  /tkm:write-journal                        # Record this milestone
```

---

## Auto-Sync Secondary Languages (reusable block)

Invoked by each primary pass's post-promote step. DRY: defined once here, referenced from pipeline-w7-w9.md, pipeline-feature-specs.md, pipeline-flows-glossary.md, pipeline-screen-specs.md, pipeline-api-contracts.md.

**Single source of truth:** the logic, report writing, and handoff-line rendering are fully implemented in `claude/skills/rebuild-spec/scripts/translation_sync_gate.py`. The LLM does NOT compose the `Secondary languages:` line — it runs the script and echoes stdout verbatim.

### Auto-sync flow (plan → translate → finalize)

**[v5.3.3 / lang-sync-fix] MANDATORY, NOT optional.** The script MUST run and MUST write `translation-sync-report.json` BEFORE the pass prints its completion handoff. A skipped auto-sync surfaces as a visible ⚠ instead of silently shipping primary-only docs.

#### Step 1 — Plan (get worklist)

```
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode plan \
  --pass <name> \
  --plan-dir plans/<active-plan>
```

Emits a JSON worklist to stdout: `{"lang": "<code>", "artifacts_to_translate": [...]}` for each secondary language that needs syncing. If `REBUILD_AUTO_SYNC_TRANSLATIONS=0`, the script emits a deferred-only worklist (no artifacts) and records that in the report.

#### Step 2 — Translate + promote (LLM work — TR.2 fan-out + TR.4 promote per lang)

For each lang in the worklist — **a sequential loop: finish one lang's TR.2 + TR.4 completely before starting the next** (this loop is prose-driven; `REBUILD_TRANSLATE_MAX_PARALLEL` below is its knob, not read by any script) — translate the listed artifacts (TR.2 fan-out) and promote to `docs/<lang>/` (TR.4). This is the only LLM-driven step. **The TR.2 fan-out here spawns the `translator` agent (`model: haiku`) exactly as in the Path-B TR.2 above — never a bare `TaskCreate` (it would inherit the session model and silently skip Haiku, C4).** Parallelism cap: `REBUILD_TRANSLATE_MAX_PARALLEL` (default **1** — langs processed sequentially) langs; `REBUILD_TRANSLATE_BATCH_SIZE` (default 5) artifacts/batch. Per-lang batch sub-agents are hard-capped at `REBUILD_TRANSLATE_MAX_AGENTS` (default 5) — past that, batch size grows so the spawned-agent count never exceeds the cap (token-cost guard). **Global constraint: langs × per-lang agents must never exceed the global 5-agent cap (SKILL.md § GLOBAL PARALLEL CAP).** This is DERIVED, not trusted to the env pair being self-consistent — before dispatching, compute `effectiveLangs = max(1, min(REBUILD_TRANSLATE_MAX_PARALLEL, floor(REBUILD_MAX_PARALLEL / REBUILD_TRANSLATE_MAX_AGENTS)))` and loop that many langs concurrently at most (defaults: `min(1, floor(5/5)) = 1`). Setting `REBUILD_TRANSLATE_MAX_PARALLEL=3` while `REBUILD_TRANSLATE_MAX_AGENTS=5` therefore still runs langs sequentially — raising lang concurrency requires shrinking `REBUILD_TRANSLATE_MAX_AGENTS` so the derived product fits the cap.

#### Step 3 — Finalize (verify, update cursors, write report)

```
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/translation_sync_gate.py \
  --mode finalize \
  --pass <name> \
  --plan-dir plans/<active-plan> \
  --lang-status <lang>:<status>[:<reason>] ...
```

The script verifies `docs/<lang>/` on disk, atomically updates `translations[lang]` cursors in `docs/.rebuild-state.json`, writes `translation-sync-report.json`, and prints the canonical `Secondary languages:` line as its **last stdout line**.

#### Step 3.5 — Mirror navigation README (per synced lang)

After finalize creates/refreshes the `docs/<lang>/` mirror, regenerate that mirror's navigation —
including the top-level reading-order `docs/<lang>/README.md` index (rebuild-spec v13.1.0). Run the
nav script ONCE per language reported `synced` by Step 3 (skip `failed`/`deferred` — their mirror is
stale or absent, so a fresh-looking README there would mislead):

```
bash: for each lang L in finalize.languages where status == "synced":
  .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/build_navigation.py \
    --lang <L> --docs-root docs/<L> --pass-complete
```

This is advisory and non-blocking (exit 0 always, same posture as the W9.6 primary nav). It
regenerates the FULL mirror nav (subdir READMEs + the reading-order README; DOCUMENT-MAP no longer
written as of v15.0.0), which is idempotent, deterministic, stdlib-only. In per-lang mode there is
**no root `docs/README.md`** (v18.0.0 — was a ~3-line pointer in v15-v17; a purely-generated root
README is removed, a hand-written one is left untouched). The single entry point is the per-lang
`docs/<primary>/README.md` full reading-order index; each per-mirror `docs/<lang>/README.md` mirrors it.
When `REBUILD_AUTO_SYNC_TRANSLATIONS=0` no lang is
`synced` this pass → Step 3.5 is a no-op and each stale mirror keeps its last README (correct).

The primary `docs/README.md` index is already written at W9.6 by the primary `build_navigation.py
--pass-complete` (no `--lang` → en labels); only the per-mirror READMEs need this step.

#### Step 4 — Echo handoff line VERBATIM

Echo the finalize stdout `Secondary languages:` line byte-for-byte in the pass completion handoff.

**DO NOT compose, paraphrase, or invent this line yourself.** The script is the only permitted source of this line. The re-sync command is always `/tkm:rebuild-spec --lang <code>` — never append a pass suffix like `--flows`, `--feature-specs`, etc.

### Report schema (for reference — written by script, not by LLM)

`translation-sync-report.json` (`schema_version: 1`):
```json
{
  "schema_version": 1,
  "pass": "<name>",
  "primary_cursor_sha": "<sha>",
  "auto_sync_enabled": true,
  "languages": [
    { "lang": "vi", "status": "synced" },
    { "lang": "jp", "status": "failed", "reason": "..." },
    { "lang": "fr", "status": "deferred", "reason": "REBUILD_AUTO_SYNC_TRANSLATIONS=0" }
  ]
}
```

### 5 canonical output cases (emitted by script — reference only)

The finalize script always emits exactly one of these 5 lines as its last stdout line:

1. `Secondary languages: ⚠ auto-sync did NOT run (no translation-sync-report.json) — secondary mirrors may be stale. Re-run the pass, or sync manually with /tkm:rebuild-spec --lang <code>.`
2. `Secondary languages: none registered`
3. `Secondary languages: synced <pass> → vi, jp (2/2)`
4. `Secondary languages: ⚠ synced: vi | STALE (failed): jp — re-sync stale with /tkm:rebuild-spec --lang jp`
5. `Secondary languages: ⚠ synced: vi | STALE (auto-sync off): jp — re-sync stale with /tkm:rebuild-spec --lang jp`

### Wiring into primary passes

Each primary pass's post-promote step runs `translation_sync_gate.py` with the pass name. The pass file specifies which artifacts changed; the script determines what to sync.

- **Core (W9):** `--pass core` — see `references/pipeline-w7-w9.md`
- **Feature-specs (FS.7):** `--pass feature-specs` — see `references/pipeline-feature-specs.md`
- **Flows (FL.5):** `--pass flows` — see `references/pipeline-flows-glossary.md`
- **Glossary (GL.3):** `--pass glossary` — see `references/pipeline-flows-glossary.md`
- **Screen-specs (SS.3):** `--pass screen-specs` — see `references/pipeline-screen-specs.md`
- **API-contracts (AC.5):** `--pass api-contracts` — see `references/pipeline-api-contracts.md`

### [v5.3.3 / lang-sync-fix] Completion gate (DRY — applies to ALL 6 passes)

**BEFORE a pass prints its final completion handoff**, run the translation completion gate:

```
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/check_translation_gate.py \
  --plan-dir plans/<active-plan> \
  --pass <name>
```

**Exit 1 BLOCKS completion — do NOT write the completion flag or print the handoff.**

This gate enforces the auto-sync contract: if secondary langs are registered, auto-sync is enabled, and `translation-sync-report.json` is missing or stale for this pass, the gate exits 1 with a `gate.report_missing` or `gate.lang_behind_cursor` issue explaining exactly what to fix. A skipped auto-sync that silently ships primary-only docs now breaks the completion contract instead of slipping through.

Enforcement class: same as the W9 promotion gate (`check_promotion_gate.py`). Same pattern: run gate → non-zero exit → halt.

Fix for a gate FAIL: re-run the pass (triggers auto-sync) or sync each stale lang manually with `/tkm:rebuild-spec --lang <code>`.

Each pass file contains a short callout referencing this section — the full gate-run command is defined here once (DRY).

## Per-pass artifact isolation

| Artifact | Path |
|----------|------|
| Translation drafts | `plans/<active-plan>/artifacts/translations/<lang>/...` |
| Stale file (transient) | `plans/<active-plan>/artifacts/translation-stale.json` |
| State cursors | `docs/.rebuild-state.json → translations.<lang>` |

---

## Component-scoped translation (`--lang L --root C`) — P05 / D2 + D6

**Source of truth for primary component docs (P04):** `docs/<primary>/components/<C>/` (resolved by
`_path_lib.resolve_component_paths(project_root, plan_dir, root_arg=C, primary_lang=primary)` — always
pass `primary_lang`). For en-primary repos this is `docs/components/<C>/`; for non-en primaries it is
`docs/<primary>/components/<C>/`.

**Secondary mirror:** `docs/<L>/components/<C>/` — exactly `resolve_docs_root(L, primary_lang, multilang)
+ /components/<C>`. The translate pipeline (Path B, TR.0–TR.5 above) runs with:

```
primary_docs_root  = docs/<primary>/components/<C>/   (source — NEVER mutated by translate)
target_docs_root   = docs/<L>/components/<C>/          (secondary mirror — prose translated, skeleton byte-identical)
```

**Wiring (mandatory deterministic step — orchestrator, NOT Python):**

```js
// --lang L --root C: translate the primary component docs to a secondary mirror.
// This runs Path B TR.0–TR.5 scoped to the component subtree.
//
// 1. Resolve primary_docs_root via _path_lib.resolve_component_paths (primary_lang from state).
// 2. Run TR.0–TR.5 with:
//      primary_docs_root = docs/<primary>/components/<C>
//      target_docs_root  = docs/<L>/components/<C>
//      artifacts         = discoverAllPrimaryArtifacts(primary_docs_root)  [*.md under that dir]
// 3. validate_translation_skeleton.py gates each artifact (same call shape as core tier).
// 4. TR.5 updates docs/<C>/.rebuild-state.json → translations.<L> cursor
//    (component-scoped state file, separate from the project-level state).
```

**Skeleton-identity invariant:** preserved unchanged — `validate_translation_skeleton.py` applies the
same check to component artifacts as to core/feature-spec artifacts. No new invariant.

**Primary NOT mutated:** the translate pass reads `docs/<primary>/components/<C>/` and writes ONLY to
`docs/<L>/components/<C>/`. Ownership is one-directional.

### Auto-sync extension (D6)

The EXISTING `translation_sync_gate.py` auto-sync flow is **extended** to cover component mirrors:

- `_translation_sync_lib._DOC_AREAS` now includes `("components", "*/*.md")` — so
  `discover_artifacts(primary_root)` enumerates `docs/<primary>/components/*/*.md` alongside the
  core/system artifacts.
- A stale-file (`translation-stale.json`) listing a component artifact
  (e.g. `components/payments/architecture.md`) causes only THAT file to be re-translated — the
  changed-only (cursor/sha) discipline is identical to core.
- `compute_finalize_result` verifies `docs/<L>` exists (the top-level secondary dir) — the same
  coarse check used for core/feature-spec syncs. Component subdirs are created by the translate
  promote step.
- Opt-out: `REBUILD_AUTO_SYNC_TRANSLATIONS=0` suppresses component re-translation exactly as it
  suppresses core re-translation (single code path, no special-casing).
- **No new translate code path.** Component sync rides the existing fan-out: the auto-sync Step 2
  spawns `subagent_type="translator"` for the component artifact list exactly as it does for core
  artifacts, with `SOURCE = docs/<primary>/components/<name>/` and `TARGET = docs/<L>/components/<name>/`.

**en-primary single-lang:** when there are no secondary languages registered in state, no component
mirrors are scheduled — the worklist is empty and no spurious translation occurs.
