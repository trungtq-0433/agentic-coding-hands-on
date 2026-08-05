# Stack: React + Vite

## Khi nào dùng
- SPA (Single Page Application) không cần SSR
- Dashboard, admin panel, internal tools
- Cần build nhanh, DX tốt

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Framework | React + Vite | React 19, Vite 6 |
| Language | TypeScript | 5.x |
| Routing | React Router | 7.x |
| Styling | Tailwind CSS | 4.x |
| UI Components | shadcn/ui | latest |
| State | Zustand | latest |
| Data Fetching | TanStack Query | 5.x |
| Forms | React Hook Form + Zod | latest |
| Testing | Vitest + Testing Library | latest |
| E2E | Playwright | latest |
| Deploy | Vercel hoặc Netlify | - |

## Init Commands

```bash
npm create vite@latest {{name}} -- --template react-ts
cd {{name}}

# Core deps
npm i react-router-dom zustand @tanstack/react-query
npm i react-hook-form @hookform/resolvers zod
npm i axios

# Styling
npm i -D tailwindcss @tailwindcss/vite
npx shadcn@latest init

# Testing
npm i -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
npm i -D @playwright/test
```

## Project Structure

```
src/
├── app/
│   ├── routes/
│   │   ├── index.tsx
│   │   ├── login.tsx
│   │   └── dashboard.tsx
│   ├── App.tsx
│   └── router.tsx
├── components/
│   ├── ui/              (shadcn)
│   └── [feature]/
├── hooks/
│   ├── useAuth.ts
│   └── use[Feature].ts
├── lib/
│   ├── api.ts           (axios instance)
│   ├── query-client.ts
│   └── utils.ts
├── stores/
│   └── auth-store.ts
├── types/
│   └── index.ts
└── main.tsx
```

## Key Patterns

### API Client
```typescript
// src/lib/api.ts
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

### Zustand Store
```typescript
// src/stores/auth-store.ts
import { create } from 'zustand'

interface AuthState {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  login: async (email, password) => { /* ... */ },
  logout: () => set({ user: null })
}))
```

## Environment Variables

```env
VITE_API_URL=http://localhost:3001/api
VITE_APP_NAME=MyApp
```
