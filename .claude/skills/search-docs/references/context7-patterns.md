# How context7.com URLs Are Shaped

## Topic-Specific URLs (reach for these first)

**Shape:** `https://context7.com/{path}/llms.txt?topic={keyword}`

**Use it when:** the user is after one specific feature or component

**Examples:**
```
shadcn/ui date picker
→ https://context7.com/shadcn-ui/ui/llms.txt?topic=date

Next.js caching
→ https://context7.com/vercel/next.js/llms.txt?topic=cache

Better Auth OAuth
→ https://context7.com/better-auth/better-auth/llms.txt?topic=oauth

FFmpeg compression
→ https://context7.com/websites/ffmpeg_doxygen_8_0/llms.txt?topic=compress
```

**Why bother:** you get back only the docs that matter — roughly 10x faster, a fraction of the tokens.

## General Library URLs (the fallback)

**GitHub repos:** `https://context7.com/{org}/{repo}/llms.txt`

**Websites:** `https://context7.com/websites/{normalized-path}/llms.txt`

## Known Repository Mappings

```
next.js → vercel/next.js
nextjs → vercel/next.js
astro → withastro/astro
remix → remix-run/remix
shadcn → shadcn-ui/ui
shadcn/ui → shadcn-ui/ui
better-auth → better-auth/better-auth
```

## Official Site Fallbacks

Only when context7.com is down:
```
Astro: https://docs.astro.build/llms.txt
Next.js: https://nextjs.org/llms.txt
Remix: https://remix.run/llms.txt
SvelteKit: https://kit.svelte.dev/llms.txt
```

## Topic Keyword Normalization

**The rules:**
- Force to lowercase
- Strip special characters
- For a multi-word topic, keep only the first word
- Cap at 20 characters

**Examples:**
```
"date picker" → "date"
"OAuth" → "oauth"
"Server-Side" → "server"
"caching strategies" → "caching"
```
