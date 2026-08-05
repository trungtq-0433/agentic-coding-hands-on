# Backend Debugging Playbook

A working reference for chasing down backend defects — the techniques, the tooling, and the habits that hold up under pressure (2025).

## How to Approach a Bug

### Debugging Is an Experiment, Not a Guess

1. **Observe** - Collect the symptoms and the raw data
2. **Hypothesize** - Propose a cause worth testing
3. **Test** - Prove or kill the hypothesis
4. **Iterate** - Sharpen the picture as you learn
5. **Fix** - Make the change
6. **Verify** - Confirm the change actually held

### Non-Negotiables

1. **Reproduce first** - No repro means you're guessing, not debugging
2. **Shrink the surface** - Strip away variables until one remains
3. **Read the logs** - The message is usually telling you something
4. **Question what you "know"** - "It should work" is a hypothesis, not a fact
5. **Move deliberately** - Random edits hide the real cause
6. **Write it down** - The next person to hit this is probably you

## Logging That Earns Its Keep

### Log in Structure, Not Prose

**Node.js (Pino - Fastest)**
```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: { colorize: true }
  }
});

// Structured logging with context
logger.info({ orderId: 'ORD-001', status: 'dispatched' }, 'Order dispatched');

// Error logging with stack trace
try {
  await dispatchOrder(orderId);
} catch (error) {
  logger.error({ err: error, orderId: 'ORD-001' }, 'Dispatch failed');
}
```

**Python (Structlog)**
```python
import structlog

logger = structlog.get_logger()

# Structured context
logger.info("order_dispatched", order_id="ORD-001", warehouse="SFO-1")

# Error with exception
try:
    dispatch_order(order_id)
except Exception as e:
    logger.error("dispatch_failed", order_id="ORD-001", exc_info=True)
```

**Go (Zap - High Performance)**
```go
import "go.uber.org/zap"

logger, _ := zap.NewProduction()
defer logger.Sync()

// Structured fields
logger.Info("order dispatched",
    zap.String("order_id", "ORD-001"),
    zap.String("warehouse", "SFO-1"),
)

// Error logging
if err := dispatchOrder(orderID); err != nil {
    logger.Error("dispatch failed",
        zap.Error(err),
        zap.String("order_id", "ORD-001"),
    )
}
```

### Picking the Right Level

| Level | Purpose | Example |
|-------|---------|---------|
| **TRACE** | Finest grain, dev machines only | Request/response bodies |
| **DEBUG** | The breadcrumbs you follow while debugging | SQL queries, cache hits |
| **INFO** | Routine "this happened" notes | User login, API calls |
| **WARN** | Something's off but nothing broke yet | Deprecated API usage |
| **ERROR** | An operation actually failed | Failed API calls, exceptions |
| **FATAL** | The kind of failure that takes you down | Database connection lost |

### Draw the Line

**✅ DO LOG:**
- Request/response metadata (leave bodies out in prod)
- Errors paired with enough context to act on them
- Timing and size numbers
- Security-relevant events (login, permission changes)
- Business milestones (orders, payments)

**❌ DON'T LOG:**
- Passwords or secrets
- Credit card numbers
- Personal identifiable information (PII)
- Session tokens
- Full request bodies in production

## Tooling, Language by Language

### Node.js / TypeScript

**1. Chrome DevTools (Built-in)**
```bash
# Run with inspect flag
node --inspect-brk app.js

# Open chrome://inspect in Chrome
# Set breakpoints, step through code
```

**2. VS Code Debugger**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Server",
      "skipFiles": ["<node_internals>/**"],
      "program": "${workspaceFolder}/src/index.ts",
      "preLaunchTask": "npm: build",
      "outFiles": ["${workspaceFolder}/dist/**/*.js"]
    }
  ]
}
```

**3. Debug Module**
```typescript
import debug from 'debug';

const log = debug('app:worker');
const error = debug('app:error');

