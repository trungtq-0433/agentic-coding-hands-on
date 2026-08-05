# pm-create-stories Interview (Brainstorming) Guide

The conversation guide for producing story details. Referenced from Step 4 of the main flow in `SKILL.md`.

## Principles of the Approach

- **Brainstorm proactively.** Rather than simply listing questions, present a hypothesis you can read from the existing materials (overview / system-overview / function-list / non-function-list / the function details under functions) and use it as a starting point to draw out the user's views.
- **Ask in small groups.** Never ask ten questions spanning multiple blocks in one message. Limit yourself to **2–4 questions per block** and move to the next block only after receiving the user's answers.
- **`Edit` the relevant section as each answer comes in** (do not batch the writing until the end).
- **Handling "I don't know / later":** when the user answers "I don't know", "later" or "your call", do not press further on that point. Form **a reasonable hypothesis** from the project's characteristics, the existing materials and similar work in general, **write it in the body prefixed with `[ASSUMPTION] ...`**, and append one row to §10 "Assumptions & open items". Add a one-line rationale for the hypothesis.
- **The project is in Japanese, but you may converse with the user (a developer) in Vietnamese.** What is written into the files, however, is consistently in Japanese.
- **When an answer contradicts the existing materials**, present both and confirm (never pick one on your own).

## Block 1: Purpose & Problem Solved → §3 "Background & purpose"

- **Aim:** articulate why this story is needed and which business problem it solves.
- **Example prompts:**
  - What is the biggest operational pain or inefficiency this story should solve?
  - How is that work handled today (manually, in another system, on paper, etc.)?
  - Once this is in place, whose outcome does it improve, and how (time saved, fewer mistakes, revenue, etc.)?
- **[ASSUMPTION] default:** infer the purpose from the "Summary" column of the related function (function-list.md) and system-overview.md §2 (background & problems), and record it with `[ASSUMPTION]`.

## Block 2: Target Users → §4 "Target users"

- **Aim:** identify the main users (roles) and the usage situations.
- **Example prompts:**
  - Who mainly uses this function? (which role in role-list.md)
  - In what situations and how often is it used (daily / occasionally, PC / phone, on site / in the office)?
  - Does it include users who are not comfortable with IT? (this affects UI assumptions)
- **[ASSUMPTION] default:** inherit the "Target roles" column from function-list.md, and infer the usage situations from the nature of the work with `[ASSUMPTION]`.

## Block 3: Scope (In / Out) → §5 "Scope"

- **Aim:** draw the boundary between what this story does and does not cover. Prevents scope creep.
- **Example prompts:**
  - What must definitely be included in this story?
  - Conversely, is there anything to exclude this time and push to another story or the next phase?
  - Are there boundaries with similar functions (overlaps, division of responsibility)?
- **[ASSUMPTION] default:** treat the scope of the related function as in-scope and adjacent functions that have their own story IDs as out-of-scope, recorded with `[ASSUMPTION]`.

## Block 4: Main Business Flow → §6 "Main business flow"

- **Aim:** draw the central flow of the work (actors, trigger, main flow, exceptions).
- **Example prompts:**
  - Please walk me through using this function end to end, from the trigger to completion.
  - Are there branches, approvals or rejections along the way?
  - What happens on failure or in exceptional cases (input errors, missing permissions, inconsistent data, etc.)?
- **[ASSUMPTION] default:** quote the corresponding flow from the function details under functions/ if present. Otherwise use a generic CRUD or request-approval flow as a starting draft, with `[ASSUMPTION]`.

## Block 5: Data Requirements → §7 "Data requirements"

- **Aim:** enumerate the data items to be newly stored or updated. Nailing down types and lengths can wait for the design phase.
- **Example prompts:**
  - What data does this function newly register or store (the main items)?
  - Are there required vs. optional fields, record-count limits or retention constraints?
  - Is there data received from or passed to other systems or functions?
- **[ASSUMPTION] default:** infer the main items from the business flow and the I/O, and record them with `[ASSUMPTION]` plus the note "types and constraints to be settled in the design phase".

## Block 6: Technical Constraints & Non-functional Considerations → §8 "Technical constraints & non-functional considerations"

- **Aim:** tie constraints on performance, security, availability, target devices, external integrations, etc. back to non-function-list.md.
- **Example prompts:**
  - Is there anything to keep in mind regarding performance, concurrent use or data volume? (mapped to the NFRs in non-function-list)
  - Are there security concerns such as permission control or personal data?
  - Are there technical premises such as target devices, browsers, offline use or external APIs?
- **[ASSUMPTION] default:** quote the project-wide NFRs from non-function-list.md as applying to this story. If story-specific additional constraints are unknown, mark them `[ASSUMPTION]`.

## Block 7: Acceptance Criteria → §9 "Acceptance criteria"

- **Aim:** define concrete, verifiable conditions for judging the story "done". These become the basis for design, testing and pm-create-tasks.
- **Example prompts:**
  - What has to be true for you to say "this story is complete"? (in a form where pass/fail can be judged)
  - Are there business rules or validations that must be satisfied?
  - Are there relevant completion criteria (D-IDs) in define-dod.md?
- **[ASSUMPTION] default:** draft the acceptance criteria in Given/When/Then form from successful completion of the main flow plus the key validations plus the related D-IDs, marked `[ASSUMPTION]`. **Never leave the acceptance criteria empty** (downstream pm-create-tasks uses them, so always put down at least a starting draft).
