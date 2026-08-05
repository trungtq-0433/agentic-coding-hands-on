# Interview Details (Items That Cannot Be Derived From the Documents)

The interview the `pm-plan-test` skill uses to fill in items that cannot be derived from the existing documents (`schedule.md`, `function-list.md`, `non-function-list.md`, `overview.md`, `stakeholders.md`, `define-dod.md`). Refer to this file and drive the conversation one question per turn within a block.

## Common Rules

- Present options **as keywords**, not as numbered choices. Accept free-text answers.
- For items inferred from the documents, confirm in the form "I understood this as X — is that right?" (do not use an open question).
- Items requiring a date, a severity response target or a number are never finalized without an explicit answer from the user. Leave unsettled items blank and report them as open items in the completion summary.

## Block T-A: Scope and Target Systems (→ test-plan §1 / §1.2)

**Example prompt (when `architecture.md` does not exist, or the in-scope/out-of-scope split cannot be read)**:
> Are there systems or functions to exclude from testing? (e.g. the external payment service is covered by the partner vendor's testing, integrations with other systems are out of scope, etc.)

**Answer interpretation rules**:
- As a rule, every function listed in `function-list.md` is in scope. Only explicitly stated items are out of scope.
- Record external services as out of scope together with the reason ("already tested by the vendor", etc.).

## Block T-B: Test Environments (→ test-plan §3)

**Example prompt**:
> Please tell me about the test environments. I'd like to confirm the URLs of the development (dev) and staging environments, how test data is prepared (masked production-equivalent data / generated dummy data, etc.), and which test level each environment is used for.

**Answer interpretation rules**:
- If there is only one environment, record that and note how it is shared across levels in the notes column.
- If the data preparation method is undecided, leave it blank and record "the test data preparation method is to be settled separately" in the assumptions (§1 `AT-xxx`).

## Block T-C: Entry and Exit Criteria (→ test-plan §5)

**Example prompt (when concrete criteria cannot be read from "testing & acceptance" in `define-dod.md`)**:
> Let me confirm the entry and exit conditions for each test level. For example, is "100% pass rate on the manual test cases" acceptable as the exit condition for integration testing, and "zero Critical/High defects" for system testing?

**Answer interpretation rules**:
- The exit criteria must not contradict the "testing & acceptance" category in `define-dod.md` (reference only — never edit the DoD side).
- If they do contradict, present both and have the user decide.

## Block T-D: Defect Severity and Response Targets (→ test-plan §6)

**Example prompt**:
> Are there response targets per defect severity (Critical / High / Medium / Low) — e.g. Critical is picked up the same day, High by the next business day? I can provide a starting draft of the definitions.

**Starting draft of the severity definitions (the AI may propose these; the response deadlines must be confirmed with the user)**:

| Severity | Definition (example) |
| --- | --- |
| Critical | Business cannot continue; involves data loss |
| High | A core function is unusable |
| Medium | Affects part of a function, but a workaround exists |
| Low | Minor impact on business, e.g. layout glitches |

**Answer interpretation rules**:
- The definitions above may be adopted as-is, but **the response targets (deadlines) are recorded only after confirming with the user**.
- If the response targets are not settled, leave them blank.

## Block T-E: Test Milestone Dates (→ test-schedule §2)

**Example prompt**:
> Let me confirm the planned dates for the main test checkpoints (test environment ready, system testing start, acceptance testing start, bug convergence judgement). I can offer estimates back-calculated from the milestones in `schedule.md`, but I'd like you to confirm them.

**Answer interpretation rules**:
- The UAT start date often depends on the client's schedule. Distinguish between fixed dates and dates pending calculation; the latter may be left blank for now.
- Present estimates back-calculated from the production release date and similar in `schedule.md` §2, but never finalize them without permission.
