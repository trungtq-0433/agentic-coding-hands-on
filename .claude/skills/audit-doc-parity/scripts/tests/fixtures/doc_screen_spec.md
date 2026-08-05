# Screen Spec — Order Export

## User Flow

### Branches

| Decision Point | Condition | Outcome |
|----------------|-----------|---------|
| Auth check | user is admin | show export button |
| Auth check | user is not admin | redirect to 403 |
| Format select | CSV selected | download CSV |

## Data Inventory

| Binding | Source | Format | Empty behavior | Cross ref |
|---------|--------|--------|----------------|-----------|
| order.id | API /orders | integer | hide row | FR-001 |
| order.total | API /orders | currency | show 0.00 | FR-001 |

## UI States

| State | Trigger | Visual behavior | User action |
|-------|---------|-----------------|-------------|
| loading | page open | spinner visible | wait |
| ready | data loaded | table visible | interact |
| error | API failure | error banner | retry |

## Validation

| Field | Required | Constraints | Error message | Async check |
|-------|----------|-------------|---------------|-------------|
| email | yes | format:email | Invalid email | no |
| date_from | no | date | Invalid date | no |
