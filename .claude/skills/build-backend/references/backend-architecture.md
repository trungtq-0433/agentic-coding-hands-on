# Backend Architecture Patterns

Field notes on microservices, event-driven design, and scaling — what each pattern buys you and what it costs (2025).

## Monolith vs Microservices

### Monolithic Architecture

```
┌─────────────────────────────────┐
│      Single Application         │
│                                 │
│  ┌─────────┐  ┌──────────┐    │
│  │  Users  │  │ Products │    │
│  └─────────┘  └──────────┘    │
│  ┌─────────┐  ┌──────────┐    │
│  │ Orders  │  │ Payments │    │
│  └─────────┘  └──────────┘    │
│                                 │
│     Single Database             │
└─────────────────────────────────┘
```

**What you gain:**
- One thing to build, one thing to ship
- Tests run locally without orchestration
- A single codebase to reason about
- Strong consistency for free (ACID transactions)

**What it costs:**
- Everything is wired to everything (tight coupling)
- You scale the whole app or none of it
- Every deploy is all-or-nothing
- Hard to swap parts of the tech stack later

**Reach for it when:** you're early — startups, MVPs, small teams, or domains whose boundaries aren't clear yet

### Microservices Architecture

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  User    │   │ Product  │   │  Order   │   │ Payment  │
│ Service  │   │ Service  │   │ Service  │   │ Service  │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
  ┌──▼──┐        ┌──▼──┐        ┌──▼──┐        ┌──▼──┐
  │  DB │        │  DB │        │  DB │        │  DB │
  └─────┘        └─────┘        └─────┘        └─────┘
```

**What you gain:**
- Ship one service without touching the rest
- Each service picks its own tech
- A failure stays contained where it started
- Scale the hot services, leave the rest alone

**What it costs:**
- Deployment becomes a moving target
- You inherit every distributed-systems headache — network latency, partial failures
- Consistency goes eventual, not immediate
- More moving parts to operate and watch

**Reach for it when:** you have large teams, domains with crisp boundaries, real need to scale services apart, or a deliberate tech mix

## Microservices Patterns

### Database per Service Pattern

**The idea:** every service keeps its own database; nobody reaches into anybody else's

```
User Service → User DB (PostgreSQL)
Product Service → Product DB (MongoDB)
Order Service → Order DB (PostgreSQL)
```

**Why it pays off:**
- Services stay independent
- Each one picks the database that fits its job
- Failures stay isolated

**What you trade away:**
- No joins reaching across services
- Transactions span the network now
- Data gets duplicated across stores

### API Gateway Pattern

```
Client
  │
  ▼
┌─────────────────┐
│  API Gateway    │  - Authentication
│  (Kong/NGINX)   │  - Rate limiting
└────────┬────────┘  - Request routing
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
  User    Product   Order   Payment
 Service  Service  Service  Service
```

**What the gateway handles:**
- Routing requests to the right service
- Authentication and authorization at the edge
- Rate limiting
- Reshaping requests and responses
- Caching

**Implementation (Kong):**
```yaml
services:
  - name: user-service
    url: http://user-service:3000
    routes:
      - name: user-route
        paths:
          - /api/users

  - name: product-service
    url: http://product-service:3001
    routes:
      - name: product-route
        paths:
          - /api/products

plugins:
  - name: rate-limiting
    config:
      minute: 100
  - name: jwt
```

### Service Discovery

**The idea:** instances come and go, so services look each other up at runtime rather than hardcoding addresses

```typescript
// Consul service discovery
import Consul from 'consul';

const consul = new Consul();

// Register service
await consul.agent.service.register({
  name: 'user-service',
  address: '192.168.1.10',
  port: 3000,
  check: {
    http: 'http://192.168.1.10:3000/health',
    interval: '10s',
  },
});

// Discover service
const services = await consul.catalog.service.nodes('product-service');
const productServiceUrl = `http://${services[0].ServiceAddress}:${services[0].ServicePort}`;
```

### Circuit Breaker Pattern

**The idea:** once a downstream service starts failing, stop hammering it — that's how you keep one failure from toppling the whole chain

```typescript
import CircuitBreaker from 'opossum';

