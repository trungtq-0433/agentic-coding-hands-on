# Skeletons for the Files This Skill Owns

`Write` these when the target file **does not exist or is empty**, then fill them in through the interview.
Never use them to overwrite a file that already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

Keep the `<!-- e.g. ... -->` markers on placeholder rows: downstream skills (`pm-plan-schedule`,
`pm-define-dod`, `pm-plan-test`, `pm-design-wireframe`) use "every cell is an HTML comment" as the signal for
"still a template, not started".

The skeleton for `qa.md` lives in `SKILL.md` under "Recording open items", not here.

---

## `project/02_requirements/system-overview.md`

```markdown
# System Overview

> The service/product view: what is being built, why, and what it is meant to achieve.
> KPIs and success criteria are **out of scope** here — they live in `project/01_management/overview.md`
> §2 and are owned by `pm-plan-project` (PLAN).

## 1. Service Overview

<!-- 3–5 lines: what the system is, who uses it, on what platform (web / mobile / both). -->

| Item | Value |
| --- | --- |
| Target platform | <!-- e.g. web (smartphone browser first) --> |
| Primary users | <!-- e.g. store staff, head office administrators --> |
| Where the data is mastered | <!-- e.g. entered in this system / referenced from an upstream system --> |

## 2. Background & Problems

| # | Current problem | Impact |
| --- | --- | --- |
| 1 | <!-- e.g. orders are managed on paper, so head office cannot see them in real time --> | <!-- e.g. a one-day lag before restocking decisions --> |

<!-- When the client cannot articulate these, propose them as a "hypothesis (needs client confirmation)"
     and log the confirmation in qa.md. Never write a hypothesis in as a settled fact. -->

## 3. Objectives & Value Delivered

| # | Objective | Value delivered | Related problem # |
| --- | --- | --- | --- |
| 1 | <!-- e.g. digitize order entry --> | <!-- e.g. head office sees orders the same day --> | 1 |

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-gather-requirements skill --> | <!-- created --> |
```

---

## `project/02_requirements/role-list.md`

```markdown
# Role List & Permission Matrix

## 1. User Roles

| ROLE-ID | Role name | Description | Typical user |
| --- | --- | --- | --- |
| ROLE-001 | <!-- e.g. general user --> | <!-- what this role does in the system --> | <!-- e.g. store staff --> |

## 2. Permission Matrix (function × role)

> One column per role in §1, one row per function in `function-list.md`.
> Legend: ✅ = allowed / — = not allowed / △ = conditional (state the condition in Notes).

| F-ID | Function | ROLE-001 | Notes |
| --- | --- | --- | --- |
| <!-- F-001 --> | <!-- function name --> | <!-- ✅ / — / △ --> | |

## 3. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-gather-requirements skill --> | <!-- created --> |
```

---

## `project/02_requirements/function-list.md`

```markdown
# Function List

> The scope of what will be built. `pm-plan-schedule` (SCH) turns the function groups into WBS Epics and the
> functions into Stories, and writes the resulting story IDs back into "Related WBS ID".
> Per-function details (use cases, I/O, business rules) belong under `functions/` and are owned by the
> downstream `requirement-analysist` — leave "Detail document" blank or `TBD` here.

## 1. Function Groups

| FG-ID | Function group | Description |
| --- | --- | --- |
| FG-01 | <!-- e.g. account management --> | <!-- what this group covers --> |

## 2. Functions

| F-ID | FG-ID | Function name | Summary | Priority | Target roles | Related WBS ID | Detail document |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | <!-- FG-01 --> | <!-- e.g. sign in --> | <!-- one line --> | <!-- must / should / could --> | <!-- ROLE-001 --> | <!-- filled in by SCH --> | <!-- TBD --> |

## 3. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-gather-requirements skill --> | <!-- created --> |
```

---

## `project/02_requirements/non-function-list.md`

```markdown
# Non-Functional Requirements

> Categories that do not apply to this project are marked **out of scope** with a reason rather than being
> filled in mechanically. Numeric targets are only written in once the user has approved them.
> Compatibility targets recorded here are authoritative for `pm-plan-test` (TEST) §3.1.

## 1. Requirements

| NFR-ID | Category | Requirement | Target value | Priority | How it is verified | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| NFR-001 | <!-- e.g. performance --> | <!-- e.g. the sign-in screen renders quickly --> | <!-- e.g. within 3 s at the 90th percentile --> | <!-- must / should --> | <!-- e.g. measured during ST --> | |

<!-- Categories to consider (see references/nfr-catalog.md): performance / availability / scalability /
     security / operability & maintainability / compatibility / internationalization / accessibility. -->

## 2. Out of Scope

| Category | Reason |
| --- | --- |
| <!-- e.g. accessibility --> | <!-- e.g. internal tool, agreed with the client as out of scope --> |

## 3. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-gather-requirements skill --> | <!-- created --> |
```

---

## `project/02_requirements/glossary.md`

```markdown
# Glossary

> Collected retroactively: note terms as they come up during the Block O–C interviews, then confirm their
> definitions together in Block D. Never open with "tell me your terminology".

## 1. Terms

| Term | Reading / abbreviation | Definition | Notes |
| --- | --- | --- | --- |
| <!-- e.g. order slip --> | <!-- e.g. hacchū-sho --> | <!-- the client's meaning, not the dictionary one --> | |

## 2. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-gather-requirements skill --> | <!-- created --> |
```
