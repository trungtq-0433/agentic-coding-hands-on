<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Profile Dispatch & Canonical Gates

Shared reference for the W0–W5 task chain (`pipeline-w0-w5.md`) and the later passes
(`pipeline-w5x-w6.md`, `pipeline-w7-w9.md`, `pipeline-feature-specs.md`). Loaded **alongside**
`pipeline-w0-w5.md` before W0–W5 dispatch — the task chain binds `profile` / `produce()` here and
references the canonical Renumber+Contiguity Gate by name. See `pipeline.md` for the wave dep graph.

## Profile-driven dispatch (v11.0.0)

The orchestrator resolved a **stack-profile** at preflight (`detect_stack_profile.py` →
`recommended_profile`, or AskUserQuestion / `generic-source` fallback). Load it once and bind it for
the wave graph (RT-F1 — `artifact_map` GATES dispatch, it is not merely printed):

```js
// `profileId` resolved at preflight (SKILL.md Preflight step 2).
const profile = JSON.parse(readFile(
  `claude/skills/rebuild-spec/references/stack-profiles/${profileId}.json`))
// produce(<artifact>): true unless the profile explicitly maps it to "skip".
// Unmapped artifact → fail-open produce (universal default).
// v21.0.0 — screen_source precedence (authoritative gate for screen-list/screen-flow ONLY):
//   these two are produced IFF profile.screen_source != "none", OVERRIDING their artifact_map.action.
//   delphi-vcl (screen_source: "dfm-form") ALSO sets artifact_map screen-list/screen-flow → "produce"
//   so the profile reads self-consistently (no skip-vs-override contradiction); the override is the
//   single source of truth and additionally lets ANY profile leave them "skip" without harm.
//   oracle-plsql/generic (screen_source: "none") never produce them regardless of artifact_map.
//   Every OTHER artifact — incl. route-list / api-map — is governed solely by artifact_map (unchanged).
const SCREEN_ARTIFACTS = new Set(["screen-list", "screen-flow"])
const screenSource = profile.screen_source ?? "none"   // defensive default (schema requires the field)
const produce = (art) =>
  SCREEN_ARTIFACTS.has(art)
    ? screenSource !== "none"
    : (profile.artifact_map[art]?.action ?? "produce") === "produce"

// ───────────────────────────────────────────────────────────────────────────────────────────
// MANDATORY RULE — the screen-artifact skip decision is `produce()` ONLY. Read this before Wave 2.
//   `screen-list`/`screen-flow` are produced whenever `produce(...)` is true — i.e. whenever
//   `profile.screen_source != "none"`. This is the SINGLE authority. Do NOT skip them for ANY
//   other reason, in particular:
//     ✗ NOT because their `class` is `"web"` and the project "looks non-web" (Delphi/desktop). The
//       `class` field feeds ONLY the universal-drop guard below — it NEVER gates screen production.
//       A `dfm-form` profile (Delphi) HAS screens (.dfm TForm units); class:web is a legacy label,
//       not a skip signal. Screens are no longer a web-only concept (v21.0.0).
//     ✗ NOT because `route-list` was skipped. screen-list/screen-flow do NOT require route-list on a
//       non-web stack — their source is `_digest_extract_form_nav.json` (see pipeline-w0-w5 Wave 2).
//     ✗ NOT because `artifact_map.action` reads "skip" on some older profile copy — `produce()`
//       (screen_source) overrides it; the shipped profiles also set action:"produce" to agree.
//   If `produce("screen-list")` is true, Wave 2 MUST author screen-list + screen-flow. Skipping them
//   while screen_source != none is a BUG, not a judgement call. (This rule exists because runs were
//   observed silently skipping Delphi screens by reading `class:web`/`action:skip` and ignoring the
//   override — see CHANGELOG v21.0.0 "Anti-skip hardening".)
// ───────────────────────────────────────────────────────────────────────────────────────────

// Producing/skipping manifest (printed once at Wave 0 open).
// Use produce() (not raw action) so screen_source precedence is reflected honestly: a profile's
// screen-list/screen-flow show under "producing" whenever screen_source != none.
const allArtifacts = Object.keys(profile.artifact_map)
const producing = allArtifacts.filter(produce)
const skipping = allArtifacts.filter((k) => !produce(k))
console.log(`[PROFILE] ${profile.id} (screen_source: ${screenSource}) — producing: ${producing.join(",")} | skipping: ${skipping.join(",")}`)
// Universal-drop guard: a universal artifact skipped while a web artifact is produced.
const droppedUniversal = Object.entries(profile.artifact_map)
  .filter(([,v]) => v.action === "skip" && v.class === "universal").map(([k]) => k)
const producesWeb = Object.entries(profile.artifact_map).some(([,v]) => v.action === "produce" && v.class === "web")
if (droppedUniversal.length && producesWeb)
  console.log(`[WARN] universal_artifact_dropped: ${droppedUniversal.join(",")}`)
```

