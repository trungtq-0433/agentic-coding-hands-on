# WBS / Task Breakdown Rules (Epic / Story / Task)

Criteria for splitting the WBS in `SCH` (schedule.md), `STORY` (stories/) and `TASK` (task-list.md + Issues). **By-feature** is the standard axis.


## 1. The Three Levels

| Level | Definition | Split axis | ID | Managed in |
|---|---|---|---|---|
| **Epic** | A large cluster of functionality — one big story | Functional domain | `E-01` | schedule.md |
| **Story** | One requirement from the user's point of view (user story) | A unit of value tied to one function | `E-01-S01` (inherits the parent Epic) | schedule.md + stories/ |
| **Task** | Concrete work for a designer / dev / tester | Phase × role × technical element | `T-001` + Issue | task-list.md |

- **Epic**: bundles several related functions (F-IDs). Never split by phase.
- **Story**: can be written as "As a …, I want to …". **One function may have multiple stories** (initial implementation / improvement or fix / change-request driven). Must satisfy INVEST and fit within one sprint. Must always have acceptance criteria.
- **Task**: completed by one assignee in 1–3 days; 1 task = 1 issue = in principle 1 assignee. Break down by phase × technical element following `pm-create-tasks/references/task-breakdown.md` §2, and always cut tasks **as children of a Story**.

## 2. Breakdown Principles

- **Top-down**: Epic → Story → Task. If a higher level is undefined, create it first (a child must never invent its own parent).
- **Linkage is mandatory**: a Story must point to its parent Epic, and a Task to its parent Story (the `Related WBS ID` column). Never create orphans.
- **MECE**: the set of children = the parent (no gaps, no overlaps). All tasks of one Story done = Story done.
- **Files you do not own are read-only** (never overwrite deliverables produced by other skills).

## 3. Change Requests (CR)

Never turn a CR straight into a Story. The flow is: register in `change-request.md` → impact analysis and client approval → record in `decision.md` → add a new Story (and an Epic if needed) to `schedule.md` → STORY/TASK. Clearly note that the item originated from a CR. Never start work before approval.

## 4. Checklist

- [ ] Are Epics split by functional domain (not by phase)?
- [ ] Can each Story be written as a user story, satisfy INVEST, fit within one sprint, and have acceptance criteria?
- [ ] Is each Task 1–3 days / 1 issue / 1 assignee, and does it point to its parent Story?
- [ ] Is each level MECE, with no orphans?
- [ ] Has every CR gone through the §3 flow?
