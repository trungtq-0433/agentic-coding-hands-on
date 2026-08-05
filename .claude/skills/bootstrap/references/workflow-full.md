# Full Interactive Workflow (`--full`)

**Thinking level:** Ultrathink
**User gates:** Nothing advances past a major phase until the user signs off.

## Step 1: Clarify Requirements

Lean on `AskUserQuestion` to draw out the real request, the constraints, the goal underneath the goal.
- One question at a time — wait for the answer before the next
- Take nothing for granted; ask
- Push back on assumptions — the best answer rarely matches the first sketch
- Keep at it until the requirements are airtight

## Step 2: Research

Fan out several `researcher` subagents at once:
- Test whether the request holds up, name the hard parts, weigh the strongest solutions
- Cap each report at 150 lines

**Gate:** Lay the findings before the user. Move on only once they approve.

## Step 3: Tech Stack

1. Ask the user what stack they favor. If they name one, jump to step 4.
2. Set `planner` and several `researcher` subagents loose in parallel to find the best fit
3. Lay out 2–3 options with their pros and cons through `AskUserQuestion`
4. Write the chosen stack into `./docs`

**Gate:** The stack is locked only when the user approves it.

## Step 4: Wireframe & Design

1. Ask the user whether they want wireframes/design. If not → skip to Step 5.
2. Run `ui-ux-designer` alongside `researcher` subagents in parallel:
   - Dig into style, trends, fonts (name an actual Google Fonts face, not the reflexive Inter/Poppins), colors, spacing, positions
3. `ui-ux-designer` produces:
   - Design guidelines at `./docs/design-guidelines.md`
   - HTML wireframes under `./docs/wireframe/`
4. No logo on hand? Drop in a placeholder or a real/provided asset
5. Capture the wireframes via `tkm:automate-browser` → store them in `./docs/wireframes/`

**Gate:** The user approves the design. Rejected? Iterate.

**Image tools:** Read tool for image analysis.

## Step 5: Planning

Fire up the **tkm:create-plan** skill: `/tkm:create-plan --hard <requirements>`
- The planner lays out a directory per the `## Naming` pattern
- Overview at `plan.md` (<80 lines) plus the `phase-XX-*.md` files
- Walk the user through the plan's pros and cons

**Gate:** The user approves the plan. DO NOT touch implementation before that.

## Step 6: Implementation → Final Report

Load `references/shared-phases.md` for the phases that remain.

Fire up the **tkm:takumi** skill: `/tkm:takumi <plan-path>` (interactive mode — a review gate at every step)
