<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Spec-Authoring Contract (takumi greenfield — delta from sibling)

**Extends:** [`feature-spec-researcher-contract.md`](feature-spec-researcher-contract.md)
(section ownership matrix, per-file depth rules, forbidden tokens, DEC-###/DISC-###/SM rules)

This file documents ONLY the delta for takumi-authored greenfield specs.
Do NOT duplicate sections already defined in the sibling contract.

---

## Draft Frontmatter Schema

Appears at the top of `technical-spec.md` and screen `spec.md` (other 3 feature files inherit
provenance from the folder; validators only scan `technical-spec.md`).

**Exact keys in order — single-line values only (stdlib `re` parseable, no nested YAML):**

NEW feature (plan-dir draft — `fcode:` OMITTED, allocated at promote):
```yaml
---
status: draft
authored_by: takumi
created: 2026-06-11
lang: en
---
```

EXISTING `implemented` feature being revised (`fcode:` present — reuse its code):
```yaml
---
status: draft
authored_by: takumi
fcode: F042
created: 2026-06-11
lang: en
---
```

Allowed values: `status` = `draft|implemented`; `authored_by` = `takumi|rebuild-spec`;
`fcode` = `^F\d{3}$` — **omit entirely for NEW-feature plan-dir drafts** (allocated at promote);
present only when revising an EXISTING `implemented` feature (reuse its code); `created` = `^\d{4}-\d{2}-\d{2}$`;
`lang` = `^[a-z]{2,3}(-[a-z0-9]{2,8})*$` — the prose language resolved by `spec-stage-procedure.md`
Pre-Step (omitting it is read as `en`). Validators do not reject the key (frontmatter is parsed by
targeted per-key regexes, no whitelist).

When takumi promotes a draft at implement-start, `status` flips to `implemented`, `fcode:` is added if
absent, `authored_by` is unchanged, and `lang:` is preserved. For a greenfield first-promote (no
`docs/.rebuild-state.json` yet), promote seeds `primary_lang` from this `lang:` value — see
[`spec-state-registration.md`](spec-state-registration.md) Step 1. On a NON-greenfield promote where
the draft's `lang:` ≠ the established `primary_lang`, the orchestrator MUST warn and ask the user
whether to proceed — it NEVER silently overwrites `primary_lang`.

---

## Authoring Mode Inputs (OVERRIDES sibling § Mandatory Context Inputs)

In greenfield/takumi mode the researcher reads:

1. Study reports from Stage 1 (researcher output from plan artifacts)
2. `clarifications.md` from the active plan directory — if present
3. MoMorph specs fetched via MCP — when a MoMorph screen URL is present

**The following 5 upstream artifacts are NOT required and MUST NOT block authoring:**
`scout-report.md`, `screen-flow.md`, `user-stories.md`, `permissions-matrix.md`, `business-rules.md`
These are produced by rebuild-spec extraction passes that have not yet run.

**Per-section authoring rules:**

The H2 set + order of `technical-spec.md` is FIXED by the canonical template
(`templates/technical-spec-template.md`) and enforced by `validate_feature_spec.py` at promote:
`## Overview → ## Polymorphic Behavior → ## Cross-Cutting Logic → ## User Stories → ## Key Entities →
## Artifact References → ## Assumptions → ## Source Code References → ## Unresolved Questions`.
A standalone `## Functional Requirements` heading is **deprecated** (validator-critical) — FRs are placed
under each US's `**Requirements fulfilled:**` list OR under `## Cross-Cutting Logic > ### Requirements`
(see parent contract § Placement Rules). Author from intent within that fixed skeleton.

| Section | Source | Rule |
|---|---|---|
| `## Overview` | Study reports + decisions | Author from intent — no source code needed |
| FRs (under US `**Requirements fulfilled:**` / `## Cross-Cutting Logic > ### Requirements`) | Study reports + decisions | Author from intent — NO standalone `## Functional Requirements` heading |
| Screens narrative (`screens.md` — `## Screen List` → `## User Journey`) | Study reports + MoMorph if present | Author from intent; heading is `## Screen List` (NOT "Screen Route Table") |
| `## Cross-Cutting Logic` → SM / ALG / INT subsections | intent only | Skeletal with explicit `TBD (draft)` markers — NEVER fabricate detail |
| `## User Stories (US###)` | intent only | Allocate US### LOCALLY (sequential no-hyphen — US001, US002 …; no upstream user-stories.md) |
| `## Key Entities` | Intended data model from Study reports | Derive from intent; no table.column citations for unwritten code |
| `## Artifact References` | feature-list.md (plan-local) | Heading MANDATORY. Greenfield: the `Feature List` row carries the provisional `F###`; every other row's `Codes Used` is `TBD (draft)` (route-list/entities/etc. not generated yet). NEVER fabricate codes. |
| `## Source Code References` | N/A (code not written yet) | Heading MUST be present; body MUST be empty or prose-only |

NEVER invent `**Source:** path:N-M` citations for code that does not yet exist.
A cited non-existent path is a **warning** while the spec is `status: draft` (authored_by: takumi),
but `citation.file_missing` becomes **critical** once the spec is promoted to `status: implemented` —
a fabricated draft citation will block validation at implement-start. Do not add it.

---

## Greenfield Output Paths

| Output | Path |
|---|---|
| Feature-list (SYSTEM only) | `plans/<plan_dir>/spec/feature-list.md` (plan-local draft — NOT docs/) |
| Feature 4-file set | `plans/<plan_dir>/spec/<slug>/` (plan-local draft — NOT docs/) |
| Screen spec | `plans/<plan_dir>/spec/<slug>/screens/SCR-<name>/spec.md` (plan-local) |
| System doc (architecture/permissions — opt-in, see § Forward-Authored System Docs) | `plans/<plan_dir>/spec/system/<name>.md` (plan-local draft — NOT docs/) |

**`## Source Code References` rule:** heading is ALWAYS present in `technical-spec.md`; body is empty
or contains prose-only notes (e.g. "No source code written yet — see `## User Stories` for planned endpoints").
The `**Source:** path:N-M` pattern MUST NOT appear in any draft spec — the validator only *warns*
(not blocks) on source checks for drafts, but any such citation flips to a critical failure after
promote (`status: implemented`).

---

## Forward-Authored System Docs (architecture + permissions)

SYSTEM-level design IS proper SDD: architecture and the permission model are decided BEFORE code.
So when a feature TOUCHES architecture or auth, Stage 1.5 ALSO forward-drafts the relevant system
narrative — drafted in the plan dir, promoted at implement-start (single-file § Promote — SYSTEM-DOC),
then RECONCILED to as-built by the post-forge Core pass.

- **Forward-authorable set = `docs/system/architecture.md`, `docs/system/permissions.md` ONLY.**
  (`entities` is NOT in scope — per-feature `## Key Entities` already carries data-model intent.)
- **Trigger (reuse, do not reinvent):** the Trigger Mapping in
  `claude/skills/takumi/references/subagent-patterns.md` → `## Documentation` —
  new service/layer/integration/data-store → `architecture.md`; Auth/RBAC/policy/guard/middleware/roles
  → `permissions.md`. A feature touching neither produces NO system draft (opt-in, no noise).
- **Draft frontmatter** (single-file; mirrors the feature draft MINUS `fcode:` — system docs are not features):
  ```yaml
  ---
  status: draft
  authored_by: takumi
  created: <YYYY-MM-DD>
  lang: <spec_lang>
  ---
  ```
- **HARD RULES (non-negotiable):**
  1. Write ONLY the `docs/system/*` narrative homes — **NEVER `docs/generated/*`** (route-list, entities,
     permissions-matrix). Those are code-derived inventories (DRY; the Core pass owns them).
  2. **NEVER fabricate codes** — `PERM###/SCR###/US###/ROUTE###/MODEL###/BL###` MUST be `TBD (draft)`,
     never a guessed/real code (these are machine-allocated, not provisional like feature-list `F###`);
     real codes are assigned at reconcile.
  3. Design **RATIONALE** ("why this architecture / permission model") goes in `docs/decisions/ADR-*.md`
     (human-owned, never regenerated) — NOT the draft. The Core reconcile may overwrite the narrative.

---

## Greenfield Feature-List (SYSTEM decomposition)

When a task is a SYSTEM (more than one user-facing intent), the spec stage first decomposes it into a
`feature-list.md` draft, then fans out one 4-file set per feature. This section is the delta for that
draft; the SINGLE-feature path never produces a feature-list. Orchestration lives in
`spec-stage-procedure.md` Steps 0–0b; this file owns the **format + content rules**.

**Format — reuse the rebuild-spec template verbatim:** `templates/feature-list-template.md`
(the `Code | Name | Type | Language | Workspace | Priority` Feature Hierarchy table + a "Feature
Details" block per `F###`). Do NOT invent a bespoke layout.

**Greenfield deltas (because no code/upstream artifacts exist yet):**

| Template element | Greenfield rule |
|---|---|
| `F###` codes | **PROVISIONAL** `F001..FNNN`, sequential. Real allocation/renumber happens at promote (existing `id_contiguity` machinery). The draft folders are named by slug (no `F###` prefix). |
| Related Screens / User Stories / APIs / Data Models / Background Logic / Permissions | Fill from intent where derivable; otherwise `TBD (draft)`. **NEVER fabricate** `SCR###/US###/ROUTE###/MODEL###/BL###/PERM###` codes for artifacts that do not exist. |
| "Cross-Reference Validation" checklist | Drop the rows that validate against `user-stories.md` / `screen-list.md` / `route-list.md` etc. (those artifacts are not produced in greenfield). Keep only `F### codes are unique`. |
| Workspace / Language columns | Best-effort from the intended stack; `TBD (draft)` if unknown. |

**Quality gate (greenfield subset of W5.6 — `verification-checklist-quality-gates.md` § FeatureList).**
The decomposition is gated before the user confirms it. Reviewer keeps the intent-based checks and
relaxes the cross-artifact ones:
- **Kept:** Check 4 F-code uniqueness (needs only the feature-list itself), Check 5 Single-Intent
  (critical), Check 6 Clear Flow / input→process→output (warning), Check 7 Vague-naming (warning),
  Check 8 Scope-overlap >50% (warning), Check 9 Grouping-coherence (critical).
- **Skipped (not failed):** Checks 1–3 only (US###/SCR### coverage + orphan) — nothing to
  cross-reference yet. Check 4 is NOT skipped despite being in Group A.

Output: `plans/<plan_dir>/spec/feature-list-review.md` with frontmatter `passed: bool, issues: int, warnings: int`.

**Feature-list frontmatter** (single-line, stdlib-`re` parseable, mirrors the per-spec schema):

```yaml
---
status: draft
authored_by: takumi
created: <YYYY-MM-DD>
---
```

No `fcode:` key on the feature-list itself (it indexes many provisional codes). The decomposition
researcher writes ONLY `feature-list.md`; it does NOT touch state files (registration is the
orchestrator's job at promote).

---

## Screen-Spec Authoring

Draft file: `plans/<plan_dir>/spec/<slug>/screens/SCR-<name>/spec.md` (plan-local, no `SCR###`).
Promoted to `docs/screens/SCR###_Name/spec.md` at implement-start (promote allocates the `SCR###`).

Draft frontmatter uses `fcode` of the owning feature (present only for EXISTING-feature updates; omit
for a NEW feature until promote):

```yaml
---
status: draft
authored_by: takumi
fcode: F042
created: 2026-06-11
---
```

**Scope: UI-layer ONLY.** Screen specs MUST NOT contain codes from these namespaces:
`FR-###`, `BR-###`, `SM-###`, `ALG-###`, `INT-###`, `SC-###`. Those codes belong in `technical-spec.md`.

**Format: follow `templates/screen-spec-template.md` headings — greenfield-lite subset.** The canonical
screen-spec template is built for reverse-engineering existing code (Data Inventory / Security Surface /
per-row `**Source:**` citations). In greenfield no code exists yet, so author the subset that is
derivable from design intent and OMIT the source-derived sections (rather than inventing a bespoke
shape). Use the template's **canonical headings verbatim** so promote reconciles cleanly:

| Template section | Greenfield draft |
|---|---|
| `# {SCR###_Name} — Screen Spec` + `**Screen** / **Type** / **Route** / **Generated**` | Author. Draft uses the draft name (`SCR-<name>`, no `SCR###`); `**Type**` = atomic\|composite. |
| `## Purpose` | Author from intent (1 sentence, plain language). |
| `## Screen Layout` + `### Layout Sketch` (ASCII) + `### Layout Regions` (table) | Author from intended layout — region names + ASCII sketch. Omit per-region source citations. |
| `## User Flow` (`### Happy Path` numbered + `### Branches` table) | Author from intent. `Source` column → `TBD (draft)`. |
| `## UI States` (loading / empty / error / saving / success table) | Author from intent. `Source` column → `TBD (draft)`. |
| `## Validation & Error Feedback` (client-side / server-side) | Author form fields + validation + error copy from intent. Endpoints/`**Source:**` → `TBD (draft)`. |
| `## Accessibility` | Author intended a11y posture, or `[NO_A11Y_DETECTED]` if undecided. |
| `## Data Inventory`, `## Conditional Rendering`, `## Component Variants`, `## Security Surface`, `## Source References`, `## Child Routes` | **OMIT in greenfield** (source-derived). Promote/post-forge reconcile adds them from the as-built code. |

Do NOT emit ad-hoc headings (`## Layout & Component Tree`, `## Form Fields`, `## User-Visible Copy`,
`## Constraints`) — those diverge from the canonical template. Fold their content into the canonical
headings above (component tree → `## Screen Layout`; form fields → `## Validation & Error Feedback`;
copy → inline in the relevant state/flow rows).

---

## Minimal-Spec Rule

| Discipline | Output |
|---|---|
| NEW feature (SINGLE) | Full 4-file set in `plans/<plan_dir>/spec/<slug>/`: `technical-spec.md`, `business-context.md`, `screens.md`, `edge-cases.md` |
| NEW SYSTEM (multi-feature) | `feature-list.md` + one full 4-file set per confirmed feature, all under `plans/<plan_dir>/spec/`. See § Greenfield Feature-List. |
| `--fast` discipline | `technical-spec.md` delta only, in the plan dir (single-feature; never decomposes). Advisory note at delivery: unwritten files remain `status: draft` with empty bodies. |
| EXISTING feature (`status: implemented`) | Author the revised draft into the plan dir tied to the existing `F###` (the shipped `docs/` spec is untouched until promote overwrites it). |

---

## Gap-Analysis Return Block

After authoring, the researcher MUST return a `## Gaps for Clarification` block.
The orchestrator (Phase 3) parses the typed fields into `AskUserQuestion` — free-form prose
is NEVER lifted verbatim as a default.

**Strict schema — numbered list, each item with exactly these fields:**

```
## Gaps for Clarification

1. question: Can unauthenticated users access this feature?
   options: [Yes public, No auth required, Role-gated, TBD]
   recommended: No auth required
   category: auth

2. question: Which external service handles payment processing?
   options: [Stripe, PayPal, Internal, TBD]
   recommended: TBD
   category: external-integration
```

**`category` values:** `auth | permissions | scope | external-integration | data-model | ui | copy | other`

Rules:
- `options` must contain 2–4 entries.
- `recommended` must be one of the `options` values exactly.
- No prose paragraphs under gap items — fields only.
- If no gaps exist, write `## Gaps for Clarification\n\n_None._`

---

## State-Registration Handoff

Registration of new F### and SCR### codes into rebuild-spec state files (`docs/.rebuild-state.json`,
`docs/_source-to-fcode.json`, `docs/generated/feature-list.md`, `docs/generated/screen-list.md`,
`_canonical-fcodes.json`) is the **orchestrator's responsibility** — not the researcher's, and it runs
at **PROMOTE time** (implement-start), not at author time.

The researcher writes spec files only, to the plan dir. It MUST NOT touch state files.

See [`spec-state-registration.md`](spec-state-registration.md) for the registration recipe.

---

## Security

Draft specs MUST NOT embed secrets, credentials, or API keys in pseudocode or prose
(inherited from sibling contract).
