# Stack: Next.js + Supabase

## Khi nào dùng
- Web app có auth, database, realtime
- MVP cần ship nhanh
- Budget thấp (free tier generous)

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Framework | Next.js (App Router) | 15.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| UI Components | shadcn/ui | latest |
| Database | Supabase (PostgreSQL) | - |
| ORM | Drizzle | latest |
| Auth | Supabase Auth | - |
| Storage | Supabase Storage | - |
| Testing | Vitest + Testing Library | latest |
| E2E | Playwright | latest |
| Deploy | Vercel (app) + Supabase (db) | - |

## Init Commands

```bash
# Create Next.js app
npx create-next-app@latest {{name}} --typescript --tailwind --app --src-dir

# Install core deps
cd {{name}}
npm i @supabase/supabase-js @supabase/ssr drizzle-orm
npm i -D drizzle-kit supabase

# Install UI
npx shadcn@latest init

# Install testing
npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom
npm i -D @playwright/test

# Init Supabase
npx supabase init
```

## Project Structure

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── api/
│   │   └── [resource]/route.ts
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/          (shadcn components)
│   └── [feature]/   (feature components)
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── middleware.ts
│   ├── db/
│   │   ├── schema.ts
│   │   └── queries.ts
│   └── utils.ts
├── hooks/
└── types/
supabase/
├── migrations/
├── seed.sql
└── config.toml
```

## Key Patterns

### Supabase Client (Server Component)
```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll(), setAll: (c) => c.forEach(({ name, value, options }) => cookieStore.set(name, value, options)) } }
  )
}
```

### Auth Middleware
```typescript
// src/middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  // refresh session, protect routes
}
export const config = { matcher: ['/dashboard/:path*'] }
```

### Drizzle Schema
```typescript
// src/lib/db/schema.ts
import { pgTable, uuid, text, timestamp } from 'drizzle-orm/pg-core'

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: timestamp('created_at').defaultNow()
})
```

## Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=
```
