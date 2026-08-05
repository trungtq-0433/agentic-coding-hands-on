<!-- Reference skeleton only — the actual companion is rendered by
     scripts/derive_confidence_report.py (deterministic Python, not this template).
     This file documents the shape for humans; keep it in sync with the script's
     render_companion() when either changes. See references/confidence-report-contract.md. -->

# Confidence Report — {artifact-relative-path}

> **Self-reported citation-coverage stat — NOT a correctness verification.** This report is
> derived deterministically by parsing the artifact's own inline `**Source:** file:line`
> citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does
> NOT verify that citations are accurate or that claims are true. For blind truth verification,
> see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| {short claim text, derived from the artifact's own line} | {enclosing H2 section name} | {file:line, or — for marker-only rows} | {○ or △} |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims — best-effort only, not authoritative.
{One bullet per marker-tagged claim: `- {section}: {claim}`. `_(none — no marker-tagged claims)_`
when there are none.}

## Risk Flags

{One bullet when `claims_total == 0` ("no detectable claims"), or when `confidence_derived < 0.5`
("low citation coverage"). `_(none)_` otherwise.}

<!--
Frontmatter (rendered above the H1 by the script, not shown in this skeleton body):
---
source_artifact: {artifact-relative-path}
claims_total: {int}
claims_with_evidence: {int}
confidence_derived: {claims_with_evidence / claims_total, or null when claims_total == 0}
generated_by: derive_confidence_report.py
---

NO standalone "human reviewer checklist" section (F15) — the Claims ↔ Evidence table is
supporting evidence for the existing verification-checklist / W7a review flow, not a
replacement for it.
-->
