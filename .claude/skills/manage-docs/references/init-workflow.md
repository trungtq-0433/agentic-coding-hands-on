# Init Workflow

## Phase 1: Parallel Codebase Scouting

1. Walk the tree and tally file counts and LOC per directory. Leave out anything that is credentials, build cache, or third-party code — `.claude`, `.opencode`, `.git`, `tests`, `node_modules`, `__pycache__`, `secrets`, and their kin.
2. Aim only at directories **that are really there** — read the project's actual shape rather than assuming a fixed set of paths.
3. Hand the exploration to the `tkm:scan-codebase` skill; it surveys the code and reports detailed summaries back to the main agent.
4. Fold those scout reports into a single context summary.

## Phase 2: Documentation Creation (doc-writer Agent)

**CRITICAL:** Spawn the `doc-writer` agent through the Task tool, carrying the merged reports. Don't pause for user input first.

Feed the assembled context to the doc-writer agent so it can lay down the first set of docs:
- `README.md`: seed the README with starting documentation (hold it under 300 lines)
- `docs/project-overview-pdr.md`: the project overview and PDR (Product Development Requirements)
- `docs/codebase-summary.md`: a summary of the codebase
- `docs/code-standards.md`: how the code is laid out and the standards it follows
- `docs/system-architecture.md`: the system architecture <!-- layout-exempt: manage-docs carve-out — stays at docs/ root in all modes -->
- `docs/project-roadmap.md`: the project roadmap
- `docs/deployment-guide.md` [optional]: how to deploy
- `docs/design-guidelines.md` [optional]: the design guidelines

## Phase 3: Size Check (Post-Generation)

Once doc-writer has finished:
1. Measure line counts with `wc -l docs/*.md 2>/dev/null | sort -rn`
2. Read `docs.maxLoc` off the session context (it falls back to 800)
3. Where a file runs past the ceiling:
   - Name which files overran, and by how many lines
   - doc-writer ought to have split those ahead of time
   - If one is still too long, put the call to the user: split it now, or keep it as-is?

## Note on the spec layer (v4.0.0+)

<!-- layout-exempt: spec layer note references docs/ root paths as definitional layer names -->
`init` deliberately leaves the spec layer alone. That machine-generated layer — `docs/system/`, `docs/generated/`, `docs/features/`, `docs/flows/` — comes from `/tkm:rebuild-spec`, run later once the codebase has enough measurable surface (routes, models, screens) to be worth describing. Should a spec layer (or an older `docs/specs/` tree) already sit there when `init` runs, don't touch it. The layered model is spelled out in `claude/skills/_shared/docs-canonical-mapping.md`.