const breaker = new CircuitBreaker(callExternalService, {
  timeout: 3000, // 3s timeout
  errorThresholdPercentage: 50, // Open circuit after 50% failures
  resetTimeout: 30000, // Try again after 30s
});

breaker.on('open', () => {
  console.log('Circuit breaker opened!');
});

breaker.fallback(() => ({
  data: 'fallback-response',
  source: 'cache',
}));

const result = await breaker.fire(requestParams);
```

**The three states:**
- **Closed:** all is well — requests pass straight through
- **Open:** failures crossed the threshold, so requests fail fast without even trying
- **Half-Open:** a few probes go through to check whether the service has come back

### Saga Pattern (Coordinating Transactions Across Services)

**Choreography-Based Saga:**
```
Order Service: Create Order → Publish "OrderCreated"
                                    ↓
Payment Service: Reserve Payment → Publish "PaymentReserved"
                                    ↓
Inventory Service: Reserve Stock → Publish "StockReserved"
                                    ↓
Shipping Service: Create Shipment → Publish "ShipmentCreated"

If any step fails → Compensating transactions (rollback)
```

**Orchestration-Based Saga:**
```
Saga Orchestrator
    ↓ Create Order
Order Service
    ↓ Reserve Payment
Payment Service
    ↓ Reserve Stock
Inventory Service
    ↓ Create Shipment
Shipping Service
```

## Event-Driven Architecture

**Worth noting:** 85% of organizations report real business value from going event-driven

### Event Sourcing

**The idea:** record the stream of events that happened, not just the latest snapshot of state

```typescript
// Traditional: Store current state
{
  userId: '123',
  balance: 500
}

// Event Sourcing: Store events
[
  { type: 'AccountCreated', userId: '123', timestamp: '...' },
  { type: 'MoneyDeposited', amount: 1000, timestamp: '...' },
  { type: 'MoneyWithdrawn', amount: 500, timestamp: '...' },
]

// Reconstruct state by replaying events
const balance = events
  .filter(e => e.userId === '123')
  .reduce((acc, event) => {
    if (event.type === 'MoneyDeposited') return acc + event.amount;
    if (event.type === 'MoneyWithdrawn') return acc - event.amount;
    return acc;
  }, 0);
```

**Why it pays off:**
- A full audit trail falls out for free
- Ask what the state was at any moment, not just now
- Replay the event log to reproduce a bug
- Build whatever projection a reader needs

### Message Broker Patterns

**Kafka (Event Streaming):**
```typescript
import { Kafka } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'order-service',
  brokers: ['kafka:9092'],
});

// Producer
const producer = kafka.producer();
await producer.send({
  topic: 'order-events',
  messages: [
    {
      key: order.id,
      value: JSON.stringify({
        type: 'OrderCreated',
        orderId: order.id,
        userId: order.userId,
        total: order.total,
      }),
    },
  ],
});

// Consumer
const consumer = kafka.consumer({ groupId: 'inventory-service' });
await consumer.subscribe({ topic: 'order-events' });
await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const event = JSON.parse(message.value.toString());
    if (event.type === 'OrderCreated') {
      await reserveInventory(event.orderId);
    }
  },
});
```

**RabbitMQ (Task Queues):**
```typescript
import amqp from 'amqplib';

const connection = await amqp.connect('amqp://localhost');
const channel = await connection.createChannel();

// Producer
await channel.assertQueue('email-queue', { durable: true });
channel.sendToQueue('email-queue', Buffer.from(JSON.stringify({
  to: user.email,
  subject: 'Welcome!',
  body: 'Thank you for signing up',
})));

// Consumer
await channel.consume('email-queue', async (msg) => {
  const emailData = JSON.parse(msg.content.toString());
  await sendEmail(emailData);
  channel.ack(msg);
});
```

## CQRS (Command Query Responsibility Segregation)

**The idea:** split the write path from the read path — the model that mutates data and the model that serves queries don't have to be the same

```
Write Side (Commands):           Read Side (Queries):
CreateOrder                      GetOrderById
UpdateOrder                      GetUserOrders
  ↓                                ↑
