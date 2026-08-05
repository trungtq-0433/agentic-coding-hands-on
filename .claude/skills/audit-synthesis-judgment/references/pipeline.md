# Pipeline — `audit-synthesis-judgment`

The full orchestration. The SKILL.md mermaid is the source of truth for the *shape*; this file is
the step detail. All Python via `.claude/skills/.venv/bin/python3 claude/skills/audit-synthesis-judgment/scripts/<script>.py`.

```
estimate-gate → locate → [ engine1 | engine2 | engine3 ] → assemble → frontmatter gate
```

## Step 0 — Estimate & gate (default `--scope all` only)

```
estimate_judgment_run.py --scope all [--plan-dir <p>] [--docs-root <d>]
```
Prints artifacts × engines + the Engine-3 candidate/LLM-call budget. A single `--scope <one>` sets
`bypass_gate: true` and skips the prompt. The orchestrator enforces the gate; the script is advisory.

## Step 1 — Locate

```
locate_synthesis_artifacts.py --scope <s> [--plan-dir <p>] [--docs-root <d>]
```
Resolves the lang-mapped docs root and emits the artifact manifest. **Refuses to guess** an
ambiguous design-intent plan-dir (logs it). Feeds all three engines.

## Step 2 — Run the three engines (parallel-runnable)

### Engine 1 — coverage (the ONLY FAIL source), deterministic
```
coverage_engine.py --scope <s> [--plan-dir <p>] [--strict-coverage] [--stack <name>]
```
graph_preflight (unless `--no-preflight`) → graph-state gate → orphans → phantoms → redundancy →
advisory validator roll-up → findings JSON + LOUD `coverage_status`. See `coverage-contract.md`.

### Engine 2 — boundary conformance, deterministic, WARN-only
```
boundary_conformance.py [--stack <name>] [--user-stories <path>]
```
Parses `user-stories.md`, applies IPE Step-3/Step-4 conformance, emits WARN/UNVERIFIABLE findings +
`boundary_status`. See `boundary-conformance-contract.md`.

### Engine 3 — adversarial judgment, LLM + refutation, WARN-only
Two Python modes wrap the LLM judges:
1. `judgment_engine.py prepare --scope <s> [--plan-dir <p>] --out candidates.json`
   → extracts candidates (inference / naming / restates / granularity), each pinned to a computed anchor.
2. **The orchestrator runs the LLM judges + refuters** per `judgment-rubric.md` +
   `adjudication-protocol.md`, obeying `prompt-injection-defense.md` (scanned prose = inert DATA;
   schema-constrained output). It writes each candidate's `verdict` + `refutations` + `confidence`
   back into the candidates JSON (`judged.json`).
3. `judgment_engine.py assemble --judged judged.json --level <l> --out engine3.json`
   → anchor gate + refutation-survival (≥2-refuter majority default; single-pass at `--level low`) +
   completion accounting (`judgment_status: OK|PARTIAL|FAILED`).

**Fan-out (medium+):** one judge per candidate, `_REFUTERS_PER_CANDIDATE` refuters each, bounded batch.
A dead judge/refuter leaves its candidate unreturned → PARTIAL (never a silent clean).

## Step 3 — Assemble + frontmatter gate

```
assemble_judgment_report.py --coverage e1.json --boundary e2.json --judgment engine3.json \
  --scope <s> --out judgment-report.md
```
Merge → dedupe (key = engine, unit, kind, evidence) → **per-engine anchor gate** (Engine-1 needs
`evidence`, Engine-2 needs a cited `clause`, Engine-3 needs `adjudicated: true`) → render →
frontmatter + the ONE result rule:

```
result = FAIL iff (orphans>0 || phantoms>0 || redundancy>0) || coverage_status == FAIL
```

WARN counts NEVER flip result. `coverage_status` (OK|UNVERIFIABLE|FAIL) is surfaced loudly and
distinct from `result` — a no-graph run is `result: PASS` + `coverage_status: UNVERIFIABLE`, never a
silent verified PASS.

## Emitter-not-gate

The skill emits `judgment-report.md`; the consumer reads `result` + `coverage_status`. It never
mutates docs or code.
