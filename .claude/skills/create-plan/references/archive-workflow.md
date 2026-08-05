# Archive Workflow

## Your mission
Read through the plans, make sense of them, then write the journal entries and file away whichever plans the user names — or the whole `plans` directory.

## Plan Resolution
1. `$ARGUMENTS` given → use that path
2. Otherwise read every plan in the `plans` directory

## Workflow

### Step 1: Read Plan Files

Open the plan directory:
- `plan.md` - the overview and the phases list
- `phase-*.md` - the first 20 lines of each, enough to read its progress and status

### Step 2: Summarize the plans and document them with `/tkm:write-journal` skill invocation
Ask through `AskUserQuestion` whether the user wants journal entries written.
If they pick "No", skip this step.
If they pick "Yes":
- Pull together what you learned in the earlier steps.
- Run the Task tool with `subagent_type="journal-writer"` in parallel to document every plan.
- Keep the entries tight — the events that mattered, the key changes, the impacts, the decisions.
- Write them into the `./docs/journals/` directory.

### Step 3: Ask user to confirm the action before archiving these plans
Ask through `AskUserQuestion` whether to archive these plans, and whether that's specific plans or only the completed ones.
Ask through `AskUserQuestion` whether to delete them outright or move them into `./plans/archive`.

### Step 4: Archive the plans
Carry out whatever the user chose:
- Move them into the `./plans/archive` directory.
- Or delete them for good: `rm -rf ./plans/<plan-1> ./plans/<plan-2> ...`

### Step 5: Ask if user wants to commit the changes
Ask through `AskUserQuestion` whether to commit, with these options:
- Stage and commit the changes (run `/tkm:git` for the commit flow)
- Commit and push the changes (run `/tkm:git` for the push flow)
- Nah, I'll do it later

## Output
Once the archiving is done, hand back a summary:
- How many plans were archived
- How many were deleted for good
- A table of the archived or deleted plans (title, status, created date, LOC)
- A table of the journal entries written (title, status, created date, LOC)

## Important Notes
- Only ask when there's a real decision behind the question
- Trade grammar for concision
- List anything still open at the end
- Stay token-efficient without dropping quality
