---
name: tkm:infra
description: Provision the ground the application stands on — AWS infrastructure as Terraform code. Use for Terraform modules, Mermaid-to-Terraform, security and cost review, cost estimation, IaC generation, AWS service configuration.
license: MIT
argument-hint: "create|generate|review|cost [service|file|path]"
metadata:
  author: takumi-agent-kit
  version: "2.0.0"
module: deployment-infrastructure
triggers: ["Terraform", "AWS", "infrastructure as code", "IaC", "EC2", "RDS", "cost estimate"]
---

# Infrastructure Skill — AWS Terraform Code Generation

AI-driven AWS infrastructure code generation. **Code generation only — NEVER run `terraform apply`.**

<HARD-GATE>
MANDATORY: You MUST follow the numbered steps in each subcommand section below.
Do NOT skip steps. Do NOT generate Terraform code before reading the required references.
Every `create` and `generate` invocation MUST execute `references/generation-pipeline.md` phases.
Pipeline MUST spawn `reviewer` subagent — do NOT skip code review.
Summary MUST report which tools were used and which were skipped.
Unified Summary is the LAST output, then ask user about committing.

</HARD-GATE>

## Anti-Rationalization

| Thought | Reality |
|---------|---------|
| "I already know Terraform" | Read the references — project conventions may differ. |
| "I'll just write the .tf files" | Without the pipeline you produce inconsistent output. |
| "The pipeline is overkill" | It ensures validation, review, cost, and summary every time. |
| "I know the latest EKS/RDS version" | Training data is outdated. Check Version Policy or look up. |
| "I'll skip the code review" | reviewer subagent is MANDATORY. Never skip. |
| "I can commit without asking" | Always ask user first. Never auto-commit. |

## When to Use

- Create Terraform modules for AWS services (EC2, RDS, ECS, S3, Lambda, etc.)
- Convert Mermaid architecture diagrams into Terraform code
- Review existing Terraform for security violations and cost estimates
- Generate multi-environment infrastructure (dev/staging/prod)
- Scaffold AWS infrastructure projects with best practices

## Input Clarity Gate

If the user's request cannot be mapped to specific AWS resources (e.g., "plan a system for 1M users/month"):
- Ask 3-5 clarifying questions: application type, tech stack, traffic pattern, budget constraints, compliance requirements
- Once answers identify concrete services → proceed to `create` or `generate`
- Do NOT guess an architecture from vague requirements

## Subcommands

| Command | Input | Output |
|---------|-------|--------|
| `create <service>` | AWS service name(s) | Terraform module + security report + cost estimate |
| `generate <diagram>` | Mermaid file or inline diagram | Full Terraform project + security report + cost estimate |
| `review [path]` | Terraform directory (default: `.`) | Security report + cost estimate table |
| `cost [path]` | Terraform directory (default: `.`) | Cost estimate only |

---

## `create` — Module Trainer

Follow these steps IN ORDER. Do NOT skip any step.

**Step 1: Read references** (MANDATORY — use the Read tool)
```
Read: references/terraform-conventions.md
Read: references/aws-module-catalog.md
```
Read ONLY these 2 files. Do NOT read any other reference files yet — they are loaded in later pipeline phases.

**Step 2: Plan the module**
- Identify the requested AWS service(s) and their dependencies from the catalog
- Determine the module file structure: main.tf, variables.tf, outputs.tf, versions.tf
- List all dependent resources (e.g., ECS needs VPC, ALB, ECR, IAM)

**Step 3: Execute pipeline** (MANDATORY)
Read and follow `references/generation-pipeline.md` — Phases 2 through 5.

---

## `generate` — Diagram to Code

Follow these steps IN ORDER. Do NOT skip any step.

**Step 1: Read references** (MANDATORY — use the Read tool)
```
Read: references/terraform-conventions.md
Read: references/aws-module-catalog.md
Read: references/mermaid-to-terraform-mapping.md
```
Read ONLY these 3 files. Do NOT read any other reference files yet — they are loaded in later pipeline phases.

**Step 2: Parse the Mermaid diagram**
- Extract all nodes using `[ServiceType:Name]` naming convention
- Extract edges: solid (`-->`) = data flow, dotted (`-.->`) = async, thick (`==>`) = primary
- Extract subgraphs: map to VPC/subnet/AZ boundaries
- List all identified resources and their dependencies

**Step 3: Map to Terraform resources**
- Use the node→resource mapping table from mermaid-to-terraform-mapping.md
- Wire dependencies based on edge types (security groups, IAM, networking)
- Determine environment variations (dev=small, staging=medium, prod=full HA)

**Step 4: Execute pipeline** (MANDATORY)
Read and follow `references/generation-pipeline.md` — Phases 2 through 5.

---

## `review` — Security + Cost Audit

