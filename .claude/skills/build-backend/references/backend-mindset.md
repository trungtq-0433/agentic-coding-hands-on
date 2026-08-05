# Backend Development Mindset

How a backend engineer reasons through problems, shapes architecture, and works alongside a team (2025).

## How to Reason Through a Problem

### Seeing the Whole Machine, Not One Gear

**Holistic Engineering** — read every component as a moving part inside one running ecosystem, never as a thing standing on its own.

```
User Request
  → Load Balancer
  → API Gateway (auth, rate limiting)
  → Application (business logic)
  → Cache Layer (Redis)
  → Database (persistent storage)
  → Message Queue (async processing)
  → External Services
```

**The questions worth asking up front:**
- What happens if this component fails?
- How does this scale under load?
- What are the dependencies?
- Where are the bottlenecks?
- What's the blast radius of changes?

### Cutting a Big Ask Down to Size

**Decomposition Strategy:** take a vague, oversized request and split it into a run of small, concrete moves.

1. **Understand requirements** — what problem are we actually solving?
2. **Identify constraints** — performance, budget, timeline, tech stack
3. **Break into modules** — split the concerns apart (auth, data, business logic)
4. **Define interfaces** — the API contracts that join the modules
5. **Prioritize** — clear the critical path first
6. **Iterate** — build it, test it, sharpen it

**Example: Building Payment System**

One vague line on the left; the actual workshop checklist on the right.

```
Complex: "Build payment processing"

Decomposed:
1. Payment gateway integration (Stripe/PayPal)
2. Order creation and validation
3. Payment intent creation
4. Webhook handling (success/failure)
5. Idempotency (prevent double charges)
6. Retry logic for transient failures
7. Audit logging
8. Refund processing
9. Reconciliation system
```

## Weighing the Trade-Offs

### CAP Theorem (Choose 2 of 3)

When the network splits, you walk away with two of the three. There is no fourth option.

**Consistency** — All nodes see same data at same time
**Availability** — Every request receives response
**Partition Tolerance** — System works despite network failures

**Where each pairing lands in practice:**
- **CP (Consistency + Partition Tolerance):** Banking systems, financial transactions
- **AP (Availability + Partition Tolerance):** Social media feeds, product catalogs
- **CA (Consistency + Availability):** Single-node databases (not distributed)

### PACELC Extension

CAP speaks only to the partition. PACELC finishes the sentence by asking what you trade when everything is healthy.

**If Partition:** Choose Availability or Consistency
**Else (no partition):** Choose Latency or Consistency

**How it shakes out:**
- **PA/EL:** Cassandra (stays up through a partition, keeps latency low the rest of the time)
- **PC/EC:** HBase (holds consistency in a partition, and keeps holding it over speed afterward)
- **PA/EC:** DynamoDB (you dial the consistency-versus-latency knob yourself)

### Performance vs Maintainability

Let the location of the code and how often hands touch it decide which way you lean.

| Optimize For | When to Choose |
|--------------|---------------|
| **Performance** | Hot loops, endpoints under heavy traffic, anything real-time |
| **Maintainability** | Internal utilities, admin panels, plain CRUD work |
| **Both** | The money-handling core: business rules, payments, auth |

**Example:**
```typescript
// Maintainable: Readable, easy to debug
const users = await db.users.findAll({
  where: { active: true },
  include: ['posts', 'comments'],
});

// Performant: Optimized query, reduced joins
const users = await db.query(`
  SELECT u.*,
    (SELECT COUNT(*) FROM posts WHERE user_id = u.id) as post_count,
    (SELECT COUNT(*) FROM comments WHERE user_id = u.id) as comment_count
  FROM users u
  WHERE u.active = true
`);
```

### Keeping Technical Debt Honest

Retiring debt deliberately pays you back in hours: handle it well and teams report a **20-40% productivity increase**.

**The four corners of debt:**
1. **Reckless + Deliberate:** "No time to design this properly"
2. **Reckless + Inadvertent:** "Layering — what's that?"
3. **Prudent + Deliberate:** "Ship it now, clean it up next sprint" (acceptable)
4. **Prudent + Inadvertent:** "Turns out there was a better way all along" (acceptable)

