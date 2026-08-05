<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Incremental State Schema

Two committed JSON files anchor incremental mode. Both live under `docs/` so they survive plan archival and are git-collaborative.

## `.rebuild-state.json`

Lives at `docs/.rebuild-state.json`.

```json
{
  "schema_version": "21.0.0",
  "primary_lang": "en",
  "last_rebuild_sha": "abc123def456...",
  "last_feature_spec_run_sha": "abc123def456...",
  "last_flows_run_sha": "abc123def456...",
  "last_glossary_run_sha": "abc123def456...",
  "rebuilt_at": "2026-05-20T08:30:00Z",
  "mode": "full|incremental",
  "fcode_index_sha": "sha256-hex-of-canonical-index-json",
  "translations": {
    "jp": {
      "translated_from_sha": "abc123def456...",
      "last_translate_run_sha": "abc123def456...",
      "passes_translated": ["core", "feature-specs", "flows", "glossary"]
    }
  },
  "doc_shas": {
    "route-list.md": "<sha256-hex>",
    "data-model.md": "<sha256-hex>",
    "screen-list.md": "<sha256-hex>",
    "screen-flow.md": "<sha256-hex>",
    "behavior-logic.md": "<sha256-hex>",
    "api-map.md": "<sha256-hex>",
    "permissions.md": "<sha256-hex>",
    "user-stories.md": "<sha256-hex>",
    "feature-list.md": "<sha256-hex>",
    "glossary.md": "<sha256-hex>"
  },
  "screen_spec_shas": {
    "SCR001": "<sha256-hex>",
    "SCR003": "<sha256-hex>"
  },
  "probe_gate": {
    "status": "awaiting_user",
    "checkpoint_wave": "Wave1: route-list",
    "probe_result": null,
    "manifest_path": null
  }
}
```

Keys in `doc_shas` are bare filenames (e.g. `route-list.md`); values are SHA-256 digests of the artifact at its layered path under `docs/` (e.g. `docs/generated/route-list.md`). See `ARTIFACT_LAYERED_PATH` in `scripts/incremental_planner.py` for the canonical filename→path mapping.

| Field | Type | Semantics |
|-------|------|-----------|
| `schema_version` | string | **[v21.0.0 — RT-F4]** State-file schema version (semver), kept in sync with `_stack_profile_lib.SCHEMA_VERSION`. On resume, if absent or `< "21.0.0"` (compare numerically, not lexically), the run **invalidates the preflight checkpoint** and re-runs `detect_stack_profile.py` + profile-resolve BEFORE continuing the wave graph. Two reasons across history: a pre-v11.0.0 state cannot carry a `profile_id`/encoding; a v11.0.0–v20.x state predates the `screen_source` profile field (v21.0.0) and would resume carrying a profile that fail-closes screens to `"none"`. Written on every state write at the current skill version. Absent key = pre-profile legacy state. |
| `primary_lang` | string | Language of the FIRST run (set once, stable thereafter). Default `"en"` when first run had no `--lang`. The primary language is generated inline from source; its freshness is tracked by the existing top-level cursor fields. |
| `translations` | object | `{ "<lang>": { translated_from_sha, last_translate_run_sha, passes_translated } }` — per-secondary-language translation cursors. Keys are normalized language codes (never includes `primary_lang`). Written by the translate pass (Phase 03 TR.5) and auto-sync (Phase 04). A secondary language L is "outdated" when `translations[L].translated_from_sha` != the primary's current cursor SHA. |
| `last_rebuild_sha` | string | `git rev-parse HEAD` at core-pass emit time. Advanced ONLY by the core pass (`--cursor core`). Can be set explicitly via `--last-rebuild-sha` during bootstrap-from-git flow (Wave -2); otherwise derives from `git rev-parse HEAD`. |
| `last_feature_spec_run_sha` | string | `git rev-parse HEAD` at the time `--feature-specs` pass completed. Advanced ONLY by `--cursor feature-specs`. **This is the diff base the `--feature-specs` planner reads** (NOT `last_rebuild_sha`): empty → first run → process ALL fcodes; set → diff source since this SHA. Reusing `last_rebuild_sha` would let a prior core run shrink the diff and silently leave specs stale. |
| `last_flows_run_sha` | string | `git rev-parse HEAD` at the time `--flows` pass completed. Advanced ONLY by `--cursor flows`. Empty string until `--flows` has run. Reserved: the `--flows` pass currently always re-synths all flows, so this is not yet read as a diff base (informational + future incremental). |
| `last_glossary_run_sha` | string | `git rev-parse HEAD` at the time `--glossary` pass completed. Advanced ONLY by `--cursor glossary`. Empty string until `--glossary` has run. Reserved: the `--glossary` pass currently always re-synths, so this is not yet read as a diff base (informational + future incremental). |
| `rebuilt_at` | string | ISO-8601 UTC timestamp |
| `mode` | string | `"full"` or `"incremental"` — the mode of the run that wrote this file |
| `fcode_index_sha` | string | SHA-256 hex digest of the canonical `_source-to-fcode.json` content |
| `doc_shas` | object | `{ "<artifact-filename>.md": "<sha256-hex>" }` — snapshot of promoted core docs, feeding out-of-band-edit detection (`_detect_oob`); absent on first run. Keys are bare filenames; files read from layered `docs/system/` or `docs/generated/` paths. **Refresh ownership:** only the `core` pass refreshes the full set; `glossary` refreshes ONLY `glossary.md`; `flows`/`feature-specs` preserve prior values verbatim (they touch no tracked core artifact). A non-core pass that re-stamped everything would silently mask an out-of-band edit made since the last core run. Does NOT include flows/features/screens (each is regenerated by its own pass). |
| `screen_spec_shas` | object | `{ "SCR###": "<sha256-hex>" }` — per-screen section sha snapshot from `screen-list.md`; absent on legacy state or when `--screen-specs` never used |
| `probe_gate` | object\|absent | Durable Wave 0.4 bootability gate state. Absent key = pre-probe legacy repo. Written on all three outcomes: `awaiting_user`, `passed`, `skipped`. See schema below. Survives session end — persists across runs. |

