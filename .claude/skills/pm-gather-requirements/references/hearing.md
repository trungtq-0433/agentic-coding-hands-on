# Interview Details (Blocks O–D)

This file collects the **example phrasings**, **answer interpretation rules** and **ordering dependencies** for each block. The skill refers to it and drives the conversation one question per turn within a block.

## Common Rules

- Present options **as keywords**, not as numbered choices
- Accept free-text answers (ask a clarifying question when ambiguous)
- For items inferred from the proposal or project brief, ask in the form "I understood this as X — is that right?" (do not use an open question)
- The block order (O → A → B → C → D) has dependencies: O (overview) is the premise for everything, B (functions) references the ROLE-IDs from A (roles), and D (glossary) aggregates the terms that came up in O–C. C (non-functional) may proceed independently of the other blocks.

## Block O: Project Overview (→ system-overview.md §1–§3)

**Premise**: handle this first. The picture of the service, its background and its objectives established here become the basis for judgements in A–D. KPIs and success criteria are out of scope for this file (`project/01_management/overview.md` = owned by pm-plan-project). Do not interview about them, do not write them, and do not add a reference row for them.

**§1 Service overview — example prompt**:
> What kind of service is this system? Please tell me the service name, the target platform (web / mobile / enterprise system, etc.), and roughly what it handles and who uses it.

**Example confirmation question (when it could be inferred from the documents)**:
> From the proposal I understood this as "a POS sales management system for multi-store retail (web, used by head office and each store)" — is that correct?

**§2 Background & problems — example prompt**:
> What operational problems exist today (as-is), and why is this system needed?

**When the user cannot produce them (AI hypothesis)**:
From the project's characteristics (industry, target operations, scale), propose the as-is state / problems / impact of leaving them unaddressed as a "**hypothesis (needs client confirmation)**", and write it in only after approval. State clearly in the body that it is a hypothesis (e.g. a note: "the following is a hypothesis based on general characteristics; do not treat it as confirmed information before client confirmation").

**§3 Objectives & value delivered — example prompt**:
> Please tell me what you want to achieve with this system (the objectives) and the value it brings to its users, such as head office and the individual stores.

**Answer interpretation rules**:
- Much of §1–§2 can be taken from the documents. Present what you read first, and interview only about the gaps and differences
- Never assert the background and problems. Always attach "needs client confirmation" to a hypothesis

## Block A: Role List (→ role-list.md §1)

**Example prompt (when nothing could be taken from the documents)**:
> Please tell me the people and roles who will use this system. Feel free to include not only general users but also administrators, operations staff, and accounts for external integrations.

**Example confirmation question (when it could be inferred from the documents)**:
> From the project brief I understood there are two roles — general members and site administrators. Is that correct? Are there any roles I've missed?

**Items to dig into** (fine to ask about all roles together, not one by one):
> For each role, please tell me the expected headcount or scale (e.g. several thousand general members, around 5 administrators in-house) and anything else worth noting.

**Answer interpretation rules**:
- If only a vague grouping such as "end user" comes up, ask exactly one question about whether it splits into sub-roles with different permissions (free member / paid member, etc.)
- Role IDs are numbered from `ROLE-001`. The `ROLE-001`/`ROLE-002` in the existing template are examples — overwrite them with real data

## Block B: Function List (→ function-list.md)

**Premise**: uses the ROLE-IDs settled in Block A.

**Example prompt**:
> Please tell me the functions this system will provide. Whatever comes to mind first is fine — we'll organize the priorities together afterwards.

**Confirming priority**:
> Is function X closest to must-have (absolutely required for the MVP), recommended, optional, or out of scope?

**Confirming target roles**:
> Which of the roles we listed earlier will use function X? (multiple roles are fine)

**Answer interpretation rules**:
- When there are many functions, do not dig into all of them at once: first list every function name and summary, then confirm the priority and target roles one function at a time
- The "Detail document" column (per-function business flows and I/O) is out of scope for this skill. If the user starts describing details (input/output items, business rules) during the interview, take them at the summary level and move on, saying "we'll dig into the details when the per-function specifications are written"
- Function IDs are numbered from `F-001`

## Block C: Non-functional Requirements (→ non-function-list.md)

**Premise**: refer to `references/nfr-catalog.md`. Can proceed independently of the other blocks.

**Example prompt (ask first)**:
> Are there any numeric targets or standards already decided for performance, availability, security, etc.? (e.g. response time, uptime, expected concurrent users)

**When the user cannot produce them**:
Refer to the relevant category in `references/nfr-catalog.md` and propose a draft with stated reasoning derived from the project's characteristics (target platform, sensitivity of the data handled, expected scale).

**Example of presenting a draft**:
> If there are no concrete standards yet — since this is a web service that will handle personal data such as email addresses — how about putting down "Security: TLS required for all traffic" and "Laws & regulations: handling in accordance with the personal data protection law" as a draft? We can adjust it later.

**Answer interpretation rules**:
- Always make clear that it is a "draft (needs confirmation)", and write it in as a confirmed value only after the user approves
- Do not force-fill categories that do not apply (e.g. an internal tool outside any regulation) — mark them out of scope
- Rather than mechanically asking about all 8 categories, prioritize the ones that matter most given the project's characteristics

## Block D: Glossary (→ glossary.md)

**Premise**: note down the business terms, abbreviations and client-specific words that come up during the Block O–C interviews (no need to write them to a separate file — just remember them within the conversation).

**Example of confirming them together**:
> Terms such as "X" and "Y" came up during our discussion — could you give me a brief definition of each? If there are other abbreviations or in-house/client-specific terms you use often, please tell me those too.

**Answer interpretation rules**:
- General IT terms (login, CSV, etc.) are generally out of scope. Focus on domain-specific and client-specific vocabulary
- If a definition is ambiguous, ask exactly one clarifying question. If it cannot be settled, it is fine to record just the term and leave the definition blank (report it as an open item in the completion summary)