**Deciding what to pay first:**
- High interest, high impact → Pay it down now
- High interest, low impact → Slot it into a sprint
- Low interest, high impact → Park it on the tech-debt backlog
- Low interest, low impact → Let it sit

## Thinking in Architecture

### Domain-Driven Design (DDD)

**Bounded Contexts** — let each domain carry its own model rather than stretching a single model to cover everything at once.

```
E-commerce System:

[Sales Context]          [Inventory Context]       [Shipping Context]
- Order (id, items,      - Product (id, stock,     - Shipment (id,
  total, customer)        location, reserved)       address, status)
- Customer (id, email)   - Warehouse (id, name)    - Carrier (name, API)
- Payment (status)       - StockLevel (quantity)   - Tracking (number)

Each context has its own:
- Data model
- Business rules
- Database schema
- API contracts
```

**Ubiquitous Language** — engineers and domain experts settle on one shared vocabulary, so the names in the code are the names the business already uses.

### Stacking the Layers So Concerns Stay Apart

A layer reaches only for the layer directly beneath it, and no responsibility leaks past its boundary.

```
┌─────────────────────────────┐
│   Presentation Layer        │  Controllers, Routes, DTOs
│   (API endpoints)           │
├─────────────────────────────┤
│   Business Logic Layer      │  Services, Use Cases, Domain Logic
│   (Core logic)              │
├─────────────────────────────┤
│   Data Access Layer         │  Repositories, ORMs, Database
│   (Persistence)             │
└─────────────────────────────┘
```

**What this buys you:**
- Each layer owns a clear job
- Testing gets simpler — swap a layer for a mock
- Implementations can change underneath without ripple
- Less coupling overall

### Designing for Failure (Resilience)

Assume every dependency will fall over at some point — because, given enough time, each one does.

**The patterns that hold the line:**
1. **Circuit Breaker** — quit hammering a service that's already down
2. **Retry with Backoff** — back off exponentially between attempts
3. **Timeout** — cap how long you're willing to wait
4. **Fallback** — degrade gracefully instead of erroring out
5. **Bulkhead** — wall failures off behind separate resource pools

```typescript
import { CircuitBreaker } from 'opossum';

const breaker = new CircuitBreaker(externalAPICall, {
  timeout: 3000, // 3s timeout
  errorThresholdPercentage: 50, // Open after 50% failures
  resetTimeout: 30000, // Try again after 30s
});

breaker.fallback(() => ({ data: 'cached-response' }));

const result = await breaker.fire(requestParams);
```

## How a Developer Holds the Work

### Code That Stays Maintainable

**SOLID Principles:**

**S - Single Responsibility** — a class should answer to exactly one reason to change.
```typescript
// Bad: User class handles auth + email + logging
class User {
  authenticate() {}
  sendEmail() {}
  logActivity() {}
}

// Good: Separate responsibilities
class User {
  authenticate() {}
}
class EmailService {
  sendEmail() {}
}
class Logger {
  logActivity() {}
}
```

**O - Open/Closed** — reach for new behavior by extending the code, leaving the parts that already work untouched.
```typescript
// Good: Strategy pattern
interface PaymentStrategy {
  process(amount: number): Promise<PaymentResult>;
}

class StripePayment implements PaymentStrategy {
  async process(amount: number) { /* ... */ }
}

class PayPalPayment implements PaymentStrategy {
  async process(amount: number) { /* ... */ }
}
```

### Working the Edges

The bugs worth fearing don't sit on the happy path — they hide out at the boundaries.

**The edges that bite most often:**
- Empty arrays/collections
- Null/undefined values
- Boundary values (min/max integers)
- Concurrent requests (race conditions)
- Network failures
- Duplicate requests (idempotency)
- Invalid input (SQL injection, XSS)

```typescript
// Good: Handle edge cases explicitly
async function getUsers(limit?: number) {
  // Validate input
  if (limit !== undefined && (limit < 1 || limit > 1000)) {
    throw new Error('Limit must be between 1 and 1000');
  }

  // Handle undefined
  const safeLimit = limit ?? 50;

  // Prevent SQL injection with parameterized query
  const users = await db.query('SELECT * FROM users LIMIT $1', [safeLimit]);

  // Handle empty results
  return users.length > 0 ? users : [];
}
```