#### `probe_gate` object schema

Example — awaiting user (pipeline halted):
```json
{
  "status": "awaiting_user",
  "checkpoint_wave": "Wave1: route-list",
  "probe_result": null,
  "manifest_path": null
}
```

Example — probe ran successfully (pipeline may proceed):
```json
{
  "status": "passed",
  "checkpoint_wave": "Wave1: route-list",
  "probe_result": "tier1_ok",
  "manifest_path": "plans/<active>/artifacts/route-manifest.json"
}
```

| Field | Type | Semantics |
|-------|------|-----------|
| `status` | string | `"awaiting_user"` — user chose "Need to set up app first"; pipeline halted; resume pending. `"passed"` — probe ran successfully (Tier-1 or deferred to Tier-2); pipeline may proceed. `"skipped"` — user explicitly declined probe; W1 route-list uses Tier-2 static parse. |
| `checkpoint_wave` | string | Pipeline wave to resume at on re-run. Always `"Wave1: route-list"` for v5.x. |
| `probe_result` | string\|null | Result of the Tier-1 CLI probe: `"tier1_ok"` (manifest written), `"tier1_failed"` (probe ran but errored; W1 falls back to Tier-2), `"skipped"` (user declined or `--full` re-probed fresh), `null` (probe not yet run — status is `awaiting_user`). |
| `manifest_path` | string\|null | Repo-relative path to the `_route-probe.json` sidecar manifest written by `probe_routes.py`. `null` when probe skipped or not yet run. |

**Backward compatibility:** Runs on repos where `probe_gate` key is absent in `.rebuild-state.json` behave exactly as before — no probe prompt, no probe gate. **Absent key = pre-probe legacy repo.** The key is written on all three probe outcomes (`awaiting_user`, `passed`, `skipped`). After a successful probe (`"passed"`) or a declined probe (`"skipped"`), the status is updated and the value **persists**; it is not erased. Incremental runs reuse the persisted status (skipping the prompt entirely). `--full` re-prompts and re-probes fresh **only when a bootable stack is detected or `--probe-routes` is passed** (condition: `hasBootableStack || explicitProbeRoutes`); `--full` alone on a non-bootable, non-flagged repo does not trigger the probe gate.

### Cursor isolation rule (CRITICAL — v5.0.0)

Each pass advances ONLY its own cursor. A non-core pass calling `build_source_to_fcode.py`
without `--cursor` would advance `last_rebuild_sha` (core cursor) and make the next core
incremental skip real source changes. Use `--cursor <pass>` to prevent this:

