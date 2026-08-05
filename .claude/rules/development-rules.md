# Development Rules

**IMPORTANT:** Read the skills catalog and turn on whatever skills the work in front of you calls for.
**IMPORTANT:** Three principles ride along on every change: **YAGNI (You Aren't Gonna Need It) — KISS (Keep It Simple, Stupid) — DRY (Don't Repeat Yourself)**.
**IMPORTANT:** The craftsman disposition behind these rules — voice, the Study→Deliver flow, Iron Laws, confidence taxonomy — lives in `.claude/ethos/ETHOS.md`. Read it when an artifact's voice or judgment is in question.

## General
- **File Naming**: Name files in kebab-case, and let the name say plainly what the file is for. Length is fine — a long, self-describing name pays off the moment an LLM scans the tree with Grep or similar and grasps the purpose without opening the file.
- **File Size Management**: Hold each code file under 200 lines so context stays manageable.
  - Break oversized files into smaller, single-purpose modules or components.
  - Reach for composition over inheritance when a widget grows complicated.
  - Pull utility functions out into their own modules.
  - Give business logic its own dedicated service classes.
- Need current library docs? Turn on the `tkm:search-docs` skill (it sits on top of `context7`) to pull the latest.
- Reach for the `gh` bash command when you need to drive GitHub.
- Reach for the `psql` bash command when debugging means querying a Postgres database.
- Use the built-in Read tool to open and describe images, screenshots, and documents directly when that helps.
- Lean on the `tkm:think-sequential` and `tkm:debug-code` skills for step-by-step reasoning, code analysis, and debugging when the task warrants it.
- **[IMPORTANT]** Honor the codebase structure and code standards documented in `./docs` as you build.
- **[IMPORTANT]** Write the real implementation — never fake it or stub it out as a stand-in.

## Code Quality Guidelines
- Read `./docs` for codebase structure and code standards, and follow them.
- Don't be a zealot about lint, but **leave no syntax errors — the code must compile**.
- Favor working, readable code over rigid style policing and formatting fussiness.
- Apply sensible quality bars — the kind that keep developers productive, not bogged down.
- Wrap risky paths in try/catch and keep security standards in view.
- Hand finished work to the `reviewer` agent after every implementation.

## Pre-commit/Push Rules
- Lint before you commit.
- Run the tests before you push — and DO NOT wave through failing tests just to make the build or GitHub Actions green.
- Keep each commit scoped to the actual code change.
- **DO NOT** commit or push secrets of any kind (dotenv files, API keys, database credentials, and the like) to the repository.
- Write clean, professional commit messages in conventional-commit form, with no AI references.

## Code Implementation
- Write code that is clean, readable, and easy to maintain.
- Stay within the architectural patterns already in place.
- Build features to spec.
- Account for edge cases and error paths.
- **DO NOT** spin up new "enhanced" copies of files — edit the existing files in place.

## Visual Aids
- Reach for `/tkm:preview-output --explain` when walking through an unfamiliar pattern or tangled logic.
- Reach for `/tkm:preview-output --diagram` for architecture diagrams and data-flow pictures.
- Reach for `/tkm:preview-output --slides` for step-by-step walkthroughs and presentations.
- Reach for `/tkm:preview-output --ascii` for terminal-friendly diagrams (no browser needed to follow them).
- Append `--html` to any generation flag for a self-contained HTML file that opens in the browser with no server.
- **Plan context:** the active plan comes from the `## Plan Context` block injected by the hook; visuals land in `{plan_dir}/visuals/`.
- With no active plan, fall back to the `plans/visuals/` directory.
- For Mermaid diagrams, the `/mermaidjs-v11` skill carries the v11 syntax rules.
- For how this folds into the larger flow, see `primary-workflow.md` → Step 6.
