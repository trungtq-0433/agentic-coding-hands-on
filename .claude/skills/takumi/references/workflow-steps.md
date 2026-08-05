<!-- layout-exempt: takumi references — all docs/system|features|generated|flows paths are takumi's own forward-draft targets, promote targets, or spec-layer detection references -->
# The Seven Stages

Every discipline shares the same seven stages. What differs is the pace and the pauses.

**Task Tool Fallback:** `TaskCreate`/`TaskUpdate`/`TaskGet`/`TaskList` are CLI-only — unavailable in VSCode extension. If they error, use `TodoWrite` for tracking. All stages remain functional without Task tools.

## Stage 0: Read the Material

1. Run the input through the rules in `intent-detection.md`
2. Announce the discipline you landed on: `⚒ Stage 0: Discipline [X] — [reason]`
3. **Classify work type** per `intent-detection.md` → "Work-Type Detection":
   - **Already-classified guard:** if the input is an existing plan (code discipline) whose
     frontmatter carries `work_type:`, USE that value — do NOT re-classify, do NOT re-ask. If the
     frontmatter carries `spec_waived:`, the spec was explicitly waived at plan time — Stage 1.5 is
     skipped and the waiver is NOT re-litigated (Pre-flight spec box quotes the recorded waiver).
   - Determine `feature | deliverable | ambiguous` BEFORE discipline routing's effects on Stage 1.5 and BEFORE any `F###` reservation claim.
   - `ambiguous` → call `AskUserQuestion` immediately (ONE question: product feature or one-off deliverable?). This is BLOCKING in all disciplines including `--auto` (F13 precedent: classification defines scope).
   - `deliverable` → Stage 1.5 is skipped entirely; no `F###` allocation; no reservation claim; Pre-flight spec box = `N/A — non-feature deliverable (work-type: deliverable)`.
   - `feature` → continue normally; Stage 1.5 runs per discipline table.
4. If discipline=code: detect blueprint path, set active plan
5. Use `TaskCreate` to create stage tasks (with dependencies if complex)
6. **Promote sentinel check:** If `docs/.spec-promote-pending.json` exists, a prior run crashed after
   starting promote (copying a plan-dir draft into `docs/`) but before Stage 6 cleaned it. Prompt BEFORE
   proceeding, following the matching branch of § Promote-Failure Rollback in `spec-state-registration.md`.
   **Detect the shape first:** a sentinel with a `features[]` array is **SYSTEM v2** — follow the
   `stage0-preflight-gates.md` → "Promote Sentinel Check" SYSTEM branch (revert every `features[]` entry by its per-entry `run_type`).
   Otherwise it is **SINGLE** (`{fcode, run_type, plan_dir, slug, from, screens, ts}`):
   > "Promote sentinel found: `<fcode>` (run_type: `<run_type>`, plan: `<plan_dir>`, started: `<ts>`).
   > Options: (1) REVERT — `git checkout HEAD -- docs/features/<fcode>_*` + the listed `screens`; if
   >   `run_type: new` also remove its `_canonical-fcodes.json` reservation row + feature-list row; if
   >   `plan.md` was repointed, restore `spec_draft: <from>`; delete sentinel.
   > (2) KEEP — leave docs as-is (promote was effectively complete); delete sentinel.
   > (3) Abort — stop this run entirely."
   Do NOT start a new run until the sentinel is resolved.
7. **SDD Mode Gate:** Resolve `takumi.sddMode` (injected `## Plan Context` line `- SDD mode: <value>`,
   or `$TKM_SDD_MODE`, or `loadConfig().takumi.sddMode`; default `ask`). Full procedure (the first-run
   `AskUserQuestion` box + persistence to `.claude/.tkm.json`) lives in
   `stage0-preflight-gates.md` → "SDD Mode Gate". Resolve it here so that when Stage 1.5 checks both signals
   (work-type AND sddMode), both are already known:
   - `on` → Stage 1.5 runs per discipline table.
   - `off` → Stage 1.5 is skipped project-wide (no `F###`, no reservation); Pre-flight spec box =
     `N/A — SDD mode disabled (takumi.sddMode: off)`. Study/Blueprint/Forge/Temper/Inspect/Deliver unchanged.
   - `ask` → BLOCKING `AskUserQuestion` (all disciplines incl. `--auto`), persist the answer, then continue with it.
   **Code discipline:** skip this gate — the blueprint already encodes the spec decision.