| Pass | `--cursor` value | Cursor advanced |
|------|-----------------|-----------------|
| Core (`/tkm:rebuild-spec`) | `core` | `last_rebuild_sha` |
| `--feature-specs` | `feature-specs` | `last_feature_spec_run_sha` |
| `--flows` | `flows` | `last_flows_run_sha` |
| `--glossary` | `glossary` | `last_glossary_run_sha` |
| `--api-contracts` | `api-contracts` | `last_api_contracts_run_sha` |

All other cursors are read from prior state and preserved verbatim.

## `_source-to-fcode.json`

```json
{
  "generated_at": "2026-05-20T08:30:00Z",
  "index": {
    "api/app/Http/Controllers/SurveyController.php": ["F001", "F005"],
    "web/src/pages/SurveyCreate.vue": ["F005"]
  }
}
```

| Field | Type | Semantics |
|-------|------|-----------|
| `generated_at` | string | ISO-8601 UTC timestamp |
| `index` | object | `{ "<repo-relative-path>": ["F###", ...] }` — sorted by path key; each value is a sorted unique array |

**Empty index is valid** (RT-C5): when `docs/features/` is absent or has no spec files, the
index is `{}`. Core-only runs always produce an empty index; `--feature-specs` incremental
treats an absent or empty index as "all fcodes" (RT-C1).

## Citation parse rules

Only TWO citation forms are recognized (verified against real specs):

1. **Inline `**Source:**`**: `**Source:** \`path/to/file.ext:44-58\``
   - Regex: `` r'\*\*Source:\*\*\s+`([^`]+)`' ``
2. **Table row in `## Source Code References`**: backtick-wrapped path in table cells
   - Regex (within section only): `` r'`([^`]+\.[A-Za-z0-9]+(?::[0-9\-]+)?)`' ``
   - Section bounded by `## Source Code References` heading until next `## ` heading

**Which spec file is read**: v4 features use `technical-spec.md` (holds `## Source Code References`).
`build_source_to_fcode.py` globs `*/technical-spec.md` first; legacy `*/spec.md` files are
picked up as a backward-compat fallback when `technical-spec.md` does not exist in the same dir.

## Path normalization

- Strip `:lines` suffix (e.g. `api/foo.php:44-58` → `api/foo.php`)
- Forward-slash only (`Path.as_posix()`)
- Repo-relative (no leading `/` or `./`)

## SHA computation (`fcode_index_sha`)

Canonical JSON serialization then SHA-256:

