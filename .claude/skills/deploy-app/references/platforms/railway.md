# Railway

## CLI
```bash
npm i -g @railway/cli
# or: curl -fsSL https://railway.com/install.sh | sh
railway login
railway up
```

## Config: railway.toml
```toml
[build]
buildCommand = "npm run build"

[deploy]
startCommand = "npm start"
healthcheckPath = "/"
restartPolicyType = "ON_FAILURE"
```

## Detection
- `railway.toml`, `railway.json`
- Railpack works out the language/framework for you

## Free Tier
- No free tier anymore (dropped in 2024)
- $5 trial credit, one time, gone after 30 days
- Hobby plan: $5/mo plus usage on top

## Rollback
```bash
railway service rollback
# Or via dashboard: Deployments → select previous
```

## Best For
Suited to: full-stack apps, databases, background workers, and private networking between services.
