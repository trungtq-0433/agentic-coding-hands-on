# Test WBS Breakdown and Date Calculation Guide

The criteria the `pm-plan-test` skill uses when assembling `test-schedule.md` §3 (test WBS) and §2 (test milestones), and `test-plan.md` §2.1 (test types performed).

This project assumes **iterative development per Epic**, so testing likewise repeats "write manual test cases → execute manual tests → fix bugs" each time an Epic's implementation completes. Do not turn it into a single test phase spanning the whole project.

## 1. `schedule.md` §3 Epic → Test WBS (`E-xx-Tnn`)

### 1.1 IT (integration testing): generate 3 rows per Epic

For each Epic in `schedule.md` §3 (`E-01`, `E-02`, …) that is a **development Epic whose deliverables are subject to behavioral verification** (development/implementation, anything involving new functionality), generate the following 3 rows:

| Test WBS ID | Test level | Name | Related Epic/Story ID |
| --- | --- | --- | --- |
| `E-xx-T01` | IT | Write manual test cases | `E-xx` |
| `E-xx-T02` | IT | Execute manual tests | `E-xx` |
| `E-xx-T03` | IT | Fix bugs | `E-xx` |

- `xx` inherits the parent Epic ID verbatim (never renumber on the test side).
- Purely planning or documentation Epics (requirements definition, design-only, operation & maintenance, incident response, etc.) and Epics performed solely by the client may be excluded from IT. When in doubt, confirm with the user.
- Whether to break the test WBS down to the Story level depends on the number and granularity of the stories under the Epic (the default is 3 rows per Epic; split per story only when the verification timing differs substantially between stories).

### 1.2 ST/UAT: treat as project-wide milestones

System testing (ST) and acceptance testing (UAT) are not repeated per Epic; they run once (or a few times) across the whole project after integration testing is complete for all Epics. If you do add test WBS rows for them, set the Related Epic/Story ID to "all Epics" or state the covered scope explicitly, and keep them consistent with the §2 test milestones (ST start, UAT start).

## 2. How to Derive the Planned Dates

Derive the planned start and end dates of each test WBS row from the corresponding Epic's "planned end date" in `schedule.md` §3:

1. The start date of `E-xx-T01` (write manual test cases) ≈ the planned end date of the parent Epic `E-xx` (case writing can begin once the design and implementation have firmed up).
2. `E-xx-T02` (execute manual tests) starts after `E-xx-T01` completes. It depends on `E-xx`'s implementation being complete (= the Epic end date).
3. `E-xx-T03` (fix bugs) runs during and after `E-xx-T02`. Allow buffer for bugs to converge.
4. Estimate each row's duration from the number of target functions, the weight of the non-functional requirements, and the assignees' capacity. No strict capacity calculation is needed — a simple "1 week = 5 business days" estimate is fine. If a figure cannot be settled, leave it blank and report it as an open item in the completion summary (never place provisional values).
5. Back-calculate the ST/UAT dates from the milestones in `schedule.md` §2 (production release, etc.) and finalize them after confirming with the user.

## 3. `non-function-list.md` Category → Test Type (`test-plan.md` §2.1)

Generate the test types performed at each test level from the category column of `non-function-list.md`:

| non-function-list.md category | Test level | Test type performed (example) |
| --- | --- | --- |
| Performance (response, throughput) | ST | Performance testing (confirming targets are met) |
| Availability & reliability | ST | Fault tolerance testing / scenario testing |
| Security | ST | Security testing (authentication & authorization, vulnerability assessment) |
| Compatibility (browser, OS, device) | ST / UAT | Cross-browser and device testing (linked to §3.1) |
| Extensibility, operability & maintainability | ST | Operational scenario testing |
| (Functional requirements in general) | IT | Connectivity testing / business flow testing (happy and alternate paths) |
| (Client business requirements) | UAT | Business scenario testing |

- The categories vary by project, so generate rows only for the categories that actually exist.
- When a matching verification method is stated in the "Verification method" column of `non-function-list.md`, copy that in preference.

## 4. Criteria for Generating Test Milestones (`M-Txx`)

Generate the §2 test milestones of `test-schedule.md` in correspondence with the milestones in `schedule.md` §2. The default sequence:

| ID | Milestone name (example) | Corresponding schedule.md M-xx |
| --- | --- | --- |
| `M-T01` | Test environment ready | The milestone between development start and integration testing start |
| `M-T02` | System testing (ST) start | The M-xx matching the ST start (after integration testing is complete for all Epics) |
| `M-T03` | Acceptance testing (UAT) start | The M-xx matching the UAT start (depends on the client's schedule) |
| `M-T04` | Bug convergence judgement | The M-xx matching the production release decision |

- Record the corresponding `schedule.md` M-xx or Epic ID in the "Related WBS ID" column.
- If the engagement's characteristics call for more or fewer milestones, adjust the `M-Txx` entries accordingly. Finalize the planned dates after confirming with the user, and leave unsettled ones blank.
