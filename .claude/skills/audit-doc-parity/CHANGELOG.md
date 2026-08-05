# Changelog — `audit-doc-parity`

All notable changes to this skill. Versioning follows the kit convention (semver in SKILL.md `metadata.version`).

## 1.1.0 — 2026-06-26

### Added
- **Layout-aware docs-root resolution** — discovery now resolves the real docs root instead of
  hardcoding `docs/`. A non-English single-lang repo (`primary_lang: vi` → docs at `docs/vi/`) or a
  per-lang repo (`docs/<primary>/`) is detected automatically. `_citation_lib.resolve_docs_root()`
  reads `primary_lang`/`translations` from the rebuild-state file (canonical `docs/.rebuild-state.json`
  or the per-lang `docs/<lang>/.rebuild-state.json`) and defers the single-vs-per-lang decision to
  rebuild-spec's canonical `_lang_lib` (single source of truth — see
  `_shared/docs-canonical-mapping.md` § Language Layout). Both `scope_doc_units.py` and
  `estimate_parity_run.py` now use it.

### Fixed
- **`estimate`/`scope` returned 0 units on non-English repos** — auto-discovery globbed only `docs/`
  while the docs lived under `docs/<primary>/`. The sweep gate now finds the in-scope docs. Degrades
  gracefully to bare `docs/` when no state file exists (legacy en behavior) or when `_lang_lib` is
  unavailable (audit-doc-parity installed without rebuild-spec).

## 1.0.0 — 2026-06-26

Initial release. Standalone semantic-parity auditor for citation-anchored, rebuild-spec-shaped docs.

### Added
- **Blind reverse-regeneration architecture** — an LLM re-describes the cited code into the doc's
  structured schema *without seeing the doc*, then a field-level diff surfaces drift. Defeats the
  anchoring bias that lets stale/fabricated/undocumented behavior slip past wording review (rebuild-spec W7a).
- **5-verdict taxonomy** — MATCH / DRIFT / FABRICATED / MISSING / UNVERIFIABLE, severity = blast radius,
  `parity_score` excluding UNVERIFIABLE, `result: PASS iff drift==0 && fabricated==0`.
- **Materiality filter** — MISSING fires only for documentation-worthy behavior (routes, user-visible
  rules, data mutations, auth gates, external side-effects, observable output contracts); field-level
  MISSING on under-described output contracts (format/columns/encoding/naming) — provably extractable only.
- **Legacy-project safety** — exclusion (both directions, reusing rebuild-spec skip-set), non-source
  behavior sources (SQL/cron/shell/config/templates), encoding-safe reads (Shift-JIS/BOM/CRLF) +
  stale-anchor degradation, live-vs-dead-code reachability. Governing rule: ambiguous → UNVERIFIABLE,
  never false DRIFT/MISSING.
- **Python plumbing (no verdicts)** — `_citation_lib.py`, `scope_doc_units.py`, `parse_doc_schema.py`,
  `estimate_parity_run.py`, `assemble_parity_report.py`. Stdlib only. Reuses rebuild-spec `CITATION_RE`,
  `assert_under`/`resolve_project_root`, the `estimate_artifact_loc.py` pattern, and `atomic_write`.
- **Modes** — `--feature F###`, `--path <doc>`, default sweep (estimate-gated); `--level low|medium|high|max`.
- **Optional rebuild-spec post-W9 gate pointer** — non-blocking, off by default.
