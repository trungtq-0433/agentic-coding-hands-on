# Skeleton for the File This Skill Owns

`Write` this when `schedule.md` **does not exist or is empty**, then fill it in through the interview.
Never use it to overwrite a file that already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

Keep the `<!-- e.g. ... -->` markers on placeholder rows: `pm-create-stories`, `pm-create-tasks`, `pm-plan-test` and
`pm-report-project` all use "§3 holds only HTML comments" as the signal for "the WBS is not started yet".

---

## `project/01_management/schedule.md`

```markdown
# Schedule

> The plan baseline. Actual progress against it is recorded in `progress.md` (owned by `pm-report-project`).
> Assumptions and constraints belong in `overview.md` — never write them here.
> **The WBS goes down to the Story level only.** Tasks live in `task-list.md` (owned by `pm-create-tasks`).

## 1. Master Schedule (by phase)

> One row per work item in `overview.md` §4. Client-side phases stay listed, so dependencies stay visible.

| Phase | Performed by | Start date (planned) | End date (planned) | Main deliverables | Related milestone ID |
| --- | --- | --- | --- | --- | --- |
| <!-- e.g. Requirements definition --> | <!-- Sun* / joint / client --> | <!-- YYYY-MM-DD --> | <!-- YYYY-MM-DD --> | <!-- e.g. function-list.md --> | <!-- M-01 --> |

<!-- Case B (function list not yet settled): only the requirements rows get dates; every later phase is
     `TBD (after the function list is settled)`. Re-run SCH once it is settled. -->

## 2. Milestones

| M-ID | Milestone | Planned date | Completion condition | Related phase |
| --- | --- | --- | --- | --- |
| M-01 | <!-- e.g. requirements sign-off --> | <!-- YYYY-MM-DD --> | <!-- what must be true for this to be met --> | <!-- Requirements definition --> |

## 3. WBS (Epic / Story)

> **Epic = function group, Story = function.** Never split an Epic by phase, and never add Task rows.
> Story IDs inherit their parent Epic (`E-01` → `E-01-S01`).

| WBS ID | Type | Name | Related F-ID | Start date (planned) | End date (planned) | Related milestone ID | Dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <!-- E-01 --> | <!-- Epic --> | <!-- e.g. account management (= FG-01) --> | | <!-- YYYY-MM-DD --> | <!-- YYYY-MM-DD --> | <!-- M-01 --> | |
| <!-- E-01-S01 --> | <!-- Story --> | <!-- e.g. sign in --> | <!-- F-001 --> | <!-- YYYY-MM-DD --> | <!-- YYYY-MM-DD --> | <!-- M-01 --> | <!-- e.g. E-01-S02 --> |

**Cross-cutting notes**: <!-- phase work that is not an Epic — IT/ST/UAT, documentation, migration,
release, operations — is carried as §1 phase rows and noted here. -->

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-plan-schedule skill --> | <!-- created --> |
```
