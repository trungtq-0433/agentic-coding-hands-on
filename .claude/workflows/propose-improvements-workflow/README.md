# `propose-improvements-workflow` (dynamic workflow)

A **dynamic workflow** for Claude Code: the sibling `propose-improvements-workflow.js` is a single
self-contained script the workflow runtime executes, calling `agent()` / `parallel()` /
`phase()` to fan out subagents in a fixed control flow. Unlike a skill (which the model
interprets), the orchestration is code — same steps, same order, every run.

It generates a customer-ready improvement proposal for the current repository — **technical**
track always, **business** track when the repo is Spec-Driven (SDD).

## Layout

```
propose-improvements-workflow.js # orchestrator (runs in the workflow sandbox) — sibling of this dir
propose-improvements-workflow/   # everything the orchestrator needs, shipped beside it
├── README.md                    # this file
├── lib/*.mjs                    # deterministic steps as runnable node CLIs
├── references/**                # per-step subagent contracts (what each step must do)
├── templates/**                 # output shapes the subagents must produce
└── __tests__/                   # node --test unit tests for the pure helpers
```

## Design rationale

The workflow sandbox has **no filesystem or module access**, which drives three rules:

1. **The orchestrator is self-contained.** No `import` of sibling files — only the runtime
   globals (`agent`, `parallel`, `phase`, `log`, `args`). All file I/O is delegated to
   subagents or to the `lib/*.mjs` CLIs.
2. **Subagents do the I/O.** `researcher` / `reviewer` / `Explore` agents read the bundled
   `references/**` and `templates/**` contracts by absolute path (resolved once at preflight)
   and write artifacts under the repo's `plans/`.
3. **Deterministic steps are node CLIs.** Pure, testable logic (detection, combine, dedup
   prep, verdict application) lives in `lib/*.mjs`. The orchestrator runs them via
   `node <lib>/<step>.mjs …`; each prints `done:`/`skip:`/`warn:` lines then a `Status:`
   trailer. Their pure cores are exported and unit-tested under `__tests__/`.

The orchestration block is guarded by `typeof agent === 'function'`, so `node --test` can
import the module to test the pure helpers without triggering a real run.

## Pipeline

Phases A–E:

```
scout → discovery → research → improvement → track proposals
      → combine → dedup → validate (one agent per item) → apply → improvement-proposal.md
```

Output: `plans/improvement-proposal/improvement-proposal.md`.

## Invocation

`/tkm:propose-improvements-workflow [prompt] [flags]`

The optional `[prompt]` (any non-flag tokens) biases prioritization only — it never replaces the full investigation.

| Flag | Effect |
|------|--------|
| `--technical-only` | technical track only (skips SDD detection) |
| `--business-only` | business track only (requires an SDD repo, else BLOCKED) |
| `--level <low\|medium\|high\|max>` | processing depth (default `medium`); `high`/`max` add the source-code security discovery + SAST rollup (composes `tkm:audit-security`) |
| `--spec-folder <path>` | force a specs root instead of auto-detecting SDD |
| `--mcp <server>` | ingest external MCP-server knowledge in Phase A (Step K) |
| `--kb <path\|url>` | ingest external knowledge-base content (local path or http(s) URL) in Phase A (Step K) |
| `--force` | wipe `plans/improvement-proposal/` **and** `plans/external-knowledge/`, regenerate from scratch |

`--technical-only` + `--business-only` together are refused (BLOCKED).

## External knowledge (`--mcp` / `--kb`)

When `--mcp`/`--kb` is set, Phase A gains **Step K**:

- **`--mcp`** (`mcp-manager` subagents): **K-mcp-plan** discovers the server's capabilities → authors `plans/improvement-proposal/mcp-plan.md`; **K-mcp-fetch** runs one parallel agent per fetch task, each writing one **distilled** file (`templates/mcp-fetch-item.md` — clean English, relevance-gated against a scout-derived target-identity descriptor, no transport scaffolding) to `plans/external-knowledge/mcp/<NN>-<slug>.md`.
- **`--kb`** (one `researcher` subagent): **K-kb-fetch** copies/fetches the source verbatim into `plans/external-knowledge/kb/`.

The fetched `plans/external-knowledge/**` files feed the business + technical discovery fan-outs (via `external_knowledge_dir`); downstream phases inherit them via discovery artifacts, and they are citeable validation Evidence (single tier — no merge step). An unreachable/empty/fetch-failed source → BLOCKED + halt (no fallback). Log line: `knowledge: mcp=<server> kb=<path> → external-knowledge/`. Neither flag → Step K is absent (byte-identical to a no-knowledge run).

## Idempotency & re-runs

Re-runs are gated at the **orchestrator** level, not just inside subagents. At Preflight the
resolver agent inventories every existing non-empty file under `plans/improvement-proposal/`
(after any `--force` wipe) and returns the list; the orchestrator builds a path set and:

- **Fully complete run** — if `improvement-proposal.md` already exists, the workflow
  short-circuits immediately (no agents spawned beyond Preflight).
- **Partial / interrupted run** — each fan-out item (scout, discovery, research, improvement,
  track proposals, validation) is skipped when its artifact is already on disk, so only the
  missing items spawn an agent. The back-half CLIs (`combine` / `dedup` / `phase-d-prep` /
  `apply-verdicts`) self-short-circuit on their own outputs.
- **`--force`** — wipes the tree first, so the inventory is empty and the full pipeline runs.

Because gating is by file **existence**, a re-run will **not** pick up code changes for an
artifact that already exists — pass `--force` to regenerate after the repo changes.

> Known limitation: on a partial resume that regenerates an upstream item, `combine.mjs` skips
> on existence (not content hash), so `combined-initial.md` can stay stale. Use `--force` for a
> guaranteed-fresh proposal. (Tracked as a follow-up.)

## Testing

```bash
cd claude/workflows/propose-improvements-workflow && node --test
```
