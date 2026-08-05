# Master Schedule, WBS and Date Calculation Guide

The criteria `pm-plan-schedule` uses when assembling `schedule.md`. **By-feature** is the standard axis.

## Model Premises

- **Phase** = a row of the §1 master schedule (requirements, basic design, development, testing, etc.). Not an Epic.
- **Epic = function group (FG) / Story = function (F)** (`skills/_shared/extras/pm-skills/wbs-task-breakdown.md`, `function-breakdown.md`). The phase × role breakdown happens at the Task level (`pm-create-tasks`); this skill goes **down to the Story level only**.

## 1. Master Schedule (§1) = Generated From `overview.md` §4

Expand each work item in `overview.md` §4 "Scope & role split" into a phase row in §1. Columns: `Phase | Performed by | Start date (planned) | End date (planned) | Main deliverables | Related milestone ID`.

| §4 work item (example) | Standard phase name | Handling |
| --- | --- | --- |
| Requirements definition (detailed requirements analysis) | Requirements definition | Dates derived per performer |
| Basic design / detailed design | Basic design | Same |
| Development / implementation | Development & implementation | Same |
| Unit testing (UT) | Unit testing | In parallel with / tied to development |
| Integration testing (IT) | Integration testing | |
| System testing (ST) | System testing | |
| Acceptance testing (UAT) | Acceptance testing | Usually performed by the client |
| Documentation | Documentation | In parallel with other phases |
| Data migration / production environment setup / production release / operation & maintenance / incident response | Same names | Match the §4 of the engagement |

- **Always state the performer column (Sun* / joint / client).** Keep client-side phases in §1 as references too (to make dependencies visible).
- Do not add phases that are not in §4, and do not drop phases that are (§4 is the only source). For rows with an empty performer, interview, write it back to §4, and then expand it.
- **Case B (function list not settled)**: derive dates only for the requirements rows; set the start/end dates of all later phases to `TBD (after the function list is settled)`.

## 2. WBS (§3) = Epic/Story, By Feature

The subject is the functions in `function-list.md`. Columns: `WBS ID | Type | Name | Related F-ID | Start date (planned) | End date (planned) | Related milestone ID | Dependencies`.

**Case A (function list settled)**:

- **Function group (FG) = Epic** (`E-01`…, in the FG order of function-list). The Epic name inherits the FG name.
- **Function (F) = Story** (`E-01-S01`…, inheriting the parent Epic). As a rule **1 function = 1 story**. However, a function that does not satisfy INVEST or exceeds one sprint may be split into multiple stories **by value or scenario** (**never by CRUD operation** — that is Task territory, owned by `pm-create-tasks`). Even when split, record the original F-ID in each story's `Related F-ID`.
- Only when there are far too many function groups (rule of thumb: more than 15 Epics) may you merge related FGs into a single Epic. Briefly confirm the grouping result with the user.
- Write the generated story IDs back into the "Related WBS ID" column of `function-list.md` (never overwrite cells that are already filled in).

**Case B (function list not settled)**:

- Turn only the requirements work into a WBS. If there are rough function-group candidates, create them as provisional Epics/Stories with the note "provisional (to be revisited once settled)". Otherwise use a single Epic "Requirements definition" plus stories such as interviews and specification writing.
- Do not write back to `function-list.md`.

Do not create Task rows (owned by `pm-create-tasks`). Phase work such as IT/ST/UAT, documentation, migration, release and operations is expressed not as Epics/Stories but as **phase rows in the §1 master schedule**, and left as a cross-cutting note in the client notes of §3.

## 3. Dependency Rules

Between phases (used to derive the earliest start date for §1 and for stories):

| Phase | Default dependency |
| --- | --- |
| Requirements definition | None (starts at kickoff) |
| Basic design | Depends on requirements definition being complete |
| Development & implementation | Depends on basic design being complete for the corresponding function |
| Unit testing | Depends on implementation being complete for the corresponding function (paired per function) |
| Integration testing | Depends on UT being complete for all functions |
| System testing | Depends on integration testing being complete |
| Acceptance testing | Depends on system testing being complete + the client's schedule |
| Documentation | Can run in parallel with development and UT. Must be complete before release |
| Data migration | After the migration approach is settled in basic design. Must be complete before release |
| Production environment setup | After requirements definition is complete; can run in parallel with development. Must be complete before release |
| Production release | Depends on acceptance passing + data migration + environment setup being complete |
| Operation & maintenance | Starts on the release date, ends on the contract end date (overview §1). If undecided, leave the end date blank with a note |
| Incident response (production) | Same period as operation & maintenance |

**For agile projects (overview §3)**: do not serialize the phases strictly. Assign work to sprints per function (story), running requirements sign-off → design → development → UT in parallel within the sprint. Place IT/ST/UAT in focused sprints that consolidate the output of several sprints. Express the §1 master schedule as rough phase bands (leading requirements definition and basic design, the development sprints, and the final testing push).

## 4. Date Calculation

Once the Sun*-side effort required for each phase / story (person-days, Block B) is settled:

1. Determine the earliest possible start date from the dependencies (§3) — the predecessor's end date or the milestone date.
2. Sum the working capacity of the assignable members (`stakeholders.md` §2, in the unit that matches the contract type in overview §1):
   - **Lab / SES (person-days/month)**: required effort ÷ total assigned person-days per month × 30 ≈ duration in days
   - **Fixed-price (total assigned person-days)**: derive a per-month person-day figure by spreading the total across the project period, then calculate the same way. If the project period is undecided, produce only relative durations as ratios and adjust the absolute dates once the milestones are settled
3. Add the duration to the earliest start date to get the end date. Keep business-day adjustment simple: "1 week = 5 business days".
4. If the result overruns a fixed milestone (one whose date was settled in Block A), present it to the user and confirm which of the following applies: adding capacity, adjusting scope, or revisiting the milestone (never adjust without permission).
5. In agile, align story dates with the sprint window in which that function is built. Make the §1 phase periods consistent by having them encompass the span of their constituent stories.
