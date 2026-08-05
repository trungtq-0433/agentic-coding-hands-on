# Source → Target Mapping (Speckit/SDD → Takumi canonical specs)

How migrate-aidd maps GitHub Spec-Kit artifacts onto the Takumi canonical
docs layout (v4): 9 core artifacts + per-feature 4-file set.
**Specs-first, code-as-fallback.**

### v4 output layout (promote targets)

<!-- layout-exempt: output layout — all paths are this skill's own promote targets; mode-aware pointer above -->
> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). In single-lang mode (the common case) the paths below are correct as-is.

```
docs/system/     ← overview.md, permissions.md, glossary.md, business-rules.md, architecture.md
docs/generated/  ← route-list.md, api-map.md, entities.md (data-model), screen-list.md,
                    screen-flow.md, behavior-logic.md, user-stories.md, feature-list.md
docs/flows/      ← {slug}.md (cross-feature flows)
docs/features/   ← {slug}/technical-spec.md, business-context.md, screens.md, edge-cases.md
```

There is NO `docs/specs/` in v4. The 4-file per-feature set replaces the old
single `spec.md` output. The `--docs-specs` arg of `promote_drafts.py` is
deprecated/no-op.

## Speckit source layout

```
<specsRoot>/NNN-feature-name/
  spec.md         # user stories (As a/I want/So that) + functional requirements + acceptance criteria
  plan.md         # technical strategy, architecture, component breakdown
  tasks.md        # ordered task checklist by phase
  data-model.md   # entities / fields / relationships (optional, per-feature)
  contracts/      # API endpoint/interface specs (optional dir)
.specify/memory/constitution.md   # project principles/constraints (or root constitution.md)
quickstart.md     # onboarding — IGNORED for migration
```

## Mapping table

| Takumi artifact | Primary speckit source | Confidence | Code fallback |
|---|---|---|---|
| user-stories | `*/spec.md` user-story sections | HIGH | none (pure spec) |
| feature-list | `*/spec.md` FRs/acceptance + `*/plan.md`,`tasks.md` phases | HIGH | none |
| data-model | `*/data-model.md` (merged across features) | HIGH | field types if missing/ambiguous |
| system-overview | `*/plan.md` + `constitution.md` | MEDIUM | always supplement (plan too high-level) + README |
| architecture.md §Design Rationale | `*/research.md` (P05) | MEDIUM | code: confirm each decision was actually built |
| route-list | `*/contracts/` | MEDIUM | always-on grep when `contracts/` absent/sparse |
| `docs/features/{slug}/contracts/` | `*/contracts/` verbatim copy (P04) | HIGH | n/a (copy-as-is) |  <!-- layout-exempt: mapping table row — docs/features/ is this skill's target -->
| screen-list | spec.md UI mentions | NONE→code | **code-scan required** (speckit is UI-agnostic) |
| screen-flow | spec.md flow hints | NONE→code | **code-scan required** |
| permissions | spec.md/constitution role mentions | NONE→code | **code-scan required** (RBAC/middleware) |
| behavior-logic | spec.md async/job language | NONE→code | **code-scan required** (workers/cron/webhooks) |

Pure-spec derivable: user-stories, feature-list, data-model (core fields).
Spec-primary + code-supplement: system-overview, route-list.
Code-only (no speckit source): screen-list, screen-flow, permissions, behavior-logic.

## Data-model cross-feature merge rule

When N feature folders each carry `data-model.md`:
1. **Union** all entities across features.
2. Same entity name in ≥2 features → **merge fields** (union of all fields).
3. Divergent field type for the same field → annotate inline
   `[CONFLICT: feat-001=int, feat-002=string]`. **Never silently drop** — the
   W7a reviewer resolves conflicts.
4. `MODEL###` codes assigned **globally** after the merge (not per-feature).

## NNN-feature → F### reconciliation rule

F### codes come from the FeatureList (Wave 5, from UserStories) — NOT directly
from `NNN-*` folder names. `_speckit-index.json` (Wave 0') is the reconciliation
hint: every speckit `NNN-feature` SHOULD map to ≥1 F###.

- **Orphan source** (`NNN-*` folder with no covering F###) → **W5.6 critical → halt.**
  Lost coverage; a speckit feature was dropped. Fix before promote.
- **Orphan feature** (F### with no `NNN-*` origin) → **W5.6 warning.** Usually a
  code-only feature surfaced by the fallback scan — acceptable, just flag.

<!-- layout-exempt: F### promote target — docs/features/ is this skill's own W9 target -->
Each reconciled F### produces a **4-file v4 feature set** (Wave 6):
`artifacts/features/{slug}/technical-spec.md`, `business-context.md`,
`screens.md`, `edge-cases.md`. Promoted to `docs/features/{slug}/` by W9.

Mapping persisted via `build_source_to_fcode.py` (Wave 9.5), seeded with speckit
folder names in place of code paths. Slug grammar unchanged — see
`claude/skills/rebuild-spec/references/canonical-fcode-schema.md`.

## Contracts carry-over (P04)

<!-- layout-exempt: contracts carry-over — docs/features/ is this skill's W9 promote target -->
speckit `<specsRoot>/NNN-feature/contracts/` → `docs/features/{slug}/contracts/`

- **Provenance tag:** links in `technical-spec.md` use `[FROM_SPEC: contracts/<filename>]`.
- **Copy semantics:** verbatim (no content mutation); atomic; path-guarded.
  Done at DRAFT stage (`artifacts/features/{slug}/contracts/`); `promote_drafts.py`
  auto-promotes the full feature dir tree including `contracts/`.
- **Unresolved Question required:** every carried-over contract must include
  `- [ ] Verify contract matches real routes — speckit contracts are aspirational`.
- **v2 deferred:** contract diff/sync against live routes. v1 is copy-as-is only.

## research.md → architecture rationale (P05)

<!-- layout-exempt: research.md routing — docs/system/ is this skill's W9 target -->
speckit `<specsRoot>/NNN-feature/research.md` → `docs/system/architecture.md` §Design Rationale

- **Citation format:** `spec://NNN-feature/research.md#Section-Heading`
  (H2 anchors extracted by `speckit_parse_lib.py` → `research_sections` in index).
- **Drift tag:** where code contradicts a research decision → `[SPEC_VS_CODE_DRIFT]` in
  the related feature's Unresolved Questions (not in architecture.md itself).
- **Absent file:** skip gracefully — no fabrication.

## Citation policy

Spec-derived facts cite the spec section (`spec://NNN-feature/spec.md#section`)
or a `specsRoot`-relative path. Code-derived facts cite the source path and are
tagged `[FROM_CODE]`. Validated by `validate_source_citations.py --mode
spec-driven`. See `citation-mode.md`.
