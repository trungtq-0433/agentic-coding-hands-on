<!-- layout-exempt: rebuild-spec owns all docs/system|components paths — all references here are output targets or internal definitions -->
# Verification Checklist: System Synthesis (--aggregate review stage, SY)
<!-- Created: v17.0.0 — aggregate hybrid artifacts gain a W7a-style reviewer→fix→promote gate -->
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope:** Loaded ONLY by the aggregate (`--aggregate`) review stage — the reviewer that runs
AFTER the system-researcher authors the `*.draft.md` documents (v18.0.0 — authored from a template +
the scout report, no longer Python-built scaffolds) and BEFORE promotion. Do NOT load in the default
(core) W7a run or any per-component pass.

**Reviewed artifacts (the 6 authored drafts):** `overview.draft.md`, `component-catalog.draft.md`,
`architecture.draft.md`, `glossary.draft.md`, `cross-service-flows.draft.md`, `data-ownership-map.draft.md`.
**NOT reviewed (mechanical — pure numbers, disk-verifiable):** `per-component-confidence.md`.

**Cross-refs:** the per-component `_service-digest.json` files (the authoritative source of services,
roles, entities, rpc/topic edges) and each component's `overview.md`. The reviewer reads these +
the filled drafts; it never reads source code.

**Severity → frontmatter:** every critical finding increments `failed:`; every warning increments
`warnings:`. The report carries the standard YAML frontmatter (`failed:`, `warnings:`, `result:`)
so the fix-cycle (mirroring W8) can decrement `failed:` and flip `result: PASS` via
`_review_report_lib.mutate_review_report`. `result: PASS` iff `failed == 0`.

## Semantic review rules (SY-R1..SY-R7)

- [ ] **SY-R1 Human-readable wording:** every filled section reads as full, plain-language sentences
  aimed at a new engineer — active voice, acronyms/terms defined on first use, no raw symbol or ID
  dumps standing in for prose (e.g. a bare list of RPC names is not a Responsibility description).
  A `{{FILL}}` region left as a fragment, a bullet-dump, or untouched marker text → critical.
- [ ] **SY-R2 Factual consistency vs digests:** no service, role, entity, or cross-service edge may be
  asserted that the digests do not support. A narrative claiming an edge absent from the topology, or
  a service not in any digest → critical. Restating a digest fact accurately is required, not optional.
- [ ] **SY-R3 [UNVERIFIED] honesty:** cross-service edges and correlations are heuristic. The filled
  prose must NOT launder an `[UNVERIFIED]` edge into asserted fact — keep the qualifier (or hedge the
  language) wherever the mechanical section marks it `[UNVERIFIED]`. Dropping the qualifier → critical.
- [ ] **SY-R4 Entity-name sanity:** the entity/ownership and catalog tables must contain no doc-section
  headings as entity names ("Entity Relationship Diagram", "Entities", "Summary", "Validation Rules")
  and no duplicate `MODELnnn — X` / `X` variants for one service (Phase 01 filters these upstream; this
  rule is the backstop if a digest predates the filter). Junk/duplicate entity → critical.
- [ ] **SY-R5 No empty-glossary-without-reason:** an empty `glossary.md` is acceptable ONLY when the
  scaffold's "no shared-term candidates detected" branch fired (no cross-service correlation). If
  correlation suggestions exist but the glossary has no defined terms → critical. If the empty state is
  genuine, the reviewer confirms the no-candidates note is present → pass.
- [ ] **SY-R6 Charts authored, coherent, safe (v19):** the researcher now DRAWS the Mermaid (Python no
  longer renders/pins it). `architecture.md` carries the topology (`flowchart LR`) + role-tiered layer
  diagram (`flowchart TB`); `cross-service-flows.md` carries the saga `sequenceDiagram`. Check:
  (a) **every node/edge traces** to a scout-report fact OR a cited component doc — an edge with NO such
  basis (a phantom edge) → **critical** (`SY-R2`); (b) a docs-derived edge is tagged `[UNVERIFIED]` and
  cited → otherwise warning; (c) the Mermaid is **syntactically valid** and node ids/labels are SAFE (no
  unescaped `"`|`` ` ``|`[`|`]`|`<`|`>` that could break out) → an unsafe/invalid chart → **critical**
  (also caught by the mechanical Mermaid lint at promote); (d) a missing chart where edges exist → warning.
  A chart that includes a reused component's docs-derived edges (which the thin digest missed) is the
  CORRECT outcome — do not flag it for diverging from the scout edge list, as long as the extra edges are
  `[UNVERIFIED]` + cited.
- [ ] **SY-R7 Read-first reasoning intact:** when `system/README.md` carries the "which service to read
  first" section, each service's one-line rationale must match its role/fan-in (gateway/entry first,
  reused last). A rationale that contradicts the metadata → warning.
- [ ] **SY-R8 Reused docs read, no blind "unobserved" (v18.0.0):** a component — and WITHOUT EXCEPTION any
  `reused: true` / docs-derived component — may be described as having no cross-service edge ONLY if its
  own docs were read and contain none. Prose that calls a component *"chưa quan sát được" / "not observed"
  / "isolated" / "no confirmed edges"* while the scout report shows that component HAS a docs path (i.e.
  its docs were available to read) → **critical**: the researcher skipped the mandatory read. A relationship
  the component's docs clearly state but the document omits → critical. A docs-derived edge the researcher
  added must carry `[UNVERIFIED]` + a `source: components/<name>/...` citation → otherwise warning.

**Critical edge cases:**
- Any hybrid draft still containing a `{{FILL}}` / `[FILL]` marker after fill → critical (also caught by
  `validate_filled_scaffold`, but the reviewer flags it as unreadable).
- A filled section that introduces a new `## ` H2 not in the scaffold → critical (breaks the promote gate).
- A reused / docs-derived component whose Responsibility cell is empty AND has no `role` fallback → warning.
- Glossary definitions written in raw technical jargon with no plain-language counterpart → warning (SY-R1).
