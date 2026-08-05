# Backend Performance & Scalability

The workshop notes on making a backend fast and keeping it fast under load — where to spend effort on queries, caching, and scaling, and where it is wasted (2025).

## Database Performance

### Query Optimization

#### Indexing Strategies

The first place to look when reads are slow. An index turns a full scan into a targeted lookup — but it is not free, so place it deliberately.

**What it buys you:** 30% disk I/O reduction, 10-100x query speedup

```sql
-- Create index on frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Composite index for multi-column queries
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Partial index for filtered queries
CREATE INDEX idx_active_users ON users(email) WHERE active = true;

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM orders
WHERE user_id = 123 AND created_at > '2025-01-01';
```

**Index Types — pick by access pattern:**
- **B-tree** - The default; reach for it first. Handles equality and range queries.
- **Hash** - Equality lookups only, fast — no range support.
- **GIN** - Full-text search and JSONB queries.
- **GiST** - Geospatial queries and range types.

**Skip the index when:**
- The table is tiny (<1000 rows) — a scan is cheaper than the index.
- The column churns constantly — every write pays to maintain it.
- Cardinality is low (e.g., a boolean with 2 values) — the index barely narrows anything.

### Connection Pooling

Opening a database connection is expensive; a pool keeps a handful warm and hands them out. This is one of the cheapest wins available.

**What it buys you:** 5-10x performance improvement

```typescript
// PostgreSQL with pg-pool
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20, // Maximum connections
  min: 5, // Minimum connections
  idleTimeoutMillis: 30000, // Close idle connections after 30s
  connectionTimeoutMillis: 2000, // Error if can't connect in 2s
});

// Use pool for queries
const result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
```

**Sizing the pool:**
- **Web servers:** begin with `connections = (core_count * 2) + effective_spindle_count`
- **Rule of thumb:** 20-30 connections per app instance
- **Adjust by observation:** once it ships, watch whether the pool runs dry — treat that formula as a first guess, not a verdict

### N+1 Query Problem

The classic trap: one query to fetch a list, then one more query per row to fill in a relation. Looks innocent in a loop; murders throughput at scale.

**Bad: N+1 queries**
```typescript
// Fetches 1 query for posts, then N queries for authors
const posts = await Post.findAll();
for (const post of posts) {
  post.author = await User.findById(post.authorId); // N queries!
}
```

**Good: fold it into one query with a join or eager load**
```typescript
// Single query with JOIN
const posts = await Post.findAll({
  include: [{ model: User, as: 'author' }],
});
```

## Caching Strategies

### Redis Caching

The fastest query is the one you never send to the database. Redis sits in front of it and absorbs the repeated reads.

**What it buys you:** 90% DB load reduction, 10-100x faster response

#### Cache-Aside Pattern (Lazy Loading)

The app owns the cache: check it first, and only touch the database on a miss. Simple, and the default choice for most read paths.

```typescript
async function getUser(userId: string) {
  // Try cache first
  const cached = await redis.get(`user:${userId}`);
  if (cached) return JSON.parse(cached);

  // Cache miss - fetch from DB
  const user = await db.users.findById(userId);

  // Store in cache (TTL: 1 hour)
  await redis.setex(`user:${userId}`, 3600, JSON.stringify(user));

  return user;
}
```

#### Write-Through Pattern

Update the database and the cache in the same breath. Costs a little on every write, but the cache never serves a stale read.

```typescript
async function updateUser(userId: string, data: UpdateUserDto) {
  // Update database
  const user = await db.users.update(userId, data);

  // Update cache immediately
  await redis.setex(`user:${userId}`, 3600, JSON.stringify(user));

  return user;
}
```

#### Cache Invalidation

The hard part. When the underlying data changes, the stale entries have to go — including any derived caches that depend on it.

