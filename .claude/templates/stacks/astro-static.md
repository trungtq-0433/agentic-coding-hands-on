# Stack: Astro (Static / Content Site)

## Khi nào dùng
- Landing page, marketing site, blog
- Content-heavy site (docs, portfolio)
- Cần performance tối đa (island architecture)
- Multi-framework (React, Vue, Svelte islands)

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Framework | Astro | 5.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| UI Islands | React (optional) | 19.x |
| CMS | Astro Content Collections / MDX | - |
| Testing | Vitest + Playwright | latest |
| Deploy | Vercel hoặc Netlify | - |

## Init Commands

```bash
npm create astro@latest {{name}}
cd {{name}}

# Integrations
npx astro add tailwind
npx astro add react     # Optional: cho interactive islands
npx astro add mdx       # Optional: cho content

# Testing
npm i -D vitest @playwright/test
```

## Project Structure

```
src/
├── pages/
│   ├── index.astro
│   ├── about.astro
│   ├── blog/
│   │   ├── index.astro
│   │   └── [slug].astro
│   └── 404.astro
├── layouts/
│   ├── BaseLayout.astro
│   └── BlogLayout.astro
├── components/
│   ├── Header.astro
│   ├── Footer.astro
│   └── InteractiveWidget.tsx   (React island)
├── content/
│   ├── config.ts
│   └── blog/
│       ├── first-post.md
│       └── second-post.md
├── styles/
│   └── global.css
└── lib/
    └── utils.ts
public/
├── favicon.svg
└── images/
```

## Key Patterns

### Astro Page (zero JS by default)
```astro
---
// src/pages/index.astro
import BaseLayout from '../layouts/BaseLayout.astro'
import { getCollection } from 'astro:content'

const posts = await getCollection('blog')
---
<BaseLayout title="Home">
  <h1>Welcome</h1>
  <ul>
    {posts.map(post => (
      <li><a href={`/blog/${post.slug}`}>{post.data.title}</a></li>
    ))}
  </ul>
</BaseLayout>
```

### Interactive Island (chỉ hydrate khi cần)
```astro
---
import Counter from '../components/Counter.tsx'
---
<!-- client:load = hydrate on page load -->
<Counter client:load />

<!-- client:visible = hydrate khi scroll vào viewport -->
<HeavyChart client:visible />
```

### Content Collection
```typescript
// src/content/config.ts
import { defineCollection, z } from 'astro:content'

export const collections = {
  blog: defineCollection({
    type: 'content',
    schema: z.object({
      title: z.string(),
      date: z.date(),
      tags: z.array(z.string()).optional(),
      draft: z.boolean().default(false)
    })
  })
}
```

## Environment Variables

```env
PUBLIC_SITE_URL=https://mysite.com
```
