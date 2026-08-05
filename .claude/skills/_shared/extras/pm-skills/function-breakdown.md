# Function Breakdown Rules (Domain / Function Group / Function)

Criteria for breaking down and organizing functions in `function-list.md` and `functions/`. **By-feature** is the standard axis, and functions are captured in **three levels**. The skills that maintain the function list (`pm-gather-requirements`, `pm-plan-schedule`) must follow these rules, as must the future `requirement-analysist` (RA) / `business-analyst` agents when they ship.


## 1. The Three Levels

| Level | Definition | Split axis | ID | Managed in |
|---|---|---|---|---|
| **Domain** | A broad grouping of a business area. Introduce **only when the system is complex** | Business domain | `D-01` | function-list.md (heading or column) |
| **Function Group** | One large cluster of functionality (a set of related functions) | Functional cluster | `FG-01` | function-list.md (heading or column) |
| **Function** | An individual function under a function group | A single unit of user value | `F-001` (follow existing numbering) | function-list.md row + details in `functions/` |

- **Domain**: introduce when the system is large and function groups alone are not enough to get an overview. **Omit it for simple systems** and use the two levels `Function Group → Function`.
- **Function Group**: a "large cluster of functionality" as seen by the user (e.g. Account, Attendance, Payroll). Never split by development phase.
- **Function**: corresponds to one row in `function-list.md`. One function = one unit of user value. Details are expanded into `functions/function-{No}-{function-name}.md`.

## 2. Breakdown Principles

- **Top-down**: (Domain →) Function Group → Function. If a higher level is undefined, define it first (a function must never invent its own parent group).
- **Use only the levels you need**: Domain is for complex systems only. Do not force three levels.
- **Linkage is mandatory**: every function must point to a parent function group, and every function group to a parent domain. Never create orphans (functions without a parent).
- **MECE**: the set of children = the parent (no gaps, no overlaps). All functions of one function group = that function group.
- **ID convention**: once assigned, an ID never changes. When a function is deleted, keep its number as a gap and never reuse it (follow the existing numbering such as `F-001`).

## 3. Reflecting This in function-list.md

- Express the three levels in `function-list.md` either by **adding "Domain" and "Function Group" columns**, or by **grouping rows under function-group headings**.
- If the existing `function-list.md` is a flat function list with no hierarchy, **do not break existing data (F-IDs and content)**. Before changing the table structure — adding columns, introducing headings, etc. — **always confirm with the user** before restructuring.
- Once a function's detail document is created, fill in the link to the file under `functions/` in the "Detail document" column of the corresponding row in `function-list.md`.

## 4. Checklist

- [ ] Is Domain limited to "only when the system is complex" (not forced into three levels unnecessarily)?
- [ ] Are function groups split as "large clusters of functionality" (not split by phase)?
- [ ] Does every function point to its parent function group (and every function group to its domain)?
- [ ] Is each level MECE, with no orphans?
- [ ] Do IDs follow the existing numbering, with deleted entries left as gaps?
