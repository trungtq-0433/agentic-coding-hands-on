# MoMorph Development Rules

> **Requires extras kit.** The `momorph-implement-design` skill referenced throughout this document ships in the `extras` kit, not base. Install with `tkm init --kit extras`.

## Critical Rules

1. **NEVER guess visual values** — MCP design data is authoritative
2. **NEVER skip clarification** — after fetching specs/test cases, MUST analyze for gaps and confirm with user before planning
3. **NEVER proceed without user confirmation** — present ambiguities interactively, wait for ALL answers
4. **`clarifications.md`** in plan directory holds prior decisions — authoritative, do not re-ask resolved items

## Parallel Execution Strategy

**OVERRIDE: This section modifies both `tkm:takumi` and `tkm:create-plan` workflows.** When MoMorph context is detected. This section is the **full protocol**.

The two-track structure (A = UI, B = backend/logic) applies the same way to both commands; only the execution differs:

- **`tkm:takumi` (implementation):** physically run both tracks concurrently — actually spawn UI subagents (Track A) and start backend implementation (Track B) at the same time. Track A and Track B never block each other.
- **`tkm:create-plan` (planning only):** **DO NOT spawn** UI subagents. Instead, represent the same two-track shape in the generated plan: Track A becomes one phase per screen, Track B becomes the chained backend/logic phases, and `blocks`/`blockedBy` between Track A and Track B is forbidden (they must be parallel-runnable when `tkm:takumi` later executes the plan). Cross-track integration goes into a dedicated integration phase near the end. Implementation work itself is deferred until the user runs `tkm:takumi`.
   - Track A phase files MUST stay minimal (≤ 30 lines): only screen refs, one-line goal, out-of-scope list, optional integration contract — `momorph-implement-design` handles the rest at runtime.

After fetching specs and test cases (Clarification Protocol step 2), the orchestrator treats both tracks as **concurrently runnable** — nothing blocks anything else. In `tkm:takumi` this means real parallel execution; in `tkm:create-plan` this means the plan's phase graph keeps Track A and Track B independent.

### Track A — UI Implementation (background `implementer` subagents)

Spawn **one background subagent per screen** via `Agent(subagent_type="implementer", run_in_background=true)`. All screen agents run in parallel.

Each subagent:

1. Activates `momorph-implement-design` skill to code that screen's UI from Figma design
2. Extracts **mock data directly from Figma design** (text content, placeholder images, sample values visible in the design) — no invented data
3. Wires up static/presentational components with mock data props
4. Runs visual validation loop (Step 7 of `momorph-implement-design` skill)
5. Reports back with: files created, component tree, data interfaces/props expected by each component

**Multi-screen rule:** If user requests N screens → spawn N independent background agents. Each agent owns one screen. No shared state between UI agents.

**Subagent prompt MUST include:** MoMorph URL, fileKey, screenId, project conventions path, and explicit instruction: "Use Figma design content as mock data source. Do NOT invent data."

### Track B — Clarification + Planning + Backend Implementation (orchestrator, main thread)

Orchestrator proceeds through the **full pipeline** without waiting for Track A:

1. Clarification Protocol (steps 3–6 below) — resolve specs gaps
2. Plan backend/behavior logic — API contracts, data models, state management
3. **Start implementing backend logic immediately** — do NOT wait for UI agents to finish

Focus areas for planning and implementation:

- Backend API contracts, data models, business logic
- Behavior logic: validation, state transitions, error handling, navigation
- Integration points: auth, third-party services, real data sources
- Gaps between specs/test cases that affect backend, not UI layout

### Integration (no hard merge point)

Track A agents complete asynchronously. As each finishes:

1. Orchestrator receives notification of completion
2. Reviews UI output (files, component interfaces, data props)
3. Integrates backend logic with UI — replaces mock data with real API calls, wires event handlers, connects state management
4. If backend implementation already done for that screen → integration phase starts immediately
5. If backend still in progress → integration happens when backend for that screen completes

**There is NO blocking merge point.** Both tracks run freely. Integration happens incrementally as outputs become available.

---

## Clarification Protocol

This is the **primary gate**. No backend planning begins without completed clarification.

1. Resolve `fileKey` and `screenId` from user input (URL, frame name, or ask). For multiple screens, collect all identifiers.
2. Fetch in parallel per screen: `get_frame(screenId)` + `download_specs(screen_id, "csv")` + `download_test_cases(screen_id, "csv")` → then **immediately spawn Track A (one UI background subagent per screen)**
3. **Deep-read** every row of specs AND test cases. Summarize: what screen does, components, user flows
4. **Cross-reference** specs vs test cases. Scan for gaps in: error states, navigation/redirects, state persistence, empty/loading/edge states, validation rules, third-party integration, responsive, accessibility, localization, security
5. **Present all gaps** as numbered questions grouped by priority (Blocking → Important → Nice-to-have). Clarifying question via AskUserQuestion. Per question: list 2-4 options, mark one [Recommended] with reasoning. If answers reveal new ambiguities, ask follow-up questions. Keep asking until all gaps are resolved.
6. Write decisions to `clarifications.md` in plan directory. **Strict format** — one line per decision: `- Q: [question] → A: [answer]`, grouped under `## Session [date]`. Follow template: `.claude/templates/plans/clarifications.md`. No custom sections, no nested bullets, no multi-line answers.
