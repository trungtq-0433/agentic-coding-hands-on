---
name: project-sun-kudos-docs-layout
description: Sun* Kudos (SAA 2025) project — docs/ layout, SDD-off mode, where runbook vs clarifications.md live
metadata:
  type: project
---

Project root: `/home/tran.quang.trung@sun-asterisk.com/Project/agentic-coding-hands-on`. Plan dir:
`plans/260805-1032-sun-kudos-website/` (17 phases, Track A = UI screens, Track B = backend/schema,
chạy song song, không blocks/blockedBy chéo track).

**SDD mode is off for this project** — no `docs/features/`, `docs/system/`, `docs/generated/` layer.
Don't go looking for it; the layered-spec rules in this agent's system prompt don't apply here.

`docs/` currently holds exactly one file: `docs/runbook-su-kien.md` — the official event-day
operations runbook (countdown env vars, Supabase local commands, Secret Box grant RPC). `README.md`
points to it for "Vận hành sự kiện". `docs.maxLoc` for this project = 800 (injected per-session by
the hook, not hardcoded).

`plans/260805-1032-sun-kudos-website/clarifications.md` is the **authoritative sink** for
grill-loop decisions and gap resolutions (per `.claude/rules/momorph/momorph-development.md`).
Implementer subagents for later phases receive it directly as context — it is not something an
end user or event-day operator would open.

See [[feedback-docs-vs-plans-boundary]] for the judgment rule on what moves from a phase file /
clarifications.md into `docs/` vs what stays in `plans/`.
