# Verification Checklist: Universal Rules

# Verification Checklist

Consumed by `reviewer` subagent when validating rebuild-spec artifacts.

## How to use

Load this file + target artifact + cross-ref artifacts listed per section.
Output: per-issue list with severity (`critical`/`warning`) and `location.file:line`.
`passed` iff `failed === 0`.

## Validator Pre-Check Protocol

Before applying this checklist to feature specs (FS.5), the reviewer MUST read `plans/<active-plan>/artifacts/validation/fs-validation-summary.json`. The orchestrator injects per-fcode validator state into each FS.5 TaskCreate prompt. The reviewer behaves differently per state:

| Validator status (per fcode) | Reviewer behavior |
|------------------------------|-------------------|
| PASS (no validator issues) | Skip all `rule_id`s listed in `## Deterministic Validator Coverage`; mark them `[deterministic-pass]` in the review report. Focus on semantic depth (BR depth, FR/SC coverage, fabricated citations, cross-ref accuracy, edge case sufficiency). |
| WARN (warnings only) | Same as PASS, but cite warning `rule_id`s under "Validator notes" in the review report. Do not re-check those rules. |
| FAIL (critical present) | This should not occur at review time — orchestrator runs implementer fix cycle BEFORE dispatching FS.5. If FAIL slips through, treat as critical and surface immediately. |
| no summary JSON (legacy plan) | Apply the full checklist (legacy mode). Note `[validator-summary-absent]` in the review report. |

`.pending` marker present in `artifacts/features/{slug}/` → reviewer emits `MISSING` for that fcode (see § Pending Marker Rule below). `MISSING` counts toward the review report's `failed` total.

## Universal rules

Applies to every artifact — do not repeat in per-artifact sections.

| Rule | Severity |
|------|----------|
| Artifact exists and is non-empty | critical |
| No placeholder text (`{PLACEHOLDER}`) | critical |
| Required sections present, in template order | critical |
| Orphaned code: exists in artifact but no F### in FeatureList references it | critical |
| Every reported issue includes `location.file` + `location.line` | critical |
| REG### must always appear as SCR###/REG### in cross-refs (bare REG### invalid) | critical |
| REG### parent SCR### must exist in same ScreenList | critical |
| REG### _NameSlug mandatory (no anonymous regions) | critical |
| REG### must not nest (no REG inside REG) | critical |
| Cross-ref tokenizer: split refs on `,` then on `/`. Left token = SCR### (must exist in ScreenList main index). Right token (if present) = REG### (must exist in the parent screen's Regions subsection). | critical |
| Content-completeness: every documented entity (route, model, screen, behavior-logic entry, permission) must be traceable to actual source code via scout-report.md inventory. Documented item with no verifiable source → critical. If scout-report.md absent → mark N/A, emit [WARN]. | critical |

- Per-feature drafts: each feature dir must contain 4 files (technical-spec.md, business-context.md, screens.md, edge-cases.md) AND no `.pending` marker. Missing any → MISSING verdict; counts toward review-report `failed`.

Counting: `critical` → `failed`; `warning` → `warnings`; `MISSING` (see § Pending Marker Rule) → `missing` (counts toward `failed` for Wave 9 gate).

### Pending Marker Rule

`.pending` is a zero-byte sentinel written by Wave 5 and removed by the FS.1 researcher on successful 4-file write (see `references/canonical-fcode-schema.md § Folder Lifecycle`). When the FS.5 reviewer encounters `.pending` in `artifacts/features/{slug}/`:

| Marker state | spec.md state | Reviewer verdict | Frontmatter slot |
|--------------|---------------|------------------|------------------|
| `.pending` present | absent | `MISSING` | `missing += 1` |
| `.pending` present | present (FS.1 wrote but failed to remove marker) | `MISSING` | `missing += 1` (partial-write signal — researcher must verify or remove marker manually) |
| `.pending` absent | present | normal review | n/a |
| `.pending` absent | absent | critical (folder skeleton without content nor marker — orchestrator bug) | `failed += 1` |

`MISSING` blocks Wave 9 (review report frontmatter `missing > 0` → doc-writer HALT). Recovery: rerun Wave 6 for the affected fcode OR (after manual verification that `spec.md` is complete) remove `.pending` and rerun Wave 7b.

