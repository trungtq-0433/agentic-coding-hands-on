# Technical Improvement — Directory Contract

**Track:** technical · **Sub-step:** 2 of 3 (fan-out)
**Output directory:** `plans/improvement-proposal/technical/02-improvement/`
**Per-item references:** `references/technical/02-improvement/*.md` (one per aspect)
**Per-item templates:** `templates/technical/02-improvement/*.md`

The orchestrator fans out **one subagent per aspect**; subagents work in parallel with
**runtime-capped concurrency** across the active fan-out phase (combined with business 3.3.*).

This file holds the **shared contract** — Items table, Shared rules, Ownership map. Each
aspect's specific Goal + use-context overrides + intake gate live in the per-aspect file
under `references/technical/02-improvement/<NN>-<slug>.md`. A per-aspect subagent loads its
own aspect file AND this file (for the Shared rules + Ownership map below).

## Items (14 total — one per aspect)

| # | Slug | Reference (subagent prompt) | Output file | Template |
|---|------|------------------------------|-------------|----------|
| 01 | architecture              | `references/technical/02-improvement/01-architecture.md`              | `plans/improvement-proposal/technical/02-improvement/01-architecture.md`              | `templates/technical/02-improvement/01-architecture.md`              |
| 02 | code-quality              | `references/technical/02-improvement/02-code-quality.md`              | `plans/improvement-proposal/technical/02-improvement/02-code-quality.md`              | `templates/technical/02-improvement/02-code-quality.md`              |
| 03 | test-coverage             | `references/technical/02-improvement/03-test-coverage.md`             | `plans/improvement-proposal/technical/02-improvement/03-test-coverage.md`             | `templates/technical/02-improvement/03-test-coverage.md`             |
| 04 | ci-cd                     | `references/technical/02-improvement/04-ci-cd.md`                     | `plans/improvement-proposal/technical/02-improvement/04-ci-cd.md`                     | `templates/technical/02-improvement/04-ci-cd.md`                     |
| 05 | performance               | `references/technical/02-improvement/05-performance.md`               | `plans/improvement-proposal/technical/02-improvement/05-performance.md`               | `templates/technical/02-improvement/05-performance.md`               |
| 06 | security-and-dependencies | `references/technical/02-improvement/06-security-and-dependencies.md` | `plans/improvement-proposal/technical/02-improvement/06-security-and-dependencies.md` | `templates/technical/02-improvement/06-security-and-dependencies.md` |
| 07 | observability             | `references/technical/02-improvement/07-observability.md`             | `plans/improvement-proposal/technical/02-improvement/07-observability.md`             | `templates/technical/02-improvement/07-observability.md`             |
| 08 | docs-and-dx               | `references/technical/02-improvement/08-docs-and-dx.md`               | `plans/improvement-proposal/technical/02-improvement/08-docs-and-dx.md`               | `templates/technical/02-improvement/08-docs-and-dx.md`               |
| 09 | error-handling            | `references/technical/02-improvement/09-error-handling.md`            | `plans/improvement-proposal/technical/02-improvement/09-error-handling.md`            | `templates/technical/02-improvement/09-error-handling.md`            |
| 10 | scalability               | `references/technical/02-improvement/10-scalability.md`               | `plans/improvement-proposal/technical/02-improvement/10-scalability.md`               | `templates/technical/02-improvement/10-scalability.md`               |
| 11 | accessibility             | `references/technical/02-improvement/11-accessibility.md`             | `plans/improvement-proposal/technical/02-improvement/11-accessibility.md`             | `templates/technical/02-improvement/11-accessibility.md`             |
| 12 | new-features              | `references/technical/02-improvement/12-new-features.md`              | `plans/improvement-proposal/technical/02-improvement/12-new-features.md`              | `templates/technical/02-improvement/12-new-features.md`              |
| 13 | ecosystem-parity          | `references/technical/02-improvement/13-ecosystem-parity.md`          | `plans/improvement-proposal/technical/02-improvement/13-ecosystem-parity.md`          | `templates/technical/02-improvement/13-ecosystem-parity.md`          |
| 14 | platform-parity           | `references/technical/02-improvement/14-platform-parity.md`           | `plans/improvement-proposal/technical/02-improvement/14-platform-parity.md`           | `templates/technical/02-improvement/14-platform-parity.md`           |

## Shared rules (apply to every aspect)

### Inputs every aspect subagent receives
- `plans/improvement-proposal/technical/01-discovery/` (DIRECTORY — MUST be non-empty). Read every `*.md` once at the start; treat the union as the discovery snapshot. Do NOT re-scan the repository.
- The aspect's per-item reference file (Goal + use-context overrides + intake gate, if any).
- This file (Shared rules + Ownership map).
- **Aspect-conditional second source.** Aspect 06 (`security-and-dependencies`) consumes `01-discovery/09-source-code-security.md` when present (i.e. `--level high|max` was set) per its per-aspect spec's `## Procedure` and `## INVARIANT`. Other aspects ignore that file.

### Idempotency
Each per-aspect subagent skips when its declared output is non-empty (logs `skip: step-4.2.<NN> (artifact exists)`).
Input directory missing or empty → `BLOCKED: step-4.1 directory missing or empty`.

### Use-context marker
Copy verbatim from line 2 of any `plans/improvement-proposal/technical/01-discovery/*.md` file. Echo as line 2 of the aspect's output. Do NOT re-read `use-context.json`. Do NOT re-classify.

