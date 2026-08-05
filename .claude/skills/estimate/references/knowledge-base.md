# Knowledge Base Reference

Quick reference for estimation calculations. Load this when calculating estimates.

## Base Efforts (Man-Days)

Base effort values for common tasks. Apply complexity and tech multipliers.

### Crud

| Task | Man-Days |
|------|----------|
| simple | 0.5 |
| standard | 1.0 |
| complex | 1.5 |

### Authentication

| Task | Man-Days |
|------|----------|
| basic | 2.0 |
| oauth single | 3.0 |
| oauth multiple | 4.0 |
| sso | 5.0 |
| mfa | 2.0 |

### Authorization

| Task | Man-Days |
|------|----------|
| basic | 1.0 |
| rbac | 2.0 |
| abac | 4.0 |

### File Operations

| Task | Man-Days |
|------|----------|
| upload simple | 1.0 |
| upload multiple | 1.5 |
| upload large | 2.5 |
| processing | 1.0 |
| storage cloud | 1.5 |

### Notifications

| Task | Man-Days |
|------|----------|
| email simple | 0.5 |
| email templated | 1.0 |
| push | 1.5 |
| sms | 1.0 |
| realtime | 2.0 |

### Search

| Task | Man-Days |
|------|----------|
| basic | 1.0 |
| advanced | 2.0 |
| fulltext | 3.0 |

### Payments

| Task | Man-Days |
|------|----------|
| integration | 5.0 |
| subscription | 4.0 |
| marketplace | 8.0 |

### Reports

| Task | Man-Days |
|------|----------|
| simple | 1.0 |
| dashboard | 2.0 |
| complex | 5.0 |

### Api

| Task | Man-Days |
|------|----------|
| endpoint simple | 0.25 |
| endpoint crud | 0.5 |
| endpoint complex | 1.0 |
| documentation | 0.5 |

### Ui

| Task | Man-Days |
|------|----------|
| page simple | 1.0 |
| page standard | 2.0 |
| page complex | 4.0 |
| component | 0.5 |

### Infrastructure

| Task | Man-Days |
|------|----------|
| architecture design | 1.0 |
| cost estimation | 0.5 |
| account setup | 1.0 |
| networking | 3.0 |
| dns ssl | 1.0 |
| compute setup | 4.0 |
| static hosting | 2.0 |
| database infra | 1.5 |
| cache search infra | 1.5 |
| ci cd per service | 4.0 |
| monitoring alerting | 3.0 |
| waf security | 1.5 |
| infra documentation | 3.0 |

### Testing

| Task | Man-Days |
|------|----------|
| unit per module | 1.0 |
| integration | 2.0 |
| e2e basic | 2.0 |
| e2e comprehensive | 4.0 |

### Documentation

| Task | Man-Days |
|------|----------|
| api | 1.0 |
| user guide | 2.0 |
| technical | 2.0 |

### Data Management

| Task | Man-Days |
|------|----------|
| simple | 1.5 |
| standard | 3.0 |
| complex | 5.0 |

### Database

| Task | Man-Days |
|------|----------|
| schema design | 2.0 |
| setup | 1.5 |
| optimization | 2.0 |

### User Management

| Task | Man-Days |
|------|----------|
| invitation | 2.0 |
| role assignment | 1.5 |
| profile | 1.0 |

### Management

| Task | Man-Days |
|------|----------|
| coordination | 5.0 |
| planning | 3.0 |
| communication | 2.0 |

### Feature Composite

| Task | Man-Days |
|------|----------|
| crud feature | 4.0 |
| auth feature | 3.5 |
| api module | 5.0 |
| notifications feature | 5.0 |
| file ops feature | 3.5 |
| reports feature | 7.5 |
| ui feature | 3.0 |

### Buffer Percentages

| Project Type | Buffer |
|--------------|--------|
| mvp | 15% |
| standard | 20% |
| enterprise | 30% |

## Complexity Multipliers

### Base Complexity

| Level | Multiplier |
|-------|------------|
| simple | 1.0x |
| medium | 1.5x |
| complex | 2.5x |
| very_complex | 4.0x |

### Complexity Factors

**Requirements**

| Factor | Multiplier |
|--------|------------|
| clear | 1.0x |
| moderate | 1.2x |
| unclear | 1.4x |
| missing | 1.6x |

**Integration**

