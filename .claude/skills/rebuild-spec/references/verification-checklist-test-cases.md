<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Verification Checklist: TestCases (`--test-cases` pass, TC.3)

See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope:** Loaded ONLY by the `--test-cases` pass reviewer (TC.3). Do NOT load in the default
(core) W7a run, nor in FS.5 (feature-spec review) — test-cases.md is a SIDECAR reviewed by its
own pass.

## TestCases

**Cross-refs:** `docs/features/{fcode}/technical-spec.md` (BR-###/SM-###/DEC-###/DISC-### source
of record), `docs/features/{fcode}/edge-cases.md` (negative-path source), `docs/features/{fcode}/
screens.md` + `business-context.md` (UAT source).

**Deterministic checks (TC.2 `validate_test_cases.py` — pre-TC.3):** `TC###` regex + per-feature
uniqueness, `Type` ∈ {UT, IT, UAT}, `Traces-to` presence, citation-source-family match (UT/IT →
code/file:line/edge-cases.md; UAT → screens.md/business-context.md section), coverage-gap report
(BR/SM/DEC/DISC codes with 0 tracing test case and no `[NO_TEST_CASE]` marker — WARN, non-halting).
Rule IDs passing TC.2 are marked `[deterministic-pass]` — skip in semantic review.

**Semantic review rules (TC-S1..TC-S6):**
- [ ] **TC-S1 Given/When/Then actually matches the cited code:** for ≥2 rows per feature, read
  the cited BR/SM/DEC/DISC block (or `file:line`) and verify the Then outcome is what that code
  actually does. A Then that contradicts or embellishes the cited behavior → critical.
- [ ] **TC-S2 UAT citation is genuinely a screens.md/business-context.md section:** a UAT row
  whose Traces-to is a code dressed up as a section reference (e.g. `BR-001 (see screens.md)`) is
  a smuggled code-only citation — critical (defeats the citation-source split's purpose).
- [ ] **TC-S3 No padding for coverage:** a row whose Given/When/Then is generic boilerplate with
  no feature-specific detail (e.g. "input is invalid → error is shown") added only to avoid a
  coverage-gap WARN → critical. Coverage gaps are meant to surface, not be papered over.
- [ ] **TC-S4 `edge-cases.md` reuse is faithful:** a UT/IT row citing `edge-cases.md` must match
  that row's actual Scenario/What-Happens content, not a paraphrase that drifts from it.
- [ ] **TC-S5 `[NO_TEST_CASE]` rationale is real:** each `## Coverage Notes` entry's rationale
  must plausibly explain why the code has no test case (not a placeholder like "N/A" with no
  reasoning) — an empty or generic rationale → warning.
- [ ] **TC-S6 DRY — no verbatim BR/SM/DEC/DISC re-listing:** Given/When/Then MUST NOT be a
  verbatim copy of the cited block's description prose — it must be reshaped into a concrete
  scenario. Verbatim duplication → warning (DRY violation, not a citation problem).

**Critical edge cases:**
- `TC###` not matching `^TC\d{3}$`, or duplicated within the same feature's file → critical
  (`validate_test_cases.py` gates this)
- `Type` not one of `UT`/`IT`/`UAT` → critical
- `Traces-to` empty, or citation-source family mismatched with `Type` → critical
- Zero test cases derived AND the feature has ≥1 BR/SM/DEC/DISC code with no `[NO_TEST_CASE]`
  note → the file is technically valid (empty-table fallback is allowed) but the coverage-gap
  WARN fires for every uncovered code — reviewer should flag if this looks like an under-effort
  draft rather than a genuinely test-case-poor feature.

**Advisory (non-defect):** `confidence-report_test-cases.md` beside the promoted `test-cases.md`
is an optional, best-effort sidecar (`scripts/derive_confidence_report.py`, v25.2.0). Its absence
is NOT a defect — do NOT flag a missing companion as a review finding. See
`references/confidence-report-contract.md`.

**Sidecar reminder (non-defect):** `test-cases.md` missing entirely for a feature is NOT a
promotion blocker — it is not in `FEATURE_FILES` and is never checked by
`check_promotion_gate.py`. Do NOT flag a feature as `MISSING` for lacking `test-cases.md`.

## Failure Trap Assertions (TestCases-specific)

- **Trap — citation-source laundering:** a UAT row citing a code, or a UT/IT row citing only a
  screens.md/business-context.md section, defeats the entire point of the citation-source split
  (risk (b) from the design phase) → critical, not a style nit.
- **Trap — coverage-gap suppression by padding:** adding a low-value, generic test case purely to
  avoid a coverage-gap WARN is worse than leaving the gap WARN visible — the WARN is a signal, not
  a defect to be hidden.
