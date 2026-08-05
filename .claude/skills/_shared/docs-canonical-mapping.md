# Docs Canonical Mapping (kit-internal reference)

Single source of truth for which skill owns which doc topic. Loaded by `rebuild-spec`, `takumi`, `manage-docs`, and `doc-writer`. Update this file FIRST when changing layered-doc behavior — drift here counts as a breaking change. **Version bumps are proportionate** (not a reflexive major for every consumer): bump a consumer's **major** only when its own resolved read/write path actually changes; a consumer whose single-lang behavior stays byte-identical and merely gained a layout-rule pointer bumps **minor/patch**; a pure annotation (e.g. a `layout-exempt` comment on a carve-out) needs no bump.

## Layered Model

`docs/` has 5 namespaces: `system/` (curated narratives), `flows/` (AI-drafted cross-feature journeys; user owns post-generation), `features/{slug}/` (4 audience-aware files per feature), `generated/` (raw inventories, free regen), `decisions/` (human-only ADRs). `manage-docs` owns top-level narrative files (`project-roadmap.md`, `code-standards.md`, etc.).

Both machine-generated and human-maintained layers coexist. They MUST NOT contain duplicate authoritative content for the same topic. When two skills both have a claim, the canonical home below wins.

## Canonical Mapping

<!-- layout-exempt: this table IS the canonical path definition; paths below are definitions, not hardcoded consumer assumptions -->
| Topic | Canonical path | Owner skill | Notes |
|---|---|---|---|
| System overview (narrative) | `docs/system/overview.md` | rebuild-spec | Full content; no stub |
| Architecture diagrams | `docs/system/architecture.md` | rebuild-spec | Mermaid + tech stack |
| Glossary | `docs/system/glossary.md` | rebuild-spec | Term:definition |
| Permissions (curated) | `docs/system/permissions.md` | rebuild-spec | Plain-lang curated view |
| Business rules (curated) | `docs/system/business-rules.md` | rebuild-spec | Plain-lang BR draft |
| Flows (cross-feature) | `docs/flows/{slug}.md` | rebuild-spec | AI draft; user may rename |
| Feature tech-spec | `docs/features/{slug}/technical-spec.md` | rebuild-spec | Per feature |
| Feature business-context | `docs/features/{slug}/business-context.md` | rebuild-spec | Per feature |
| Feature screens | `docs/features/{slug}/screens.md` | rebuild-spec | Per feature |
| Feature edge-cases | `docs/features/{slug}/edge-cases.md` | rebuild-spec | Per feature |
| Feature test-cases | `docs/features/{slug}/test-cases.md` | rebuild-spec | Per feature, SIDECAR (opt-in `--test-cases`); UT/IT/UAT derived from the already-cited technical-spec.md/edge-cases.md — NOT in the mandatory 4-tuple, never gates promotion |
| Route inventory (raw) | `docs/generated/route-list.md` | rebuild-spec | Free regen |
| API map | `docs/generated/api-map.md` | rebuild-spec | Routes + bg-jobs |
| API contracts | `docs/generated/api-contracts.md` | rebuild-spec | REST/GraphQL/gRPC request-response contracts (opt-in `--api-contracts`) |
| Permissions matrix (raw) | `docs/generated/permissions-matrix.md` | rebuild-spec | PERM### codes |
| Entities | `docs/generated/entities.md` | rebuild-spec | Renamed data-model |
| User stories | `docs/generated/user-stories.md` | rebuild-spec | US### codes |
| Feature catalog | `docs/generated/feature-list.md` | rebuild-spec | F### inventory |
| Job inventory | `docs/generated/job-list.md` | rebuild-spec | JOB### inventory + per-job detail sections in ONE artifact (opt-in `--jobs`); re-projection of `behavior-logic.md` BL### entries filtered to job types — NO `docs/jobs/` namespace (F13) |
| Design intent (EXPERIMENTAL) | `docs/system/design-intent.md` | rebuild-spec | Cross-cutting architectural rationale ("why built this way"), opt-in `--design-intent`; EXPERIMENTAL/report-only (F11) — v1 writes to the plan dir and stops; promotes here ONLY after explicit user confirmation. See Disambiguation note below vs `business-rules.md`/`architecture.md` |
| ADRs | `docs/decisions/ADR-*.md` | human only | Never regenerated |
| Roadmap | `docs/project-roadmap.md` | manage-docs | Unchanged |
| Code standards | `docs/code-standards.md` | manage-docs | Unchanged |
| Deployment | `docs/deployment-guide.md` | manage-docs | Unchanged |
| System architecture (manage-docs) | `docs/system-architecture.md` | manage-docs | Coexists with `docs/system/architecture.md` — different scope |
| Feature spec DRAFT (pre-promote) | `plans/<plan_dir>/spec/<slug>/*` | takumi | Plan-local; NEVER in docs/ until promote. No `F###`. |
| Feature spec (promoted) | `docs/features/{slug}/*` | rebuild-spec | `status: implemented`; written by takumi promote at implement-start, then rebuild-spec owns. |
| Screen spec DRAFT (pre-promote) | `plans/<plan_dir>/spec/<slug>/screens/*` | takumi | Plan-local; `SCR###` allocated at promote. |
| Screen spec (promoted) | `docs/screens/{SCR###_Name}/spec.md` | rebuild-spec | Written by promote; rebuild-spec `--screen-specs` may regen if sha absent. |
| System-doc DRAFT (pre-promote) | `plans/<plan_dir>/spec/system/<name>.md` | takumi | Plan-local forward-draft (architecture/permissions); opt-in when a task touches architecture/auth. NO `F###`. |
| Docs reading-order index | single-lang `docs/README.md`; per-lang `docs/<primary>/README.md` (+ `docs/<lang>/README.md` mirrors) | rebuild-spec | Reading-order landing; free regen each pass; 2-zone user tail preserved. In per-lang mode there is **no root `docs/README.md`** (v18.0.0 — a purely-generated one is removed, a hand-written one left untouched); the single entry point is `docs/<primary>/README.md`. |
| System Overview deliverable | `docs/<ProjectName>_System_Overview.md` + `.docx` | rebuild-spec | Client-facing synthesis (opt-in `--overview`); re-shapes promoted docs/, never reads source. |
| API Design workbook | `docs/api/<System> - API Design.xlsx` | rebuild-spec | Client-facing Sun* BM-2-901-52 deliverable (opt-in `--api-doc`); distinct from `--api-contracts` markdown. |
| Per-component docs | `docs/<primary>/components/<name>/` (non-en or per-lang) or `docs/components/<name>/` (en single-lang) — SINGLE source of truth; secondary langs at `docs/<L>/components/<name>/` are translate-mirrors (v23.0.0) | rebuild-spec | system-of-systems tier; see ADR-0003 |