```typescript
// Invalidate on update
async function deleteUser(userId: string) {
  await db.users.delete(userId);
  await redis.del(`user:${userId}`);
  await redis.del(`user:${userId}:posts`); // Invalidate related caches
}

// Pattern-based invalidation
await redis.keys('user:*').then(keys => redis.del(...keys));
```

### Cache Layers

Think in layers — each one catches what the one above it missed, so the request travels as short a distance as possible:

```
Client
  → CDN Cache (static assets, cuts latency 50%+)
  → API Gateway Cache (public endpoints)
  → Application Cache (Redis)
  → Database Query Cache
  → Database
```

### Cache Best Practices

1. **Cache what gets read often** - user profiles, config, product catalogs
2. **Choose TTL deliberately** - it is the dial between freshness and speed
3. **Invalidate on write** - a consistent cache is the only kind worth keeping
4. **Name keys consistently** - the `resource:id:attribute` pattern reads well and invalidates cleanly
5. **Watch the hit rate** - aim for >80%; below that, the cache is barely earning its keep

## Load Balancing

### Algorithms

Three ways to spread traffic across servers — choose by what the workload needs.

**Round Robin** - even rotation across servers
```nginx
upstream backend {
    server backend1.example.com;
    server backend2.example.com;
    server backend3.example.com;
}
```

**Least Connections** - send the request to whichever server is least busy
```nginx
upstream backend {
    least_conn;
    server backend1.example.com;
    server backend2.example.com;
}
```

**IP Hash** - pin each client to one server (session affinity)
```nginx
upstream backend {
    ip_hash;
    server backend1.example.com;
    server backend2.example.com;
}
```

### Health Checks

A load balancer is only as good as its ability to tell live servers from dead ones. Give it an endpoint that reports the truth about dependencies, not just "the process is up".

```typescript
// Express health check endpoint
app.get('/health', async (req, res) => {
  const checks = {
    uptime: process.uptime(),
    timestamp: Date.now(),
    database: await checkDatabase(),
    redis: await checkRedis(),
    memory: process.memoryUsage(),
  };

  const isHealthy = checks.database && checks.redis;
  res.status(isHealthy ? 200 : 503).json(checks);
});
```

## Asynchronous Processing

### Offloading Slow Work to Message Queues

If a request triggers work that takes seconds, do not make the caller wait for it. Hand the job to a queue, return immediately, and let a worker process it out of band.

```typescript
// Producer - Add job to queue
import Queue from 'bull';

const emailQueue = new Queue('email', {
  redis: { host: 'localhost', port: 6379 },
});

await emailQueue.add('send-welcome', {
  userId: user.id,
  email: user.email,
});

// Consumer - Process jobs
emailQueue.process('send-welcome', async (job) => {
  await sendWelcomeEmail(job.data.email);
});
```

**Good candidates to push off the request path:**
- Email sending
- Image/video processing
- Report generation
- Data export
- Webhook delivery

## CDN (Content Delivery Network)

Serve bytes from a node near the user instead of from your origin halfway around the world. The closer the edge, the lower the latency.

**What it buys you:** 50%+ latency reduction for global users

### Configuration

```typescript
// Cache-Control headers
res.setHeader('Cache-Control', 'public, max-age=31536000, immutable'); // Static assets
res.setHeader('Cache-Control', 'public, max-age=3600'); // API responses
res.setHeader('Cache-Control', 'private, no-cache'); // User-specific data
```

**CDN Providers:**
- Cloudflare (free tier goes a long way, edge nodes everywhere)
- AWS CloudFront (plugs straight into the AWS stack)
- Fastly (purges the cache instantly)

## Horizontal vs Vertical Scaling

Two directions to grow, and the trade-off is real — name it out loud before committing.

### Horizontal Scaling (Scale Out)

Add more machines.

**In its favor:**
- Failure of one node does not take you down
- Headroom is effectively unlimited
- Runs on commodity hardware, so cost scales gently

**The cost:**
- Architecture gets more complicated
- Keeping data consistent across nodes is hard
- Network hops add overhead

