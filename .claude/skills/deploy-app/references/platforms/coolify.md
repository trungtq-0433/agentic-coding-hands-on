# Coolify (Self-Hosted)

## Setup
```bash
# Install on VPS
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

## Deploy
```bash
# Via API
curl -X POST "https://your-coolify.com/api/v1/deploy" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"uuid": "APP_UUID"}'

# Or via dashboard / Git webhook (auto-deploy)
```

## Detection
- `docker-compose.yml` + Coolify dashboard reference
- Dockerfile, buildpack detection

## Free Tier
- Free, since you host it yourself (open-source)
- You only pay for the VPS (~$5-6/mo on DO/Vultr, $2.50 at Vultr's floor)

## Rollback
From the dashboard: pick an earlier deployment

## Best For
Teams who want a Heroku-style PaaS on their own box. 280+ one-click services.
Spans multiple servers, supports Docker Swarm, and gets free SSL through Let's Encrypt.
