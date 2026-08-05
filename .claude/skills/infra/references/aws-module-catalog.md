# AWS Terraform Module Catalog

Practical patterns for AI-driven infrastructure code generation. Focus: essential config keys, dependencies, and variable patterns.

## Networking

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **VPC** | aws_vpc | cidr_block, enable_dns_hostnames | None | vpc_cidr, env |
| **Subnet** | aws_subnet | vpc_id, cidr_block, az, map_public_ip | VPC | subnet_cidr, availability_zone |
| **IGW** | aws_internet_gateway | vpc_id | VPC | vpc_id |
| **NAT GW** | aws_nat_gateway | subnet_id, allocation_id (EIP) | Subnet, EIP | subnet_id, eip_id |
| **Route Table** | aws_route_table | vpc_id, routes (cidr→target) | VPC | vpc_id, routes |
| **Security Group** | aws_security_group | vpc_id, ingress/egress rules | VPC | vpc_id, allowed_cidr, protocol |
| **SG Rule** | aws_security_group_rule | sg_id, cidr_blocks, from/to_port | SG | sg_id, source_cidr |

## Compute

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **EC2 Instance** | aws_instance | ami, instance_type, subnet_id, sg_ids, key_name | Subnet, SG, key pair | instance_type, ami_id, tags |
| **Launch Template** | aws_launch_template | image_id, instance_type, user_data, sg_ids | SG | instance_type, user_data |
| **ASG** | aws_autoscaling_group | launch_template, min/max/desired_capacity, vpc_zones, target_group_arns | Launch Template, ALB (optional) | min_size, max_size, desired_capacity |

## Database

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **RDS** | aws_db_instance | db_subnet_group_name, engine, instance_class, allocated_storage, username, password | DB Subnet Group | engine, engine_version (**⚠ check SKILL.md Version Policy**), instance_class, allocated_storage |
| **DB Subnet Group** | aws_db_subnet_group | subnet_ids | Subnets | subnet_ids |
| **Aurora Cluster** | aws_rds_cluster | engine (aurora), master_username, master_password, db_subnet_group_name | DB Subnet Group | engine_version (**⚠ check SKILL.md Version Policy**), master_user |
| **DynamoDB** | aws_dynamodb_table | name, billing_mode, attribute definitions, key_schema, gsi/lsi | None | table_name, billing_mode, attributes |
| **ElastiCache** | aws_elasticache_cluster | engine, node_type, num_cache_nodes, subnet_group_name, sg_ids | Cache Subnet Group, SG | engine, node_type, num_nodes |

## Containers

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **ECS Cluster** | aws_ecs_cluster | name, capacity_providers | None | cluster_name |
| **ECS Task Def** | aws_ecs_task_definition | family, container_definitions (JSON), execution_role_arn, requires_compatibilities | IAM Role | container_image, cpu, memory |
| **ECS Service** | aws_ecs_service | cluster_name, task_definition, desired_count, launch_type, load_balancer config | ECS Cluster, Task Def, ALB (optional) | desired_count, container_port |
| **EKS Cluster** | aws_eks_cluster | role_arn, vpc_config (subnet_ids), enabled_cluster_logging | IAM Role, Subnets | cluster_name, version (**⚠ check SKILL.md Version Policy**) |
| **EKS Node Group** | aws_eks_node_group | cluster_name, node_role_arn, subnet_ids, scaling_config | EKS Cluster, IAM Role | desired_size, instance_types |
| **ECR Repository** | aws_ecr_repository | repository_name, image_tag_mutability, scan_on_push | None | repo_name |

## Load Balancing

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **ALB** | aws_lb | name, load_balancer_type="application", subnets, sg_ids | Subnets, SG | lb_name, internal (bool) |
| **Target Group** | aws_lb_target_group | name, port, protocol, vpc_id, health_check config | VPC | tg_name, port, protocol |
| **ALB Listener** | aws_lb_listener | load_balancer_arn, port, protocol, default_action (forward to TG) | ALB, Target Group | lb_arn, listener_port |
| **NLB** | aws_lb | load_balancer_type="network", subnets | Subnets | lb_name, internal |

## Serverless

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **Lambda** | aws_lambda_function | filename/s3_key, function_name, role_arn, handler, runtime, environment vars | IAM Role | function_name, handler, runtime |
| **Lambda Permission** | aws_lambda_permission | function_name, action="lambda:InvokeFunction", principal | Lambda | function_name, principal_arn |
| **API Gateway v2** | aws_apigatewayv2_api | name, protocol_type, target (Lambda URI) | Lambda | api_name, stage_name |
| **API Stage** | aws_apigatewayv2_stage | api_id, name, auto_deploy | API Gateway | stage_name |

