# Skeletons for the Files This Skill Owns

`Write` these when the target file **does not exist or is empty**. Never use them to overwrite a file that
already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

§2 and §3 of both files are **fixed definitions**: they ship filled in on purpose, because this skill is the
side that *applies* them. Never rewrite them afterwards. The `R-001` / `P-001` placeholder rows are not real
data — the first real registration may replace them.

---

## `project/01_management/risks-problems/risk-list.md`

```markdown
# Risk List

> Risks are uncertainties that **have not happened yet but could**. Once one materializes it is registered
> as an issue in `problem-list.md` and the two are cross-linked — the risk row is never deleted.

## 1. Risks

| R-ID | Category | Risk content | Probability | Impact | Risk level | Response strategy | Countermeasure | Owner | Status | Related issue ID | Discovered on | Update date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | <!-- one of the 6 categories --> | <!-- what could happen, and the consequence --> | <!-- high / medium / low --> | <!-- high / medium / low --> | <!-- from the §2 matrix --> | <!-- avoid / mitigate / transfer / accept --> | <!-- what we will do --> | | <!-- Monitoring --> | <!-- P-xxx, once it materializes --> | <!-- YYYY-MM-DD --> | <!-- YYYY-MM-DD --> |

## 2. Judgement Criteria

> **Fixed definitions — never rewrite this section.**

**Categories (6)**: `Technical` / `Schedule` / `Budget & contract` / `Quality` / `Team & staffing` / `Customer relations`

**Risk level matrix** (probability × impact):

| | Impact: high | Impact: medium | Impact: low |
| --- | --- | --- | --- |
| **Probability: high** | High | High | Medium |
| **Probability: medium** | High | Medium | Low |
| **Probability: low** | Medium | Low | Low |

**Response strategies**: `avoid` (remove the cause) / `mitigate` (reduce probability or impact) / `transfer` (move it to another party) / `accept` (monitor and prepare a contingency).

## 3. Status Definitions

> **Fixed definitions — never rewrite this section.**

| Status | Meaning |
| --- | --- |
| Monitoring | Registered and being watched (the initial status) |
| Occurred (became an issue) | It materialized; a `P-xxx` was registered and cross-linked |
| Resolved | The countermeasure removed it |
| No action needed | Circumstances changed, or the impact turned out to be negligible |

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-track-risks-issues skill --> | <!-- created --> |
```

---

## `project/01_management/risks-problems/problem-list.md`

```markdown
# Issue List

> Issues are problems, failures and blockers that **have already occurred**. Defects found in testing are
> registered here too (`pm-plan-test` §6 points at this file).

## 1. Issues

| P-ID | Category | Issue content | Priority | Response plan | Owner | Deadline | Status | Originating risk ID | Discovered on | Update date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P-001 | <!-- one of the 6 categories --> | <!-- what happened, and its impact --> | <!-- high / medium / low --> | <!-- what we will do --> | | <!-- YYYY-MM-DD --> | <!-- Open --> | <!-- R-xxx, if it came from a risk --> | <!-- YYYY-MM-DD --> | <!-- YYYY-MM-DD --> |

## 2. Priority Guidelines

> **Fixed definitions — never rewrite this section.**

**Categories (6)**: the same 6 as `risk-list.md` §2.

| Priority | Guideline |
| --- | --- |
| High | Blocks the business or the project; no workaround; affects a milestone |
| Medium | There is a workaround, but it must be resolved within the phase |
| Low | Limited impact; may be handled when there is room |

## 3. Status Definitions

> **Fixed definitions — never rewrite this section.**

| Status | Meaning |
| --- | --- |
| Open | Registered; handling not started (the initial status) |
| In progress | Being handled |
| On hold | Deliberately deferred (state the reason in the response plan) |
| Resolved | Handling complete and confirmed |

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-track-risks-issues skill --> | <!-- created --> |
```
