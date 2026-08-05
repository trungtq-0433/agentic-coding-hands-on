---
name: tkm:build-frontend
description: Shape the surface the user touches — React/TypeScript frontends with modern patterns. Components, Suspense, lazy loading, useSuspenseQuery, MUI v7, TanStack Router, performance optimization.
argument-hint: "[component or feature]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: design-frontend
triggers: ["React component", "TypeScript frontend", "TanStack Router", "MUI", "useSuspenseQuery", "lazy loading"]
---

# Shaping the Surface

The surface is the one part of the system the user actually puts their hands on. They never see the query plan or the cache layer — but they feel the spinner that lingers, the panel that jumps half a second after it appears, the click that does nothing for a beat too long. This skill is about that felt experience: components that settle into place calmly, data that arrives without the layout lurching, an interface that behaves like it expects to be used rather than merely demoed.

## When to Reach for This Skill

- Standing up a new component or page
- Putting together a whole feature
- Pulling data through TanStack Query
- Wiring routes with TanStack Router
- Dressing components in MUI v7
- Squeezing out performance
- Deciding where frontend code should live
- Holding the line on TypeScript discipline

---

## Quick Start

### Spinning Up a Component

Before a component is done, walk this list:

- [ ] Typed with the `React.FC<Props>` pattern
- [ ] Heavy? Split it out with `React.lazy(() => import())`
- [ ] Loading handled by a `<SuspenseLoader>` wrapper
- [ ] Data pulled via `useSuspenseQuery`
- [ ] Imports go through the aliases: `@/`, `~types`, `~components`, `~features`
- [ ] Styles inline under 100 lines, broken into their own file beyond that
- [ ] Handlers handed to children are wrapped in `useCallback`
- [ ] The default export lives at the bottom
- [ ] No bailing out early with a loading spinner
- [ ] User-facing messages go through `useMuiSnackbar`

### Standing Up a Feature

When a whole feature is on the table, lay out the bones first:

- [ ] Open a `features/{feature-name}/` directory
- [ ] Carve it into `api/`, `components/`, `hooks/`, `helpers/`, `types/`
- [ ] Add the API service file at `api/{feature}Api.ts`
- [ ] Declare the TypeScript types under `types/`
- [ ] Register the route at `routes/{feature-name}/index.tsx`
- [ ] Lazy-load the feature's components
- [ ] Draw Suspense boundaries around them
- [ ] Surface the feature's public API from its `index.ts`

---

## Import Aliases Quick Reference

| Alias | Resolves To | Example |
|-------|-------------|---------|
| `@/` | `src/` | `import { apiClient } from '@/lib/apiClient'` |
| `~types` | `src/types` | `import type { User } from '~types/user'` |
| `~components` | `src/components` | `import { SuspenseLoader } from '~components/SuspenseLoader'` |
| `~features` | `src/features` | `import { authApi } from '~features/auth'` |

Defined in: [vite.config.ts](../../vite.config.ts) lines 180-185

---

## Common Imports Cheatsheet

```typescript
// React & Lazy Loading
import React, { useState, useCallback, useMemo } from 'react';
const Heavy = React.lazy(() => import('./Heavy'));

// MUI Components
import { Box, Paper, Typography, Button, Grid } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

// TanStack Query (Suspense)
import { useSuspenseQuery, useQueryClient } from '@tanstack/react-query';

// TanStack Router
import { createFileRoute } from '@tanstack/react-router';

// Project Components
import { SuspenseLoader } from '~components/SuspenseLoader';

// Hooks
import { useAuth } from '@/hooks/useAuth';
import { useMuiSnackbar } from '@/hooks/useMuiSnackbar';

// Types
import type { Post } from '~types/post';
```

---

## Topic Guides

### 🎨 Component Patterns

**The shape of a modern component:**
- `React.FC<Props>` so the props are typed at the door
- `React.lazy()` to split heavy code out of the main bundle
- `SuspenseLoader` to own the loading moment
- A named const up top, the default export at the bottom

**Where the judgment lives:**
- Lazy-load anything weighty — grids, charts, editors
- Every lazy component sits behind a Suspense boundary
- Lean on `SuspenseLoader` (it fades in rather than snapping)
- Read a component top to bottom: Props → Hooks → Handlers → Render → Export

