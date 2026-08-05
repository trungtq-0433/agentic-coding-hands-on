# Unified Summary Template

All `create`, `generate`, and `review` outputs MUST use this format:

```markdown
## Infrastructure Summary

### Tools
| Tool | Status | Install |
|------|--------|---------|
| terraform | vX.X.X / not installed | `brew install terraform` |
| tfsec | vX.X.X / not installed | `brew install tfsec` |
| checkov | vX.X.X / not installed | `pip install checkov` |
| infracost | vX.X.X / not installed | `brew install infracost` |
| oiq | available / not installed | github.com/terrateamio/openinfraquote |

### Security Review
**Methods:** AI review (CIS + Well-Architected) · tfsec vX.X.X · checkov vX.X.X
**Skipped:** tfsec (not installed) · checkov (not installed)

| # | Severity | Resource | Finding | Recommendation |
|---|----------|----------|---------|----------------|
| 1 | HIGH | aws_s3_bucket.data | Public access not blocked | Enable block_public_access |
| 2 | MEDIUM | aws_db_instance.main | Single-AZ in prod | Set multi_az = true |

### Cost Estimate
Break down cost for ALL environments (dev, staging, prod). One subtotal row per env, then grand total.

| # | Resource | Type | Qty | Monthly USD | Notes |
|---|----------|------|-----|-------------|-------|
|   | **Dev** | | | | |
| 1 | EKS Cluster | aws_eks_cluster | 1 | $73.00 | Control plane |
| 2 | RDS Aurora | aws_rds_cluster | 1 | $73.00 | Single writer |
|   | **dev subtotal** | | | **$146.00** | |
|   | **Prod** | | | | |
| 3 | EKS Cluster | aws_eks_cluster | 1 | $73.00 | Control plane |
| 4 | RDS Aurora | aws_rds_cluster | 2 | $146.00 | Writer + reader |
|   | **prod subtotal** | | | **$219.00** | |
|   | **Grand Total** | | | **$XXX.00** | estimate only |

### Files Generated
| # | Path | Description |
|---|------|-------------|
| 1 | modules/vpc/main.tf | VPC, subnets, NAT |
| 2 | modules/eks/main.tf | EKS cluster + node group |

### Summary
- **Security:** X HIGH · Y MEDIUM · Z LOW
- **Cost:** ~$XXX/month total (dev: $X · staging: $X · prod: $X) — estimate only
- **Files:** N files across M modules
```
