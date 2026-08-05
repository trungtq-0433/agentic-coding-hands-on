---
name: tkm:pm-design-wireframe
description: |
  Screen wireframe creation (creating README.md + option-A/B/C.md under
  plans/project-management/screens/{screen-name}/ and updating
  plans/project-management/screens/screen-index.md). Picks a function from function-list.md or a user story from
  project/01_management/stories/, breaks it down into the screens needed, and produces 2–3 low-fi wireframe
  options (ASCII/Markdown, mobile-first) for the chosen screen so the user can pick one. Points that cannot
  be answered on the spot during the interview are collected as [ASSUMPTION] entries under "Assumptions &
  open items" in the README instead of blocking the work. Writes only under plans/project-management/ (project/ is
  read-only). Invoked from the WF menu of jp-project-manager.
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-design-wireframe Skill

The skill that takes the deliverables of the requirements and WBS phases (the function list, the user stories) as input and produces **low-fidelity screen wireframes**, **2–3 options per screen**, for the user to choose from. Invoked from the `WF` menu of the `jp-project-manager` agent.

## Purpose

Break the chosen function/story down into screens, and for the selected screen create and update:

- [`plans/project-management/screens/{screen-name}/README.md`](../../../plans/project-management/screens/) — **the screen's index**. Records the screen information (screen name, slug, related F-ID/Story, target roles), the purpose and usage context, **the list of options and a comparison table**, **the decision** (chosen option and rationale) and the assumptions and open items. Created from the README template in `references/output-template.md`.
- `plans/project-management/screens/{screen-name}/option-A.md` / `option-B.md` / `option-C.md` — **the wireframe for each option** (2–3 options). An ASCII/Markdown mobile-first wireframe plus the approach, the transitions, the data shown, how it maps to the acceptance criteria, and its pros and cons. Created from the option template in `references/output-template.md`.
- [`plans/project-management/screens/screen-index.md`](../../../plans/project-management/screens/screen-index.md) — **the catalog of all screens** (screen / slug / related F-ID & Story / number of options / chosen option / status / link). Create it with `Write` if it does not exist, and thereafter update the relevant row with `Edit`.

**Important (scope boundaries)**:

- Write **only under `plans/project-management/`**. Never write anything into `project/` (requirements, management, or the formal screen design under `project/04_screen-design/`).
- [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md), [`functions/`](../../../project/02_requirements/functions/), [`project/01_management/stories/`](../../../project/01_management/stories/), [`system-overview.md`](../../../project/02_requirements/system-overview.md), [`role-list.md`](../../../project/02_requirements/role-list.md) and [`non-function-list.md`](../../../project/02_requirements/non-function-list.md) are **read-only** (referenced only as the basis for the screen design).
- `plans/project-management/` is an exploratory workspace. Carrying the chosen option into the formal screen design (`project/04_screen-design/screen-list.md` and the specs) is **a later phase owned by someone else**, and this skill never writes there.

## Reference Documents

Load at runtime as needed:

- `references/wireframe-guide.md` — how to break work down into screens, the ASCII wireframe notation (component catalog), mobile-first principles, and the axes for differentiating the 2–3 options.
- `references/hearing.md` — the blocks of the screen UI interview (purpose & usage context / data shown / main actions & navigation / states & exceptions / multilingual & mobile constraints) and example prompts.
- `references/output-template.md` — the output templates for `README.md`, `option-X.md` and `screen-index.md`.

## How Inputs Are Received

The subject is, as a rule, a function from `function-list.md` or a user story from `stories/`. The user may supply supplementary materials (screen mockups, reference UIs, spec notes, etc.) in any of these forms:

1. **A path to a real file** — read with `Read`
2. **Pasted directly into the chat** (text / Markdown / a textual representation of a screen sketch)
3. **Nothing at all** — infer from `function-list.md`, the story details and the background information, and interview about the gaps