**Reach for it when:** traffic is high, you need redundancy, and the application is stateless

### Vertical Scaling (Scale Up)

Make one machine bigger.

**In its favor:**
- Architecture stays simple
- Often needs no code changes at all
- Consistency is easy with a single node

**The cost:**
- Hardware tops out eventually
- That one box is a single point of failure
- The high end gets expensive fast

**Reach for it when:** the app is monolithic, you need to scale quickly, and strict data consistency matters most

## Database Scaling Patterns

### Read Replicas

When reads dwarf writes, copy the data to standby nodes and route reads there, leaving the primary free to handle writes.

```
Primary (Write) → Replica 1 (Read)
               → Replica 2 (Read)
               → Replica 3 (Read)
```

**Implementation:**
```typescript
// Write to primary
await primaryDb.users.create(userData);

// Read from replica
const users = await replicaDb.users.findAll();
```

**Where it pays off:**
- Read-heavy workloads (90%+ reads)
- Analytics queries
- Reporting dashboards

### Database Sharding

**Horizontal Partitioning** - when one database can no longer hold or serve all the data, split it across several, each owning a slice

```typescript
// Shard by user ID
function getShardId(userId: string): number {
  return hashCode(userId) % SHARD_COUNT;
}

const shardId = getShardId(userId);
const db = shards[shardId];
const user = await db.users.findById(userId);
```

**Ways to choose the slice — pick by how data is accessed:**
- **Range-based:** carve by ID band — Users 1-1M → Shard 1, 1M-2M → Shard 2
- **Hash-based:** scatter evenly with Hash(userId) % shard_count
- **Geographic:** keep data near its users — EU users → EU shard, US users → US shard
- **Entity-based:** split by table — Users → Shard 1, Orders → Shard 2

## Performance Monitoring

You cannot fix what you cannot see. Instrument before you optimize.

### Key Metrics

**Application:**
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Error rate
- CPU/memory usage

**Database:**
- Query execution time
- Connection pool saturation
- Cache hit rate
- Slow query log

**Tools:**
- Prometheus + Grafana (metrics)
- New Relic / Datadog (APM)
- Sentry (error tracking)
- OpenTelemetry (distributed tracing)

## Performance Optimization Checklist

### Database
- [ ] Hot columns carry an index
- [ ] A connection pool is in place
- [ ] No N+1 query patterns left
- [ ] Slow query log is being watched
- [ ] Execution plans have been read

### Caching
- [ ] Hot data lives in Redis
- [ ] TTLs chosen deliberately, not by default
- [ ] Writes invalidate their cache entries
- [ ] Static assets served from a CDN
- [ ] Hit rate sits above 80%

### Application
- [ ] Slow work pushed to async jobs
- [ ] Responses compressed (gzip)
- [ ] Traffic spread across a load balancer
- [ ] Health endpoint reports real status
- [ ] CPU and memory limits set

### Monitoring
- [ ] An APM tool is wired up (New Relic/Datadog)
- [ ] Errors land in tracking (Sentry)
- [ ] Dashboards render the metrics (Grafana)
- [ ] Alerts fire on the numbers that matter
- [ ] Distributed tracing covers the microservices

## Common Performance Pitfalls

The mistakes that show up again and again:

1. **No caching** - hammering the database for data that never changed
2. **Missing indexes** - paying for a full table scan on every lookup
3. **N+1 queries** - fetching relations one row at a time inside a loop
4. **Synchronous processing** - blocking the request on work that could run later
5. **No connection pooling** - building a fresh connection for every request
6. **Unbounded queries** - no LIMIT, so a big table can return everything at once
7. **No CDN** - shipping every static asset straight from the origin

## Resources

- **PostgreSQL Performance:** https://www.postgresql.org/docs/current/performance-tips.html
- **Redis Best Practices:** https://redis.io/docs/management/optimization/
- **Web Performance:** https://web.dev/performance/
- **Database Indexing:** https://use-the-index-luke.com/
