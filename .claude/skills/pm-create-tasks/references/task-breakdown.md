# pm-create-tasks Task Breakdown Guide

The practical guide for breaking work into tasks by phase and creating them as GitHub Issues. Referenced from Steps 2–4 of the main flow in `SKILL.md`.

## Principles of the Approach

- **Put out a starting draft first.** Assemble a breakdown draft from the WBS and the stories, then have the user confirm or amend it.
- **Inherit task names and WBS IDs.** Use the story names and IDs from schedule.md §3 and the content of the story details verbatim — never renumber or rename. The only IDs this skill assigns are the T-IDs within task-list.md.
- **Always get approval before creating.** Creating GitHub Issues is an outward-facing, hard-to-undo operation. The user must approve the Step 3 draft before you create anything in Step 4.
- **What is written into files is consistently in Japanese.** Conversation with developers may be in Vietnamese, but task-list.md and the Issue titles and bodies are in Japanese.

## 1. Phase Selection (the user chooses; an Epic is never a phase)

Per [`skills/_shared/extras/pm-skills/wbs-task-breakdown.md`](../../_shared/extras/pm-skills/wbs-task-breakdown.md), **an Epic is a function group and is never split by phase** — `pm-plan-schedule`/SCH produces feature-named Epics such as "Account management". So there is nothing to classify: **never try to read a phase out of an Epic name.**

The phase is a **separate axis, settled by the user**:

- The four phases are **requirements definition / basic design / development & implementation / testing**. They are the rows of `schedule.md` §1 (the master schedule), not entries in §3 (the WBS).
- Ask the user which phase to create tasks for, and (optionally) which Epics or stories to limit it to. Every Epic in §3 is a candidate for every phase — one feature cluster produces design tasks, development tasks and test tasks over the life of the project.
- **Cross-reference `overview.md` §4** (which lists work by phase with a "Performed by" column): present phases performed by Sun* or jointly first, and mark client-only phases as such (either excluded, or annotated when the user still wants them).
- **Duplicate prevention does the rest.** Because the same Epic is revisited once per phase, §3's (task name + related WBS ID) check is what stops a re-run from creating the same task twice — not the phase classification.

> **Legacy WBS (Epic = phase):** if the Epics in §3 are phase-named ("Requirements definition", "Testing", …) rather than feature-named, the schedule predates the current rule. Do not silently reinterpret it — say so, and ask the user whether to (a) create tasks against those Epics as-is for this run, or (b) re-run `pm-plan-schedule` (SCH) first to rebuild the WBS by function group.

## 2. Per-Phase Task Breakdown Rules

Once the phase is chosen, break work down **per story** across the in-scope Epics (the `E-xx-Sxx` entries in schedule.md §3). Every rule below applies to a story regardless of which Epic it belongs to.

### Requirements definition

- **1 story → 1 task.** Name it after the work applied to that story (e.g. `Requirements interview (<story name>)`).
- Related WBS ID = that story ID.

### Basic design

- **1 story → up to 3 tasks** (the DB task is conditional):
  1. `Write screen specification`
  2. `API design`
  3. `Database design` … only when the target involves data persistence. Create it if function-list.md or story §7 "Data requirements" mentions storing data. If you cannot judge, ask **exactly one** question: "does this story need database design?"
- Each task name may append the target story name for clarity (e.g. `Write screen specification (<story name>)`).
- Related WBS ID = that story ID (all three tasks point to the same story).

### Development & implementation

- **1 story → several tasks, one per technical element.** Read the story details (`project/01_management/stories/story-{WBS ID}-*.md`) and infer the required technical elements from:
  - §5 Scope (the in-scope functionality)
  - §6 Main business flow (screen interaction, batch, external integration?)
  - §8 Technical constraints & non-functional considerations (target devices = web/mobile, external APIs, infrastructure requirements)
- Examples of inferred elements and the default task names:
  | Technical element | Example task name |
  |---|---|
  | backend / API | `Backend implementation (<story name>)` |
  | frontend / web UI | `Frontend implementation (<story name>)` |
  | mobile | `Mobile implementation (<story name>)` |
  | infra / environment | `Infrastructure & environment setup (<story name>)` |
  | external integration | `External integration implementation (<story name>)` |
- **When the story details do not exist**: do not subdivide without permission — either point the user to elaborating it with `pm-create-stories` (STORY) first, or present the default two-way split of `Backend implementation` + `Frontend implementation` and confirm with the user.
- Related WBS ID = that story ID (every split task points to the same story).

### Testing

- **1 story → 1 task.** Task name such as `Execute tests (<story name>)`. The test target is that story.
- When the project runs several test levels (UT/IT/ST/UAT), confirm with the user which level this run covers and reflect it in the task name (e.g. `Execute IT (<story name>)`). Test levels are levels, not Epics — never expect an Epic per level.
- Related WBS ID = that story ID.

## 3. Duplicate Prevention and T-ID Numbering

- **Duplicate check:** cross-reference against the existing rows in task-list.md §1 by the pair (task name + related WBS ID). Since the phase is baked into the task name, this also keeps the design, development and test tasks of the same story distinct. If a matching row already exists, do not create it again (report it as "skipped, already exists"). Reuse the existing row's Issue URL so the same Issue is never created twice.
- **T-ID numbering:** number sequentially from one past the highest existing `T-xxx` in task-list.md §1, zero-padded to three digits (`T-001`, `T-002`, …). If there are none, start at `T-001`.
- Since the skill is designed to be run several times, always report "newly created this run" and "skipped as duplicates" separately.

## 4. GitHub Issue Body Template (in Japanese)

The body template passed to `gh issue create --body`. Quote the acceptance criteria from story §9 and attach the reference links. For phases with no story (requirements definition, etc.), keep the corresponding items brief.

```markdown
## 概要
<1–3 line summary of the work performed in this task>

## 関連WBS
- WBS ID: <E-xx-Sxx>
- 関連Story: <link to project/01_management/stories/story-{WBS ID}-{name}.md, if any>
- フェーズ: <requirements definition / basic design / development & implementation / testing>

## スコープ
<summary of story §5 in-scope. For design and testing tasks, the target deliverables>

## 受入条件（Acceptance Criteria）
<quote the acceptance criteria from story §9. If there are none, state the criteria for judging the work complete>
- [ ] ...

## 参照
- schedule.md (WBS)
- function-list.md / non-function-list.md (the relevant F-IDs / NFR-IDs)
- define-dod.md (the relevant D-IDs)
```

- **Title** = the task name (in Japanese, verbatim).
- **Label** = the phase name (`requirements` / `basic-design` / `development` / `testing`). If the label does not exist, create it first with `gh label create` (any color, e.g. requirements=`0e8a16` / basic-design=`1d76db` / development=`5319e7` / testing=`d93f0b`). Continue creating the Issue even if this fails (`|| true`).
- If the **assignee** is known you may add `--assignee`, and `--milestone` if the milestone exists on the GitHub side (both optional).

## 5. Row Format for task-list.md

After creation, append one row at a time to the §1 table (column order follows the definition in task-list.md):

```
| T-xxx | <Issue URL> | <task name> | <WBS ID> | <assignee / Claude Code> | Not started | | | <today> | <comment> |
```

- The status right after creation is `Not started` (Issue registered, work not begun).
- If Issue creation failed, leave the "GitHub Issue" column blank and put `Issue not created` in the comment column, to be filled in on a re-run.
- Append one row to §4 Revision history with the date (`currentDate`), the updater (`pm-create-tasks skill`) and the content (a summary of what was created).
