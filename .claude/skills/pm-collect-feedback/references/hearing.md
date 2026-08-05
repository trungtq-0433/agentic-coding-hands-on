# Interview Details (Blocks A–C)

This file collects the **example phrasings** and **answer interpretation rules** for each block. The skill refers to it and drives the conversation one question per turn within a block.

## Common Rules

- Present options **as keywords**, not as numbered choices
- Accept free-text answers (ask a clarifying question when ambiguous)
- Items requiring judgement — category, handling, status, the decision on whether to act — are never finalized without an explicit answer from the user
- Always label detected candidates as "candidate (needs confirmation)" and wait for the user to accept, amend or reject them
- Administrative reminders, such as guiding the user to run a downstream skill (pm-create-tasks / change-request / pm-track-risks-issues), must not interrupt the block's conversation — report them together in the completion summary

## Block A: Choosing the Job (→ main flow Step 1)

**Example prompt**:
> Which would you like to do for feedback management this time?
> - (1) **Status review and decisions**: go through the existing feedback (open / under consideration / in progress) and check whether a decision on acting has been made and whether the work has progressed
> - (2) **New collection**: comb the meeting minutes and the opinions raised in reviews, UAT and regular meetings for new feedback, and register it
>
> (You can also do both, in the order 2 → 1.)

**Answer interpretation rules**:
- (1) → Step 2A, (2) → Step 2B, both → run 2B then 2A (collect first, then review the decisions)
- If there is zero real data (still a template), say so and recommend (2)
- If the user names a specific piece of feedback, you may go straight into reviewing (1) or registering (2) that entry

## Block B: Reviewing and Deciding on Existing Feedback (job 1 → Step 2A)

**Present first**: list the active entries (status `Open` / `Under consideration` / `In progress`) and confirm them one at a time.

**Example prompt (deciding whether to act)**:
> Has a decision been made on feedback `FB-003` (UI/UX: show more rows on the list screen)?
> - **Act on it** (→ depending on the content, I'll guide you to raise it as a change request, an issue or a task) /
> - **Do not act** (record the reason and close it) /
> - **Still under consideration** (keep tracking it provisionally)

**Example prompt (checking progress on an in-progress entry)**:
> Has feedback `FB-005` (Function: add a field to the CSV export, related ID: T-012) progressed? If it's finished, I'll update the status to "Done".

**Answer interpretation rules**:
- **Do not act** → status `Will not act`, record the reason in the `Handling` column, and close it
- **Act on it** → following the routing in detection-catalog.md §4, guide the user to the appropriate downstream step and update the status to `In progress`:
  - Affects scope or budget → guide to `change-request.md` (CR) and put `CR-xxx` in `Related ID`
  - A bug or defect → guide to `problem-list.md` (RISK) and put `P-xxx` in `Related ID`
  - An improvement needing implementation → guide to `pm-create-tasks` (TASK) and put `T-xxx` / the Issue URL in `Related ID`
  - If the handover target's ID/URL is not yet settled, leave `Related ID` blank and say it will be backfilled next time
- **Under consideration** → status `Under consideration` (update the comment)
- **Handling complete** → status `Done`
- In every case set the update date to `currentDate`. If a judgement is ambiguous, ask a clarifying question and leave the existing value unchanged until settled

## Block C: Collecting New Feedback (job 2 → Step 2B)

**Present first**: list the candidates enumerated from the meeting minutes and human input using the detection rules in `references/detection-catalog.md` as "candidates (needs confirmation)" (source, origin, category, content). Then ask for additions.

**Example prompt (confirming the automatic detection)**:
> The following feedback candidates came up from the meeting minutes. Please tell me whether to register them, or whether they need amending or rejecting.
> (e.g. at the `regular meeting`, Mr./Ms. Suzuki said "show more rows on the list screen" → candidate, category UI/UX; during `UAT`, "the report takes a long time to load" → candidate, category Performance)

**Example prompt (additional interview)**:
> Besides the above, are there other opinions, improvement requests or observations from reviews, UAT or regular meetings? (screen usability, missing or excess functionality, documentation, performance, etc.)

**Example prompt (filling in the attributes)**:
> Please tell me this feedback's **source** (e.g. the client 〈Mr./Ms. Suzuki〉 / Sun* internal), its **origin** (review / UAT / regular meeting, etc.) and the date received. Whatever you know is fine.

**Answer interpretation rules**:
- The category must always be one of the 5 (UI/UX / Function / Documentation / Performance / Other). For vague wording, ask one question using the clues in detection-catalog.md §2 and assign it
- Never register a clear bug or a decision as feedback (detection-catalog.md §1). When the judgement is ambiguous, ask one question to route it
- Candidates that are substantially the same as an existing entry are reported as "skipped, already exists (FB-ID)" and not registered
- For handling, owner, related ID, date received and so on where the user says "we'll decide later / unknown", leave them blank, register with the initial status `Open`, and report them as open items in the completion summary
