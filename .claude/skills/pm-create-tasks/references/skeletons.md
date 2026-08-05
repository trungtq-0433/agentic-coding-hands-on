# Skeleton for the File This Skill Owns

`Write` this when `task-list.md` **does not exist or is empty**, then append the created tasks to §1.
Never use it to overwrite a file that already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

The column order in §1 is what `references/task-breakdown.md` §5 appends against — keep it as written.

---

## `project/01_management/task-list.md`

```markdown
# Task List

> The aggregated view of the work. The details of each task live in its GitHub Issue; this file is the
> index plus the state. Tasks are always children of a Story in `schedule.md` §3 — never orphans.

## 1. Tasks

| T-ID | GitHub Issue | Task name | Related WBS ID | Assignee | Status | Start date | End date | Update date | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <!-- T-001 --> | <!-- Issue URL --> | <!-- task name (Japanese) --> | <!-- E-01-S01 --> | <!-- assignee --> | <!-- Not started --> | | | <!-- YYYY-MM-DD --> | |

## 2. Status Definitions

| Status | Meaning |
| --- | --- |
| Not started | The Issue is registered; work has not begun |
| In progress | Work is under way |
| In review | Implementation is done and under review |
| Done | Merged / accepted, and the Issue is closed |
| On hold | Blocked (state the blocker in the comment) |

## 3. Conventions

- **T-IDs** are numbered sequentially, zero-padded to three digits (`T-001`, `T-002`, …), continuing from
  one past the highest existing ID. This is the only ID series this skill mints.
- **Task names and WBS IDs are inherited verbatim** from `schedule.md` §3 and the story details.
- **Duplicate prevention** works on the pair (task name + related WBS ID). A matching row is never created
  twice; reuse the existing row's Issue URL.
- If Issue creation failed, leave "GitHub Issue" blank and put `Issue not created` in the comment, to be
  filled in on a re-run.

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-create-tasks skill --> | <!-- created --> |
```
