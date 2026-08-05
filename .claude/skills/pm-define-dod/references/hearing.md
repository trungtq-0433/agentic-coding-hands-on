# Interview Details (Blocks A–D)

This file collects the **example phrasings** and **answer interpretation rules** for each block. The skill refers to it and drives the conversation one question per turn within a block.

## Common Rules

- Present options **as keywords**, not as numbered choices
- Accept free-text answers (ask a clarifying question when ambiguous)
- Items requiring a judgement — status, approval, waive/defer decisions — are never finalized without an explicit answer from the user
- When the user cannot produce a criterion, always label the AI's draft as a "draft (needs confirmation)" and wait for it to be accepted, amended or dropped
- Administrative reminders, such as prompting for a record in `problem-list.md` / `decision.md`, must not interrupt the block's conversation — report them together in the completion summary

## Block A: Criteria for Functional and Non-functional Requirements (→ define-dod.md §1)

**Example prompt**:
> My assumption is that the completion criterion is that all "must-have" functions in `function-list.md` pass acceptance testing — is that right? Should functions at "recommended" or below also be included?

**Example prompt (non-functional requirements)**:
> My assumption is to define the completion criteria per category in `non-function-list.md`. Are there categories such as performance or security that you'd like to give their own separate criteria?

**Answer interpretation rules**:
- Priorities and categories marked out of scope are not included in the criteria
- The aggregation unit (all functions in one row / grouped by priority / one row per function) follows the user's answer. The default is "one row covering all 'must-have' items, with the other priorities confirmed separately"
- When a function or non-functional requirement needs its own criterion, add it as a separate row with its `F-xxx` / `NFR-xxx` stated in the "Related ID" column
- The "Related ID (KPI/function/non-functional, etc.)" column records either the set of IDs covered, or "all"

## Block B: Criteria for the Other Categories (→ define-dod.md §1 / documents & deliverables, testing & acceptance, operational transition & handover, contract & billing)

**Example prompt (documents & deliverables)**:
> What deliverables must be delivered under the contract (design documents, manuals, the full source code, etc.)?

**Example prompt (testing & acceptance)**:
> Are there pass criteria for acceptance testing (UAT)? (e.g. zero critical bugs, all findings addressed, the client's acceptance signature, etc.)

**Example prompt (operational transition & handover)**:
> Is there an operational transition scope? (e.g. delivering the operations manual only / building the monitoring setup / handing over to a maintenance contract)

**Example prompt (contract & billing)**:
> Let me confirm the acceptance and billing completion criteria in light of the contract type in `overview.md` (quasi-delegation / fixed-price / SES). For fixed-price the criterion is often receipt of the acceptance certificate, and for quasi-delegation approval of the capacity reports — how should we define it on this project?

**Pattern for presenting an AI draft** (when the user cannot produce criteria):
> Present a draft as a confirmation — "is X the right criterion, or is there a different one?" — based on the points to consider for that category in `references/criteria-catalog.md`.

**Answer interpretation rules**:
- If the user answers "I don't know / we'll decide later", leave the criterion cell blank and report it as an open item in the completion summary
- Categories with low relevance (e.g. an internal tool with no operational transition) may be skipped with a one-line note that they are out of scope

## Block C: Adjusting the Category Guidelines (→ define-dod.md §2)

**Preliminary check**:
> Check `overview.md` §1 "Contract type" and §4 "Scope & role split". If operation & maintenance is entirely the client's, the handling of the "operational transition & handover" category may change.

**Example prompt**:
> The current categories are the six: functional requirements / non-functional requirements / documents & deliverables / testing & acceptance / operational transition & handover / contract & billing. Given this project's characteristics (contract type, role split), are there categories you'd like to add or remove?

**Answer interpretation rules**:
- For a quasi-delegation contract, propose replacing the "contract & billing" criterion with approval of the capacity reports rather than an acceptance certificate, and confirm it
- If operation & maintenance is performed entirely by the "Client" in `overview.md` §4, confirm whether to narrow "operational transition & handover" to "up to delivering the handover procedures" or mark it out of scope
- If anything is added, removed or annotated, apply it to the category table in §2 with `Edit`

## Block D: Closing Judgement (→ define-dod.md §1 from the status column onward, and §4)

**Preliminary check**:
> Assumes that Step 1 settled the mode as "closing judgement".

**Example prompt (confirming evidence)**:
> For {the criterion}, is the {acceptance test result report, etc.} recorded in the judgement method / evidence column ready? Does the result meet the criterion?

**Example prompt (when partially met)**:
> You said it is partially met — are the remaining issues registered in `problem-list.md`? If not, I recommend registering them.

**Example prompt (confirming approval of the handling)**:
> I'd propose "waive out of scope" as the handling for {criterion ID} — has the decision-maker in `stakeholders.md` ({name}) approved it?

**Answer interpretation rules**:
- The AI must never infer the status from the judgement method / evidence content. Adopt only the user's explicit answer (met / partially met / not met)
- The handling (address and meet it / waive out of scope / defer to the next phase) stays "awaiting approval" and must not be written into §1 as a confirmed value until approval is confirmed
- §4 "Overall closing judgement" is only tallied once every real data row in §1 is out of the "unsettled" state (met / partially met + handling settled / not met + handling settled). If you produce a provisional tally, state explicitly in the overall comment that it is provisional
