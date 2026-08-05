# Netlify

## CLI
```bash
npm install -g netlify-cli
netlify login
netlify deploy          # draft
netlify deploy --prod   # production
netlify deploy --dir=dist --prod  # specify build dir
```

## Config: netlify.toml
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## Detection
- `netlify.toml`, `_redirects`, `_headers` files

## Free Tier
- 100GB bandwidth/mo, 300 build min/mo
- 125K function invocations, 10GB storage
- Cross a limit and the site goes dark until you act

## Rollback
```bash
netlify deploy --prod --alias=DEPLOY_ID
# Or via dashboard: Deploys → Published deploy → select previous
```

## Best For
Pick it for: static sites, JAMstack builds, and serverless functions.