### Wave 0.6 — structural extraction (v11.1.0, RT-F1 guard `extractors.length > 0`)

Runs after scout (Wave 0), before W1. Deterministic, per-profile. Web profiles declare
`extractors: []` → this whole block is skipped cleanly.

```js
if ((profile.extractors ?? []).length > 0) {
  for (const ext of profile.extractors) {  // e.g. extract_sql_schema, extract_data_flow
    // Resume: skip an extractor already completed in _extraction-manifest.json (RT-F11).
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/${ext}.py \
      --root . --plan-dir plans/<active-plan> \
      --encoding "${profile.source_encoding.primary}" \
      --fallback "${profile.source_encoding.fallback}"
    // writes plans/<active-plan>/artifacts/_digest_${ext}.json (atomic) + updates _extraction-manifest.json
  }
  // Wave 0.6 complete ONLY when every declared extractor is completed:true in the manifest.
  console.log(`[INFO] Wave 0.6 structural extraction complete: ${profile.extractors.join(", ")}`)
} else {
  console.log(`[SKIP] Wave 0.6 structural extraction (profile ${profile.id}: extractors=[])`)
}
```

The digests feed W1.b (crud-matrix) + W1.c (db-objects) — dispatched alongside W1 when the profile
maps those artifacts to `produce`. W1.b/W1.c researchers write the artifact FROM the digest (every
cell citation-bound), then `validate_crud_matrix.py` / `validate_db_catalog.py` gate the result. See
`references/structural-extractor-contract.md`. Both emit `[WARN] stale_digest` if the digest's
`source_tree_hash`/`generated_at` is older than current source.

**Guard rule:** wrap every web-class dispatch + its halt gate in `if (produce("<artifact>")) { … }`.
A `skip` creates NO task and runs NO gate — print `[SKIP] <artifact> (profile)` instead. The guarded
points below: `route-list` (+ W1.1 gate), `screen-list`/`screen-flow` (+ W2a.1 gate), `api-map`
(`behavior-logic`/`data-model`/`user-stories`/`feature-list` are universal — always produced). Wave 0.4
route-probe is additionally gated on `profile.probe.bootable`. This is a **conditional branch reading
data** — NOT a per-stack fork; one wave-graph, profile-driven.

**Stack identity (RT-F2):** `detectedStack` / `stackNote` / `[MULTI_STACK]` derive from the profile detect
output — `profile.detected_language_heading` is the canonical `## Detected Language` value, and the
`[MULTI_STACK]` annotation is built from `detectJson.matched[]` (every profile that matched), not only the
root-manifest scan. The legacy `manifestMap` scan below is retained as a secondary signal for web stacks.

## Renumber+Contiguity Gate (canonical)

This gate runs after every artifact write (full runs only). Referenced inline at each artifact wave.
**Substitution:** replace `<artifact>` with the artifact name (e.g. `data-model`, `screen-list`).
**Full vs incremental:** renumber fires on full runs only; contiguity always runs (report-only on incremental).

```js
// Apply "Renumber+Contiguity Gate (canonical)" with artifact=<artifact>
// F4: renumber fires on FULL runs ONLY.
// F2: async-TaskCreate guard — caller must confirm artifact file is non-empty and fully merged.
const isFull = mode === "full"
if (isFull) {
  // 1. RENUMBER (full-gen only)
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
    --artifact <artifact> --plan-dir plans/<active-plan>
  // 2. CONTIGUITY GATE
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
    --artifact <artifact> --plan-dir plans/<active-plan> \
    --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  // exit 1 → FAIL → HALT (surface JSON); exit 2 → internal error → halt  [HALT scoped to FULL mode]
} else {
  // F4: ANY incremental (incl. --artifact) → renumber SKIPPED, contiguity report-only.
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
    --artifact <artifact> --plan-dir plans/<active-plan> --report-only \
    --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  // report-only → exit always 0, gaps downgraded to warning, NEVER halts
  console.log(`[INFO] <artifact> renumber skipped (incremental: IDs frozen)`)
}
```

Exception — combined W2 path (screen-list + behavior-logic): run renumber+contiguity for EACH artifact
in order (SCR renumber → BL renumber → SCR contiguity → BL contiguity) before the W2a.1 composite guard.

Exception — feature-list: F### integrity gate runs FIRST (before renumber), then renumber, then
slice-plan key rewrite, then contiguity gate. See W5 orchestrator post-step for full sequence.
