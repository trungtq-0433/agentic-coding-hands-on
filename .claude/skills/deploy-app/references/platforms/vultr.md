# Vultr

## CLI
```bash
# Install
go install github.com/vultr/vultr-cli/v3@latest
# or download binary from GitHub releases

# Auth (uses env var)
export VULTR_API_KEY="your-api-key"
vultr-cli instance list

# Create instance (IaaS — no PaaS deploy)
vultr-cli instance create --region ewr --plan vc2-1c-1gb --os 387
```

## Detection
- Nothing to detect — it's raw VPS/Kubernetes with no project-level config

## Free Tier
- None. Floor is $2.50/mo (VX1, 1vCPU, 0.5GB RAM)
- VKE (Kubernetes): control plane is free, you pay for the nodes

## Best For
Raw VPS, Kubernetes (VKE), and bare metal.
Layer Coolify or Dokploy on top if you want a PaaS feel.
Coolify installs in one click straight from the Vultr Marketplace.
