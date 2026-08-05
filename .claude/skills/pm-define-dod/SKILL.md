---
name: tkm:pm-define-dod
description: >
  Creates the definition of done (define-dod.md) and performs the closing judgement. Defines completion
  criteria by category, based on the functional and non-functional requirements in function-list.md and
  non-function-list.md plus overview.md (contract type, role split) and stakeholders.md (approval flow).
  At closing it assesses how far the existing criteria have been met and records the handling of unmet
  criteria (met / waived / deferred) following the client approval flow.
  ALWAYS activate when the user mentions: definition of done, DoD, Definition of Done, closing judgement,
  completion criteria, pm-define-dod, DOD (JP-PM menu).
  SKIP: settling functional and non-functional requirements = function-list.md / non-function-list.md
  (→ pm-gather-requirements/REQ); settling the contract, organization and approval flow = overview.md /
  stakeholders.md (→ pm-plan-project/PLAN).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[create|update|closing] [<requirements specification> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-define-dod Skill

Creates the Definition of Done and performs the closing judgement. Invoked from the `DOD` menu of `jp-project-manager`.

## Target Folder (important)

**The only file written to is [`project/01_management/define-dod.md`](../../../project/01_management/define-dod.md).** Every other file is a read-only reference and must never be overwritten:

- [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) and [`project/02_requirements/non-function-list.md`](../../../project/02_requirements/non-function-list.md) — settling functional and non-functional requirements is owned by REQ.
- [`project/01_management/overview.md`](../../../project/01_management/overview.md) §1 contract type and §4 scope, and [`project/01_management/stakeholders.md`](../../../project/01_management/stakeholders.md) §2 organization and §3 approval flow — settling these is owned by PLAN.
- [`project/01_management/decision.md`](../../../project/01_management/decision.md) and [`project/01_management/risks-problems/problem-list.md`](../../../project/01_management/risks-problems/problem-list.md) — when a record is needed, only prompt the user; never `Edit` them (decision is owned by JP-PM, problem by RISK).

Within `define-dod.md`, §3 (the definitions of statuses and judgement criteria, and the flow for unmet criteria) must not be rewritten either. This skill is the side that **executes** that flow; changing the definitions is out of scope. §4 stays blank in initial-setup mode and is filled in only in closing-judgement mode.

## Purpose

Fill in §1 (list of completion criteria), §2 (category guidelines), §4 (overall closing judgement) and §5 (revision history) of [`project/01_management/define-dod.md`](../../../project/01_management/define-dod.md).

## Input

The primary input is the existing documents in the repository. On activation, `Read` the files listed under "Target folder" directly (do not ask the user for paths).

Only when those are empty or still templates (e.g. REQ has not been run) may you accept an external "requirements specification" as a substitute, supplied in any of three ways: (1) a path to a real file (`Read`), (2) pasted directly into the chat, or (3) not at all (filled in through the interview). If `Read` fails on a binary format (`.docx`, `.xlsx`, etc.), write a throwaway Python script via Bash to extract the text without asking for confirmation (`python-docx` / `openpyxl`, falling back to `zipfile` + `xml.etree`; do not leave intermediate files inside the repository). For legacy binaries (`.doc`, `.xls`) or when extraction fails, do not persist — say "please paste the relevant part as text, or give me the path again in PDF or text format". Information obtained from a substitute input must not be written into `function-list.md` / `non-function-list.md`; use it only as the basis for the DoD criteria.

## Conversation Guidelines

- Give keyword examples rather than numbered choices, and ask one question per turn within a block.
- Items involving the mode determination, a judgement, a number or an approval are never finalized without an explicit answer from the user.
- Always label a draft criterion as a "draft (needs confirmation)" and wait for it to be accepted, amended or dropped. Never write it in as a confirmed value without permission.
- Reminders to register something in `problem-list.md` / `decision.md` must not interrupt the interview — report them together in the Step 10 completion summary.

## Main Flow

**Initial-setup mode** runs Steps 1–5, 9 and 10; **closing-judgement mode** runs Steps 1 and 6–10 (Steps 2–5 are also used when the existing criteria need revisiting).

### Step 1: Confirm the input and the mode

`Read` the files listed under "Input". **If `define-dod.md` does not exist or is empty, `Write` it from `references/skeletons.md` first** (the kit ships no `project/` tree, so its absence is the normal starting state, not an error). Then check whether §1 of `define-dod.md` has any real data rows (rows whose category/criterion cells are not `<!-- e.g. ... -->`), and whether all five "Content" cells in §4 are blank.

- Zero real data rows (only the `D-001` placeholder) → assume **initial-setup mode** and proceed without confirming.
- Real data rows present, §4 blank → ask one question: "adding/revising criteria" or "closing judgement"?
- Real data rows present, §4 filled in → ask one question: "re-judgement (update)" or "adding/revising criteria"?

The final mode is always settled by what the user says.

### Step 2: Survey the existing documents (initial setup)

Organize `function-list.md` (counts by priority), `non-function-list.md` (counts and priorities by category), `overview.md` §1/§4, and `stakeholders.md` §2/§3. If `function-list.md` / `non-function-list.md` are empty, ask one question: "running REQ first would make the criteria easier to write, but we can also proceed as-is". Do not block.

### Step 3: Confirm and adjust the category guidelines (§2, hearing.md Block C)

Present the current six categories (functional requirements / non-functional requirements (quality & performance) / documents & deliverables / testing & acceptance / operational transition & handover / contract & billing) and, in light of `overview.md` §1/§4, confirm whether any should be added, removed or annotated as out of scope. `Edit` §2 if anything changes.

### Step 4: Derive the criteria for functional and non-functional requirements (§1, hearing.md Block A)

Aggregate `function-list.md` by priority and `non-function-list.md` by category, and present draft criteria as additions under new `D-xxx` IDs, **without overwriting existing non-placeholder rows**. After confirmation, `Edit` §1 (recording `F-xxx` / `NFR-xxx` in the "Related ID" column). Functions and NFRs that should be handled separately get their own rows.

### Step 5: Criteria for the other four categories (§1, hearing.md Block B, criteria-catalog.md)

In the order documents & deliverables / testing & acceptance / operational transition & handover / contract & billing, first ask whether criteria exist; if not, present a draft based on the points to consider in `references/criteria-catalog.md`. `Edit` each one as it is settled. Categories marked out of scope in Step 3 may be skipped.

### Step 6: Confirm the judgement method and evidence, and settle the status (closing, hearing.md Block D)

For each real data row in §1, confirm the result recorded in the "Judgement method / evidence" column and settle the status (met / partially met / not met). The AI must never infer the judgement. For partially met, check whether the remaining issues are registered in `problem-list.md` (do not register them yourself).

### Step 7: Handling flow for unmet and partially met criteria (closing)

Execute the four steps of §3 "Flow for unmet criteria" exactly as written:

1. Propose the handling (address and meet it / waive it out of scope / defer to the next phase) and the reason as a "draft (needs confirmation)".
2. Confirm the review and approval status (approver, approval date) with the relevant approver in `stakeholders.md` §3.
3. Only for approved rows, `Edit` and finalize the status / handling / reason / approver / approval date / update date. Leave unapproved rows on hold as "awaiting approval".
4. When an important decision arises, prompt the user to record it in `decision.md` (do not `Edit` it).

### Step 8: Fill in the §4 overall closing judgement (closing)

Confirm that every row has been judged (if unresolved rows remain, confirm that the figures are provisional). Calculate the overall achievement rate as the count of "met" ÷ the total count, and count waived and deferred items separately (confirm the calculation method with the user too). `Edit` the final approver, approval date and overall comment (draft → confirm).

### Step 9: Append to the revision history

If there was a substantive change, add one row to §5 "Revision history" with the date, the updater (`pm-define-dod skill` or the persona name) and the content.

### Step 10: Completion summary

Summarize the criteria filled in, the category adjustments, and (at closing) the achievement rate. State explicitly, as preconditions for closing, any criteria left unsettled, any handling still awaiting approval, and any records still to be registered in `problem-list.md` / `decision.md`.

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "Input".
- `function-list.md` / `non-function-list.md` are empty → recommend running REQ with exactly one question. Do not block.
- About to overwrite an existing real data row → always get confirmation before proceeding.
- A handling decision without client approval → do not finalize it; report it as "awaiting approval" in the completion summary.
- A criterion whose status or evidence is never settled → leave it blank and never guess whether it was met.
- Remaining issues from a partially met criterion are not in `problem-list.md` → prompt for registration, but never write it yourself.

## On-demand References

| Reference | When to read it |
|---|---|
| [`references/skeletons.md`](references/skeletons.md) | In Step 1, when `define-dod.md` does not exist yet |
| [`references/hearing.md`](references/hearing.md) | When running interview Blocks A–D |
| [`references/criteria-catalog.md`](references/criteria-catalog.md) | In Step 5, when proposing draft criteria |
