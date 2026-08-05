# Security Review Rules for Terraform AWS Infrastructure

Practical security checklist for reviewing Terraform AWS code before deployment. Use with `tfsec` and `checkov`.

## HIGH Severity (Must-Fix Before Deploy)

### IAM & Authentication
- [ ] IAM policies: no `"*"` in Action field
- [ ] IAM policies: no `"*"` in Resource field (except for non-sensitive ops like list-buckets)
- [ ] IAM users: no inline policies (use groups or roles instead)
- [ ] Lambda execution roles: not using AdministratorAccess or similar blanket policies
- [ ] Root account: no access keys in use
- [ ] API keys/secrets: not hardcoded in code or outputs

### Storage & Encryption
- [ ] S3 buckets: `block_public_access` enabled on all buckets
- [ ] S3 buckets with sensitive data: encryption enabled (default or KMS)
- [ ] EBS volumes: encrypted (default or custom KMS key)
- [ ] RDS/database: encryption_enabled = true
- [ ] Secrets Manager secrets: KMS encryption enabled
- [ ] DynamoDB: encryption at rest enabled

### Network & Access
- [ ] Security groups: no ingress `0.0.0.0/0` on ports 3306, 5432, 1433, 27017, 6379 (databases)
- [ ] Security groups: no ingress `0.0.0.0/0` on port 22 (SSH) in production
- [ ] Security groups: no ingress `0.0.0.0/0` on port 3389 (RDP) in production
- [ ] RDS instances: publicly_accessible = false
- [ ] RDS instances: deletion_protection = true (production)
- [ ] VPC flow logs enabled on production VPCs

### Logging & Monitoring
- [ ] CloudTrail: enabled and multi-region (production)
- [ ] CloudTrail: logs stored in encrypted S3 bucket with MFA delete
- [ ] S3 buckets with data: access logging enabled
- [ ] ALB/NLB: access logs enabled
- [ ] CloudFront distributions: logging enabled
- [ ] CloudWatch Log Groups: retention policy set (not infinite)

### Compute & Containers
- [ ] EC2 instances: IMDSv2 enforced (http_tokens = "required")
- [ ] Lambda: not running with admin-level permissions
- [ ] ECS task definitions: not running as root (no user = "0")
- [ ] ECS tasks: secrets injected via Secrets Manager, not environment variables

---

## MEDIUM Severity (Should-Fix)

### Encryption & Key Management
- [ ] S3 buckets: using AES256 or KMS, not other algorithms
- [ ] RDS: using AES256 or customer-managed KMS key
- [ ] EBS: using default AWS key or customer-managed KMS key
- [ ] S3 buckets with sensitive data: MFA delete enabled
- [ ] Backup keys: using KMS encryption

### Database & Data Protection
- [ ] RDS in production: multi_az = true
- [ ] RDS: backup_retention_period >= 7 days
- [ ] RDS: automatic_failover_enabled = true (production)
- [ ] DynamoDB: point_in_time_recovery_enabled = true
- [ ] RDS: enable_http_endpoint = false (unless explicitly needed for Aurora Serverless)
- [ ] Database replicas: encrypted with same KMS key

### Access & Permissions
- [ ] IAM roles: least privilege principle applied (no wildcard resources)
- [ ] IAM policies: specific actions listed (not "s3:*" or "ec2:*")
- [ ] S3 bucket policies: no public read/write access
- [ ] Cognito: not using unencrypted password fields
- [ ] API Gateway: API keys required for sensitive endpoints

### Monitoring & Alerting
- [ ] CloudWatch alarms: set for critical metrics (CPU, disk, memory)
- [ ] CloudWatch alarms: SNS topic configured for notifications
- [ ] Log retention: set for all CloudWatch log groups
- [ ] Config rules: enabled to monitor compliance (production)

### Compute & Network
- [ ] EC2 security groups: described (description field present)
- [ ] Security group rules: described (description field present)
- [ ] Network ACLs: not overly permissive
- [ ] VPC: default security group modified or not used
- [ ] ECS: container images from trusted registries only (ECR with image scanning)

---

## LOW Severity (Nice-to-Have)

### Code Quality
- [ ] Resource tags: all resources tagged with environment, owner, cost_center
- [ ] Variable descriptions: present and descriptive
- [ ] Output descriptions: present (especially for sensitive outputs)
- [ ] Resource naming: follows convention (e.g., `{env}-{component}-{name}`)
- [ ] Comments: complex logic explained

### Lifecycle & Maintenance
- [ ] S3 buckets: versioning enabled (data protection)
- [ ] S3 buckets: lifecycle rules configured for old versions
- [ ] ECR repositories: lifecycle rules configured (max image count)
- [ ] EBS snapshots: automated snapshots configured
- [ ] AMI: automated snapshots configured

