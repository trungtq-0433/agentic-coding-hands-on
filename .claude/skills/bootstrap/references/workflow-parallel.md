# Parallel Workflow (`--parallel`)

**Thinking level:** Ultrathink parallel
**User gates:** The design sign-off is the only checkpoint; implementation fans out across multiple agents at once.

## Step 1: Research

Launch at most 2 `researcher` agents side by side:
- Map the requirements, validate them, name the hard parts, weigh solutions
- Hold reports to 150 lines or under

No checkpoint — keep moving.

## Step 2: Tech Stack

Set `planner` and several `researcher` agents loose in parallel on the best-fit stack.
Write it into `./docs` (≤150 lines).

No checkpoint — keep moving.

## Step 3: Wireframe & Design

1. Run `ui-ux-designer` alongside `researcher` agents in parallel:
   - Dig into style, trends, fonts, colors, spacing, positions
   - Name an actual Google Fonts face (not the reflexive Inter/Poppins)
2. `ui-ux-designer` produces:
   - Design guidelines at `./docs/design-guidelines.md`
   - HTML wireframes under `./docs/wireframe/`
3. No logo? Drop in a placeholder or a real/provided asset
4. Capture it via `tkm:automate-browser` → store in `./docs/wireframes/`

**Gate:** Put the design in front of the user for approval. Rejected? Iterate.

**Image tools:** Read tool for image analysis.

## Step 4: Parallel Planning

Fire up the **tkm:create-plan** skill: `/tkm:create-plan --parallel <requirements>`
- Carves phases so each one **owns its files outright** — no two phases touch the same file
- **Dependency matrix**: spells out which phases can run together and which must wait
- `plan.md` carries the dependency graph, the execution strategy, and the file-ownership matrix
- Task hydration wires `addBlockedBy` for the sequential links and leaves the parallel groups unblocked

No checkpoint — roll into implementation.

## Step 5: Parallel Implementation → Final Report

Load `references/shared-phases.md` for the phases that remain.

Fire up the **tkm:takumi** skill: `/tkm:takumi --parallel <plan-path>`
- Read `plan.md` for the dependency graph and execution strategy
- Fire off several `implementer` agents in PARALLEL for the phases that can overlap
  - Hand each one: its phase file path and the environment info
- Use `ui-ux-designer` for frontend (read assets with the Read tool)
- Stay inside the file-ownership lines
- Type-check once implementation lands

Takumi then carries testing, review, docs, onboarding, and the final report per `shared-phases.md`.
