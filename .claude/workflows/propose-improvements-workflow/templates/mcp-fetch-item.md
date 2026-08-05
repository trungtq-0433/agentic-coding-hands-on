# {slug}

<!-- Phase A Step K (`--mcp`). One file per fetch task, written by the K-mcp-fetch subagent
     (mcp-manager) as it executes mcp-plan.md. The body is DISTILLED, not raw: clean English
     markdown holding only facts relevant to this task's Goal. NEVER paste the tool's response
     envelope, result-metadata keys, or internal chunk/result identifiers; strip escaped control
     chars (\n). Keep the fixed three-section shape below. Contract: references/knowledge-ingestion.md. -->

**Source:** MCP {server} · call={tool|resource} · args={non-secret keys | none} · fetched={YYYY-MM-DD}

## Facts about the target

<!-- Distilled facts that are about THE TARGET (matches the target-identity descriptor: tech stack +
     product name + distinguishing facts, supplied from scout-report.md — NOT the bare folder name).
     English only. One concise bullet per fact. Write ONLY this task's own facts — there is no
     cross-task dedup (each fetch task runs as an independent parallel agent). -->

- {fact}

## Adjacent / other-subject context (flagged)

<!-- Facts the source returned that describe a DIFFERENT product / codebase / subject than the target
     (per the identity descriptor). File them here with a one-line caveat — NEVER under "Facts about
     the target". Omit the section if empty. -->

- {off-subject fact} — _caveat: describes {other subject}, not the target._

## Confidence & gaps

<!-- Inferred / unverified claims surfaced from the source. Preserve the source's [INFERENCE] /
     [unverified] tags here (do NOT strip them during distillation). Downstream validation treats a
     fact resting on these as WEAK evidence. Note coverage gaps too. "none" if fully grounded. -->

- {inferred/unverified claim} [INFERENCE | unverified]
- gaps: {what this task could not retrieve, or "none"}