(34 rows)

<!-- layout-exempt: maintenance note — names a code constant, not a consumer path assumption -->
**Reading-order index upkeep:** when adding a new generated/system artifact, add it to
`claude/skills/rebuild-spec/scripts/_nav_strings.py` → `READING_ORDER` (on-disk path + `artifact_key`)
and add a matching `artifact_descriptions[key]` line in EACH per-language locale module
(`_nav_strings_en.py` / `_nav_strings_vi.py` / `_nav_strings_ja.py`), or it will be absent from the
`docs/README.md` index. Role reading-paths live in `_nav_strings.py` → `ROLES` (language-independent
number sequences; labels translated per-locale via `role_labels`).

<!-- layout-exempt: prose below defines the canonical path contracts and disambiguation notes — paths are authoritative definitions, not consumer hardcodes -->
**Forward-authored system docs (Capability A):** `docs/system/architecture.md` and
`docs/system/permissions.md` are forward-authorable by `takumi` — drafted in the plan dir (single file,
`status: draft`), promoted at implement-start (single-file § Promote — SYSTEM-DOC: no `F###`, no
feature-list row), then RECONCILED to as-built by the rebuild-spec Core pass. Forward drafts write ONLY
`docs/system/*`, NEVER `docs/generated/*` (code-derived). Rationale → `docs/decisions/ADR-*` (human-owned).

