# Spec-Parse Strategy (per-artifact researcher contract)

For each Takumi artifact: which speckit paths to READ, which rebuild-spec
template to FILL, the code-fallback grep when specs fall short, and the citation
rule. Researchers read `_session-context.md` FIRST, then the sources below.

**Principle:** old specs are primary evidence; touch code ONLY for the
enumerated gap of each artifact. Cite spec-URI for spec facts, source path
(`[FROM_CODE]`) for code facts.

---

## Spec-derived artifacts (Wave 1' + Wave 4/5)

### system-overview  (MEDIUM — spec-primary + code-supplement)
- Read: `<specsRoot>/*/plan.md`, `constitution.md`, repo `README*`.
- Template: `claude/skills/rebuild-spec/templates/system-overview-template.md`.
- Fallback: plan.md is usually too high-level → ALWAYS supplement with README +
  inferred structure (top-level dirs, manifest). Flag LOW-confidence sections.
- Cite: spec-URI for plan/constitution facts; `[FROM_CODE]` for inferred structure.

### architecture — Design Rationale section  (MEDIUM — research.md → architecture.md, P05)
- Read: all `<specsRoot>/*/research.md` files where `_speckit-index.json` records `has_research: true`.
- Fill: append a **"## Design Decisions / Rationale"** section to `architecture.md`
  (do NOT create a separate artifact — DRY, architecture.md already exists).
- Each decision entry format:
  ```
  ### <Decision title>
  **Why chosen:** <rationale from research.md>
  **Alternatives rejected:** <if documented>
  **Source:** spec://NNN-feature/research.md#Section-Heading
  ```
  Use the H2 anchors from `research_sections` in `_speckit-index.json` to construct
  the spec-URI (replace spaces with `-`).
- Drift rule: cross-check each decision against code-scan facts (route-list, permissions,
  data-model entities). If code **contradicts** the decision:
  - Tag the entry: `[SPEC_VS_CODE_DRIFT]`
  - Add to the **related feature's** `technical-spec.md` Unresolved Questions:
    `- [ ] [SPEC_VS_CODE_DRIFT] <decision summary> — research.md prescribes <X> but code scan found no evidence.`
  - Conservative threshold: only flag when a direct artifact (route, permission, entity)
    is clearly missing; do NOT flag for stylistic/implementation-detail divergence.
- Absent file: if `research.md` is missing for a feature, skip — no fabrication, no placeholder.
- Incomplete code-scan: emit plain rationale entry + soft UQ:
  `- [ ] Verify <decision> is implemented in code (code-scan incomplete at migration time).`
- Cite: `spec://NNN-feature/research.md#section` for research facts; `[FROM_CODE]` for
  code-scan cross-check evidence.

### route-list  (MEDIUM)
- Read: `<specsRoot>/*/contracts/**`.
- Template: `claude/skills/rebuild-spec/templates/route-list-template.md`.
- Fallback (always-on, `contracts/` is rare): grep route declarations —
  `@app.route|@(Get|Post|Put|Delete|Patch)\(|router\.(get|post|put|delete)|->(get|post)\(`.
- Cite: spec-URI for contract endpoints; `[FROM_CODE]` for grepped routes.

### data-model  (HIGH)
- Read: every `<specsRoot>/*/data-model.md`.
- Template: `claude/skills/rebuild-spec/templates/data-model-template.md`.
- Merge: union across features; same entity → merge fields; divergent type →
  `[CONFLICT: ...]`; `MODEL###` assigned globally (see source-target-mapping.md).
- Fallback: only for missing/ambiguous field types → inspect model/migration files.
- Gate: Wave 1.5 DataModel structural gate runs UNCHANGED (schema-only).

### user-stories  (HIGH — pure spec)
- Read: `<specsRoot>/*/spec.md` user-story sections.
- Template: `claude/skills/rebuild-spec/templates/user-stories-template.md`.
- Protocol: `claude/skills/rebuild-spec/references/user-stories-ipe-protocol.md`.
- Fallback: none. Cite: spec-URI only.

### feature-list  (HIGH — pure spec)
- Read: `<specsRoot>/*/spec.md` FRs/acceptance + `*/plan.md`,`tasks.md` phases.
- Template: `claude/skills/rebuild-spec/templates/feature-list-template.md`.
- Emits `_canonical-fcodes.json` + per-feature `.pending` markers (as rebuild-spec).
- Reconcile each F### against `_speckit-index.json` NNN folders (orphan rules).

### feature-spec fan-out  (Wave 6 — per-feature, 4-file v4 model)
- Read: scoped `<specsRoot>/*/spec.md` + UserStories + FeatureList for that F###.
- Templates (4 files per feature, v4):
  - `claude/skills/rebuild-spec/templates/technical-spec-template.md`
  - `claude/skills/rebuild-spec/templates/business-context-template.md`
  - `claude/skills/rebuild-spec/templates/screens-template.md`
  - `claude/skills/rebuild-spec/templates/edge-cases-template.md`
- Output per feature: `artifacts/features/{slug}/technical-spec.md`,
  `business-context.md`, `screens.md`, `edge-cases.md`.
  (NOT a single spec.md — v4 uses 4 audience-split files per feature.
  The pre-v4 single-file template is no longer used.)
- `validate_source_citations.py` validates `technical-spec.md` ONLY
  (`business-context.md`, `screens.md`, `edge-cases.md` are skipped by the
  validator). Every spec-URI citation in `technical-spec.md` must resolve under
  `--specs-root`.

---

## Code-scan fallback artifacts (Wave 2 / 2b / 3)

These have NO speckit source — derived from code, **scoped** by route-list +
data-model + feature folders (seed the scan; if scoping unresolvable, fall back
to full `/tkm:scan-codebase`). Composite-screen H1–H6 + 1-BL-per-file cardinality
apply UNCHANGED (see rebuild-spec references).

| Artifact | Scan scope | Template |
|---|---|---|
| screen-list | frontend/views/components (seeded by route-list) | `screen-list-template.md` |
| screen-flow | router config, navigation, page transitions | `screen-flow-template.md` |
| behavior-logic | workers, cron, webhooks, event handlers (`bl-source-patterns.md`); seed from `_scout-bl-inventory.md` if non-empty | `behavior-logic-template.md` |
| permissions | middleware, RBAC, role config; supplement from spec.md role mentions | `permissions-template.md` |

(templates under `claude/skills/rebuild-spec/templates/`)

### Specs-only repo (no source to scan)
When the working tree has no source code (greenfield speckit), do **best-effort
inference** from explicit spec hints — NOT blanket "No data":
- screen-list / screen-flow ← spec.md UI mentions and flow language
- permissions ← spec.md / constitution role mentions
- behavior-logic ← spec.md async/job/webhook language

Every inferred entry MUST carry `[INFERRED]` + a confidence note and cite the
spec section it came from. **Never invent** entries with no spec basis — an
artifact with zero spec hints emits a "No data — speckit source absent, no code
to scan" marker for that artifact only. The W7a reviewer scrutinizes all
`[INFERRED]` entries. (Validation Session 1 decision.)

### Citation rule (code-scan artifacts)
Code-derived entries cite real source paths tagged `[FROM_CODE]`. Inferred
entries cite the spec section as a spec-URI plus `[INFERRED]`.
