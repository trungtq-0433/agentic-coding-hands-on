# Validation Verdict — Per-Item Output Template

<!-- One file per item under `plans/improvement-proposal/validation/item-<NN>-<slug>.md`.
     Written by the per-item validator subagent (Phase D, Step 6 — one subagent per item, runtime-capped concurrency) atomically via
     Bash + tempfile + rename. Consumed by the Step 7 apply subagent at
     the apply step (Phase E) which parses frontmatter `decision:` to
     apply KEEP/REVISE/DROP. -->

## File naming

`plans/improvement-proposal/validation/item-{NN}-{kebab-slug}.md`

- `{NN}` — zero-padded 1-based item index in document order (Technical first, then Business).
- `{kebab-slug}` — lower-case kebab slug derived from the item title.

## File body (REQUIRED structure)

```markdown
---
item_index: {N}
item_slug: {kebab-slug}
track: {technical | business}
decision: {KEEP | REVISE | DROP}
---

# Audits

- **Clause:** (need) {atomic claim from the item's `**Need:**` bullet}
  - **Evidence:** {repo `path:line` that supports the claim, or the grep performed + its negative result}
  - **Verdict:** {correct | wrong}
- **Clause:** (need) {next Need claim}
  - **Evidence:** …
  - **Verdict:** {correct | wrong}
- **Clause:** (solution) {atomic claim from `**Proposed solution:**` — library/dep, file path, API symbol, version pin, pattern, or config key}
  - **Evidence:** {forward-looking stack-fit check against repo `path:line` — lockfile / manifest / repo tree / existing-impl grep / env schema}
  - **Verdict:** {correct | wrong}
- **Clause:** (solution) {next Proposed solution claim}
  - **Evidence:** …
  - **Verdict:** {correct | wrong}

# Reason

{1-3 sentences naming the specific claim(s) that failed or were corrected and the judgment (value rating, use-context, benefits, coherence) behind the decision.}

# Revised item

{Omit this entire `# Revised item` block when decision is KEEP or DROP.
 When decision is REVISE, emit the FULL revised item starting with `## <title>`,
 followed by the five bullets in order: Value, Need, Benefits, Proposed solution, Engineering effort hint.
 `**Category:**` is NOT part of the schema — apply rejects bodies that include it (KEEP fallback).
 Schema MUST be preserved exactly — no extra headings, no extra bullets.}
