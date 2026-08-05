---
name: tkm:pm-plan-test
description: >
  Creates the test plan (test-plan.md) and the test schedule (test-schedule.md). Taking schedule.md §2/§3
  (milestones and the WBS Epics/Stories) as the primary input, it cross-references function-list.md,
  non-function-list.md (verification methods), overview.md §4 (test role split), define-dod.md
  (testing & acceptance category) and stakeholders.md §2 (QA organization) to derive the test levels,
  the test organization, the pass/fail criteria, the per-Epic test WBS and the test milestones.
  ALWAYS activate when the user mentions: test plan, test schedule, test WBS, test milestones,
  test-plan, test-schedule, pm-plan-test, TEST (JP-PM menu).
  SKIP: writing and executing test cases = testcase/ (test execution phase); definition of done =
  define-dod.md (→ pm-define-dod/DOD); the main WBS and schedule (→ pm-plan-schedule/SCH).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[create|update] [<test strategy doc> <non-functional details> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-plan-test Skill

Creates the test plan and the test schedule. Invoked from the `TEST` menu of `jp-project-manager`.

## Target Folder (important)

**Deliverables are written only under `project/05_test/`.** `project/01_management/`, `project/02_requirements/` and `project/03_basic-design/` are **read-only inputs** and must never be overwritten.

## Purpose

Fill in **these two files only** (`Write` either one from `references/skeletons.md` if it does not exist yet, then replace the `<!-- e.g. ... -->` markers with real data):

- [`project/05_test/test-plan.md`](../../../project/05_test/test-plan.md) — purpose & scope / test levels & approach / environments / organization & roles / entry & exit criteria / defect management
- [`project/05_test/test-schedule.md`](../../../project/05_test/test-schedule.md) — assumptions / test milestones / test WBS (per Epic)

Do not touch `project/05_test/testcase/` (owned by the test execution phase) or `project/01_management/define-dod.md` (owned by the DOD skill — reference only).

## Input

The primary inputs are the existing documents (`schedule.md` and others), normally read with `Read`. The user may supply supplementary materials (test strategy documents, non-functional details, etc.) in any of three ways: (1) a path to a real file, (2) pasted into the chat, or (3) not at all. If `Read` fails on `.docx` / `.xlsx`, extract the text with a throwaway Python script via Bash without asking for confirmation (`python-docx` / `openpyxl`, falling back to `zipfile` + `xml.etree`; keep intermediate files outside the repository). For legacy binaries (`.doc`, `.xls`) or when extraction fails, do not persist — say "please paste the relevant part as text, or give me the path again in PDF or text format".

## Conversation Guidelines

- **Try inferring from the documents first, and interview only about what is missing.** Even inferred items must be confirmed ("I understood this as X — is that right?") before being finalized.
- Numbers, dates and judgements — test milestone dates, severity response targets, environment details — are never finalized without an explicit answer from the user (never place provisional values).
- **Epic IDs are inherited verbatim from `schedule.md` §3** (never renumber them). Test WBS IDs use the `E-01-T01` format, and test milestones the `M-T01` format, numbered chronologically (`references/test-breakdown.md`).
- Copy performers and approvers from the rows you can read in `overview.md` §4 and `stakeholders.md` §2, and interview only about the rows you cannot read (do not re-ask every time).
- Do not stop the interview on items that cannot be answered on the spot and need client confirmation. Log them in `project/05_test/qa.md` and move on (see "Recording open items").
- Conversation with devs may be in Vietnamese, but **what is written into the files is consistently in Japanese**.

## Main Flow

You may repeat "confirm → apply" block by block.

1. **Check inputs and existing files** — `Read` `schedule.md` (§2 M-xx / §3 WBS — the primary input), `function-list.md`, `non-function-list.md`, `overview.md` §3/§4, `define-dod.md` (reference), `stakeholders.md` §2, and `test-plan.md` / `test-schedule.md` (**create either from `references/skeletons.md` if it does not exist**, then judge whether it is filled in or still a template). If `schedule.md` §3 contains only template examples, ask **exactly one** question — "running `pm-plan-schedule` (SCH) first makes per-Epic derivation easier, but we can also proceed at an overview level" — and do not block. Never overwrite real data without permission.
2. **test-plan §1 and §1.2** — the purpose (verifying functional and non-functional requirements, providing material for the release decision), the scope (all entries in `function-list.md` by default), and the target/out-of-scope systems: refer to `project/03_basic-design/system-design/architecture.md` §3/§4 if it exists, otherwise interview using `references/hearing.md`.
3. **test-plan §2 and §2.1** — keep the 4 levels (UT/IT/ST/UAT). Adjust the "performed by (AI/human)" column to match `overview.md` §3 and the AI usage policy (defaults: UT = AI / IT = AI and human / ST = human / UAT = human, client-led). Generate the §2.1 test types from the `non-function-list.md` categories (mapping table in `references/test-breakdown.md`).
4. **test-plan §3 and §3.1** — for §3.1, copy the target combinations and whether responsive testing is required from the "compatibility" entry of `non-function-list.md` (non-function-list.md is authoritative for target values). Interview using `references/hearing.md` for whatever is unknown about the environments, URLs and data preparation in §3.
5. **test-plan §4** — copy the UT/IT/ST/UAT rows of `overview.md` §4 (whether performed, and by whom); for "not required", record the reason in the notes. Approvers come from `stakeholders.md` §2. Interview only about rows you cannot read.
6. **test-plan §5 and §6** — the §5 exit criteria must be consistent with "testing & acceptance" in `define-dod.md` (reference only). §6 covers the definitions of severity Critical/High/Medium/Low and the response targets (initial values in `references/hearing.md`; response deadlines must be confirmed with the user). Keep the statement that defects are registered in `problem-list.md`.
7. **test-schedule §1 and §2** — write the §1 assumptions in the `AT-001` format (implementation and UT complete for each Epic, environment/data preparation, etc., plus the impact if an assumption breaks). For §2, record the test milestones corresponding to the `schedule.md` §2 milestones in the `M-T01` format, linking them to M-xx / Epic IDs via "Related WBS ID" (criteria in `references/test-breakdown.md`; dates confirmed with the user).
8. **test-schedule §3 test WBS (the core)** — following `references/test-breakdown.md`, generate 3 IT rows for **each Epic** in `schedule.md` §3: `E-xx-T01 write manual test cases / T02 execute / T03 fix bugs`, with the parent Epic ID in "Related Epic/Story ID". Derive the planned start/end dates iteratively from that Epic's planned end date in `schedule.md` §3 (do not make it a single pass across the whole project). ST/UAT are project-wide milestones and must be consistent with §2. Assignees come from `overview.md` §4 and `stakeholders.md` §2.
9. **Links and revision history** — check the links in test-plan §8/§9. For each file with a substantive change, append one row to its revision history (test-plan §10 / test-schedule §4) with the date (`currentDate`), the updater (`pm-plan-test skill`) and the content.
10. **Completion summary** — summarize the test WBS produced (number of Epics covered, number of IT rows), the number of test milestones and the test period, and state explicitly for downstream work the items logged in `qa.md` (awaiting customer confirmation) and the items left blank.

## Recording Open Items (qa.md)

Items that cannot be answered on the spot during the interview and need client confirmation (UAT milestone dates, test environment URLs, data preparation methods, agreement on exit criteria, severity response targets, etc.) should be logged in [`project/05_test/qa.md`](../../../project/05_test/qa.md) and left behind while you move on. **This list is intended to be shown to the customer as-is, so write each question politely, addressed to the customer, and self-contained** (no internal assumptions or abbreviations). Items decided on the Sun* side (internal staffing, etc.) do not belong here.

- If `qa.md` is empty or does not exist, create it with `Write` using the skeleton below. If a table already exists, append in its format and continue the QA-ID numbering.
- Once an answer is received, set "Status" to `Answered`, fill in "Answer", "Answer date" and "Respondent", and reflect it in test-plan / test-schedule.

```markdown
# Test Q&A — List of Items for Customer Confirmation

> This is a list of items that could not be settled on the spot during the test planning (pm-plan-test)
> interview, for the customer to confirm. We apologize for the imposition and would be grateful if you
> could fill in the "Answer" column.

## 1. Items for Confirmation

| QA-ID | Subject | Question | Status | Raised on | Answer | Answer date | Respondent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QA-001 | (test-plan §3 environments / §5 criteria / test-schedule §2 milestones, etc.) | (question addressed to the customer) | Unanswered | YYYY-MM-DD | | | |

> **Status**: `Unanswered` (awaiting a reply) / `Answered` (reply received and applied to the relevant file) / `On hold` (agreed to defer)

## 2. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| YYYY-MM-DD | pm-plan-test skill | Raised QA-001 |
```

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "Input" above.
- `schedule.md` §3 is empty (no Epics) → do not invent Epics. Propose `pm-plan-schedule` (SCH) in Step 1 and confirm whether to proceed at an overview level.
- About to overwrite real data in an existing file → always get confirmation before proceeding.
- Milestone dates or severity response targets are never settled → leave those cells blank, log them in `qa.md` and report them in Step 10 (never place provisional values).
- The performers in `overview.md` §4 and test-plan §4 conflict → present both and let the user decide (never edit `overview.md`).

## On-demand References

| Reference | When to read it |
|---|---|
| [`references/skeletons.md`](references/skeletons.md) | Step 1, when `test-plan.md` / `test-schedule.md` do not exist yet |
| [`references/test-breakdown.md`](references/test-breakdown.md) | Steps 3/7/8: Epic → test WBS breakdown, date calculation, test type mapping, milestone generation |
| [`references/hearing.md`](references/hearing.md) | Steps 2/4/6: interviewing about items that cannot be derived from the documents |
