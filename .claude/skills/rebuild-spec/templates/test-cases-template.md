<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Test Cases — {F###_NAME}

**SIDECAR (v26.1.0):** this is a 5th, optional file alongside the 4 mandatory feature-spec files.
Its absence never blocks feature-spec promotion.

**Code Format**: `TC###` — 3-digit zero-padded, **resets per feature** (this file's own scope is
the reset boundary; unlike `JOB###`, which is file-global).

**Citation-source split**: `UT`/`IT` rows cite a `BR-###`/`SM-###`/`DEC-###`/`DISC-###` code, a
`` `file:line` ``, or an `edge-cases.md` row. `UAT` rows cite a `screens.md`/`business-context.md`
section — NEVER a bare code (UAT is less code-traceable by design; see
`references/test-cases-researcher-contract.md`).

**CSV export**: out of scope v1 — Markdown is the sole output. See plan Decision.

---

## Test Cases

| Test-ID | Type (UT\|IT\|UAT) | Given | When | Then | Traces-to |
|---------|---------------------|-------|------|------|-----------|
| {TC001} | {UT} | {precondition / input state} | {action / event} | {expected observable outcome} | {`BR-001`} |
| {TC002} | {IT} | {precondition spanning ≥2 components} | {action / event} | {expected observable outcome} | {`SM-001`} |
| {TC003} | {UAT} | {user starting point} | {user action} | {what the user sees/can do next} | {screens.md § User Journey step N} |

{Zero derivable test cases (rare) → replace the table above with:
`_(no test cases derived — feature has no BR/SM/DEC/DISC codes or edge cases)_`}

---

## Coverage Notes

{Optional. List any BR-###/SM-###/DEC-###/DISC-### code from technical-spec.md that
deliberately has NO tracing test case, with the `[NO_TEST_CASE]` marker and a one-line rationale.
An unlisted, uncovered code still WARNs (non-halting) at the TC.2 validator — 100% coverage is
not always achievable or desired.}

- {`BR-004`} — [NO_TEST_CASE] {one-line rationale, e.g. "pure logging side-effect, nothing
  observable to assert"}
