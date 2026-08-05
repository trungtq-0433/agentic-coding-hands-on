# Retrieval Strategy — Docs-First, Sufficiency-Gated, Level-Tuned

How deep to dig before answering. The default is **fast and cheap**: read the documentation Takumi
already produced, check whether that is enough, and only reach into source code when it is not — or
when the asker raises the level with `--level high`/`--level max`. This mirrors a human expert: check the docs
first, open the code only if needed. The depth dial is a single processing level:
`--level low|medium|high|max` (default `--level medium`).

## Contents
- Processing levels (the depth dial)
- Two stages (fast path → escalation → optional verify)
- Sufficiency self-check (the gate)
- Targeted escalation (not a full scan)
- Fast-path token discipline (budgets)
- Worked examples

## Processing Levels (the depth dial)

One `--level <value>` flag sets how hard the engine works. Default — no flag — is `--level medium`.

| Level | Invocation | What it does | Gate behavior |
|---|---|---|---|
| **Low** | `--level low` | Specs/docs only, never touches source. Answers just the question's core, terse. | **Never escalate** — answer from docs (best-effort if thin) and stop. |
| **Medium** *(default)* | `--level medium` / _(none)_ | Docs-first, plus the **related/adjacent** context around the question, not only the literal ask. | Escalate to **targeted** code search only on hard INSUFFICIENT. |
| **High** | `--level high` | Detailed. Starts from specs, then **reaches into source** and notes explicit code references in the answer. | Always touch source; then **Stage-3 verify** the key claim. |
| **Max** | `--level max` | Detailed + thorough. **Forces multiple sub-agents** searching different angles and a **full codebase scan** to verify every specs-derived claim. | Always fan-out + force-scan verify. |

