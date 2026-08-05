# Delivery & Operations — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}

- **CI/CD provider + pipeline stages:** {GitHub Actions | GitLab CI | Jenkins | …} (cite `{workflow-path:line}`)
- **Testing story:**
  - Frameworks present: {jest | vitest | pytest | go test | …} (cite `{path:line}`)
  - Coverage file: `{path}` or `(none)`
  - Test directory layout: `{path}`
- **Containerization:** {Dockerfile, docker-compose, Helm, k8s manifests, Terraform} (cite `{path:line}`)
- **Observability signals:**
  - Logging library: {pino | winston | structlog | logrus | …} (cite `{path:line}`)
  - Metrics endpoint: `{route}` or `(none)`
  - Tracing SDK: {OTel | Datadog | New Relic | …} (cite `{path:line}` or `(none)`)
  - Error reporting: {Sentry | Bugsnag | …} (cite `{path:line}` or `(none)`)

<!-- Total length under 120 lines. Snapshot only — no narration. -->
