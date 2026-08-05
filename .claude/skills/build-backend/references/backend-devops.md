# Backend DevOps Practices

How backends get shipped and watched in production — pipelines, containers, rollout strategies, and observability (2025).

## Deployment Strategies

### Blue-Green Deployment

**The idea:** run two mirror environments — Blue is live, Green holds the new build

```
Production Traffic → Blue (v1.0)
                     Green (v2.0) ← Deploy & Test

Switch:
Production Traffic → Green (v2.0)
                     Blue (v1.0) ← Instant rollback available
```

**In its favor:**
- Nobody sees downtime
- Roll back in an instant
- Exercise the whole environment before you flip the switch

**The cost:**
- You're paying for two full stacks
- Database migrations get tricky

### Canary Deployment

**The idea:** let the new version in slowly (1% → 5% → 25% → 100%)

```bash
# Kubernetes canary deployment
kubectl set image deployment/api api=myapp:v2
kubectl rollout pause deployment/api  # Pause at initial replicas

# Monitor metrics, then continue
kubectl rollout resume deployment/api
```

**In its favor:**
- Keeps the blast radius small
- Catches trouble while it's still small
- Real users tell you the truth early

**The cost:**
- You need monitoring in place
- The rollout takes longer to finish

### Feature Flags — Letting Risk Out a Little at a Time

**Why it pays off:** 90% fewer deployment failures when combined with canary

```typescript
import { LaunchDarkly } from 'launchdarkly-node-server-sdk';

const client = LaunchDarkly.init(process.env.LD_SDK_KEY);

// Check feature flag
const showNewCheckout = await client.variation('new-checkout', user, false);

if (showNewCheckout) {
  return newCheckoutFlow(req, res);
} else {
  return oldCheckoutFlow(req, res);
}
```

**Where they earn their keep:**
- Rolling a feature out to users in stages
- A/B testing
- Killing a misbehaving feature instantly
- Letting you deploy code without releasing it

## Containerization with Docker

### Multi-Stage Builds — Shrinking the Final Image

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
WORKDIR /app

# Copy only necessary files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package.json ./

# Security: Run as non-root
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001
USER nodejs

EXPOSE 3000
CMD ["node", "dist/main.js"]
```

**What you get:**
- Images that slim right down (50-90% reduction)
- Deploys that move quicker
- Less surface for an attacker to grab

### Docker Compose (Local Development)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres-data:
```

## Kubernetes Orchestration

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myregistry/api:v1.0.0
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## CI/CD Pipelines

### GitHub Actions (Modern, Integrated)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Snyk scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: Container scan
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker scan myapp:${{ github.sha }}

  deploy:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Build and push Docker image
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api api=ghcr.io/${{ github.repository }}:${{ github.sha }}
          kubectl rollout status deployment/api
```

## Monitoring & Observability

### The Three Things Observability Rests On

**1. Metrics (Prometheus + Grafana)**

```typescript
import { Counter, Histogram, register } from 'prom-client';

// Request counter
const httpRequestTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status'],
});

// Response time histogram
const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route'],
  buckets: [0.1, 0.5, 1, 2, 5],
});

// Middleware to track metrics
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestTotal.inc({ method: req.method, route: req.route?.path, status: res.statusCode });
    httpRequestDuration.observe({ method: req.method, route: req.route?.path }, duration);
  });

  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

**2. Logs (ELK Stack - Elasticsearch, Logstash, Kibana)**

```typescript
import winston from 'winston';
import { ElasticsearchTransport } from 'winston-elasticsearch';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new ElasticsearchTransport({
      level: 'info',
      clientOpts: { node: 'http://localhost:9200' },
      index: 'logs',
    }),
  ],
});

// Structured logging
logger.info('User created', {
  userId: user.id,
  email: user.email,
  ipAddress: req.ip,
  userAgent: req.headers['user-agent'],
});
```

**3. Traces (Jaeger/OpenTelemetry)**

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';

const sdk = new NodeSDK({
  traceExporter: new JaegerExporter({
    endpoint: 'http://localhost:14268/api/traces',
  }),
  serviceName: 'api-service',
});

sdk.start();

// Traces automatically captured for HTTP requests, database queries, etc.
```

### Health Checks

```typescript
// Liveness probe - Is the app running?
app.get('/health/liveness', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: Date.now() });
});

// Readiness probe - Is the app ready to serve traffic?
app.get('/health/readiness', async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    externalAPI: await checkExternalAPI(),
  };

  const isReady = Object.values(checks).every(Boolean);
  res.status(isReady ? 200 : 503).json({
    status: isReady ? 'ready' : 'not ready',
    checks,
  });
});

async function checkDatabase() {
  try {
    await db.query('SELECT 1');
    return true;
  } catch {
    return false;
  }
}
```

## Secrets Management

### HashiCorp Vault

```bash
# Store secret
vault kv put secret/myapp/db password=super-secret

# Retrieve secret
vault kv get -field=password secret/myapp/db
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  url: postgresql://user:pass@host:5432/db
---
# Reference in deployment
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: url
```

## Infrastructure as Code (Terraform)

```hcl
# main.tf
resource "aws_db_instance" "main" {
  identifier        = "myapp-db"
  engine            = "postgres"
  engine_version    = "15.3"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  username          = "admin"
  password          = var.db_password

  backup_retention_period = 7
  skip_final_snapshot     = false
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "myapp-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
}
```

## DevOps Checklist

- [ ] A CI/CD pipeline stood up (GitHub Actions/GitLab CI/Jenkins)
- [ ] Docker multi-stage builds in place
- [ ] Kubernetes deployment manifests written
- [ ] A rollout strategy picked — blue-green or canary
- [ ] Feature flags wired in (LaunchDarkly/Unleash)
- [ ] Health checks answering (liveness + readiness probes)
- [ ] Metrics flowing into Prometheus + Grafana
- [ ] Logs landing in the ELK Stack or its equivalent
- [ ] Traces stitched together with Jaeger/OpenTelemetry
- [ ] Secrets kept out of code (Vault/AWS Secrets Manager)
- [ ] Infrastructure expressed as code (Terraform/CloudFormation)
- [ ] Autoscaling switched on
- [ ] A backup and disaster-recovery plan that's been thought through

## Resources

- **Kubernetes:** https://kubernetes.io/docs/
- **Docker:** https://docs.docker.com/
- **Prometheus:** https://prometheus.io/docs/
- **OpenTelemetry:** https://opentelemetry.io/docs/
- **Terraform:** https://www.terraform.io/docs/
