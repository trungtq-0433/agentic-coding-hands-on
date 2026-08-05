# Render

## CLI
There's no first-party CLI — you ship by pushing to Git or hitting the API.

```bash
# Git push to connected branch (auto-deploy)
git push origin main

# API trigger
curl -X POST "https://api.render.com/deploy/srv-XXXXX?key=YOUR_KEY"
```

## Config: render.yaml
```yaml
services:
  - type: web
    name: my-app
    runtime: node
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
```

## Detection
- `render.yaml` in repo root

## Free Tier
- 750 free instance hours/mo (Starter)
- Free PostgreSQL (90 days)
- Goes to sleep after 15min idle, then ~30s to wake

## Rollback
From the dashboard: Events → pick an earlier deploy → Manual Deploy

## Best For
Good for: full-stack apps, background workers, cron jobs, and managed PostgreSQL.
