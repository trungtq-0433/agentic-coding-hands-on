# Fast Workflow (`--fast`)

**Thinking level:** Think hard
**User gates:** None — it runs hands-off from open to close.

## Step 1: Combined Research & Planning

Research runs all at once, then pours into planning:

**Parallel research batch** (launch these together):
- 2 `researcher` subagents (max 5 sources each): probe the request, validate the idea, surface solutions
- 2 `researcher` subagents (max 5 sources each): hunt for the best-fit tech stack
- 2 `researcher` subagents (max 5 sources each): study design style, trends, fonts, colors, spacing, positions
  - Name an actual Google Fonts face (not the reflexive Inter/Poppins)

Hold every report to 150 lines or under.

## Step 2: Design

1. The `ui-ux-designer` subagent digests the research and produces:
   - Design guidelines at `./docs/design-guidelines.md`
   - HTML wireframes under `./docs/wireframe/`
2. No logo on hand? Drop in a placeholder or a real/provided asset
3. Capture the wireframes via `tkm:automate-browser` → store them in `./docs/wireframes/`

**Image tools:** Read tool for image analysis.

No checkpoint — go straight on.

## Step 3: Planning

Fire up the **tkm:create-plan** skill: `/tkm:create-plan --fast <requirements>`
- Skip research — it is already in hand from above
- Read the codebase docs and write the plan directly
- Plan directory follows the `## Naming` pattern
- Overview at `plan.md` (<80 lines) plus the `phase-XX-*.md` files

No checkpoint — roll into implementation.

## Step 4: Implementation → Final Report

Load `references/shared-phases.md` for the phases that remain.

Fire up the **tkm:takumi** skill: `/tkm:takumi --auto <plan-path>`
- Bypasses every review gate (fast planning earns fast execution)
- Auto-approves when the score hits 9.5+ with zero critical issues
- Drives through all phases without pausing

**Note:** In fast mode, `git-manager` auto-commits (no push) once everything is done.
