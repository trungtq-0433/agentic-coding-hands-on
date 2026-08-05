# F002_Search — Search

**Priority**: P1
**Type**: ui
**Generated**: 2026-05-16

## Overview

Search lets authenticated users query items by keyword across the items table.
Results are paginated and sorted by relevance score.
Touches the Item model and the SearchController.

## Why This Exists

Users need to locate items quickly without browsing the full catalogue.
Reduces time-to-find and drives engagement with item detail pages.

## Who Uses It

- **Authenticated User** — submits search queries to find items

## Business Workflow

1. User submits GET /search?q=keyword → SearchController reads query param.
2. SearchController queries items table WHERE name LIKE ? OR description LIKE ?.
3. Results sorted by relevance_score DESC, paginated 20 per page.
4. Empty result set returns HTTP 200 with empty array, not 404.

## Screen Flow

**See:** ScreenFlow § F002_Search

| Screen | Route | Purpose |
|--------|-------|---------|
| SCR002_SearchPage | `/search` | User enters query and views results |

## Cross-Cutting Logic

### Requirements

| Code | Description | Endpoint/Handler | Verifiable |
|------|-------------|------------------|------------|
| FR-002 | System paginates results at 20 per page | GET /search | yes |

### Business Rules

None.

### State Machines

None.

### Algorithms

None.

### External Integrations

None.

### Verification

- **SC-002** — search returns paginated results (covers FR-002)

## User Stories

### US002_Search — User searches for items (Priority: P1)

**What happens:** Authenticated user submits a keyword and receives a paginated list of matching items.
**Why this priority:** High-frequency workflow — users search multiple times per session.
**Independent Test:** GET /search?q=test returns 200 with items array and pagination metadata.

**Acceptance Scenarios:**

1. **Given** an authenticated user, **When** they GET /search?q=widget, **Then** they receive HTTP 200 with matching items.
2. **Given** a query matching no items, **When** they GET /search?q=zzznomatch, **Then** they receive HTTP 200 with empty array.
3. **Given** a query with 100 matches, **When** they GET /search?q=item&page=2, **Then** they receive the second page of 20 results.

**Requirements fulfilled:**
- **FR-002** System paginates results at 20 per page — `GET /search` via `SearchController::index`

**Verification:**
- **SC-002** — search returns paginated results (covers FR-002)

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty query string | HTTP 422: "The q field is required." |
| Query longer than 255 chars | HTTP 422: "The q may not be greater than 255 characters." |
| Unauthenticated request | HTTP 401: "Unauthenticated." |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Item | items | id, name, description, relevance_score | Primary search target |
| SearchLog | search_logs | id, user_id, query, created_at | Audit trail |
| Pagination | (virtual) | page, per_page, total | Result windowing |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F002_Search | [x] |
| Route List | [route-list.md](../../route-list.md) | GET /search | [ ] |
| Data Model | [data-model.md](../../data-model.md) | Item | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR002_SearchPage | [ ] |
| Screen Flow | [screen-flow.md](../../screen-flow.md) | — | [ ] |
| Behavior Logic | [behavior-logic.md](../../behavior-logic.md) | — | [ ] |
| Permissions | [permissions.md](../../permissions.md) | — | [ ] |
| User Stories | [user-stories.md](../../user-stories.md) | US002_Search | [ ] |

**Rule:** Every code listed MUST exist in its source artifact. Orphan refs = reviewer critical.

## Assumptions

- Full-text search is not enabled; LIKE queries are sufficient at current scale.
- Relevance score is pre-computed and stored, not calculated at query time.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| SearchController | `app/Http/Controllers/SearchController.php:1-60` | Query execution + pagination |
| Item | `app/Models/Item.php:1-40` | Item entity + search scope |
| SearchLog | `app/Models/SearchLog.php:1-25` | Audit logging |

## Unresolved Questions

1. **Relevance scoring**: How is relevance_score computed — manual curation or automated?
