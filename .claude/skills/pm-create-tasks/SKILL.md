---
name: tkm:pm-create-tasks
description: >
  Task creation (filling in project/01_management/task-list.md + creating GitHub Issues).
  Based on the WBS (Epic/Story) in schedule.md §3 and the story details, it breaks work down into tasks
  per phase (requirements definition / basic design / development & implementation / testing) and creates
  them after the target phase is chosen interactively.
  Each task is created as a GitHub Issue whose URL is linked from task-list.md.
  It can be invoked repeatedly over time to add or update tasks while preventing duplicates.
  ALWAYS activate when the user mentions: task creation, task breakdown, task-list, GitHub Issue,
  pm-create-tasks, TASK (JP-PM menu).
  SKIP: WBS and schedule = schedule.md (→ pm-plan-schedule/SCH);
  story details = stories/ (→ pm-create-stories/STORY);
  progress updates = progress.md (→ pm-report-project/REP).
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
argument-hint: "[requirements|basic-design|development|testing] [<WBS ID> ...]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
---

# pm-create-tasks Skill

The skill that turns the WBS (Epic/Story) in schedule.md and the story details into actual work tasks, creating them in `task-list.md` and as GitHub Issues. Invoked from the `TASK` menu of the `jp-project-manager` agent. It can be invoked any number of times over the course of the project to add new tasks and update the task list.

## Purpose

The **main purpose** is creating the following (per task: one row in task-list.md + one GitHub Issue):

- [`project/01_management/task-list.md`](../../../project/01_management/task-list.md) §1 — append one row per created task (linking the GitHub Issue URL in the "GitHub Issue" column)
- **GitHub Issues** — create each task's details (work content, acceptance criteria, references) with the `gh` CLI. task-list.md is the aggregated view; the details live in the Issue.

**Secondarily**, update:

- `plans/project-management/jp-pm-memory.md` — reflect the `## GitHub Settings` (repository), the status of the `TASK` row, and `## What To Do Next` (Steps 1 and 5)

**Important (scope boundaries)**:

- [`project/01_management/schedule.md`](../../../project/01_management/schedule.md) is **read-only**. Never create or change WBS entries (Epics/Stories) — that is owned by `pm-plan-schedule`/SCH. If §3 is empty (template examples only), do not create anything: say "please create the WBS with SCH first" and stop.
- `project/01_management/stories/story-*.md` is **read-only**. Never create or change story details — that is owned by `pm-create-stories`/STORY. This skill uses those deliverables as input (especially §5 scope, §8 technical constraints and §9 acceptance criteria).
- [`project/01_management/overview.md`](../../../project/01_management/overview.md) (§3 ticket management tool, §4 role split), [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) and [`project/01_management/define-dod.md`](../../../project/01_management/define-dod.md) are **read-only** (reference only).
- Do not touch [`project/01_management/progress.md`](../../../project/01_management/progress.md) (WBS progress — owned by `pm-create-stories` / `pm-report-project`). The only progress this skill updates is the task rows in task-list.md.

## Reference Documents

Load at runtime as needed:

- `references/skeletons.md` — the `task-list.md` skeleton, used in Step 1 when the file does not exist yet
- `references/task-breakdown.md` — phase selection, per-phase task breakdown rules, how to infer the technical elements of development tasks (BE/FE/mobile/infra), the GitHub Issue body template, and the conventions for duplicate prevention and T-ID numbering

## How Inputs Are Received

This skill's primary inputs are the already-existing [`schedule.md`](../../../project/01_management/schedule.md) §3 (the WBS) and the story details under `project/01_management/stories/`; additional files from the user are not required. The target phase is settled interactively (Step 2). If the user does supply reference materials, they can be received in any of these forms:

1. **A path to a real file** — read with `Read`
2. **Pasted directly into the chat** (text / Markdown)
3. **Nothing at all** — filled in from the existing documents (Step 1) and the conversation (Steps 2–3)

**Known limitation**: `Read` handles PDFs directly, but `.docx` / `.xlsx` / `.doc` / `.xls` are binary formats and cannot be read as-is. When given one of these paths, or when Read fails, you may proceed in the following order without asking for confirmation:

1. **Write a throwaway Python script via Bash to parse it**: `.docx` / `.xlsx` are ZIP + XML structures, so use `python-docx` / `openpyxl` if available; otherwise use the standard library `zipfile` + `xml.etree.ElementTree` to parse `word/document.xml` (docx) or `xl/sharedStrings.xml` and `xl/worksheets/sheetN.xml` (xlsx) directly and pull out the text. Read and use the extracted text on the spot, and do not leave the script or intermediate files under the project (use the OS temp directory if a temporary file is needed).
2. If method 1 does not work for `.doc` / `.xls` (legacy binary formats), if `python3` is unavailable, or if the extracted result is garbled/empty and unusable, do not keep trying other approaches — say:

