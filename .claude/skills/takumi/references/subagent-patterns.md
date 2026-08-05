<!-- layout-exempt: takumi references — all docs/system|features|generated|flows paths are takumi's own forward-draft targets, promote targets, or spec-layer detection references -->
# Workshop Delegation

The master craftsman knows which work belongs to which hands.
These are the delegation patterns for each stage of the workshop.

## Task Tool Pattern

```
Task(subagent_type="[type]", prompt="[task description]", description="[brief]")
```

## Study Stage (Research)

```
Task(subagent_type="researcher", prompt="Research [topic]. Report ≤150 lines.", description="Research [topic]")
```
- Run researchers side by side, one per topic
- Hold each report to 150 lines, sources cited

## Scout Stage

```
Task(subagent_type="scout", prompt="Find files related to [feature] in codebase", description="Scout [feature]")
```
- Use `/tkm:scan-codebase ext` (preferred) or `/tkm:scan-codebase` (fallback)

## Feature Decomposition (Stage 1.5a — SYSTEM only)

Spawned FIRST when the task is a SYSTEM (more than one user-facing intent). Decomposes the system into
a `feature-list.md` draft (rebuild-spec format). Does NOT author per-feature specs and does NOT touch
state files. See `spec-stage-procedure.md` Step 0a.

```
Task(
  subagent_type="researcher",
  prompt="""
Decompose this SYSTEM into a feature-list DRAFT. Do NOT author per-feature specs yet.

Contract: claude/skills/rebuild-spec/references/spec-authoring-contract.md § Greenfield Feature-List
Format template: claude/skills/rebuild-spec/templates/feature-list-template.md
Canonical code-token formats: claude/skills/rebuild-spec/references/code-formats.md
  (F###/US###/SCR###/BL###/PERM###/MODEL### = NO hyphen; e.g. F001_Auth, US001_Login. Match the template verbatim.)

Study reports (primary input):
  [paths to Stage 1 researcher reports]

Output (write ONE file, plan-local — NEVER docs/):
  - plans/<plan_dir>/spec/feature-list.md   (status: draft, authored_by: takumi)

Rules:
  - Split by the rebuild-spec criteria: one F### = exactly ONE user-facing intent (Check 5).
  - Codes are PROVISIONAL F001..FNNN, sequential — real allocation happens at promote. No fcode: on the file.
  - Related Screens/User Stories/APIs/Data Models/BL/Permissions: fill from intent or write `TBD (draft)`. NEVER fabricate SCR###/US###/ROUTE###/MODEL### codes.
  - Drop cross-artifact validation rows (no user-stories.md/screen-list.md exists). Keep "F### codes are unique".
  - Return the feature list as a summary (codes, names, one-line intents, priority) for the user-confirmation gate.
""",
  description="Decompose system → feature-list"
)
```

## Feature-List Quality Gate (Stage 1.5a — SYSTEM only)

Spawned after decomposition, before the user-confirmation rest point. Runs the greenfield subset of the
rebuild-spec W5.6 checks. See `spec-stage-procedure.md` Step 0b.

```
Task(
  subagent_type="reviewer",
  prompt="""
Quality-gate this greenfield feature-list draft.

File: plans/<plan_dir>/spec/feature-list.md
Criteria: claude/skills/rebuild-spec/references/verification-checklist-quality-gates.md § FeatureList

Run the GREENFIELD subset:
  - KEEP: Check 4 F-code uniqueness (needs only the feature-list itself), Check 5 Single-Intent (critical),
    Check 6 Clear Flow / input→process→output (warning), Check 7 Vague-naming (warning),
    Check 8 Scope-overlap >50% (warning), Check 9 Grouping-coherence (critical).
  - SKIP (do NOT fail): Checks 1–3 ONLY (US###/SCR### cross-artifact coverage + orphan) — no upstream artifacts exist. Check 4 is NOT skipped despite being in Group A.

Output: plans/<plan_dir>/spec/feature-list-review.md with YAML frontmatter `passed: bool, issues: int, warnings: int`.
On critical fail, list the exact features to merge/split and why.
""",
  description="Quality-gate feature-list"
)
```

## Spec Stage

