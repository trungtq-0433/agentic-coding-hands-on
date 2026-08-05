# Artifact Discovery

Run this **first**, before answering any question. It tells you what Takumi-generated evidence
exists in the project so the user never has to know where to look. Discovery is pure-glob and
cheap — no subagent spawn.

## The Four Evidence Layers (+ codebase fallback)

<!-- layout-exempt: evidence table lists docs/ root paths as discovery sentinels (single-lang); mode-aware pointer added at 1a -->
| Layer | Produced by | Where | What it holds |
|---|---|---|---|
| **Specs** | `rebuild-spec` **or** SDD / spec-kit | `docs/` (v4 layered) **or** `specs/` **or** `.specify/` | rebuild-spec v4 layout: `docs/generated/{feature-list,entities,route-list,screen-list,screen-flow,behavior-logic,api-map,user-stories,permissions-matrix}.md`, `docs/system/{overview,architecture,glossary,permissions,business-rules}.md`, `docs/features/{slug}/{technical-spec,business-context,screens,edge-cases}.md`, `docs/flows/{slug}.md`. SDD layout: per-feature folders `specs/NNN-name/` each with `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/`, `diagrams/` |
| **Docs** | `manage-docs` | `docs/*.md` | system-architecture, project-overview-pdr, project-roadmap, code-standards, deployment-guide, design-guidelines, codebase-summary |
| **Improvement Proposals** | `propose-improvements` | `plans/improvement-proposal/` | technical + business proposals, combined proposal |
| **Plans** | `create-plan` | `plans/<active>/`, `plans/*/` | `plan.md`, `phase-*.md`, `research/`, `reports/`, `artifacts/` |
| **Codebase** | _(always present)_ | repo root | source of truth fallback via `tkm:scan-codebase` |

**Canonical paths for the Specs + Docs layers are owned by
[`_shared/docs-canonical-mapping.md`](../../_shared/docs-canonical-mapping.md).** That file is the
single source of truth — read it for the exact topic→path table. Do **not** restate the mapping
here (duplication there is a declared breaking-change surface). Not covered by canonical-mapping:
the Improvement Proposals and Plans rows, and the **SDD / spec-kit Specs layout** (`specs/`, `.specify/`) — that
one is governed by [`propose-improvements/references/sdd-detection.md`](../../propose-improvements/references/sdd-detection.md).

## Discovery Algorithm

1. **Probe each layer** with sentinel globs. Layer is PRESENT if any sentinel matches:

   <!-- layout-exempt: detection sentinel globs use docs/ root (single-lang); mode-aware resolution added at 1a -->
   | Layer | Sentinels (PRESENT if any exists) |
   |---|---|
   | Specs | `docs/system/**/*.md`, `docs/generated/**/*.md`, `docs/features/**/*.md`, `docs/flows/**/*.md`, `specs/**/spec.md`, `specs/**/*.md`, `.specify/**/*` |
   | Docs | `docs/system-architecture.md`, `docs/project-overview-pdr.md`, any `docs/*.md` |
   | Improvement Proposals | `plans/improvement-proposal/**/*proposal*.md`, `plans/improvement-proposal/**/*.md` |
   | Plans | active-plan pointer, else `plans/*/plan.md` |

1a. **Resolve `specsRoot`** (Specs layer can be one of two layouts). Pick the FIRST that exists with
   content, mirroring the kit's SDD detection — see
   [`propose-improvements/references/sdd-detection.md`](../../propose-improvements/references/sdd-detection.md) §
   "`specsRoot` resolution" (single source of truth; do not re-derive the logic):

   <!-- layout-exempt: specsRoot detection — docs/system|generated|features|flows are detection sentinels not write targets; mode-aware pointer added below -->
   1. `specs/` (SDD / spec-kit per-feature folders) → `specsRoot = specs/`
   2. `docs/` (rebuild-spec v4 layered — any of `docs/system/`, `docs/generated/`, `docs/features/`, `docs/flows/` present) → `specsRoot = docs/`
   3. `.specify/` → `specsRoot = .specify/`

   **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). In single-lang mode (the common case) `specsRoot = docs/` and all paths below are unchanged.

   **SDD layout has no `feature-list.md`** — the set of `specs/NNN-*/` folders *is* the feature
   catalog, and each folder's `spec.md` title is the feature name. Map intents accordingly:
   feature list → enumerate folders + read each `spec.md` heading; feature detail →
   `specs/NNN-name/spec.md`; impact → that folder's `data-model.md` + `contracts/` + `tasks.md`.

2. **Resolve the active plan** for the Plans layer: read the active-plan pointer if the project
   tracks one (`plans/.active` or equivalent written by the plan tooling); otherwise pick the
   newest `plans/*/plan.md` — directory names are `YYMMDD-HHMM-slug`, so lexical sort = chronological.

3. **Build the evidence inventory** — a compact table the router (`question-routing.md`) consumes:

   ```
   | Layer    | Present? | Key files found                          | If absent → advise |
   | Specs    | yes      | generated/feature-list.md, entities.md, features/F012…  | —     |
   | Docs     | yes      | system-architecture.md                   | —                  |
   | Improvement Proposals | no | —                               | /tkm:propose-improvements |
   | Plans    | yes      | 260603-0033-…/plan.md                     | —                  |
   | Codebase | yes      | (always)                                 | —                  |
   ```

## Absent-Layer Advisory

When a layer the question needs is ABSENT, the answer still proceeds (best-effort from whatever IS
present, falling back to `tkm:scan-codebase` on the live codebase) and **appends** a one-line
suggestion. Never dead-end, never silently omit. Map:

| Absent layer | Advisory string |
|---|---|
| Specs | `Run /tkm:rebuild-spec for a deeper spec-backed answer.` |
| Docs | `Run /tkm:manage-docs init to generate narrative docs.` |
| Improvement Proposals | `Run /tkm:propose-improvements to generate an improvement proposal.` |
| Plans | `No active plan found — run /tkm:create-plan to capture intent.` |

This mirrors the read-time intent of `docs-canonical-mapping.md` § "Absent-Layer Advisory" but as a
suggestion surfaced to the asker, not a stderr build signal.

## Evidence Inventory Output Contract

Discovery's only output is the inventory table above. The router reads two things from it per layer:
**Present?** (drives routing + degradation) and **Key files found** (the concrete paths to cite).
Discovery never reads file *contents* — it only locates. Content reading happens during the Gather
step, scoped to the files the router selects.

## Constraints

- **Read-only.** Discovery never executes project code and never edits anything.
- **Source of truth is `claude/skills/...`** — discovery operates on the *target project's* tree
  (`docs/`, `plans/`), not on the kit itself.
- Respect the privacy-block hook on any file-read prompt.
