# Cloudflare D1 & KV

## D1 (SQLite Database)

### Setup
```bash
# Create database
wrangler d1 create my-database

# Add to wrangler.toml
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "YOUR_DATABASE_ID"

# Apply schema
wrangler d1 execute my-database --file=./schema.sql
```

### Usage

```typescript
// Query
const result = await env.DB.prepare(
  "SELECT * FROM users WHERE id = ?"
).bind(userId).first();

// Insert
await env.DB.prepare(
  "INSERT INTO users (name, email) VALUES (?, ?)"
).bind("Alice", "alice@example.com").run();

// Batch (atomic)
await env.DB.batch([
  env.DB.prepare("UPDATE accounts SET balance = balance - 100 WHERE id = ?").bind(user1),
  env.DB.prepare("UPDATE accounts SET balance = balance + 100 WHERE id = ?").bind(user2)
]);

// All results
const { results } = await env.DB.prepare("SELECT * FROM users").all();
```

### Features
- Reads replicate worldwide, so they stay fast
- One writer keeps consistency straightforward
- Plain SQLite syntax
- 25GB database size limit
- ACID transactions via batch

## KV (Key-Value Store)

### Setup
```bash
# Create namespace
wrangler kv:namespace create MY_KV

# Add to wrangler.toml
[[kv_namespaces]]
binding = "KV"
id = "YOUR_NAMESPACE_ID"
```

### Usage

```typescript
// Put with TTL
await env.KV.put("session:token", JSON.stringify(data), {
  expirationTtl: 3600,
  metadata: { userId: "123" }
});

// Get
const value = await env.KV.get("session:token");
const json = await env.KV.get("session:token", "json");
const buffer = await env.KV.get("session:token", "arrayBuffer");
const stream = await env.KV.get("session:token", "stream");

// Get with metadata
const { value, metadata } = await env.KV.getWithMetadata("session:token");

// Delete
await env.KV.delete("session:token");

// List
const list = await env.KV.list({ prefix: "user:" });
```

### Features
- Reads return in sub-milliseconds (edge-cached)
- Eventually consistent (~60 seconds globally)
- 25MB value size limit
- Entries expire on their own (TTL)

## Use Cases

### D1
- Relational data
- Multi-table queries with JOINs
- ACID transactions
- User accounts, orders, inventory

### KV
- Cache
- Sessions
- Feature flags
- Rate limiting
- Live counters

## Decision Matrix

| Need | Choose |
|------|--------|
| SQL queries | D1 |
| Sub-millisecond reads | KV |
| ACID transactions | D1 |
| Values over 25MB | R2 |
| Strong consistency | D1 (writes), Durable Objects |
| Expiry handled for you | KV |

## Resources

- D1: https://developers.cloudflare.com/d1/
- KV: https://developers.cloudflare.com/kv/
