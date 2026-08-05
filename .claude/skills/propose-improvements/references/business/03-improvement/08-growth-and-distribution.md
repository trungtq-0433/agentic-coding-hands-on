# Improvement Aspect — Growth & Distribution

**Track:** business · **Aspect:** 08 of 11 · **Slug:** `growth-and-distribution`
**Read first:** `references/business/03-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/business/03-improvement/08-growth-and-distribution.md`
**Template:** `templates/business/03-improvement/08-growth-and-distribution.md`

## Goal
Identify gaps in the product's ability to scale into new segments or geographies (multi-tenancy, internationalisation, pricing tier infrastructure, usage metering, admin tooling, capacity planning) AND gaps in differentiating distribution channels (marketplaces, OEM, reseller, host-platform peer coverage).

## Intake gate
Pure third-party integrations (Slack, Notion, Jira, GitHub, etc.) are NOT in scope here — they belong under `01-new-features`. This aspect covers growth-readiness gaps and DIFFERENTIATING distribution channels only (marketplace listings that change CAC, OEM/white-label/co-sell, reseller/agency enablement, missing integration category peers under the single-vendor rule, missing host-platform peers under the host-platform rule).

Emit `Status: opportunity` ONLY when a growth-readiness gap OR one of these distribution moves is evidenced + named in research. Otherwise emit `Status: clean — no growth or distribution gap evidenced` and stop.

## Use-context overrides
**When `internal`:** Drop pricing-tier / usage-metering / billing / entitlement-ladder sub-items entirely. Drop consumer-market distribution, public marketplace listings, and consumer-facing referral programs.

**When `hybrid`:** Drop consumer onboarding funnels and mass-market upgrade prompts. Every entry MUST name the enterprise/partner/self-host audience it targets.

**Single-vendor integration rule:** For any single-vendor integration surfaced by research §6, include missing category peers as distinct deal-expansion items.

**Host-platform product rule:** For any host-platform product identified in discovery §1, enumerate dominant peer host platforms that ≥2 competitors support (per research §2) but this product does NOT.
