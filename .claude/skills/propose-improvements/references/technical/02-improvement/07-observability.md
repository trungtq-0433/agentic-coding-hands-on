# Improvement Aspect — Observability

**Track:** technical · **Aspect:** 07 of 14 · **Slug:** `observability`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/07-observability.md`
**Template:** `templates/technical/02-improvement/07-observability.md`

## Goal
Enumerate observability improvement opportunities: structured logging, metrics instrumentation, distributed tracing, error reporting, alerting rules, dashboards, on-call tooling, SLO/SLA definition.

## Intake gate
Owns ALL logging, metrics, and tracing infrastructure exclusively. Aspect 09-error-handling MUST NOT emit entries whose primary remedy is adding structured logs, wiring metrics, or plumbing traces. Business aspect 10-analytics-instrumentation MUST NOT emit entries whose primary remedy is operational telemetry (that belongs here). Logging of errors = 07; circuit-breaker logic = 09; alert when it trips = 07.