| Factor | Multiplier |
|--------|------------|
| none | 1.0x |
| internal | 1.1x |
| external simple | 1.2x |
| external complex | 1.4x |
| legacy | 1.5x |

**Performance**

| Factor | Multiplier |
|--------|------------|
| standard | 1.0x |
| optimized | 1.2x |
| high | 1.4x |
| realtime | 1.6x |

**Security**

| Factor | Multiplier |
|--------|------------|
| standard | 1.0x |
| enhanced | 1.2x |
| compliance | 1.3x |
| critical | 1.5x |

**Data**

| Factor | Multiplier |
|--------|------------|
| simple | 1.0x |
| moderate | 1.2x |
| complex | 1.4x |
| distributed | 1.6x |

**Ui Ux**

| Factor | Multiplier |
|--------|------------|
| basic | 1.0x |
| custom | 1.2x |
| complex | 1.4x |
| animations | 1.3x |

**Testing**

| Factor | Multiplier |
|--------|------------|
| standard | 1.0x |
| comprehensive | 1.2x |
| critical | 1.4x |

**Team**

| Factor | Multiplier |
|--------|------------|
| experienced | 0.9x |
| standard | 1.0x |
| mixed | 1.1x |
| new | 1.3x |

**Project Type**

| Factor | Multiplier |
|--------|------------|
| greenfield | 1.0x |
| enhancement | 1.1x |
| refactoring | 1.3x |
| migration | 1.4x |

## Tech Stack Multipliers

### Team Familiarity

| Level | Multiplier |
|-------|------------|
| expert | 0.8x |
| familiar | 1.0x |
| moderate | 1.2x |
| learning | 1.5x |
| new | 1.8x |

### Frontend

| Technology | Multiplier |
|------------|------------|
| react | 1.0x |
| vue | 1.0x |
| angular | 1.1x |
| svelte | 0.95x |
| react_native | 1.2x |
| flutter | 1.1x |
| native_ios | 1.3x |
| native_android | 1.3x |

### Backend

| Technology | Multiplier |
|------------|------------|
| django | 1.0x |
| fastapi | 0.95x |
| express | 1.0x |
| nestjs | 1.1x |
| go | 1.0x |
| spring_boot | 1.15x |
| rails | 0.9x |

### Databases

| Technology | Multiplier |
|------------|------------|
| postgresql | 1.0x |
| mysql | 1.0x |
| mongodb | 1.0x |
| redis | 0.9x |
| elasticsearch | 1.3x |
| neo4j | 1.4x |

### Infrastructure

| Technology | Multiplier |
|------------|------------|
| aws | 1.0x |
| gcp | 1.0x |
| azure | 1.0x |
| docker | 1.0x |
| kubernetes | 1.0x |
| lambda | 1.1x |
| cloudflare_workers | 1.0x |

## Experience Factors

### Experience Level

| Level | Multiplier | Description |
|-------|------------|-------------|
| junior | 1.3x | Less experienced, needs more time and guidance |
| mid | 1.0x | Standard baseline for estimation |
| senior | 0.8x | Experienced developer, faster delivery |

### Domain Familiarity

| Level | Multiplier | Description |
|-------|------------|-------------|
| new | 1.25x | New domain requires learning curve |
| familiar | 1.0x | Standard baseline familiarity |
| expert | 0.85x | Expert knowledge speeds delivery |

### Team Size

| Size | Range | Multiplier |
|------|-------|------------|
| solo | 1-1 | 1.0x |
| small | 2-3 | 0.95x |
| medium | 4-6 | 1.1x |
| large | 7-999 | 1.25x |

## Risk Patterns

See full risk assessment patterns below.

### Technical Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| integration complexity | high | 1.3x |
| new technology | medium | 1.4x |
| performance requirements | high | 1.25x |
| security sensitive | critical | 1.35x |

### Scope Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| unclear requirements | high | 1.5x |
| scope creep | medium | 1.2x |
| complex business logic | medium | 1.3x |

### Resource Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| team availability | high | 1.4x |
| skill gaps | medium | 1.35x |

### External Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| vendor dependency | medium | 1.25x |
| regulatory compliance | high | 1.3x |

## Validation Thresholds

### Estimate Bounds

| Metric | Min | Max | Warning |
|--------|-----|-----|--------|
| Story Points (per req) | 1 | 21 | >13 |
| Man-Days (per req) | 0.25 | 20 | >10 |

