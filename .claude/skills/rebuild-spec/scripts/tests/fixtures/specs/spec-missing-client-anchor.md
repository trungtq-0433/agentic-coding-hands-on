# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-25

## Overview

Authentication allows registered users to sign in with email and password.

## Why This Exists

Users must prove identity before accessing protected resources.

## Who Uses It

- **Registered User** — signs in to access the application

## Business Workflow

1. User submits email and password via POST /login → LoginController validates input.
2. LoginController queries users table WHERE email = ? AND checks password hash.
3. On match → sessions table INSERT with token; on failure → return HTTP 401.

## Screen Flow

**See:** ScreenFlow § F001_Auth

- SCR001_LoginForm — `/login` (atomic)

## Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

## Cross-Cutting Logic

### Requirements

None.

### Business Rules

None.

### Decision Logic

None.

### State Machines

None.

### Algorithms

None.

### External Integrations

None.

### Verification

None.

<!-- **Client behavior:** anchor intentionally omitted to trigger FeatureSpec.missing_client_behavior_anchor -->

## User Stories

### US001_Login — User logs in (Priority: P0)

**What happens:** Registered user submits valid credentials and receives a session token.
**Why this priority:** Core entry point — no other feature works without authentication.
**Independent Test:** POST /login with valid credentials returns 200 and session token.

**Acceptance Scenarios:**

1. **Given** a registered user with valid credentials, **When** they POST to /login, **Then** they receive HTTP 200.
2. **Given** an unregistered email, **When** they POST to /login, **Then** they receive HTTP 401.
3. **Given** a valid email but wrong password, **When** they POST to /login, **Then** they receive HTTP 401.

**Requirements fulfilled:**
- **FR-001** System validates credentials — `POST /login` via `LoginController::store`

**Verification:**
- **SC-001** login succeeds with valid credentials (covers FR-001)

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty password submitted | HTTP 422: "The password field is required." |
| Invalid email format | HTTP 422: "The email must be a valid email address." |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | users | id, email, password_hash, status | Credential lookup |
| Session | sessions | id, user_id, token, expires_at | Token storage |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F001_Auth | [x] |
| Route List | [route-list.md](../../route-list.md) | POST /login | [ ] |
| Data Model | [data-model.md](../../data-model.md) | User | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR001_LoginForm | [ ] |

## Assumptions

- Password hashing uses bcrypt with cost factor 12.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| authenticate | `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:5-10` | Credential validation logic |

## Unresolved Questions

1. **Token expiry**: Is 24h the intended session lifetime or is it configurable?