log('Job queue worker started, concurrency=%d', 5);
error('Failed to connect to job queue');

// Run with: DEBUG=app:* node app.js
```

### Python

**1. PDB (Built-in Debugger)**
```python
import pdb

def calculate_discount(cart):
    # Set breakpoint — execution pauses here
    pdb.set_trace()

    # Debugger commands:
    # l - list code
    # n - next line
    # s - step into
    # c - continue
    # p variable - print variable
    # q - quit
    result = apply_rules(cart)
    return result
```

**2. IPython Debugger (Nicer Ergonomics)**
```python
from IPython import embed

def calculate_discount(cart):
    # Drop into a full IPython shell with tab-complete
    embed()

    result = apply_rules(cart)
    return result
```

**3. VS Code Debugger**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

### Go

**1. Delve (Standard Debugger)**
```bash
# Install
go install github.com/go-delve/delve/cmd/dlv@latest

# Debug
dlv debug main.go

# Commands:
# b main.main - set breakpoint
# c - continue
# n - next line
# s - step into
# p variable - print variable
# q - quit
```

**2. VS Code Debugger**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Package",
      "type": "go",
      "request": "launch",
      "mode": "debug",
      "program": "${workspaceFolder}"
    }
  ]
}
```

### Rust

**1. LLDB/GDB (Native Debuggers)**
```bash
# Build with debug info
cargo build

# Debug with LLDB
rust-lldb ./target/debug/myapp

# Debug with GDB
rust-gdb ./target/debug/myapp
```

**2. VS Code Debugger (CodeLLDB)**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug",
      "program": "${workspaceFolder}/target/debug/myapp",
      "args": [],
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

## Digging Into the Database

### Inspecting SQL Queries (PostgreSQL)

**1. EXPLAIN ANALYZE**
```sql
-- Show query execution plan and actual timings
EXPLAIN ANALYZE
SELECT p.title, COUNT(r.id) AS review_count, AVG(r.rating) AS avg_rating
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
WHERE p.published_at > '2024-01-01'
GROUP BY p.id, p.title
ORDER BY avg_rating DESC
LIMIT 10;

-- Look for:
-- - Seq Scan on large tables (missing indexes)
-- - High execution time
-- - Large row estimates
```

**2. Turn On Slow Query Logging**
```sql
-- PostgreSQL configuration
ALTER DATABASE shopdb SET log_min_duration_statement = 1000; -- Log queries >1s

-- Check slow queries
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**3. Watch What's Running Now**
```sql
-- See currently running queries
SELECT pid, now() - query_start AS duration, query, state
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Kill a long-running query
SELECT pg_terminate_backend(pid);
```

### MongoDB

**1. Explain a Query's Cost**
```javascript
db.products.find({ sku: 'GADGET-X1' }).explain('executionStats')

// Look for:
// - totalDocsExamined vs nReturned (should be close)
// - COLLSCAN (collection scan - needs index)
// - executionTimeMillis (should be low)
```

**2. Profile the Slow Ones**
```javascript
// Enable profiling for queries >100ms
db.setProfilingLevel(1, { slowms: 100 })

// View slow queries
db.system.profile.find().limit(5).sort({ ts: -1 }).pretty()

// Disable profiling
db.setProfilingLevel(0)
```

### Redis

**1. Watch Commands Live**
```bash
# See all commands in real-time
redis-cli MONITOR

# Check slow log
redis-cli SLOWLOG GET 10

# Set slow log threshold (microseconds)
redis-cli CONFIG SET slowlog-log-slower-than 10000
```

**2. Inspect Memory**
```bash
# Memory usage by key pattern
redis-cli --bigkeys

# Memory usage details
redis-cli INFO memory

# Analyze specific key
redis-cli MEMORY USAGE mykey
```

## Poking at the API

### Exercising HTTP Endpoints

**1. cURL Testing**
```bash
# Verbose output with headers
curl -v https://api.example.com/products

