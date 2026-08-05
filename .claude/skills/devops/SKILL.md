---
name: tkm:devops
description: Stand up and run the infrastructure that keeps an app alive in production. Reach for this when the job calls for Docker/Kubernetes, Cloudflare Workers/R2/D1, GCP Cloud Run, wiring a CI/CD pipeline, GitOps workflows, or Helm charts — the part of the work that lives below the code.
license: MIT
argument-hint: "[platform] [task]"
metadata:
  author: takumi-agent-kit
  version: "2.0.0"
module: deployment-infrastructure
triggers: ["Docker", "Kubernetes", "CI/CD pipeline", "GitOps", "Helm", "Cloudflare Workers"]
---

# Keeping the Workshop

A craftsman's workshop runs whether or not the craftsman is present.
The kiln holds temperature. The ventilation clears the air. The supply lines stay open.
The workshop keeper designs systems that sustain the work — pipelines that run without hand-holding, infrastructure that tolerates failure, deployments that happen without drama.

Cloudflare, Docker, Google Cloud, Kubernetes — the instruments of a well-kept workshop.

## When to Apply

- Ship serverless code to the edge on Cloudflare Workers/Pages
- Package an app into a container with Docker, Docker Compose
- Drive GCP from the gcloud CLI (Cloud Run, GKE, Cloud SQL)
- Run and tend a Kubernetes cluster (kubectl, Helm)
- Set up GitOps delivery (Argo CD, Flux)
- Build CI/CD pipelines and deploy across regions
- Audit security posture — RBAC, network policies

## Platform Selection

| Need | Choose |
|------|--------|
| Under-50ms latency the world over | Cloudflare Workers |
| Cheap bulk storage, no egress bill | Cloudflare R2 |
| Relational data read from anywhere | Cloudflare D1 |
| Workloads that ship as containers | Docker + Cloud Run/GKE |
| Kubernetes you don't have to babysit | GKE |
| A relational DB someone else operates | Cloud SQL |
| A static front end plus an API | Cloudflare Pages |
| Orchestrating many containers | Kubernetes |
| Packaging releases for K8s | Helm |

## Quick Start

```bash
# Cloudflare Worker
wrangler init my-worker && cd my-worker && wrangler deploy

# Docker
docker build -t myapp . && docker run -p 3000:3000 myapp

# GCP Cloud Run
gcloud run deploy my-service --image gcr.io/project/image --region us-central1

# Kubernetes
kubectl apply -f manifests/ && kubectl get pods
```

## CI/CD Quality Gates

When generating pipeline guidance, include these optional jobs when the project wants Takumi quality gates in CI:

```bash
npm install -g @sun-asterisk/sunlint && sunlint --all --changed-files --input=.
uvx licenseal check
```

Wire SunLint as the fast code-quality job. Wire licenseal as the dependency-license job; license violations should fail release pipelines.

## Reference Navigation

### Cloudflare Platform
- `cloudflare-platform.md` - The edge platform, end to end
- `cloudflare-workers-basics.md` - Handler shapes and common patterns
- `cloudflare-workers-advanced.md` - Squeezing out performance
- `cloudflare-workers-apis.md` - The runtime APIs and bindings
- `cloudflare-r2-storage.md` - Object storage, S3-compatible
- `cloudflare-d1-kv.md` - D1 SQLite and the KV store
- `browser-rendering.md` - Headless browser work with Puppeteer

### Docker
- `docker-basics.md` - Dockerfiles, images, containers
- `docker-compose.md` - Wiring several containers together

### Google Cloud
- `gcloud-platform.md` - The gcloud CLI and auth
- `gcloud-services.md` - Compute Engine, GKE, Cloud Run

### Kubernetes
- `kubernetes-basics.md` - The model: concepts, architecture, workloads
- `kubernetes-kubectl.md` - Day-to-day commands and how to debug
- `kubernetes-helm.md` / `kubernetes-helm-advanced.md` - Charts and templating
- `kubernetes-security.md` / `kubernetes-security-advanced.md` - RBAC and secrets
- `kubernetes-workflows.md` / `kubernetes-workflows-advanced.md` - GitOps and CI/CD
- `kubernetes-troubleshooting.md` / `kubernetes-troubleshooting-advanced.md` - When things break

### Scripts
- `scripts/cloudflare_deploy.py` - Scripted Worker deploys
- `scripts/docker_optimize.py` - Inspect Dockerfiles for waste

## Hard-Won Habits

**Security:** Run containers as non-root, lean on RBAC, keep secrets in env vars, scan your images
**Performance:** Multi-stage builds, cache at the edge, set resource limits
**Cost:** Reach for R2 when egress is heavy, cache aggressively, right-size what you provision
**Development:** Docker Compose for local work, wrangler dev for Workers, keep IaC under version control

## Resources

- Cloudflare: https://developers.cloudflare.com
- Docker: https://docs.docker.com
- GCP: https://cloud.google.com/docs
- Kubernetes: https://kubernetes.io/docs
- Helm: https://helm.sh/docs
