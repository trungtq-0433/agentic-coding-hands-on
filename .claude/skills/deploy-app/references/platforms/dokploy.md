# Dokploy (Self-Hosted)

## Setup
```bash
# Install on VPS
curl -sSL https://dokploy.com/install.sh | sh
```

## Deploy
```bash
# Via CLI
dokploy app deploy <app-id>

# Or via webhook trigger / dashboard
```

## Detection
- `dokploy.yml`, Dockerfile, `docker-compose.yml`

## Free Tier
- Free, self-hosted and open-source
- The VPS is your only cost

## Rollback
From the dashboard: pick an earlier deployment

## Best For
The other self-hosted choice next to Coolify. Native Docker Compose, multi-server Docker Swarm.
Leans on Traefik for reverse proxy and SSL. Speaks MySQL, PostgreSQL, MongoDB, Redis, and MariaDB.
