# Validation Question Framework

## Question Categories

| Category | Keywords to detect |
|----------|-------------------|
| **Architecture** | "approach", "pattern", "design", "structure", "database", "API" |
| **Assumptions** | "assume", "expect", "should", "will", "must", "default" |
| **Tradeoffs** | "tradeoff", "vs", "alternative", "option", "choice", "either/or" |
| **Risks** | "risk", "might", "could fail", "dependency", "blocker", "concern" |
| **Scope** | "phase", "MVP", "future", "out of scope", "nice to have" |

## Question Format Rules

- Give every question 2-4 concrete options
- Tag the one you'd recommend with a "(Recommended)" suffix
- The "Other" option shows up on its own
- Aim each question at a decision that's been left implicit

## Example Questions

Category: Architecture
Question: "How should the validation results be persisted?"
Options:
1. Save to plan.md frontmatter (Recommended)
2. Create validation-answers.md
3. Don't persist

Category: Assumptions
Question: "The plan assumes API rate limiting is not needed. Is this correct?"
Options:
1. Yes, not needed for MVP
2. No, add basic rate limiting now (Recommended)
3. Defer to Phase 2

## Validation Log Format

```markdown
## Validation Log

### Session {N} — {YYYY-MM-DD}
**Trigger:** {what prompted this validation}
**Questions asked:** {count}

#### Questions & Answers

1. **[{Category}]** {full question text}
   - Options: {A} | {B} | {C}
   - **Answer:** {user's choice}
   - **Custom input:** {verbatim "Other" text if applicable}
   - **Rationale:** {why this decision matters}

#### Confirmed Decisions
- {decision}: {choice} — {brief why}

#### Action Items
- [ ] {specific change needed}

#### Impact on Phases
- Phase {N}: {what needs updating and why}
```

## Recording Rules

- **Full question text**: the question word for word, not a paraphrase
- **All options**: every option you put on the table
- **Verbatim custom input**: the "Other" text exactly as typed
- **Rationale**: say why this decision steers the build
- **Session numbering**: bump it up from the last session
- **Trigger**: note what set this validation off

## Section Mapping for Phase Propagation

| Change Type | Target Section |
|-------------|----------------|
| Requirements | Requirements |
| Architecture | Architecture |
| Scope | Overview / Implementation Steps |
| Risk | Risk Assessment |
| Unknown | Key Insights (new subsection) |