# Include response headers
curl -i https://api.example.com/products/GADGET-X1

# POST with JSON
curl -X POST https://api.example.com/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"GADGET-X1","priceInCents":4999}' \
  -v

# Save response to file
curl https://api.example.com/products -o response.json
```

**2. HTTPie (Friendlier Syntax)**
```bash
# Install
pip install httpie

# Simple GET
http GET https://api.example.com/products

# POST with JSON
http POST https://api.example.com/products sku=GADGET-X1 priceInCents:=4999

# Custom headers
http GET https://api.example.com/products Authorization:"Bearer token123"
```

**3. Middleware That Logs Requests**

**Express/Node.js:**
```typescript
import morgan from 'morgan';

// Development
app.use(morgan('dev'));

// Production (JSON format)
app.use(morgan('combined'));

// Custom format showing route + timing
app.use(morgan(':method :url :status :response-time ms :res[content-length]b'));
```

**FastAPI/Python:**
```python
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - started_at) * 1000

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(elapsed_ms, 2),
    )
    return response
```

## Chasing Performance Problems

### Profiling the CPU

**Node.js (0x)**
```bash
# Install
npm install -g 0x

# Profile application
0x node app.js

# Open flamegraph in browser
# Identify hot spots (red areas)
```

**Node.js (Clinic.js)**
```bash
# Install
npm install -g clinic

# CPU profiling
clinic doctor -- node app.js

# Heap profiling
clinic heapprofiler -- node app.js

# Event loop analysis
clinic bubbleprof -- node app.js
```

**Python (cProfile)**
```python
import cProfile
import pstats

# Profile a specific block of work
profiler = cProfile.Profile()
profiler.enable()

# The code under investigation
result = rebuild_search_index()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 costliest call paths
```

**Go (pprof)**
```go
import (
    "net/http"
    _ "net/http/pprof"
)

func main() {
    // Enable profiling endpoint
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()

    // Your application
    startServer()
}

// Profile CPU
// go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

// Profile heap
// go tool pprof http://localhost:6060/debug/pprof/heap
```

### Tracking Down Memory Issues

**Node.js (Heap Snapshots)**
```typescript
// Capture heap snapshot on demand for comparison
import { writeHeapSnapshot } from 'v8';

app.get('/debug/heap', (req, res) => {
    const filename = writeHeapSnapshot();
    res.send(`Snapshot written: ${filename}`);
});

// Workflow in Chrome DevTools:
// 1. Take snapshot before suspected leak
// 2. Trigger the leaking operation N times
// 3. Take second snapshot and compare — look for growing object counts
```

**Python (Memory Profiler)**
```python
from memory_profiler import profile

@profile
def build_catalog_index(product_ids: list[str]):
    # Tracks per-line allocation — spot the lines that balloon memory
    index = {pid: load_product(pid) for pid in product_ids}
    return index

# Run with: python -m memory_profiler script.py
# Prints line-by-line memory usage delta
```

## Debugging in Production

### Watching It Run — Application Performance Monitoring (APM)

**New Relic**
```typescript
// newrelic.js
export const config = {
  app_name: ['My Backend API'],
  license_key: process.env.NEW_RELIC_LICENSE_KEY,
  logging: { level: 'info' },
  distributed_tracing: { enabled: true },
};

// Import at app entry
import 'newrelic';
```

**DataDog**
```typescript
import tracer from 'dd-trace';

tracer.init({
  service: 'backend-api',
  env: process.env.NODE_ENV,
  version: '1.0.0',
  logInjection: true
});
```

**Sentry (Error Tracking)**
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});

// Capture errors with structured context
try {
  await fulfillOrder(orderId);
} catch (error) {
  Sentry.captureException(error, {
    tags: { operation: 'order-fulfillment' },
    extra: { orderId },
  });
}
```

### Tracing Across Services

