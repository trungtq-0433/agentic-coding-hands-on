---
name: tkm:pm-report-project
description: >
  Progress reporting (updating progress.md + creating the weekly report
  reports/yyyy-mm-dd-weekly-report.md).
  Cross-references the planned dates in schedule.md, task-list.md, GitHub Issues and the EM's task report
  to bring the overall progress summary, milestone progress, WBS progress and variance against plan in
  progress.md up to date, then produces a client-facing weekly report from that snapshot. When internal
  delivery data is needed, it delegates to the project-manager (EM) agent via Task and integrates the result.
  Invoked from the REP menu of jp-project-manager, and can be run repeatedly over time to update.
  Owns the JP-PM document tree only — requires project/01_management/ to exist. If the repository
  has no project/01_management/ this skill does not apply.
  ALWAYS activate when the user mentions: progress report, weekly report, weekly-report,
  progress update, pm-report-project, REP (JP-PM menu).
  SKIP: the WBS and schedule (the plan) = schedule.md (→ pm-plan-schedule/SCH);
  task creation = task-list.md (→ pm-create-tasks/TASK);
  registering risks and issues = risk-list.md / problem-list.md (→ pm-track-risks-issues/RISK).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
  - Task
argument-hint: "[progress|report] [<EM report> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-report-project Skill

The skill that brings the project's progress up to date with reality and turns it into a client-facing weekly report. Invoked from the `REP` menu of the `jp-project-manager` agent. Choose interactively which of the **two jobs** to do — (1) updating `progress.md` (bringing the actual progress against plan up to date) or (2) creating the weekly report (a client-facing summary) — and run it repeatedly over time. The order (1) → (2) is recommended (update the progress first, then build the report from it).

## Purpose

The **main purpose** is filling in and updating:

- [`project/01_management/progress.md`](../../../project/01_management/progress.md) §1 (overall progress summary), §2 (milestone progress), §3 (WBS progress, including variance against plan), §4 (revision history)
- `project/01_management/reports/<currentDate>-weekly-report.md` — the weekly report (a new file each period), written from the report skeleton in `references/skeletons.md`

**Secondarily**, update:

- `plans/project-management/jp-pm-memory.md` — the status of the `REP` row, `## What To Do Next`, and `Last updated` (Step 3)

**Important (scope boundaries)**:

