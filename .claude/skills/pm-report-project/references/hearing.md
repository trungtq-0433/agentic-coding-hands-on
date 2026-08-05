# Interview Details (Blocks A–C)

This file collects the **example phrasings** and **answer interpretation rules** for each block. The skill refers to it and drives the conversation one question per turn within a block.

## Common Rules

- Present options **as keywords**, not as numbered choices
- Accept free-text answers (ask a clarifying question when ambiguous)
- Items requiring judgement — status, progress percentage, variance against plan — are never finalized without both backing from actual data (task-list / GitHub Issues / EM report) and an explicit answer from the user
- Always label derived progress values as "candidate (needs confirmation)" and wait for the user to accept, amend or reject them
- Administrative reminders, such as prompting for a record in `decision.md`, must not interrupt the block's conversation — report them together in the completion summary

## Block A: Choosing the Job (→ main flow Step 1)

**Example prompt**:
> Which would you like to do for the progress report this time?
> - (1) **Update the progress**: cross-reference the planned dates in schedule, the tasks, the GitHub Issues and the EM's task report to bring `progress.md` (milestone / WBS status, progress percentage, variance against plan) up to date
> - (2) **Create the weekly report**: produce a client-facing weekly report (`reports/<date>-weekly-report.md`) from the latest progress
>
> (You can also do both, in the order 1 → 2. Since the report copies from the latest progress, 1 → 2 is recommended.)

**Answer interpretation rules**:
- (1) → Step 2A, (2) → Step 2B, both → run 2A then 2B
- If `progress.md` has zero actuals (still a template), say so and recommend (1) (never produce an empty report)
- If the user names a specific milestone / WBS item / period, you may narrow the update (1) or the report (2) to that scope

## Block B: Updating the Progress (job 1 → Step 2A)

**Present first**: show a **list of candidate updates** (ID, proposed status, proposed progress percentage, proposed variance against plan) derived by cross-referencing the milestones/WBS in `schedule.md` against the states in `task-list.md` and the GitHub Issues, and confirm them one at a time.

**Example prompt (milestone / WBS)**:
> For milestone `M-02` (completion of X), the planned date in schedule is 2026-08-01 — what is the actual state?
> - Complete (please tell me the actual date) /
> - In progress (a rough progress percentage if you have one) /
> - Not started or delayed (reason and outlook)

**Example prompt (whether EM delivery data is needed)**:
> Should I check the actual progress, completion status and blockers of the individual tasks with the EM (project-manager) and pull that in? (Tell me the target WBS/period and I'll delegate and consolidate it.)

**Answer interpretation rules**:
- **Status / progress percentage**: finalize only values backed by actuals (task-list / Issues / EM report). Leave unsupported progress percentages blank (follow the rules in `field-mapping.md`)
- **Variance against plan**: compare the planned date in `schedule.md` (milestone = planned date, WBS = planned end date) against the actual (or `currentDate` if incomplete) and enter only the conclusion: `On track` / `N days behind` / `N days ahead`
- **Actual date**: record it for completed items; blank when incomplete
- **Overall summary (§1)**: after the individual updates, bring the overall status (on track / caution / delayed), the variance against plan and the comment up to date. If there is a delay, write the cause in the comment, bad news first
- If a judgement is ambiguous, ask a clarifying question and leave the existing value unchanged until settled. The update date is `currentDate`

## Block C: Creating the Weekly Report (job 2 → Step 2B)

**Present first**: offer candidate periods (e.g. the day after the last report through the end of this week) and the draft items picked up from `progress.md`, risks-problems and decision.md, then confirm the approach.

**Example prompt (report information)**:
> I'll create the weekly report. Please tell me the reporting period (e.g. 2026-08-03 – 2026-08-07) and the author's name. I'll set the creation date to today.

**Example prompt (summary, results, plan)**:
> In one line, what was this week's highlight (overall progress and anything noteworthy)? Please tell me the main tasks/deliverables completed this week and anything due to start next week (I'll also show the candidates picked up from progress.md and task-list).

**Example prompt (items to confirm and share)**:
> Are there items you'd like the client to confirm or approve (decisions, pending judgements, plans for handling risks)? I'll present the new and updated candidates from `decision.md`, `problem-list.md` and `risk-list.md`.

**Answer interpretation rules**:
- The period and author are settled by the user's input. Creation date = `currentDate`
- §3 Progress status copies and summarizes the relevant parts of `progress.md` §2/§3 (the just-updated content if job 1 was run), following the mapping in `field-mapping.md`
- §6 Issues & risks covers **new and updated entries only** from `problem-list.md` / `risk-list.md` (never paste everything). Copy the ID, content, status and plan
- §7 Decisions & items for confirmation covers the new decisions from `decision.md` plus the items the client is asked to confirm
- Summarize it as a client-facing report (never paste internal notes or the EM's raw data verbatim). Bad news first
- If a weekly report file already exists for the period, do not overwrite it — ask whether to update it
