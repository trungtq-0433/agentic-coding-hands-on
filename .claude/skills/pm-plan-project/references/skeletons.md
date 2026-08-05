# Skeletons for the Files This Skill Owns

`Write` these when the target file **does not exist or is empty**, then fill them in through the interview.
Never use them to overwrite a file that already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

Keep the `<!-- e.g. ... -->` markers on placeholder rows: the other skills use "every cell is an HTML
comment" as the signal for "still a template, not started".

---

## `project/01_management/overview.md`

```markdown
# Project Overview

> The management view of the project: contract, organization, way of working and constraints.
> The service/product view (background, problems, objectives) lives in
> `project/02_requirements/system-overview.md` and is owned by `pm-gather-requirements` (REQ).

## 1. Basic Information

| Item | Value |
| --- | --- |
| Project name | <!-- e.g. Store Operations Management System --> |
| Project code | <!-- e.g. store-ops (internal slug) --> |
| Client name | <!-- e.g. Example Corp. --> |
| Contract type | <!-- fixed-price / quasi-delegation (lab, SES) --> |
| Contract period | <!-- e.g. 2026-04-01 – 2026-09-30 --> |
| Project type | <!-- e.g. new build / renewal / additional development --> |

## 2. KPI & Success Criteria

| KPI | Target | How it is measured | Measured by |
| --- | --- | --- | --- |
| <!-- e.g. order processing time --> | <!-- e.g. 30% reduction --> | <!-- e.g. average of the operation log --> | <!-- e.g. client --> |

**Success criteria**: <!-- what state counts as this project having succeeded, in prose -->

## 3. Way of Working

| Item | Value |
| --- | --- |
| Development method | <!-- e.g. Scrum, 2-week sprints / waterfall --> |
| Sprint length | <!-- e.g. 2 weeks (blank if not agile) --> |
| Communication channels | <!-- e.g. Slack (day to day) + weekly regular meeting --> |
| Ticket management tool | <!-- e.g. GitHub Issues (owner/repo) --> |
| Language of deliverables | <!-- e.g. Japanese --> |

## 4. Scope & Role Split

| Work item | Performed by | Notes |
| --- | --- | --- |
| Requirements definition | <!-- Sun* / client / joint --> | |
| Basic design | <!-- Sun* / client / joint --> | |
| Development & implementation | <!-- Sun* / client / joint --> | |
| UT / IT | <!-- Sun* / client / joint --> | |
| ST | <!-- Sun* / client / joint --> | |
| UAT | <!-- Sun* / client / joint --> | <!-- often client-led --> |
| Production infrastructure setup | <!-- Sun* / client / joint --> | <!-- often the client's responsibility --> |
| Data migration | <!-- Sun* / client / joint --> | <!-- often the client's responsibility --> |
| Operation & maintenance | <!-- Sun* / client / joint --> | |

> Express what Sun\* does **not** handle in the "Performed by" column. Do not add a separate
> "out of scope" subheading.

## 5. Constraints

| Category | Constraint |
| --- | --- |
| Technical | <!-- e.g. must run on the client's existing AWS account --> |
| Budget & resources | <!-- e.g. cap of N person-months --> |
| Schedule | <!-- e.g. release fixed to the start of the fiscal year --> |
| Other | |

## 6. Requirements to Uphold (D/C/Q/S)

| Category | Memo |
| --- | --- |
| Delivery (D) | <!-- what matters about the deadline --> |
| Cost (C) | <!-- what matters about cost --> |
| Quality (Q) | <!-- what matters about quality --> |
| Scope (S) | <!-- what matters about scope --> |

**Trade-off allocation (14 pts total)**: D = _ / C = _ / Q = _ / S = _
<!-- Always decided by the user. Never finalize an allocation without permission. -->

## 7. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-plan-project skill --> | <!-- created --> |
```

---

## `project/01_management/stakeholders.md`

```markdown
# Stakeholders

> Organization, approval flow and escalation. The `Assigned effort (capacity)` column in §2 is the input
> `pm-plan-schedule` (SCH) uses for date calculation.

## 1. Client Organization

| Role | Name | Affiliation | Contact | Authority |
| --- | --- | --- | --- | --- |
| <!-- e.g. project owner --> | | | | <!-- e.g. final approval of scope changes --> |

## 2. Sun\* Organization

| Role | Name | Affiliation | Contact | Authority | Assigned effort (capacity) |
| --- | --- | --- | --- | --- | --- |
| <!-- e.g. PM --> | | | | | <!-- e.g. 0.5 person-months/month (lab) or 20 person-days total (fixed-price) --> |

> The unit follows the contract type in `overview.md` §1: lab/SES = person-days per month;
> fixed-price = total assigned person-days for the project.

## 3. Decision-Making & Approval Flow

| Subject | Proposed by | Reviewed by | Approved by | Notes |
| --- | --- | --- | --- | --- |
| <!-- e.g. scope change --> | | | | |
| <!-- e.g. deliverable acceptance --> | | | | |

## 4. Escalation Flow

| Level | Trigger | Contact | Response time |
| --- | --- | --- | --- |
| 1 | <!-- e.g. a delay within the team --> | | |
| 2 | <!-- e.g. a delay affecting a milestone --> | | |
| 3 | <!-- e.g. contract-level impact --> | | |

## 5. Contact & Communication Channels

| Purpose | Channel | Frequency | Participants |
| --- | --- | --- | --- |
| <!-- e.g. day-to-day contact --> | <!-- e.g. Slack --> | <!-- e.g. as needed --> | |
| <!-- e.g. regular progress meeting --> | <!-- e.g. Google Meet --> | <!-- e.g. weekly --> | |

> The same answer feeds "communication channels" and "ticket management tool" in `overview.md` §3.
> Never interview for it twice.

## 6. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-plan-project skill --> | <!-- created --> |
```