**OpenTelemetry (Vendor-Agnostic)**
```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';

const sdk = new NodeSDK({
  traceExporter: new JaegerExporter({
    endpoint: 'http://localhost:14268/api/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

// Traces HTTP, database, Redis automatically
```

### Pulling Logs Together

**ELK Stack (Elasticsearch, Logstash, Kibana)**
```yaml
# docker-compose.yml
version: '3'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - 9200:9200

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - 5601:5601
```

**Loki + Grafana (Lightweight)**
```yaml
# promtail config for log shipping
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: backend-api
          __path__: /var/log/app/*.log
```

## Scenarios You'll Hit Again and Again

### 1. CPU Pinned at 100%

**Steps:**
1. Profile the CPU and read the flamegraph
2. Spot the functions soaking up time
3. Look closely for:
   - Loops that never terminate
   - Expensive regex work
   - Algorithms that scale badly (O(n²))
   - Synchronous work parked on the event loop (Node.js)

**Node.js Example:**
```typescript
// ❌ Bad: Blocking event loop — O(n²) nested scan on every request
function findDuplicateSkus(catalog: string[]) {
  const duplicates: string[] = [];
  for (let i = 0; i < catalog.length; i++) {
    for (let j = i + 1; j < catalog.length; j++) {
      if (catalog[i] === catalog[j]) duplicates.push(catalog[i]);
    }
  }
  return duplicates;
}

// ✅ Good: O(n) single pass with a Set
function findDuplicateSkus(catalog: string[]) {
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  for (const sku of catalog) {
    if (seen.has(sku)) duplicates.add(sku);
    else seen.add(sku);
  }
  return [...duplicates];
}
```

### 2. Memory Leaks

**Symptoms:**
- The footprint keeps climbing and never settles
- The process eventually gets killed (OOM)
- Things slow down before they crash

**Where they usually come from:**
```typescript
// ❌ Memory leak: Event listeners not removed
class InventoryMonitor {
  constructor(eventBus) {
    eventBus.on('stock-update', (update) => this.handleUpdate(update));
    // Listener never removed — holds reference to InventoryMonitor forever
  }
}

// ✅ Fix: Remove listeners on teardown
class InventoryMonitor {
  constructor(eventBus) {
    this.eventBus = eventBus;
    this.handler = (update) => this.handleUpdate(update);
    eventBus.on('stock-update', this.handler);
  }

  destroy() {
    this.eventBus.off('stock-update', this.handler);
  }
}

// ❌ Memory leak: Global accumulator without a bound
const priceHistory = new Map();
function recordPrice(sku: string, price: number) {
  priceHistory.set(sku, price); // Grows without limit across restarts
}

// ✅ Fix: LRU cache with size and TTL limit
import LRU from 'lru-cache';
const priceHistory = new LRU({ max: 5000, ttl: 1000 * 60 * 30 }); // 30-min TTL
```

**How to catch it:**
```bash
# Node.js: Check heap size over time
node --expose-gc --max-old-space-size=4096 app.js

# Take periodic heap snapshots
# Compare snapshots in Chrome DevTools
```

### 3. Sluggish Database Queries

**Steps:**
1. Switch on the slow query log
2. Read the plan with EXPLAIN
3. Add the index the planner is missing
4. Reshape the query if needed

**PostgreSQL Example:**
```sql
-- Before: Slow full table scan
SELECT * FROM order_items
WHERE product_id = 456
ORDER BY purchased_at DESC
LIMIT 20;

-- EXPLAIN shows: Seq Scan on order_items (cost=0.00..98432.00 rows=12 ...)

-- Fix: Add composite index matching the query shape
CREATE INDEX idx_order_items_product_purchased
ON order_items(product_id, purchased_at DESC);

-- After: Index Scan using idx_order_items_product_purchased
-- 50–100x faster for large tables
```

### 4. Connection Pool Runs Dry

**Symptoms:**
- "Connection pool exhausted" errors
- Requests that hang and never return
- The database sitting at its connection ceiling

