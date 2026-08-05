# Reporting Patterns

## Report Types

### 1. Session Status Report

A fast read on what the current session moved.

```markdown
## Session Report: [Date]

### Work Completed
- [x] [Task/feature description]
- [x] [Task/feature description]

### In Progress
- [ ] [Task description] — [% complete, blocker if any]

### Tasks Created
- [N] tasks hydrated from [plan]
- [M] completed, [K] remaining

### Next Session
1. [Priority item]
2. [Follow-up item]
```

### 2. Plan Completion Report

The full account, written when a plan crosses the finish line.

```markdown
## Plan Complete: [Plan Name]

### Summary
- **Duration:** [start] → [end]
- **Phases:** [N] completed
- **Files changed:** [count]
- **Tests:** [pass/total]

### Achievements
- [Feature/capability delivered]

### Known Limitations
- [Any caveats or future work needed]

### Documentation Updates
- [Which docs were updated]
```

### 3. Progress Report (Multi-Plan)

A single view spanning every plan still in motion.

```markdown
## Project Progress: [Date]

| Plan | Status | Progress | Priority | Next Action |
|------|--------|----------|----------|-------------|
| [name] | [status] | [%] | P[N] | [action] |

### Highlights
- [Key achievement or milestone]

### Risks
- [Risk] — [Mitigation]

### Blockers
- [Blocker] — [Resolution path]
```

## Report Naming

Follow the pattern the hooks inject under `## Naming`:
`{reports-path}/pm-{date}-{time}-{slug}.md`

Example: `plans/reports/pm-260205-2221-auth-progress.md`

## Report Generation Workflow

1. `TaskList()` → pull the status of every task
2. Glob `./plans/*/plan.md` → sweep the live plans
3. Read the phase files → tally the checkboxes
4. Pour the metrics into the report template
5. Write it out to the reports directory
6. Surface the things that matter: wins, blockers, risks, what's next

## Concision Rules

- Trade grammar for brevity
- Reach for a table before a paragraph
- Leave unresolved questions for the end
- Numbers over prose — counts and percentages carry more
- Drop the context everyone already has; keep what someone can act on