**[📖 Complete Guide: resources/component-patterns.md](resources/component-patterns.md)**

---

### 📊 Data Fetching

**Start here: useSuspenseQuery**
- Pairs with a Suspense boundary instead of a manual loading flag
- Reads cache first, hits the API second
- Retires the `isLoading` branch entirely
- Generic, so the return type is known

**The API service layer:**
- One file per feature: `features/{feature}/api/{feature}Api.ts`
- Calls ride on the shared `apiClient` axios instance
- Keep every feature's methods in one place
- Routes read `/form/route`, never `/api/form/route`

**[📖 Complete Guide: resources/data-fetching.md](resources/data-fetching.md)**

---

### 📁 File Organization

**Drawing the line between features/ and components/:**
- `features/` holds the domain-bound work — posts, comments, auth
- `components/` holds the genuinely shared pieces — SuspenseLoader, CustomAppBar

**Feature Subdirectories:**
```
features/
  my-feature/
    api/          # API service layer
    components/   # Feature components
    hooks/        # Custom hooks
    helpers/      # Utility functions
    types/        # TypeScript types
```

**[📖 Complete Guide: resources/file-organization.md](resources/file-organization.md)**

---

### 🎨 Styling

**Where the styles go:**
- Under 100 lines: keep them inline as `const styles: Record<string, SxProps<Theme>>`
- Past 100 lines: lift them into a dedicated `.styles.ts` file

**The default tool:**
- Style MUI components through the `sx` prop
- `SxProps<Theme>` keeps it type-safe
- Reach into the theme with `(theme) => theme.palette.primary.main`

**MUI v7 Grid:**
```typescript
<Grid size={{ xs: 12, md: 6 }}>  // ✅ v7 syntax
<Grid xs={12} md={6}>             // ❌ Old syntax
```

**[📖 Complete Guide: resources/styling-guide.md](resources/styling-guide.md)**

---

### 🛣️ Routing

**TanStack Router, organized by folder:**
- Each route lives at `routes/my-route/index.tsx`
- Components come in lazy-loaded
- Declare them with `createFileRoute`
- Hang breadcrumb data off the loader

**Example:**
```typescript
import { createFileRoute } from '@tanstack/react-router';
import { lazy } from 'react';

const MyPage = lazy(() => import('@/features/my-feature/components/MyPage'));

export const Route = createFileRoute('/my-route/')({
    component: MyPage,
    loader: () => ({ crumb: 'My Route' }),
});
```

**[📖 Complete Guide: resources/routing-guide.md](resources/routing-guide.md)**

---

### ⏳ Loading & Error States

**THE NON-NEGOTIABLE: never return early**

```typescript
// ❌ NEVER - Causes layout shift
if (isLoading) {
    return <LoadingSpinner />;
}

// ✅ ALWAYS - Consistent layout
<SuspenseLoader>
    <Content />
</SuspenseLoader>
```

**The reason it matters:** an early return swaps the whole subtree, the layout jumps when data lands (Cumulative Layout Shift), and the user feels the flinch. A Suspense boundary holds the frame steady.

**When something fails:**
- Tell the user through `useMuiSnackbar`
- Never reach for `react-toastify`
- Catch failures in TanStack Query's `onError`

**[📖 Complete Guide: resources/loading-and-error-states.md](resources/loading-and-error-states.md)**

---

### ⚡ Performance

**The levers worth pulling:**
- `useMemo` for computations that cost something — filter, sort, map
- `useCallback` for handlers you pass down to children
- `React.memo` to stop an expensive component re-rendering for nothing
- Debounce search input by 300–500ms
- Clean up in `useEffect` so listeners and timers don't leak

**[📖 Complete Guide: resources/performance.md](resources/performance.md)**

---

### 📘 TypeScript

**The bar we hold:**
- Strict mode on, `any` off the table
- Functions declare their return type
- Pull types with `import type { User } from '~types/user'`
- Prop interfaces carry JSDoc

**[📖 Complete Guide: resources/typescript-standards.md](resources/typescript-standards.md)**

---

### 🔧 Common Patterns

