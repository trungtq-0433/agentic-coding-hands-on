# Materiality Filter — `audit-doc-parity`

The code→doc direction (MISSING) is only useful if it reports behavior a human would actually want
documented. Without this filter the report floods with benign noise (private helpers, log lines,
guard clauses) and gets ignored after run 1. This filter is the gate on **every MISSING verdict**.

> Iron Law #5: NEVER emit MISSING for non-documentation-worthy code.
> Iron Law #6: NEVER grade subjective depth — field-level MISSING fires ONLY on provably extractable detail.

## Documentation-worthy (MISSING may fire)

A regenerated behavior is material when it is **observable from outside the unit**:

- **Public routes / endpoints** — any HTTP/GraphQL/gRPC surface a client can call.
- **User-visible rules** — validation, business rules, decision branches that change what the user sees or can do.
- **Data mutations** — create/update/delete of persisted entities (DB writes, state transitions).
- **Auth / permission gates** — role checks, policy guards, ownership checks, feature/experiment gates.
- **External side-effects** — events emitted, webhooks fired, mail/notifications sent, queue jobs enqueued, third-party API calls (incl. their payload shape).
- **Observable output contracts** — see below.

## Suppressed (MISSING must NOT fire)

Internal mechanics with no external observability:

- Private helpers / internal-only functions.
- Guard clauses, null checks, defensive early-returns.
- Logging / metrics / tracing instrumentation.
- Internal control-flow branches that produce no externally observable difference.
- Anything excluded by `legacy-considerations.md` group A (generated/vendored/tests/<10 LOC/abstract bases).

## Output contracts (field-level MISSING)

This is the answer to *"an export feature must describe the output file."* MISSING also fires at the
**field level**: when a documented operation produces a material output the code *provably builds*,
but the doc under-describes it.

Comparable output sub-fields (each must be **extractable from code** to be flagged):

| Sub-field | Example evidence in code |
|-----------|--------------------------|
| format | `text/csv`, `application/json`, `.xlsx` writer |
| columns / keys | the literal header row / serialized field list |
| encoding | BOM write, `Shift_JIS`, `utf-8` charset header |
| naming pattern | `order_export_{date}.csv`, `Content-Disposition` filename |
| response shape | the serialized response object / status envelope |
| emitted payload | event/webhook body fields |

**Example:** doc says `Output: a file`; code builds a CSV with columns `id,total,status` + UTF-8 BOM +
filename `order_export_{YYYYMMDD}.csv`. → field-level MISSING on `columns`, `encoding`, `naming` (each
EXTRACTED from code). The bare `format: file` is a DRIFT-adjacent under-description, reported as MISSING
sub-fields, never as a subjective "too shallow" grade.

## The hard boundary (Iron Law #6)

Flag under-detail **only** when the missing detail is provably extractable from code. Detail the code
cannot confirm is **out of scope** — never flagged:

- *Why* the user exports (intent / motivation).
- Expected data *volume* or performance characteristics not in code.
- Subjective "is this explained well enough" judgments. (That is exactly the W7a noise this skill replaces.)

If you cannot point at the code line that proves the missing detail, it is not MISSING — at most it is
a human-review note, and v1 does not emit those.
