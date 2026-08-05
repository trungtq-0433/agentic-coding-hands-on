# Field Mapping (Input → progress.md → Weekly Report)

The conventions for judging progress and for copying into the report. The skill refers to this file to (1) derive each column of `progress.md` and (2) turn that content into each section of the weekly report. **IDs must always match `schedule.md`.**

## 1. Input → progress.md (job 1)

For each milestone and WBS item, cross-reference the following inputs to derive the columns.

### The inputs and their roles

| Input | How it is obtained | Role |
| --- | --- | --- |
| `schedule.md` | Read | **The planned-date baseline** (milestone = planned date, WBS = planned end date). The baseline for the ID scheme. Read-only |
| `task-list.md` | Read | The state of each task (not started / in progress / done) → the basis for WBS status and progress percentage |
| GitHub Issues | `gh issue list` / `gh issue view` | Issue open/closed state and labels → the basis for the actual task state and blockers |
| EM task report | `Task` (delegated to project-manager) | Actual progress, completion status and blockers for internal tasks. Fills the gaps that task-list and Issues leave |

### How to derive each column

- **Status** (`Not started` / `In progress` / `Done` / `Delayed`):
  - All child tasks/Issues complete → `Done` (record the actual date)
  - Some started → `In progress`
  - Nothing started → `Not started`
  - Past the planned date and incomplete, or no prospect of finishing within the planned date → `Delayed`
- **Progress % ** (WBS only): fill in **only when backed by actuals**, such as the proportion of completed child tasks. Without backing, leave it **blank** (never fill it by guesswork).
- **Actual date**: record only for completed items. Blank when incomplete.
- **Variance against plan**: **only the conclusion** from comparing the planned date in `schedule.md` against the actual (or `currentDate` if incomplete):
  - Completed on or before the planned date / progressing as planned → `On track`
  - N days past the planned date (`currentDate` − planned date if incomplete) → `N days behind`
  - Completed N days earlier than planned → `N days ahead`
  - Note: never duplicate the planned dates themselves into `progress.md` (refer to `schedule.md`)
- **Blockers & related issue IDs** (WBS only): record the relevant `P-xxx` from `problem-list.md`.
- **Update date**: `currentDate`.

### How to derive §1, the overall progress summary

Aggregate it after updating §2/§3:

- **Overall status**: a delayed milestone/WBS item sits on the critical path, or several are delayed → `Delayed`; an isolated minor delay needing attention → `Caution`; everything on track → `On track`
- **Variance against plan**: the most impactful variance in one line (e.g. `M-02 is 3 days behind`)
- **Comment**: the cause and the plan for addressing it, concisely, bad news first
- **Update date**: `currentDate`

## 2. progress.md / risks / decision → Weekly Report (job 2)

Fill each section of the copied `reports/<currentDate>-weekly-report.md` from the sources below. **Summarize for the client** (never paste internal notes or raw data verbatim).

| Weekly report section | Primary source | What to write |
| --- | --- | --- |
| §1 Report information | Interview (Block C) | Period and author (from the interview), creation date = `currentDate` |
| §2 This week's summary | `progress.md` §1 | Overall status and variance against plan in about 3 lines. Bad news first |
| §3 Progress status (table) | `progress.md` §2/§3 | Copy and summarize the milestones/WBS for the period (ID, content, status, progress %, comment) |
| §4 This week's results | `task-list.md` / `progress.md` / EM report | Tasks that became `Done` this week, and deliverables |
| §5 Next week's plan | `schedule.md` / `task-list.md` | Tasks and milestones due to start next week |
| §6 Issues & risks (table) | `problem-list.md` / `risk-list.md` | **New and updated entries only** (ID, content, status, plan). Do not paste everything |
| §7 Decisions & items for confirmation | `decision.md` + interview | New decisions (DEC-xxx) plus items the client is asked to confirm or approve |
| §8 Other shared information | Interview, meeting minutes | Anything to share that does not fit above |

## 3. File Naming and Copying Conventions

- The weekly report file name is `reports/<currentDate>-weekly-report.md` (e.g. `2026-08-07-weekly-report.md`). Agree with the user whether the date is the report's creation date or the last day of the period.
- Create it by `Write`-ing the report skeleton from `references/skeletons.md`. If the repository already carries a `reports/yyyy-mm-dd-weekly-report.md` template, copy that instead and never modify the template itself.
- If a file of the same name (same period) already exists, do not overwrite it — ask the user whether to update it.
- The leading blockquote at the top of the weekly report (the template's explanatory text) may be removed in the real file, or adapted as part of the report body (prioritize a client-facing presentation).

## 4. Prohibitions and Cautions

- Never finalize a progress percentage or status by guesswork when actuals do not back it (leave it blank).
- Never duplicate the planned dates from `schedule.md` into `progress.md` (variance against plan is the conclusion only).
- Never rewrite the leading guidance in `progress.md`, its table column definitions, or its ID scheme.
- `decision.md`, risks-problems, task-list and schedule are **read-only** (this skill never edits them).
- The IDs in every table must match `schedule.md` and the respective trackers (never mint new IDs on your own).