**What this guide walks through:**
- React Hook Form paired with Zod validation
- The contract a DataGrid wrapper has to honor
- House style for Dialog components
- Reading the current user via the `useAuth` hook
- Mutations that invalidate the cache after they land

**[📖 Complete Guide: resources/common-patterns.md](resources/common-patterns.md)**

---

### 📚 Complete Examples

**End-to-end, working code:**
- A component that uses every pattern at once
- A feature laid out in full
- The API service layer
- A route with lazy loading wired in
- Suspense sitting in front of useSuspenseQuery
- A validated form

**[📖 Complete Guide: resources/complete-examples.md](resources/complete-examples.md)**

---

## Navigation Guide

| When the task is... | Open this resource |
|------------|-------------------|
| Build a component | [component-patterns.md](resources/component-patterns.md) |
| Pull in data | [data-fetching.md](resources/data-fetching.md) |
| Decide where files live | [file-organization.md](resources/file-organization.md) |
| Style a component | [styling-guide.md](resources/styling-guide.md) |
| Wire a route | [routing-guide.md](resources/routing-guide.md) |
| Cover loading and failure | [loading-and-error-states.md](resources/loading-and-error-states.md) |
| Tune performance | [performance.md](resources/performance.md) |
| Get the types right | [typescript-standards.md](resources/typescript-standards.md) |
| Forms, auth, or DataGrid | [common-patterns.md](resources/common-patterns.md) |
| See it all assembled | [complete-examples.md](resources/complete-examples.md) |

---

## The Principles That Hold It Together

1. **Anything heavy loads lazily** — routes, DataGrid, charts, editors
2. **Suspense owns the loading moment** — `SuspenseLoader`, not an early return
3. **useSuspenseQuery is the default** — every new fetch goes through it
4. **A feature keeps its shape** — `api/`, `components/`, `hooks/`, `helpers/`
5. **Style placement follows size** — inline under 100 lines, its own file beyond
6. **Imports ride the aliases** — `@/`, `~types`, `~components`, `~features`
7. **Never return early** — that is what keeps the layout from jumping
8. **All notifications go through useMuiSnackbar**

---

## Quick Reference: File Structure

```
src/
  features/
    my-feature/
      api/
        myFeatureApi.ts       # API service
      components/
        MyFeature.tsx         # Main component
        SubComponent.tsx      # Related components
      hooks/
        useMyFeature.ts       # Custom hooks
        useSuspenseMyFeature.ts  # Suspense hooks
      helpers/
        myFeatureHelpers.ts   # Utilities
      types/
        index.ts              # TypeScript types
      index.ts                # Public exports

  components/
    SuspenseLoader/
      SuspenseLoader.tsx      # Reusable loader
    CustomAppBar/
      CustomAppBar.tsx        # Reusable app bar

  routes/
    my-route/
      index.tsx               # Route component
      create/
        index.tsx             # Nested route
```

---

## Starting Point: A Component to Copy

```typescript
import React, { useState, useCallback } from 'react';
import { Box, Paper } from '@mui/material';
import { useSuspenseQuery } from '@tanstack/react-query';
import { featureApi } from '../api/featureApi';
import type { FeatureData } from '~types/feature';

interface MyComponentProps {
    id: number;
    onAction?: () => void;
}

export const MyComponent: React.FC<MyComponentProps> = ({ id, onAction }) => {
    const [state, setState] = useState<string>('');

    const { data } = useSuspenseQuery({
        queryKey: ['feature', id],
        queryFn: () => featureApi.getFeature(id),
    });

    const handleAction = useCallback(() => {
        setState('updated');
        onAction?.();
    }, [onAction]);

    return (
        <Box sx={{ p: 2 }}>
            <Paper sx={{ p: 3 }}>
                {/* Content */}
            </Paper>
        </Box>
    );
};

export default MyComponent;
```

For the fully worked versions, see [resources/complete-examples.md](resources/complete-examples.md)

---

## Skills That Sit Alongside This One

- **error-tracking**: Sentry-based error tracking — it reaches into the frontend too
- **backend-dev-guidelines**: the API shapes on the other side of the wire that this code consumes

---

**Skill Status**: Split into modules that load on demand, so the context window only carries what the current task needs.
