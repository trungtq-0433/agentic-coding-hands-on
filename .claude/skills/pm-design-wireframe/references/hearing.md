# Screen UI Interview Guide

Example prompts and interpretation tips for gathering the information needed to draw the wireframes for the chosen screen, used in Step 3 of the `pm-design-wireframe` skill. Proceed **one block at a time (2–4 questions each)**, presenting your inference first and confirming it. Do not chase questions that cannot be answered on the spot — mark them `[ASSUMPTION]` and collect them under "Assumptions & open items" in the README.

---

## Common Rules

- **Infer first, confirm briefly.** Present what you can read from the story (§5 scope, §6 business flow, §7 data requirements, §9 acceptance criteria), `function-list.md` and `role-list.md` as a hypothesis, and confirm with "I understood this as X — is that right?"
- **Proceed block by block.** In the order Block 1 → 5 below. Limit each block to 2–4 questions, give keyword examples, and accept natural-language answers (never force a numbered choice).
- **"I don't know / decide later" must not stop the work.** Adopt the `[ASSUMPTION] default`, reflect it in the wireframe, and leave it under "Assumptions & open items" in the README as something to confirm.
- **What is written into the files is Japanese.** The conversation language is free, but the deliverables (README, options, the labels inside the wireframes) are written in Japanese (the default display language).
- **Never decide on your own when things conflict.** If the materials disagree, present both and have the user settle it.
- **Do not break the mobile-first premise.** Translate every answer into "how does this look in a single column on a narrow screen?"

The information from each block maps to the sections of the option template in `references/output-template.md` (see "Reflected in" for each block).

---

## Block 1: The Screen's Purpose & Usage Context → option §1 Approach / README §2 Purpose & usage context

**Aim**: articulate in 1–2 sentences what the screen is for, who uses it and when, and where it sits in the business flow.

**Example prompts**:
- "Is the main purpose of this screen X (e.g. letting the user sign in to the system)?"
- "Is it mainly ROLE-00X (e.g. guest) who operates it? Do other roles use it too?"
- "In the business flow, where does the user come from **immediately before** this screen, and where do they go **after success**? (From story §6 I read it as X.)"