**Why it happens, and how to fix it:**
```typescript
// ❌ Bad: Connection leak — no release on error path
async function getProduct(sku: string) {
  const client = await pool.connect();
  const result = await client.query(
    'SELECT * FROM products WHERE sku = $1', [sku]
  );
  return result.rows[0];
  // If the query throws, client is never returned to the pool!
}

// ✅ Good: Always release in finally
async function getProduct(sku: string) {
  const client = await pool.connect();
  try {
    const result = await client.query(
      'SELECT * FROM products WHERE sku = $1', [sku]
    );
    return result.rows[0];
  } finally {
    client.release(); // Always runs — even on error
  }
}

// ✅ Better: Let the pool manage the lifecycle
async function getProduct(sku: string) {
  const result = await pool.query(
    'SELECT * FROM products WHERE sku = $1', [sku]
  );
  return result.rows[0]; // Pool automatically reclaims the connection
}
```

### 5. Race Conditions

**Example:**
```typescript
// ❌ Bad: Race condition — two concurrent reservations both see qty=1
let availableQty = 1;

async function reserveStock(sku: string) {
  const qty = availableQty;    // Worker A reads 1
  await notifyWarehouse(sku);  // Worker B also reads 1 during await
  availableQty = qty - 1;      // Both write 0 — one reservation is silent-lost
}

// ✅ Fix: Atomic decrement (Redis)
async function reserveStock(sku: string) {
  const remaining = await redis.decr(`stock:${sku}`);
  if (remaining < 0) {
    await redis.incr(`stock:${sku}`); // roll back
    throw new Error('Out of stock');
  }
  return remaining;
}

// ✅ Fix: Pessimistic lock via database transaction
async function reserveStock(sku: string, qty: number) {
  await db.transaction(async (trx) => {
    const item = await trx('inventory')
      .where({ sku })
      .forUpdate() // Row-level lock — serializes concurrent reservations
      .first();

    if (item.stock_count < qty) throw new Error('Insufficient stock');

    await trx('inventory')
      .where({ sku })
      .update({ stock_count: item.stock_count - qty });
  });
}
```

## Working Checklist

**Before you touch the code:**
- [ ] Read the error message to the end
- [ ] Pull context from the logs
- [ ] Get a reliable reproduction
- [ ] Narrow the failure down by bisecting
- [ ] Confirm the assumptions you're carrying

**While investigating:**
- [ ] Turn on debug-level logging
- [ ] Drop log points where they'll tell you something
- [ ] Set breakpoints and step through
- [ ] Profile when it's slow
- [ ] Look at the queries hitting the database
- [ ] Keep an eye on system resources

**For production incidents:**
- [ ] Open the APM dashboards
- [ ] Walk the distributed traces
- [ ] Look at how error rates moved
- [ ] Line it up against the normal baseline
- [ ] Check whether anything just shipped
- [ ] Account for infrastructure changes

**Once you've fixed it:**
- [ ] Confirm the fix locally
- [ ] Lock it in with a regression test
- [ ] Write down what happened
- [ ] Ship it with monitoring on
- [ ] Confirm it holds in production

## Further Reading

**Tools:**
- Node.js: https://nodejs.org/en/docs/guides/debugging-getting-started/
- Chrome DevTools: https://developer.chrome.com/docs/devtools/
- Clinic.js: https://clinicjs.org/
- Sentry: https://docs.sentry.io/
- DataDog: https://docs.datadoghq.com/
- New Relic: https://docs.newrelic.com/

**Guides worth keeping handy:**
- 12 Factor App Logs: https://12factor.net/logs
- Google SRE Book: https://sre.google/sre-book/table-of-contents/
- OpenTelemetry: https://opentelemetry.io/docs/

**Database references:**
- PostgreSQL EXPLAIN: https://www.postgresql.org/docs/current/using-explain.html
- MongoDB Performance: https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/
