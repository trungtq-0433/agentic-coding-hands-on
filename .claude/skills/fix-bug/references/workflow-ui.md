# UI Fix Workflow

For mending visual/UI issues. Leans on the design skills. Phases are tracked through native Claude Tasks.

## Required Skills (activate in order)
1. `tkm:design-ui` - Design database (ALWAYS FIRST)
2. `tkm:design-ui` - Design principles
3. `tkm:design-to-code` - Implementation patterns

## Pre-fix Research
```bash
python3 .claude/skills/design-ui/scripts/search.py "<product-type>" --domain product
python3 .claude/skills/design-ui/scripts/search.py "<style>" --domain style
python3 .claude/skills/design-ui/scripts/search.py "accessibility" --domain ux
```

## Task Setup (Before Starting)

```
T1 = TaskCreate(subject="Analyze visual issue",    activeForm="Analyzing visual issue")
T2 = TaskCreate(subject="Implement UI fix",         activeForm="Implementing UI fix",       addBlockedBy=[T1])
T3 = TaskCreate(subject="Verify visually",          activeForm="Verifying visually",         addBlockedBy=[T2])
T4 = TaskCreate(subject="DevTools check",           activeForm="Checking with DevTools",     addBlockedBy=[T3])
T5 = TaskCreate(subject="Test compilation",         activeForm="Testing compilation",        addBlockedBy=[T4])
T6 = TaskCreate(subject="Update design docs",       activeForm="Updating design docs",       addBlockedBy=[T5])
```

## Workflow

### Step 1: Analyze
`TaskUpdate(T1, status="in_progress")`
Study the screenshots with the Read tool (for video, study the supplied frames with the Read tool).

- Read `./docs/design-guidelines.md` first
- Pin down the exact visual discrepancy

`TaskUpdate(T1, status="completed")`

### Step 2: Implement
`TaskUpdate(T2, status="in_progress")`
Use the `ui-ux-designer` agent.

`TaskUpdate(T2, status="completed")`

### Step 3: Verify Visually
`TaskUpdate(T3, status="in_progress")`
Screenshot, then Read-tool analysis.

- Frame the parent container, not the whole page
- Hold it against the design guidelines
- If it's off → leave T3 `in_progress` and drop back to Step 2

`TaskUpdate(T3, status="completed")`

### Step 4: DevTools Check
`TaskUpdate(T4, status="in_progress")`
Use the `tkm:automate-browser` skill.

`TaskUpdate(T4, status="completed")`

### Step 5: Test
`TaskUpdate(T5, status="in_progress")`
Use the `tester` agent for the compilation check.

`TaskUpdate(T5, status="completed")`

### Step 6: Document
`TaskUpdate(T6, status="in_progress")`
Update `./docs/design-guidelines.md` if it's warranted.

`TaskUpdate(T6, status="completed")`

## Tips
- Use the Read tool to study screenshots and visual assets