┌─────────┐                    ┌─────────┐
│ Write   │ → Events →         │  Read   │
│  DB     │    (sync)          │  DB     │
│(Postgres)                    │(MongoDB)│
└─────────┘                    └─────────┘
```

**Why it pays off:**
- Read models shaped purely for fast queries
- Reads scale on their own, apart from writes
- Free to back reads and writes with different databases

**Implementation:**
```typescript
// Command (Write)
class CreateOrderCommand {
  constructor(public userId: string, public items: OrderItem[]) {}
}

class CreateOrderHandler {
  async execute(command: CreateOrderCommand) {
    const order = await Order.create(command);
    await eventBus.publish(new OrderCreatedEvent(order));
    return order.id;
  }
}

// Query (Read)
class GetOrderQuery {
  constructor(public orderId: string) {}
}

class GetOrderHandler {
  async execute(query: GetOrderQuery) {
    // Read from optimized read model
    return await OrderReadModel.findById(query.orderId);
  }
}
```

## Scalability Patterns

### Horizontal Scaling (Scale Out)

```
Load Balancer
    ↓
┌───┴───┬───────┬───────┐
│ App 1 │ App 2 │ App 3 │ ... App N
└───┬───┴───┬───┴───┬───┘
    └───────┴───────┘
         ↓
    Shared Database
    (with read replicas)
```

### Database Sharding

Split one big dataset across many databases so no single node carries it all.

**Range-Based Sharding:**
```
Users 1-1M     → Shard 1
Users 1M-2M    → Shard 2
Users 2M-3M    → Shard 3
```

**Hash-Based Sharding:**
```typescript
function getShardId(userId: string): number {
  const hash = crypto.createHash('md5').update(userId).digest('hex');
  return parseInt(hash.substring(0, 8), 16) % SHARD_COUNT;
}

const shardId = getShardId(userId);
const db = shards[shardId];
const user = await db.users.findById(userId);
```

### Caching Layers

```
Client
  → CDN (static assets)
  → API Gateway Cache (public endpoints)
  → Application Cache (Redis - user sessions, hot data)
  → Database Query Cache
  → Database
```

## Architecture Decision Matrix

| Pattern | When to Use | Complexity | Benefits |
|---------|-------------|------------|----------|
| **Monolith** | Small team, MVP, boundaries still fuzzy | Low | Quick to build, easy to reason about |
| **Microservices** | Large team, sharp domains, scale-apart needs | High | Deploy in isolation, failures stay contained |
| **Event-Driven** | Async flows, you need the audit trail | Moderate | Loose coupling, room to scale |
| **CQRS** | Reads and writes pull in different directions | High | Queries tuned hard, reads scale alone |
| **Serverless** | Bursty traffic, work triggered by events | Low | Scales itself, you pay per call |

## Anti-Patterns to Avoid

1. **Distributed Monolith** — split into services that still can't deploy without each other; you paid the cost and kept the coupling
2. **Chatty Services** — chains of inter-service calls that drown in network overhead
3. **Shared Database** — services reaching into one common DB, coupling them right back together
4. **Over-Engineering** — microservices bolted onto an app that a monolith would serve fine
5. **No Circuit Breakers** — nothing to stop one failure cascading through the system

## Architecture Checklist

- [ ] Boundaries follow the domain, not the org chart (DDD)
- [ ] Each service owns its own database — nothing borrowed
- [ ] Client traffic enters through an API Gateway
- [ ] Services find each other via discovery
- [ ] Circuit breakers wrap the calls that can fail
- [ ] Services talk asynchronously over an event backbone (Kafka/RabbitMQ)
- [ ] CQRS applied where reads vastly outnumber writes
- [ ] Distributed tracing is collecting spans (Jaeger/OpenTelemetry)
- [ ] Every service exposes a health check
- [ ] Designed to grow by adding nodes

## Resources

- **Microservices Patterns:** https://microservices.io/patterns/
- **Martin Fowler - Microservices:** https://martinfowler.com/articles/microservices.html
- **Event-Driven Architecture:** https://aws.amazon.com/event-driven-architecture/
- **CQRS Pattern:** https://martinfowler.com/bliki/CQRS.html