## Storage & CDN

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **S3 Bucket** | aws_s3_bucket | bucket, acl, versioning, server_side_encryption config | None | bucket_name, region |
| **S3 Policy** | aws_s3_bucket_policy | bucket, policy (JSON) | S3 Bucket | bucket_id, policy_json |
| **CloudFront** | aws_cloudfront_distribution | origin config, default_cache_behavior, viewer_protocol_policy | S3 (optional) | domain_name, origin_id |
| **Route53 Zone** | aws_route53_zone | name | None | domain_name |
| **Route53 Record** | aws_route53_record | zone_id, name, type (A/AAAA/CNAME), alias/set_identifier | Route53 Zone, target resource | zone_id, record_name |

## Messaging

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **SQS Queue** | aws_sqs_queue | name, visibility_timeout, message_retention_seconds, receive_wait_time | None | queue_name, visibility_timeout |
| **SNS Topic** | aws_sns_topic | name, display_name | None | topic_name |
| **SNS Subscription** | aws_sns_topic_subscription | topic_arn, protocol, endpoint | SNS Topic | topic_arn, protocol |

## Supporting Services

| Service | Resources | Key Config | Dependencies | Variables |
|---------|-----------|-----------|---|---|
| **IAM Role** | aws_iam_role | assume_role_policy (JSON), name | None | role_name, trust_policy |
| **IAM Policy** | aws_iam_policy | name, policy (JSON) | None | policy_name, policy_document |
| **IAM Role Policy Attachment** | aws_iam_role_policy_attachment | role, policy_arn | IAM Role, Policy | role_name, policy_arn |
| **Secrets Manager** | aws_secretsmanager_secret | name, recovery_window_in_days | None | secret_name |
| **Secret Version** | aws_secretsmanager_secret_version | secret_id, secret_string | Secret | secret_id, secret_value |
| **ACM Certificate** | aws_acm_certificate | domain_name, validation_method | Route53 (for DNS validation) | domain_name, subject_alt_names |
| **CloudWatch Log Group** | aws_cloudwatch_log_group | name, retention_in_days | None | log_group_name, retention_days |
| **CloudWatch Alarm** | aws_cloudwatch_metric_alarm | alarm_name, metric_name, threshold, comparison_operator | CloudWatch Log Group | alarm_name, metric_name, threshold |

## Common Dependency Graph

```
Root Dependencies (no requirements):
  - IAM Roles / Policies
  - S3 Buckets
  - DynamoDB Tables
  - SNS Topics / SQS Queues
  - Secrets Manager
  - Route53 Zone

Tier 1 (require root):
  - VPC, Subnets, Security Groups
  - RDS/Aurora (need DB Subnet Group)
  - Lambda (needs IAM Role)
  - ECR Repository

Tier 2 (require Tier 1 or root):
  - EC2 Instances (need Subnet, SG)
  - ECS Cluster + Task Definition (need IAM + ECR)
  - EKS Cluster (need IAM + Subnets)
  - NAT Gateway (needs Subnet + EIP)
  - ElastiCache (needs Subnet Group + SG)

Tier 3 (integrate multiple tiers):
  - ALB/NLB (needs Subnets + SG)
  - ECS Service (needs Cluster + Task Def + ALB)
  - CloudFront (needs S3/custom origin)
  - API Gateway (needs Lambda + IAM)

Tier 4 (observability/routing):
  - CloudWatch Alarms (targets ASG/ECS services)
  - Route53 Records (point to ALB/CloudFront/API Gateway)
  - ACM Certificates (for HTTPS on ALB/CloudFront)

ECS/Fargate Full Stack Example:
  IAM Role → ECR Repo → Task Definition + VPC (Subnets + SG) + ALB → ECS Service → CloudWatch Logs
```

## Quick Patterns for AI Generation

**Stateless API (Lambda + API GW + RDS):**
- Lambda function → IAM role + VPC config
- API Gateway v2 → Lambda permission
- RDS → DB Subnet Group + Security Group (open to Lambda SG)

**Web Service (ECS Fargate + ALB + RDS):**
- VPC → Subnets (public for ALB, private for ECS)
- Security Groups (ALB ingress 80/443, ECS ingress from ALB)
- ALB → Target Group → ECS Service
- ECS Task Definition → IAM role + container image from ECR
- RDS in private subnet, SG allows ECS SG

**Batch Processing (Lambda + SQS + S3):**
- SQS Queue + S3 Bucket (source/destination)
- Lambda function → S3 permissions + SQS read permission
- CloudWatch alarm on queue depth → Lambda trigger config

**Multi-region Setup (CloudFront + Route53 + ACM):**
- S3 bucket (or ALB) as origin
- CloudFront distribution + ACM certificate
- Route53 alias record pointing to CloudFront domain