<!-- layout-exempt: forward-draft authoring contract — paths are rule definitions, not consumer assumptions -->
**Draft authoring note:** `takumi` authors drafts ONLY to `plans/<plan_dir>/spec/<slug>/` (+
`plans/<plan_dir>/spec/system/` for system docs) — never to
`docs/features/` or `docs/screens/`. `docs/features/` and `docs/screens/` contain ONLY promoted,
`status: implemented` content owned by `rebuild-spec`. At implement-start, takumi's promote step copies
the plan-dir draft into `docs/` and flips `status: implemented` (see
`claude/skills/rebuild-spec/references/spec-state-registration.md` § Promote). There is no longer an
in-place `draft → implemented` flip or a `docs/.spec-reconcile-pending.json` sentinel — replaced by
`docs/.spec-promote-pending.json`.
See `claude/skills/rebuild-spec/references/spec-authoring-contract.md` for authoring rules.

<!-- layout-exempt: disambiguation note — both paths are definitional (specifying two distinct files that coexist) -->
**Disambiguation:** `docs/system/architecture.md` (rebuild-spec: generated diagrams + tech stack) and `docs/system-architecture.md` (manage-docs: narrative architecture doc) are SEPARATE files with different scopes. They coexist intentionally.

**Disambiguation (design-intent vs business-rules vs architecture, v26.1.0 B5):** `docs/system/design-intent.md` holds ONLY cross-cutting **architectural rationale** — the "why" behind a choice spanning multiple rules/entities/layers, inferred from ADRs/code/docs and EXPERIMENTAL (F11). `docs/system/business-rules.md` owns per-rule As-Is/To-Be behavior; `docs/system/architecture.md` owns structure/stack description. design-intent may CITE either, never re-narrate their content — a paragraph that only restates existing artifact content with no added "why" is a DRY violation the reviewer gates on.

## Language Layout

### Modes

| Mode | When | Docs root for specs |
|------|------|---------------------|
| **single-lang** | No secondary language registered AND no `docs/<primary>/.layout-migrated` sentinel | `docs/` if `primary_lang == en`, else `docs/<primary>/` |
| **per-lang** | A secondary language key exists in `docs/.rebuild-state.json → translations` (any key other than `primary_lang`) OR `docs/<primary>/.layout-migrated` exists | `docs/<primary>/` |

<!-- layout-exempt: clarifying note — defines the resolution rule, not a consumer hardcode -->
**Non-en single-lang:** the bare `docs/` root is reserved for an **en-primary** single-lang repo. A non-en primary in single-lang mode (e.g. `primary_lang: vi`, no translations) resolves to `docs/<primary>/` — `_lang_lib.resolve_docs_root` returns `docs/` only when `lang == primary == en`. The rebuild-state file then lives at `docs/<primary>/.rebuild-state.json` (inside the resolved root), not at `docs/` root.

**Mode signal:** a secondary language is registered in `docs/.rebuild-state.json → translations` (a key other than `primary_lang`) OR the layout sentinel `docs/<primary>/.layout-migrated` exists. Bare `docs/<primary>/` directory existence is NOT a signal — it may simply be a language mirror created by a prior translate pass.

### Resolution Rule (consumers)

<!-- layout-exempt: this section IS the resolution rule definition — paths here are the rule, not consumer assumptions -->
Every skill that reads or writes `docs/system|features|generated|flows|screens|components` MUST resolve the docs root by mode before constructing paths. `system`, `features`, `generated`, `flows`, `screens` are relocated on a per-lang flip via `MOVED_LAYERS` in `migrate_docs_layout.py`; `components` is resolved directly to the lang-namespaced path by `resolve_component_paths` (v23.0.0 single-source model — no flip). `check_layout_paths.py` guards all of these:

