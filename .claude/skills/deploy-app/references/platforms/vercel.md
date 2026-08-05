# Vercel

## CLI
```bash
npm i -g vercel
vercel login
vercel              # preview
vercel --prod       # production
```

## Config: vercel.json
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": null,
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

## Detection
- `vercel.json`, `.vercel/` directory
- Recognizes Next.js, Vite, and Remix on its own

## Free Tier (Hobby)
- 100GB bandwidth/mo, 1M edge requests/mo
- Personal projects only — no commercial use
- 10s function timeout
- Commercial work means upgrading to Pro ($20/mo)

## Rollback
```bash
vercel rollback [deployment-url]
```

## Best For
Its sweet spot: frontend frameworks (Next.js gets first-class treatment), serverless APIs, and SPAs.