> "I couldn't read this file correctly automatically. Could you paste the relevant part as text, or export it to PDF/text and give me the path again?"

## Conversation Guidelines

- **Propose proactively.** Present a starting draft of the task breakdown (a draft task list per phase) first, and have the user confirm or amend it.
- **Always stop at the phase selection and the creation approval.** At Step 2 (choosing the target phase) and at the end of Step 3 (approving the draft), wait for an explicit instruction from the user. Creating GitHub Issues is an outward-facing, hard-to-undo operation, so **never create an Issue before approval**.
- Task names and WBS IDs are **inherited verbatim** from schedule.md §3 and the stories — never renumber or rename them. The only IDs this skill assigns are the T-IDs (the sequence within task-list.md).
- You may converse with the user (a developer) in Vietnamese, but **what is written into task-list.md and the GitHub Issues is consistently in Japanese**.
- Never overwrite existing real task rows in task-list.md or re-create existing Issues without permission (duplicate prevention — see Step 3).

## Main Flow

### Step 1: Load context (grasp progress)

`Read` the following to grasp the overall picture, the WBS, the existing tasks and the GitHub settings:

- [`project/01_management/overview.md`](../../../project/01_management/overview.md) — §3 "Ticket management tool" (a clue to the GitHub repository) and §4 "Scope & role split" (whether each phase is performed by Sun*)
- [`project/01_management/schedule.md`](../../../project/01_management/schedule.md) §3 — the WBS (Epic/Story) list
- [`project/01_management/task-list.md`](../../../project/01_management/task-list.md) — the existing tasks (the basis for duplicate prevention and T-ID numbering). **If it does not exist or is empty, `Write` it from `references/skeletons.md`** — the kit ships no `project/` tree, so its absence is the normal starting state
- Scan `project/01_management/stories/` — the elaborated stories (input for breaking down development tasks)
- `plans/project-management/jp-pm-memory.md` — the repository under `## GitHub Settings`. **This file is not shipped with the kit** — the `jp-project-manager` agent creates it on first activation. If it is absent, treat every skill as "not started", carry on, and create it from the skeleton in the agent definition when you write the state back
- [`skills/_shared/extras/pm-skills/wbs-task-breakdown.md`](../_shared/extras/pm-skills/wbs-task-breakdown.md) — §1 the Task constraints (1–3 days, 1 task = 1 issue = 1 assignee, always cut as a child of a Story) and §3 the change-request flow. A kit file, always present

If schedule.md §3 is empty (template examples only), there is nothing to create tasks from — say "please create the WBS with `pm-plan-schedule` (SCH) first" and **stop**.

### Step 2: Let the user choose the phase and the scope

**An Epic is a function group, never a phase** ([`skills/_shared/extras/pm-skills/wbs-task-breakdown.md`](../_shared/extras/pm-skills/wbs-task-breakdown.md)) — so do not try to derive the phase from Epic names. Following §1 of `references/task-breakdown.md`, treat the phase as a separate axis the **user** settles:

1. List the four phases (**requirements definition / basic design / development & implementation / testing**) with their `overview.md` §4 "Performed by" value, presenting **the phases performed by Sun\*** first and marking client-only ones.
2. List the Epics and their stories from schedule.md §3 as the available scope — **every Epic is a candidate for every phase**.
3. **Ask which phase to create tasks for, and optionally which Epics or stories to limit it to. Stop here and wait for their choice.** Accept several phases at once, or a single Epic or story.

If the Epics in §3 are phase-named rather than feature-named (a WBS predating the current rule), say so and ask whether to proceed against them as-is or re-run `pm-plan-schedule` (SCH) first — never reinterpret them silently.

### Step 3: Build the task breakdown draft and get approval

For the selected phase, break the work into tasks **per story** across the in-scope Epics, using the per-phase rules in `references/task-breakdown.md` (summary):

| Phase | Task breakdown rule |
|---|---|
| Requirements definition | **One task per story** (task name = the work applied to that story) |
| Basic design | **Up to three tasks per story**: `Write screen specification`, `API design`, `Database design`. The DB task only applies when the target involves data persistence (judge from function-list / the story; if unclear, ask exactly one question) |
| Development & implementation | For each story, infer the technical elements (backend / frontend / mobile / infra, etc.) from the story details (§5 scope, §6 business flow, §8 technical constraints) and **split into one task per element**. If the story details do not exist yet, either point the user to STORY first, or present the default BE/FE split and confirm |
| Testing | **One task per story** (the test target is that story). If several test levels are in play, confirm which level this run covers and put it in the task name |

