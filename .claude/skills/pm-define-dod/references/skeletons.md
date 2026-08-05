# Skeleton for the File This Skill Owns

`Write` this when `define-dod.md` **does not exist or is empty**, then fill it in through the interview.
Never use it to overwrite a file that already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

Note that **§3 is a fixed definition**: it ships filled in on purpose, because this skill is the side that
*executes* that flow rather than authoring it. Everything else starts as placeholders, and §4 stays blank
until closing-judgement mode runs.

---

## `project/01_management/define-dod.md`

```markdown
# Definition of Done

> The criteria that decide whether this project can be closed, and the record of the closing judgement.
> §1 is filled in during initial setup; §4 only at closing.

## 1. Completion Criteria

| D-ID | Category | Criterion | Judgement method / evidence | Status | Handling | Reason | Approver | Approval date | Related ID | Update date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D-001 | <!-- one of the §2 categories --> | <!-- what must be true --> | <!-- how it is verified, and with what evidence --> | <!-- not judged --> | | | | | <!-- F-xxx / NFR-xxx --> | <!-- YYYY-MM-DD --> |

## 2. Category Guidelines

| Category | What it covers | In scope? |
| --- | --- | --- |
| Functional requirements | Whether the functions in `function-list.md` are complete and accepted | <!-- yes / out of scope + reason --> |
| Non-functional requirements (quality & performance) | Whether the `non-function-list.md` targets are met | <!-- yes / out of scope + reason --> |
| Documents & deliverables | Whether the contracted deliverables have been handed over | <!-- yes / out of scope + reason --> |
| Testing & acceptance | Test completion and the client's acceptance | <!-- yes / out of scope + reason --> |
| Operational transition & handover | Handover to operations, manuals, training | <!-- yes / out of scope + reason --> |
| Contract & billing | Acceptance certificate, invoicing, contract closing | <!-- yes / out of scope + reason --> |

## 3. Status Definitions & the Flow for Unmet Criteria

> **Fixed definitions — never rewrite this section.** This skill applies them; changing them is out of scope.

**Statuses**: `not judged` / `met` / `partially met` / `not met`.

**Flow for unmet and partially met criteria**:

1. Propose the handling — **address and meet it** / **waive it (out of scope)** / **defer it to the next phase** — with the reason, as a draft needing confirmation.
2. Take it through the approver for that subject in `stakeholders.md` §3 and record the review and approval status.
3. Finalize status / handling / reason / approver / approval date / update date **only for approved rows**. Unapproved rows stay on hold as "awaiting approval".
4. When an important decision arises, prompt the user to record it in `decision.md` (never edit that file from here).

## 4. Overall Closing Judgement

| Item | Content |
| --- | --- |
| Overall achievement rate | <!-- met ÷ total; filled in at closing --> |
| Waived items | <!-- count --> |
| Deferred items | <!-- count --> |
| Final approver | |
| Approval date | |
| Overall comment | |

## 5. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-define-dod skill --> | <!-- created --> |
```
