# Stack: Express + PostgreSQL

## Khi nào dùng
- API-only backend (REST hoặc GraphQL)
- Microservice
- Cần full control server-side logic

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Runtime | Node.js | 20.x |
| Framework | Express | 5.x |
| Language | TypeScript | 5.x |
| Database | PostgreSQL | 16 |
| ORM | Drizzle | latest |
| Validation | Zod | latest |
| Auth | JWT (jose) | latest |
| Testing | Vitest + Supertest | latest |
| Deploy | Railway | - |

## Init Commands

```bash
mkdir {{name}} && cd {{name}}
npm init -y

# Core
npm i express zod dotenv cors helmet
npm i drizzle-orm postgres
npm i jose bcryptjs

# Dev
npm i -D typescript tsx @types/node @types/express @types/cors @types/bcryptjs
npm i -D drizzle-kit
npm i -D vitest supertest @types/supertest

# TypeScript config
npx tsc --init --target es2022 --module nodenext --outDir dist --rootDir src
```

## Project Structure

```
src/
├── routes/
│   ├── auth.ts
│   ├── users.ts
│   └── [resource].ts
├── middleware/
│   ├── auth.ts
│   ├── validate.ts
│   └── error-handler.ts
├── db/
│   ├── schema.ts
│   ├── index.ts
│   └── migrations/
├── services/
│   └── [resource].service.ts
├── lib/
│   ├── jwt.ts
│   └── hash.ts
├── types/
│   └── index.ts
├── app.ts
└── server.ts
tests/
├── routes/
│   ├── auth.test.ts
│   └── [resource].test.ts
└── setup.ts
drizzle.config.ts
```

## Key Patterns

### App Setup
```typescript
// src/app.ts
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import { errorHandler } from './middleware/error-handler'
import { authRouter } from './routes/auth'

const app = express()
app.use(helmet())
app.use(cors())
app.use(express.json())

app.use('/api/auth', authRouter)
app.use(errorHandler)

export { app }
```

### Validation Middleware
```typescript
// src/middleware/validate.ts
import { ZodSchema } from 'zod'
import { Request, Response, NextFunction } from 'express'

export const validate = (schema: ZodSchema) =>
  (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body)
    if (!result.success) return res.status(400).json({ errors: result.error.flatten() })
    req.body = result.data
    next()
  }
```

### Drizzle Schema
```typescript
// src/db/schema.ts
import { pgTable, uuid, text, timestamp, varchar } from 'drizzle-orm/pg-core'

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  name: varchar('name', { length: 100 }),
  createdAt: timestamp('created_at').defaultNow()
})
```

## Environment Variables

```env
PORT=3001
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
JWT_SECRET=your-secret-key
NODE_ENV=development
```