Spawned in Stage 1.5 after the draft slug + plan-dir target are resolved (NO ID allocation — `F###`
is allocated at promote). For a SYSTEM, **one researcher per confirmed feature** (bounded batch
`REBUILD_FS_BATCH_SIZE`, default 5). Receives the spec-authoring contract and Study reports (plus,
for a SYSTEM, its own feature's row from `feature-list.md`); FILLs the pre-scaffolded feature spec
DRAFT in the plan dir (scaffolder owns structure); returns a strict-schema gap block.

```
Task(
  subagent_type="researcher",
  prompt="""
FILL the pre-scaffolded greenfield feature spec DRAFT using the spec-authoring contract.
(Files already exist with correct frontmatter + H2 skeleton — do NOT recreate frontmatter or reorder H2.
Write content into the pre-existing sections; the scaffolder has already created the file structure.)

Contract (delta): claude/skills/rebuild-spec/references/spec-authoring-contract.md
Parent contract (section ownership, per-file depth rules, placement rules): claude/skills/rebuild-spec/references/feature-spec-researcher-contract.md
Canonical code-token formats (READ FIRST — non-negotiable): claude/skills/rebuild-spec/references/code-formats.md
Per-file FORMAT templates — match each file's H2 structure EXACTLY (greenfield deltas in the contract):
  - technical-spec.md  → claude/skills/rebuild-spec/templates/technical-spec-template.md
  - business-context.md → claude/skills/rebuild-spec/templates/business-context-template.md
  - screens.md          → claude/skills/rebuild-spec/templates/screens-template.md
  - edge-cases.md       → claude/skills/rebuild-spec/templates/edge-cases-template.md
  - screen spec.md      → claude/skills/rebuild-spec/templates/screen-spec-template.md

Slug + target:
  slug: <human slug> (no F### — allocated at promote)
  plan_dir: plans/<plan_dir>
  fcode: OMIT for a new feature (allocated at promote); set only when revising an EXISTING implemented feature (reuse its code)

Language directive (resolved by the orchestrator — spec-stage-procedure.md Pre-Step):
  spec_lang: <resolved code, e.g. en | vi | jp>
  rule: Write all prose in <spec_lang>. Keep ALL headings, code tokens (F###/US###/SCR###/BL###/PERM###/DEC-###/DISC-###/MODEL###), field labels, table-column headers, fenced code blocks, frontmatter, file paths, and status enums in English (canonical skeleton). If spec_lang is "en", write everything in English. [Same skeleton-in-English rule as build_session_context.py generation mode — keep the two in sync.]

Study reports (context — use as primary input):
  [paths to Stage 1 researcher reports]

Output paths (write directly to the plan dir — NEVER docs/):
  - plans/<plan_dir>/spec/<slug>/technical-spec.md   (status: draft, authored_by: takumi, lang: <spec_lang>)
  - plans/<plan_dir>/spec/<slug>/business-context.md
  - plans/<plan_dir>/spec/<slug>/screens.md
  - plans/<plan_dir>/spec/<slug>/edge-cases.md
  - plans/<plan_dir>/spec/<slug>/screens/SCR-<name>/spec.md   (if new screen — UI-layer only, no SCR###)

Rules:
  - Use Study reports as primary context for intent.
  - SYSTEM only — this feature is one of many: read its row in plans/<plan_dir>/spec/feature-list.md
    (provisional F###, intent, related codes) and author ONLY this feature's scope; do not overlap siblings.
  - Author per contract (gap-analysis, frontmatter schema, section depth rules).
  - CODE TOKENS — follow code-formats.md EXACTLY. The numbered prefixes split into two punctuation
    classes; mixing them is the #1 format bug:
      • NO hyphen: F###, US###, SCR###, REG###, BL###, PERM###, MODEL### (e.g. US001_Login — NOT US-001).
      • WITH hyphen: FR-###, BR-###, SM-###, ALG-###, INT-###, DEC-###, DISC-### (e.g. BR-001_Name).
    US### codes you DEFINE locally use the canonical no-hyphen form (US001, US002, …).
  - H2 STRUCTURE — each file MUST match its template's required H2 set and order. Specifically:
      • technical-spec.md: Overview → Polymorphic Behavior → Cross-Cutting Logic → User Stories →
        Key Entities → Artifact References → Assumptions → Source Code References → Unresolved Questions.
        NO standalone `## Functional Requirements` (deprecated — FRs go under each US's
        `**Requirements fulfilled:**` or `## Cross-Cutting Logic > ### Requirements`). `## Artifact
        References` is MANDATORY (greenfield: list Feature List with the provisional F###; other rows
        `TBD (draft)` — see contract).
      • screens.md: `## Screen List` (NOT "Screen Route Table") → `## User Journey`.
      • screen spec.md: follow the greenfield-lite subset of screen-spec-template.md per the contract
        § Screen-Spec Authoring — canonical headings (`## Purpose`, `## Screen Layout` + Layout Sketch +
        Layout Regions, `## User Flow`, `## UI States`, `## Validation & Error Feedback`,
        `## Accessibility`); do NOT invent ad-hoc headings.
  - Record `lang: <spec_lang>` in technical-spec.md frontmatter; write prose per the Language directive above.
  - NEVER invent **Source:** path:N-M citations for code that does not exist yet.
  - Return a ## Gaps for Clarification block in the strict schema (see contract).
  - Do NOT touch state files (_canonical-fcodes.json, .rebuild-state.json, etc.) — orchestrator handles registration.