8. **Spec Promote (code discipline — Stage 0 IS implement-start for code).** Promote runs once, at
   implement-start. For `code` discipline that point is HERE (the blueprint already exists, so loading
   it begins implementation). For every forging discipline (interactive/auto/parallel/no-test/fast)
   implement-start is blueprint-approval → Forge, so they promote at the **Stage 3 Promote Gate** with
   this same recipe — NOT here. If `plan.md` frontmatter has `spec_draft:` (a plan-dir
   draft path), run the promote recipe NOW — after blueprint load, BEFORE Stage 3 Forge:
   **`claude/skills/rebuild-spec/references/spec-state-registration.md` § Promote** (P0–P5).
   On success the spec lives at `docs/features/F###_Slug/` (`status: implemented`) and
   `docs/.spec-promote-pending.json` is present until Stage 6 deletes it. After promote, repoint
   `plan.md` frontmatter: replace `spec_draft:` with `spec: docs/features/F###_Slug/` so Stage 6 and
   downstream tooling resolve the promoted location.
   **SYSTEM (`spec_draft:` dir contains `feature-list.md`):** run **§ Promote — SYSTEM** instead — it
   loops over all N feature folders (per-feature run-type, contiguous block reservation for the new
   subset, provisional→real remap that promote also writes back into every `phase-XX` `feature: F###`),
   and repoints `spec:` to a YAML **list** of the promoted `docs/features/F###_Slug/` dirs. Emit:
   `⚒ Stage 0: Specs promoted — N features at docs/features/`.
   If frontmatter already has `spec:` (no `spec_draft:`) the spec was promoted on a prior run — skip
   promote. If neither (`spec_waived:` / `work_type: deliverable`) — skip. Emit (SINGLE):
   `⚒ Stage 0: Spec promoted — F### at docs/features/F###_Slug/`.
   **Also promote any `spec/system/*` drafts** (architecture/permissions) via
   **§ Promote — SYSTEM-DOC** (single-file: copy → `docs/system/<name>.md`, flip status, sentinel
   `system_docs` branch — NO F###/feature-list row). Runs alongside the feature promote.

**Output:** `⚒ Stage 0: Discipline [interactive|auto|fast|parallel|no-test|code] — [detection reason] — work-type [feature|deliverable] — sddMode [on|off]`
(append `— sddMode [on|off]` once the SDD Mode Gate resolves; omit for `code` discipline where the gate is skipped.)
If classification is `ambiguous`, emit `⚒ Stage 0: … — work-type ambiguous — AskUserQuestion` and
block; Stage 0 does not complete (and the Output line above is not final) until the user resolves
the question to `feature` or `deliverable`.

## Stage 1: Study the Craft (skip if fast/code)

**Interactive/Auto:**
- Send several `researcher` agents out at once, each on its own topic
- Read the existing code via `/tkm:scan-codebase ext` or the `scout` agent
- Cap each report at 150 lines

**Parallel:**
- Optional: at most 2 researchers, and only when the work warrants it

**Evidence emission (after scoping):** resolve `{plan}/evidence/` once (absolute) and write `study-context.json` — `{task, mode, acceptanceCriteria[], touchpoints[], blastRadius[], contracts[]}`. This is the brief the inspection is later checked against; an empty `acceptanceCriteria` makes "done" unfalsifiable. Shape: `_shared/references/evidence-artifacts.md`.

**Greenfield/empty repo:** Study may be trivially short — there is nothing to scan. That empties
Study, NOT Stage 1.5. Emit `⚒ Stage 1: Study complete — greenfield, nothing to scan` and proceed
to Stage 1.5 regardless. Skipping Study NEVER skips Spec.

**Output:** `⚒ Stage 1: Study complete — [N] reports gathered`

## Stage 1.5: Spec — Author the Feature Spec (skip if fast-minimal/code OR work-type=deliverable OR sddMode=off)

If `takumi.sddMode` is `off` (resolved by the Stage 0 SDD Mode Gate): skip this stage entirely — NO `F###` allocation, NO reservation claim, NO spec researcher; proceed to Stage 2 with Blueprint Pre-flight spec box = `N/A — SDD mode disabled (takumi.sddMode: off)`. This is a project-level waiver and is NOT re-litigated per run.

If work-type=deliverable: skip this stage entirely — NO `F###` allocation, NO reservation claim; proceed to Stage 2 with Blueprint Pre-flight spec box = `N/A — non-feature deliverable (work-type: deliverable)`.

**Interactive/Auto/Parallel/No-test:**

**Spec output shape (NON-NEGOTIABLE — this is the rebuild-spec feature shape, NOT a screen spec).**
A feature draft is a DIRECTORY of **four files**, never a single `spec.md`:

```
plans/<plan_dir>/spec/<slug>/technical-spec.md     # FR/BR/SM/ALG/INT, key entities, user stories
plans/<plan_dir>/spec/<slug>/business-context.md   # plain language, no codes
plans/<plan_dir>/spec/<slug>/screens.md            # screen flow + route table
plans/<plan_dir>/spec/<slug>/edge-cases.md         # test scenarios + error states
```

`technical-spec.md` (the file validators scan) opens with **YAML frontmatter**, never a blockquote;
the other three inherit provenance from the folder:

```yaml
---
status: draft
authored_by: takumi
created: <YYYY-MM-DD>
lang: <spec_lang>
---
```

**Spec language (MANDATORY gate — BLOCKING for greenfield interactive).** The shared procedure's
Pre-Step resolves `spec_lang` ONCE per run before any researcher spawns: existing
`docs/.rebuild-state.json → primary_lang` wins (no prompt); greenfield asks (`AskUserQuestion`:
en / vi / jp / Other) in every interactive discipline; takumi `--auto` defaults silently to `en`.
This is surfaced at Stage 0 (`stage0-preflight-gates.md` → "Language Gate") and verified at the
Blueprint Pre-flight `Spec language resolved` box — never silently default `en` on an interactive run. The directive rides in each researcher's spawn prompt and is recorded as
`lang:` in `technical-spec.md` — promote bootstraps `primary_lang` from it for greenfield.

**Three forbidden shortcuts (these are exactly how this stage fails in practice):**
1. ❌ Authoring a single bespoke `spec.md` instead of the 4-file set. (`spec.md` is the *screen* shape — `spec/<slug>/screens/SCR-<name>/spec.md` — never the feature shape.)
2. ❌ A blockquote `> Status: draft …` instead of the YAML frontmatter above.
3. ❌ Allocating an `F###` at author time (in the title, frontmatter, plan, or "promote to docs/features/F###_*"). For a NEW feature the `fcode:` key is **OMITTED entirely** — it is allocated at promote (implement-start). Set `fcode:` only when revising an EXISTING `implemented` feature (reuse its code).

Also record `spec_draft:` in `plan.md` frontmatter (not as prose) — SINGLE:
`plans/<plan_dir>/spec/<slug>/`; SYSTEM: `plans/<plan_dir>/spec/`.

**SYSTEM vs SINGLE — enumerate-first, default SYSTEM.** Step 0 of the shared procedure runs two checks
before choosing mode: (B) a CLOSED conjunction smell-flag on the raw task text (ports Wave4.5 Check 1
conjunction rule to feature granularity — ALWAYS-fire phrases force SYSTEM immediately; NEVER-fire
CRUD pairs stay SINGLE; gray zone falls to enumeration), then (A) an explicit enumeration of distinct
user-facing intents (`(actor, action-domain, outcome)` triples). Count ≥ 2 → SYSTEM (the default for
any ambiguous case — over-decomposition is recoverable; under-decomposition is not). Count = 1
confirmed → SINGLE. Step 0 MUST emit `plans/<plan_dir>/spec/.intent-enum.json` (mode, intents,
justification) — this is the chokepoint artifact `scaffold_spec.py` reads to gate file creation.
A forced SYSTEM stalls `--auto` at Rest Point 1.5a (deliberate human-in-the-loop gate, never silent).
`--fast` is the only exception: always SINGLE, never decomposes, still emits the artifact with
`justification` set. When SYSTEM: the procedure decomposes into a `feature-list.md` draft (rebuild-spec
format), runs the quality gate (greenfield subset of W5.6), and pauses at **Rest Point 1.5a** for you
to confirm/merge/split — **BLOCKING even in `--auto`**. Then fans out one 4-file set per confirmed
feature (bounded batch `REBUILD_FS_BATCH_SIZE`). A SINGLE feature skips decomposition (N=1, no
feature-list). Full rules: the shared procedure Steps 0–0b + `spec-authoring-contract.md`
§ Greenfield Feature-List.

Run the shared procedure in full:
**`claude/skills/rebuild-spec/references/spec-stage-procedure.md`**

The procedure covers: scope assessment + SYSTEM decomposition into `feature-list.md` (Step 0) with its
quality gate and **Rest Point 1.5a** (confirm feature set), draft slug + plan-dir target resolution
(no author-time ID allocation or sentinel — drafts go to the plan dir; `F###` allocation + registration
happen at promote, code-discipline Stage 0 step 8), **scaffolder invocation** (`scaffold_spec.py`
creates the 4-file set with correct frontmatter + H2 skeleton before the researcher spawns —
researchers FILL pre-scaffolded files, not create them from scratch), spec researcher spawn/fan-out
(rejected/failed-spawn cleanup), per-feature content verification (Step 2.5 — structural checks owned
by scaffolder; lint guards researcher CONTENT mutations only), gap clarification (F13 auto-mode
blocking-category rule), **[Rest Point 1.5b]** spec approval gate (abort deletes the plan-dir draft
only), and emit line.

**Forward-draft system docs (architecture / auth — opt-in).** If this task TOUCHES architecture
(new service/layer/integration/data-store) or auth (RBAC/policy/guard/middleware/roles) — detected via
the existing Trigger Mapping (`references/subagent-patterns.md` → `## Documentation`; do NOT reinvent
the pattern) — ALSO forward-draft the relevant `docs/system/*` narrative to
`plans/<plan_dir>/spec/system/<name>.md` (`architecture.md` and/or `permissions.md`), per
`spec-authoring-contract.md` § Forward-Authored System Docs (single-file draft frontmatter, NEVER
fabricate codes, rationale → ADR, NEVER write `docs/generated/*`). Record the draft path(s) in `plan.md`
frontmatter so promote finds them. A task touching neither → no system draft (opt-in, no noise).
These promote at implement-start ALONGSIDE the feature promote (§ Promote — SYSTEM-DOC) and are
reconciled to as-built when the post-forge Core pass next runs (Step 6.a-pre — see its reconcile caveat).

**Fast discipline (takumi-specific):** Skip the Stage 1.5 researcher spawn. Author only a minimal delta
to `technical-spec.md` (overview section) in the plan dir.
Even though the researcher is skipped, still run the shared **Pre-Step language resolution**
(`spec-stage-procedure.md` § Pre-Step) inline before writing the minimal spec, and stamp the
resolved `lang: <spec_lang>` into the draft frontmatter: existing `docs/.rebuild-state.json`
`primary_lang` wins; greenfield + `--auto` → silent `en`; greenfield interactive → ask. Never leave
`lang:` unresolved.
Still write `spec_draft: plans/<plan_dir>/spec/<slug>/` into `plan.md` (promote repoints it to `spec:`
at implement-start). Registration does not run at author time — it runs at promote (the REDUCED recipe
subset; see `spec-state-registration.md` § Fast-Discipline Subset). Partial specs KEEP `status: draft`.
At delivery, emit one-line advisory:
> "⚒ minimal spec only — run `/tkm:rebuild-spec --features F###` for the full 4-file spec."

**Code discipline:** Skip Stage 1.5 entirely — blueprint already exists.

### [Rest Point 1] After Study (skip if auto)
- Present study summary to user
- Use `AskUserQuestion` to ask: "Proceed to spec?" / "Request further study" / "Abort"
- **Auto discipline:** Skip this rest point

### MoMorph Parallel UI Hook (between Stage 1.5 and Stage 2)

**Trigger:** User input contains MoMorph URL (`momorph.ai/files/*/screens/*`), explicit `fileKey`/`screenId`, or keyword "momorph"/"figma" referencing a screen to implement.

**When triggered, BEFORE entering Stage 2:**
1. Collect all screen identifiers from user input (may be 1 or N screens)
2. Fetch per screen in parallel: `get_frame(screenId)` + `download_specs(screen_id, "csv")` + `download_test_cases(screen_id, "csv")`
3. **Spawn one background `implementer` subagent PER SCREEN** (via `Agent` with `run_in_background: true`). All UI agents run concurrently:
   - Each subagent uses `momorph-implement-design` skill for its screen (ships in `extras` kit; install via `tkm init --kit extras`)
   - Mock data extracted directly from Figma design (text, images, sample values visible in the design) — NO invented data
   - Prompt MUST include: MoMorph URL, fileKey, screenId, project conventions path
   - Each subagent reports back: files created, component tree, data interfaces/props expected
4. **DO NOT wait for UI agents.** Continue immediately to Stage 2 (Blueprint) → Stage 3 (Forge). Blueprint and forge proceed in parallel with UI agents.
5. **Integration is incremental:** As each UI agent completes (background notification), integrate its output with the forged logic. No hard merge point — work flows continuously.

**If NOT triggered:** Proceed to Stage 2 normally.

See `.claude/rules/momorph/momorph-development.md` → "Parallel Execution Strategy" for full protocol.

## Stage 2: Draft the Blueprint

**HARD GATE — Blueprint Pre-flight (interactive/auto/parallel/no-test).** Before spawning the
`planner`, emit the Blueprint Pre-flight block (SKILL.md → Workshop Rest Points) verbatim. The
the spec box must honestly read `[x]` for one of these six valid states (full/minimal drafts are
authored to the plan dir and recorded as `spec_draft: plans/<plan_dir>/spec/<slug>/`):
- full spec draft (Stage 1.5),
- minimal spec draft (`fast`),
- existing blueprint (`code`, N/A),
- explicit user waiver (quote their words),
- `N/A — non-feature deliverable (work-type: deliverable)`,
- `N/A — SDD mode disabled (takumi.sddMode: off)`.

If none of these holds, do NOT spawn the planner: return to Stage 1.5 and run it first. An empty repo is NOT a waiver
— greenfield is when the spec is created. (But `sddMode: off` IS a project-level waiver — that state is valid.)

**Interactive/Auto/No-test:**
- Use `planner` agent with study context and the draft path from Stage 1.5 (SINGLE:
  `plans/<plan_dir>/spec/<slug>/`; SYSTEM: `plans/<plan_dir>/spec/` — includes `feature-list.md` + N
  feature folders). If a draft was authored, pass it explicitly — planner MUST reference FR/SC IDs
  from the draft and write `spec_draft:` into `plan.md` frontmatter (SINGLE value
  `plans/<plan_dir>/spec/<slug>/`; SYSTEM value `plans/<plan_dir>/spec/`).
  (`spec:` is written ONLY by the promote step — Stage 0 step 8 for `code`, or the Stage 3 Promote Gate
  for forging disciplines — never by the planner.)
- **SYSTEM — feature↔phase decoupling (1:N, planner's call).** Features (the WHAT) and phases (the
  HOW/sequencing) are NOT 1:1. The planner reads `feature-list.md` and self-evaluates merge vs split:
  a large feature MAY span **multiple** `phase-XX-*.md` files; several small related features MAY share
  one phase. Every phase file MUST carry `feature: F###` (or a comma-separated list when a phase covers
  more than one) in its frontmatter so promote/tracking can map phases back to features. Use the
  **provisional** `F###` from `feature-list.md` (real codes are allocated at promote).
- Planner MUST also write `work_type: feature|deliverable` into `plan.md` frontmatter alongside the optional `spec_draft:` field.
- **When `sddMode=off`:** the planner MUST write `spec_waived: "SDD mode disabled (takumi.sddMode: off)"`
  into `plan.md` frontmatter (and NO `spec_draft:`/`spec:`). This makes the promote step (Stage 0 step 8
  / Stage 3 Promote Gate) and Stage 6.b promote-cleanup all skip by the explicit `spec_waived:` condition — same record tkm-plan's
  step 1d writes. Mutually exclusive with `spec_draft:` and `spec:`.
- Create `plan.md` + `phase-XX-*.md` files

**Fast:**
- Use `/tkm:create-plan --level low` with scout results only
- Minimal blueprint, focus on action

**Parallel:**
- Use `/tkm:create-plan --parallel` for dependency graph + file ownership matrix

**Code:**
- Skip — blueprint already exists
- Parse existing plan for phases

**Output:** `⚒ Stage 2: Blueprint drafted — [N] phases`

### [Rest Point 2] After Blueprint (skip if auto)
- Present blueprint overview with phases
- Use `AskUserQuestion` to ask: "Validate the blueprint or approve to begin forging?" — "Validate" / "Approve" / "Abort" / "Other" ("Request revisions")
  - "Validate": run `/tkm:create-plan validate` skill invocation
  - "Approve": proceed to forge
  - "Abort": stop the workflow
  - "Other": revise the blueprint based on feedback
- **Auto discipline:** Skip this rest point

## Stage 3: Forge the Piece

**Promote Gate (implement-start — ALL forging disciplines: interactive/auto/parallel/no-test/fast).**
Forging IS implement-start. **Run this BEFORE `TaskList`/`TaskCreate`** (so the provisional→real `F###`
remap lands in the phase files before tasks are built from them). If `plan.md` frontmatter still has
`spec_draft:` (i.e. sddMode on, work-type feature, spec not yet promoted), run the promote recipe NOW —
identical to Stage 0 step 8:
**`claude/skills/rebuild-spec/references/spec-state-registration.md` § Promote** (SINGLE), or
**§ Promote — SYSTEM** when the `spec_draft:` dir holds `feature-list.md`. It allocates the real `F###`,
copies drafts to `docs/features/F###_Slug/` (`status: implemented`), registers state, writes the
`docs/.spec-promote-pending.json` sentinel (deleted at Stage 6.b), repoints `plan.md` `spec_draft:` →
`spec:`, and (SYSTEM) writes each real `F###` back into every `phase-XX` `feature:` key.
Emit `⚒ Stage 3: Spec promoted — <F### | N features> at docs/features/`.
**Also promote any `spec/system/*` drafts** (architecture/permissions) via **§ Promote — SYSTEM-DOC**
(single-file copy → `docs/system/<name>.md`, flip status, sentinel `system_docs` branch) — alongside the feature promote.
**Idempotent / skip conditions:** `code` discipline already promoted at Stage 0 step 8 (frontmatter is
`spec:`, no `spec_draft:`) → no-op; `spec_waived:` / `work_type: deliverable` / `sddMode: off` → skip.
This closes the gap where an end-to-end interactive/auto run authors the spec AND forges in ONE session
and would otherwise never reach the code-discipline Stage 0 promote (spec stuck as a plan-dir draft).

**IMPORTANT:**
1. `TaskList` before anything else — the planning skill may have seeded tasks earlier this session
2. Found some? Carry them forward, don't recreate
3. None there? Read the plan phases and `TaskCreate` one per unchecked `[ ]` item, in priority order, carrying its metadata (`phase`, `planDir`, `phaseFile`)
4. Chain dependencies between tasks with `addBlockedBy`

**All disciplines:**
- Use `TaskUpdate` to mark tasks as `in_progress` immediately
- Execute phase tasks sequentially (Stage 3.1, 3.2, etc.)
- Use `ui-ux-designer` for frontend (activate `tkm:design-ui` first for style selection if no design system exists)
- Use the Read tool to analyze image assets
- Run type checking after each file

**Parallel discipline:**
- Lean on the full Claude Tasks toolset: `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList`
- Fan out across several `implementer` agents
- When agents pick up a task, use `TaskUpdate` to assign and mark `in_progress` immediately
- Respect file ownership boundaries
- Wait for parallel group before advancing

**Output:** `⚒ Stage 3: Forged [N] files — [X/Y] tasks complete`

### [Rest Point 3] After Forge (skip if auto)
- Present forge summary (files changed, key changes)
- Use `AskUserQuestion` to ask: "Proceed to tempering?" / "Request forge changes" / "Abort"
- **Auto discipline:** Skip this rest point

## Stage 4: Temper the Edge (skip if no-test)

**All disciplines (except no-test):**
- Cover the happy path, the edges, and the failure modes
- **MUST** spawn `tester` subagent: `Task(subagent_type="tester", prompt="Run test suite", description="Temper the work")`
- On any failure, **MUST** spawn the `debugger` subagent → fix → run again
- **Forbidden:** faked mocks, commented-out tests, loosened assertions, or skipping the subagent handoff

**Evidence emission:** pass the absolute `{plan}/evidence/` dir to the `tester` subagent. It reports each command + its REAL exit code + a one-line summary into that dir; the orchestrator turns those raw runs into `temper-results.json` via `buildTemperResults()` in `hooks/lib/evidence-validator.cjs` — code constructs the artifact so `exitCode` is always a real integer, never a string a model typed. Parallel test groups write `temper-results-<label>.json`; the validator aggregates them.

**Output:** `⚒ Stage 4: Tempering [X/X passed] — tester subagent invoked`

### [Rest Point 4] After Tempering (skip if auto)
- Present tempering results summary
- Use `AskUserQuestion` to ask: "Proceed to inspection?" / "Request tempering fixes" / "Abort"
- **Auto discipline:** Skip this rest point

## Stage 5: Master's Inspection

**All disciplines — MANDATORY subagent:**
- **MUST** spawn `reviewer` subagent: `Task(subagent_type="reviewer", prompt="Inspect changes. Return score, critical defects, concerns, refinements.", description="Inspect work")`
- **DO NOT** inspect code yourself — delegate to the reviewer
- **Evidence emission:** pass the absolute `{plan}/evidence/` dir to the reviewer; it is the SINGLE writer of `inspection-verdict.json` — `{score, criticalCount, decision, acceptanceCovered[], regressionChecked[], contractStatus, refuted[], unproven[], reachableRegressions[]}`. `decision` is `SEALED` only when `criticalCount==0` AND `refuted`/`unproven`/`reachableRegressions` are empty AND `contractStatus != UNKNOWN`. Score is advisory — it never seals by itself.

**Interactive/Parallel/Code/No-test:**
- Interactive cycle (max 3): see `review-cycle.md`
- Requires user approval

**Auto:**
- Pass it through when the score hits 9.5+ with zero critical defects
- Mend critical defects on its own, up to 3 rounds
- Hand it back to the user once 3 rounds fall short

**Fast:**
- Simplified inspection, no fix loop
- User approves or aborts

**Output:** `⚒ Stage 5: Inspection [score]/10 — [Approved|Auto-approved] — reviewer subagent invoked`

## Stage 6: Deliver the Work

**Hard ordering rule (Stage 6 trap):** Both subagents in step 6.1 (`project-manager` AND `doc-writer`) must be spawned BEFORE any commit-related `AskUserQuestion`. The commit prompt is NOT the seal — the Delivery Manifest is. If you find yourself about to ask "Ready to commit?" and have not yet spawned both, STOP and spawn them first. No exceptions for "tests passed and review approved" — that is precisely when the trap fires. Full anti-rationalization table: SKILL.md → "Delivery Anti-Rationalization".

### Step 6.a-pre — Documentation gen gate (orchestrator, after Inspect, BEFORE doc-writer)

Runs AFTER Temper+Inspect (code is final) and BEFORE Step 6.a artifact detection. Bootstraps the
code-derived doc layer (Core/Flow) via `rebuild-spec` so doc-writer then has something to surgically
keep fresh. Cursor-driven off `docs/.rebuild-state.json` — NOT `ls docs/`.

**Guard — run only when ALL hold; else skip with `⚒ Step 6.a-pre: gen gate skipped — <reason>`:**
`plan.md` frontmatter `work_type: feature` AND sddMode resolved `on` AND code was forged this session.
(deliverable / `spec_waived:` / SDD off / no-forge → skip.)

```bash
# REBASELINE_THRESHOLD_FILES: re-baseline advisory fires when files changed since the last Core
# rebuild reaches this (≈5 feature areas ≈ 20 files — single files-based trigger; tunable knob).
REBASELINE_THRESHOLD_FILES=20
STATE=docs/.rebuild-state.json
CORE_SHA=$(node -e "try{process.stdout.write((require('./'+process.argv[1]).last_rebuild_sha)||'')}catch(e){}" "$STATE" 2>/dev/null)
FLOW_SHA=$(node -e "try{process.stdout.write((require('./'+process.argv[1]).last_flows_run_sha)||'')}catch(e){}" "$STATE" 2>/dev/null)
core_absent=$([ -z "$CORE_SHA" ] && echo 1 || echo 0)
flow_absent=$([ -z "$FLOW_SHA" ] && echo 1 || echo 0)
# staleness: files changed since the last Core rebuild
CHANGED=$([ -n "$CORE_SHA" ] && git diff --name-only "$CORE_SHA"..HEAD 2>/dev/null | wc -l | tr -d ' ' || echo 0)
core_stale=$([ -n "$CORE_SHA" ] && [ "$CHANGED" -ge "$REBASELINE_THRESHOLD_FILES" ] && echo 1 || echo 0)
```
Treat a cursor read that FAILS (no node / parse error) as "unknown, skip with advisory" — NOT as
"absent" (a false-absent would trigger a spurious full regen). Emit
`⚒ Step 6.a-pre: gen gate skipped — cursor read failed (state unknown); run /tkm:rebuild-spec manually if docs look stale.`

**`fast` discipline** — do NOT auto-run a heavy Core pass (fast trades thoroughness for speed). Treat
the gate as advisory-only: emit `ℹ Step 6.a-pre: docs not bootstrapped (fast); run /tkm:rebuild-spec when ready.`
and continue. (Interactive `fast` may still pick passes from the box if it appears.)

**Interactive branch** — if `core_absent || flow_absent`, `AskUserQuestion` (multiSelect)
`[Core] [Flow] [Skip]`, each option with a 1-line cost note (rebuild-spec spawns several agents).
(multiSelect — picking both `Core` + `Flow` IS "both"; no separate `Both` option.)
Inline dependency note: **"Flow requires Core (feature-specs) first."** ENFORCE: if the user picks Flow
while Core is absent and not also picked → run Core first, then Flow. If nothing is absent → **no box**
(doc-writer keeps prose fresh per-task; nothing to bootstrap).

**`--auto` branch** — NEVER prompts:
- **Bootstrap** (`core_absent || flow_absent`) → run the absent passes automatically in dependency
  order **Core → Flow**.
- **Re-baseline** (`core_stale`, nothing absent) → **ADVISORY ONLY**, do NOT regenerate:
  `ℹ Step 6.a-pre: docs may be drifting — <CHANGED> files changed since last Core rebuild (≥ REBASELINE_THRESHOLD_FILES); consider /tkm:rebuild-spec.`

**Run chosen passes on the FINAL forged code** (Core before Flow when both): `Core = /tkm:rebuild-spec`,
`Flow = /tkm:rebuild-spec --flows`.
`docs/.rebuild-state.json` is READ before the pass; each pass advances ONLY its own cursor
(cursor-isolation) — the gate itself never writes state. Then continue to Step 6.a.

**No-handroll rule (HARD).** ONLY `/tkm:rebuild-spec` (Core) and `/tkm:rebuild-spec --flows` (Flow)
satisfy this gate. Hand-authoring a doc-writer-style subset of the code-derived layer — a few
`docs/system/*` or `docs/generated/*` files written by the orchestrator or a doc-writer spawn — does
**NOT** satisfy it and counts as a SKIP. The canonical pipeline is the only thing that advances the
state cursor; anything that leaves the cursor untouched did not bootstrap the layer. If `rebuild-spec`
itself fails (e.g. `promote_drafts.py` exits non-zero — see its `promoted 0` block), **STOP and fix the
pipeline** — never substitute a hand-rolled subset to "make the gate green".

**Cursor postcondition (HARD).** After the pass returns, RE-READ `docs/.rebuild-state.json` and assert
the relevant cursor advanced to HEAD: Core must move `last_rebuild_sha`, Flow must move
`last_flows_run_sha`. If the cursor is unchanged from its pre-pass value, the pass did **not** actually
run — do NOT emit "ran". Re-invoke the pass once; if it still does not advance, emit BLOCKED with the
stuck cursor sha and stop (do not hand-roll).

**Evidence emit (derived from state, not self-asserted).** Only after the postcondition passes, emit
`⚒ Step 6.a-pre: ran <Core|Flow|Both> on forged code — <N> core artifacts @ <sha7>` where `<N>` is the
count of code-derived artifacts present and `<sha7>` is the advanced cursor (Core → `last_rebuild_sha`,
Flow → `last_flows_run_sha`; Both → Core's). The count/sha come from the re-read state, never from the
orchestrator's recollection.

**Lifecycle:** this bootstraps the prose layer ONCE when absent; doc-writer (guardrailed prose) keeps it
fresh per-task; the re-baseline THRESHOLD is the drift escape hatch. **Reconcile caveat:** forward-drafted
`docs/system/*` (Stage 1.5) are reconciled to as-built only WHEN the Core pass actually runs here — i.e.
when Core is absent (auto-bootstrap). On a repo that already has a Core baseline, the gate only emits the
re-baseline advisory; the promoted system-doc draft then stays as-is until a manual `/tkm:rebuild-spec`.
See `_shared/docs-canonical-mapping.md` — don't restate.

### Step 6.a — Artifact detection (orchestrator, before doc-writer spawn)

Run this detection BEFORE spawning `doc-writer`. The orchestrator resolves the conditional and renders the prompt with the artifact branch already inlined or omitted — `doc-writer` does NOT see literal `[IF SPECS_PRESENT > 0:]` markers.

> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). The `ls` command below probes `docs/` root which is correct for single-lang mode (the common case).

```bash
SPECS_PRESENT=$(ls docs/system/*.md docs/generated/*.md docs/features/*/*.md docs/flows/*.md 2>/dev/null | wc -l | tr -d ' ')
# Step 6 runs BEFORE git-manager commits, so capture uncommitted working tree + index vs HEAD.
# Includes both staged and unstaged changes from this session.
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null)

# Advisory: signal absent doc layer when session changed substantial feature surface.
# Source for trigger patterns: claude/skills/takumi/references/subagent-patterns.md
#                              → ## Documentation → Trigger Mapping
TRIGGER_HITS=0
if [ -n "$CHANGED_FILES" ]; then
  TRIGGER_HITS=$(echo "$CHANGED_FILES" \
    | grep -vE '/(tests?|__tests__|spec|mocks?|fixtures?)/|\.(test|spec)\.' \
    | grep -cE '/(routes?|controllers?|api|endpoints?|models?|schema|migrations?|prisma|pages?|screens?|views?|router|navigation|auth|rbac|policy|guard|middleware|jobs?|queues?|workers?|cron|listeners?|webhooks?|observers?|sockets?|websockets?|gateways?|realtime|channels?|sse)/')
fi

if [ ! -d docs ] && [ "$TRIGGER_HITS" -ge 2 ]; then
  echo "ℹ  ./docs/ not found — ${TRIGGER_HITS} feature-surface files changed this session." 1>&2
  echo "ℹ  Consider /tkm:manage-docs init to scaffold project docs." 1>&2
elif [ -d docs ] && [ "$SPECS_PRESENT" = "0" ] && [ "$TRIGGER_HITS" -ge 2 ]; then
  echo "ℹ  spec layer (docs/system, docs/generated, docs/features, docs/flows) absent — ${TRIGGER_HITS} feature-surface files changed this session." 1>&2
  echo "ℹ  Consider /tkm:rebuild-spec to generate spec layer for richer planning context." 1>&2
fi
```

- If `SPECS_PRESENT == 0` → omit the artifact branch from the `doc-writer` prompt. No warning, no extra prompt bloat.
- If `SPECS_PRESENT > 0` → build `IMPACT_MAP` from `CHANGED_FILES` using the trigger table in `subagent-patterns.md` → `## Documentation` → Trigger Mapping (single source — do NOT duplicate the table here).
- Emergent-infra ADR nudge: when `IMPACT_MAP` hits `behavior-logic.md`/`entities.md`/`architecture.md` for infra the original task did NOT request, emit the 1-line ADR advisory per `subagent-patterns.md` → Trigger Mapping → Rules (stderr only; never auto-writes ADRs).
- If `CHANGED_FILES` is empty (e.g. user already committed before invoking finalize) → fall back to the active phase's "Related code files" list, or to `git diff --name-only HEAD~..HEAD` for the last commit. Log which source was used.

Detection is idempotent: an absent spec layer exits cleanly with no error. `tr -d ' '` normalizes BSD-`wc` whitespace padding so `[ "$SPECS_PRESENT" = "0" ]` comparisons work.

**Absent-layer advisory:** the `if/elif` block above is stderr-only and **never** enters the `doc-writer` prompt — `doc-writer` still sees the same artifact branch (omitted when `SPECS_PRESENT == 0`). The two layers are mutually exclusive by control flow: `docs/` missing suppresses the spec-layer advisory because the layered namespaces (`docs/system/`, `docs/generated/`, …) cannot exist without their `docs/` parent. Threshold is `≥ 2` feature-surface hits **after** stripping test/mock/fixture paths, so single-file or pure-test sessions stay silent. Contract details: [`_shared/docs-canonical-mapping.md` § Absent-Layer Advisory](../../_shared/docs-canonical-mapping.md#absent-layer-advisory).

### Step 6.b — Promote cleanup (orchestrator, before doc-writer spawn)

**Skip this step entirely** when `plan.md` frontmatter has `work_type: deliverable` or `spec_waived:`
— no spec was authored and none is expected here; the waiver must NOT be re-litigated.

**Promote sanity-check FIRST (safety net).** Before cleanup, inspect `plan.md` frontmatter:
- If it has `spec:` → spec was promoted at implement-start (Stage 0 step 8 for `code`, or the Stage 3
  Promote Gate for forging disciplines). Proceed with cleanup below.
- If it STILL has `spec_draft:` (work_type feature, sddMode on) → **the Promote Gate did not run** — a
  bug in this run. Do NOT silently ship a forged-but-unpromoted state. Emit a LOUD advisory in the
  Delivery Manifest and to the user:
  `⚠ Spec NOT promoted — drafts remain at <spec_draft path>; docs/features/ was never created. The`
  `code is forged but its spec is still a plan-dir draft. Run the Stage 3 Promote Gate recipe now`
  `(spec-state-registration.md § Promote / § Promote — SYSTEM) to allocate F### and copy to docs/features/,`
  `or re-run "/tkm:takumi <plan.md>" (code discipline) which promotes at Stage 0 step 8.`
  Then continue cleanup (there is no sentinel to delete in this case).

The spec (when promoted) lives at `docs/features/F###_Slug/` (`status: implemented`) — flipped at
implement-start. Stage 6 does NOT flip status — that happened at promote. Stage 6 only:

**SYSTEM (`spec:` is a YAML list of feature dirs):** iterate step 1 over EVERY listed feature + its
screens (refresh each `SCR###` sha), then delete the single batch sentinel ONCE. The same `spec:`
scalar-vs-list tolerance applies as at Stage 0 step 8.

1. **Refresh `screen_spec_shas`** if a screen was registered at promote. Read
   `docs/generated/screen-list.md`. For each `SCR###` section associated with this feature, extract the
   section body (all lines between `## SCR###` heading and the next `## SCR` heading, exclusive of the
   heading line itself, line endings preserved — `splitlines(keepends=True)` semantics; see Step 6 of
   `spec-state-registration.md` for the exact algorithm). Compute:
   ```
   screen_spec_shas["SCR###"] = sha256(section_body.encode("utf-8")).hexdigest()
   ```
   This is the SAME hash the incremental planner computes via `_hash_screen_sections` /
   `_parse_screen_sections`. Write the refreshed value into `docs/.rebuild-state.json`.
   **Do NOT use `sha256(spec.md)` — that will mismatch the planner and cause regeneration.**

2. **Delete the promote sentinel** `docs/.spec-promote-pending.json` → marks a clean promote. If the
   sentinel carried a `system_docs` array (§ Promote — SYSTEM-DOC), those promoted `docs/system/*` files
   are already in place — the single delete here clears the whole sentinel (feature + system_docs) at once.

3. **`code` discipline:** always runs steps 1–2 for the completed spec scope.

If `spec:` is present but `docs/features/F###_Slug/` is incomplete (partial/fast), skip the sha
refresh; the sentinel is still deleted (the fast spec is the sanctioned partial state).

**Every mode — these subagents are required, no exceptions:**
1. **MUST** spawn these subagents in parallel:
   - `Task(subagent_type="project-manager", prompt="Run full sync-back for [plan-path]: reconcile all completed Claude Tasks with all phase files, backfill stale completed checkboxes across every phase, then update plan.md frontmatter/table progress. Do NOT only mark current phase.", description="Update plan")`
   - `doc-writer` — use the canonical prompt template in `subagent-patterns.md` → `## Documentation`. Substitute `[plan-name]` with the active plan name, inline `CHANGED_FILES`, and (when `SPECS_PRESENT > 0`) inline the resolved `IMPACT_MAP` from 6.a. DO NOT duplicate the template body here (DRY).
2. Project-manager sync-back MUST include:

### Status Sync (Deliver)

Drive status changes through the CLI so they land the same way every time:

```bash
# Mark completed phases
tkm plan check <phase-id>

# Mark in-progress phases
tkm plan check <phase-id> --start

# Revert if needed
tkm plan uncheck <phase-id>
```

**Fallback:** When `tkm` is out of reach, hand-edit plan.md —
touch only the Status column cell and leave the table shape intact.
   - Walk through every `phase-XX-*.md` in the plan directory.
   - Flip each finished item `[ ] → [x]` from the completed-task list — earlier phases closed before this one count too.
   - Recompute `plan.md` status/progress (`pending`/`in-progress`/`completed`) from what the checkboxes actually say.
   - Surface any completed task that has no matching phase file as an unresolved mapping.
3. Use `TaskUpdate` to mark Claude Tasks complete after sync-back confirmation.
4. Onboarding check (API keys, env vars)
5. **Run the evidence gate (hard stage)** — `node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir <abs {plan}/evidence> --stage hard`. Exit 0 = SEALED, proceed. Exit 2 = BLOCKED: print the reasons, loop back to fix the unproven/failed item, re-emit the artifact, re-run the gate. The commit prompt is forbidden while the gate exits 2. (See "Evidence Gate" below.)
6. **Emit the Delivery Manifest** to the user (see SKILL.md → "Delivery Manifest"). This is a printed emission, not a private check. All pre-commit boxes (gen-gate, project-manager, orchestrator, doc-writer, TaskUpdate, evidence-gate) must read `[x]` from real subagent/gate verdicts. If any reads `[ ]`, complete that step NOW. The commit prompt is forbidden until the Manifest passes.
7. **MUST** spawn git subagent (only after the Manifest is emitted with all pre-commit boxes checked): `Task(subagent_type="git-manager", prompt="Stage and commit changes", description="Commit work")`
8. Run `/tkm:write-journal` to record the session.

**CRITICAL:** Stage 6 is INCOMPLETE without ALL of the following:
- (a0) documentation gen gate (6.a-pre) evaluated — its Manifest box MUST be emitted (HARD: a missing box is INCOMPLETE). Whether the gate RUNS a pass is conditional on the guard (feature + sddMode on + forged); when the guard is false the box reads `[x] skipped: <reason>`, not absent,
- (a) artifact detection (6.a) run,
- (b) all 3 subagents spawned (`project-manager`, `doc-writer`, `git-manager`) — `doc-writer` is spawned regardless of perceived doc impact; its verdict is what determines whether files change,
- (c) the evidence gate run at `--stage hard` with a real exit-0 SEALED,
- (d) Delivery Manifest emitted verbatim to the user with all pre-commit boxes (gen-gate, project-manager, orchestrator, doc-writer, TaskUpdate, evidence-gate) = `[x]`,
- (e) `/tkm:write-journal` run.

A passing inspection (Stage 5) does NOT absolve any of these. DO NOT pass literal `[IF SPECS_PRESENT > 0:]` to `doc-writer` — orchestrator resolves the conditional first.

**Auto discipline:** Continue to next phase automatically, return to **Stage 3**.
**Others:** Ask user before next phase

**Output:** `⚒ Stage 6: Delivered — 3 subagents invoked — Full-plan sync-back complete — Committed`

## Evidence Gate

"Done" means **evidence, not a promise.** Stages 1/4/5 each leave a structured artifact in `{plan}/evidence/`; Stage 6 runs a deterministic gate over them before the work is sealed. The gate is **inline-only** — the skill runs the CLI at its own Deliver boundary. There is no global hook to bypass and no session/branch plan to resolve: the skill already knows `{plan}` and passes the absolute `{plan}/evidence/` path explicitly to the gate and to every subagent.

| Artifact | Stage | Writer |
|----------|-------|--------|
| `study-context.json` | 1 (Study) | orchestrator, after scoping |
| `temper-results.json` | 4 (Temper) | code (`buildTemperResults`) from `tester`'s raw runs |
| `inspection-verdict.json` | 5 (Inspect) | `reviewer` (single writer) |

**Run it (hard stage) before the commit prompt:**

```bash
node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir "<abs {plan}/evidence>" --stage hard
# exit 0 → SEALED, proceed   |   exit 2 → BLOCKED, show reasons and loop back
```

What blocks at a hard stage: a missing artifact, a failed/`skipped`-only temper run, a non-integer `exitCode`, an unknown/extra key, a `decision` other than `SEALED`, a non-zero `criticalCount`, any `refuted`/`unproven`/`reachableRegressions`, or an `UNKNOWN` contract. A leaked secret VALUE only **warns** (advisory — never blocks). The gate fails OPEN only on its own internal crash, never on a real validation failure. Full field contract + anti-faking intent: `_shared/references/evidence-artifacts.md`.

## Discipline Flow Summary

Legend: `[R]` = Rest Point (human approval required) | `1.5` = Spec stage | `(+promote)` = Spec Promote at implement-start (draft → `docs/features/`, real `F###`)

```
interactive: 0 → 1 → [R] → 1.5 → [R] → 2 → [R] → (+promote)3 → [R] → 4 → [R] → 5(user) → 6
auto:        0 → 1 → 1.5 → 2 → (+promote)3 → 4 → 5(auto) → 6 → next phase (NO pauses)
fast:        0 → skip → 1.5(minimal) → 2(fast) → [R] → (+promote)3 → [R] → 4 → [R] → 5(simple) → 6
parallel:    0 → 1? → [R] → 1.5 → [R] → 2(parallel) → [R] → (+promote)3(multi-agent) → [R] → 4 → [R] → 5(user) → 6
no-test:     0 → 1 → [R] → 1.5 → [R] → 2 → [R] → (+promote)3 → [R] → skip → 5(user) → 6
code:        0(+promote@step8) → skip → skip → 3 → [R] → 4 → [R] → 5(user) → 6
```

**Key distinction:** `auto` is the ONLY discipline that skips all rest points.

**Promote timing:** `(+promote)` fires once at implement-start — the entry to Stage 3 Forge for every
forging discipline, or Stage 0 step 8 for `code` (blueprint already exists). It is guarded by
`spec_draft:` still being present in `plan.md`, so it runs exactly once wherever implement-start lands.

**SDD off:** when `takumi.sddMode: off`, drop the `1.5` node from every flow above — the pipeline runs
study → blueprint → forge → temper → inspect → deliver with no spec stage.

## Critical Rules

- Never skip stages without discipline justification
- **MANDATORY DELEGATION:** Stages 4, 5, 6 MUST spawn subagents via Task tool. DO NOT perform directly.
  - Stage 4: `tester` (and `debugger` if failures)
  - Stage 5: `reviewer`
  - Stage 6: `project-manager`, `doc-writer`, `git-manager`
- Use `TaskCreate` for each unchecked item with priority order and dependencies (or `TodoWrite` if Task tools unavailable).
- Use `TaskUpdate` to mark `in_progress` when picking up a task (skip if Task tools unavailable).
- Use `TaskUpdate` to mark `complete` immediately after the task is finished (skip if Task tools unavailable).
- All stage outputs follow format: `⚒ Stage [N]: [status] — [metrics]`
- **VALIDATION:** If Task tool calls = 0 at end of workflow, the work is INCOMPLETE.