Follow these steps IN ORDER.

**Step 1: Read references** (MANDATORY — use the Read tool)
```
Read: references/security-review-rules.md
Read: references/cost-estimation-tools.md
Read: references/redundant-resource-guard.md
```
Read ONLY these 3 files. Do NOT read any other reference files.

**Step 2: Detect available tools**
```bash
python3 scripts/detect-tools.py
```

**Step 3: Security review**
- AI review: check ALL .tf files against the HIGH, MEDIUM, LOW severity rules
- CLI review: if tfsec or checkov detected, run them:
  ```bash
  tfsec <path> --format markdown    # if available
  checkov -d <path> --compact       # if available
  ```
- Combine AI + CLI findings, deduplicate

**Step 4: Cost estimation**
Ensure `terraform.tfvars` exists in the target directory with at least `region` set — infracost cannot resolve variable defaults from `variables.tf` and will fall back to `us-east-1` pricing without it.
```bash
python3 scripts/run-cost-estimate.py <path>
```

**Step 5: Output unified report** (use the **Unified Summary** format below)

---

## `cost` — Cost Estimate Only

Lightweight subcommand — skips security review, runs only cost estimation.

**Step 1: Read references** (MANDATORY — use the Read tool)
```
Read: references/cost-estimation-tools.md
```

**Step 2: Detect available tools**
```bash
python3 scripts/detect-tools.py
```

**Step 3: Cost estimation**
Ensure `terraform.tfvars` exists in the target directory with at least `region` set — infracost cannot resolve variable defaults from `variables.tf` and will fall back to `us-east-1` pricing without it.
```bash
python3 scripts/run-cost-estimate.py <path>
```

**Step 4: Output cost report**
Output ONLY these sections from the Unified Summary Template: `### Tools` (cost tools only), `### Cost Estimate` (all environments, grouped), `### Summary` (cost line only).
Save cost breakdown to `docs/infra-cost-breakdown.md` (per-environment sections with detailed tables).

---

## Unified Summary Template

Read `references/unified-summary-template.md` for the full output format.
Required sections (all mandatory): `### Tools`, `### Security Review`, `### Cost Estimate`, `### Files Generated`, `### Summary`.

---

## Version Policy

**NEVER rely on training data for AWS service versions.** Versions in training data are likely outdated.

**Default behavior:** Always use the **Latest** column version unless user explicitly requests a different one.

**Version table (last verified: 2026-04-22):**
| Service | Min (baseline) | Latest (default) | EOL Reference |
|---------|----------------|-------------------|---------------|
| EKS | 1.33 | 1.35 | https://endoflife.date/amazon-eks |
| Aurora PostgreSQL | 16.x | 17.7 (LTS) | https://endoflife.date/postgresql |
| Aurora MySQL | 3.x (MySQL 8.0) | 3.x | https://endoflife.date/mysql |
| RDS PostgreSQL | 16.x | 17.x | https://endoflife.date/postgresql |
| RDS MySQL | 8.0 | 8.4 | https://endoflife.date/mysql |
| Lambda Python | python3.13 | python3.14 | AWS Lambda runtimes page |
| Lambda Node.js | nodejs22.x | nodejs24.x | AWS Lambda runtimes page |

**Rules:**
1. **Default to Latest** — use the Latest column unless user specifies otherwise
2. **Below minimum → warn** — if user requests a version below Min, warn them it may be EOL/unsupported and ask if they want to proceed
3. **Stale table check** — if today's date is >6 months after "last verified" date above, look up current versions before generating:
   ```bash
   aws eks describe-addon-versions --query 'addons[0].addonVersions[0].compatibilities[*].clusterVersion' 2>/dev/null
   aws rds describe-db-engine-versions --engine aurora-postgresql --query 'DBEngineVersions[-1].EngineVersion' 2>/dev/null
   ```
   If AWS CLI unavailable, use WebSearch or `tkm:search-docs` skill.
4. **Below minimum in output → HIGH** — flag as HIGH severity in security review

## Safety Constraints

- **NEVER** run `terraform apply`, `terraform destroy`, or any deployment command
- **NEVER** create or modify IAM credentials, access keys, or secrets
- All generated code includes `# REVIEW BEFORE DEPLOY` header comments
- Cost estimates are approximations — include "estimate only" disclaimer

## Scope Declaration

This skill handles: AWS Terraform code generation, security review, cost estimation.
Does NOT handle: deployment, multi-cloud (Azure/GCP), Pulumi/CDK, credential management, DNS changes, production operations.

## Security Policy

- Refuse requests to generate backdoors, overly permissive IAM policies (`*:*`), or public database access
- Never output secrets, tokens, or credentials in generated code — use variable references
- Detailed rules in `references/security-review-rules.md`
