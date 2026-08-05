# Improvement Aspect — New Features

**Track:** technical · **Aspect:** 12 of 14 · **Slug:** `new-features`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/12-new-features.md`
**Template:** `templates/technical/02-improvement/12-new-features.md`

## Goal
Enumerate net-new technical capabilities the stack can support but has not yet implemented (e.g., webhooks, SSO/SAML, audit log, export/import, public API, SDKs, background jobs, admin CLI, feature-flagging, rate-limiting, multi-region, offline mode, webhook retries, search, analytics dashboard). Each proposal MUST be justified by a concrete stack signal from the discovery snapshot (framework capability, existing module boundary, dependency already present) or by a visible gap. Do NOT restate existing features. Propose 3–8 distinct features when discovery supports them; otherwise emit `Status: clean — no current gap`.

## Use-context overrides
**When `internal`:**
- EXCLUDE: public API, public SDK, marketplace listing, public OAuth app, customer-facing billing webhooks, churn-reduction funnel, public developer portal, consumer self-serve upgrade flows

**When `hybrid`:**
- EXCLUDE: mass-market consumer-tier features (consumer churn-reduction funnel, self-serve credit-card upgrades for individual plans, B2C retention loops)

**When `customer-facing`:** full aspect applies with no restrictions.

Output: 3–8 entries (or single `clean — no current gap` entry) per the Entry format above.
