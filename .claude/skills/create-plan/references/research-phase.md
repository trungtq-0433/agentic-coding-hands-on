# Research & Analysis Phase

**When to skip:** Already holding researcher reports? Skip this phase.

## Core Activities

### Parallel Researcher Agents
- Fan out several `researcher` agents at once, each chasing a different approach
- Let them all report back before you move on
- Give each researcher one specific angle or approach to dig into

### Sequential Thinking
- Pull in the `tkm:think-sequential` skill for problem-solving that loops back on itself
- A structured way to reason through tangled analysis
- Lets you reason in steps and revise as you learn

### Documentation Research
- Use the `tkm:search-docs` skill to read and absorb the docs
- Dig into the plugins, packages, and frameworks in play
- Reach the latest technical docs through the llms.txt standard

### GitHub Analysis
- Use the `gh` command to read and work through:
  - GitHub Actions logs
  - Pull requests
  - Issues and discussions
- Mine those for the technical context that matters

### Remote Repository Analysis
Handed a GitHub repository URL, build a fresh codebase summary:
```bash
# usage: 
repomix --remote <github-repo-url>
# example: 
repomix --remote https://github.com/modelcontextprotocol/servers
```

### Debugger Delegation
- Hand root-cause work to the `debugger` agent
- Reach for it when the issue or bug is genuinely knotty
- Diagnostics are the debugger agent's home turf

## Spec Layer Check (Step 3/4)

Before spawning researchers or after collecting study reports, check whether the project already has
a spec layer for the feature being planned.

> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). The commands below use `docs/` root which is correct for single-lang mode (the common case).

```bash
ls docs/features/ 2>/dev/null  # layout-exempt: detection command; docs/ root single-lang per pointer above
```

- If `docs/features/F###_*/` exists (a PROMOTED spec) for the relevant feature AND it is not being <!-- layout-exempt: detection logic; docs/ root single-lang per pointer above -->
  revised → the planner writes `spec: docs/features/F###_Slug/` and references its FR/SC/US IDs directly.
  If it IS being revised → step 1d choice (a) authors a NEW draft to the plan dir tied to the existing
  `F###` → `spec_draft: plans/<plan_dir>/spec/<slug>/` (promote overwrites docs/ at implement-start).
- When a draft or promoted spec is available, instruct the planner: **skip re-deriving requirements
  already captured** — read the FR/SC/US IDs directly and reference them in phase files.
- If no spec layer exists:
  - `work_type: feature` → the SKILL.md step 1d blocking gate applies. This path is never reached
    silently — the gate fires BEFORE research and presents the 3-option choice (a/b/c) to the user.
    Do NOT proceed specless for feature-class work without an explicit waiver. Choice (a) authors a
    draft → `spec_draft:`; `F###` is allocated only at promote (implement-start), never here.
  - `work_type: deliverable` → proceed specless with `work_type: deliverable` in plan.md frontmatter;
    no spec, no `F###` reservation.

## Best Practices

- Go wide before you go deep
- Write findings down so the synthesis phase has something to chew on
- Surface more than one approach so there's something to compare
- Keep edge cases in mind while you research, not after
- Flag the security implications early, not at the end
