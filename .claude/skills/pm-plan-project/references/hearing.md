# Interview Details (Blocks A–E)

This file collects the **example phrasings** and **answer interpretation rules** for each block. The skill refers to it and drives the conversation one question per turn within a block. It covers only the items that `field-mapping.md` marks as "cannot be extracted from the documents"; for items already extracted, switch to a confirmation question.

## Common Rules

- Present options **as keywords**, not as numbered choices
- Accept free-text answers (ask a clarifying question when ambiguous)
- For items inferred from the documents, ask in the form "I understood this as X — is that right?" (do not use an open question)
- Items requiring a judgement or a number (KPIs, trade-off allocation) are never finalized without an explicit answer from the user

## Block A: Basic Info (→ overview.md §1)

**Example prompt (when nothing could be taken from the documents)**:
> Let me confirm the basics of the project. Could you tell me the project name, the client name, the contract type (fixed-price / quasi-delegation / SES, etc.), the contract period, and the project type (new development / maintenance & operation / replacement, etc.)?

**Example confirmation question (when it could be inferred from the documents)**:
> From the estimate I read the contract type as quasi-delegation and the contract period as August 2026 – January 2027 — is that correct?

**About the project code**:
> What should we use as the internal project code? (e.g. an abbreviation of the client name plus the year is fine)

## Block B: KPIs & Success Criteria (→ overview.md §2)

**Example prompt**:
> Could you tell me the success criteria for this project? Are there measurable numeric targets (number of contracts, retention rate, churn rate, etc.)?

**Answer interpretation rules**:
- If only a qualitative answer is given (e.g. "improve operational efficiency") → confirm "so concrete numeric targets are still undecided, correct? I'll leave the KPI fields blank so they can be added later" and do not force a number
- If the proposal states something qualitative, read it back and then ask "if we turn this into a measurable numeric target, what would it look like?"

## Block C: Way of Working & Organization (→ overview.md §3, stakeholders.md §2)

**Example prompt**:
> Let me confirm how development will run. Which approach do you have in mind — agile or waterfall?
> What communication channels will you use? (e.g. Chatwork / Slack / Teams / email + Backlog, Jira, etc.)
> What ticket management tool will you use? (e.g. GitHub Issues / Backlog / Jira, etc.)

**About the Sun*-side organization (when a cost sheet exists)**:
> From the cost sheet I read the team as 1 PM, 3 engineers and 1 QA — could you give me their names and contact details?

**When there is no cost sheet**:
> Could you tell me the names and contact details of the Sun*-side team (PM / tech lead / developers / QA)?

## Block D: Scope & Role Split (→ overview.md §4)

**Example prompt**:
> Let me confirm the role split across the development phases. Are requirements, design, development and testing all expected to be handled by Sun*? Among them, are there phases the client will handle (e.g. UAT, production infrastructure setup, data migration)?

**Example confirmation question (when the scope could be read from the proposal)**:
> From the proposal I read it as Sun* handling requirements through integration testing, and the client handling acceptance testing (UAT) and production environment setup — is that correct?

**Cross-checking against the contract type**:
> You mentioned the contract type is {fixed-price / quasi-delegation}, so {for fixed-price: "Sun* bears responsibility for completing the deliverable — is the assumption that the client will provide the UAT and acceptance criteria?" / for quasi-delegation: "Sun* is responsible for performing the work, but is the assumption that decision-making and acceptance judgements are made by the client?"}

**About confirming out-of-scope work**:
> Please tell me about any work Sun* will not handle (e.g. production infrastructure setup and operation, UAT) or that the client will not handle (e.g. data migration, documentation). Making this explicit avoids disputes later about work outside the contract or estimate scope.

Express the answers in the **"Performed by" column of the scope & role split table** ("Client", "Out of scope", etc.). Do not create a standalone "out-of-scope" subheading in overview.md (it would duplicate the table).

**Answer interpretation rules**:
- Settle each work item as one of "Sun*", "Client" or "Joint". For "Joint", add a note on who leads
- For a vague answer (e.g. "basically leave it to Sun*") → confirm the test phases (UT/IT/ST/UAT) and production work (infrastructure setup, release, operation) individually. UAT and production infrastructure setup in particular are often the client's responsibility — never write "Sun*" on assumption
- If the contract type (fixed-price / quasi-delegation) and the role split contradict each other (e.g. a fixed-price contract where Sun* has final decision rights over requirements) → go back to the premise (Block A) and confirm

## Block E: Client Organization & Flows (→ stakeholders.md §1, §3, §4, §5)

**Example prompt (fine to ask together)**:
> Could you tell me about the client-side organization? Please give me the names, affiliations and contact details of the decision-maker (final approver), the project owner, and the point of contact (PM/PL). All at once is fine.

**About the approval flow**:
> When a requirement/specification change or a schedule change comes up, who proposes it, who reviews it and who approves it?

**About escalation**:
> Please tell me the escalation contacts when issues or trouble arise, and the target response times (e.g. first level within one business day, second level same day).

**About communication frequency**:
> Please tell me the frequency of regular meetings, and the channels and timing for day-to-day communication. (Here you are confirming how the communication channels identified in Block C are used by frequency and purpose.)

## Block F: Constraints & Trade-offs (→ overview.md §5, §6)

**About constraints**:
> Are there any technical constraints, external system integrations, or budget/resource constraints?

**About the trade-off allocation**:
> If you were to allocate 14 points in total across Delivery (hitting the deadline), Cost (staying within budget), Quality and Scope (feature range), which would you weight most heavily?

**When presenting the proposal's tone as a hypothesis**:
> The way the proposal is written suggests you prioritize Delivery (releasing on time) — is it OK to allocate on that understanding? Please give me the specific numbers (pts).

**Answer interpretation rules**:
- If the answer does not total 14 pts → re-confirm ("could you adjust so the total comes to 14 pts?")
- For a vague answer such as "they're all equally important" → prompt again with "if you had to prioritize". If it still cannot be decided, leave it blank and report it as an open item in the Step 6 completion summary