- **Default is `--level medium`** — it equals the docs-first + sufficiency-gate + targeted-escalation flow
  (the fast common case from #96: answer from docs, fall into source only when docs fall short).
- `--level low` is the cheapest: it trades completeness for speed and never reads code.
- `--level high` and `--level max` are the thorough end; `--level max` is **"thorough, not fast"** — opt-in only.
- **Parse rule:** `--level <value>` is two tokens — the flag plus a value in `low|medium|high|max`.
  Strip both; everything else is the question. No `--level` flag ⇒ `--level medium`. A missing or
  unrecognized value after `--level` also falls back to `medium`.
- **Read-only at every level** — higher levels read *more* code (and, for `--level max`, spawn read-only
  sub-agents); none of them ever edits project files.

## Two Stages

```
                 ┌─ Discover (glob only, no reads) ─ Route ─┐
   question ───▶ │  STAGE 1  Gather scoped docs (grep-first) │
                 └──────────────┬───────────────────────────┘
                                ▼
                     ┌─ Sufficiency self-check ─┐
            SUFFICIENT │                         │ INSUFFICIENT(target)
              ┌────────┘                         └────────┐
              ▼                                           ▼
   Synthesize from docs + cite          STAGE 2  Code search
   (early-exit — cheapest path)         medium: targeted (grep symbol → enclosing block)
   (--level low stops here always)      high:   always, targeted + note refs
                                        max:    full scan + multi-subagent fan-out
                                                    │
                                                    ▼
                                         Synthesize + cite code
                                                    │
                         (--level high / --level max) ▼ STAGE 3
                                         Verify answer against code
```

- **Stage 1 — Fast path.** Discovery is glob-only (already cheap; see
  [`artifact-discovery.md`](./artifact-discovery.md)). Route the question
  ([`question-routing.md`](./question-routing.md)), gather only the selected docs, then run the
  sufficiency check. `--level low` answers from here and never proceeds to Stage 2.
- **Stage 2 — Escalation.** `--level medium`: only when the gate returns INSUFFICIENT (targeted, not a blind
  scan). `--level high`: always, targeted, and note explicit code refs. `--level max`: always, **full scan +
  multiple read-only sub-agents** searching different angles to verify every specs-derived claim.
- **Stage 3 — Verify.** `--level high` / `--level max`: spot-check the key claim(s) against the cited code.

## Sufficiency Self-Check (the gate)

A cheap, **internal reasoning step — no extra file reads**. After Stage 1, ask:

> "Do the gathered docs let me answer THIS question, with citations, at the depth asked?"

Return exactly one:

- **`SUFFICIENT`** → synthesize from docs and stop (early-exit).
- **`INSUFFICIENT(reason, target)`** → escalate; `target` = the concrete symbol / route / file name
  to grep in source.

Heuristics (bias toward SUFFICIENT to protect the speed goal):

| Question shape | Usually |
|---|---|
| What the product does, feature list, architecture, feature detail, improvement proposal — and the docs cover it | **SUFFICIENT** |
| Implementation-level: exact algorithm, precise constant/value, error handling, perf, concurrency, "how *exactly*…" — and docs only describe intent | **INSUFFICIENT** (target = the named symbol/route) |
| Docs layer fully ABSENT for the intent | not this gate — use the absent-layer fallback in `question-routing.md` |

If you cannot decide, prefer **one** targeted grep over answering blind.

**Level override of the gate:** `--level low` ignores INSUFFICIENT (answers from docs anyway, noting the
gap); `--level high` / `--level max` treat every question as escalate-worthy (reach source regardless of the
gate). `--level medium` is the only level that lets the gate decide.

## Targeted Escalation (not a full scan)

On INSUFFICIENT (medium) or always (high):

1. If `graphify-out/graph.json` exists (Knowledge Graph is on by default), load `../../_shared/graphify-code-graph.md` and run
   `graphify explain/query/path/affected` for the `target` symbol, route, or file.
2. `grep` the `target` symbol/route across source only to confirm graph leads or fill graph gaps
   (use `tkm:scan-codebase` only when you need broad discovery, not for a known symbol).
3. Open only the **enclosing block** (function / class / section) of the top matches — not whole
   files. This counters grep's context-loss (a bare matched line omits its surrounding logic).
4. Caps: ≤ 6 matched files, ≤ ~24 KB read in the escalation step.
5. Cite the code files actually read. Graph output may guide the answer, but the `## Sources`
   block must cite docs/source files that were read, not only the graph.

A **full-tree scan happens ONLY under `--level max`** (paired with multi-subagent fan-out) — never on the
`--level low` / `--level medium` / `--level high` paths, which stay targeted.

## Fast-Path Token Discipline (budgets)

Tool-calls and stray file reads dominate cost, so the fast path minimizes reads, not just reorders
them:

- Discovery never reads file contents (glob only).
- Gather reads only router-selected files. **Grep-before-read**: locate the answer span first; for a
  large file (> ~200 lines) read the relevant section, not the whole file.
- Budget cap: fast path reads ≤ 6 files / ≤ ~24 KB before the sufficiency check.
- **Early-exit:** once SUFFICIENT, stop gathering immediately.

These are defaults, not hard limits — exceed them only with a stated reason. `--level max` deliberately
exceeds them (full scan + fan-out); that is its purpose, not a violation.

## Worked Examples

1. **"What does this product do?"** *(default `--level medium`)* → Stage 1 reads `feature-list.md` → gate
   **SUFFICIENT** → answer + adjacent context (e.g. who uses it) + cite. No code read.
2. **"What does this product do? `--level low`"** → Stage 1 reads `feature-list.md` → answer the core list,
   terse, no adjacent context, no code. Cheapest path.
3. **"How exactly are passwords hashed at login?"** *(default `--level medium`)* → Stage 1 reads the auth
   spec → gate **INSUFFICIENT**(target=`login`/hashing) → grep `hash`/`bcrypt` → read the enclosing
   function → "bcrypt, 12 rounds" + cite the code file.
4. **"How is auth structured? `--level high`"** → specs first, then always reach source → answer with
   explicit code references noted → Stage-3 verify the key claim against the cited code.
5. **"Is this feature safe to remove? `--level max`"** → specs + **multiple read-only sub-agents** (route
   refs, data-model refs, background jobs, tests) + full codebase scan → cross-verify every
   specs-derived claim → impact answer with confidence tags + Stage-3 verify.

## Constraints

- **Read-only at every level.** `--level high` and `--level max` read *more* code (and `--level max` spawns read-only
  sub-agents + a full scan); none ever edits it.
- Tag escalated/inferred claims with the [`confidence`](../../confidence/SKILL.md) taxonomy when the
  code evidence is partial (e.g. `[INFERRED:0.6]`).
- This file owns the depth policy; `question-routing.md` and `answer-synthesis.md` link here rather
  than restating it (DRY).
