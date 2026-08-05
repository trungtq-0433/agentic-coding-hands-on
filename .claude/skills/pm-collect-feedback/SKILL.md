---
name: tkm:pm-collect-feedback
description: >
  Feedback management (creating and updating feedback-list.md). Collects day-to-day feedback and
  improvement requests from the meeting minutes (mtg-logs) and human input, recording them by category.
  Each piece of feedback is tracked provisionally in this list until a decision is made; anything decided
  to be acted on is handed over to pm-create-tasks (TASK) to raise a GitHub Issue, and the resulting T-ID /
  Issue URL is linked in the related-ID column. Invoked from the FB menu of jp-project-manager, and can
  be run repeatedly over time to update.
  ALWAYS activate when the user mentions: feedback, improvement request, feedback-list,
  pm-collect-feedback, FB (JP-PM menu).
  SKIP: registering bugs and defects as issues = problem-list.md (→ pm-track-risks-issues/RISK);
  changes affecting scope or budget = change-request.md (→ change management/CR);
  raising tasks for improvements that need implementation = task-list.md (→ pm-create-tasks/TASK).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[review|collect] [<meeting minutes> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-collect-feedback Skill

The skill that collects the day-to-day feedback, observations and improvement requests raised in reviews, UAT, regular meetings and so on, and tracks them provisionally in `feedback-list.md`. Invoked from the `FB` menu of the `jp-project-manager` agent. Choose interactively which of the **two jobs** to do — (1) reviewing existing feedback and updating decisions/statuses, or (2) collecting new feedback from the meeting minutes and human input — and run it repeatedly over time to keep the list current.

Feedback is tracked provisionally in this list "until a decision on whether to act on it is made", and **only what is decided to be acted on** is handed over to the downstream skills (mainly `pm-create-tasks` / TASK). This skill never creates GitHub Issues itself.

## Purpose

The **main purpose** is filling in and updating:

- [`project/07_feedbacks/feedback-list.md`](../../../project/07_feedbacks/feedback-list.md) §1 (feedback list) and §4 (revision history)

**Secondarily**, update:

- `plans/project-management/jp-pm-memory.md` — the status of the `FB` row, `## What To Do Next`, and `Last updated` (Step 3). If `FB` shares a row with other codes (`REP CR RISK FB BUG TL CHK`, etc.), you may split `FB` out onto its own row

**Important (scope boundaries)**:

- The following are **read-only** (referenced only as collection input; never touch the skills that own them):
  - `project/01_management/mtg-logs/*` (the meeting minutes — the main source of feedback. Read only)
  - [`project/01_management/decision.md`](../../../project/01_management/decision.md) (decisions are not feedback. Reference only; do not prompt for records)
- The following are **handover targets** (this skill never edits or raises entries in them — it only guides the user to run the relevant skill, and copies the generated ID/URL into the `Related ID` column of feedback-list.md):
  - [`project/07_feedbacks/change-request.md`](../../../project/07_feedbacks/change-request.md) (changes affecting scope or budget. Owned by CR / change management)
  - [`project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) (bugs and defects. Owned by `pm-track-risks-issues`/RISK)
  - [`project/01_management/task-list.md`](../../../project/01_management/task-list.md) and **GitHub Issues** (owned by `pm-create-tasks`/TASK. **This skill never creates, updates or closes an Issue** — it may only check a URL with `gh issue view` and copy it)
- **Never rewrite §2 (category guidelines) or §3 (handling flow) of feedback-list.md.** These are fixed definitions, and this skill is the side that **applies** them. The allowed status values are defined in `references/detection-catalog.md`; never add new sections to the template.

## Reference Documents

Load at runtime as needed:

- `references/skeletons.md` — the `feedback-list.md` skeleton, used in Step 1 when the file does not exist yet
- `references/detection-catalog.md` — the rules for detecting feedback candidates from each input (meeting minutes / human input), the definitions of the 5 categories and how to assign them, how to route the handling (change-request / problem-list / pm-create-tasks / tracked in this list), the allowed status values and their transitions, and the conventions for FB-ID numbering, duplicate prevention and filling in the related ID
- `references/hearing.md` — example prompts and answer interpretation rules for Blocks A–C (mode selection / reviewing and deciding on existing entries / collecting new ones)

## How Inputs Are Received

This skill's primary inputs are the **meeting minutes in the repository** (`project/01_management/mtg-logs/*`) and **human input** (opinions raised in reviews, UAT and regular meetings). The meeting minutes are loaded directly with `Read` on activation (no need to ask the user for paths). If the user supplies human input or reference materials, they can be received in any of these forms:

1. **A path to a real file** — read with `Read`
2. **Pasted directly into the chat** (text / Markdown)
3. **Nothing at all** — filled in from the existing meeting minutes, feedback-list.md and the conversation

**Known limitation**: `Read` handles PDFs directly, but `.docx` / `.xlsx` / `.doc` / `.xls` are binary formats and cannot be read as-is. When given one of these paths, or when Read fails, you may proceed in the following order without asking for confirmation:

1. **Write a throwaway Python script via Bash to parse it**: `.docx` / `.xlsx` are ZIP + XML structures, so use `python-docx` / `openpyxl` if available; otherwise use the standard library `zipfile` + `xml.etree.ElementTree` to parse `word/document.xml` (docx) or `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` (xlsx) directly and pull out the text. Read and use the extracted text on the spot, and do not leave the script or intermediate files under the project (use the OS temp directory if a temporary file is needed).
2. If method 1 does not work for `.doc` / `.xls` (legacy binary formats), if `python3` is unavailable, or if the extracted result is garbled/empty and unusable, do not keep trying other approaches — say:

> "I couldn't read this file correctly automatically. Could you paste the relevant part as text, or export it to PDF/text and give me the path again?"

## Conversation Guidelines

- **Propose proactively.** Present the feedback candidates detected from the meeting minutes and the proposed decisions/status updates for existing entries as a starting point, and have the user confirm or amend them.
- **Always stop at the mode selection and before registering or updating.** At the end of Step 1 (choosing job 1 or 2) and before writing each entry into the list (draft approval), wait for an explicit instruction from the user.
- Always label detected candidates as "candidate (needs confirmation)" and wait for the user to accept, amend or reject them. **Never register anything on the AI's inference alone** (especially the category, the handling, the status, and the decision on whether to act).
- You may converse with the user (a developer) in Vietnamese, but **what is written into feedback-list.md is consistently in Japanese**.
- The category must always be one of the 5 (`UI/UX` / `Function` / `Documentation` / `Performance` / `Other`), following the definitions in feedback-list.md §2 and `references/detection-catalog.md`.
- Never overwrite existing real data rows (non-placeholder `FB-xxx`) without permission. Number new entries sequentially from one past the highest existing ID (see the steps for duplicate prevention).
- **Never confuse feedback with bugs or decisions.** Clear defects belong in problem-list, and settled agreements and decisions in decision (not handled by this skill). What this skill records is "opinions, improvement requests and observations where it is undecided whether to act".

## Main Flow

### Step 1: Load context and choose the mode

Load the following to understand the current state:

- [`feedback-list.md`](../../../project/07_feedbacks/feedback-list.md) — the existing feedback (the baseline for FB-ID numbering and duplicate prevention). **If it does not exist or is empty, `Write` it from `references/skeletons.md`** (the kit ships no `project/` tree, so its absence is the normal starting state). If the source/content cells of every row are HTML comments only (`<!-- e.g. ... -->`) and the only real data is the single `FB-001` placeholder row, judge it "still a template (not started)"
- `plans/project-management/jp-pm-memory.md` — the state of the `FB` row and `## GitHub Settings` (useful when handing over). **This file is not shipped with the kit** — the `jp-project-manager` agent creates it on first activation. If it is absent, treat every skill as "not started", carry on, and create it from the skeleton in the agent definition when you write the state back
- Collection inputs (used in job 2 — skim them here): the meeting minutes under `project/01_management/mtg-logs/`, and any human input the user supplied

Then, following Block A of `references/hearing.md`, **ask the user which job to perform. Stop here and wait for their choice**:

- **Job 1 (status review and decisions)** → Step 2A
- **Job 2 (collect and register new entries)** → Step 2B

Both may be done in sequence (the order 2 → 1 is recommended: collect first, then review the decisions). If there is zero real data (still a template), add that starting with job 2 is the natural choice.

### Step 2A: Review and decide on existing feedback (job 1)

Following Block B of `references/hearing.md`, review the **undecided and in-progress entries** one at a time (status `Open` / `Under consideration` / `In progress`):

- For each entry, confirm interactively whether a decision on acting has been made and whether the handling has progressed, then update the status, the handling, the related ID and the update date (`Edit`).
- **Decided not to act** → update the status to `Will not act` and record the reason in the `Handling` column (closed within this list).
- **Decided to act** → following the routing rules in `references/detection-catalog.md` §3, **guide** the user to the downstream step appropriate to the content (this skill never raises or registers anything):
  1. A change affecting scope, schedule or budget → guide the user to raise it formally in `change-request.md` (CR), and record the resulting `CR-xxx` in the `Related ID` column
  2. A bug or defect → guide the user to register it in `problem-list.md` (`pm-track-risks-issues`/RISK), and record the resulting `P-xxx` in the `Related ID` column
  3. Anything else (an improvement or request needing implementation) → **guide the user to run `pm-create-tasks` (TASK)** to raise a GitHub Issue, and record the resulting `T-xxx` / Issue URL in the `Related ID` column
  - In all cases update the status to `In progress`. While the handover target's ID/URL does not yet exist, leave `Related ID` blank and say it will be backfilled on the next run (you may check the URL with `gh issue view` and copy it).
- **Handling complete** → once the user confirms the work is done, update the status to `Done`.

Judgements (whether to act, status changes) are always settled by the user's explicit answer. Keep the order: present the proposed update → approval → `Edit`.

### Step 2B: Collect and register new feedback (job 2)

Following the detection rules in `references/detection-catalog.md`, enumerate **candidate** feedback from each input (entries the user raises directly are also accepted):

- Opinions, improvement requests and observations from the client or from Sun* that appear in the "Discussion" section of `mtg-logs/*`
- Improvement requests among the "Action items" in `mtg-logs/*` that have not yet been turned into tasks
- Human input (opinions raised in reviews, UAT and regular meetings)

**Exclude what is not feedback**: settled decisions (owned by decision.md) and clear bug reports (candidates for problem-list — the routing is handled in Step 2A / at handover).

Present the detected candidates as **"candidates (needs confirmation)"**, together with the date received, the source, the origin (review / UAT / regular meeting, etc.), the category (one of the 5) and the content. Following Block C of `references/hearing.md`, also accept additional entries the user raises.

**Duplicate prevention**: cross-reference against the existing real data rows in `feedback-list.md` by (content + category), and mark anything already present as "skipped, already exists (FB-ID)". **Only approved candidates** are registered in Step 3. Never write before approval.

### Step 3: Fill in the list and update state

1. **feedback-list.md §1** (approved feedback): number from one past the highest existing `FB-xxx` (zero-padded to three digits) and append one row at a time with `Edit`. The columns are:
   `| FB-xxx | Date received | Source | Origin | Category | Feedback content | Handling | Owner | Status | Related ID | Update date |`
   - Date received and update date = `currentDate` (use the meeting date from the minutes as the date received when it is known). Choose the category from the 5. The initial status is `Open`. Handling, owner and related ID may be blank before a decision.
   - If the list is still a template (`FB-001` a placeholder), replace that row with the first real data.
2. **Revision history**: append one row to feedback-list.md §4 (date = `currentDate`, updater = `pm-collect-feedback skill` or the persona name in use, content = a summary of the update).
3. **jp-pm-memory.md**: update the status of the `FB` row (🔄 if ongoing, ✅ at a natural stopping point, together with the feedback count), `## What To Do Next` and `Last updated` (today). If `FB` shares a row with other codes, you may split `FB` out onto its own row.

### Step 4: Completion summary

Report as a list: the feedback added and updated (FB-ID, category, content, status), the related links created (`Related ID` → CR/P/T/Issue), the entries skipped as duplicates, and anything left undecided. For entries decided to be acted on, prompt the user to run the corresponding downstream skill (`pm-create-tasks` / `change-request` / `pm-track-risks-issues`). Recommend reviewing after regular meetings and UAT, and mention that re-running later allows status review, new additions and backfilling the related IDs.

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "How inputs are received"
- feedback-list.md does not exist → the normal first-run state, not an error: `Write` it from `references/skeletons.md` and carry on
- feedback-list.md is still a template (zero real data) → do not block; start with job 2 (collect and register). The placeholder `FB-001` row may be replaced by the first real data
- `mtg-logs/` is empty or no minutes exist → skip detection from the minutes and continue with human input as the primary source (do not block)
- Category, handling or status are never settled → leave them blank and do not fill them in by guesswork. Report them as open items in the completion summary
- The handover target's (pm-create-tasks / change-request / problem-list) ID/URL does not exist yet → leave `Related ID` blank, set the status to `In progress`, and say it will be backfilled on the next run
- About to overwrite an existing real data row → always get confirmation before proceeding (skip duplicates and report them)

## Related Files

- `references/skeletons.md` — the `feedback-list.md` skeleton
- `references/detection-catalog.md` — detection rules, category definitions, routing, statuses, ID and related-ID conventions
- `references/hearing.md` — prompts and interpretation rules for Blocks A–C
- [`../../../project/07_feedbacks/feedback-list.md`](../../../project/07_feedbacks/feedback-list.md) — the feedback list (this skill's main deliverable)
- `../../../project/01_management/mtg-logs/` — the meeting minutes (collection input), read-only
- [`../../../project/07_feedbacks/change-request.md`](../../../project/07_feedbacks/change-request.md) — handover target for scope and budget changes; this skill never edits it (guidance only)
- [`../../../project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) — handover target for bugs and defects; this skill never edits it (guidance only)
- [`../../../project/01_management/task-list.md`](../../../project/01_management/task-list.md) — handover target for tasks / GitHub Issues; this skill never raises them (owned by `pm-create-tasks`; URL copying only)
- `plans/project-management/jp-pm-memory.md` — the `FB` state is updated
