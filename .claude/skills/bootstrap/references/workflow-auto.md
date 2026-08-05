# Auto Workflow (`--auto`) — Default

**Thinking level:** Ultrathink
**User gates:** The design sign-off is the only checkpoint; everything else runs on its own.

## Step 1: Research

Fan out several `researcher` subagents at once:
- Pressure-test the request, sanity-check the idea, surface the hard parts, weigh the strongest solutions
- Cap each report at 150 lines

No checkpoint here — keep moving.

## Step 2: Tech Stack

1. Put `planner` and a handful of `researcher` subagents to work in parallel on the best-fit stack
2. Record the stack under `./docs`

No checkpoint — pick the strongest option and carry on.

## Step 3: Wireframe & Design

1. Run `ui-ux-designer` alongside `researcher` subagents in parallel:
   - Dig into style, trends, fonts (name an actual Google Fonts face, not the reflexive Inter/Poppins), colors, spacing, positions
2. `ui-ux-designer` produces:
   - Design guidelines at `./docs/design-guidelines.md`
   - HTML wireframes under `./docs/wireframe/`
3. No logo on hand? Drop in a placeholder or a real/provided asset
4. Capture the wireframes via `tkm:automate-browser` → store them in `./docs/wireframes/`

**Gate:** Put the design in front of the user for approval. Rejected? Iterate.

**Image tools:** Read tool for image analysis.

## Step 4: Planning

Fire up the **tkm:create-plan** skill: `/tkm:create-plan --auto <requirements>`
- The planning skill reads the complexity and chooses the right mode itself
- Spins up the plan directory per the `## Naming` pattern
- Overview at `plan.md` (<80 lines) plus the `phase-XX-*.md` files

No checkpoint — roll straight into implementation.

## Step 5: Implementation → Final Report

Load `references/shared-phases.md` for the phases that remain.

Fire up the **tkm:takumi** skill: `/tkm:takumi --auto <plan-path>`
- Bypasses every review gate
- Auto-approves when the score hits 9.5+ with zero critical issues
- Drives through all phases without pausing
