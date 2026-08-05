---
name: tkm:pm-create-stories
description: >
  Elaborates WBS stories (creating project/01_management/stories/story-{WBS ID}-{name}.md).
  Picks one Story from schedule.md §3 and, through interactive brainstorming, digs into its purpose,
  target users, scope, business flow, data, technical constraints and acceptance criteria to produce the
  story details, then reflects the start/creation status in progress.md §3. The result feeds the
  downstream design work and pm-create-tasks.
  ALWAYS activate when the user mentions: story details, user story, user-story,
  story, pm-create-stories, STORY (JP-PM menu).
  SKIP: the main WBS and schedule (defining Epics/Stories) = schedule.md (→ pm-plan-schedule/SCH);
  task breakdown and creation = task-list.md (→ pm-create-tasks/TASK);
  per-function detailed analysis = functions/ (→ requirement-analysist).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[<Story WBS ID>] [<supplementary materials> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-create-stories Skill

The skill that elaborates a WBS story from schedule.md to a level usable for design and task creation. Invoked from the `STORY` menu of the `jp-project-manager` agent.

## Purpose

The **main purpose** is creating the following single file (one file per story):

- [`project/01_management/stories/story-{WBS ID}-{name}.md`](../../../project/01_management/stories/) — the details of the target story, `Write`n from the skeleton in `references/skeletons.md` (the kit ships no template file, and none is needed)

**Secondarily**, so that "which story is being worked on" survives across sessions, reflect the start/creation status in (Steps 3 and 6):

- [`project/01_management/progress.md`](../../../project/01_management/progress.md) §3 (WBS progress) — only the status, comment and update date of the target story's WBS ID row

**Important (scope boundaries)**:

- [`project/01_management/schedule.md`](../../../project/01_management/schedule.md) is **read-only**. Never create or change WBS entries (Epics/Stories) — that is owned by `pm-plan-schedule`/SCH. If the target story does not exist in schedule.md §3, do not start elaborating; instead say "please create the WBS with SCH first".
- [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md), [`non-function-list.md`](../../../project/02_requirements/non-function-list.md), [`functions/`](../../../project/02_requirements/functions/), [`role-list.md`](../../../project/02_requirements/role-list.md) and [`project/01_management/define-dod.md`](../../../project/01_management/define-dod.md) are **read-only** (referenced only for F-IDs / NFR-IDs / D-IDs, roles, business flows, etc.).
- Do not touch [`project/01_management/task-list.md`](../../../project/01_management/task-list.md) (task creation is owned by the separate `pm-create-tasks` skill). This skill's deliverable (the story details) feeds `pm-create-tasks` and the design phase.
- In `progress.md`, update **only the target story's WBS ID row in §3**. The overall progress summary (§1), milestone progress (§2) and tracking actual development progress percentages are owned by `pm-report-project`/REP. This skill records only "the status of the story detail document".

## Reference Documents

Load at runtime as needed:

- `references/skeletons.md` — the story detail skeleton (§1–§12), used in Step 3 when creating the file
- `references/hearing.md` — example prompts for brainstorming Blocks 1–7, how to ask in small groups, and the `[ASSUMPTION]` default rule for "I don't know / later"

## How Inputs Are Received

This skill's primary input is the already-existing [`schedule.md`](../../../project/01_management/schedule.md) §3 (the WBS stories); additional files from the user are not required. The details are settled through the interactive interview (Step 4). If the user does supply reference materials, they can be received in any of these forms:

1. **A path to a real file** — read with `Read`
2. **Pasted directly into the chat** (text / Markdown)
3. **Nothing at all** — filled in from the existing documents (Step 1) and the interview (Step 4)

**Known limitation**: `Read` handles PDFs directly, but `.docx` / `.xlsx` / `.doc` / `.xls` are binary formats and cannot be read as-is. When given one of these paths, or when Read fails, you may proceed in the following order without asking for confirmation:

1. **Write a throwaway Python script via Bash to parse it**: `.docx` / `.xlsx` are ZIP + XML structures, so use `python-docx` / `openpyxl` if available; otherwise use the standard library `zipfile` + `xml.etree.ElementTree` to parse `word/document.xml` (docx) or `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` (xlsx) directly and pull out the text. Read and use the extracted text on the spot, and do not leave the script or intermediate files under the project (use the OS temp directory if a temporary file is needed).
2. If method 1 does not work for `.doc` / `.xls` (legacy binary formats), if `python3` is unavailable, or if the extracted result is garbled/empty and unusable, do not keep trying other approaches — say:

> "I couldn't read this file correctly automatically. Could you paste the relevant part as text, or export it to PDF/text and give me the path again?"

## Conversation Guidelines

- **Brainstorm proactively.** Present a hypothesis derived from the existing materials first, and use it as a starting point to draw out the user's views.
- **Ask in small groups.** Never line up ten questions spanning multiple blocks in a single message. Limit yourself to **2–4 questions per block** and move to the next block only after receiving answers (details in `references/hearing.md`).
- **Handling "I don't know / later / your call":** do not press further. Form a reasonable hypothesis, write it in the body prefixed with `[ASSUMPTION] ...`, and also collect it in §10 "Assumptions & open items". Add a one-line rationale for the hypothesis.
- Story IDs and names are **inherited verbatim** from schedule.md §3 — never renumber or rename them.
- You may converse with the user (a developer) in Vietnamese, but **what is written into the files is consistently in Japanese**.
- When about to overwrite real data in existing materials (e.g. filled-in rows of progress.md), get confirmation before proceeding.

## Main Flow

### Step 1: Load context (grasp progress)

`Read` the following to grasp the overall project picture and the current progress:

- [`project/01_management/overview.md`](../../../project/01_management/overview.md) — contract, organization, way of working, constraints
- [`project/02_requirements/system-overview.md`](../../../project/02_requirements/system-overview.md) — background, problems, objectives
- [`project/01_management/schedule.md`](../../../project/01_management/schedule.md) §3 — the WBS (Epic/Story) list
- [`project/01_management/progress.md`](../../../project/01_management/progress.md) §3 — WBS progress (status of each story). This file is **owned by `pm-report-project`/REP**: if it does not exist, do not create it — skip the Step 3/6 progress updates, and say so in the completion summary
- [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) / [`non-function-list.md`](../../../project/02_requirements/non-function-list.md) — references for the related functional and non-functional requirements
- [`skills/_shared/extras/pm-skills/wbs-task-breakdown.md`](../_shared/extras/pm-skills/wbs-task-breakdown.md) — §1 what a Story must satisfy (INVEST, fits one sprint, always has acceptance criteria, one function may carry several stories) and §3 the change-request flow. A kit file, always present

If schedule.md §3 is empty (template examples only), there is nothing to elaborate — say "please create the WBS with `pm-plan-schedule` (SCH) first" and stop.

### Step 2: Propose the next story

Scan `project/01_management/stories/` to see which stories are already elaborated. Cross-reference the stories in schedule.md §3 against the statuses in progress.md §3 and **propose the story to work on next**. Rough priority for the proposal:

- Stories with no detail file yet (not elaborated)
- Stories whose dependencies (the "Dependencies" column of schedule.md) are satisfied
- Stories with high priority / a nearby related milestone

Offer 2–3 candidates and **add a one-line reason for recommending each (dependencies, priority, deadline)**. **Stop here and wait for the user to choose which story to elaborate.** Accept a match on the number, the WBS ID or the name.

### Step 3: Record the start and create the story file (progress update)

Once the user picks a target story:

1. `Edit` that WBS ID row in `progress.md` §3: set the status to `🔄 In progress`, the comment to `Writing story details`, and the update date to today (`currentDate`). If the WBS ID row does not exist in §3 yet, add one row mirroring the ID from schedule.md §3 (the progress percentage and actual dates may stay blank). Never overwrite rows that already contain actuals without permission — limit yourself to appending to the comment.
2. Using the skeleton in `references/skeletons.md`, `Write` a new `project/01_management/stories/story-{WBS ID}-{name}.md` (e.g. `story-E-01-S01-sign-in.md`). Fill in §1 "Story information" from schedule.md §3 and function-list.md (story ID, name, related Epic, related function IDs, priority; status = `Drafting details`; creation date).

At this point the file records which story is being worked on, so the work can be resumed after a session change.

### Step 4: Brainstorming (Blocks 1–7)

Following `references/hearing.md`, interview through Blocks 1–7 **in order, in small groups** (2–4 questions per block, moving on only after answers). As each block's answers come in, `Edit` the corresponding chapter:

| Block | Theme | Section to fill in |
|-------|--------|-----------------|
| 1 | Purpose & problem solved | §3 Background & purpose |
| 2 | Target users | §4 Target users |
| 3 | Scope (in/out) | §5 Scope |
| 4 | Main business flow | §6 Main business flow |
| 5 | Data requirements | §7 Data requirements |
| 6 | Technical constraints & non-functional | §8 Technical constraints & non-functional considerations |
| 7 | Acceptance criteria | §9 Acceptance criteria |

For items where the user says "I don't know / later", record a reasonable hypothesis prefixed with `[ASSUMPTION] ...` and append one row to §10 "Assumptions & open items" (do not press on the same point).

### Step 5: Complete the story details

Apply every block and finish the file. In particular:

- Summarize §2 "User story" in one sentence in the form "As a …, I want to … because …"
- **Never leave §9 "Acceptance criteria" empty** (it is the basis used by the downstream design work and `pm-create-tasks`, so always put down at least a starting draft)
- Tidy up §11 "Related documents" with the relevant F-IDs / NFR-IDs / D-IDs and a link to that story in schedule.md

### Step 6: Record completion and revision history

1. `Edit` the comment on that WBS ID row in `progress.md` §3 to `Story details written (stories/story-{...}.md)` and set the update date to today. **Do not set the status to `Done`** (the story's own development is not finished). Tracking development progress (percentages, actuals) is owned by `pm-report-project`/REP.
2. Set §1 status of the created story file to `Details written`, and append one row to §12 "Revision history" with the date, the updater (`pm-create-stories skill` or the persona name in use) and the content.

### Step 7: Completion summary

- Summarize the elaborated story (ID, name) and the path of the generated file
- **Present the `[ASSUMPTION]` entries and open items from §10 as a list**, with a note on who should confirm each and by when
- Point to the next action: using these details as input, move on to the **design phase** (screen design / API design) or to **`pm-create-tasks`** (task creation). Also mention returning to Step 2 to elaborate another story

## Error Handling

- The target story does not exist in schedule.md §3 → do not start elaborating; point the user to creating the WBS with `pm-plan-schedule` (SCH)
- schedule.md §3 is empty (template only) → stop at Step 1 and point to SCH
- Unreadable file format → guide the user with the fallback wording under "How inputs are received"
- About to overwrite an existing actuals row in progress.md §3 → do not overwrite without permission; limit yourself to appending to the comment, or get confirmation
- An interview item is never settled → do not force an assertion; leave it as an `[ASSUMPTION]` and report it as an open item in the Step 7 completion summary

## Related Files

- `references/hearing.md` — details of brainstorming Blocks 1–7
- `references/skeletons.md` — the story detail skeleton
- [`../../../project/01_management/schedule.md`](../../../project/01_management/schedule.md) — the WBS (Epic/Story), read-only
- [`../../../project/01_management/progress.md`](../../../project/01_management/progress.md) — WBS progress (§3 is updated)
- [`../../../project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) / [`non-function-list.md`](../../../project/02_requirements/non-function-list.md) — references
- [`../../../project/01_management/define-dod.md`](../../../project/01_management/define-dod.md) — the definition of done (keep the acceptance criteria consistent with it)
