# Shared Phases (All Modes)

The tail of every run looks the same: once the plan exists and the takumi skill takes over, these phases play out.
Takumi owns the heavy lifting — what follows is just the bootstrap-flavored guidance layered on top.

## Implementation

Owned by the **tkm:takumi** skill. The bootstrap-specific bits:
- Work the `./plans` plan from the main agent, one step at a time
- Lean on the `ui-ux-designer` subagent for frontend, following `./docs/design-guidelines.md`
- For assets, work from the real/provided files and read them with the Read tool — never fabricate
- Type-check and compile at the close of each phase

## Testing

Owned by the **tkm:takumi** skill. The bootstrap-specific bits:
- Tests must be genuine — no fake data, no mocks, no shortcuts, no placeholder solutions
- The `tester` subagent runs the suite and reports back to the main agent
- On a failure: `debugger` subagent → fix → run again until the suite is green
- A red suite is never something to wave through to satisfy the build or CI

## Code Review

Owned by the **tkm:takumi** skill. The bootstrap-specific bits:
- The `reviewer` subagent reads the code
- Anything critical: fix it, retest, and loop back
- Once the suite passes and the review is done, summarize for the user

## Documentation

Once review clears, send the `doc-writer` subagent in to write or refresh:
- `./docs/README.md` (≤300 lines)
- `./docs/codebase-summary.md`
- `./docs/project-overview-pdr.md` (Product Development Requirements)
- `./docs/code-standards.md`
- `./docs/system-architecture.md` <!-- layout-exempt: manage-docs narrative carve-out — stays at docs/ root in all modes -->

Then the `project-manager` subagent handles:
- `./docs/project-roadmap.md`
- Marking the plan and its phases as complete

## Onboarding

Walk the user into their own project:
- One question at a time — wait for the answer before moving on
- For instance: tell them to fetch an API key → collect it → drop it into the env vars
- Should they want config tweaks, loop until they sign off

## Final Report

1. Recap every change, each with a short note on what it did
2. Show the user how to get rolling and point at sensible next steps
3. Check whether they want to commit/push:
   - If so: `git-manager` subagent commits (and pushes when asked)
   - `--fast` mode: commit automatically (no push), no prompt

**Report rules:**
- Trade grammar for brevity
- End with any open questions
