<!-- layout-exempt: RE output contract — docs/ paths are rebuild-spec's own output targets -->
# RE Output Contract (Phase C)

When rebuild-spec runs in **reverse-engineering mode** (a profile with `re_contract: true` —
set by `delphi-vcl`/`oracle-plsql` profiles and by the `--legacy` preset), provenance stops being
optional and becomes a first-class output contract. This does NOT rewrite the existing Pending Marker
Rule (`verification-checklist-universal.md`) — it RAISES it from advisory to enforced for RE runs.

## When this contract is active

`re_contract` is resolved from the active profile (`profile.re_contract === true`). It is `false`/absent
for `web-js-ts` and `generic-source` (normal mode — behavior unchanged, no new gate). `--legacy` forces
it `true` (additively — see SKILL.md § `--legacy`). Never active for a plain web run → zero regression.

## The contract (RE mode only)

1. **Every structural claim carries a Source citation.** Each entity, route-less screen, BL item,
   CRUD cell, and DB object MUST cite `file:line` (the existing `**Source:** \`path:line\`` form).
   A structural claim with no citation is a critical violation in RE mode (in normal mode it stays a
   warning, preserving backward-compatibility).
2. **Unverifiable claims are marked, never dropped.** Anything the deterministic extractor could not
   confirm (dynamic SQL, inferred relationship, runtime-resolved target) MUST carry `[UNVERIFIED]`
   (or the localized `未確認` in a `ja` mirror) — never silently asserted as fact and never deleted.
3. **Citation density is measured, not assumed.** The reviewer runs a **citation-density check**
   (`validate_source_citations.py --re-mode`): the fraction of structural claims that carry ≥1
   citation must meet the threshold. Below threshold → `[WARN] citation_density_low` (RE mode only).

## Citation-density threshold

Default **80%** of structural claims must be cited. Configurable via `REBUILD_CITATION_DENSITY_MIN`
(a float 0–1, e.g. `0.8`). The check is advisory (WARN), not a HALT — a legacy codebase legitimately
has un-citable inferred content; the WARN tells the reviewer where to look, it does not block promotion.
In **normal mode the density check does not run at all** (no false positives on web specs).

## Reviewer wiring

The core reviewer (W7a) and the citation validator are extended for RE mode only:
- `validate_source_citations.py` gains `--re-mode` + `--density-min <float>`. Without `--re-mode` its
  behavior is byte-for-byte unchanged (regression-free).
- `pipeline-w7-w9.md` runs the density check with `--re-mode` when `profile.re_contract === true`.

See: `verification-checklist-universal.md` § Pending Marker Rule (the rule this contract enforces),
`structural-extractor-contract.md` (where `[UNVERIFIED]` originates for dynamic SQL).