- **Single-lang mode** → docs root = `docs/` (zero behavior change from pre-translation behavior).
- **Per-lang mode** → docs root = `docs/<primary>/`; artifact paths become `docs/<primary>/system/`, `docs/<primary>/features/`, `docs/<primary>/screens/`, `docs/<primary>/components/`, etc.

This is the **single source of truth** for the resolution rule. Consumers MUST NOT re-derive or duplicate it — point here instead.

### manage-docs Narrative Carve-out (intentional)

<!-- layout-exempt: carve-out definition — these docs stay at docs/ root in all modes by design -->
The following project-level narrative files are owned by `manage-docs` and stay at `docs/` root in **both** modes, even when `primary_lang ≠ en`:
<!-- layout-exempt: carve-out list items — names here are definitional -->
- `docs/project-roadmap.md`
- `docs/code-standards.md`
- `docs/system-architecture.md`
- `docs/deployment-guide.md`
- Similar project-level docs listed in the `manage-docs` canonical rows above.

**Rationale:** these are project governance artifacts, rarely translated, and referenced by CI/tooling by absolute path. Moving them on a per-lang flip would break non-rebuild-spec consumers. `manage-docs` reads and writes `docs/*.md` root only — this is intentional, not oversight.

## Output Language — Translation Mirrors (v5.1.0)

`docs/<lang>/` directories are 1:1 prose-translated mirrors of the primary language's docs, owned exclusively by `rebuild-spec --lang`. The English skeleton (headings, code tokens, field labels, table headers, fenced code, frontmatter) is byte-identical across ALL languages.

| Aspect | Value |
|--------|-------|
| Primary docs | `docs/` (if `primary_lang=en`, single-lang mode) or `docs/<primary_lang>/` (per-lang mode) |
| Mirror docs | `docs/<lang>/` (one per secondary language) |
| State | `docs/.rebuild-state.json` (root, language-independent) — `primary_lang` + `translations` map |
| Validator | `validate_translation_skeleton.py` enforces skeleton identity |
| Owner | `rebuild-spec` only — manage-docs/doc-writer/takumi remain at their respective roots per the Layout rule above |
| Auto-sync | After any primary pass promotes, mirrors re-translated for changed artifacts (env opt-out: `REBUILD_AUTO_SYNC_TRANSLATIONS=0`) |

<!-- layout-exempt: this line IS the mode-dependency explanation — it defines the rule, not a hardcoded assumption -->
**Docs root is mode-dependent** (see § Language Layout above): in single-lang mode the canonical spec paths are `docs/system/`, `docs/features/`, `docs/components/`, etc.; in per-lang mode they are `docs/<primary>/system/`, `docs/<primary>/features/`, `docs/<primary>/components/`, etc. Mirror paths (`docs/<lang>/`) are only consumed by the `--lang` translate pass.

## Stub Rule

<!-- layout-exempt: stub rule references the removed pre-v4 path and the current canonical definition -->
None — v4.0.0+ promotes full content for all artifacts. The pre-v4 `docs/specs/system-overview.md` redirect stub is removed. `docs/system/overview.md` carries full content.

## Surgical-Edit Rule

When `doc-writer` is invoked via `tkm:takumi` Step 6 (NOT via `rebuild-spec` Wave 9):

