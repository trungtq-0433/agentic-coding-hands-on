---
name: tkm:pm-plan-schedule
description: |
  Creates the schedule baseline (schedule.md). Builds a master schedule by phase from overview.md §4
  (role split), and turns the function groups (FG) / functions (F) in function-list.md into a WBS of
  Epics / Stories. If the function list is not yet settled, plans only the requirements phase up front.
  ALWAYS activate when the user mentions: schedule, master schedule, WBS, milestones, Epic, Story,
  schedule.md, pm-plan-schedule, SCH (JP-PM menu).
  SKIP: story details = stories/ (→ pm-create-stories/STORY); task breakdown and creation = task-list.md
  (→ pm-create-tasks/TASK); actual progress against plan = progress.md (→ pm-report-project/REP);
  test milestones and test WBS = test-schedule.md (→ pm-plan-test/TEST).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-plan-schedule Skill

The skill that creates the schedule baseline. Invoked from the `SCH` menu of `jp-project-manager`.

## Primary Deliverable

[`project/01_management/schedule.md`](../../../project/01_management/schedule.md): **§1 master schedule (by phase) / §2 milestones / §3 WBS (Epic/Story)**.

Only when data required for the WBS calculation is missing, write **secondarily** to the following (never overwrite without permission):

- `overview.md` §4 (role split) — only rows where the performer is empty
- `stakeholders.md` §2 — only members whose "Assigned effort (capacity)" column is empty
- `function-list.md` — only the "Related WBS ID" column (Case A only, see below)

**Do not touch**: `define-dod.md` / `progress.md` (actuals tracking is owned by REP) / the other columns of `stakeholders.md` §2, and §1 and §3–§6.
**Do not write assumptions into schedule.md.** Schedule assumptions and constraints belong in `overview.md` (this skill only references assumptions that are already in overview).

## Model (important)

- **Phase**: requirements, basic design, development, testing, etc. These are the rows of **§1 the master schedule**, not Epics. The phase × role breakdown happens at the Task level (owned by `pm-create-tasks`).
- **Epic = function group (FG)**, **Story = function (F)**. Follow [`skills/_shared/extras/pm-skills/wbs-task-breakdown.md`](../_shared/extras/pm-skills/wbs-task-breakdown.md) (Epics split by functional domain, never by phase) and [`skills/_shared/extras/pm-skills/function-breakdown.md`](../_shared/extras/pm-skills/function-breakdown.md) (FG → F). **The WBS goes down to the Story level only** (never create Task rows).

> `pm-create-stories` (STORY) and `pm-create-tasks` (TASK) consume this model as-is: STORY elaborates the `E-xx-Sxx` entries produced here, and TASK takes the phase as a **separate axis chosen by the user** rather than reading it out of Epic names.

## References

- `references/skeletons.md` — the `schedule.md` skeleton, used in Step 1 when the file does not exist yet
- `references/wbs-breakdown.md` — master schedule generation, Epic/Story granularity, dependencies, date calculation
- `references/hearing.md` — interview Block A (milestones) / B (effort) / C (capacity) / D (dependencies and confirming the function list is settled)

## Input

The estimate (effort) may be given as a path (`Read`), pasted, or not supplied at all (settled in Block B). Milestones must always be settled through the interview (documents are reference only).
`.docx` / `.xlsx` may be extracted with a throwaway Python script via Bash (`zipfile` + XML parsing, etc.). If extraction is impossible, or for `.doc`/`.xls`, or if python3 is unavailable, do not persist — ask for "a text paste, or the file again in PDF/text format". Do not leave intermediate files under the project.

## Conversation Guidelines

- Never finalize milestones, effort, capacity or dependencies without an explicit answer from the user (the AI must not place provisional dates).
- The unit used when asking about capacity follows the contract type in `overview.md` §1 (lab/SES = person-days per month; fixed-price = total assigned person-days for the project). If it is undecided, confirm that first.
- If you group stories (e.g. because there are too many function groups), briefly confirm the result.

## Main Flow

### Step 1: Load and determine the case

`Read` `schedule.md` / `overview.md` (§1 contract type, §3 way of working, §4 role split) / `stakeholders.md` §2 / `function-list.md` and check. Also `Read` the two kit rules this skill applies (always present, unlike the `project/` files): [`wbs-task-breakdown.md`](../_shared/extras/pm-skills/wbs-task-breakdown.md) (§1 Epic/Story definitions and MECE, §3 the change-request flow) and [`function-breakdown.md`](../_shared/extras/pm-skills/function-breakdown.md) (FG → F levels, ID conventions, and the rule to confirm with the user before restructuring `function-list.md`).

