# Output Standards & Quality

## Plan File Format

### YAML Frontmatter (Required for plan.md)

All `plan.md` files MUST include YAML frontmatter at the top:

```yaml
---
title: "{Brief plan title}"
description: "{One-sentence summary for card preview}"
status: pending  # pending | in-progress | completed | cancelled
priority: P2     # P1 (High) | P2 (Medium) | P3 (Low)
effort: 4h       # Estimated total effort
issue: 74        # GitHub issue number (if applicable)
branch: kai/feat/feature-name
tags: [frontend, api]  # Category tags
blockedBy: []    # Plan dirs this plan waits on (e.g., [260301-1200-auth-system])
blocks: []       # Plan dirs this plan blocks (e.g., [260228-0900-user-dashboard])
work_type: feature               # Optional — feature | deliverable (set by step 1d gate)
# Choose AT MOST ONE of the next three lines — never two (mutually exclusive):
spec_draft: plans/<plan_dir>/spec/<slug>/  # Optional — a plan-dir draft (gate choice a); promote repoints to spec: at implement-start
# spec: docs/features/F###_slug/  # Optional — a PROMOTED, unrevised spec (or written by takumi promote)  # layout-exempt: schema example; docs/ root single-lang
# spec_waived: "user's words"    # Optional — verbatim; ONLY on gate choice (b)
created: 2025-12-16
---
```

### Auto-Population Rules

As you create a plan, fill these fields for yourself:
- **title**: lift it from the task description
- **description**: the first sentence of the Overview section
- **status**: always `pending` on a fresh plan
- **priority**: whatever the user asked for, or `P2` by default
- **effort**: the phase estimates added up
- **issue**: read it off the branch name or surrounding context
- **branch**: the current git branch (`git branch --show-current`)
- **tags**: infer them from the task's keywords (frontend, backend, api, auth, and so on)
- **blockedBy**: found during the pre-creation scan (`[]` when there's nothing)
- **blocks**: found during the pre-creation scan (`[]` when there's nothing)
- **spec_draft**: set to the plan-dir draft path when a draft was authored (gate choice a, e.g.,
  `plans/<plan_dir>/spec/<slug>/`). The planner writes THIS field, not `spec:`. Promote (takumi
  Stage 0) repoints it to `spec:` at implement-start. Omit when no draft was authored.
- **spec**: written by takumi's promote step; the planner sets it directly ONLY for a PROMOTED,
  unrevised spec already in `docs/features/`. **omit the field entirely** otherwise — never guess. <!-- layout-exempt: docs/ root single-lang; mode-aware pointer in frontmatter-fields.md -->
- **work_type**: set by step 1d gate to `feature` or `deliverable`; omit if not yet classified
- **spec_waived**: set verbatim from user's words when gate choice (b) is selected; mutually exclusive with `spec_draft:`/`spec:`; omit otherwise
- **created**: today, in YYYY-MM-DD form

### Tag Vocabulary (Recommended)

Stick to this set so tags stay consistent:
- **Type**: `feature`, `bugfix`, `refactor`, `docs`, `infra`
- **Domain**: `frontend`, `backend`, `database`, `api`, `auth`
- **Scope**: `critical`, `tech-debt`, `experimental`

### Task Naming Conventions

**subject** (imperative): an action verb plus what it produces, under 60 chars
  Examples: "Setup database migrations", "Implement OAuth2 flow"

**activeForm** (continuous): the subject's present participle
  Examples: "Setting up database", "Implementing OAuth2"

**description**: a sentence or two of concrete deliverables, pointing at the phase file

The full TaskCreate patterns and metadata live in `task-management.md`.

## Task Breakdown

- Break a tangle of requirements into tasks someone can actually pick up and finish
- Each task runs on its own, with its dependencies named outright
- Order them by dependency, then risk, then business value
- Leave no instruction open to interpretation
- Name the exact file paths for every change
- Spell out what "done" looks like for each task

### File Management

For each file the work touches, list:
- Its full path, never relative
- The action (modify/create/delete)
- A line on what's changing
- What other changes it hangs on
- Fully respect the `./claude/rules/development-rules.md` file.

## Workflow Process

1. **Initial Analysis** → read the docs, get your bearings
2. **Research Phase** → fan out researchers, probe the approaches
3. **Synthesis** → read the reports, settle on the best path
4. **Design Phase** → shape the architecture and the implementation
5. **Plan Documentation** → write the whole thing up in Markdown
6. **Review & Refine** → check it's complete, clear, and ready to act on

## Output Requirements

### What Planners Do
- Plan, full stop — no implementation
- Hand back the plan's file path and a summary
- Make the plan carry its own context
- Drop in snippets or pseudocode where they clear things up
- Offer more than one option, with the trade-offs, when it helps
- Fully respect the `./claude/rules/development-rules.md` file.

### Writing Style
**IMPORTANT:** Trade grammar for concision
- Clear beats pretty
- Bullets and lists over paragraphs
- Short sentences
- Cut the dead words
- Lead with what's actionable

### Unresolved Questions
**IMPORTANT:** Close out with `AskUserQuestion` for anything still open
- Things that need clarifying
- Technical calls that need the user's input
- Unknowns that would shape the build
- Trade-offs that are really business decisions
Then fold the answers back into the plan and phases.

## Quality Standards

### Thoroughness
- Specific and complete through research and planning alike
- Account for the edge cases and the failure modes
- Walk the whole user journey
- Write down every assumption

### Maintainability
- Plan for the long maintenance tail
- Leave room for what comes next
- Record why each decision went the way it did
- Resist over-engineering
- Fully respect the `./claude/rules/development-rules.md` file.

### Research Depth
- Unsure? Research harder
- More than one option, each with its trade-offs laid bare
- Check your choices against the established practice
- Keep the industry standards in view

### Security & Performance
- Confront every security concern head-on
- Name the performance costs
- Plan for scale
- Account for the resource limits

### Implementability
- Detailed enough for a junior dev to follow
- Squared against the patterns already here
- Consistent with the codebase's own standards
- Backed by clear examples

**Remember:** A plan is the load-bearing part of the work — get it right and the build follows. Be thorough; leave no corner of the solution unconsidered.