<!-- layout-exempt: surgical-edit table defines the path contract; paths are definitions, not hardcoded consumer assumptions -->
| Path | doc-writer surgical-edit? | Notes |
|---|---|---|
| `docs/generated/*` | YES | Raw inventories |
| `docs/system/*` | YES (guardrailed prose) | Curated narratives — forward-authored (Cap. A), reconciled by Core pass |
| `docs/features/*/technical-spec.md` | YES | BR/SM/ALG/INT table edits |
| `docs/features/*/business-context.md` | YES (guardrailed prose) | Patch-within-section; preserve codes+headings |
| `docs/features/*/screens.md` | YES | `## Screen List` table + `## User Journey` |
| `docs/features/*/edge-cases.md` | YES | Edge case table rows |
| `docs/features/*/test-cases.md` | YES | Test-case table rows (SIDECAR — opt-in `--test-cases`) |
| `docs/screens/*/spec.md` | YES (guardrailed prose) | Patch-within-section; UI-layer codes preserved |
| `docs/flows/*` | YES (guardrailed prose) | User owns — SKIP if `doc_lock: user`; else patch-within-section |
| `docs/decisions/*` | NEVER | Human only |

MAY (inventory/table paths): add/remove/edit rows in inventory tables; update counts; copy adjacent-row schema when inserting.
MAY (guardrailed prose paths): patch prose WITHIN an existing section; keep every heading and all 12 code families (FR/BR/SM/ALG/INT/SC/F/US/SCR/REG/BL/PERM) verbatim.
MUST NOT: rewrite section headings, change document structure, edit schema codes, or touch NEVER paths above.
MUST NOT: full-rewrite a prose file; create new per-feature/per-screen dirs; edit a file whose frontmatter has `doc_lock: user`. If new F### detected → advise `Run /tkm:rebuild-spec --features F###`.

Wave 9 promotion (full-content writes) bypasses this rule.

### User-lock marker

A prose file MAY opt out of all auto-editing with frontmatter key `doc_lock: user` (distinct from
`authored_by:` provenance — a `rebuild-spec`/`takumi`-authored file can still be user-locked without
lying about who drafted it). `doc-writer` MUST skip any file carrying `doc_lock: user` and append a
1-line advisory: `ℹ <path> is doc_lock: user — left untouched.` `docs/flows/*` is the canonical <!-- layout-exempt: definitional reference to the user-owned layer path -->
user-owned layer where this matters most.

## Escalation Heuristic

If a single artifact has **more than 3 changed source files** affecting it in one takumi session, `doc-writer` SKIPS the edit and appends a non-blocking advisory to its output:

```
Run /tkm:rebuild-spec --artifact api-map
```

User decides whether to regenerate. Edits to other artifacts in the same session proceed normally.

## Absent-Layer Advisory

When the doc layer that `doc-writer` would surgically edit is **missing** AND the session changed `≥ 2` feature-surface files, `tkm:takumi` Step 6.a and `tkm:manage-docs update` Phase 2.a emit a 2-line `ℹ` advisory on **stderr only**. Two mutually-exclusive layers:

<!-- layout-exempt: advisory condition table; paths here are detection sentinels, not hardcoded consumer write targets -->
| Condition | Advisory points to |
|---|---|
| `! -d docs` AND `TRIGGER_HITS ≥ 2` | `/tkm:manage-docs init` |
| `-d docs` AND no `docs/system/`, `docs/features/`, or `docs/generated/` AND `TRIGGER_HITS ≥ 2` | `/tkm:rebuild-spec` |
| `docs/system/`, `docs/features/`, or `docs/generated/` present | *(no advisory — surgical edit proceeds)* |

**Contract:**

- Stderr only (`1>&2`); does NOT mutate the `doc-writer` prompt; does NOT block flow (fires in `--auto` mode too).
- Mutually exclusive by control flow (`if … elif …`) — `docs/` absent suppresses the specs advisory because subdirs cannot exist without the parent.
- `TRIGGER_HITS` counts session-changed files matching the trigger-pattern set **after** stripping test/mock/fixture paths (`tests/`, `__tests__/`, `mocks/`, `fixtures/`, `*.test.*`, `*.spec.*`). Pure-test sessions stay silent.
- Trigger patterns are an inline mirror of `subagent-patterns.md` → `## Documentation` → Trigger Mapping. Update both when adding patterns.

