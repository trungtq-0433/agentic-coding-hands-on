# Backend Technologies

The toolbox for building a modern backend — languages, frameworks, databases, and queues — with notes on where each one earns its place (2025).

## Programming Languages

### Node.js/TypeScript
**Where it stands:** TypeScript has become the default for Node.js backends — the industry standard.

**Plays to its strengths with:**
- Teams running JavaScript end to end
- Real-time applications (WebSockets, Socket.io)
- Quick prototyping on the npm ecosystem (2M+ packages)
- Event-driven architectures

**Popular Frameworks:**
- **NestJS** - structured and modular, TypeScript from the ground up, built for larger teams
- **Express** - thin, bends to whatever you need, and still the crowd favorite (23M weekly downloads)
- **Fastify** - built for speed (20k req/sec vs Express 15k req/sec)
- **tRPC** - types that flow end to end, no GraphQL layer required

**Pick it when:** the team already lives in JavaScript/TypeScript, real-time features are on the table, and shipping fast is the priority.

### Python
**Where it stands:** FastAPI adoption surge - 73% migrating from Flask

**Plays to its strengths with:**
- Data-heavy applications
- ML/AI integration (TensorFlow, PyTorch)
- Scientific computing
- Scripting and automation

**Popular Frameworks:**
- **FastAPI** - async-first and current, spins up OpenAPI docs on its own, leans on Pydantic to validate
- **Django** - everything in the box: ORM, admin panel, authentication
- **Flask** - small and pliable, a natural fit for microservices

**Pick it when:** you are wiring in data science or ML/AI, prototyping quickly, or the team's depth is in Python.

### Go
**Where it stands:** the go-to for microservices at scale (Docker and Kubernetes are themselves written in Go)

**Plays to its strengths with:**
- High-concurrency systems (goroutines)
- Microservices architectures
- CLI tools and DevOps tooling
- System programming

**Popular Frameworks:**
- **Gin** - a quick HTTP router (40x faster than Martini)
- **Echo** - fast on its feet and easy to extend
- **Fiber** - an Express-shaped API riding on Fasthttp

**Pick it when:** you are building microservices, need heavy concurrency, are writing DevOps tooling, or want a single-binary deploy.

### Rust
**Where it stands:** 72% most admired language, 1.5x faster than Go

**Plays to its strengths with:**
- Performance-critical systems
- Memory-safe system programming
- High-reliability requirements
- WebAssembly backends

**Popular Frameworks:**
- **Axum** - comfortable to write, composable, sitting on tokio
- **Actix-web** - the speed king (benchmark leader)
- **Rocket** - type-safe and friendly to pick up

**Pick it when:** you need every last bit of performance, memory safety is non-negotiable, or you want low-level control.

## Databases

### Relational (SQL)

#### PostgreSQL
**Where it stands:** the default SQL choice for new projects

**What it gives you:**
- ACID guarantees that keep your data honest
- JSON/JSONB columns when you want SQL and NoSQL in one place
- Full-text search and geospatial work via PostGIS
- A deep index toolbox (B-tree, Hash, GiST, GIN)
- Window functions, CTEs, materialized views

**Where it fits:**
- Online stores where transactions cannot drop
- Anything handling money
- Reporting that asks hard questions of the data
- Multi-tenant applications

**Pick it when:** you need ACID guarantees, lean on complex queries and joins, or data integrity cannot bend.

### NoSQL

#### MongoDB
**Where it stands:** the leading document database

**What it gives you:**
- Schemas that bend as your model shifts
- Scale-out built in through sharding
- A muscular aggregation pipeline for shaping data
- GridFS for stashing large files

**Where it fits:**
- Content management systems
- Analytics that run in real time
- IoT data collection
- Catalogs where every item has its own shape

**Pick it when:** the schema keeps shifting, you iterate fast, or you need to scale out horizontally.

### Caching & In-Memory

#### Redis
**Where it stands:** the industry standard for caching and session storage

**What it gives you:**
- A key-value store that lives entirely in memory
- Pub/sub messaging
- Sorted sets for leaderboards
- Geospatial indexes
- Streams for event sourcing

**Performance:** 10-100x faster than disk-based databases

**Where it fits:**
- Holding sessions
- Rate limiting
- Leaderboards that update live
- Job queues (Bull, BullMQ)
- A caching layer (90% DB load reduction)

