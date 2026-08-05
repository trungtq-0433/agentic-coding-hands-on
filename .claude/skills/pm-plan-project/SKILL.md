---
name: tkm:pm-plan-project
description: >
  Creates the initial project plan (overview.md / stakeholders.md). Taking the proposal, project brief,
  estimate and cost sheet as input, it captures the contract, organization, way of working and constraints,
  plus the approval and escalation flows.
  Missing information is gathered through a natural-language interview and written into the two files.
  ALWAYS activate when the user mentions: initial project plan, planning, overview, stakeholders,
  organization chart, approval flow, pm-plan-project, PLAN (JP-PM menu).
  SKIP: service overview / background problems / objectives = system-overview.md (→ pm-gather-requirements/REQ);
  definition of done = define-dod.md (→ pm-define-dod/DOD); WBS and schedule (→ pm-plan-schedule/SCH).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[create|update] [<proposal> <brief> <estimate> <cost sheet> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-plan-project Skill

Creates the initial plan when a project starts. Invoked from the `PLAN` menu of `jp-project-manager`.

## Target Folder (important)

**This skill works only under the target folder `project/01_management/`.** All reads and writes (`Read`/`Edit`) are limited to files under `project/01_management/`; never write into any other folder. Reading input materials (proposal, brief, estimate, etc.) is exempt from this, but deliverables must always be written under `project/01_management/`.

## Purpose

Fill in **these two files only**:

- [`project/01_management/overview.md`](../../../project/01_management/overview.md) — contract, organization, way of working, constraints
- [`project/01_management/stakeholders.md`](../../../project/01_management/stakeholders.md) — organization, approval flow, escalation

## Input

The user may supply the proposal / project brief (client brief) / estimate / cost sheet in any of three ways: (1) a path to a real file (`Read`), (2) pasted directly into the chat, or (3) not at all (= to be covered by the interview from the start). If `Read` fails on a binary format (`.docx`, `.xlsx`, etc.), write a throwaway Python script via Bash to extract the text without asking for confirmation (`python-docx` / `openpyxl`, falling back to `zipfile` + `xml.etree`; do not leave intermediate files inside the repository). For legacy binaries (`.doc`, `.xls`) or when extraction fails, do not persist — say "please paste the relevant part as text, or give me the path again in PDF or text format".

## Conversation Guidelines

- **Try inferring from the documents first, and interview only about what is missing.** Even inferred items must be confirmed ("I understood this as X — is that right?") before being finalized (this pattern applies to every step).
- Run the interview in the Block A–F units of `references/hearing.md`, **one question per turn within a block**. Give keyword examples rather than numbered choices, and accept natural-language answers. When ambiguous, ask a clarifying question.
- The D/C/S/Q trade-off allocation (14 pts) and the KPI numbers **must always be decided by the user**. You may propose a tentative allocation, but never finalize it without permission.
- Do not block just because only some inputs are available. Mention the gap briefly and fill it in through the interview. Only when all four are missing and there is no other information, ask one question before starting: "do you have any materials? If not, I'll organize things by asking questions."
- **Do not stop the interview on items that cannot be answered on the spot and need client confirmation.** Log them right away in `qa.md` as a **question for the customer** and move on (see "Recording open items").

## Main Flow

You may repeat "confirm → apply" block by block (there is no need to run all steps in one pass).

1. **Check the inputs** — read the supplied materials and identify what is missing.
2. **Check the two existing files** — `Read` `project/01_management/overview.md` and `project/01_management/stakeholders.md`. **If either does not exist or is empty, `Write` it from `references/skeletons.md` first** and treat it as entirely empty (the kit ships no `project/` tree, so a fresh repository having neither file is the normal starting state). Then classify each cell/section as *empty* (guidance only / blank) or *filled in*. Never overwrite filled-in content without permission: present the existing value and ask whether to update it. If both files are completely filled in, ask "which items would you like to update?" and switch from a full sweep to pinpoint handling.
3. **Extract from the documents** — fill in the items you can infer, following `references/field-mapping.md` (do not write yet at this point; list them as items to confirm in Step 4).
4. **Interview (Blocks A–F)** — follow `references/hearing.md` in the order A → … → F. Use confirmation questions for items you could infer and open questions for those you could not. For Block D (scope and role split), always cross-check that it does not contradict the contract type (fixed-price / quasi-delegation) confirmed in Block A. **UAT, production infrastructure setup and data migration are often the client's responsibility**, so never assume "Sun*" and finalize it.
5. **Apply to the files** — write the confirmed content into the relevant cells with `Edit`. For substantive changes, append one row to that file's "Revision history" table with the date, the updater (`pm-plan-project skill` or the persona name) and the content (per file). The contact channels in `stakeholders.md` and the way of working in `overview.md` (communication channels / ticket management tool) share the same answer — reflect it in both (never ask twice). When filling in `overview.md`, apply the formatting rules in the Notes column of `references/field-mapping.md` at the same time.
6. **Completion summary** — for each of the two files, state a summary of what was filled in, which items were left blank (answers deferred), and the number of open items logged in `qa.md` (awaiting customer confirmation), and communicate them as open items that downstream skills (REQ / SCH / DOD, etc.) need to know before starting.

## Recording Open Items (qa.md)

Items that cannot be answered on the spot during the interview and "need client confirmation" (undecided points about contract terms, approval flow, role split, etc.) should be logged in [`project/01_management/qa.md`](../../../project/01_management/qa.md) and left behind while you move on. **This list is intended to be shown to the customer as-is for them to answer, so write each question politely, addressed to the customer, and self-contained** (no internal assumptions or abbreviations). Items decided on the Sun* side, such as the D/C/S/Q allocation or internal staffing, do not belong in qa.md (it is limited to items for customer confirmation).

- If `qa.md` is empty or does not exist, create it with `Write` using the skeleton below. If a table already exists, append in its format and continue the QA-ID numbering.
- Each question should state "about what" and "what you want to confirm" in one sentence. Example:
  > (bad — internal memo style) What's the acceptance flow?
  > (good — addressed to the customer) Regarding acceptance of the deliverables, could you tell us the expected duration from your review to approval, and which department on your side will be responsible?
- Once an answer is received, set "Status" to `Answered`, fill in "Answer", "Answer date" and "Respondent", and reflect it in the relevant file (overview.md / stakeholders.md). Items requiring a formal client decision then flow into the practice of recording them in `decision.md` after the decision (owned by JP-PM).

```markdown
# Planning Q&A — List of Items for Customer Confirmation

> This is a list of items that could not be settled on the spot during the initial project planning
> (pm-plan-project) interview, for the customer to confirm. We apologize for the imposition and would be
> grateful if you could fill in the "Answer" column.

## 1. Items for Confirmation

| QA-ID | Subject | Question | Status | Raised on | Answer | Answer date | Respondent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QA-001 | (overview §4 role split / stakeholders, etc.) | (question addressed to the customer) | Unanswered | YYYY-MM-DD | | | |

## 2. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| YYYY-MM-DD | pm-plan-project skill | Raised QA-001 |
```

## Error Handling

- Unreadable file format → follow the extraction fallback described in "Input" above (Python via Bash for `.docx` / `.xlsx`; for legacy binaries or failed extraction, ask for the text to be pasted or for a PDF/text path).
- Multiple inputs conflict (e.g. the proposal and the estimate give different contract periods) → present both and let the user decide. Never pick one on your own.
- About to overwrite real data in an existing file → always get confirmation before proceeding.

## On-demand References

| Reference | When to read it |
|---|---|
| [`references/skeletons.md`](references/skeletons.md) | In Step 2, when `overview.md` / `stakeholders.md` do not exist yet |
| [`references/field-mapping.md`](references/field-mapping.md) | In Step 3, when mapping inputs to output fields |
| [`references/hearing.md`](references/hearing.md) | In Step 4, when running the interview (Blocks A–F) |