""",
  description="Fill pre-scaffolded spec draft (<slug>)"
)
```

## Blueprint Stage (Planning)

```
Task(subagent_type="planner", prompt="Create implementation plan based on reports: [reports] and spec draft: [spec_draft path]. Save to [path]", description="Plan [feature]")
```
- Input: researcher and scout reports + the Stage 1.5 spec draft
- Output: `plan.md` + `phase-XX-*.md` files
- **SYSTEM:** the spec draft path is `plans/<plan_dir>/spec/` (contains `feature-list.md` + N feature
  folders). Planner reads `feature-list.md` and decides feature↔phase mapping **1:N** — a large
  feature MAY split across multiple `phase-XX` files; small related features MAY share one phase.
  Each `phase-XX-*.md` carries `feature: F###` (comma-separated if it covers several) using the
  provisional codes. See `workflow-steps.md` Stage 2.

## UI Craft Stage

```
Task(subagent_type="ui-ux-designer", prompt="Implement [feature] UI per ./docs/design-guidelines.md", description="UI [feature]")
```
- For frontend work
- Follow design guidelines

## Tempering Stage (Testing)

```
Task(subagent_type="tester", prompt="Run test suite for plan phase [phase-name]", description="Temper [phase]")
```
- Must achieve 100% pass rate

## Debugging

```
Task(subagent_type="debugger", prompt="Analyze failures: [details]", description="Debug [issue]")
```
- Use when tempering reveals failures
- Provides root cause analysis

## Master's Inspection (Code Review)

```
Task(subagent_type="reviewer", prompt="Review changes for [phase]. Check security, performance, YAGNI/KISS/DRY. Return score (X/10), critical defects, concerns, refinements.", description="Inspect [phase]")
```

## Plan Sync-back (Project Manager)

```
Task(subagent_type="project-manager", prompt="Run full sync-back in [plan-path]: reconcile completed tasks with all phase files, backfill stale completed checkboxes across all phases, update plan.md status/progress, and report unresolved mappings.", description="Sync plan")
```

## Documentation

Canonical doc-writer prompt — used by both `tkm:takumi` Step 6 and `tkm:manage-docs update` Phase 2.

**Assembly rule (orchestrator MUST execute before spawning — no LLM-side conditional parsing):**

```
prompt = BASE_BLOCK
if SPECS_PRESENT > 0 and IMPACT_MAP is non-empty:
    prompt = prompt + "\n\n" + APPENDIX_BLOCK
prompt = prompt.replace("{PLAN_NAME}",     plan_name)
prompt = prompt.replace("{CHANGED_FILES}", changed_files_list)
prompt = prompt.replace("{IMPACT_MAP}",    impact_map_list)   # only present in APPENDIX
Task(subagent_type="doc-writer", prompt=prompt, description="Update docs")
```

`doc-writer` MUST receive a fully-rendered prompt — no `{...}` placeholders, no `BASE_BLOCK`/`APPENDIX_BLOCK` headings, no commentary about which variant was chosen.

### BASE_BLOCK (always included)

```
Update docs for {PLAN_NAME}.

Changed files: {CHANGED_FILES}

General docs to review (update only if relevant):
- README.md
- docs/project-overview-pdr.md
- docs/codebase-summary.md
- docs/code-standards.md
- docs/system-architecture.md
- docs/project-roadmap.md
- docs/deployment-guide.md (optional)
- docs/design-guidelines.md (optional)
```

### APPENDIX_BLOCK (included only when SPECS_PRESENT > 0 and IMPACT_MAP non-empty)

```
Layered docs/ spec artifacts (surgical edits only — DO NOT regenerate):
{IMPACT_MAP}

Rules: add/remove rows in tables; preserve FR/BR/SM/ALG/INT/SC/F/US/SCR/REG/BL/PERM codes; copy adjacent-row schema. If >3 changed source files touch one artifact → SKIP and advise `/tkm:rebuild-spec --artifact NAME`. Never create new feature spec files — advise `/tkm:rebuild-spec --features F###` instead. Do NOT flip `status:` or refresh `screen_spec_shas` here — promote-cleanup (sha refresh, sentinel delete, status flip) is the orchestrator's Stage 6.b duty, not doc-writer's (doc-writer cannot read `plan.md`).

See `claude/skills/_shared/docs-canonical-mapping.md` for canonical homes.
```

### Worked example — Variant A (SPECS_PRESENT == 0)

Inputs: `plan_name = "auth-feature"`, `changed_files = "src/auth/login.ts, src/auth/session.ts"`.

Resulting `prompt` value passed to `Task(...)`:

```
Update docs for auth-feature.

Changed files: src/auth/login.ts, src/auth/session.ts

General docs to review (update only if relevant):
- README.md
- docs/project-overview-pdr.md
- docs/codebase-summary.md
- docs/code-standards.md
- docs/system-architecture.md
- docs/project-roadmap.md
- docs/deployment-guide.md (optional)
- docs/design-guidelines.md (optional)
```

### Worked example — Variant B (SPECS_PRESENT > 0, IMPACT_MAP non-empty)

Inputs: `plan_name = "auth-feature"`, `changed_files = "src/auth/login.ts, src/routes/api.ts"`, `impact_map = "- docs/generated/route-list.md (from src/routes/api.ts)\n- docs/system/permissions.md (from src/auth/login.ts)"`.

Resulting `prompt` value passed to `Task(...)`:

```
Update docs for auth-feature.

Changed files: src/auth/login.ts, src/routes/api.ts

General docs to review (update only if relevant):
- README.md
- docs/project-overview-pdr.md
- docs/codebase-summary.md
- docs/code-standards.md
- docs/system-architecture.md
- docs/project-roadmap.md
- docs/deployment-guide.md (optional)
- docs/design-guidelines.md (optional)

Layered docs/ spec artifacts (surgical edits only — DO NOT regenerate):
- docs/generated/route-list.md (from src/routes/api.ts)
- docs/system/permissions.md (from src/auth/login.ts)

Rules: add/remove rows in tables; preserve FR/BR/SM/ALG/INT/SC/F/US/SCR/REG/BL/PERM codes; copy adjacent-row schema. If >3 changed source files touch one artifact → SKIP and advise `/tkm:rebuild-spec --artifact NAME`. Never create new feature spec files — advise `/tkm:rebuild-spec --features F###` instead. Do NOT flip `status:` or refresh `screen_spec_shas` here — promote-cleanup (sha refresh, sentinel delete, status flip) is the orchestrator's Stage 6.b duty, not doc-writer's (doc-writer cannot read `plan.md`).

See `claude/skills/_shared/docs-canonical-mapping.md` for canonical homes.
```

### Trigger Mapping

`CHANGED_FILES` → affected layered `docs/` artifacts. Orchestrator uses this table to build `IMPACT_MAP` (drop rows where the artifact does not exist on disk). Paths are the v4 canonical homes — see `claude/skills/_shared/docs-canonical-mapping.md`.

| Changed file pattern | Affected artifact(s) |
|---|---|
| Backend route / controller / API handler | `docs/generated/route-list.md` |
| ORM model / migration / schema definition | `docs/generated/entities.md` |
| Frontend page / screen / route component | `docs/generated/screen-list.md`, `docs/generated/screen-flow.md` |
| Navigation / router config | `docs/generated/screen-flow.md` |
| Auth / RBAC / policy / guard / middleware / roles | `docs/system/permissions.md` |
| New service / layer / integration / data-store (architecture-shaping) | `docs/system/architecture.md` |
| Job / queue worker / scheduler / cron / listener / observer / webhook | `docs/generated/behavior-logic.md` |
| Realtime: WebSocket / SSE / EventSource / socket gateway / pub-sub channel | `docs/generated/behavior-logic.md` |
| New feature surface (touches ≥2 of: routes, screens, models, jobs) | `docs/generated/feature-list.md` (advise `--features F###` if entirely new) |
| User-visible flow change (forms, wizards, multi-step interactions) | `docs/generated/user-stories.md` |

Rules:
- Edits stay in tables; never rewrite headings or schemas.
- Per-artifact >3 changed source files → skip + advise `/tkm:rebuild-spec --artifact NAME`.
- New per-feature spec → never created here; advise `/tkm:rebuild-spec --features F###`.
  Promote-cleanup (`status:` flips, `screen_spec_shas` refresh) is the orchestrator's
  Stage 6.b duty, NOT doc-writer's.
- Emergent-infra ADR nudge: if `IMPACT_MAP` hits `behavior-logic.md`, `entities.md`, or `architecture.md`
  for infrastructure the original task did NOT explicitly request (queue/socket/realtime/new model
  introduced during planning), the orchestrator emits a 1-line stderr advisory
  `ℹ  Consider docs/decisions/ADR-### — records WHY this unrequested infra was added`. Advisory only —
  never auto-writes ADRs (`docs/decisions/*` is human-only). The "unrequested" judgment is the
  orchestrator's (it holds the original request); bash detection cannot make it.
- Full surgical-edit + escalation policy: `claude/skills/_shared/docs-canonical-mapping.md`.

## Delivery Stage (Git)

```
Task(subagent_type="git-manager", prompt="Stage and commit changes with conventional commit message", description="Commit work")
```

## Parallel Forge

```
Task(subagent_type="implementer", prompt="Implement [phase-file] with file ownership: [files]", description="Forge phase [N]")
```
- Launch multiple for concurrent phases
- Include file ownership boundaries to avoid conflicts