### Ratio Checks

- **SP to Man-Days ratio**: 0.5 (1 SP ≈ 0.5 days)
- **Tolerance**: ±30%

## Role Split Heuristics

Default effort distribution by task type. AI adjusts based on actual requirements.

| Task Type | BE | FE | QA Manual | Design | Infra | Notes |
|-----------|----|----|-----------|--------|-------|-------|
| Crud | 40% | 34% | 25% | - | - | |
| Authentication | 54% | 21% | 23% | - | - | |
| Authorization | 70% | - | 30% | - | - | |
| File Operations | 35% | 39% | 24% | - | - | |
| Notifications | 33% | 31% | 35% | - | - | |
| Search | 38% | 38% | 23% | - | - | |
| Payments | 50% | 22% | 27% | - | - | |
| Reports | 35% | 35% | 30% | - | - | |
| Ui | - | 48% | 23% | 28% | - | |
| Infrastructure | - | - | - | - | 100% | |
| Testing | - | - | 60% | - | - | |
| Documentation | 60% | - | - | - | - | |
| Api | 54% | 28% | 17% | - | - | |
| Data Management | 30% | 52% | 17% | - | - | |
| Database | 77% | - | 22% | - | - | |
| User Management | 48% | 34% | 17% | - | - | |
| Management | - | - | - | - | - | |

### Management Overhead

- PM: ~10% of total project MD
- BRSE (tiered, default: `middle_with_comtor`): BrSE overhead varies by seniority and comtor support
  - `middle_solo` (1:4): ~25% of dev MD — BrSE middle, no comtor (~25% of dev MD, 1 BrSE per 4 devs)
  - `middle_with_comtor` (1:7): ~14% of dev MD — BrSE middle + 1 comtor (~14% of dev MD, 1 BrSE per 7 devs)
  - `lead_with_comtor` (1:10): ~9% of dev MD — BrSE lead/PSM + 1 comtor (~9% of dev MD, 1 BrSE per 10-12 devs)

## Infrastructure Cloud Pricing

Reference prices for cloud infrastructure estimation. Currency: USD. Last updated: 2026-05-07.

**Reference prices for estimation. Verify with provider calculators before client submission.**

### AWS

Default region: ap-northeast-1

#### Compute

**Fargate**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 0.25 vCPU / 0.5 GB | $14.26 |
| medium | 0.5 vCPU / 1 GB | $26.60 |
| large | 1 vCPU / 2 GB | $53.20 |
| HA Multiplier | - | 2.0x |

**Ec2**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | t4g.micro (2 vCPU / 1 GB) | $8.47 |
| medium | t4g.small (2 vCPU / 2 GB) | $16.94 |
| large | t4g.medium (2 vCPU / 4 GB) | $33.87 |
| HA Multiplier | - | 2.0x |

#### Database

**Aurora**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | db.t4g.medium (2 vCPU / 4 GB) | $82.72 |
| medium | db.r6g.large (2 vCPU / 16 GB) | $219.73 |
| large | db.r6g.xlarge (4 vCPU / 32 GB) | $439.46 |
| HA Multiplier | - | 2.0x |

**Rds Postgres**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | db.t4g.micro (2 vCPU / 1 GB) | $17.81 |
| medium | db.t4g.medium (2 vCPU / 4 GB) | $71.25 |
| HA Multiplier | - | 2.0x |

#### Cache

**Elasticache**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | cache.t4g.micro (2 vCPU / 0.5 GB) | $13.68 |
| medium | cache.t4g.small (2 vCPU / 1.37 GB) | $35.87 |
| large | cache.t4g.medium (2 vCPU / 3.09 GB) | $65.70 |
| HA Multiplier | - | 3.0x |

#### Search

**Opensearch**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | t3.small.search (2 vCPU / 2 GB) | $40.88 |
| medium | t3.medium.search (2 vCPU / 4 GB) | $81.98 |
| HA Multiplier | - | 2.0x |

#### Networking

**Nat Gateway**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | per AZ | $45.38 |

**Alb**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | Application Load Balancer | $22.66 |

**Route53**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | hosted zone + queries | $1.50 |

**Waf**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | Web ACL + rules | $10.60 |

#### Storage

**S3**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | 50 GB standard | $7.65 |

**Cloudfront**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 100 GB transfer | $3.78 |
| medium | 500 GB transfer | $18.90 |
| large | 1 TB transfer | $35.10 |