**Known limitation**: `Read` handles PDFs directly, but `.docx` / `.xlsx` / `.doc` / `.xls` are binary formats and cannot be read as-is. When given one of these paths, or when Read fails, you may proceed in the following order without asking for confirmation:

1. **Write a throwaway Python script via Bash to parse it**: `.docx` / `.xlsx` are ZIP + XML structures, so use `python-docx` / `openpyxl` if available; otherwise use the standard library `zipfile` + `xml.etree.ElementTree` to parse `word/document.xml` (docx) or `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` (xlsx) directly and pull out the text. Read and use the extracted text on the spot, and do not leave the script or intermediate files under the project.
2. If method 1 does not work for `.doc` / `.xls` (legacy binary formats), or the extraction result is unusable, do not persist — say "please paste the relevant part as text, or export it to PDF/text and give me the path again".

## Conversation Guidelines

- **Always try inferring from the documents first, and narrow the interview to the gaps.** Get a sense of the screen from the story's §5 scope, §6 business flow, §7 data requirements and §9 acceptance criteria, and confirm with "I understood this as X — is that right?" before finalizing.
- Run the interview block by block following `references/hearing.md`, **one block at a time** (2–4 questions each). Give keyword examples rather than numbered choices, and accept natural-language answers.
- **Do not chase questions the user cannot answer on the spot.** Say "I'll proceed with a placeholder on that point", reflect it in the wireframe marked `[ASSUMPTION]`, and collect it under "Assumptions & open items" in the README. Never block the whole exercise.
- **Mobile first.** Draw every option for a narrow screen (equivalent to ~375px) in a single column. Prefer placing the CTA within thumb reach at the bottom.
- **Differentiate the 2–3 options substantively.** Use the "axes for differentiation" in `references/wireframe-guide.md` and vary the layout/flow approach — navigation, information density, number of steps, CTA placement. Never produce options that differ only in color or spacing.
- **Finish one screen at a time.** Pick one target screen and complete its 2–3 options plus the README before moving to the next (never leave several screens half-done in parallel).
- **The language written into the files is Japanese** (repository-wide). The conversation with the user may be in the user's own language, but the body of the deliverable files and the labels inside the wireframes are written in Japanese (the default display language).

## Main Flow

### Step 1: Check the inputs and context

- `Read` [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) to grasp the function list, priorities, target roles and related WBS IDs (story IDs).
- Check [`project/01_management/stories/`](../../../project/01_management/stories/) for story details tied to the target function. If they exist, `Read` them and take in §5 scope, §6 business flow, §7 data requirements, §8 technical/non-functional, §9 acceptance criteria and §10 assumptions (the main input for the wireframes).
- Refer **read-only** to [`project/02_requirements/system-overview.md`](../../../project/02_requirements/system-overview.md), [`role-list.md`](../../../project/02_requirements/role-list.md) and [`non-function-list.md`](../../../project/02_requirements/non-function-list.md) to grasp the target platform, roles and the non-functional requirements that bear on the UI (performance, multilingual support, etc.).
- If [`plans/project-management/screens/screen-index.md`](../../../plans/project-management/screens/screen-index.md) exists, `Read` it to avoid duplicating existing screens.

### Step 2: Break down into screens (function/story → screens)

- Following "How to break work down into screens" in `references/wireframe-guide.md`, break the chosen function/story into **a list of the screens needed**. Split by the steps of the business flow, by differences in role or state, by modals and sub-screens, and so on.
- Present each screen with **a screen name (in Japanese) + a slug (romaji kebab-case, e.g. `login` / `dashboard` / `mypage-profile`) + the related F-ID/Story**.
- **Have the user choose which screen to wireframe** (one). If the user directly names a screen, use that one.

### Step 3: Screen UI interview

Following `references/hearing.md`, dig into the chosen screen block by block (infer → confirm; unsettled points become `[ASSUMPTION]`):

