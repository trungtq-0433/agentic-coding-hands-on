# F999_Orphan — Orphan Feature

**Priority**: P3
**Type**: ui
**Generated**: 2026-05-16

## Overview

This is an orphan feature folder not declared in canonical or feature-list.
It exists only to trigger the existence.orphan_folder warning rule.

## Why This Exists

N/A — inferred from code; domain confirmation needed.

## Who Uses It

- **Developer** — test fixture only

## Business Workflow

1. No real workflow.
2. Placeholder step two.
3. Placeholder step three.

## Screen Flow

N/A — background feature; no user-facing screen flow.

## Cross-Cutting Logic

### Requirements

None.

### Business Rules

None.

### State Machines

None.

### Algorithms

None.

### External Integrations

None.

### Verification

None.

## User Stories

### US999_Orphan — Orphan story (Priority: P3)

**What happens:** Nothing — this is a test fixture.
**Why this priority:** Lowest priority; test only.
**Independent Test:** Not applicable.

**Acceptance Scenarios:**

1. **Given** this is a fixture, **When** nothing happens, **Then** nothing happens.
2. **Given** this is a fixture, **When** validated, **Then** orphan warning fires.
3. **Given** orphan folder exists, **When** validator runs, **Then** warning is emitted.

**Requirements fulfilled:**
- **FR-999** Test fixture — `GET /orphan` via `OrphanController::index`

**Verification:**
- **SC-999** orphan folder triggers warning (covers FR-999)

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Orphan folder present | Warning emitted by existence validator |
| Canonical does not list F999 | existence.orphan_folder rule fires |
| Feature list also absent | Same warning via fallback path |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Orphan | orphans | id, name | Test only |
| Fixture | fixtures | id, type | Test only |
| Placeholder | placeholders | id, value | Test only |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F999_Orphan | [x] |
| Route List | [route-list.md](../../route-list.md) | — | [ ] |
| Data Model | [data-model.md](../../data-model.md) | — | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | — | [ ] |
| Screen Flow | [screen-flow.md](../../screen-flow.md) | — | [ ] |
| Behavior Logic | [behavior-logic.md](../../behavior-logic.md) | — | [ ] |
| Permissions | [permissions.md](../../permissions.md) | — | [ ] |
| User Stories | [user-stories.md](../../user-stories.md) | US999_Orphan | [ ] |

**Rule:** Every code listed MUST exist in its source artifact. Orphan refs = reviewer critical.

## Assumptions

- This is a synthetic fixture — no real assumptions apply.
- Validator treats undeclared folders as warnings, not critical errors.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| OrphanController | `app/Http/Controllers/OrphanController.php:1-10` | Placeholder |
| Orphan | `app/Models/Orphan.php:1-10` | Placeholder entity |
| Fixture | `app/Models/Fixture.php:1-10` | Placeholder model |

## Unresolved Questions

1. **Orphan cleanup**: Should orphan folders be auto-deleted on next Wave 5 run?
