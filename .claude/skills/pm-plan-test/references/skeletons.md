# Skeletons for the Files This Skill Owns

`Write` these when the target file **does not exist or is empty**, then fill them in through the interview.
Never use them to overwrite a file that already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

The skeleton for `project/05_test/qa.md` lives in `SKILL.md` under "Recording open items", not here.

---

## `project/05_test/test-plan.md`

```markdown
# Test Plan

> How this project will be tested. The exit criteria in §5 must stay consistent with the
> "testing & acceptance" category of `project/01_management/define-dod.md` (reference only).

## 1. Purpose & Scope

<!-- Why we test: verifying the functional and non-functional requirements, and providing material for
     the release decision. -->

### 1.1 In Scope

<!-- Default: every entry in function-list.md. State any exclusions explicitly. -->

### 1.2 Target & Out-of-Scope Systems

| System | In scope? | Notes |
| --- | --- | --- |
| <!-- e.g. the web application --> | <!-- yes / no --> | |

## 2. Test Levels & Approach

| Level | Purpose | Performed by (AI / human) | Performed by (org) | Notes |
| --- | --- | --- | --- | --- |
| UT | Unit behaviour | <!-- default: AI --> | <!-- Sun* --> | |
| IT | Integration & business flow | <!-- default: AI + human --> | <!-- Sun* --> | |
| ST | System-wide, incl. non-functional | <!-- default: human --> | <!-- Sun* --> | |
| UAT | Acceptance against business needs | <!-- default: human --> | <!-- client-led --> | |

### 2.1 Test Types Performed

> Generated from the categories present in `non-function-list.md` — only the categories that actually
> exist (mapping table in `references/test-breakdown.md` §3).

| Test type | Level | Target | Verification method |
| --- | --- | --- | --- |
| <!-- e.g. performance testing --> | <!-- ST --> | <!-- NFR-001 --> | <!-- from non-function-list "how it is verified" --> |

## 3. Test Environments

| Environment | Purpose | URL / location | Data preparation | Owner |
| --- | --- | --- | --- | --- |
| <!-- e.g. staging --> | <!-- IT / ST --> | <!-- TBD --> | <!-- e.g. masked copy of production --> | |

### 3.1 Compatibility Targets

> Copied from the "compatibility" entry of `non-function-list.md`, which is authoritative for the values.

| Browser / OS / device | Version | Responsive testing required? |
| --- | --- | --- |
| <!-- e.g. Chrome (Windows) --> | <!-- latest --> | <!-- yes / no --> |

## 4. Organization & Roles

| Level | Performed? | Performed by | Approver | Notes |
| --- | --- | --- | --- | --- |
| UT | <!-- yes / not required + reason --> | <!-- from overview.md §4 --> | <!-- from stakeholders.md §2 --> | |
| IT | | | | |
| ST | | | | |
| UAT | | | | |

## 5. Entry & Exit Criteria

| Level | Entry criteria | Exit criteria |
| --- | --- | --- |
| IT | <!-- e.g. implementation and UT complete for the target Epic --> | <!-- e.g. all planned cases executed, no open Critical/High --> |
| ST | | |
| UAT | | |

## 6. Defect Management

| Severity | Definition | Response target |
| --- | --- | --- |
| Critical | <!-- e.g. the business cannot proceed; no workaround --> | <!-- confirm with the user; never place a provisional value --> |
| High | <!-- e.g. a main function is unusable; a workaround exists --> | |
| Medium | <!-- e.g. a sub-function is affected --> | |
| Low | <!-- e.g. cosmetic --> | |

Defects found in testing are registered in
`project/01_management/risks-problems/problem-list.md` (owned by `pm-track-risks-issues`/RISK).

## 7. Assumptions & Risks

<!-- Test-specific assumptions and their impact if broken. -->

## 8. Related Documents

<!-- schedule.md / function-list.md / non-function-list.md / define-dod.md / test-schedule.md -->

## 9. Open Items

<!-- Items awaiting customer confirmation are tracked in project/05_test/qa.md. -->

## 10. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-plan-test skill --> | <!-- created --> |
```

---

## `project/05_test/test-schedule.md`

```markdown
# Test Schedule

> Test milestones and the per-Epic test WBS. Epic IDs are inherited verbatim from
> `project/01_management/schedule.md` §3 — never renumber them on the test side.

## 1. Assumptions

| AT-ID | Assumption | Impact if it does not hold |
| --- | --- | --- |
| AT-001 | <!-- e.g. implementation and UT are complete for each Epic before IT starts --> | <!-- e.g. IT start slips by the same amount --> |

## 2. Test Milestones

| M-T ID | Milestone | Planned date | Related WBS ID | Completion condition |
| --- | --- | --- | --- | --- |
| M-T01 | <!-- e.g. test environment ready --> | <!-- YYYY-MM-DD, confirmed with the user --> | <!-- schedule.md M-xx --> | |

## 3. Test WBS

> Three IT rows per development Epic: write cases → execute → fix bugs. ST/UAT are project-wide
> (see `references/test-breakdown.md` §1.2), not per-Epic.

| Test WBS ID | Test level | Name | Related Epic/Story ID | Start date (planned) | End date (planned) | Assignee |
| --- | --- | --- | --- | --- | --- | --- |
| <!-- E-01-T01 --> | <!-- IT --> | <!-- Write manual test cases --> | <!-- E-01 --> | <!-- YYYY-MM-DD --> | <!-- YYYY-MM-DD --> | |
| <!-- E-01-T02 --> | <!-- IT --> | <!-- Execute manual tests --> | <!-- E-01 --> | | | |
| <!-- E-01-T03 --> | <!-- IT --> | <!-- Fix bugs --> | <!-- E-01 --> | | | |

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-plan-test skill --> | <!-- created --> |
```
