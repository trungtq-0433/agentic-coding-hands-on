# Stack: Hono + Cloudflare Workers

## Khi nào dùng
- API edge-first (low latency toàn cầu)
- Serverless / pay-per-request
- Lightweight, performance-critical APIs
- Cloudflare ecosystem (D1, R2, KV, Queues)

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Framework | Hono | 4.x |
| Runtime | Cloudflare Workers | - |
| Language | TypeScript | 5.x |
| Database | Cloudflare D1 (SQLite) | - |
| ORM | Drizzle | latest |
| Auth | JWT (hono/jwt) | built-in |
| Storage | Cloudflare R2 | - |
| Testing | Vitest + miniflare | latest |
| Deploy | Wrangler (Cloudflare) | - |

## Init Commands

```bash
npm create hono@latest {{name}}
# Select: cloudflare-workers

cd {{name}}
npm i drizzle-orm
npm i -D drizzle-kit @cloudflare/vitest-pool-workers vitest wrangler
```

## Project Structure

```
src/
├── routes/
│   ├── auth.ts
│   └── [resource].ts
├── middleware/
│   ├── auth.ts
│   └── cors.ts
├── db/
│   ├── schema.ts
│   └── migrations/
├── lib/
│   └── utils.ts
├── types.ts
└── index.ts
tests/
├── routes/
│   └── [resource].test.ts
└── setup.ts
wrangler.toml
drizzle.config.ts
```

## Key Patterns

### Hono App
```typescript
// src/index.ts
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { jwt } from 'hono/jwt'
import { authRouter } from './routes/auth'

type Bindings = { DB: D1Database; JWT_SECRET: string }

const app = new Hono<{ Bindings: Bindings }>()

app.use('/api/*', cors())
app.route('/api/auth', authRouter)

export default app
```

### Drizzle + D1
```typescript
// src/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name')
})
```

### Wrangler Config
```toml
# wrangler.toml
name = "{{name}}"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "DB"
database_name = "{{name}}-db"
database_id = "xxx"

[[r2_buckets]]
binding = "STORAGE"
bucket_name = "{{name}}-files"
```

## Deploy

```bash
# Create D1 database
wrangler d1 create {{name}}-db

# Run migrations
wrangler d1 migrations apply {{name}}-db

# Deploy
wrangler deploy
```

## Environment Variables

```toml
# In wrangler.toml [vars]
[vars]
JWT_SECRET = "your-secret"
```
