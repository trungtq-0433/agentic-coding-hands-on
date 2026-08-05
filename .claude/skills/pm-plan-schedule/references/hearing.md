# Interview Details (Blocks A–D)

Example prompts and interpretation rules for each block. Proceed **one to a few questions per block**, and move on only after receiving an answer.

## Common Rules

- Give keyword examples rather than numbered choices. Free text is allowed (ask a clarifying question when ambiguous).
- Never finalize milestones, effort, capacity or dependencies without an explicit answer.
- For items you could infer from the estimate or similar, ask in closed form: "I understood this as X — is that right?"

## Block A: Milestones (→ §2)

> Please tell me the main milestones (kickoff / requirements sign-off / internal release / UAT start / production release, etc.), along with each planned date and completion condition (deliverable).

- Distinguish between milestones with fixed dates (contractual deadlines, fixed days) and those determined after the WBS calculation (e.g. UAT start). The latter may be left blank for now.
- IDs use the `M-01` format, numbered chronologically.

## Block B: Effort (→ the rows in §1 and §3)

> Roughly how much effort does {phase name / function name} take? (in person-days)

- When there is an estimate: "I read the development phase total as N person-days — is that correct? How is it allocated per function?"
- When only a total per Epic is available, confirm the story-level allocation with the user (you may propose a proportional split by complexity, but never finalize it without permission).
- Leave effort that is never settled blank and report it as an open item in the summary.

## Block C: Working Capacity (→ stakeholders.md §2)

First check the contract type in `overview.md` §1 (if undecided, first confirm "lab/SES or fixed-price?").

- **Lab / SES**: > Please give {name}'s capacity in person-days per month (e.g. 20 person-days/month).
- **Fixed-price**: > Please give {name}'s total assigned person-days across the whole project (e.g. 120 person-days).
- If the answer is a utilization percentage, normalize it to person-days by asking "how many person-days per month is that, counting 1 person-day = 1 business day?"
- Hold off on the date calculation for rows involving members whose capacity is unsettled, and report them in the summary.

## Block D: Dependencies and Confirming the Function List Is Settled (→ the dependencies column of §3, and the case determination)

> Are there any schedule dependencies (client review/approval lead times, the start date of specific members, external partners' timelines, etc.)?

> **Is the function list (function-list.md) settled?**
> - Settled → plan all phases + the full WBS (Case A)
> - Not settled → plan only the requirements phase up front, and re-run SCH once it is settled (Case B)

- If the dependencies do not contradict the defaults in `references/wbs-breakdown.md` §3, adopt them as-is (do not re-ask every time).
- **Do not write assumptions into schedule.md.** Schedule assumptions and constraints (client-driven lead times, etc.) belong in `overview.md` (this skill only references the assumptions in overview).
