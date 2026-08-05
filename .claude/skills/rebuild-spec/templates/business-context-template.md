<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
<!-- FORBIDDEN TOKENS — researcher self-checks regex before writing:
BL\d{3}|SCR\d{3}|REG\d{3}|US\d{3}|ROUTE\d{3}|MODEL\d{3}|PERM\d{3}|FR-\d{3}|BR-\d{3}|SM-\d{3}|ALG-\d{3}|INT-\d{3}|SC-\d{3}|HTTP \d{3}|\bGET|\bPOST|\bPUT|\bDELETE|\bPATCH|\.\w+ ?= ?|[A-Z]{2,4}-\d{3}
Any match outside fenced code blocks = CRITICAL contract violation. Rewrite in plain language.
-->
<!-- LARGE OUTPUT NOTE: if this file exceeds 400 lines, signal to orchestrator for chunked review -->

# Business Context — {F###_NAME}

## Why It Matters

{1–2 sentences on business rationale — user problem solved, product value, or compliance driver.}

{If code provides no signal for rationale, write exactly:
`N/A — inferred from code; domain confirmation needed.`}

{If this feature participates in a cross-feature flow, add:
This feature is part of [{Flow Name}](../../docs/flows/{slug}.md).}

## Who Uses It

{List personas using plain role descriptions — no PERM codes.}

- **{Persona / role}** — {what they do with this feature and why it matters to them}
- **{Persona 2}** — {what they do with this feature and why it matters to them}

## What They Do

{Numbered business workflow steps using business verbs (submits, approves, reviews, selects, receives).
Do NOT use technical verbs (dispatches, queries, hydrates, serializes, mounts, renders).
Each step describes a meaningful action a person takes or a business outcome that occurs.}

1. {Actor} {business verb} {object} — {outcome}
2. {Actor} {business verb} {object} — {outcome}
3. {condition or business rule in plain language} — {what happens}
4. {final business outcome or confirmation}

{Minimum 3 steps for non-trivial features.}

## Unresolved Questions

{Business-side gaps only — domain rules, stakeholder intent, missing rationale.
Write `None.` if no open questions.}

- **{Topic}**: {specific business question that could not be inferred from code}
