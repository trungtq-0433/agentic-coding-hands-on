---
name: tkm:build-backend
description: Build reliable backends — Node.js, Python, Go (NestJS, FastAPI, Django). REST/GraphQL/gRPC APIs, auth (OAuth, JWT), databases, microservices, OWASP security, Docker/K8s.
license: MIT
argument-hint: "[framework] [task]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: backend-database
triggers: ["API", "backend", "REST endpoint", "GraphQL", "NestJS", "FastAPI", "Django", "auth backend", "microservice"]
---

# Forging the Structure

Nobody who lives in a house ever sees the beams that hold it up.
Backends are the same: the contracts between services, the gate that checks who you are, the way a query is shaped — none of it is visible, yet everything visible leans on it.
This is quiet work. You measure it by what never breaks, not by what gets noticed.

## Reach for this when you are

- Shaping a REST, GraphQL, or gRPC interface
- Standing up the machinery that proves and grants identity
- Tuning how schemas are laid out and how queries hit them
- Putting caching and other speed work in place
- Closing the gaps the OWASP Top 10 warns about
- Splitting a system into services that scale on their own
- Deciding how to test — unit, integration, end-to-end
- Wiring the pipeline that builds, ships, and rolls back
- Watching production and chasing down what misbehaves

## Picking your materials

**Languages:** Node.js/TypeScript when one team owns front and back; Python when data or ML sits in the loop; Go when concurrency is the point; Rust when nothing slower will do
**Frameworks worth reaching for:** NestJS, FastAPI, Django, Express, Gin
**Databases:** PostgreSQL for ACID guarantees, MongoDB when the schema must bend, Redis for the cache layer
**APIs:** REST to keep it plain, GraphQL to hand clients the shape they want, gRPC when the wire speed matters

See `references/backend-technologies.md` for the side-by-side breakdown.

## Where each reference lives

**The raw stack:**
- `backend-technologies.md` — languages, frameworks, databases, message queues, ORMs
- `backend-api-design.md` — how REST, GraphQL, and gRPC are best laid out

**Guarding the door:**
- `backend-security.md` — OWASP Top 10 2025, hardening habits, input validation
- `backend-authentication.md` — OAuth 2.1, JWT, RBAC, MFA, session handling

**Speed and shape:**
- `backend-performance.md` — caching, query tuning, load balancing, scaling
- `backend-architecture.md` — microservices, event-driven, CQRS, saga patterns

**Keeping it honest in production:**
- `backend-testing.md` — what to test, with which tools, and how in CI/CD
- `backend-code-quality.md` — SOLID, design patterns, code that reads clean
- `backend-devops.md` — Docker, Kubernetes, release strategies, monitoring
- `backend-debugging.md` — tracing, profiling, logging, fault-finding under live traffic
- `backend-mindset.md` — how to think through problems, design, and work with others

## What the field has settled on (2025)

**Security:** hash with Argon2id, bind every query's parameters (cuts SQL injection by ~98%), run OAuth 2.1 with PKCE, throttle with rate limits, set your security headers.

**Performance:** Redis in front of the database (sheds ~90% of its load), indexes that match your reads (~30% less I/O), a CDN at the edge (50%+ off latency), and pooled connections so you stop paying handshake cost.

**Testing:** keep the 70-20-10 shape (unit, integration, E2E), reach for Vitest (~50% quicker than Jest), add contract tests where services meet — and remember ~83% of migrations bite back when they ship untested.

**DevOps:** roll out blue-green or canary, hide risk behind feature flags (~90% fewer bad releases), expect Kubernetes (~84% of teams run it), watch with Prometheus/Grafana, and trace with OpenTelemetry.

## Quick Decision Matrix

| Need | Choose |
|------|--------|
| Fast development | Node.js + NestJS |
| Data/ML integration | Python + FastAPI |
| High concurrency | Go + Gin |
| Max performance | Rust + Axum |
| ACID transactions | PostgreSQL |
| Flexible schema | MongoDB |
| Caching | Redis |
| Internal services | gRPC |
| Public APIs | GraphQL/REST |
| Real-time events | Kafka |

## The order of work

**API:** pick the style → draw the schema → validate what comes in → put auth in front → throttle the traffic → write the docs → handle the errors

**Database:** pick the engine → draw the schema → lay the indexes → pool the connections → settle a migration path → prove backup/restore → measure under load

**Security:** walk the OWASP Top 10 → bind your queries → OAuth 2.1 + JWT → set security headers → rate-limit → validate input → Argon2id for passwords

**Testing:** unit 70% → integration 20% → E2E 10% → load tests → migration tests → contract tests where services meet

**Deployment:** Docker → CI/CD → blue-green/canary → feature flags → monitoring → logging → health checks

## Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OAuth 2.1: https://oauth.net/2.1/
- OpenTelemetry: https://opentelemetry.io/
