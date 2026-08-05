# Catalog of AI Draft Proposals for Non-functional Requirements

For each of the 8 categories in `non-function-list.md` §2 ("Category guidelines"), this file describes what reasoning the AI should base a draft on when the user cannot provide numeric targets. **Always present them as a "draft (needs confirmation)" and turn them into confirmed values only after the user approves** (never finalize numbers without permission).

Sources to reference for the reasoning: `project/02_requirements/system-overview.md` (target platform, service overview, background problems), the proposal / project brief (client brief), and the interview content.

## Performance

**What to look at**: the target platform (web / mobile / enterprise system), expected concurrent users, whether real-time behavior is required.

**Draft examples**:
- A typical web admin UI → "list and detail screens render within 3 seconds"
- Search and listing as the main functions → "search results render within 3 seconds (99th percentile within 5 seconds)"
- When the reasoning is thin, do not put out a specific number of seconds; propose "performance targets to be set separately based on measurements after go-live" and also offer the option of leaving it blank

## Availability

**What to look at**: whether it is an enterprise system (internal, only needs to run on weekdays during business hours) or consumer-facing (24/365 operation assumed), and whether the contract states an uptime SLA.

**Draft examples**:
- Internal business system → "uptime around 99% (excluding planned downtime and maintenance), RTO 1 business day, RPO 24 hours"
- Consumer-facing service → "uptime around 99.5%; RTO/RPO to be discussed separately depending on the scope of impact of an incident"

## Security

**What to look at**: whether it handles sensitive data such as personal, payment or medical information, and whether it is publicly exposed or internal only.

**Draft examples**:
- A web service handling personal data (email, name, etc.) → "TLS required for all traffic, passwords stored hashed, access to personal data restricted to authorized roles only"
- Handles payment data → "note compliance with applicable guidelines such as PCI DSS as an item under consideration (details to be settled in a separate security design)"
- Internal-only system with low sensitivity → "basic authentication and authorization are sufficient; details to be discussed with the operations owner"

## Extensibility

**What to look at**: expected future traffic growth and expected feature additions (a roadmap in the proposal, etc.).

**Draft examples**:
- When the proposal states a clear future plan → turn that statement into a draft as-is and confirm it
- When nothing is stated → present it with blanks, e.g. "no clear expansion plan at this point; whether to design for future feature additions is to be discussed separately"

## Operability & Maintainability

**What to look at**: the operating model (does Sun* also handle operations, or is it handed over to the client?) and whether there is monitoring/alerting (refer to the communication channels and organization info in `overview.md`).

**Draft examples**:
- A contract where Sun* also handles operations → "error logging and monitoring, alert notifications when incidents occur"
- A development-only contract handed over to the client → "completion is defined as delivering the operations manual and deployment procedures; the monitoring setup is built separately by the client"

> **Compatibility (supported browsers / OS / devices and target test environments) is out of scope for this catalog.** Those requirements are defined in the test planning phase (`project/05_test/test-plan.md`), so this skill (requirements definition) does not propose them as NFRs.

## Laws & Regulations

**What to look at**: whether personal data is handled (personal data protection law), and whether there are industry-specific regulations (medical, financial, education, etc.).

**Draft examples**:
- Handles personal data → "appropriate collection, use and storage in accordance with the personal data protection law"
- When industry-specific regulation seems likely → list the regulations that may apply while stating explicitly that "the details require legal confirmation on the client side"; the AI must not assert whether a regulation applies

## Data Management

**What to look at**: the importance of the data (would business stop if it were lost?) and the expected retention period (inferred from the proposal and contract period).

**Draft examples**:
- Ordinary business data → "daily backups; data retained for the contract period plus a margin (e.g. 1 year after contract end)"
- Highly critical data (payment history, etc.) → propose stricter backup frequency and retention, and state explicitly that "the concrete numbers require client confirmation"

## Common Rules When Presenting

- Present each category's draft as a confirmation: "is X the right understanding, or is there a different standard?"
- If the user answers "I don't know / we'll decide later", leave the target-value and standard cells blank and report it as an open item in the skill's completion summary (the AI must never fill in numbers unilaterally)
- Categories with low relevance (e.g. an internal tool with virtually no legal or regulatory concerns) may be skipped with a one-line note that they are out of scope
