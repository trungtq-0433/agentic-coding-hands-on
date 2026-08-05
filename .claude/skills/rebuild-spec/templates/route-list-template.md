# Route List

**Project**: {PROJECT_NAME}
**Generated**: {DATE}

## Backend Routes

> **Completeness Contract:** emit exactly ONE row per leaf route (HTTP method + concrete path). Expand framework resource macros (Rails `resources :x` → 7 RESTful rows). FORBIDDEN: resource-summary tables (`| Resource | Actions |`), approximation markers (`~N`, `(+nhiều)`, `see routes.rb`, `etc.`), wildcard paths (`/x/*`). Scout counts are estimates, not authority.

> **Code Column Contract:** `Code` is mandatory going forward — `ROUTE###`, contiguous and global across this one file (same shape as `SCR###`/`F###`). `Owner F###` carries the bare feature code that claims the route, or `—` when the route cannot be attributed to a single feature (shared/infra routes). Rare shared routes may list comma-separated multi-owners, e.g. `F001, F003`.

{POPULATED_BY_FRAGMENTS}

### File: {ROUTE_FILE}

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /api/resource | ROUTE001 | F001 | ResourceController@index | auth |
| POST | /api/resource | ROUTE002 | F001 | ResourceController@store | auth |
| GET | /api/resource/:id | ROUTE003 | F001 | ResourceController@show | auth |
| PUT | /api/resource/:id | ROUTE004 | F001 | ResourceController@update | auth |
| DELETE | /api/resource/:id | ROUTE005 | — | ResourceController@destroy | auth |

## Frontend Routes/Pages

### File: {PAGE_FILE}

| Path | Component | Route Name |
|------|-----------|------------|
| / | HomePage | home |
| /resource | ResourceListPage | resource-list |
| /resource/:id | ResourceDetailPage | resource-detail |

## Summary

| Category | Count |
|----------|-------|
| Backend Routes | {N} |
| Frontend Pages | {N} |
| Total | {N} |
