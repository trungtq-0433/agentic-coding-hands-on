# Skeleton for the File This Skill Owns

`Write` this when `feedback-list.md` **does not exist or is empty**. Never use it to overwrite a file that
already has content — see the layout rule
[`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

§2 and §3 are **fixed definitions**: they ship filled in on purpose, because this skill is the side that
*applies* them. Never rewrite them, and never add columns or sections. The `FB-001` placeholder row is not
real data — the first real registration may replace it.

---

## `project/07_feedbacks/feedback-list.md`

```markdown
# Feedback List

> Day-to-day feedback, observations and improvement requests from reviews, UAT and regular meetings.
> Each entry is tracked **provisionally here until a decision on whether to act is made**; whatever is
> decided to be acted on is handed over downstream and its ID recorded in "Related ID".
> This list is neither a bug tracker (→ `problem-list.md`) nor a record of decisions (→ `decision.md`).

## 1. Feedback

| FB-ID | Date received | Source | Origin | Category | Feedback content | Handling | Owner | Status | Related ID | Update date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FB-001 | <!-- YYYY-MM-DD --> | <!-- e.g. Client / Sun* (internal) --> | <!-- Review / UAT / Regular meeting --> | <!-- one of the 5 categories --> | <!-- what was said --> | <!-- decided handling; blank before a decision --> | | <!-- Open --> | <!-- CR-xxx / P-xxx / T-xxx / Issue URL --> | <!-- YYYY-MM-DD --> |

## 2. Category Guidelines

> **Fixed definitions — never rewrite this section.** Always choose exactly one.

| Category | What it covers |
| --- | --- |
| `UI/UX` | Screen presentation and usability |
| `Function` | How usable or complete the functionality is (excluding defects) |
| `Documentation` | The content of manuals, specifications and the like |
| `Performance` | Response time and processing performance |
| `Other` | Anything that fits none of the above |

## 3. Handling Flow

> **Fixed definitions — never rewrite this section.** This skill never raises anything itself: it guides
> the user to the owning skill and copies the resulting ID back into "Related ID".

| Nature of the content | Handover target | Related ID |
| --- | --- | --- |
| A change affecting scope, schedule or budget | `change-request.md` (CR) | `CR-xxx` |
| A bug or defect | `problem-list.md` (`pm-track-risks-issues` / RISK) | `P-xxx` |
| An improvement or request needing implementation | `pm-create-tasks` (TASK) → GitHub Issue | `T-xxx` or the Issue URL |
| A minor improvement, or something to consider later | Tracked here; no handover | blank |

**Statuses**: `Open` (just registered) → `Under consideration` → act / `Will not act` (terminal);
acting moves it to `In progress` → `Done` (terminal).

## 4. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-collect-feedback skill --> | <!-- created --> |
```
