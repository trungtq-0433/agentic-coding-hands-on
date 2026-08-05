# API Map

## Endpoints by Domain

{POPULATED_BY_FRAGMENTS}

{Group routes by domain/resource area. One table per domain group.}

### {Domain Name}

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| {METHOD} | `{/path/to/resource}` | `{Controller::method}` | {what this endpoint does} |
| {METHOD} | `{/path/to/resource/:id}` | `{Controller::method}` | {what this endpoint does} |

### {Domain Name}

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| {METHOD} | `{/path/to/resource}` | `{Controller::method}` | {what this endpoint does} |

## Background Jobs

{BL### inventory restated with job scheduling and trigger info.}

| Code | Name | Type | Trigger | Schedule |
|------|------|------|---------|----------|
| {BL001_CODE} | {BL001_NAME} | {TYPE} | {TRIGGER} | {cron expression or "on-demand"} |
| {BL002_CODE} | {BL002_NAME} | {TYPE} | {TRIGGER} | {cron expression or "on-demand"} |

## Webhooks / External Calls

{INT-type entries from technical specs — outgoing integrations and incoming webhooks.}

| Direction | Target / Source | Event / Endpoint | Description |
|-----------|----------------|------------------|-------------|
| outgoing | {external service name} | `{endpoint or topic}` | {what data is sent and when} |
| incoming | {external service name} | `{/webhook/path}` | {what event triggers this and what happens} |