#### Monitoring

**Cloudwatch**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | dashboards + alarms + logs | $5.71 |

#### Ci Cd

**Codepipeline**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | per pipeline | $1.00 |

**Codebuild**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | general1.small (100 min/mo) | $0.50 |
| medium | general1.medium (300 min/mo) | $1.50 |

### GCP

Default region: asia-northeast1

#### Compute

**Cloud Run**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 0.25 vCPU / 0.5 GB | $12.00 |
| medium | 1 vCPU / 1 GB | $30.00 |
| large | 2 vCPU / 2 GB | $55.00 |

**Gke Autopilot**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 0.25 vCPU / 0.5 GB per pod | $20.00 |
| medium | 0.5 vCPU / 1 GB per pod | $40.00 |

#### Database

**Cloud Sql Postgres**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | db-f1-micro (shared vCPU / 0.6 GB) | $9.37 |
| medium | db-custom-2-8192 (2 vCPU / 8 GB) | $115.00 |
| HA Multiplier | - | 2.0x |

**Firestore**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | pay-per-use (estimated 1M reads/mo) | $6.00 |

#### Cache

**Memorystore Redis**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | M1 (1 GB) | $43.80 |
| medium | M2 (5 GB) | $175.20 |
| HA Multiplier | - | 2.0x |

#### Storage

**Gcs**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | 50 GB standard | $1.30 |

**Cloud Cdn**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 100 GB transfer | $8.50 |
| medium | 500 GB transfer | $38.00 |

#### Monitoring

**Cloud Monitoring**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | free tier + 150 MB logs | $0.00 |

#### Ci Cd

**Cloud Build**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 120 min/day free + overage | $0.00 |
| medium | e2-medium (300 min/mo) | $3.00 |

### AZURE

Default region: japaneast

#### Compute

**App Service**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | B1 (1 vCPU / 1.75 GB) | $13.14 |
| medium | P1v3 (2 vCPU / 8 GB) | $108.04 |

**Container Apps**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 0.25 vCPU / 0.5 GB | $15.00 |
| medium | 0.5 vCPU / 1 GB | $30.00 |

#### Database

**Azure Postgres Flex**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | Burstable B1ms (1 vCPU / 2 GB) | $24.82 |
| medium | GP D2ds_v5 (2 vCPU / 8 GB) | $146.74 |
| HA Multiplier | - | 2.0x |

#### Cache

**Azure Cache Redis**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | C0 Basic (250 MB) | $16.79 |
| medium | C1 Standard (1 GB) | $58.40 |
| HA Multiplier | - | 2.0x |

#### Storage

**Blob**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| flat | 50 GB hot tier | $1.04 |

**Azure Cdn**

| Tier | Spec | Monthly USD |
|------|------|-------------|
| small | 100 GB transfer | $8.13 |
| medium | 500 GB transfer | $35.10 |

### Managed Platforms

**Supabase**

| Plan | Spec | Monthly USD |
|------|------|-------------|
| free | 500 MB DB, 1 GB storage, 50K MAU | Custom |
| pro | 8 GB DB, 100 GB storage, 100K MAU | $25.00 |
| team | dedicated infra, SOC2, priority support | $599.00 |

**Vercel**

| Plan | Spec | Monthly USD |
|------|------|-------------|
| free | hobby use, 100 GB bandwidth | Custom |
| pro | team use, 1 TB bandwidth, analytics | $20.00 |
| enterprise | custom SLA, SSO, dedicated support | Custom |

**Cloudflare**

| Plan | Spec | Monthly USD |
|------|------|-------------|
| free | CDN, DDoS, SSL | Custom |
| pro | WAF, image optimization | $20.00 |
| business | advanced WAF, custom SSL | $200.00 |

**Railway**

| Plan | Spec | Monthly USD |
|------|------|-------------|
| starter | $5 credit, shared resources | $5.00 |
| pro | team features, increased limits | $20.00 |

### Environment Profiles

| Environment | Sizing | HA | Multi-AZ | Notes |
|-------------|--------|----|---------|---------|

| dev | small | No | No | Development environment — single instance, no redundancy |
| staging | small | No | No | Staging environment — mirrors dev sizing |
| production | large | Yes | Yes | Production — HA enabled, multi-AZ for databases and cache |
| uat | small | No | No | UAT environment — same as staging |

