# Catalog of AI Draft Proposals for Completion Criteria

For each of the 6 categories in `define-dod.md` §2 ("Category guidelines"), this file describes what reasoning the AI should base a draft on when the user cannot produce criteria. **Always present them as a "draft (needs confirmation)" and turn them into confirmed values only after the user approves** (never finalize criteria without permission).

Sources to reference for the reasoning: `project/01_management/overview.md` (§1 contract type, §4 scope & role split), `project/02_requirements/function-list.md` (counts by priority), `project/02_requirements/non-function-list.md` (counts by category), `project/01_management/stakeholders.md` (§2 organization).

## Functional Requirements

**What to look at**: the priority distribution in `function-list.md` (counts of must-have / recommended / optional / out of scope), and whether there are out-of-scope functions.

**Draft examples**:
- Almost everything is priority "must-have" → "all functions with priority 'must-have' have passed acceptance testing"
- Many items at "recommended" or below → "functions with priority 'must-have' and 'recommended' have passed acceptance testing ('optional' items may be deferred to the next phase)"

## Non-functional Requirements (Quality & Performance)

**What to look at**: the counts and priorities by category in `non-function-list.md`, and whether numeric targets exist.

**Draft examples**:
- Categories with explicit numeric targets → "every item in category X meets its target value / standard (verification method: as documented in non-function-list.md)"
- Many categories with unsettled numeric targets → add the proposal "items whose target values are unsettled will be judged from measurements after go-live, so they are out of scope at closing"

## Documents & Deliverables

**What to look at**: whether the contract type (`overview.md` §1) mentions deliverables, and who performs the "Documentation" row in `overview.md` §4.

**Draft examples**:
- Fixed-price contract with a deliverables list in the contract → "the full set of deliverables listed in the contract (design documents, manuals, etc.) has been delivered"
- Lab / SES contract → "there is no contractual deliverable obligation, so the documents produced during development (design notes, handover materials, etc.) are in order"
- Documentation is performed by the client → propose marking this category out of scope, or narrowing it to "only the documents Sun* is responsible for producing"

## Testing & Acceptance

**What to look at**: who performs "acceptance testing (UAT)" in `overview.md` §4, and whether the contract states acceptance conditions.

**Draft examples**:
- UAT performed by the client → "unit / integration / system testing is complete on the Sun* side, and the client's acceptance has been obtained through UAT (zero critical bugs)"
- UAT performed by Sun* → "Sun* has completed all testing from unit through acceptance, and the client has approved the test result report"

## Operational Transition & Handover

**What to look at**: who performs "post-release operation & maintenance" and "incident response (production)" in `overview.md` §4.

**Draft examples**:
- Operation & maintenance is handed over to the client → "the operations manual, monitoring configuration and incident response flow have been handed over, and the client is in a position to begin operating"
- Sun* continues to own operation & maintenance (moving to a separate contract) → "the switch to the operation & maintenance contract and the team handover are complete"
- Out of scope (an internal tool with no operational transition) → propose marking this category out of scope in §2 (decided in Block C)

## Contract & Billing

**What to look at**: the contract type in `overview.md` §1 (quasi-delegation / fixed-price / SES).

**Draft examples**:
- Fixed-price contract → "the contracted work is complete and the acceptance certificate has been received from the client"
- Quasi-delegation / SES contract → "all capacity reports for the contract period have been approved by the client and billing is complete" (the criterion is approval of the capacity reports, not an acceptance certificate)

## Common Rules When Presenting

- Present each category's draft as a confirmation: "is X the right criterion, or is there a different one?"
- If the user answers "I don't know / we'll decide later", leave the criterion cell blank and report it as an open item in the skill's completion summary (the AI must never settle criteria unilaterally)
- Categories with low relevance (e.g. an internal tool with virtually no operational transition or handover concerns) may be skipped with a one-line note that they are out of scope (if a category was marked out of scope in §2 during Block C, do not propose a draft for it at all)
