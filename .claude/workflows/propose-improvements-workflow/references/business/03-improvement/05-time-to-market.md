# Improvement Aspect — Time-to-Market

**Track:** business · **Aspect:** 05 of 11 · **Slug:** `time-to-market`
**Read first:** `references/business/03-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/business/03-improvement/05-time-to-market.md`
**Template:** `templates/business/03-improvement/05-time-to-market.md`

## Goal
Identify gaps in release cadence, staging/production parity, feature flag infrastructure, and rollback capability that slow delivery or increase the risk of shipping. Slow TTM allows competitors to capture demand while fixes and features queue up.

## Intake gate
Emit `Status: opportunity` ONLY when ALL of:
- The repo or research artifact names a SPECIFIC released-feature deadline (date, milestone name, or contract clause).
- The blocked work is a process gate (CI duration, release-train cadence, environment promotion delay) — not a feature ask.
- Removing the gate has a quantifiable WAITED-FOR-WHO that closes a deal / prevents missed revenue.

If any of these is missing → emit a single `Status: clean — no concrete TTM gate evidenced` entry and stop.
