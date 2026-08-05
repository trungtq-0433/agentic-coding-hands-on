# Pipeline — `audit-doc-parity`

The end-to-end orchestration. Python plumbs (steps 0, 1, 5); the LLM judges (steps 2, 3, 4). This
keeps the "LLM judges, Python plumbs" invariant: no Python step ever emits a verdict.

All scripts run via `.claude/skills/.venv/bin/python3 claude/skills/audit-doc-parity/scripts/<script>.py`.

## Step 0 — Estimate & gate (Python; sweep only)

```
estimate_parity_run.py --project-root <root> [--feature F###]
```

- Counts in-scope feature units + total cited LoC, prints a cost/scope estimate (reuses the
  `estimate_artifact_loc.py` shape).
- **Default sweep:** show the estimate and PROMPT the user to proceed (cost guard — this is a heavy
  skill by design). `--feature`/`--path` callers **bypass** the gate entirely.
- Advisory exit 0; the *orchestrator* enforces the gate, not the script (don't-abort-in-Python).

## Step 1 — Discover & scope (Python)

```
scope_doc_units.py    --project-root <root> [--feature F### | --path <doc>]   → doc-units.json
parse_doc_schema.py   --units doc-units.json                                  → doc-schema.json (per unit)
```

- `scope_doc_units.py`: discover behavioral doc units (per `regen-schema-contract.md` § discovery map);
  per unit, parse `**Source:**` citations (`_citation_lib.py`) → assemble code regions = **citation span
  + enclosing function/class** (never whole files). Apply the exclusion skip-list **both directions**
  (legacy group A). Citation absent/unreadable/stale → mark the claim `UNVERIFIABLE` (carried downstream).
  Emits `doc-units.json` (unit id, doc paths, code regions, citation-coverage flag, truncation flags).
- `parse_doc_schema.py`: extract the doc side of the comparable field set into JSON (per artifact, incl.
  output sub-fields). This is the doc half of the diff.

## Step 2 — Blind regenerate (LLM, fan-out)

Per `blind-regen-prompt.md`. One subagent per feature unit, reads ONLY the code regions from
`doc-units.json` — NEVER the doc. Emits regen-schema JSON, every behavior cited. Bounded-batch fan-out
(`AUDIT_PARITY_MAX_PARALLEL` / `AUDIT_PARITY_BATCH_SIZE`, default 5).

## Step 3 — Field-level diff (LLM-judged)

For each unit, compare regen JSON ↔ doc-schema JSON per the diff rules in `regen-schema-contract.md`
§ Diff rules. Apply `materiality-filter.md` to the MISSING direction (incl. output-contract field-level
MISSING). Confidence floor: a verdict below `0.5` confidence degrades to UNVERIFIABLE, never asserts
DRIFT/MISSING. Output one verdict record per compared field (schema below).

The diff is **LLM-judged** (it requires semantic equivalence calls — "admin role" ≡ "requires admin"),
NOT a Python string compare. Python only *assembles* the verdicts in step 5.

## Step 4 — Adjudication tie-break (LLM, flagged only)

Per `adjudication-protocol.md`. Every flagged DRIFT/FABRICATED gets one both-sides re-read →
CONFIRM (stands) / REFUTE (→ MATCH) / DEGRADE (→ UNVERIFIABLE). Anchoring is confined here.

## Step 5 — Assemble report (Python)

```
assemble_parity_report.py --verdicts verdicts.json --out parity-report.md --project-root <root>
```

Consumes the post-adjudication verdict JSON, computes counts + `parity_score` + `result`, renders
`templates/parity-report.md`. Stdlib only, no verdicts of its own — pure assembly.

## Verdict JSON contract (step 3/4 output → step 5 input)

`assemble_parity_report.py` reads exactly this shape:

```json
{
  "project": "myapp",
  "scope": { "mode": "sweep|feature|path", "features": 12, "claims": 240 },
  "findings": [
    {
      "verdict": "MATCH|DRIFT|FABRICATED|MISSING|UNVERIFIABLE",
      "unit": "F012_OrderExport",
      "kind": "FR",
      "field": "auth",
      "doc_location": "docs/features/F012_OrderExport/technical-spec.md:42",
      "doc_says": "endpoint requires admin role",
      "code_reality": "src/api/orders.ts:88-95 — only checks isAuthenticated, no role check",
      "evidence_line": "src/api/orders.ts:90",
      "severity": "critical|warning",
      "confidence": "EXTRACTED:0.9",
      "adjudicated": true
    }
  ]
}
```

- `assemble_parity_report.py` computes: `match/drift/fabricated/missing/unverifiable` = counts by
  `verdict`; `parity_score = match / (match+drift+fabricated)` (0.0 when denominator 0);
  `result = PASS iff drift==0 && fabricated==0`.
- MATCH findings are rolled up one-line in the report body (`✓ unit.field`), like rebuild-spec's
  "Passed Checks". DRIFT/FABRICATED → Critical section; MISSING/UNVERIFIABLE → Warning section.
- A DRIFT/FABRICATED with `adjudicated: false` is a contract violation (Iron Law #3) — the assembler
  logs a warning; such a finding should never reach it.
