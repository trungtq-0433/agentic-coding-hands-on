# Stack: Remix + Railway

## Khi nào dùng
- Full-stack web app cần SSR tốt
- Progressive enhancement (hoạt động không JS)
- SEO quan trọng
- Cần deploy cả frontend + backend 1 nơi

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Framework | Remix | 2.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| Database | PostgreSQL (Railway) | 16 |
| ORM | Prisma | latest |
| Auth | Remix Auth (custom session) | - |
| Testing | Vitest + Testing Library | latest |
| Deploy | Railway | - |

## Init Commands

```bash
npx create-remix@latest {{name}} --template remix-run/indie-stack
cd {{name}}

# Đã bao gồm: Tailwind, Prisma, Vitest, session auth, Docker
# Nếu dùng template khác:
npm i @prisma/client
npm i -D prisma tailwindcss vitest @testing-library/react
```

## Project Structure

```
app/
├── routes/
│   ├── _index.tsx
│   ├── login.tsx
│   ├── dashboard.tsx
│   └── api.[resource].ts
├── models/
│   ├── user.server.ts
│   └── [resource].server.ts
├── components/
│   └── [component].tsx
├── utils/
│   ├── session.server.ts
│   ├── db.server.ts
│   └── env.server.ts
├── root.tsx
└── entry.server.tsx
prisma/
├── schema.prisma
├── seed.ts
└── migrations/
```

## Key Patterns

### Loader + Action (Remix core pattern)
```typescript
// app/routes/dashboard.tsx
import type { LoaderFunctionArgs, ActionFunctionArgs } from '@remix-run/node'
import { json } from '@remix-run/node'
import { useLoaderData, Form } from '@remix-run/react'
import { requireUser } from '~/utils/session.server'
import { getTasks, createTask } from '~/models/task.server'

export async function loader({ request }: LoaderFunctionArgs) {
  const user = await requireUser(request)
  const tasks = await getTasks(user.id)
  return json({ tasks })
}

export async function action({ request }: ActionFunctionArgs) {
  const user = await requireUser(request)
  const form = await request.formData()
  await createTask({ title: String(form.get('title')), userId: user.id })
  return json({ ok: true })
}

export default function Dashboard() {
  const { tasks } = useLoaderData<typeof loader>()
  return (
    <div>
      <Form method="post">
        <input name="title" required />
        <button type="submit">Add Task</button>
      </Form>
      <ul>{tasks.map(t => <li key={t.id}>{t.title}</li>)}</ul>
    </div>
  )
}
```

### Railway Deploy
```toml
# railway.toml
[build]
  builder = "nixpacks"
  buildCommand = "npm run build"

[deploy]
  startCommand = "npm start"
  healthcheckPath = "/healthcheck"
  restartPolicyType = "on_failure"
```

## Environment Variables

```env
DATABASE_URL=postgresql://...
SESSION_SECRET=your-session-secret
NODE_ENV=production
```