### Terraform State
- [ ] State file: stored in encrypted S3 backend
- [ ] S3 backend bucket: versioning enabled
- [ ] S3 backend bucket: public access blocked
- [ ] Terraform variables: no secrets in .tfvars committed to Git
- [ ] .gitignore: includes .tfvars, *.tfstate, *.tfstate.backup

---

## tfsec Integration

### Installation
```bash
# macOS
brew install tfsec

# Linux
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

# or via npm
npm install -g tfsec
```

### Usage
```bash
# Run with JSON output
tfsec . --format json --out security-report.json

# Run with markdown
tfsec . --format markdown --out security-report.md

# Run with minimal output
tfsec .

# Run with custom minimum severity
tfsec . --minimum-severity MEDIUM

# Run on specific directory
tfsec ./infrastructure
```

### Key tfsec Rules (map to this checklist)
- **AVD-AWS-0001**: S3 bucket public access
- **AVD-AWS-0002**: IAM policy wildcard actions/resources
- **AVD-AWS-0006**: RDS encryption at rest
- **AVD-AWS-0008**: RDS publicly accessible
- **AVD-AWS-0012**: EC2 IMDSv2
- **AVD-AWS-0020**: CloudTrail enabled
- **AVD-AWS-0032**: ECS root user
- **AVD-AWS-0037**: Security group overly permissive

---

## checkov Integration

### Installation
```bash
pip install checkov

# or via homebrew (macOS)
brew install checkov
```

### Usage
```bash
# Run with JSON output
checkov -d . --output json > checkov-report.json

# Run with markdown
checkov -d . --output markdown > checkov-report.md

# Run terraform framework only
checkov -d . --framework terraform

# Run with compact output
checkov -d . --framework terraform --compact

# Run with specific checks
checkov -d . --check CKV_AWS_1,CKV_AWS_2

# Run on specific directory
checkov -d ./infrastructure
```

### Key checkov Checks
- **CKV_AWS_1**: S3 bucket public access
- **CKV_AWS_2**: CloudTrail enabled
- **CKV_AWS_3**: RDS encryption
- **CKV_AWS_5**: ELB/ALB access logs
- **CKV_AWS_7**: ECR image scanning
- **CKV_AWS_8**: EC2 public IP
- **CKV_AWS_19**: Security group ingress rules
- **CKV_AWS_21**: S3 bucket versioning
- **CKV_AWS_23**: CloudWatch Log retention
- **CKV_AWS_26**: EC2 IMDSv2
- **CKV_AWS_33**: KMS key rotation
- **CKV_AWS_34**: DynamoDB encryption

---

## Report Output Format

### Markdown Table Format
```markdown
## Security Review Report - {Environment}

### Summary
- **HIGH**: X findings (must-fix)
- **MEDIUM**: Y findings (should-fix)
- **LOW**: Z findings (nice-to-have)

### Findings

| Severity | Resource | Rule | Finding | Recommendation |
|----------|----------|------|---------|----------------|
| HIGH | aws_s3_bucket.data | S3 public access | block_public_access not enabled | Set all block_public_access flags to true |
| MEDIUM | aws_db_instance.main | RDS multi-AZ | Not multi-AZ in production | Set multi_az = true |
| LOW | aws_security_group.web | Missing description | No description field | Add descriptive description |

### tfsec Tool Output
[Embedded tfsec JSON or markdown]

### checkov Tool Output
[Embedded checkov JSON or markdown]
```

### JSON Format (for tooling)
```json
{
  "summary": {
    "HIGH": 5,
    "MEDIUM": 12,
    "LOW": 8
  },
  "findings": [
    {
      "severity": "HIGH",
      "resource": "aws_s3_bucket.data",
      "rule": "S3 public access",
      "finding": "block_public_access not enabled",
      "recommendation": "Set all block_public_access flags to true",
      "tool": "manual_review"
    }
  ]
}
```

---

## Review Workflow

1. **Run automated tools** (tfsec + checkov)
   ```bash
   tfsec . --format json --out tfsec-report.json
   checkov -d . --output json > checkov-report.json
   ```

2. **Parse results** (group by severity)
   - Extract HIGH, MEDIUM, LOW findings
   - Map tool rule IDs to checklist items

3. **Manual verification** (checklist items not covered by tools)
   - IAM policy least privilege
   - Naming conventions
   - Tag coverage
   - Documentation

4. **Generate report**
   - Use markdown table format
   - Include tool outputs
   - List remediation steps
   - Sign off with reviewer name/date

5. **Remediate** (HIGH → MEDIUM → LOW)
   - Fix HIGH findings before deployment
   - Schedule MEDIUM findings
   - Document LOW findings in backlog

6. **Re-run & verify**
   - Run tools again after fixes
   - Confirm all HIGH findings resolved
   - Update report with final results
