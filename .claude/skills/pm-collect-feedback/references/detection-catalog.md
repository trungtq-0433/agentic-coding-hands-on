# Feedback Detection Catalog

The set of rules for detecting feedback candidates from the meeting minutes and human input, and for categorizing, routing and numbering them. Referenced from Steps 2A/2B/3 of the skill body (`SKILL.md`).

## 1. What Counts as Feedback (what to pick up)

What this skill records in `feedback-list.md` is **"day-to-day opinions, improvement requests and observations where it is not yet decided whether to act"**. Distinguish it from:

| Type | Example | Handling |
|------|-----|------|
| **Feedback** (pick up) | "I'd like more rows shown on the list screen", "the steps are hard to follow", "the response feels slow" | Register in feedback-list.md and track provisionally |
| Bugs and defects (do not pick up) | "pressing save crashes with an error", "the total is calculated wrong" | If it will be acted on, hand it over to problem-list.md (RISK) (§3) |
| Decisions (do not pick up) | "agreed on a 3-business-day lead time" | Owned by decision.md. This skill does not handle it |
| Work already turned into tasks (do not pick up) | Items already raised in task-list.md / GitHub Issues | Skip as duplicates (§4) |

When the judgement is ambiguous (bug or improvement request?), present it as a candidate, ask one question, and let the user make the call.

## 2. Category Definitions (5)

Matches feedback-list.md §2. Always choose exactly one. For vague wording ("hard to use", etc.), ask one question about which aspect is meant and assign accordingly.

| Category | Description | Clues for assigning |
|----------|------|----------------|
| `UI/UX` | Opinions about screen presentation and usability | "hard to read", "hard to click", "the flow is confusing", "rows shown" |
| `Function` | Opinions about how usable or complete the functionality is (excluding defects) | "I'd like to be able to …", "this function is missing", "I want to add a field" |
| `Documentation` | Opinions about the content of manuals, specifications, etc. | "the manual is out of date", "it differs from the specification", "please add an explanation" |
| `Performance` | Opinions about response time and processing performance | "slow", "takes a long time to load", "sluggish" |
| `Other` | Opinions and observations that fit none of the above | When nothing above clearly applies |

## 3. Detection Rules (by input)

### 3-1. Meeting minutes (`project/01_management/mtg-logs/*`)

Scan them with the structure of the minutes template in mind:

- **"3. Discussion"** — extract the opinions, requests, concerns and observations raised by the client or by Sun*. Map the speaker to `Source` (e.g. `Client (Mr./Ms. Suzuki)` / `Sun* (internal)`), and the meeting type to `Origin` (e.g. `Regular meeting` / `Review` / `UAT`).
- **"4. Decisions"** — do not pick up decisions (owned by decision.md).
- **"5. Action items"** — improvement requests whose `Related ID (task-list.md)` is still empty (not yet turned into a task) may become feedback candidates. Do not pick up items that are already tasks.
- Use the meeting date of those minutes as the `Date received` by default.

### 3-2. Human input

Turn the opinions the user pastes into the chat or raises verbally from reviews, UAT and regular meetings straight into candidates. If the source, origin or date received is unknown, confirm it in Block C.

## 4. Routing Rules (the handling)

Matches the handling flow in feedback-list.md §3. **Only for entries decided to be acted on**, guide the user to the appropriate downstream step (this skill never raises or registers anything).

| Nature of the content | Handover target | Related ID to record |
|------------|-----------|----------------|
| A change affecting scope, schedule or budget | `change-request.md` (CR / change management) | `CR-xxx` |
| A bug or defect | `problem-list.md` (`pm-track-risks-issues`/RISK) | `P-xxx` |
| An improvement or request needing implementation (not covered above) | `pm-create-tasks` (TASK) → GitHub Issue | `T-xxx` or the Issue URL |
| A minor improvement or something to consider later (not implemented now) | Tracked in this list (no handover) | Blank |

- Running the handover target is **only guided to the user**. The generated ID/URL may be backfilled into the `Related ID` column on a later run (the Issue URL can be checked with `gh issue view`).
- When one piece of feedback matches several rows (e.g. both a bug and a scope change), choose one primary handover target and list the related IDs together.

## 5. Status Definitions (expressed in the existing "Status" column — never add columns)

The values allowed in the `Status` column of feedback-list.md. Never add new sections to the template; this catalog is the authority for the definitions.

| Status | Meaning | Next transition |
|-----------|------|----------|
| `Open` | Just registered. Whether to act is undecided | → `Under consideration` / act / `Will not act` |
| `Under consideration` | Whether to act is being considered (internally or with the client) | → act / `Will not act` |
| `Will not act` | Decided not to act (record the reason in the handling column). Closed within this list | (terminal) |
| `In progress` | Decided to act, and the work is progressing at the handover target (CR/P/T/Issue) | → `Done` |
| `Done` | The handling is complete | (terminal) |

- For `Open` / `Under consideration` entries (before a decision), the handling, owner and related ID may be left blank (provisional tracking).
- The status and the decision on whether to act are always settled by the user's explicit answer. Never fill them in by guesswork.

## 6. FB-ID Numbering, Duplicate Prevention and Related IDs

- **Numbering**: `FB-` plus a three-digit zero-padded sequence (`FB-001`, `FB-002`, …). Number from one past the highest FB-ID among the real data rows in `feedback-list.md`. The template placeholder `FB-001` (whose cells are HTML comments only) is replaced by the first real data.
- **Duplicate prevention**: cross-reference new candidates against the existing real data rows by (feedback content + category); if substantially the same, report "skipped, already exists (FB-ID)" and do not register it. Also do not register content already raised in task-list.md / GitHub Issues.
- **Related IDs**: once the handover target is settled, record `CR-xxx` / `P-xxx` / `T-xxx` / the Issue URL in the `Related ID (change request / issue)` column. Several may be listed, comma-separated.
- **Dates**: the date received is the meeting date from the minutes when known, otherwise `currentDate`. The update date is always `currentDate`.
