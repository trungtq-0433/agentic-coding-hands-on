# Improvement Aspect — Customer Support Readiness

**Track:** business · **Aspect:** 11 of 11 · **Slug:** `customer-support-readiness`
**Read first:** `references/business/03-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/business/03-improvement/11-customer-support-readiness.md`
**Template:** `templates/business/03-improvement/11-customer-support-readiness.md`

## Goal
Identify gaps in in-app help, error messages, status page, diagnostics, and self-service support tooling. Poor support readiness increases support costs, delays time-to-resolution, and erodes trust — especially during incidents or onboarding.

## Intake gate
Emit `Status: opportunity` ONLY when:
- The proposed runbook / SOP / playbook ENABLES a specific customer outcome (e.g., self-serve onboarding, first 500ms of a P1 incident, dunning recovery, GDPR DSAR turnaround within SLA).
- The artifact MUST cite the customer-side metric the readiness piece moves (CSAT, time-to-resolution, escalation rate, churn deflection).
- Pure internal process docs / engineering onboarding docs are NOT in scope here — they belong to technical `08-docs-and-dx`.

If unmet → emit `Status: clean — no customer-outcome runbook evidenced` and stop.
