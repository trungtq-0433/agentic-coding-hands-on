# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-16

## Overview

Authentication allows registered users to sign in with email and password.
The system validates credentials against the users table and issues a session token.
It touches the User model, sessions table, and the login controller.

## Why This Exists

Users must prove identity before accessing protected resources.
Provides the security boundary for all downstream features.

## Who Uses It

- **Registered User** — signs in to access the application (PERM001_AuthRequired)

## Business Workflow

1. User submits email and password via POST /login → LoginController validates input format.
2. LoginController queries users table WHERE email = ? AND checks bcrypt hash.
3. On match → sessions table INSERT with token, user_id, expires_at.
4. On failure → return HTTP 401 with error message.

## Screen Flow

**See:** ScreenFlow § F001_Auth

| Screen | Route | Purpose |
|--------|-------|---------|
| SCR001_LoginForm | `/login` | User enters credentials |

## Cross-Cutting Logic

### Requirements

| Code | Description | Endpoint/Handler | Verifiable |
|------|-------------|------------------|------------|
| FR-001 | System validates email format | POST /login | yes |

### Business Rules

None.

### State Machines

None.

### Algorithms

None.

### External Integrations

None.

### Verification

- **SC-001** — login succeeds with valid credentials (covers FR-001)

## User Stories

### US001_Login — User logs in (Priority: P0)

**What happens:** Registered user submits valid credentials and receives a session token.
**Why this priority:** Core entry point — no other feature works without authentication.
**Independent Test:** POST /login with valid credentials returns 200 and session token.

**Acceptance Scenarios:**

1. **Given** a registered user with valid credentials, **When** they POST to /login, **Then** they receive HTTP 200 and a session token.
2. **Given** an unregistered email, **When** they POST to /login, **Then** they receive HTTP 401.
3. **Given** a valid email but wrong password, **When** they POST to /login, **Then** they receive HTTP 401.

**Requirements fulfilled:**
- **FR-001** System validates email format — `POST /login` via `LoginController::store`

**Verification:**
- **SC-001** login succeeds with valid credentials (covers FR-001)

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty password submitted | HTTP 422: "The password field is required." |
| Invalid email format | HTTP 422: "The email must be a valid email address." |
| Account locked after 5 failures | HTTP 423: "Account locked. Try again in 15 minutes." |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | users | id, email, password_hash, status | Credential lookup |
| Session | sessions | id, user_id, token, expires_at | Token storage |
| LoginAttempt | login_attempts | id, email, ip, created_at | Brute-force tracking |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F001_Auth | [x] |
| Route List | [route-list.md](../../route-list.md) | POST /login | [ ] |
| Data Model | [data-model.md](../../data-model.md) | User, Session | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR001_LoginForm | [ ] |
| Screen Flow | [screen-flow.md](../../screen-flow.md) | — | [ ] |
| Behavior Logic | [behavior-logic.md](../../behavior-logic.md) | — | [ ] |
| Permissions | [permissions.md](../../permissions.md) | PERM001_AuthRequired | [ ] |
| User Stories | [user-stories.md](../../user-stories.md) | US001_Login | [ ] |

**Rule:** Every code listed MUST exist in its source artifact. Orphan refs = reviewer critical.

## Assumptions

- Password hashing uses bcrypt with cost factor 12.
- Session tokens are 64-byte random hex strings, not JWTs.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| LoginController | `app/Http/Controllers/LoginController.php:1-80` | Credential validation + session creation |
| User | `app/Models/User.php:1-50` | User entity + password hash relation |
| Session | `app/Models/Session.php:1-30` | Session token storage |

**Source:** `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:5-10`

## Unresolved Questions

1. **Token expiry**: Is 24h the intended session lifetime or is it configurable per environment?