**Version policy:** adding/removing/relaxing this advisory is **patch** (additive console output, no contract change). The surgical-edit contract above and the canonical mapping table remain the breaking-change surface.

## Version Policy

This file is the contract. Any change to the mapping table, stub rule, surgical-edit rule, or escalation heuristic is **breaking** for the consumers it actually affects. Bumps are **proportionate to the real change** (see the header note): a consumer whose resolved read/write path changes bumps **major**; one that stays byte-identical in single-lang mode and only gained a layout-rule pointer bumps **minor/patch**; a pure `layout-exempt` annotation needs no bump. The `§ Language layout` rule (single-lang `docs/` root vs per-lang `docs/<primary>/`) is the current example: rebuild-spec (resolver + migration) is major; pointer-only consumers are minor.

PR `2026-05-11` bumps:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 2.9.1 | 3.0.0 |
| `takumi` | 2.1.1 | 3.0.0 |
| `manage-docs` | 1.0.0 | 2.0.0 |
| `doc-writer` (agent) | n/a (unversioned) | tagged "v3.0.0+" section |

PR `2026-05-26` bumps:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 3.0.0 | 4.0.0 |
| `takumi` | — | pending consumer update |
| `manage-docs` | — | pending consumer update |
| `doc-writer` (agent) | — | pending consumer update |

NOTE: takumi, manage-docs, and doc-writer version bumps deferred to follow-up PRs. Only rebuild-spec is bumped in this revision.

PR `2026-06-11` bumps (draft-authoring contract addition — mapping table change = major bump for all consumers):

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 5.3.3 | 6.0.0 |
| `takumi` | pending | pending consumer update |
| `manage-docs` | pending | pending consumer update |
| `doc-writer` (agent) | pending | pending consumer update |

PR `2026-06-15` bumps (plan-dir draft + promote-at-implement model — breaking contract change for all
consumers; removes in-place flip & reconcile sentinel):

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 6.0.0 | 7.0.0 |
| `takumi` | 3.1.0 | 4.0.0 |
| `manage-docs` | 2.0.1 | 3.0.0 |
| `doc-writer` (agent) | tagged "v3.0.0+" | tagged "v4.0.0+" |

PR `2026-06-15` patch (promote spec at implement-start for forging disciplines — non-breaking fix):

| Skill / agent | From | To |
|---|---|---|
| `takumi` | 4.0.0 | 4.0.1 |

PR `2026-06-15` bumps (SDD doc-coverage — forward-draft system docs + post-forge gen gate +
guardrailed prose edits; the surgical-edit rule change is breaking for all consumers):

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 7.0.0 | 8.0.0 |
| `takumi` | 4.0.1 | 5.0.0 |
| `manage-docs` | 3.0.1 | 4.0.0 |
| `doc-writer` (agent) | tagged "v4.0.0+" | tagged "v5.0.0+" |

PR `rewrite-takumi-flow-to-SDD` (2026-06-16) ledger catch-up (records actual shipped versions — the route-completeness,
contiguous-IDs, artifact-sharding, and SDD spec-first pipeline / Work-Type gate PRs bumped the
owners without touching this contract; this PR edits the contract surface, so the ledger is brought
current here):

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 8.0.0 | 9.0.1 |
| `takumi` | 5.0.0 | 5.4.1 |

PR `2026-06-24` (reading-order `docs/README.md` index — additive generated file, per-language,
auto-pruned, regen-safe). The change ADDS a generated artifact; it does NOT alter any consumer's
resolved read/write path. Per the proportionate-bump rule this is **minor** for rebuild-spec (the
owner gains a new output) and **no bump** for other consumers (takumi/manage-docs/doc-writer do not
read `docs/README.md`). Working-tree rebuild-spec is at 13.0.0, ahead of the 9.0.1 ledgered above:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 13.0.0 | 13.1.0 |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

