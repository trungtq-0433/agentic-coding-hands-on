# AWS (Amplify / S3 / ECS)

## Amplify Hosting
```bash
npm install -g @aws-amplify/cli
amplify configure
amplify init
amplify publish
```

### Config: amplify.yml
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

### Free Tier (12 months)
1000 build min/mo, 15GB storage, 15GB bandwidth.
Once that lapses: $0.01/build min, $0.023/GB storage, $0.15/GB served.

## S3 Static Hosting
```bash
aws s3 sync ./dist s3://BUCKET_NAME --delete
aws s3 website s3://BUCKET_NAME --index-document index.html --error-document error.html
```

### Free Tier (12 months)
5GB storage, 20K GET, 2K PUT requests.

## ECS Fargate
```bash
aws ecs update-service --cluster CLUSTER --service SERVICE --force-new-deployment
```
Driven by `task-definition.json`. No free tier here.

## Detection
- `amplify.yml`, `buildspec.yml` → Amplify
- S3 bucket policy JSON → S3
- `task-definition.json` → ECS

## Best For
- Amplify: static sites paired with serverless backends
- S3 + CloudFront: the cheapest way to serve static at scale
- ECS: enterprise-grade containerized workloads