```

> **How to fill each field** (decompose claims, decide verdicts, choose KEEP/REVISE/DROP, the
> evidence-source ban on `plans/improvement-proposal/**`) lives in `references/validation.md` —
> the validator reads it alongside this template. This file defines only the **output shape**.

## Frontmatter rules

- `item_index` — integer, matches the 1-based position assigned by the orchestrator.
- `item_slug` — kebab-case, must match the `{slug}` in the file name.
- `track` — `technical` or `business` (lower-case).
- `decision` — `KEEP` | `REVISE` | `DROP` (case-insensitive — the apply subagent accepts both `keep` and `KEEP`).

## Audits block rules (output shape only)

These are the **shape** constraints the apply step and human review depend on. For *how* to decompose claims and decide verdicts — the `(need)`/`(solution)` decomposition criteria, the evidence-source ban on `plans/improvement-proposal/**`, and what makes a verdict `correct`/`wrong` — see `references/validation.md` §"What to do" and §"Evidence source rule". The validator reads that file alongside this template; it is not repeated here.

**Scope:** Audits cover the `**Need:**` and `**Proposed solution:**` bullets only. Each `**Clause:**` MUST start with `(need)` or `(solution)`. Other bullets (Value, Benefits, Engineering effort hint) are summarised in `# Reason`, not audited here.

- One audit bullet per atomic claim. Emit all `(need)` bullets first (Need's document order), then all `(solution)` bullets (Proposed solution's document order).
- Each audit bullet has exactly three nested sub-bullets in this order: `**Clause:**`, `**Evidence:**`, `**Verdict:**`.
- `**Clause:**` is prefixed with `(need)` or `(solution)` and preserves every `path:line` / version / ID / metric verbatim so the trail stays grep-able. `**Verdict:**` is exactly `correct` or `wrong`. No prose-only `**Evidence:**`.
- If `**Need:**` is missing/empty: one bullet — `**Clause:** (need) Need bullet absent or empty`, `**Evidence:** schema requires Need bullet; not found in `item_markdown``, `**Verdict:** wrong`. Same for a missing `**Proposed solution:**` under `(solution)`.
- Always emit `# Audits` — even on `DROP`, even when every claim is `correct`.
- `# Audits` is informational — the apply subagent does not parse it; the `decision:` frontmatter is the single source of truth for KEEP/REVISE/DROP. The block exists for human review.

## Decision semantics

The `decision:` value is determined by the validation procedure in `references/validation.md` (§"What to do"), NOT by the audits block alone. This table maps each decision only to its **output requirement** and **apply-subagent effect**:

| decision | `# Revised item` required? | apply-subagent effect |
|----------|----------------------------|------------------------------|
| `KEEP`   | NO  | Item kept as-is in final proposal |
| `REVISE` | YES — full revised item | Item replaced with revised body |
| `DROP`   | NO  | Item removed; `drop:` log line emitted |

## Revise body example

```markdown
---
item_index: 3
item_slug: introduce-edge-rate-limiter
track: technical
decision: REVISE
---

# Audits

- **Clause:** (need) p95 latency 850ms at the `/api/search` route under burst load
  - **Evidence:** `tests/perf/k6-search-2026-04.json:23` records `"p95_ms": 850` for the `/api/search` scenario; CI run reference in `.github/workflows/perf.yml:18`.
  - **Verdict:** correct
- **Clause:** (need) no rate limiter detected in middleware chain
  - **Evidence:** ripgrep on `rate.?limit|throttl|bucket` across `src/api/middleware/` returned 0 hits; `src/api/middleware/index.ts:1-44` registers only auth + logging.
  - **Verdict:** correct
- **Clause:** (need) stale path `src/api/old-middleware.ts:42`
  - **Evidence:** `src/api/old-middleware.ts` does not exist in the current tree (`git ls-files` returns nothing matching); closest live file is `src/api/middleware/index.ts`.
  - **Verdict:** wrong
- **Clause:** (solution) Redis-backed token-bucket rate limiter (introduces `ioredis` or `redis` dep)
  - **Evidence:** `package.json:1-60` declares no redis client dependency; `docker-compose.yml:1-30` declares no redis service; existing cache layer is in-memory `node-cache` (`package.json:42`).
  - **Verdict:** wrong
- **Clause:** (solution) introduce `src/api/middleware/rate-limit.ts`
  - **Evidence:** `src/api/middleware/` exists and accepts new modules per `src/api/middleware/index.ts:1-44` convention (each middleware exports a single Express handler); no name collision (`git ls-files src/api/middleware/rate-limit.ts` empty).
  - **Verdict:** correct

# Reason

Item is coherent; the `(need)` latency claim is evidenced from
`tests/perf/k6-search-2026-04.json:23`, but the `(need)` citation to
`src/api/old-middleware.ts:42` is stale (closest supportable file is
`src/api/middleware/index.ts`). The `(solution)` Redis claim fails its lockfile / infra
check — no redis client or service in the repo — so the proposed solution is rewritten
to use the existing in-memory `node-cache` token-bucket approach instead. The `(solution)`
file-path claim holds. Value rating downgraded `high` → `medium` per the repo's
reliability-only signal (no revenue/incident anchor in the perf fixture or any commit
message).

# Revised item

## Introduce edge rate limiter

- **Value:** medium
- **Need:** p95 latency 850ms at the `/api/search` route under burst load (`tests/perf/k6-search-2026-04.json:23`); no rate limiter detected in middleware chain (`src/api/middleware/index.ts:1-44` registers only auth + logging).
- **Benefits:** Reliability — predictable latency under load; cost — fewer wasted compute cycles serving abusive clients.
- **Proposed solution:** Introduce a `node-cache`-backed token-bucket rate limiter in `src/api/middleware/rate-limit.ts` keyed on IP + route prefix; default 60 req/min/IP, configurable via env (extend `src/config/env.ts`).
- **Engineering effort hint:** medium
```

## Atomic write recipe

The validator MUST write each verdict file atomically via Bash + tempfile + rename. The Write
tool is NOT atomic, and a half-written verdict whose frontmatter parses but body is truncated
would silently mis-apply on the next idempotent run. See `references/validation.md` → "Output
format" for the exact `cat > "$TMP" <<'__PROPOSAL_VERDICT_END__' … mv "$TMP" '<output_path>'`
recipe.