PR `2026-06-24` (rebuild-spec `--overview` + `--api-doc` standalone passes — two opt-in client-facing
deliverables: System Overview `.md`+`.docx` and Sun* API Design `.xlsx`). Both ADD output paths
(`docs/<ProjectName>_System_Overview.*`, `docs/api/<System> - API Design.xlsx`); neither alters an
existing consumer's resolved path. Per the proportionate-bump rule this is **minor** for rebuild-spec
(owner gains two new outputs) and **no bump** elsewhere:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 13.1.0 | 13.2.0 |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

PR `2026-06-24` (per-lang aggregate layout — `components/` added to `LANGUAGE_LAYERS`; DOCUMENT-MAP
removed; root README becomes a 3-line pointer in per-lang mode). `components/` is now a first-class
relocatable language layer: rebuild-spec's resolved write path changes (per-lang output moves from
`docs/components/` to `docs/<primary>/components/`). Per the proportionate-bump rule this is **major**
for rebuild-spec (resolved path changes); takumi/manage-docs/doc-writer do NOT read `components/` or
DOCUMENT-MAP → **no bump**:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 14.1.0 | 15.0.0 |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

PR `2026-06-30` (v23.0.0 single-source translate model — per-component docs source path now
lang-resolved via `resolve_component_paths`; derived-view machinery deleted; `components` removed
from the flip path). rebuild-spec resolved write path for non-en repos changes (per-component runs
now write `docs/<primary>/components/` directly — no aggregate-side projection). Per the
proportionate-bump rule this is **major** for rebuild-spec:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 22.0.0 | 23.0.0 |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

PR `2026-07-07` (v26.1.0 — A2 `--jobs` standalone pass, first of 3 Wave-3 sub-releases). ADDS
one output path (`docs/generated/job-list.md`); no existing consumer's resolved path changes.
`docs/jobs/` namespace explicitly DROPPED (F13) — job-list.md is a single artifact under the
already-translation-covered `generated/` namespace. Per the proportionate-bump rule this is
**minor** for rebuild-spec (owner gains one new output) and **no bump** elsewhere:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 26.0.0 | 26.1.0 |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

PR `2026-07-07` (v26.1.0 — B6 `--test-cases` standalone pass, second of 3 Wave-3 sub-releases,
SAME v26.1.0 as the jobs entry above — F14). ADDS one output path per feature
(`docs/features/{slug}/test-cases.md`), SIDECAR (5th file, never joins the mandatory 4-tuple or
the promotion gate); no existing consumer's resolved path changes. Per the proportionate-bump
rule this is **minor** for rebuild-spec (owner gains one new per-feature output) and **no bump**
elsewhere — no separate version bump, folded into the same 26.1.0 already recorded above:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 26.1.0 | 26.1.0 (no change — same Wave-3 release, sub-entry 2/3) |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

PR `2026-07-07` (v26.1.0 — B5 `--design-intent` standalone pass, third of 3 Wave-3 sub-releases,
SAME v26.1.0 as the jobs/test-cases entries above — F14). ADDS one output path
(`docs/system/design-intent.md`), EXPERIMENTAL/report-only (F11) — v1 writes to the plan dir and
promotes here ONLY after explicit user confirmation, no auto-promote path; no existing
consumer's resolved path changes. Per the proportionate-bump rule this is **minor** for
rebuild-spec (owner gains one new, gated output) and **no bump** elsewhere — no separate version
bump, folded into the same 26.1.0 already recorded above:

| Skill / agent | From | To |
|---|---|---|
| `rebuild-spec` | 26.1.0 | 26.1.0 (no change — same Wave-3 release, sub-entry 3/3) |
| `takumi` | — | unchanged |
| `manage-docs` | — | unchanged |
| `doc-writer` (agent) | — | unchanged |

Consumers: link this file from `## References` in each owner's SKILL.md / agent.md. Do NOT duplicate the table — link only.
