---
name: tkm:pm-gather-requirements
description: >
  Creates the requirements documents (system-overview.md / role-list.md / function-list.md /
  non-function-list.md / glossary.md). Taking the proposal and project brief (client brief) as input, it
  captures the service overview, background problems and objectives, user roles, the function list,
  non-functional requirements and the glossary. Missing information is gathered through a natural-language
  interview. For non-functional requirements, when the user cannot provide numbers, the AI proposes a draft
  based on the project's characteristics.
  ALWAYS activate when the user mentions: requirements definition, requirements, function list,
  non-functional requirements, role list, glossary, service overview, pm-gather-requirements, REQ (JP-PM menu).
  SKIP: contract / organization / way of working = overview.md (→ pm-plan-project/PLAN); definition of done =
  define-dod.md (→ pm-define-dod/DOD); per-function details (use cases, I/O, business rules) =
  functions/ (→ requirement-analysist).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[create|update] [<proposal> <project brief> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-gather-requirements Skill

Creates the documents for the requirements definition phase. Invoked from the `REQ` menu of `jp-project-manager`.

## Target Folder (important)

**This skill works only under the target folder `project/02_requirements/`.** All reads and writes (`Read`/`Edit`) are limited to files under `project/02_requirements/`; never write into any other folder. Reading input materials (proposal, brief, etc.) is exempt from this, but deliverables must always be written under `project/02_requirements/`.

## Purpose

Fill in **these five files only**:

- [`project/02_requirements/system-overview.md`](../../../project/02_requirements/system-overview.md) — service overview, background problems, objectives (§1–§3)
- [`project/02_requirements/role-list.md`](../../../project/02_requirements/role-list.md) — user role list and permission matrix
- [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) — function list (scope)
- [`project/02_requirements/non-function-list.md`](../../../project/02_requirements/non-function-list.md) — non-functional requirements list
- [`project/02_requirements/glossary.md`](../../../project/02_requirements/glossary.md) — glossary

**Scope boundaries**:

- Do not create the per-function details under `functions/` (use cases, I/O, business rules, business flows). Leave the "Detail document" column of function-list.md blank or `TBD`, and defer it to the downstream `requirement-analysist`.
- Do not touch the contract / organization / way of working (overview.md) or the definition of done (define-dod.md).

## Input

The user may supply the proposal / project brief (client brief) in any of three ways: (1) a path to a real file (`Read`), (2) pasted directly into the chat, or (3) not at all (= to be covered by the interview from the start). If `Read` fails on a binary format (`.docx`, `.xlsx`, etc.), write a throwaway Python script via Bash to extract the text without asking for confirmation (`python-docx` / `openpyxl`, falling back to `zipfile` + `xml.etree`; do not leave intermediate files inside the repository). For legacy binaries (`.doc`, `.xls`) or when extraction fails, do not persist — say "please paste the relevant part as text, or give me the path again in PDF or text format".

## Conversation Guidelines

- **Try inferring from the documents first, and interview only about what is missing.** Even inferred items must be confirmed ("I understood this as X — is that right?") before being finalized (applies to every step).
- Run the interview in the Block O–D units of `references/hearing.md`, **one question per turn within a block**. Give keyword examples rather than numbered choices, and accept natural-language answers. When ambiguous, ask a clarifying question.
- **Never dump the background & problems (Block O §2) or the non-functional requirements (Block C) entirely on the user.** When the user cannot produce them, propose them as a "hypothesis / draft (needs client confirmation)" derived from the project's characteristics, and let the user accept, amend or drop each one. Never write them in as confirmed values without permission.
- **The glossary (Block D) is collected retroactively.** Note down business terms, abbreviations and client-specific words as they come up during Blocks O–C, then list them in Block D and confirm their definitions. Never start from zero with "tell me your terminology".
- **Do not stop the interview on questions that cannot be answered on the spot.** Items where the user says "I need to take this back / it needs client confirmation" should be logged right away in `qa.md` as a **question for the customer** so you can move on (see "Recording open items").

## Main Flow

You may repeat "confirm → apply" block by block (there is no need to run all steps in one pass).

1. **Check the inputs** — read the supplied materials and identify what is missing.
2. **Check the five existing files** — `Read` all five target files. **Any that do not exist or are empty are `Write`n from `references/skeletons.md` first** (the kit ships no `project/` tree, so a fresh repository having none of them is the normal starting state). Then classify each section and row as *empty* (guidance / template examples only) or *filled in* (real data). Never overwrite filled-in content without permission: present the existing value and ask whether to update it. If all five files are completely filled in, ask "which items would you like to update?" and switch to pinpoint handling.
3. **Overview (system-overview.md §1–§3)** — following Block O of `references/hearing.md`, interview about the service overview, background problems, and objectives / value delivered. If the client cannot produce the background and problems, propose them as a "hypothesis (needs client confirmation)" based on general characteristics such as multi-store retail. KPIs and success criteria are out of scope (owned by overview.md) and must not be written here.
4. **Roles → functions → permission matrix** — settle the roles in Block A (role-list.md §1, numbered from `ROLE-001`) and the functions in Block B (function-list.md: function name, summary, priority, target roles; leave the "Detail document" column blank). Structure the function hierarchy (Function Group → Function — Domain only for complex systems — IDs, MECE) per [`skills/_shared/extras/pm-skills/function-breakdown.md`](../_shared/extras/pm-skills/function-breakdown.md); `Read` it before you structure the hierarchy. Then have the AI draft the function × role permissions, confirm them in one pass, and apply them to role-list.md §2.
5. **Non-functional requirements (non-function-list.md)** — following Block C and `references/nfr-catalog.md`, first ask whether numeric targets exist; if not, propose a "draft (needs confirmation)" derived from the project's characteristics. Write in only the approved values. Do not mechanically fill in every category (mark inapplicable ones as out of scope).
6. **Glossary (glossary.md)** — present the terms that came up in Blocks O–C as a list and confirm their definitions together. Apply only the confirmed ones.
7. **Apply, revision history, completion summary** — apply confirmed content with `Edit` as you go. For each file with a substantive change, append one row to its "Revision history" table with the date, updater (`pm-gather-requirements skill` or the persona name) and content. Finally, report a summary of what was filled in for each of the five files, the number of open items logged in `qa.md` (awaiting customer confirmation), and the fact that the details behind function-list.md are owned by the downstream `requirement-analysist`.

## Recording Open Items (qa.md)

Items the user cannot answer on the spot during the interview and that "need client confirmation" should be logged in [`project/02_requirements/qa.md`](../../../project/02_requirements/qa.md) and left behind while you move on. **This list is intended to be shown to the customer as-is for them to answer, so write each question politely, addressed to the customer, and self-contained** (no internal assumptions or abbreviations).

- If `qa.md` is empty or does not exist, create it with `Write` using the skeleton below. If a table from `requirement-analysist` or similar already exists, append in its format and continue the QA-ID numbering.
- Each question should state "about what" and "what you want to confirm" in one sentence. Example:
  > (bad — internal memo style) What payment methods?
  > (good — addressed to the customer) Regarding the sales management function, could you tell us which payment methods need to be supported (e.g. cash / credit card / e-money / code payments)?
- Once an answer is received, set "Status" to `Answered`, fill in "Answer", "Answer date" and "Respondent", and reflect it in the relevant file (system-overview, role-list, etc.).

```markdown
# Requirements Q&A — List of Items for Customer Confirmation

> This is a list of items that could not be settled on the spot during the requirements definition
> (pm-gather-requirements) interview, for the customer to confirm. We apologize for the imposition and would
> be grateful if you could fill in the "Answer" column.

## 1. Items for Confirmation

| QA-ID | Subject | Question | Status | Raised on | Answer | Answer date | Respondent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QA-001 | (system-overview §2 etc. / F-ID) | (question addressed to the customer) | Unanswered | YYYY-MM-DD | | | |

## 2. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| YYYY-MM-DD | pm-gather-requirements skill | Raised QA-001 |
```

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "Input" above.
- Multiple inputs conflict → present both and let the user decide. Never pick one on your own.
- About to overwrite real data in an existing file → always get confirmation before proceeding.
- The user cannot decide on a non-functional requirement or on the background → leave it blank or as a hypothesis, and log it in `qa.md` as an item for customer confirmation (never force a decision).

## On-demand References

| Reference | When to read it |
|---|---|
| [`references/skeletons.md`](references/skeletons.md) | In Step 2, for any of the five files that does not exist yet |
| [`references/hearing.md`](references/hearing.md) | In Steps 3–6, when running the interview (Blocks O–D) |
| [`references/nfr-catalog.md`](references/nfr-catalog.md) | In Step 5, when proposing a draft of the non-functional requirements |
