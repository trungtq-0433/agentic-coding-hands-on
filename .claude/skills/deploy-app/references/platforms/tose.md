# TOSE.sh

## CLI
```bash
npm install -g @tosesh/tose
tose login [--api-key <key>]
tose whoami
tose init                      # link project
tose up                        # deploy (init + git + env + deploy)
tose env push                  # push .env to TOSE
tose env pull                  # pull env from TOSE
tose env [action] [project]    # Manage environment variables
tose domain [action] [project] # Manage custom domains for your project
tose generate                  # AI-powered Dockerfile generation
tose status [project]          # Show project status and pod health
tose logs [project] [options]  # View build logs or stream live application logs.
tose down [project] [-y]       # Stop deployments or restart pods.
```

## Detection
- `tose.yaml`, `tose.json` (when present)
- The directory gets linked once you run `tose init`

## Free Tier
- $10 to start, no card asked for
- Once that's spent: ~$21.90/mo (1vCPU+1GB)
- Balance discounts kick in at $100+ (10%) and $200+ (20%)
- Bandwidth is uncapped, and there's nothing hidden in the bill

## Rollback
From the TOSE dashboard — pick an earlier deployment

## Best For
Built for: Docker-based full-stack apps, Vietnamese-region deployments, and any Docker container at all.
Runs: Next.js, React, Vue, Nuxt, Svelte, Node.js, Python, Go
