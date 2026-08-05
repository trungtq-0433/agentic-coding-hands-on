---
name: tkm:pm-track-risks-issues
description: >
  Risk and issue management (risk-list.md / problem-list.md): status review and new registration.
  Reviews the status of existing risks/issues interactively, and detects new risks/issues from
  schedule.md, progress.md, GitHub Issues, meeting minutes, the change tracker and so on, registering
  them by category. When a risk materializes, it is registered as an issue and the two are cross-linked
  via the originating risk ID and related issue ID.
  Invoked from the RISK menu of jp-project-manager, and can be run repeatedly over time to update.
  ALWAYS activate when the user mentions: risk management, issue management, risk, issue, risk-list,
  problem-list, pm-track-risks-issues, RISK (JP-PM menu).
  SKIP: changes affecting scope or budget = change-request.md (→ change management/CR);
  day-to-day feedback = feedback-list.md (→ pm-collect-feedback/FB);
  settled decisions = decision.md.
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[review|detect] [<meeting minutes> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-track-risks-issues Skill

The skill that manages the project's risks (things that have not happened yet but could) and issues (problems that have actually occurred). Invoked from the `RISK` menu of the `jp-project-manager` agent. Choose interactively which of the **two jobs** to do — (1) reviewing the status of existing risks/issues, or (2) detecting and registering new ones — and run it repeatedly over time to keep the lists current.

## Purpose

The **main purpose** is filling in and updating **two files**:

- [`project/01_management/risks-problems/risk-list.md`](../../../project/01_management/risks-problems/risk-list.md) §1 (risk list) and §4 (revision history)
- [`project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) §1 (issue list) and §4 (revision history)

**Secondarily**, update:

- `plans/project-management/jp-pm-memory.md` — the status of the `RISK` row, `## What To Do Next`, and `Last updated` (Step 3)

**Important (scope boundaries)**:

- The following are **read-only** (referenced only as detection input; never touch the skills that own them):
  - [`project/01_management/schedule.md`](../../../project/01_management/schedule.md) (owned by `pm-plan-schedule`/SCH)
  - [`project/01_management/progress.md`](../../../project/01_management/progress.md) (progress updates are owned by REP and others)
  - [`project/01_management/overview.md`](../../../project/01_management/overview.md) / [`project/01_management/stakeholders.md`](../../../project/01_management/stakeholders.md) (refer to §3, the approval flow) / [`project/01_management/task-list.md`](../../../project/01_management/task-list.md)
  - [`project/07_feedbacks/change-request.md`](../../../project/07_feedbacks/change-request.md) / `project/01_management/mtg-logs/*`
  - **GitHub Issues** (read only via the `gh` CLI. Never create, update or close an Issue)
- Do not touch [`project/01_management/decision.md`](../../../project/01_management/decision.md). When an important decision arises from a handling plan, only prompt the user to record it — never `Edit` it.
- **Never rewrite §2 (judgement criteria) or §3 (status definitions) of the two files.** These are fixed definitions, and this skill is the side that **applies** them.

## Reference Documents

Load at runtime as needed:

- `references/skeletons.md` — the `risk-list.md` / `problem-list.md` skeletons, used in Step 1 when a file does not exist yet
- `references/detection-catalog.md` — the rules for detecting risk and issue candidates from each input (schedule / progress / GitHub Issues / change management / meeting minutes), the definitions of the 6 categories and how they map to the user's own wording (management / progress / quality / technical), the criteria for separating risks from issues, and the conventions for ID numbering, duplicate prevention and cross-linking
- `references/hearing.md` — example prompts and answer interpretation rules for Blocks A–C (mode selection / reviewing existing entries / interviewing about new ones)

## How Inputs Are Received

This skill's primary inputs are the **existing documents in the repository** (the two files themselves plus schedule.md, progress.md, etc.) and **GitHub Issues** (`gh issue list` / `gh issue view`), loaded directly on activation with `Read` / `Bash` (no need to ask the user for paths). In addition, if the user supplies reference materials (EM task reports, meeting minutes, change trackers, etc.), they can be received in any of these forms:

1. **A path to a real file** — read with `Read`
2. **Pasted directly into the chat** (text / Markdown)
3. **Nothing at all** — filled in from the existing documents and the conversation

**Known limitation**: `Read` handles PDFs directly, but `.docx` / `.xlsx` / `.doc` / `.xls` are binary formats and cannot be read as-is. When given one of these paths, or when Read fails, you may proceed in the following order without asking for confirmation:

1. **Write a throwaway Python script via Bash to parse it**: `.docx` / `.xlsx` are ZIP + XML structures, so use `python-docx` / `openpyxl` if available; otherwise use the standard library `zipfile` + `xml.etree.ElementTree` to parse `word/document.xml` (docx) or `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` (xlsx) directly and pull out the text. Read and use the extracted text on the spot, and do not leave the script or intermediate files under the project (use the OS temp directory if a temporary file is needed).
2. If method 1 does not work for `.doc` / `.xls` (legacy binary formats), if `python3` is unavailable, or if the extracted result is garbled/empty and unusable, do not keep trying other approaches — say:

> "I couldn't read this file correctly automatically. Could you paste the relevant part as text, or export it to PDF/text and give me the path again?"

## Conversation Guidelines

- **Propose proactively.** Present the detected risk/issue candidates and the proposed status updates for existing entries as a starting point, and have the user confirm or amend them.
- **Always stop at the mode selection and before registering or updating.** At the end of Step 1 (choosing job 1 or 2) and before writing each entry into a list (draft approval), wait for an explicit instruction from the user.
- Always label detected candidates as "candidate (needs confirmation)" and wait for the user to accept, amend or reject them. **Never register anything on the AI's inference alone** (especially probability, impact, priority and status).
- You may converse with the user (a developer) in Vietnamese, but **what is written into risk-list.md and problem-list.md is consistently in Japanese**.
- The category must always be one of the 6 (`Technical` / `Schedule` / `Budget & contract` / `Quality` / `Team & staffing` / `Customer relations`), following the definitions in `references/detection-catalog.md`.
- Never overwrite existing real data rows (non-placeholder `R-xxx` / `P-xxx`) without permission. Number new entries sequentially from one past the highest existing ID (see the steps for duplicate prevention).

## Main Flow

### Step 1: Load context and choose the mode

Load the following to understand the current state:

- [`risk-list.md`](../../../project/01_management/risks-problems/risk-list.md) / [`problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) — the existing risks/issues (the baseline for ID numbering and duplicate prevention). **If either does not exist or is empty, `Write` it from `references/skeletons.md`** (the kit ships no `project/` tree, so their absence is the normal starting state). If the category/content cells of every row are HTML comments only (`<!-- e.g. ... -->`) and the only real data is the single `R-001` / `P-001` placeholder row, judge it "still a template (not started)"
- `plans/project-management/jp-pm-memory.md` — the state of the `RISK` row and `## GitHub Settings` (the repository). **This file is not shipped with the kit** — the `jp-project-manager` agent creates it on first activation. If it is absent, treat every skill as "not started", carry on, and create it from the skeleton in the agent definition when you write the state back
- Detection inputs (used in job 2 — skim them here): `schedule.md`, `progress.md`, `feedbacks/change-request.md`, `mtg-logs/`, and `gh issue list` (the repository under `## GitHub Settings`; skip if unauthenticated or unconfigured)

Then, following Block A of `references/hearing.md`, **ask the user which job to perform. Stop here and wait for their choice**:

- **Job 1 (status review)** → Step 2A
- **Job 2 (detect and register new entries)** → Step 2B

Both may be done in sequence (the order 1 → 2 is recommended). If there is zero real data (still a template), add that starting with job 2 is the natural choice.

### Step 2A: Review the status of existing risks/issues (job 1)

Following Block B of `references/hearing.md`, review the **active entries** one at a time (`Monitoring` in risk-list; `Open` / `In progress` / `On hold` in problem-list):

- For each entry, confirm interactively whether it is still valid, whether the situation has changed, and whether the handling has progressed, then update the status, the handling content and the update date (`Edit`).
- **A risk materializing**: when the user judges that a `Monitoring` risk has actually occurred,
  1. Register a new `P-xxx` in `problem-list.md` (record that risk's `R-xxx` in `Originating risk ID`; inherit the category from the risk)
  2. Update the original risk row to `Occurred (became an issue)` and record that `P-xxx` in `Related issue ID`
- **A risk disappearing**: risks that are no longer needed due to a change in circumstances are updated to `Resolved` (resolved by the countermeasure) or `No action needed` (minor impact, circumstances changed).
- **Closing an issue**: once the user confirms the handling is complete, update it to `Resolved` and record the handling content and comments.

Judgements (status changes, whether to turn a risk into an issue) are always settled by the user's explicit answer. Keep the order: present the proposed update → approval → `Edit`.

### Step 2B: Detect and register new risks/issues (job 2)

Following the detection rules in `references/detection-catalog.md`, enumerate **candidate** risks/issues from each input (entries the user raises directly are also accepted):

- Delays, placeholder assumptions and unsettled effort in `schedule.md` / `progress.md` → a `Schedule` or `Team & staffing` risk; a confirmed delay → a `Schedule` issue
- Blockers listed in the "Blockers & related issue IDs" column of `progress.md` → an issue
- GitHub Issues (`bug` label, long-stalled items, technical issues with external dependencies) → a `Quality` / `Technical` issue or risk
- Unagreed changes in `change-request.md` → a `Budget & contract` / `Customer relations` risk
- Concerns raised in meeting minutes or by a person

Present the detected candidates as **"candidates (needs confirmation)"**, together with whether each is a risk or an issue, its category (one of the 6), its content and a proposed owner. Following Block C of `references/hearing.md`, also accept additional entries the user raises.

**Duplicate prevention**: cross-reference against the existing real data rows in `risk-list.md` / `problem-list.md` by (content + category), and mark anything already present as "skipped, already exists". **Only approved candidates** are registered in Step 3. Never write before approval.

### Step 3: Fill in the lists and update state

1. **risk-list.md §1** (approved risks): number from one past the highest existing `R-xxx` and append one row at a time with `Edit`.
   - Choose the category from the 6. Enter high/medium/low for probability and impact after confirming with the user, and determine the risk level using the judgement matrix in §2 (never rewrite the matrix). The response strategy is avoid / mitigate / transfer / accept. Discovery date and update date = `currentDate`. The initial status is `Monitoring`.
2. **problem-list.md §1** (approved issues): number from one past the highest existing `P-xxx` and append one row at a time with `Edit`.
   - Fill in the category, priority (high/medium/low per the guidelines in §2), the response plan, the owner and the deadline. Fill in `Originating risk ID` only when it came from a risk. Discovery date and update date = `currentDate`. The initial status is `Open`.
3. **Revision history**: append one row to §4 of each updated file (date = `currentDate`, updater = `pm-track-risks-issues skill` or the persona name in use, content = a summary of the update).
4. **jp-pm-memory.md**: update the status of the `RISK` row (🔄 if ongoing, ✅ at a natural stopping point, together with the risk/issue counts), `## What To Do Next` and `Last updated` (today). If `RISK` shares a row with other codes (`REP CR RISK FB BUG TL CHK`, etc.), you may split `RISK` out onto its own row.

### Step 4: Completion summary

Report as a list: the risks/issues added and updated (ID, category, content), the cross-links created (`R-xxx` ⇔ `P-xxx`), the entries skipped as duplicates, and anything left unsettled. If an important decision arises from a handling plan, prompt the user to record it in `decision.md` (never `Edit` it yourself). Recommend reviewing it at the regular meeting, and mention that re-running later allows status review and new additions.

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "How inputs are received"
- Either file does not exist → the normal first-run state, not an error: `Write` it from `references/skeletons.md` and carry on
- Both files are still templates (zero real data) → do not block; start with job 2 (detect and register). The placeholder `R-001` / `P-001` rows may be replaced by the first real data
- `gh` not authenticated, repository not configured, insufficient permissions → skip only the GitHub Issue detection, report that, and continue with the other inputs (schedule / progress / meeting minutes, etc.). Do not block
- Probability, impact, priority or status are never settled → leave them blank and do not fill them in by guesswork. Report them as open items in the completion summary
- About to overwrite an existing real data row → always get confirmation before proceeding (skip duplicates and report them)

## Related Files

- `references/skeletons.md` — the `risk-list.md` / `problem-list.md` skeletons
- `references/detection-catalog.md` — detection rules, category definitions, ID and cross-link conventions
- `references/hearing.md` — prompts and interpretation rules for Blocks A–C
- [`../../../project/01_management/risks-problems/risk-list.md`](../../../project/01_management/risks-problems/risk-list.md) — the risk list (this skill's main deliverable)
- [`../../../project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) — the issue list (this skill's main deliverable)
- [`../../../project/01_management/schedule.md`](../../../project/01_management/schedule.md) / [`../../../project/01_management/progress.md`](../../../project/01_management/progress.md) — detection input, read-only
- [`../../../project/07_feedbacks/change-request.md`](../../../project/07_feedbacks/change-request.md) / `../../../project/01_management/mtg-logs/` — detection input, read-only
- [`../../../project/01_management/overview.md`](../../../project/01_management/overview.md) / [`../../../project/01_management/stakeholders.md`](../../../project/01_management/stakeholders.md) — references, read-only
- [`../../../project/01_management/decision.md`](../../../project/01_management/decision.md) — important decisions are only prompted for, never edited
- `plans/project-management/jp-pm-memory.md` — the `RISK` state is updated
