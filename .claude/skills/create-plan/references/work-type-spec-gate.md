# Work-Type & Spec Gate (Step 1d)

**BLOCKING — runs before any `F###` reservation claim.** This is the full procedure for the
`Work-Type & Spec Gate` node in the SKILL.md Process Flow. SKILL.md carries only the one-line
trigger; the logic lives here.

## SDD Mode pre-check

Resolve `takumi.sddMode` (injected `## Plan Context` line `- SDD mode: <value>`, or `$TKM_SDD_MODE`,
or `loadConfig().takumi.sddMode`; default `ask`). Same project-level toggle as takumi — see takumi
SKILL.md → "SDD Mode" and `takumi/references/stage0-preflight-gates.md` → "SDD Mode Gate".

- `off` → skip this gate's spec-layer branch entirely: proceed specless with NO `F###` reservation;
  plan.md frontmatter gets `spec_waived: "SDD mode disabled (takumi.sddMode: off)"`. Still classify
  work-type for `work_type:`. Do NOT prompt the (a)/(b)/(c) spec choice.
- `ask` → run the takumi SDD Mode Gate's first-run `AskUserQuestion` box
  (`takumi/references/stage0-preflight-gates.md` → "SDD Mode Gate") and persist the answer to
  `.claude/.tkm.json` BEFORE proceeding (one shared decision across takumi and create-plan), then
  route per the resolved value.
- `on` → proceed with the spec gate below as normal.

## Sentinel pre-check

Caller requirement of the shared procedure: if `docs/.spec-promote-pending.json` exists, a prior
promote crashed mid-flight — prompt repair (REVERT `git checkout HEAD -- docs/features/<fcode>_*` + <!-- layout-exempt: git revert command; docs/ root single-lang -->
delete sentinel, or KEEP + delete sentinel) BEFORE this gate proceeds. Same semantics as takumi
Stage 0 promote-sentinel check.

## Level mapping

When the shared procedure runs (choice a), ALL create-plan levels — `--level low`, `medium`, `high`,
`max`, `--parallel`, `--two`, or no flag — are treated as interactive: ask ALL gaps, present the
approval gate. create-plan's `--level` is a research-depth flag, NOT takumi `--auto`; the F13
silent-default rule never applies here.

## Classify work-type

Classify using cues in `claude/skills/takumi/references/intent-detection.md` → "Work-Type Detection"
(LINK for cues only — never copy or paraphrase them here):

- `deliverable` → proceed specless; plan.md frontmatter gets `work_type: deliverable`. No spec involvement.
- `ambiguous` → `AskUserQuestion` BLOCKING (ONE question: "Is this a product feature or a one-off
  deliverable?"). Resolve, then re-route as `feature` or `deliverable`.
- `feature` → Spec Layer Check (see `references/research-phase.md`):
  - **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). In single-lang mode (the common case) all paths below are correct as-is.
  - Spec exists in `docs/features/` AND no changes intended → planner writes `spec:` (the promoted <!-- layout-exempt: detection check; docs/ root single-lang per mode-aware pointer above -->
    path; planner references it, no draft authored).
  - Spec exists but this plan REVISES it → choice (a): author a NEW draft to the plan dir tied to
    the existing `F###` → `spec_draft:`. Promote overwrites docs/ at implement-start.
  - Spec absent → BLOCKING `AskUserQuestion` with 3 choices:
    - **(a) "Author spec first" [Recommended]** → run the shared procedure
      `claude/skills/rebuild-spec/references/spec-stage-procedure.md` in full (authors the draft
      to `plans/<plan_dir>/spec/<slug>/`, NO `F###`, NO docs/ write). Continue planning
      referencing the draft; plan.md gets `spec_draft: plans/<plan_dir>/spec/<slug>/`. `F###` +
      docs/ promotion happen later when `/tkm:takumi <plan>` begins (code-discipline Stage 0
      promote step).
    - **(b) "Waive — plan specless"** → plan.md frontmatter gets
      `spec_waived: "<user's exact words, verbatim>"`. No `F###` reservation.
    - **(c) "Switch to /tkm:takumi"** → abort `create-plan`; emit ready-to-run command:
      `/tkm:takumi "<original task>"`. Stop here.
