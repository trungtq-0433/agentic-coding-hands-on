# Architecture Shape — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}

<!-- Derived from the scout report's `## Relevant Files` bullets (distinct top-level
     path prefixes) and any monorepo / multi-stack flags in `## Notes`. Do NOT re-glob —
     the scout `## Relevant Files` list is the canonical file list. -->

- **Repo shape:** {monorepo | single package} — {workspaces / lerna / turborepo / nx / single}
- **Layering:** {`app/` | `lib/` | `pkg/` | `services/` | …} (cite distinct top-level prefixes from scout `## Relevant Files`)
- **Module / package inventory:**
  - `{module-path}` — {one-line purpose}
  - `{module-path}` — {one-line purpose}
- **Architecture signals (from `Grep` against the scout `## Relevant Files` bullets):**
  - {signal: candidate "god files" >200 LOC + ≥10 inbound imports}: `{path:line}` ({inbound count})
  - {signal: cross-module reference hot-spots}: `{path:line}`
  - {signal: entry points}: `{path:line}`

<!-- Total length under 150 lines. Snapshot only — no narration. -->
