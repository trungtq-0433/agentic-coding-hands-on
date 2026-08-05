# Skeletons for the Files This Skill Owns

`Write` these when the target file **does not exist or is empty**. Never use them to overwrite a file that
already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

Two different uses:

- **`progress.md`** — created once, then updated in place on every run.
- **The weekly report** — the skill writes a **new dated file** each period,
  `reports/{currentDate}-weekly-report.md`, from the report skeleton below. There is no template file to
  copy from and none is needed; if a `reports/yyyy-mm-dd-weekly-report.md` template happens to exist in the
  consumer's repository, prefer copying that and leave it unmodified.

---

## `project/01_management/progress.md`

```markdown
# Progress

> Actual progress against the plan. **The planned dates live in `schedule.md`** and are never duplicated
> here — "variance against plan" records the conclusion only (`On track` / `N days behind` / `N days
> ahead`). Every ID must match `schedule.md`.
> A progress percentage with no backing from actuals stays **blank**; never fill one in by guesswork.

## 1. Overall Progress Summary

| Item | Content |
| --- | --- |
| Overall status | <!-- On track / Caution / Delayed --> |
| Variance against plan | <!-- the most impactful variance, in one line --> |
| Comment | <!-- cause and plan for addressing it; bad news first --> |
| Update date | <!-- YYYY-MM-DD --> |

## 2. Milestone Progress

| M-ID | Milestone | Status | Actual date | Variance against plan | Update date |
| --- | --- | --- | --- | --- | --- |
| <!-- M-01, from schedule.md §2 --> | <!-- milestone name --> | <!-- Not started / In progress / Done / Delayed --> | <!-- only when complete --> | <!-- On track / N days behind --> | <!-- YYYY-MM-DD --> |

## 3. WBS Progress

| WBS ID | Name | Status | Progress % | Actual date | Variance against plan | Blockers & related issue IDs | Comment | Update date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <!-- E-01-S01, from schedule.md §3 --> | <!-- story name --> | <!-- Not started / In progress / Done / Delayed --> | <!-- blank unless backed by actuals --> | | <!-- On track / N days behind --> | <!-- P-xxx --> | | <!-- YYYY-MM-DD --> |

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-report-project skill --> | <!-- created --> |
```

---

## `project/01_management/reports/{YYYY-MM-DD}-weekly-report.md`

Client-facing. **Summarize** — never paste internal notes or the EM's raw data verbatim. Bad news first,
with numbers, owners and next actions.

```markdown
# Weekly Report ({period})

## 1. Report Information

| Item | Content |
| --- | --- |
| Reporting period | <!-- YYYY-MM-DD – YYYY-MM-DD --> |
| Author | |
| Creation date | <!-- YYYY-MM-DD --> |

## 2. This Week's Summary

<!-- About 3 lines from progress.md §1: overall status and variance against plan. Bad news first. -->

## 3. Progress Status

| ID | Content | Status | Progress % | Comment |
| --- | --- | --- | --- | --- |
| <!-- M-01 / E-01-S01 --> | | | | |

## 4. This Week's Results

<!-- Tasks that became Done this week, and the deliverables produced. -->

## 5. Next Week's Plan

<!-- Tasks and milestones due to start next week. -->

## 6. Issues & Risks

> **New and updated entries only** — do not paste the whole tracker.

| ID | Content | Status | Plan |
| --- | --- | --- | --- |
| <!-- P-001 / R-001 --> | | | |

## 7. Decisions & Items for Confirmation

<!-- New decisions (DEC-xxx from decision.md), plus what we are asking the client to confirm or approve. -->

## 8. Other Shared Information

<!-- Anything worth sharing that does not fit above. -->
```