- **Block 1, purpose & usage context**: the screen's purpose, the roles that operate it, its entry and exit points in the business flow.
- **Block 2, data & information elements**: the information shown on screen (derived from story §7 data requirements), and whether it is read from an upstream/admin system or entered on this site.
- **Block 3, main actions & navigation**: the primary CTA, the destinations, and movement to and from other screens.
- **Block 4, states & exceptions**: empty / loading / error / no permission, etc. (derived from the story's §6 alternate and exception flows).
- **Block 5, language & mobile constraints**: the supported display languages and the default one (read them from `non-function-list.md` / `system-overview.md` — never assume a language set), mobile first, the related NFRs.

### Step 4: Produce 2–3 wireframe options

- Using the "axes for differentiation" in `references/wireframe-guide.md`, conceive **2–3 options with genuinely different approaches** (e.g. single page ↔ stepped, bottom nav ↔ hamburger, list-first ↔ card-first).
- Draw each option mobile-first using the ASCII component catalog in the same guide. Include the key states (normal / empty / error) alongside where useful. Labels are in Japanese.

### Step 5: Create the output files

- Based on `references/output-template.md`, `Write` new `plans/project-management/screens/{slug}/README.md` and `option-A.md` / `option-B.md` (and `option-C.md` if needed) files (Write creates the folder automatically).
- The README records the screen information, the purpose, the list of options (comparison table), **the decision (still "undecided" at this point)** and the assumptions and open items. Each option records the approach, the wireframe, the transitions, the data shown (from §7), how it maps to the acceptance criteria (from §9), and its pros and cons.
- `Edit` (or `Write` if it does not exist) [`plans/project-management/screens/screen-index.md`](../../../plans/project-management/screens/screen-index.md) to add the row for this screen (number of options, chosen option "undecided", status, link).
- Add one row to the revision history (where present) of the README and the index with the date (`currentDate`), the updater (`pm-design-wireframe skill` or the persona name in use) and the content.

### Step 6: Present the options and record the choice

- Present the 2–3 options to the user together with the comparison table (differentiation points, pros and cons) and **have them choose which to adopt**.
- Once chosen, `Edit` the README's "Decision" with **the chosen option, the rationale and the decision date**, and update "Chosen option" and "Status" in `screen-index.md`. If the user defers, leave it "undecided" and record that as an assumption.

### Step 7: Completion summary

- Summarize and report the screen folder and option files created, the row added to `screen-index.md`, and the outcome of the selection.
- State explicitly the remaining assumptions and open items (`[ASSUMPTION]` / needs confirmation) and which screen would be good to tackle next (one of those broken out in Step 2 that has not been started), and propose the next action.

## Error Handling

- Unreadable file format → guide the user with the fallback wording under "How inputs are received".
- Neither story details nor function details exist for the target function → do not block; design the screen hypothetically from the summary in `function-list.md` plus `system-overview.md` / `role-list.md`, and collect the points that cannot be settled as `[ASSUMPTION]` entries in the README.
- Materials contradict each other → present both statements and have the user decide. Never pick one on your own.
- About to overwrite an existing screen folder (option files) → present the existing content and confirm whether to update it or use a different slug before proceeding.
- If you feel you need to write outside `plans/project-management/` → do not write. Explain that it is out of scope and point to who owns that work (requirements = `business-analyst`, formal screen design = a later phase).

## Related Files

- `references/wireframe-guide.md` — screen breakdown, ASCII notation, mobile first, the axes for differentiation
- `references/hearing.md` — the blocks of the screen UI interview
- `references/output-template.md` — the output templates for README / option / screen-index
- [`../../../project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) — the function list (input, read-only)
- [`../../../project/01_management/stories/`](../../../project/01_management/stories/) — the user story details (input, read-only)
- [`../../../project/02_requirements/role-list.md`](../../../project/02_requirements/role-list.md) / [`non-function-list.md`](../../../project/02_requirements/non-function-list.md) / [`system-overview.md`](../../../project/02_requirements/system-overview.md) — references (read-only)
- [`../../../plans/project-management/`](../../../plans/project-management/) — the output location (the only writable area)
