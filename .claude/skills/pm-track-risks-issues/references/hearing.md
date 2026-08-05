# Interview Details (Blocks A–C)

This file collects the **example phrasings** and **answer interpretation rules** for each block. The skill refers to it and drives the conversation one question per turn within a block.

## Common Rules

- Present options **as keywords**, not as numbered choices
- Accept free-text answers (ask a clarifying question when ambiguous)
- Items requiring judgement — status, whether to turn a risk into an issue, probability/impact/priority — are never finalized without an explicit answer from the user
- Always label detected candidates as "candidate (needs confirmation)" and wait for the user to accept, amend or reject them
- Administrative reminders, such as prompting for a record in `decision.md`, must not interrupt the block's conversation — report them together in the completion summary

## Block A: Choosing the Job (→ main flow Step 1)

**Example prompt**:
> Which would you like to do for risk and issue management this time?
> - (1) **Status review**: go through the existing risks and issues (monitoring / open / in progress) and check whether they still stand, have been resolved, or have progressed
> - (2) **New detection**: comb the schedule, progress, GitHub Issues, meeting minutes and so on for new risks and issues, and register them
>
> (You can also do both, in the order 1 → 2.)

**Answer interpretation rules**:
- (1) → Step 2A, (2) → Step 2B, both → run 2A then 2B
- If there is zero real data (still a template), say so and recommend (2)
- If the user names a specific risk/issue, you may go straight into reviewing (1) or registering (2) that entry

## Block B: Reviewing Existing Risks/Issues (job 1 → Step 2A)

**Present first**: list the active entries (risks that are `Monitoring`, issues that are `Open` / `In progress` / `On hold`) and confirm them one at a time.

**Example prompt (risk)**:
> How does risk `R-003` (Schedule: the client review lead time is a placeholder) stand now?
> - Still valid (keep monitoring) /
> - It actually happened (→ I'll register it as an issue) /
> - Resolved (the countermeasure worked, or it is no longer needed)

**Example prompt (issue)**:
> Has issue `P-002` (Quality: a severe bug in integration testing) progressed? If it is resolved, tell me what was done; if it is ongoing, tell me the current situation.

**Answer interpretation rules**:
- **Risk materializing**: "it happened" → register a new `P-xxx` in `problem-list.md` (`Originating risk ID` = that `R-xxx`, category inherited), update the risk row to `Occurred (became an issue)` and record the `Related issue ID` (detection-catalog.md §4)
- **Risk disappearing**: resolved by the countermeasure = `Resolved`; minor impact or circumstances changed = `No action needed`
- **Issue progress**: handling complete = `Resolved` (record what was done and any comments) / ongoing = `In progress` (update the comment) / deferred for now = `On hold`
- In every case set the update date to `currentDate`. If a judgement is ambiguous, ask a clarifying question and leave the existing value unchanged until settled

## Block C: Interviewing About New Risks/Issues (job 2 → Step 2B)

**Present first**: list the candidates enumerated from each input using the detection rules in `references/detection-catalog.md` as "candidates (needs confirmation)" (risk or issue, category, content). Then ask for additions.

**Example prompt (confirming the automatic detection)**:
> From the progress tracker and the GitHub Issues, the following risk and issue candidates came up. Please tell me whether to register them, or whether they need amending or rejecting.
> (e.g. milestone `M-02` is 3 days behind → issue candidate / Schedule; 5 unresolved Issues with the `bug` label → issue candidate / Quality)

**Example prompt (additional interview)**:
> Besides the above, are there any risks you're currently concerned about (things that haven't happened but could), or issues that have already occurred? (staffing, agreement with the customer, budget and contract, etc.)

**Interviewing about the ratings (presenting a draft when the user cannot produce values)**:
- Risk:
  > What are this risk's **probability** (high/medium/low) and **impact** (high/medium/low)? If it's hard to judge, I'd tentatively put "probability: medium / impact: high (= risk level high)" based on the content — does that work?
  (The risk level is determined automatically by the judgement matrix in `risk-list.md` §2. Never change the matrix.)
- Issue:
  > How should we treat this issue's **priority** (high/medium/low)? As a guide, "high" if it directly affects work in progress or the release, "medium" if it needs prompt attention but is not an immediate blocker.

**Answer interpretation rules**:
- The category must always be one of the 6 (Technical / Schedule / Budget & contract / Quality / Team & staffing / Customer relations). If the user uses a vague word such as "management", ask one question using the mapping table in detection-catalog.md §2 and assign it
- Present probability, impact and priority as a "draft (needs confirmation)" and settle them with the user's confirmation. Leave unsettled values blank
- Candidates that are substantially the same as an existing entry are reported as "skipped, already exists (ID)" and not registered
- Response plans, owners and deadlines the user defers with "we'll decide later" are left blank and reported as open items in the completion summary