### How to Hold Testing in Your Head (TDD/BDD)

Hand the routine cases to the machine — roughly **70% happy-path tests drafted by AI** — and save your own attention for the edges.

**Test-Driven Development (TDD):**
```
1. Write failing test
2. Write minimal code to pass
3. Refactor
4. Repeat
```

**Behavior-Driven Development (BDD):**
```gherkin
Feature: User Registration
  Scenario: User registers with valid email
    Given I am on the registration page
    When I enter "test@example.com" as email
    And I enter "SecurePass123!" as password
    Then I should see "Registration successful"
    And I should receive a welcome email
```

### Seeing Inside a Running System

Wiring in instrumentation earns its keep — observability work returns a **100% median ROI, $500k average return**.

**Three questions to chase down a problem:**
1. **Is it slow?** → Read the metrics (response time, DB queries)
2. **Is it broken?** → Read the logs (errors, stack traces)
3. **Where is it broken?** → Follow the traces (distributed systems)

```typescript
// Good: Structured logging with context
logger.error('Payment processing failed', {
  orderId: order.id,
  userId: user.id,
  amount: order.total,
  error: error.message,
  stack: error.stack,
  timestamp: Date.now(),
  ipAddress: req.ip,
});
```

## Working With the Team

### Designing the Contract — Treat the API Like a Product

Someone on the other end depends on your API. Build it the way you'd build a product for them.

**What to hold to:**
1. **Versioning** — `/api/v1/users`, `/api/v2/users`
2. **Consistency** — endpoints that all behave the same way
3. **Documentation** — OpenAPI/Swagger
4. **Backward compatibility** — never yank the rug out from existing clients
5. **Clear error messages** — tell the caller how to fix what went wrong

```typescript
// Good: Consistent API design
GET    /api/v1/users         # List users
GET    /api/v1/users/:id     # Get user
POST   /api/v1/users         # Create user
PUT    /api/v1/users/:id     # Update user
DELETE /api/v1/users/:id     # Delete user

// Consistent error format
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "field": "email",
    "timestamp": "2025-01-09T12:00:00Z"
  }
}
```

### Talking Through Schema Decisions

The points where a schema discussion is won or lost:

- **Normalization vs Denormalization** — what you give up to gain speed
- **Indexing strategy** — your query patterns decide which indexes earn a place
- **Migration path** — evolving the schema while the lights stay on
- **Data types** — VARCHAR(255) vs TEXT, INT vs BIGINT
- **Constraints** — Foreign keys, unique constraints, check constraints

### Reviewing Code to Stop Bugs Early

A review is the cheapest spot on the whole pipeline to kill a defect. Go looking for:

- Holes an attacker walks through — SQL injection, XSS
- Speed traps — N+1 queries, a missing index
- Error paths — anything that can throw and isn't caught
- The corners — nulls, empty inputs, the min/max boundary
- Whether the next reader will follow it — names, a comment where the logic earns one
- Coverage — does the new code come with tests

**Constructive Feedback:** aim at the code and the fix, never at the author.
```
# Good review comment
"This could be vulnerable to SQL injection. Consider using parameterized queries:
`db.query('SELECT * FROM users WHERE id = $1', [userId])`"

# Bad review comment
"This is wrong. Fix it."
```

## Mindset Checklist

- [ ] Map the dependencies before you touch anything
- [ ] Name the trade-off you're making (CAP, performance vs maintainability)
- [ ] Assume failure and plan for it (circuit breakers, retries)
- [ ] Hold to SOLID principles
- [ ] Walk the edges (null, empty, boundaries)
- [ ] Let the test come first (TDD/BDD)
- [ ] Attach context to every log line (structured logging)
- [ ] Treat the API like a product (versioning, docs)
- [ ] Have a plan for how the schema will grow
- [ ] Leave reviews that point at the fix

## Resources

- **Domain-Driven Design:** https://martinfowler.com/bliki/DomainDrivenDesign.html
- **CAP Theorem:** https://en.wikipedia.org/wiki/CAP_theorem
- **SOLID Principles:** https://en.wikipedia.org/wiki/SOLID
- **Resilience Patterns:** https://docs.microsoft.com/en-us/azure/architecture/patterns/
