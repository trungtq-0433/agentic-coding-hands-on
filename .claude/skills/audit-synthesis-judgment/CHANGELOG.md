# Changelog — `audit-synthesis-judgment`

All notable changes to this skill. Versioning follows the kit convention (semver in SKILL.md `metadata.version`).

## 1.0.0 — 2026-07-21

### Added

- **The fourth audit axis for rebuild-spec's synthesis tier — judgment soundness.** Not coverage
  (A1 confidence-report), not truth (audit-doc-parity, which its Iron Law #6 forbids from grading a
  judgment), but whether the feature partition is well-drawn, the user-story enumeration sound, the
  inferred "why" a valid inference, and the artifact set complete + non-redundant. Report-only;
  emits `judgment-report.md` with machine-readable PASS/FAIL frontmatter.
- **Three engines layered by objectivity:**
  - **Engine 1 — deterministic coverage (the ONLY FAIL source).** `coverage_engine.py` +
    `_graph_state_lib` (absent/empty/partial/stale classification) + `_coverage_orphan_lib`
    (code-level orphans, symbol-level materiality, empty-index guard) + `_coverage_phantom_lib`
    (citation→graph-node resolution, graph-completeness gated) + `_redundancy_lib` (literal
    duplicate-artifact FAIL only). Advisory roll-up of an enumerated validator subset. Loud
    `coverage_status` — a no-graph / core-only / partial-graph run degrades to UNVERIFIABLE, never a
    silent PASS. `--strict-coverage` turns a missing graph on a `graphable` stack into a hard FAIL.
  - **Engine 2 — protocol-conformance boundary check (WARN).** `boundary_conformance.py` +
    `_ipe_parse_lib` + `_ipe_conformance_lib`. Parses the promoted `user-stories.md` and audits
    conformance to the per-stack IPE Step-3 merge rule + Step-4 anti-CRUD rule — catching the
    86-vs-354 over/under-merge deterministically, citing the violated clause. No re-synthesis.
  - **Engine 3 — adversarial judgment residue (WARN).** `judgment_engine.py` (`prepare`/`assemble`)
    + `_granularity_lib` (MAD outlier stat with a mean-AD fallback). LLM judges on inference
    validity (Toulmin), naming, granularity, and "restates w/o added why"; no finding stands without
    surviving a ≥2-refuter majority refutation pass (single-pass only at `--level low`). design-intent
    findings WARN-capped (EXPERIMENTAL upstream).
- **Load-bearing invariant:** every FAIL/WARN anchors to a computed signal; FAIL is Engine-1
  deterministic computation alone — a stochastic Engine-2/3 signal never increments a FAIL count.
- **Prompt-injection defense** (`references/prompt-injection-defense.md`): scanned doc/code prose is
  inert DATA; Engine-3 judge/refuter output is schema-constrained so an injected `<!-- SYSTEM: … -->`
  cannot change a verdict (tested).
- **`--plan-dir`** locates an un-promoted `design-intent.md`; the locator refuses to guess when the
  flag is absent and multiple candidate plan dirs exist.
- Wired **optional / non-blocking / off-by-default** into five rebuild-spec pass handoffs
  (`pipeline-w7-w9`, `pipeline-feature-specs`, `pipeline-flows-glossary`, `pipeline-jobs`,
  `pipeline-design-intent`). Core-pass advisory points at `--scope user-stories` with a timing note
  (code-level coverage needs `--feature-specs` first).

### Notes

- **`_citation_lib.py` is COPIED from `audit-doc-parity`** (not imported) so this skill is
  self-contained / independently installable — `audit-doc-parity` may not be present, whereas
  `rebuild-spec` (whose output this audits) always is. The copy still resolves `rebuild-spec`'s
  `_lang_lib` as a sibling for layout-aware docs-root resolution. A test asserts the copied
  `CITATION_RE` matches parity's behavior; keep the two in sync when parity's citation/path-guard
  logic changes.
- Added a `graphable: true|false` field to the five stack-profile JSONs (`web-js-ts`,
  `generic-source` → true; `cobol`, `delphi-vcl`, `oracle-plsql` → false) — consumed by
  `--strict-coverage`.