- The following are **read-only** (referenced only as input for judging progress and for copying into the report; never touch the skills that own them):
  - [`project/01_management/schedule.md`](../../../project/01_management/schedule.md) (owned by `pm-plan-schedule`/SCH. **Planned dates are referenced here** and never duplicated into progress.md)
  - [`project/01_management/task-list.md`](../../../project/01_management/task-list.md) (owned by `pm-create-tasks`/TASK)
  - [`project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) / [`project/01_management/risks-problems/risk-list.md`](../../../project/01_management/risks-problems/risk-list.md) (owned by `pm-track-risks-issues`/RISK; the source for §6 of the weekly report)
  - [`project/01_management/decision.md`](../../../project/01_management/decision.md) (the source for §7 of the weekly report — **never edit it**)
  - [`project/01_management/overview.md`](../../../project/01_management/overview.md) / [`project/01_management/stakeholders.md`](../../../project/01_management/stakeholders.md) (references for approvals and report recipients)
  - **GitHub Issues** (read only via the `gh` CLI. Never create, update or close an Issue)
- If the consumer's repository happens to contain a `reports/yyyy-mm-dd-weekly-report.md` template, it is **read as the copy source only and never modified**. Otherwise use the skeleton in `references/skeletons.md`. Either way, always write into a new dated file.
- Never rewrite the leading guidance blockquotes in `progress.md`, or **the column definitions and ID scheme of its tables**. IDs must match `schedule.md`.
- When **internal delivery data** (each task's actual progress, completion status, blockers) is needed, obtain it by delegating to the `project-manager` (EM) agent via `Task`, and re-integrate it for the customer. Writing to Issues or tasks is left to the EM side; this skill never does it.

## Reference Documents

Load at runtime as needed:

- `references/skeletons.md` — the `progress.md` skeleton and the weekly report skeleton, used when the file does not exist yet
- `references/field-mapping.md` — the rules for deriving each column of `progress.md` (status, progress percentage, variance against plan) from each input (schedule / task-list / GitHub Issues / EM report), the mapping from `progress.md`, risks-problems and decision.md into the 8 sections of the weekly report, the convention for calculating variance against plan, and the file naming convention for weekly reports
- `references/hearing.md` — example prompts and answer interpretation rules for Blocks A–C (mode selection / progress update / weekly report)

## How Inputs Are Received

This skill's primary inputs are the **existing documents in the repository** (`progress.md`, `schedule.md`, `task-list.md`, risks-problems, decision.md) and **GitHub Issues** (`gh issue list` / `gh issue view`), loaded directly on activation with `Read` / `Bash` (no need to ask the user for paths). When the actual progress of internal tasks is needed, obtain it by delegating to `project-manager` (EM) via `Task`. In addition, if the user supplies reference materials (EM task reports, meeting minutes, change trackers, etc.), they can be received in any of these forms:

1. **A path to a real file** — read with `Read`
2. **Pasted directly into the chat** (text / Markdown)
3. **Nothing at all** — filled in from the existing documents and, if needed, EM delegation and conversation

**Known limitation**: `Read` handles PDFs directly, but `.docx` / `.xlsx` / `.doc` / `.xls` are binary formats and cannot be read as-is. When given one of these paths, or when Read fails, you may proceed in the following order without asking for confirmation:

1. **Write a throwaway Python script via Bash to parse it**: `.docx` / `.xlsx` are ZIP + XML structures, so use `python-docx` / `openpyxl` if available; otherwise use the standard library `zipfile` + `xml.etree.ElementTree` to parse `word/document.xml` (docx) or `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` (xlsx) directly and pull out the text. Read and use the extracted text on the spot, and do not leave the script or intermediate files under the project (use the OS temp directory if a temporary file is needed).
2. If method 1 does not work for `.doc` / `.xls` (legacy binary formats), if `python3` is unavailable, or if the extracted result is garbled/empty and unusable, do not keep trying other approaches — say:

> "I couldn't read this file correctly automatically. Could you paste the relevant part as text, or export it to PDF/text and give me the path again?"

## Conversation Guidelines

- **Propose proactively.** Present the progress update you derived from the inputs (status, progress percentage, variance against plan) or a draft weekly report as a starting point, and have the user confirm or amend it.
- **Always stop at the mode selection and before writing.** At the end of Step 1 (choosing job 1 or 2) and before writing into `progress.md` or the weekly report (draft approval), wait for an explicit instruction from the user.
- Always label derived progress values as "candidate (needs confirmation)" and wait for the user to accept, amend or reject them. **Never finalize on the AI's inference alone** (especially progress percentages, statuses and variance against plan). **A progress percentage with no backing from actual data (task-list / Issues / EM report) is left blank.**
- Variance against plan records **only the conclusion** from comparing the planned date in `schedule.md` (milestone = planned date, WBS = planned end date) against the actual (or today, `currentDate`, if incomplete) — e.g. `On track` / `3 days behind` / `2 days ahead`. Never duplicate the planned dates themselves into `progress.md`.
- You may converse with the user (a developer) in Vietnamese, but **what is written into progress.md and the weekly report is consistently in Japanese**.
- Write the weekly report as a **client-facing summary** (never paste internal notes or the EM's raw data verbatim — summarize on the assumption the customer will read it). Bad news first, and include numbers, owners and next actions.
- Never overwrite existing real data (actuals rows that are not placeholders) without permission. If a weekly report file already exists for the period, do not create a duplicate — propose updating that file.

## Main Flow

### Step 1: Load context and choose the mode

Load the following to understand the current state:

- [`progress.md`](../../../project/01_management/progress.md) — the current actual progress. **If it does not exist or is empty, `Write` it from `references/skeletons.md`** (the kit ships no `project/` tree, so its absence is the normal starting state), then judge whether each row is still a template of HTML comments only, or contains real data
- [`schedule.md`](../../../project/01_management/schedule.md) — the planned-date baseline (the basis for variance against plan; the ID scheme)
- [`task-list.md`](../../../project/01_management/task-list.md) — task states (input for judging progress)
- `plans/project-management/jp-pm-memory.md` — the state of the `REP` row and `## GitHub Settings` (the repository). **This file is not shipped with the kit** — the `jp-project-manager` agent creates it on first activation. If it is absent, treat every skill as "not started", carry on, and create it from the skeleton in the agent definition when you write the state back
- The sources for the report (used in job 2 — skim them here): `risks-problems/problem-list.md`, `risk-list.md`, `decision.md`, and `gh issue list` (the repository under `## GitHub Settings`; skip if unauthenticated or unconfigured)
- The existing weekly report files under `reports/` (to prevent duplicate creation)

Then, following Block A of `references/hearing.md`, **ask the user which job to perform. Stop here and wait for their choice**:

- **Job 1 (update progress.md)** → Step 2A
- **Job 2 (create the weekly report)** → Step 2B

Both may be done in sequence (the order 1 → 2 is recommended, since the weekly report copies from the latest `progress.md`). If `progress.md` is still a template (zero actuals), say so and add that starting with job 1 is the natural choice.

### Step 2A: Update progress.md (job 1)

Following the rules in `references/field-mapping.md`, cross-reference each input to bring the actual progress up to date:

- **Cross-referencing the inputs**: the planned dates in `schedule.md` × the states in `task-list.md` / GitHub Issues × the EM report → derive the status, progress percentage and actual date for each milestone and WBS item.
- **When the actual progress of internal tasks is needed**: confirm via Block B of `references/hearing.md`, then use `Task` to ask the `project-manager` (EM) agent for "the task progress, completion status and blockers for the target WBS/period", and integrate the result.
- **Calculating variance against plan**: compare the planned date in `schedule.md` against the actual (or `currentDate` if incomplete) and record only the conclusion: `On track` / `N days behind` / `N days ahead`.
- **What to fill in**: §2 milestone progress, §3 WBS progress (Epic/Story), and on that basis bring §1 the overall progress summary up to date (overall status = on track / caution / delayed, variance against plan, comment, update date). Update date = `currentDate`.

Keep the order: present the derived values as "candidates (needs confirmation)" → user approval → `Edit`. Leave unsupported progress percentages blank. Finally, append one row to §4 revision history (date = `currentDate`, updater = `pm-report-project skill`, content = a summary of the update).

### Step 2B: Create the weekly report (job 2)

Following Block C of `references/hearing.md`, interview about the reporting period, the author, this week's highlights and the items to confirm with the client (if job 1 was just performed, its results may be reused).

1. **Create the file**: `Write` `reports/<currentDate>-weekly-report.md` from the report skeleton in `references/skeletons.md` (or, if the repository already carries a `reports/yyyy-mm-dd-weekly-report.md` template, copy that instead and leave it unmodified). If a file of the same name already exists, do not overwrite it — propose updating it instead.
2. **Fill it in**: following the mapping in `references/field-mapping.md`, complete the 8 sections (summarized for the client):
   - §1 Report information (period, author, creation date = `currentDate`)
   - §2 This week's summary (about 3 lines, bad news first)
   - §3 Progress status (copy and summarize the relevant parts of `progress.md` §2/§3)
   - §4 This week's results (completed tasks, deliverables) / §5 Next week's plan (what will be started)
   - §6 Issues & risks (new and updated entries in `problem-list.md` / `risk-list.md`)
   - §7 Decisions & items for confirmation (new decisions from `decision.md` plus items the client is asked to confirm)
   - §8 Other shared information
3. Keep the order: present the draft → user approval → write.

### Step 3: Update state

Update `jp-pm-memory.md`:

1. The status of the `REP` row (🔄 if ongoing, ✅ at a natural stopping point, noting the scope of the update). If `REP` shares a row with other codes (`REP CR RISK FB BUG TL CHK`, etc.), you may split `REP` out onto its own row.
2. `## What To Do Next` (e.g. the next reporting period, remaining EM delegation, items awaiting client confirmation).
3. `Last updated` (`currentDate`).

### Step 4: Completion summary

Report as a list: the milestones/WBS items updated (ID, status, variance against plan), any newly identified delays and blockers, the path of the weekly report file created, the items the client should be asked to confirm or approve, and any progress values left unsettled. Recommend sharing it at the regular meeting, and mention that re-running later can update the progress and produce the next report. If an important progress judgement arises (a plan for handling a delay, etc.), prompt the user to record it in `decision.md` (never `Edit` it yourself).

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "How inputs are received"
- `progress.md` / `schedule.md` are still templates (zero actuals and zero plan) → say honestly that there is no progress data yet and encourage recording it. **Do not produce an empty weekly report** (either prepare the data via job 1 first, or limit yourself to a minimal summary)
- `gh` not authenticated, repository not configured, insufficient permissions → skip only the GitHub Issue lookups, report that, and continue with the other inputs (progress / task-list / EM delegation / meeting minutes, etc.). Do not block
- The `project-manager` (EM) agent does not respond or returns nothing → put the delegated portion on hold and update what the existing documents show. State the items awaiting the EM as unsettled in the completion summary. Do not block
- `progress.md` / the weekly report file do not exist → this is the normal first-run state, not an error. `Write` them from `references/skeletons.md` and carry on. Never invent a structure of your own instead
- Progress percentages, statuses or variance against plan are never settled → leave them blank and do not fill them in by guesswork. Report them as open items in the completion summary
- About to overwrite an existing real data row or an existing weekly report file → always get confirmation before proceeding

## Related Files

- `references/skeletons.md` — the `progress.md` and weekly report skeletons
- `references/field-mapping.md` — input → progress.md derivation rules, progress.md/risks/decision → weekly report mapping, variance calculation and file naming conventions
- `references/hearing.md` — prompts and interpretation rules for Blocks A–C
- [`../../../project/01_management/progress.md`](../../../project/01_management/progress.md) — actual progress (this skill's main deliverable)
- `../../../project/01_management/reports/<currentDate>-weekly-report.md` — the weekly report (this skill's main deliverable, newly created)
- [`../../../project/01_management/schedule.md`](../../../project/01_management/schedule.md) / [`../../../project/01_management/task-list.md`](../../../project/01_management/task-list.md) — input for judging progress, read-only
- [`../../../project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) / [`../../../project/01_management/risks-problems/risk-list.md`](../../../project/01_management/risks-problems/risk-list.md) — source for §6 of the weekly report, read-only
- [`../../../project/01_management/decision.md`](../../../project/01_management/decision.md) — source for §7 of the weekly report, never edited
- [`../../../project/01_management/overview.md`](../../../project/01_management/overview.md) / [`../../../project/01_management/stakeholders.md`](../../../project/01_management/stakeholders.md) — references, read-only
- `plans/project-management/jp-pm-memory.md` — the `REP` state is updated
