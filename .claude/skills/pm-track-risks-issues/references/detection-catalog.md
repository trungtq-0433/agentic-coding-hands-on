# Detection Catalog

The conventions for detecting **risk** and **issue (problem)** candidates from each input and assigning them a category. The skill refers to this file to enumerate candidates and **must always present them to the user as "candidates (needs confirmation)"** before registering them. Never finalize on the AI's inference alone.

## 1. Separating Risks From Issues

| | Risk (`risk-list.md`) | Issue (`problem-list.md`) |
| --- | --- | --- |
| Definition | An uncertainty that **has not happened yet but could** | A problem, failure or blocker that **has already occurred** |
| Example | "If the client's review slips, the downstream work could be pushed back" | "The M-02 review is 3 business days late and the downstream work cannot start" |
| ID | `R-xxx` | `P-xxx` |
| Initial status | `Monitoring` | `Open` |

- When in doubt, decide by asking "has it already happened?" If yes, it is an issue; if not (i.e. if you can talk about it in terms of probability), it is a risk.
- When a risk materializes, do not delete the risk — set it to `Occurred (became an issue)`, register a new issue, and cross-link them (→ §4).

## 2. Category Definitions (6, fixed)

The "Category" column of `risk-list.md` / `problem-list.md` must always be one of the following 6. Map the user's own wording (management / progress / quality / technical …) using the table below.

| Category | Covers | Mapping to user wording |
| --- | --- | --- |
| `Technical` | Technical difficulty, architecture, dependence on external APIs/libraries, performance, technical debt | "technical problem", "technical" |
| `Schedule` | Delays, lead times, missed milestones, optimistic estimates | "progress", "schedule" |
| `Budget & contract` | Cost overruns, effort overruns, contract scope, billing, the cost impact of scope | (the financial side of management) |
| `Quality` | Bugs, defects, insufficient testing, review findings, deliverable quality | "quality" |
| `Team & staffing` | Understaffing, skill mismatch, departures, capacity crunch, assignments | "management (the staffing side)" |
| `Customer relations` | Agreement with the client, slow decisions, requirement changes, communication | "management (the customer side)" |

> When the user says "a management risk", ask one question to determine whether it is about staffing or about customer relations, and assign it to `Team & staffing` or `Customer relations`.

## 3. Detection Rules by Input

Each line reads "signal → candidate type and category". These only trigger presenting a candidate; the final call is the user's.

### schedule.md (read-only)
- Lead times or assumptions marked "placeholder" or "needs confirmation" (e.g. A-xxx assumption unconfirmed, review lead time a placeholder) → **Risk / `Schedule`**
- Per-story effort allocation unsettled, or thin estimating rationale → **Risk / `Schedule`** or **`Team & staffing`**
- Milestones close together / dependencies concentrated → **Risk / `Schedule`**

### progress.md (read-only)
- A WBS item or milestone whose "variance against plan" is `N days behind`, or whose status is `Delayed` → **Issue / `Schedule`** (already occurring)
- A blocker recorded in the "Blockers & related issue IDs" column → **Issue** (judge the category from the blocker's content)
- Progress percentage stuck for a long time, or implausibly far ahead raising quality concerns → **Risk** (`Schedule` / `Quality`)

### GitHub Issues (`gh issue list` / `gh issue view`, read-only)
- Fetch with `gh issue list --state open` against the repository under `## GitHub Settings` in `jp-pm-memory.md`. If unauthenticated or unconfigured, **skip this section** and continue with the other inputs.
- Many open Issues with `bug`-type labels, or a severe bug → **Issue / `Quality`**
- Overdue or long-stalled Issues (no update for a long time) → **Issue** (judge the category from the content)
- Issues with unresolved external dependencies or technical spikes → **Risk / `Technical`**
- Note: never create, update or close an Issue (read-only).

### feedbacks/change-request.md (read-only)
- Unagreed or pending change requests (affecting scope, cost or deadline) → **Risk / `Budget & contract`** or **`Customer relations`**
- Approved but the increased effort is not yet reflected → **Issue / `Budget & contract`**

### mtg-logs/* and human input
- Concerns, action items and open questions raised in the meeting minutes or by the user verbally/in chat → assign a risk/issue type and category based on the content (prefer the user's own wording)

## 4. ID Numbering, Duplicate Prevention and Cross-Linking

### Numbering
- `R-xxx`: sequential from one past the highest number among the existing real data rows in `risk-list.md` §1 (if `R-001` is only a placeholder, start at `R-001`).
- `P-xxx`: the same for `problem-list.md` §1.
- Zero-padded to three digits (`R-001`, `P-012`, …). Match the existing numbering width.

### Duplicate prevention
- Cross-reference new candidates against the existing real data rows by (the gist of the content + category); if substantially the same, do not register it and report "skipped, already exists (ID)".
- Placeholder rows (the `R-001` / `P-001` rows containing `<!-- e.g. ... -->`) are not real data, so they may be overwritten (replaced) by the first real registration.

### Cross-linking (a risk materializing)
The procedure when the user judges that a risk has actually occurred:
1. Register a new `P-xxx` in `problem-list.md`. Put the original `R-xxx` in the `Originating risk ID` column, and inherit the category from the risk as a rule.
2. Update the corresponding `R-xxx` row in `risk-list.md` to `Status = Occurred (became an issue)` and record the `P-xxx` in the `Related issue ID` column.
3. Set the update date of both files to `currentDate` and append to the §4 revision history of each.
