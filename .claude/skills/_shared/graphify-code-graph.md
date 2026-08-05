# Graphify Code Graph

Shared rule for consuming an existing Graphify graph. This file is for discovery,
impact, tracing, and verification scope. It does not own graph creation.

## Activation

Use this rule when ALL are true:

- The task needs source-code discovery, impact analysis, root-cause tracing, security
  threat tracing, affected-test selection, or source-backed spec/testcase context.
- Graphify is enabled — it is **ON by default**; disabled only via `tkm graphify off`
  / config `graphify.enabled=false` (`.takumi.json` or `.tkm.json`) or env
  `GRAPHIFY_DISABLE=1` / `REBUILD_NO_GRAPH=1`.
- `graphify-out/graph.json` exists.

If graphify is disabled, or the graph is absent, unreadable, stale, or `graphify` is
unavailable, continue with the skill's normal grep/glob/scan workflow. Never block the
task on graph availability.

## Graph Shape

`graphify-out/graph.json` is NetworkX node-link JSON:

- Top-level: `nodes`, `links` or `edges`, optional `hyperedges`, `built_at_commit`.
- Node fields commonly include `id`, `label`, `source_file`, `source_location`,
  `community`, `file_type`, `_origin`.
- Edge fields commonly include `source`, `target`, `relation`, `confidence`,
  `confidence_score`, `source_file`, `source_location`.
- Prefer `EXTRACTED` edges. Treat `INFERRED` as a lead and `AMBIGUOUS` as something
  that must be verified in source before use.

`graphify-out/GRAPH_REPORT.md` summarizes corpus size, graph freshness, god nodes,
surprising connections, import cycles, and communities. Read it first for orientation.

## Commands

Run commands from the repository root. Use `--graph graphify-out/graph.json` when cwd is
uncertain.

```bash
graphify query "How does <symbol/feature/route> connect to <area>?" --budget 1500
graphify explain "<symbol-or-file>"
graphify path "<source-symbol>" "<target-symbol>"
graphify affected "<changed-symbol-or-file>" --depth 2
```

Use `query` for broad context, `explain` for a node and neighbors, `path` for explicit
relationship chains, and `affected` for reverse-impact scope.

## Use Rules

1. Use graph output to choose candidate files, symbols, routes, dependencies, tests, and
   reviewers before doing broad text search.
2. Verify important claims by reading source lines, specs, diffs, tests, or logs. Graph is
   a map, not the source of truth for behavior.
3. Keep the user's requested scope authoritative. Treat graph-expanded items as
   `graph-suggested` until source or spec evidence confirms they are in scope.
4. Check freshness when the answer depends on current code: compare `built_at_commit` or
   the `GRAPH_REPORT.md` freshness note with `git rev-parse HEAD`. A stale graph may guide
   search but must not be the only evidence.
5. Do not run `graphify update`, install Graphify, or edit graph files unless the current
   skill explicitly authorizes graph maintenance or the user asks for it.
6. Watch known gaps: dynamic dispatch, framework magic routes, generated code, runtime
   configuration, DB column detail, external services, and tests may be incomplete. Fall
   back to grep/glob/tool-specific scans for those.

## Freshness Contract

The kit keeps the graph fresh automatically (when graphify is enabled — the default):

- **Code** is refreshed cheaply and often: the `graph-reindex-sync` SessionStart hook runs
  `graphify update .` (code re-extraction, AST-only, **no LLM**) each session, and graphify's
  native git hooks re-index on commit/checkout. So code edges are current every session.
- **Docs** (`.md`, `.mdx`, `.rst`, `.txt`, `.pdf`) need a semantic re-extraction that costs
  LLM — only `rebuild-spec` does that. The SessionStart hook only **nudges** when docs
  changed since `built_at_commit`; it never spends tokens.

So treat code edges as current, but verify doc-derived edges against source when freshness
matters (see Use Rule 4). Disable everything via config `graphify.enabled=false` (CLI /
`.tkm.json`) or env `GRAPHIFY_DISABLE=1` / `REBUILD_NO_GRAPH=1`.

## Skill-Specific Emphasis

| Skill family | Graph use |
|---|---|
| Discovery (`scan-codebase`) | Start from `GRAPH_REPORT.md`, `query`, `explain`, `path`, then grep/read to confirm. |
| Review (`review-code`) | Use `affected` and `path` to select context files; review remains centered on the diff. |
| Debug/fix (`debug-code`, `fix-bug`) | Use graph paths to form hypotheses and trace callers/callees; reproduction and source evidence still decide root cause. |
| Specs/tests (`ask-expert`, `generate-testcases`) | Docs/specs remain behavior authority; graph only clarifies source relationships, implementation evidence, and regression scope. |
| Security/risk (`audit-security`, `predict-risks`) | Trace entrypoint -> auth/middleware -> service -> sink paths; dependency, secret, and static scans still run separately. |
