# Cloudflare Platform Overview

The Cloudflare Developer Platform is a full edge-computing stack for building entire applications on a network that spans 300+ cities.

## Core Concepts

### Edge Computing Model

**Global Network:**
- Your code lives on machines in 300+ cities worldwide
- Each request is served from the closest location to the caller
- Latency stays tiny (<50ms typical)
- Failover and redundancy come built in

**V8 Isolates:**
- Slim execution sandboxes that spin up quicker than containers
- Cold starts measured in milliseconds
- Nothing to provision or babysit
- Scales itself
- You pay per request, not per idle server

### Key Components

**Workers** - Serverless compute that runs at the edge
- Handlers for HTTP, scheduled, queue, and email events
- Runs JavaScript/TypeScript/Python/Rust
- CPU capped at 50ms (free), 30s (paid)
- 128MB memory limit

**D1** - SQLite database that replicates reads globally
- Plain SQLite syntax, nothing new to learn
- One writer keeps consistency simple
- Reads replicate across the globe
- 25GB database size limit
- Wrap transactions in batch operations

**KV** - Key-value store spread across the edge
- Reads come back in sub-milliseconds (edge-cached)
- Eventually consistent (~60s globally)
- 25MB value size limit
- TTL expiry handled for you
- Where it shines: caching, session data, feature flags

**R2** - Object storage that speaks the S3 API
- No egress fees — that's the big win over S3
- Storage with no cap
- 5TB object size limit
- S3-compatible API
- Multipart upload support

**Durable Objects** - Single-instance stateful compute with WebSockets
- One instance per key gives you strong consistency
- Persistent storage (1GB limit paid)
- WebSocket support
- Hibernates itself when idle

**Queues** - Message queue plumbing
- At-least-once delivery
- Retries on their own (exponential backoff)
- Dead-letter queue support
- Batch processing

**Pages** - Static hosting plus serverless functions
- Push to Git and it deploys itself
- Routes follow your directory layout
- Framework support (Next.js, Remix, Astro, SvelteKit)
- Preview deployments out of the box

**Workers AI** - AI model inference at the edge
- LLMs (Llama 3, Mistral, Gemma, Qwen)
- Image generation (Stable Diffusion, DALL-E)
- Embeddings (BGE, GTE)
- Speech recognition (Whisper)
- No GPUs to manage

**Browser Rendering** - Headless browser you drive remotely
- Puppeteer/Playwright support
- Screenshots, PDFs, web scraping
- Reuse sessions to keep costs down
- MCP server support for AI agents

## Architecture Patterns

### Full-Stack Application

```
┌─────────────────────────────────────────┐
│    Cloudflare Pages (Frontend)          │
│    Next.js / Remix / Astro               │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│    Workers (API Layer)                   │
│    - Routing                             │
│    - Authentication                      │
│    - Business logic                      │
└─┬──────┬──────┬──────┬──────┬───────────┘
  │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼
┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────────────┐
│ D1 │ │ KV │ │ R2 │ │ DO │ │ Workers AI │
└────┘ └────┘ └────┘ └────┘ └────────────┘
```

### Polyglot Storage Pattern

```typescript
export default {
  async fetch(request: Request, env: Env) {
    // KV: Fast cache
    const cached = await env.KV.get(key);
    if (cached) return new Response(cached);

    // D1: Structured data
    const user = await env.DB.prepare(
      "SELECT * FROM users WHERE id = ?"
    ).bind(userId).first();

    // R2: Media files
    const avatar = await env.R2_BUCKET.get(`avatars/${user.id}.jpg`);

    // Durable Objects: Real-time
    const chat = env.CHAT_ROOM.get(env.CHAT_ROOM.idFromName(roomId));

    // Queue: Async processing
    await env.EMAIL_QUEUE.send({ to: user.email, template: 'welcome' });

    return new Response(JSON.stringify({ user }));
  }
};
```

## Wrangler CLI Essentials

### Installation
```bash
npm install -g wrangler
wrangler login
wrangler init my-worker
```

### Core Commands
```bash
# Development
wrangler dev                    # Local dev server
wrangler dev --remote          # Dev on real edge

# Deployment
wrangler deploy                # Deploy to production
wrangler deploy --dry-run      # Preview changes

# Logs
wrangler tail                  # Real-time logs
wrangler tail --format pretty  # Formatted logs

# Versions
wrangler deployments list      # List deployments
wrangler rollback [version]    # Rollback

# Secrets
wrangler secret put SECRET_NAME
wrangler secret list
```

### Resource Management
```bash
# D1
wrangler d1 create my-db
wrangler d1 execute my-db --file=schema.sql

# KV
wrangler kv:namespace create MY_KV
wrangler kv:key put --binding=MY_KV "key" "value"

# R2
wrangler r2 bucket create my-bucket
wrangler r2 object put my-bucket/file.txt --file=./file.txt
```

## Configuration (wrangler.toml)

```toml
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"

# Environment variables
[vars]
ENVIRONMENT = "production"

# D1 Database
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "YOUR_DATABASE_ID"

# KV Namespace
[[kv_namespaces]]
binding = "KV"
id = "YOUR_NAMESPACE_ID"

# R2 Bucket
[[r2_buckets]]
binding = "R2_BUCKET"
bucket_name = "my-bucket"

# Durable Objects
[[durable_objects.bindings]]
name = "COUNTER"
class_name = "Counter"
script_name = "my-worker"

# Queues
[[queues.producers]]
binding = "MY_QUEUE"
queue = "my-queue"

# Workers AI
[ai]
binding = "AI"

# Cron triggers
[triggers]
crons = ["0 0 * * *"]
```

## Best Practices

### Performance
- Keep the Worker bundle small (<1MB bundled)
- Reach for bindings instead of fetch — they skip the HTTP hop
- Lean on KV and the Cache API for hot data
- Batch multiple D1 queries together
- Stream large responses rather than buffering them

### Security
- Stash API keys with `wrangler secret`
- Keep production/staging/development environments apart
- Validate anything the user sends
- Rate-limit with KV or Durable Objects
- Set sane CORS headers

### Cost Optimization
- Put large files in R2 (zero egress fees vs S3)
- Cache in KV to cut D1/R2 request volume
- Dedupe repeated requests through caching
- Index D1 properly so queries stay cheap
- Watch usage through Cloudflare Analytics

## Decision Matrix

| Need | Choose |
|------|--------|
| Sub-millisecond reads | KV |
| SQL queries | D1 |
| Files over 25MB | R2 |
| Live WebSocket connections | Durable Objects |
| Background work off the request path | Queues |
| ACID transactions | D1 |
| Strong consistency | Durable Objects |
| No egress charges | R2 |
| AI inference | Workers AI |
| Static site hosting | Pages |

## Resources

- Docs: https://developers.cloudflare.com
- Wrangler: https://developers.cloudflare.com/workers/wrangler/
- Discord: https://discord.cloudflare.com
- Examples: https://developers.cloudflare.com/workers/examples/
- Status: https://www.cloudflarestatus.com