### Single-aspect scope
Each subagent fills exactly one aspect heading and its entries. No prioritization, no cross-aspect ranking, no final recommendation — Step 4.3 (proposal) handles selection.

### Use-context-conditional rules (universal)
In every aspect: drop sub-bullets whose remedy is a monetization, customer-funnel, or public-distribution change when `internal`; drop consumer-funnel sub-bullets when `hybrid`. Additional per-aspect overrides are documented in each aspect's reference file.

### Customer-value signal vocabulary (gated by use-context)
- `customer-facing` → `reliability | speed | cost | compliance | retention | revenue | unblocked roadmap | differentiation`
- `hybrid` → `enterprise deal-size unlock | partner-adoption expansion | self-host packaging | differentiation | compliance | operational efficiency | platform capability | reliability`
- `internal` → `operational efficiency | risk reduction | compliance | employee productivity | platform capability | time-to-market for dependent teams | reliability`

Reject `revenue impact | retention | conversion | churn reduction` for `internal`. Reject `mass-market retention | consumer conversion | consumer churn` for `hybrid`.

### Evidence rules
- Every `Evidence:` MUST quote a concrete item from the discovery snapshot (paraphrasing OK — path/metric/ID must survive).
- NEVER introduce claims not supported by discovery. If a claim requires fresh evidence, write `Status: needs-more-discovery` — do NOT fabricate.
- NEVER quote secret values; cite classes (`API_KEY at .env:12`) only.

### Entry format

Every aspect output uses this shape (repeat per opportunity):

```markdown
- Status: <opportunity | clean — no current gap | needs-more-discovery>
- Category: <aspect-id — MUST match the filename's aspect slug>
- Observation: <1-2 sentences tied directly to the discovery snapshot>
- Evidence: <quote specific bullet(s) from discovery; include path:line, metric, or node ID>
- Potential improvement: <what could be done; 1-3 sentences, technology-consistent with stack>
- Customer-value signal: <categorical tag — vocabulary gated by use-context above>
- Value: <high | medium | low>
- Engineering effort hint: <no | very-low | low | medium | high> — based on stack fit and scope, not guessing
- Risk if untouched: <what breaks, slows, or costs the customer if we do nothing>
```

### Value scoring rubric
- **high** — averts a concrete customer-visible incident (outage, security breach, compliance audit failure, revenue leak), unblocks a roadmap item the customer has publicly committed to, or removes a named production risk (EOL runtime past vendor support, known-bad CVE in a prod path). Customer would prioritize this ahead of feature work.
- **medium** — measurably improves a reliability/speed/cost metric, reduces engineering drag on the team, or closes a dependency-hygiene gap that will bite within 1–2 quarters. Customer would schedule this into the next planning cycle.
- **low** — engineering-taste refactor, polish, or long-horizon modernization with no pressing deadline and no customer-visible signal. Customer would park it in the backlog.

If evidence is weak/thin for the magnitude claim, score one step lower. Never score `high` without a concrete risk or unblocked outcome cited from the discovery snapshot.

### Output format
Each aspect writes to its declared output path. H1: `# Improvement Aspect: <Title> — <project name>`. Line 2: verbatim use-context marker. Followed by entries per the Entry format above. Total length under 200 lines.

## Ownership map

Consult before emitting any item — defer to the owner if the topic is not in your row.
Emit an item ONLY when: (a) it falls within YOUR Goal AND (b) the ownership map assigns its primary topic to your aspect. If both conditions fail, drop it — the rightful owner aspect will pick it up.

| Topic | Owner aspect | Tie-breaker |
|-------|-------------|-------------|
| Module boundaries, coupling, layering, god files | 01-architecture | |
| Readability, types, lint, code duplication, TODOs | 02-code-quality | Dependency cleanup → 06-security; tests → 03-test-coverage |
| Tests of any kind, coverage, test infrastructure | 03-test-coverage | A11y tests still here, not 11-accessibility |
| Pipeline stages, build, deploy gates, release automation | 04-ci-cd | SAST/secret-scan **stage** = 04; SAST **findings** = 06 |
| Caching, N+1 queries, hot-path, latency, bundle | 05-performance | "Cache layer" always 05 (even when framed as scale) |
| Secrets, CVEs, auth/authz, dep hygiene, supply-chain | 06-security-and-dependencies | Unused-dep cleanup = 06; SAST findings = 06 (sourced from `4.1.09` when `--level high|max`); SAST stage = 04 |
| Logs, metrics, traces, alerts, dashboards, SLO | 07-observability | "Log/emit metric/trace" mechanics always 07 (even from error handlers) |
| README, API docs, runbooks, architecture diagrams, DX | 08-docs-and-dx | Documenting a new capability = 08; building it = 12 |
| Error classification, retry, circuit breaker, degradation | 09-error-handling | Logging of errors = 07; circuit-breaker logic = 09; alert when it trips = 07 |
| Statelessness, sharding, queue decoupling, conn pool, multi-region | 10-scalability | Caching always defers to 05 |
| WCAG, keyboard nav, screen-reader, ARIA, contrast | 11-accessibility | Writing tests for a11y features = 03 |
| Net-new technical capabilities (SSO, SDK, webhooks, audit log, public API) | 12-new-features | Documenting the capability = 08 |
| Vendor-category parity (CI, IDE, observability vendor peers) | 13-ecosystem-parity | |
| Client/deployment-platform parity (iOS, Android, web, desktop, SDK) | 14-platform-parity | |
