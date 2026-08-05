# Terraform Conventions Reference

Practical patterns for AI-driven Terraform code generation. Used by `/tkm:infra` skill.

## Directory Layout

```
project/
├── modules/{service}/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── envs/{dev,staging,prod}/
│   ├── main.tf
│   ├── terraform.tfvars
│   └── backend.tf
└── shared/data-sources.tf
```

## Naming Conventions

**Resources:** `{project}_{env}_{service}_{type}`
```hcl
aws_security_group "myapp_dev_api_sg" { }
aws_rds_cluster "myapp_prod_db" { }
```

**Variables, outputs, locals:** `snake_case`
```hcl
variable "instance_type" { }
output "rds_endpoint" { }
locals { service_name = "${var.project}-${var.env}" }
```

## Module Structure

### main.tf

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags { tags = local.common_tags }
}

resource "aws_security_group" "main" {
  name_prefix = local.service_name
  description = "Security group for ${local.service_name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    cidr_blocks     = var.allowed_cidrs
    description     = "Application traffic"
  }

  tags = merge(local.common_tags, { Name = "${local.service_name}_sg" })
}
```

Pattern: Always merge `common_tags` + `Name` tag. Use descriptions on security rules.

### variables.tf

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string

  validation {
    condition = contains([
      "t3.micro", "t3.small", "t3.medium", "t3.large",
      "m5.large", "m5.xlarge"
    ], var.instance_type)
    error_message = "Instance type must be from approved list."
  }
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed for ingress"
  type        = list(string)

  validation {
    condition = alltrue([for cidr in var.allowed_cidrs : can(cidrhost(cidr, 0))])
    error_message = "All items must be valid CIDR notation."
  }
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

Pattern: Validate CIDR, enums, and instance types. Always include description.

### outputs.tf

```hcl
output "security_group_id" {
  description = "Security group ID for other modules"
  value       = aws_security_group.main.id
}

output "instance_ips" {
  description = "Instance private IPs"
  value       = aws_instance.app[*].private_ip
}
```

Pattern: All outputs need description. Use `sensitive = true` for passwords only.

### versions.tf

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## Environment Separation

Each env has isolated state + configuration:

### envs/dev/backend.tf

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-tf-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "tf-locks-dev"
  }
}
```

Rules:
- Separate S3 bucket per environment
- DynamoDB table for locking (key = `LockID`)
- Versioning + MFA delete on S3

### envs/dev/terraform.tfvars

```hcl
instance_type           = "t3.small"
db_multi_az             = false
backup_retention_days   = 7
allowed_cidrs           = ["10.0.0.0/8"]
```

### envs/prod/terraform.tfvars

```hcl
instance_type           = "t3.medium"
db_multi_az             = true
backup_retention_days   = 30
allowed_cidrs           = ["10.0.0.0/8", "203.0.113.0/24"]
```

Pattern: Dev is minimal, prod is high-availability.

## Tagging Strategy

All resources inherit tags via `default_tags`:

```hcl
provider "aws" {
  default_tags {
    tags = {
      Name        = local.service_name
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      CreatedBy   = "terraform"
    }
  }
}
```

Mandatory: Name, Environment, Project, ManagedBy, CreatedBy

Rules:
- Tag at provider level (inherited by all resources)
- Never use timestamps (Terraform detects drift)
- Use for billing + console filtering

## Post-Generation Checks

```bash
terraform validate
terraform fmt --recursive
terraform plan -out=tfplan
tfsec . --format table
```

CI/CD: Add to pre-commit hooks + pipeline.

## Common Patterns

### Module Composition

```hcl
module "vpc" {
  source = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
  environment = var.environment
}

module "rds" {
  source = "./modules/rds"
  security_group_ids = [module.vpc.db_sg_id]
  depends_on = [module.vpc]
}
```

### Conditional Resources

```hcl
resource "aws_cloudwatch_log_group" "app" {
  count             = var.enable_logging ? 1 : 0
  name              = "/aws/lambda/${local.service_name}"
  retention_in_days = var.log_retention_days
}
```

### Locals for Computed Values

```hcl
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
  service_name = "${var.project}-${var.environment}-${var.service}"
}
```

## Security Rules

- Never commit `.tfstate` files; use S3 backend
- Flag `0.0.0.0/0` ingress as HIGH (unless ALB/CloudFront)
- All security group rules require `description` field
- Use `sensitive = true` on password/token outputs
- Never hardcode IAM credentials (use `aws_iam_role`)

## File Checklist

- [ ] `main.tf` includes `default_tags` at provider level
- [ ] `variables.tf` has `description`, `type`, `validation` for critical vars
- [ ] `outputs.tf` describes what each output is for
- [ ] `versions.tf` pins AWS provider to `~> X.Y`
- [ ] `backend.tf` in each env with unique S3 bucket
- [ ] `terraform.tfvars` per env with environment-specific values
- [ ] All resources tagged via `default_tags` + `Name` tag
- [ ] All security group rules have `description` fields
- [ ] No hardcoded AWS credentials or secrets
- [ ] Run `terraform fmt` before committing
- [ ] Run `terraform validate` in CI/CD