**Answer interpretation rules**:
- If there are several purposes, narrow it to one main purpose (put the secondary ones in the README's supplementary notes).
- Identify roles by their ID in `role-list.md`. If the elements shown vary by role, handle that difference in Block 4 (states).

**[ASSUMPTION] defaults**: preceding/next screen unknown → place a provisional value following the main flow in story §6. Role unknown → adopt the target roles from `function-list.md`.

## Block 2: Data & Information Elements → option §4 Data shown / the wireframe itself

**Aim**: enumerate the information elements on the screen and where each comes from (read from an upstream/admin system, or entered and saved on this site).

**Example prompts**:
- "Are the main items shown on this screen X and Y (from story §7 data requirements)?"
- "Are these **only read and displayed** from an upstream system, or does the user **enter and edit** them here?"
- "For a list, what do you show per item? (e.g. title, one or two supporting attributes, a status, an action button)"

**Answer interpretation rules**:
- Always distinguish **display-only vs. editable** (show the difference in the wireframe: display-only as label + value, editable as an input field).
- When there are many items, prioritize them and order them top-down by importance in the single mobile column.
- For sensitive information (personal identification documents, payment details, health data, etc. — whatever this project handles), confirm how much is displayed and whether masking is required.

**[ASSUMPTION] defaults**: source unknown → take the default from what `system-overview.md` says about where the data is mastered; if it says nothing, assume the screen is **display-only** and mark it `[ASSUMPTION]`. Field details undecided → include only the main items and note "to be settled in a later phase".

## Block 3: Main Actions & Navigation → option §3 Screen transitions & main navigation / the CTA in the wireframe

**Aim**: decide the primary action (CTA) on this screen, and the transitions and movement to and from other screens.

**Example prompts**:
- "Is the **main action** on this screen X (e.g. 'Sign in', 'Submit application')? Are there secondary actions (e.g. language switching, sign out)?"
- "Where does the user go after the action succeeds, and after it fails?"
- "Does the user need a way to move from this screen to others (e.g. the dashboard, My Page)? (bottom nav / menu, etc.)"

**Answer interpretation rules**:
- Narrow the primary CTA to one and place it in the mobile thumb zone (the lower part of the screen). Do not over-emphasize secondary actions.
- Record the transitions in option §3 as a simple flow (using the `→` notation) under "Screen transitions & main navigation".

**[ASSUMPTION] defaults**: destination undecided → place a provisional value following the postconditions in story §6. Navigation presence unknown → assume no navigation for single-purpose screens and a bottom nav for screens requiring browsing (this may itself differentiate the options).

## Block 4: States & Exceptions → option §2 Wireframe (per state) / README assumptions

**Aim**: enumerate the non-happy-path screen states (empty, loading, error, no permission, etc.) and reflect them in the wireframe.

**Example prompts**:
- "Do you need a display for when there is no data (the empty state)? (e.g. a list with zero matching records)"
- "How should errors be shown (e.g. authentication failure, network error, invalid input)? From story §6 alternate/exception flows I read it as X."
- "Does the display change by role or state? (e.g. an indicator while an account is still pending verification)"

**Answer interpretation rules**:
- Include the key states in the wireframe as **per-state blocks** (there is no need to draw every state — prioritize the ones that change a design decision).
- Match the granularity of error messages (generic display only vs. detailed guidance) to the story's approach (e.g. an invalid account gets only a generic error).

**[ASSUMPTION] defaults**: state requirements unstated → provide at minimum the empty and error states as placeholders. Multilingual error wording need not be settled (just the container).

## Block 5: Language & Mobile Constraints → option §2 Wireframe / README §2 supplementary notes

**Aim**: reflect this project's language support and the mobile-first constraints in the layout.

**First read the language set from the documents.** The supported display languages and the default one come
from `non-function-list.md` (the multilingual / internationalization entry) or `system-overview.md` — **never
assume a particular language set**. A single-language project needs no switcher at all, and the number of
languages changes the layout tolerance you have to design for.

**Example prompts**:
- "From non-function-list.md I read the display languages as {the languages actually listed there}, with {X} as the default — is that right? Should the switcher UI live on this screen?"
- "Is the target mainly the smartphone browser? (Should we also consider desktop?)"
- "Are there constraints on performance, accessibility, etc. that affect the UI? (e.g. the login screen renders within 3 seconds = NFR-002)"

**Answer interpretation rules**:
- When the project is multilingual, the position of the language switcher UI can itself differentiate the options (a dropdown in the header vs. consolidated into a settings screen, etc.).
- Assume label lengths vary across whichever languages the project supports: use a layout that tolerates wrapping and truncation.
- Where there is a related NFR, note its ID in option §5 or the README's technical notes.

**[ASSUMPTION] defaults**: the documents say nothing about languages → assume **single-language, no switcher** and mark it `[ASSUMPTION]` (never invent a second language). Multilingual but the need for a switcher is unknown → provisionally place it on entry screens such as login and consolidate it into settings for internal screens. Target device unknown → adopt mobile-primary (responsive).

---

## Quick Reference: Block → Output Mapping

| Block | Theme | Mainly reflected in |
|---|---|---|
| 1 | Purpose & usage context | option §1 Approach, README §2 Purpose & usage context |
| 2 | Data & information elements | option §4 Data shown, the wireframe itself |
| 3 | Main actions & navigation | option §3 Screen transitions & main navigation, the CTA in the wireframe |
| 4 | States & exceptions | option §2 Wireframe (per state), README assumptions |
| 5 | Multilingual & mobile constraints | option §2/§5, README §2 supplementary and technical notes |