**Pick it when:** you need sub-millisecond latency, a caching layer, or somewhere to keep sessions.

## ORMs & Database Tools

### Modern ORMs (2025)

**Drizzle ORM** (TypeScript)
- Out front in the NestJS performance race
- 7.4kb, zero dependencies
- Reads almost like raw SQL, fully typed
- Reach for it when: performance is the bottleneck in a TypeScript app

**Prisma** (TypeScript)
- Hands you a typed client it generates for you
- Migrations come in the box
- A genuine pleasure to use, Prisma Studio included
- Reach for it when: you want to move fast with type safety along for the ride

**TypeORM** (TypeScript)
- Battle-tested and complete in features
- Does both Active Record and Data Mapper
- Reach for it when: the app is a complex enterprise system

**SQLAlchemy** (Python)
- The ORM every Python shop reaches for
- A query builder with real reach
- Reach for it when: you are on a Python backend

## Message Queues & Event Streaming

### RabbitMQ
**Its lane:** task queues and request/reply patterns

**What it gives you:**
- Routing you can shape any way you like (direct, topic, fanout, headers)
- Acknowledged, durable messages
- Dead letter exchanges for the ones that fail
- A broad protocol spread (AMQP, MQTT, STOMP)

**Where it fits:**
- Chewing through background jobs
- Talk between microservices
- Email/notification queues

**Pick it when:** you want a classic message broker, need rich routing, and throughput is moderate.

### Apache Kafka
**Its lane:** event streaming at millions of messages per second

**What it gives you:**
- Spread across nodes and tolerant of faults
- Throughput in the millions msg/sec
- Replay of past messages, bounded by retention
- Stream processing through Kafka Streams

**Where it fits:**
- Analytics that run in real time
- Event sourcing
- Log aggregation
- Netflix/Uber scale (billions events/day)

**Pick it when:** you are streaming events, throughput is enormous, you need replay, or analytics run in real time.

## Framework Comparisons

### Node.js Frameworks

| Framework | Performance | Learning Curve | Use Case |
|-----------|------------|----------------|----------|
| Express | Moderate | Easy | Learning, quick prototypes |
| NestJS | Moderate | Steep | Large team codebases |
| Fastify | High | Moderate | When latency matters most |
| tRPC | High | Moderate | One TypeScript stack top to bottom |

### Python Frameworks

| Framework | Performance | Features | Use Case |
|-----------|------------|----------|----------|
| FastAPI | High | Modern, async | Fresh builds, API services |
| Django | Moderate | Batteries-included | Apps that need everything bundled |
| Flask | Moderate | Minimal | Microservices, lean APIs |

## Technology Selection Flowchart

When the choice is not obvious, walk the questions in order and let the first clear "yes" decide.

```
Start → Need real-time features?
       → Yes → Node.js + Socket.io
       → No → Need ML/AI integration?
              → Yes → Python + FastAPI
              → No → Need maximum performance?
                     → Yes → Rust + Axum
                     → No → Need high concurrency?
                            → Yes → Go + Gin
                            → No → Node.js + NestJS (safe default)

Database Selection:
ACID needed? → Yes → PostgreSQL
            → No → Flexible schema? → Yes → MongoDB
                                   → No → PostgreSQL (default)

Caching needed? → Always use Redis

Message Queue:
Millions msg/sec? → Yes → Kafka
                 → No → RabbitMQ
```

## Common Pitfalls

The wrong turns that cost the most later:

1. **Putting relational data in NoSQL** - the moment the data shows clear relationships, reach for PostgreSQL
2. **Leaving connection pooling off** - a pool hands you a 5-10x performance boost, so don't walk past it
3. **Running without indexes** - index the columns you hit again and again (30% I/O reduction)
4. **Breaking into microservices on day one** - begin as a monolith and split only once the pain is real
5. **Skipping the cache entirely** - Redis caching cuts DB load by 90%

## Resources

- **NestJS:** https://nestjs.com
- **FastAPI:** https://fastapi.tiangolo.com
- **PostgreSQL:** https://www.postgresql.org/docs/
- **MongoDB:** https://www.mongodb.com/docs/
- **Redis:** https://redis.io/docs/
- **Kafka:** https://kafka.apache.org/documentation/