Because the phase is part of the task name, the same story legitimately yields a design task, development tasks and a test task over the project's life — the duplicate check below is what keeps a re-run from repeating any of them.

Attach the following to each draft task: **task name (in Japanese) / related WBS ID (inherited from the story ID) / phase (= the Issue label)**.

**Duplicate prevention**: cross-reference against the existing rows in task-list.md by (task name + related WBS ID); tasks that already exist are not created again — mark them "skipped, already exists". Number new tasks' T-IDs sequentially starting from one past the highest existing T-ID.

Present the breakdown result (the split between new and skipped) as a list, and **wait for the user's approval to create the GitHub Issues. Never create an Issue before approval.**

### Step 4: Settle the repository and create the GitHub Issues

1. **Settle the repository**: use the repository (`owner/repo`) under `## GitHub Settings` in jp-pm-memory.md if present. Otherwise try `gh repo view --json nameWithOwner -q .nameWithOwner` (the current repository). If it is still unknown, or a different repository is needed, **ask the user for `owner/repo`** and record it under `## GitHub Settings` in jp-pm-memory.md once settled.
2. **Prepare the labels**: create the phase-name labels (`requirements` / `basic-design` / `development` / `testing`) if they do not exist: `gh label create "<phase>" --repo <owner/repo> --color <hex> 2>/dev/null || true`.
3. **Create the Issues** (per approved task): assemble the body using the (Japanese) body template in `references/task-breakdown.md`, then run
   ```bash
   gh issue create --repo <owner/repo> --title "<task name>" --body "<body>" --label "<phase>"
   ```
   and take note of the Issue URL from stdout. The body must include the related WBS ID, a link to the related story, a scope summary, the acceptance criteria (quoted from story §9) and the reference documents.
   - If `gh` fails (not authenticated, wrong repository, insufficient permissions), stop creating Issues and report the cause. You may still append rows to task-list.md with the "GitHub Issue" column blank and `Issue not created` in the comment (the URL is filled in on a later re-run).

### Step 5: Fill in task-list.md and update the state

1. Append the created tasks to **task-list.md §1** one row at a time with `Edit`:
   `| T-xxx | <Issue URL> | <task name> | <WBS ID> | Claude Code | Not started | | | <today> | <comment> |`
   (today = `currentDate`. Record the assignee if known; otherwise a default such as `Claude Code` is fine.)
2. Append one row to **task-list.md §4 Revision history** (date = `currentDate`, updater = `pm-create-tasks skill` or the persona name in use, content = a summary of what was created).
3. Update **jp-pm-memory.md**: the repository under `## GitHub Settings`, the status of the `TASK` row (🔄 if creation continues, ✅ at a natural stopping point, together with the number created), `## What To Do Next`, and `Last updated` (today).
4. **Completion summary**: list the tasks created (T-ID, task name, Issue URL), the tasks skipped as duplicates, and any items needing confirmation. Mention returning to Step 2 to create tasks for another phase, and that re-running later can add new tasks and fill in missing URLs.

## Error Handling

- schedule.md §3 is empty (template only) → stop at Step 1 and point to `pm-plan-schedule` (SCH)
- No story details exist when breaking down development tasks → point to `pm-create-stories` (STORY), or present the default BE/FE split and get the user's confirmation (never subdivide without permission)
- `gh` not authenticated, wrong repository, insufficient permissions → stop creating Issues and report the cause. Append the rows to task-list.md only, leaving `Issue not created` in the comment, and fill them in on a re-run
- Unreadable file format → guide the user with the fallback wording under "How inputs are received"
- Existing task rows in task-list.md or already-created Issues → never overwrite or re-create them without permission (skip duplicates and report them)

## Related Files

- `references/skeletons.md` — the `task-list.md` skeleton
- `references/task-breakdown.md` — phase selection, task breakdown, Issue body template, numbering conventions
- [`../../../project/01_management/task-list.md`](../../../project/01_management/task-list.md) — the task list (this skill's main deliverable)
- [`../../../project/01_management/schedule.md`](../../../project/01_management/schedule.md) — the WBS (Epic/Story), read-only
- [`../../../project/01_management/stories/`](../../../project/01_management/stories/) — story details, read-only (input for breaking down development tasks)
- [`../../../project/01_management/overview.md`](../../../project/01_management/overview.md) — §3 ticket management tool, §4 role split, read-only
- [`../../../project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md) / [`../../../project/01_management/define-dod.md`](../../../project/01_management/define-dod.md) — references
- `plans/project-management/jp-pm-memory.md` — `## GitHub Settings` and the `TASK` state are updated
