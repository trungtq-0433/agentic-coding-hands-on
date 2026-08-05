# Solution Design

## Core Principles

Keep these three close at every turn:
- **YAGNI** (You Aren't Gonna Need It) - leave the feature out until something actually needs it
- **KISS** (Keep It Simple, Stupid) - reach for the simple shape before the clever one
- **DRY** (Don't Repeat Yourself) - one source of truth, no copy-paste logic

## Design Activities

### Technical Trade-off Analysis
- Weigh more than one approach per requirement
- Set each option's gains against its costs
- Hold the near-term win up against the long-term bill
- Trade complexity off against maintainability deliberately
- Ask whether the effort is worth what it buys
- Land on the strongest option, grounded in current practice

### Security Assessment
- Spot the soft spots while it's still on paper
- Settle who authenticates and who's authorized
- Work out what the data needs protecting from
- Decide where input has to be validated
- Plan how secrets and config stay safe
- Walk the OWASP Top 10
- Cover the API surface — rate limiting, CORS, the rest

### Performance & Scalability
- Find the bottlenecks before they find you
- Look hard at the database queries
- Decide where caching earns its keep
- Account for memory, CPU, and network
- Leave room to scale out or up
- Think about how load gets spread
- Push work off the critical path where it makes sense

### Edge Cases & Failure Modes
- Walk the error paths deliberately
- Assume the network will drop
- Decide what a partial failure looks like
- Build the retries and the fallbacks
- Keep the data consistent under stress
- Watch for the races
- Aim for graceful degradation, not a hard stop

### Architecture Design
- Shape a system that can grow
- Build for the people who maintain it next
- Map how the components talk
- Trace the data as it moves
- Weigh microservices against a monolith honestly
- Nail down the API contracts
- Decide where state lives and how it changes

## Best Practices

- Write down each design call and the reasoning behind it
- Hold both the technical and the business needs in view
- Walk the whole user journey end to end
- Plan for monitoring and the ability to see inside
- Design as if tests are coming, because they are
- Think through how it deploys — and how it rolls back
