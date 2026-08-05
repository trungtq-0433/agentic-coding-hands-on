# Primary Workflow

**IMPORTANT:** Read the skills catalog and turn on whatever skills the work in front of you calls for.
**IMPORTANT**: Spend tokens like they cost something — stay efficient without dropping quality.

#### 1. Code Implementation
- Open with the `planner` agent: have it lay out an implementation plan with TODO tasks under `./plans`.
- During planning, run several `researcher` agents in parallel — each digs into a different technical topic, then reports back to `planner` to feed the plan.
- Write code that is clean, readable, and easy to maintain.
- Stay within the architectural patterns already in place.
- Build features to spec.
- Account for edge cases and error paths.
- **DO NOT** spin up new "enhanced" copies of files — edit the existing files in place.
- **[IMPORTANT]** After you create or change a code file, run the compile command/script to catch compile errors early.

#### 2. Testing
- Hand the **simplified code** to the `tester` agent to exercise.
  - Write thorough unit tests.
  - Push coverage high.
  - Exercise the error paths.
  - Check that performance requirements hold.
- Tests run against the FINAL code — the same code that gets reviewed and merged.
- **DO NOT** look past failing tests just to make the build pass.
- **IMPORTANT:** no fake data, mocks, cheats, tricks, or stopgaps slipped in to fake a green build or pass GitHub Actions.
- **IMPORTANT:** When tests fail, fix them by the recommendations and send them back to the `tester` agent for another run. Only close out the session once everything passes.

#### 3. Code Quality
- Once tests pass, hand the clean, tested code to the `reviewer` agent.
- Hold to the coding standards and conventions.
- Write code that documents itself.
- Comment the parts where the logic is genuinely intricate.
- Tune for performance and maintainability.

#### 4. Integration
- Follow the plan the `planner` agent produced.
- Make the new code sit cleanly inside what is already there.
- Honor the API contracts exactly.
- Keep backward compatibility intact.
- Document any breaking changes.
- When docs need it, hand off to the `doc-writer` agent to update `./docs`.

#### 5. Debugging
- When a user reports a bug or a server/CI-CD failure, hand it to the `debugger` agent to run tests and produce a summary report.
- Read that summary from the `debugger` agent and implement the fix.
- Send the result to the `tester` agent to run tests and report back.
- If the `tester` agent flags failing tests, fix them by the recommendations and loop back to **Step 3**.

#### 6. Visual Explanations
When you need to make complex code, a protocol, or an architecture click:
- **When to use:** the user says "explain", "how does X work", or "visualize", or the topic has 3+ pieces interacting.
- `/tkm:preview-output --explain <topic>` for a visual explanation built from ASCII + Mermaid.
- `/tkm:preview-output --diagram <topic>` for architecture and data-flow diagrams.
- `/tkm:preview-output --slides <topic>` for step-by-step walkthroughs.
- `/tkm:preview-output --ascii <topic>` for terminal-only output.
- **HTML mode** (add `--html` for self-contained HTML pages that open straight in the browser):
  - `/tkm:preview-output --html --explain <topic>` — publication-quality HTML explanation
  - `/tkm:preview-output --html --diagram <topic>` — interactive HTML diagram with zoom controls
  - `/tkm:preview-output --html --slides <topic>` — magazine-quality slide deck
  - `/tkm:preview-output --html --diff [ref]` — visual diff review
  - `/tkm:preview-output --html --plan-review` — plan vs codebase comparison
  - `/tkm:preview-output --html --recap [timeframe]` — project context snapshot
- **Plan context:** visuals land in the plan folder named by the `## Plan Context` hook injection; with none, they go to `plans/visuals/`.
- **Markdown mode:** opens automatically in the browser via markdown-novel-viewer, Mermaid rendered.
- **HTML mode:** opens straight in the browser — self-contained, no server.
- For more on this, see `development-rules.md` → "Visual Aids".