**If `schedule.md` does not exist or is empty, `Write` it from `references/skeletons.md` first** — the kit ships no `project/` tree, so its absence is the normal starting state. The other three are **read-only inputs owned by PLAN and REQ**: if they are missing, do not create them; treat them as "not started" and say which skill owns them.

Then check:

- Whether each section is empty (template examples) or filled in (for filled-in content, present the existing value and ask whether to update)
- Rows in `overview.md` §4 with an empty performer / the §1 contract type
- Members in `stakeholders.md` §2 whose "Assigned effort" is empty
- **Whether the function list is settled** (confirm in Block D; if unclear, ask the user directly)
  - **Case A (settled)**: plan all phases + the full WBS
  - **Case B (not settled)**: plan **only the requirements phase** up front (§1 has dates only for requirements, everything after is `TBD (after the function list is settled)`; §3 covers only requirements work). Re-run SCH once it is settled to expand into Case A

If most of `overview.md` §4 is undecided and `function-list.md` is also empty, ask exactly one question — "running PLAN/REQ first would improve accuracy, but we can also proceed as-is" — and do not block.

### Step 2: Milestones (Block A)

Using Block A of `references/hearing.md`, gather the names, planned dates and completion conditions, and `Edit` each into `schedule.md` §2 as it is settled. Use the `Related phase` column (the phase name).

### Step 3: Master schedule (§1)

Following `references/wbs-breakdown.md` §1, expand each work item in `overview.md` §4 into a phase row in §1. State the **performer (Sun* / joint / client)** on every row (keep client-side phases as references too). For rows with an empty performer, interview on the spot and write it back to `overview.md` §4 (add one row to the overview revision history if there is a substantive change). Dates are derived from the milestones and dependencies (Step 6). **In Case B, only the requirements rows get dates; everything after is TBD.**

### Step 4: WBS (§3, Epic/Story)

Follow `references/wbs-breakdown.md` §2:

- **Case A**: **function group (FG) → Epic** and **function (F) → Story** from `function-list.md` (as a rule 1 function = 1 story; however, a function that breaks INVEST or exceeds one sprint may be split into multiple stories by value or scenario — never by CRUD operation. Group related functions only when there are too many FGs, and confirm). Record the `Related F-ID` on each story.
- **Case B**: turn only the requirements work into stories (if there are rough function-group candidates, create provisional Epics/Stories; otherwise a single Epic "Requirements definition" plus interview/analysis stories).

**Down to the Story level only.** Never create Task rows.

### Step 5: Effort (Block B) and capacity (Block C)

Apply the effort you can take from the estimate; interview in Block B for the rest. For members in `stakeholders.md` §2 whose "Assigned effort" is empty, confirm in Block C (using the unit that matches the contract type) and `Edit` (add one row to the stakeholders revision history if there is a substantive change).

### Step 6: Date calculation

Following `references/wbs-breakdown.md` §3 and §4, derive the start/end dates of each phase in §1 and each story in §3 from the milestones, the dependencies, and effort ÷ capacity. If the project is agile (overview §3), do not serialize the phases strictly: assign work to sprints per function (story), so a story's dates are the sprint window in which that function is built. If the result overruns a fixed milestone, present it to the user and confirm how to adjust (never adjust without permission).

### Step 7: function-list integration (Case A only)

`Edit` the generated story IDs into the "Related WBS ID" column of `function-list.md` (never overwrite cells that are already filled in). In Case B, do not write back.

### Step 8: Revision history and completion summary

Append one row (date, updater, content) to the revision history of each file with a substantive change (`schedule.md` is mandatory). In the summary, present the number of Epics/Stories, the number of milestones, the period, and the open items. **In Case B, explain that "SCH should be re-run after the function list is settled, to expand to all phases".**

## On Error

- Unreadable format → guide the user with the fallback wording above
- The estimate and the interview conflict → present both and let the user decide
- About to overwrite existing real data → get confirmation
- Effort or capacity remains undecided to the end → leave the dates on those rows blank and report them as open items in the summary (never place provisional values)

## Related Files

- `references/skeletons.md` / `references/wbs-breakdown.md` / `references/hearing.md`
- [`../../../project/01_management/schedule.md`](../../../project/01_management/schedule.md) / [`overview.md`](../../../project/01_management/overview.md) / [`stakeholders.md`](../../../project/01_management/stakeholders.md)
- [`../../../project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md)
- [`../_shared/extras/pm-skills/wbs-task-breakdown.md`](../_shared/extras/pm-skills/wbs-task-breakdown.md) / [`../_shared/extras/pm-skills/function-breakdown.md`](../_shared/extras/pm-skills/function-breakdown.md)
