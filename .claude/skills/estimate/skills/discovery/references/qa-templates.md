# Q&A Templates for Discovery

These templates **guide AI question generation** — adapt to actual document content. Not rigid forms.

## Q&A Format

```markdown
### Q{N}: [{Category}] {Question}
**Context:** {Why asking — reference what spec says/omits}
**Options:** {Suggested answers if applicable, or "Free text"}
**Answer:** _______________
**Priority:** {Critical|High|Medium} — {brief reason}
```

## Priority Rules

| Priority | Criteria | Examples |
|----------|----------|---------|
| **Critical** | Blocks architecture or platform decisions | Tech stack, platforms, auth method, hosting |
| **High** | Significantly affects effort calculation | Feature scope, integration complexity, data volume |
| **Medium** | Improves estimation accuracy | UI preferences, specific behaviors, edge cases |

## Feature-Type Question Templates

### Authentication
- [Scope] Existing auth service to integrate, or build from scratch?
- [Technical] Social login providers needed? (Google, Apple, LINE, etc.)
- [Technical] MFA required? Which methods? (SMS, authenticator app, email)
- [Functional] Session management: JWT stateless or server-side sessions?
- [Functional] Password recovery flow requirements?

### CRUD Screens
- [Functional] Which data fields are required vs optional?
- [Functional] Validation rules (format, uniqueness, cross-field)?
- [Scope] Bulk operations needed? (import, export, batch delete)
- [Functional] Soft delete or hard delete? Audit trail?
- [Technical] Real-time updates needed (WebSocket) or standard refresh?

### File Operations
- [Technical] Maximum file size? Allowed file types?
- [Technical] Storage service: S3, GCS, Azure Blob, or on-premise?
- [Functional] Image processing needed? (resize, crop, thumbnail, watermark)
- [Scope] CDN delivery for static assets?
- [Functional] File versioning or overwrite?

### Search
- [Scope] Search scope: which entities/content types are searchable?
- [Technical] Full-text engine needed (Elasticsearch, Algolia) or DB search?
- [Functional] Filters and facets required? Which fields?
- [Functional] Auto-suggest / autocomplete needed?
- [Functional] Search result ranking/relevance tuning?

### Notifications
- [Scope] Channels: email, push, SMS, in-app, LINE, Slack?
- [Functional] Notification templates: who designs/manages them?
- [Functional] Frequency controls / digest options?
- [Functional] User opt-out / preference settings?
- [Technical] Real-time delivery or batch?

### Payments
- [Technical] Payment gateway: Stripe, PayPay, GMO, SePay, other?
- [Functional] Subscription/recurring billing model?
- [Functional] Refund flow: automatic or manual approval?
- [Scope] Tax calculation requirements? Invoicing?
- [Technical] PCI compliance scope? (redirect vs embedded form)

### Reports / Dashboard
- [Functional] Data sources and refresh frequency? (real-time, daily, on-demand)
- [Functional] Export formats: CSV, Excel, PDF?
- [Scope] Number of distinct report types / dashboard views?
- [Technical] Charting library preference? (Chart.js, D3, Recharts)
- [Functional] Role-based dashboard views?

### API Integrations
- [Technical] Existing APIs to integrate? Documentation available?
- [Technical] API authentication: API key, OAuth, custom?
- [Technical] Rate limits or quota constraints?
- [Scope] Webhook support needed? (inbound, outbound, or both)
- [Functional] Error handling / retry strategy for third-party failures?

### Infrastructure
- [Technical] Hosting preference: AWS, GCP, Azure, on-premise?
- [Technical] Region/data residency requirements?
- [Scope] Environments needed: dev, staging, production?
- [Technical] CI/CD pipeline: existing or build new?
- [Technical] Backup and disaster recovery requirements?

## Cross-Cutting Question Templates

### Scope
- [Scope] Target platforms: web, iOS, Android, desktop?
- [Scope] Project phases / MVP scope vs full scope?
- [Scope] Expected timeline or deadline constraints?
- [Scope] Team composition constraints? (available roles, headcount)
- [Scope] Multi-tenant or single-tenant architecture?

### Technical
- [Technical] Tech stack: frontend framework, backend language, database?
- [Technical] Existing codebase to extend, or greenfield?
- [Technical] Monorepo or polyrepo? Monolith or microservices?
- [Technical] Browser/OS version support requirements?

### Non-Functional
- [Technical] Performance targets: response time, concurrent users?
- [Scope] Internationalization (i18n) — which languages?
- [Scope] Accessibility requirements (WCAG level)?
- [Technical] SEO requirements?
- [Technical] Logging, monitoring, observability requirements?

### Data
- [Technical] Data migration from existing system? Volume?
- [Technical] Data compliance: GDPR, HIPAA, APPI, PDPA?
- [Scope] Expected data volume / growth rate?
- [Technical] Data backup frequency and retention policy?
