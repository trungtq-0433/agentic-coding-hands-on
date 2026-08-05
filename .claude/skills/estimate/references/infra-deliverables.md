# Infra Deliverables — Cost Estimate + Architecture Diagram

## When This Activates
After main estimation (Step 7) when `infra` role is in `active_roles`.

## Workflow

### 1. Collect Infra Config (interactive)
Ask user via AskUserQuestion:
- Cloud provider: AWS / GCP / Azure / Managed (Supabase/Vercel/Cloudflare)
- Architecture pattern: web_app_classic / web_app_serverless / microservices / static_site_api / data_pipeline / managed_serverless / custom
- Environments: Dev, Staging, Production, UAT (multi-select)
- Services to include (pre-filled from pattern template, user can add/remove)

### 2. Generate Cost Estimate
Build JSON config from user answers:
```json
{"provider": "aws", "region": "ap-northeast-1", "environments": ["dev", "staging", "production"],
 "services": {"compute": {"type": "fargate", "count": 2}, "database": {"type": "aurora"}, ...},
 "project_name": "Project Name"}
```

Run:
```bash
python3 scripts/render-infra-cost.py <config.json> -o output/<project-slug>/infra/
```

Output: `output/<project-slug>/infra/cost-estimate.md`

**Note:** `render-infra-cost.py` only supports AWS/GCP/Azure providers (service-based pricing). For managed providers (Supabase, Vercel, Cloudflare), write `cost-estimate.md` manually — their pricing is plan-based and simpler.

### 3. Generate Architecture Diagram

**Default: Mermaid (recommended)** — no system dependencies, renders via `npx @mermaid-js/mermaid-cli`.

Build JSON config:
```json
{"provider": "managed", "pattern": "managed_serverless", "project_name": "Project Name"}
```

Run:
```bash
python3 scripts/generate-infra-diagram.py <config.json> -o output/<project-slug>/infra/
```

Output:
- `output/<project-slug>/infra/architecture-diagram.mmd` (always — Mermaid source)
- `output/<project-slug>/infra/architecture-diagram.png` (auto-rendered if Node.js available)

Options:
- `--format svg` or `--format pdf` — change output image format
- `--no-render` — generate `.mmd` only, skip PNG rendering
- `--python-diagrams` — legacy mode: generate Python `diagrams` script (requires `pip install diagrams` + system graphviz)
- `--python-diagrams --render` — legacy mode with auto-render

**Available providers**: `aws`, `gcp`, `azure`, `managed`
**Available patterns**: `web_app_classic`, `web_app_serverless`, `microservices`, `static_site_api`, `data_pipeline`, `managed_serverless`, `custom`

### 4. Update Manifest
Run: `python3 scripts/init-manifest.py output/<project-slug>/`

## Output Structure
```
output/<project-slug>/
├── ... (main estimate files)
└── infra/
    ├── cost-estimate.md
    ├── architecture-diagram.mmd    (Mermaid source)
    └── architecture-diagram.png    (rendered)
```
