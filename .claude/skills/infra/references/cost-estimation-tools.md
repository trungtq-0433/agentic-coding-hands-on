# Cost Estimation Tools Reference

Reference for the 3-tier cost estimation tool chain used by `scripts/run-cost-estimate.py`.

## Tool Priority

```
infracost (primary) → oiq (offline fallback) → heuristic (no-tool fallback)
```

Detection is handled by `scripts/detect-tools.py`, which outputs a JSON object with
availability, version, and path for each tool.

---

## Tier 1 — Infracost (Primary)

Infracost provides cloud cost estimates for Terraform using live pricing data.

**Install:**
```bash
# macOS
brew install infracost

# Linux
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh
```

**Auth (required for API calls):**
```bash
infracost auth login
# or set environment variable:
export INFRACOST_API_KEY="<your-key>"
```

**Usage:**
```bash
infracost breakdown --path <tf-dir> --format json
```

**Parse output:**
- Top-level field: `totalMonthlyCost` (string, USD)
- Per-resource costs: `.projects[].breakdown.resources[].monthlyCost`
- Resource name: `.projects[].breakdown.resources[].name`
- Resource type: `.projects[].breakdown.resources[].resourceType`

**Notes:**
- Requires network access for pricing API
- API key obtained free at https://www.infracost.io
- Supports all major Terraform providers, not just AWS

---

## Tier 2 — OpenInfraQuote / oiq (Offline Fallback)

`oiq` is a fully offline alternative that matches Terraform resources to a local prices CSV.

**Install:**
```bash
go install github.com/terrateamio/openinfraquote/cmd/oiq@latest
```

**Setup prices data (one-time):**
```bash
oiq download   # downloads prices.csv to ~/.oiq/prices.csv
```

**Usage:**
```bash
oiq match --tf-dir <tf-dir> | oiq price --prices-file ~/.oiq/prices.csv
```

**Parse output:**
- Tab/space-separated lines: `<resource_name>  <type>  <monthly_cost>`
- Sum lines to get total
- Some lines may show `UNKNOWN` for unsupported resource types

**Notes:**
- No network required after initial `oiq download`
- Coverage is narrower than infracost (mainly AWS compute/RDS)
- Prices CSV may lag behind actual AWS pricing

---

## Tier 3 — Heuristic Fallback (No Tools)

When neither infracost nor oiq is available, the script uses static pricing from
`assets/pricing-heuristic.json`.

**Algorithm:**
1. Grep `.tf` files in the target directory for `resource "aws_*"` declarations
2. Extract resource type and name from each match
3. Look up resource type in `assets/pricing-heuristic.json` → `resources.<type>.base_monthly`
4. If instance_type or class is specified in the `.tf` source, use `variants.<value>` cost
5. Sum all matched resources
6. Always include "ESTIMATE ONLY — verify with infracost" disclaimer

**Supported resource types:** see `assets/pricing-heuristic.json` for full list.

**Limitations:**
- Cannot account for data transfer, request volume, or storage usage
- Fargate/Lambda costs are base only (excludes invocation charges)
- Multi-AZ / read replica multipliers not applied automatically

---

## Tool Chain Detection Flow

```
detect-tools.py
  └─ checks: terraform, infracost, oiq, tfsec, checkov
  └─ outputs JSON: { "infracost": { "available": true, "version": "...", "path": "..." }, ... }

run-cost-estimate.py <tf-dir>
  └─ calls detect-tools.py
  └─ picks best tool (infracost → oiq → heuristic)
  └─ runs estimation
  └─ formats markdown table → stdout
```

---

## Cost Report Output Format

All three tiers produce the same markdown format:

```markdown
## Cost Estimate (Monthly USD)

| Resource | Type | Monthly Cost | Notes |
|----------|------|-------------|-------|
| web_alb | aws_lb | $22.00 | Application LB |
| main_db | aws_db_instance | $150.00 | db.r6g.large |
| app_cluster | aws_eks_cluster | $73.00 | Control plane only |

**Total Estimated:** $245.00/month
**Tool Used:** infracost 0.10.x
**Disclaimer:** Estimates only. Actual costs vary by usage, region, and configuration.
```

Fields:
- **Resource** — Terraform resource label (logical name in .tf files)
- **Type** — Terraform resource type (e.g. `aws_db_instance`)
- **Monthly Cost** — USD/month formatted to 2 decimal places
- **Notes** — instance type, size, or relevant config hint

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `INFRACOST_API_KEY` | Skip `infracost auth login` when set |
| `OIQ_PRICES_FILE` | Override default `~/.oiq/prices.csv` path |
| `INFRA_HEURISTIC_FILE` | Override default `assets/pricing-heuristic.json` path |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `infracost breakdown` fails with 401 | Missing API key | Run `infracost auth login` or set `INFRACOST_API_KEY` |
| `oiq price` fails with "no prices file" | prices.csv not downloaded | Run `oiq download` |
| Heuristic shows $0 for all resources | No `.tf` files in path | Confirm `--path` points to directory with `.tf` files |
| Cost is 0 for `aws_ecs_service` | Fargate billed by task CPU/mem | Check `aws_ecs_task_definition` resource |
| `detect-tools.py` shows oiq not found | `$GOPATH/bin` not in `$PATH` | Add `export PATH="$PATH:$(go env GOPATH)/bin"` to shell profile |
