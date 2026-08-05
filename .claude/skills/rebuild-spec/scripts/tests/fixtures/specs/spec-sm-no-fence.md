# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-18

## Overview

Authentication allows registered users to sign in.

## Why This Exists

Users must prove identity.

## Who Uses It

- **Registered User** — signs in

## Business Workflow

1. User submits credentials.
2. Validate.
3. Issue token.

## Screen Flow

**See:** ScreenFlow § F001_Auth

## Cross-Cutting Logic

### Requirements

None.

### Business Rules

None.

### State Machines

See SM-001 below.

### SM-001_LoginFlow

The login state machine governs session transitions but the diagram fence has
been forgotten — this is the failure case that sm_mermaid must still catch.

### Algorithms

None.

### External Integrations

None.

### Verification

None.

## User Stories

### US001_Login — User logs in (Priority: P0)

**What happens:** Valid credentials return token.
**Why this priority:** Core entry point.
**Independent Test:** POST /login returns 200.

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty password | HTTP 422 |

## Key Entities

| Entity | Table | Purpose |
|--------|-------|---------|
| User | users | Credential lookup |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F001_Auth | [x] |
| Route List | [route-list.md](../../route-list.md) | — | [ ] |
| Data Model | [data-model.md](../../data-model.md) | — | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR001_LoginForm | [ ] |
| Screen Flow | [screen-flow.md](../../screen-flow.md) | — | [ ] |
| Behavior Logic | [behavior-logic.md](../../behavior-logic.md) | — | [ ] |
| Permissions | [permissions.md](../../permissions.md) | — | [ ] |
| User Stories | [user-stories.md](../../user-stories.md) | — | [ ] |

**Rule:** Every code listed MUST exist in its source artifact. Orphan refs = reviewer critical.

## Assumptions

- bcrypt hashing.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| LoginController | `app/Http/Controllers/LoginController.php:1-80` | Validation |

## Unresolved Questions

None.
