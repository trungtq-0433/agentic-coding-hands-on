# Improvement Aspect — Ecosystem Parity

**Track:** technical · **Aspect:** 13 of 14 · **Slug:** `ecosystem-parity`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/13-ecosystem-parity.md`
**Template:** `templates/technical/02-improvement/13-ecosystem-parity.md`

## Goal
For each `single-vendor` entry in the discovery's vendor-category map, enumerate the dominant peer vendors in the same category that the product does NOT yet support. Each missing peer is a distinct opportunity. Use widely recognized market share, not exhaustive lists (target 1–3 peers per category). Do NOT propose peers outside the vendor's category. If the discovery map contains zero `single-vendor` entries, emit `Status: clean — no current gap` and stop.

## Use-context overrides
**When `internal`:**
- SKIP SaaS-only peers requiring external exposure. Do NOT push peer vendors whose adoption would require exposing the product externally.

**When `hybrid`:**
- EXCLUDE SaaS-only peers that do not also offer a self-hosted or on-premises option.

**When `customer-facing`:** full latitude — any dominant peer in the same category is in scope.

`Engineering effort hint` MUST reflect whether the existing integration code is abstracted (adapter pattern → low/medium) or hardcoded per-vendor (→ high). Cite the evidence that informed the effort estimate.