```python
canonical = json.dumps(index, sort_keys=True, separators=(",", ":"))
sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

Where `index` is the `"index"` sub-object of `_source-to-fcode.json` (excluding `generated_at` so the hash is a stable content fingerprint).

## `.incremental-plan.json`

Per-run decision payload emitted by `scripts/incremental_planner.py`. Lives at `plans/<active>/artifacts/.incremental-plan.json`. Ephemeral — each incremental run overwrites it.

```json
{
  "mode": "incremental",
  "affected_waves": ["Wave1: route-list", "Wave2: screen-list + screen-flow"],
  "affected_fcodes": ["F001", "F005"],
  "w5_reran": true,
  "cascade_chain": "route → W1.route-list → W2 → W3 → W4 → W5",
  "fallback_reason": null,
  "fallback_to_full": false,
  "deleted_files": [],
  "doc_shas_snapshot": {
    "route-list.md": "<sha256-hex>",
    "data-model.md": "<sha256-hex>"
  },
  "generated_at": "2026-05-20T08:30:00Z",
  "since_sha": "abc123",
  "head_sha": "def456",
  "affected_screens": ["SCR001", "SCR003"],
  "screen_spec_shas_snapshot": { "SCR001": "<sha>", "SCR002": "<sha>" },
  "stale_features": true,
  "stale_flows": true,
  "stale_glossary": false
}
```

| Field | Type | Semantics |
|-------|------|-----------|
| `mode` | string | `"full"` or `"incremental"` — decision output |
| `affected_waves` | string[] | Pipeline.md subject strings for waves that must re-run; empty for `other`-only changes |
| `affected_fcodes` | string[] | F### codes whose specs must be regenerated; all F### if `w5_reran=true` |
| `w5_reran` | boolean | `true` if Wave 5 (feature-list) is in `affected_waves`; gates FS.1 (feature-specs) scope (all vs subset) |
| `cascade_chain` | string | Human-readable cascade trace for logging; `null` if mode=full |
| `fallback_reason` | string\|null | Why mode fell back to full; `null` if incremental succeeded |
| `fallback_to_full` | boolean | `true` if planner originally computed incremental but a fallback condition fired |
| `deleted_files` | string[] | Repo-relative paths deleted since `last_rebuild_sha`; advisory only |
| `doc_shas_snapshot` | object | `{ "<artifact>.md": "<sha256>" }` — state of `docs/` artifacts at plan time; updated by hydrate |
| `generated_at` | string | ISO-8601 UTC timestamp of planner invocation |
| `since_sha` | string | Git SHA used as diff base (`last_rebuild_sha` from state file) |
| `head_sha` | string | Current `git rev-parse HEAD` at plan time |
| `affected_screens` | string[] | SCR### codes to regenerate; absent when `mode=full` (treat absent as "all screens") |
| `screen_spec_shas_snapshot` | object | Full sha snapshot of all SCR sections at plan time; promote step writes this into `.rebuild-state.json → screen_spec_shas` |
| `stale_features` | boolean | `true` iff ≥1 changed source file maps to an F### via reverse-index. Signals `--feature-specs` may need a re-run. Only present in `mode=incremental` core payloads (V7). |
| `stale_flows` | boolean | `true` iff `stale_features` OR data-model/screen-flow/behavior-logic wave re-generated. Signals `--flows` may need a re-run. Only present in `mode=incremental` core payloads (V7). |
| `stale_glossary` | boolean | `true` iff `stale_features` OR data-model wave re-generated. Signals `--glossary` may need a re-run. Only present in `mode=incremental` core payloads (V7). |

## Per-pass validator summary files (RT-C2)

Each pass writes its own validator summary JSON to avoid clobbering the core `validation-summary.json`:

| Pass | Validator summary file |
|------|----------------------|
| Core (`/tkm:rebuild-spec`) | `validation-summary.json` |
| `--feature-specs` | `fs-validation-summary.json` |
| `--flows` | `flow-validation-summary.json` |
| `--glossary` | *(no separate validator; glossary content reviewed inline)* |

Validators accept `--summary-out <path>` to route their output. Pipeline stages pass the
appropriate path; no change needed to the validator scripts themselves.

## Screen section sha computation

Parse `screen-list.md`, slice body from each `## SCR\d{3,4}[a-z]?` heading to next heading (or EOF). `sha256(body.encode("utf-8")).hexdigest()` per SCR. Headings themselves excluded from the body to avoid noise on whitespace-only edits to the heading line.

## Stale marker files (V7 — selective staleness)

Written by the core incremental planner (W9 step) ONLY when `stale_*` flags are true.
Each pass CLEARS its own marker on successful promote.

| Flag true | Marker written | Content |
|-----------|---------------|---------|
| `stale_features` | `docs/features/.stale` | `source changed — run '/tkm:rebuild-spec --feature-specs' to refresh` |
| `stale_flows` | `docs/flows/.stale` | `source changed — run '/tkm:rebuild-spec --flows' to refresh` |
| `stale_glossary` | `docs/system/.glossary.stale` | `source changed — run '/tkm:rebuild-spec --glossary' to refresh` |

No marker is written when the corresponding flag is false (no noise for unrelated changes).
`docs/features/.stale` is also written by `promote_drafts.py --scope core` when leftover
`docs/features/` dirs exist after a v4→v5 upgrade (RT-C4).

## `translation-stale.json` (transient)

Lives at `plans/<active>/artifacts/translation-stale.json`. Written by each primary pass post-promote listing which artifacts changed. Consumed by the auto-sync hook (Phase 04) to scope the translate pass to only the changed artifacts. Ephemeral — each primary pass overwrites it.

```json
{
  "pass": "core",
  "changed_artifacts": ["route-list.md", "data-model.md"],
  "primary_cursor_sha": "abc123def456..."
}
```

| Field | Type | Semantics |
|-------|------|-----------|
| `pass` | string | Which pass just promoted (`core`, `feature-specs`, `flows`, `glossary`, `screen-specs`, `api-contracts`) |
| `changed_artifacts` | string[] | Artifact filenames (or fcode slugs for features, flow slugs for flows) that changed this pass |
| `primary_cursor_sha` | string | The primary's cursor SHA at promote time — written into `translations[L].translated_from_sha` on successful translate |
