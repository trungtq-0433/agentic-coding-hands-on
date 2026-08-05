# Plan Creation & Organization

## Directory Structure

### Plan Location

Take the path from `Plan dir:` in the `## Naming` section the hooks inject — it's already fully computed for you.

**Example:** `plans/251101-1505-authentication/` or `ai_docs/feature/MRR-1453/`

### File Organization

IN CURRENT WORKING PROJECT DIRECTORY:
```
{plan-dir}/                                    # From `Plan dir:` in ## Naming
├── research/
│   ├── researcher-XX-report.md
│   └── ...
├── reports/
│   ├── scout-report.md
│   ├── researcher-report.md
│   └── ...
├── plan.md                                    # Overview access point
├── phase-01-setup-environment.md              # Setup environment
├── phase-02-implement-database.md             # Database models
├── phase-03-implement-api-endpoints.md        # API endpoints
├── phase-04-implement-ui-components.md        # UI components
├── phase-05-implement-authentication.md       # Auth & authorization
├── phase-06-implement-profile.md              # Profile page
└── phase-07-write-tests.md                    # Tests
```

### Task Hydration

Once plan.md and the phase files exist, hydrate tasks (unless `--no-tasks`):
1. TaskCreate per phase, chained with `addBlockedBy`
2. Add separate tasks for the high-risk steps
3. The patterns and the takumi handoff protocol are in `task-management.md`

### Active Plan State Tracking

SKILL.md's "Active Plan State" section holds the full rules. The gist:
- Read the active/suggested/none state from the `## Plan Context` the hooks inject
- After the plan is created: `node .claude/scripts/set-active-plan.cjs {plan-dir}`
- An active plan writes to its own reports path; a suggested one falls back to the default

## Plan Creation via CLI

Once research and design have settled the phases:

1. **Scaffold via CLI:**
   ```bash
   tkm plan create \
     --title "{plan title}" \
     --phases "{Phase1},{Phase2},{Phase3}" \
     --dir {plan-dir} \
     --priority {P1|P2|P3} \
     [--issue {N}]
   ```

2. **Fill content sections** in plan.md via Edit tool:
   - `## Overview` — brief description
   - `## Dependencies` — cross-plan dependencies

3. **Fill each phase-XX.md** with:
   - Architecture, implementation steps, success criteria
   - Requirements, risk assessment, security considerations

4. **NEVER edit the Phases table directly** — the CLI owns it.
   For structural changes, go through `tkm plan check/uncheck/add-phase`.

**Fallback:** When the `tkm` CLI isn't around (say the user never installed it),
write plan.md by hand in the canonical 3-column format.

## File Structure

### Overview Plan (plan.md)

**IMPORTANT:** Every plan.md MUST carry YAML frontmatter — the schema lives in `output-standards.md`.

**Example plan.md structure:**
```markdown
---
title: "Feature Implementation Plan"
description: "Add user authentication with OAuth2 support"
status: pending
priority: P1
effort: 8h
issue: 123
branch: kai/feat/oauth-auth
tags: [auth, backend, security]
blockedBy: []
blocks: [260115-0900-user-dashboard]
work_type: feature                   # optional — feature | deliverable (step 1d gate)
# Choose AT MOST ONE of the next three lines — never two (mutually exclusive):
spec_draft: plans/260115-1430-auth/spec/user-auth/   # optional — plan-dir draft (gate choice a); promote repoints to spec:
# spec: docs/features/F042_UserAuth/  # optional — a PROMOTED, unrevised spec (or set by takumi promote)  # layout-exempt: schema example; docs/ root single-lang
# spec_waived: "user's words"        # optional — verbatim; ONLY when spec was waived (gate choice b)
created: 2025-12-16
---

# Feature Implementation Plan

## Overview

Brief description of what this plan accomplishes.

## Cross-Plan Dependencies

| Relationship | Plan | Status |
|-------------|------|--------|
| Blocks | [260115-0900-user-dashboard](../260115-0900-user-dashboard/plan.md) | pending |

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Setup Environment](./phase-01-setup.md) | Pending |
| 2 | [Core Implementation](./phase-02-impl.md) | Pending |
| 3 | [Testing & Validation](./phase-03-test.md) | Pending |

<!-- IMPORTANT: Link text MUST be human-readable names (not filenames).
     Bad:  [phase-01-setup.md](./phase-01-setup.md)
     Good: [Setup Environment](./phase-01-setup.md) -->

## Dependencies

- List key dependencies here
```

**Guidelines:**
- Stay high-level and under 80 lines
- Show every phase with its status/progress
- Link out to the detailed phase files
- Name the key dependencies

### Phase Files (phase-XX-name.md)
Hold to the `./claude/rules/development-rules.md` file throughout.
Each phase file carries:

**Context Links**
- Links to related reports, files, documentation

**Overview**
- Priority
- Current status
- Brief description

**Key Insights**
- Important findings from research
- Critical considerations

**Requirements**
- Functional requirements
- Non-functional requirements

**Architecture**
- System design
- Component interactions
- Data flow

**Related Code Files**
- List of files to modify
- List of files to create
- List of files to delete

**Related Spec IDs** *(optional — include only when `plan.md` has a `spec:` field)*
- List the FR/SC/US IDs from the spec that this phase implements.
  Example: `FR-001 (user login)`, `SC-002 (session timeout)`, `US001 (auth flow)`
- Specless plans omit this subsection entirely — backwards compatible.

**Implementation Steps**
- Detailed, numbered steps
- Specific instructions

**Todo List**
- Checkbox list for tracking

**Success Criteria**
- Definition of done
- Validation methods

**Risk Assessment**
- Potential issues
- Mitigation strategies

**Security Considerations**
- Auth/authorization
- Data protection

**Next Steps**
- Dependencies
- Follow-up tasks
