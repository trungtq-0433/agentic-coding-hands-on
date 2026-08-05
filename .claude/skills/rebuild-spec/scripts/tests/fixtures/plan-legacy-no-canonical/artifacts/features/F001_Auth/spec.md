# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-16

## Overview

Authentication allows registered users to sign in with email and password.

## Why This Exists

Users must prove identity before accessing protected resources.

## Who Uses It

- **Registered User** — signs in to access the application

## Business Workflow

1. User submits email and password via POST /login.
2. LoginController validates credentials against users table.
3. On match, session token is issued and stored.
4. On failure, HTTP 401 is returned.

## Screen Flow

**See:** ScreenFlow § F001_Auth

| Screen | Route | Purpose |
|--------|-------|---------|
| SCR001_LoginForm | `/login` | User enters credentials |

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

### US001_Login — User logs in (Priority: P0)

**What happens:** Registered user submits valid credentials and receives a session token.
**Why this priority:** Core entry point for all protected features.
**Independent Test:** POST /login with valid credentials returns 200 and session token.

**Acceptance Scenarios:**

1. **Given** a registered user, **When** they POST valid credentials, **Then** they receive HTTP 200.
2. **Given** invalid credentials, **When** they POST to /login, **Then** they receive HTTP 401.
3. **Given** empty password, **When** they POST to /login, **Then** they receive HTTP 422.

**Requirements fulfilled:**
- **FR-001** Validates credentials — `POST /login` via `LoginController::store`

**Verification:**
- **SC-001** login succeeds with valid credentials (covers FR-001)

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty password | HTTP 422: "The password field is required." |
| Invalid email format | HTTP 422: "The email must be a valid email address." |
| Unknown email | HTTP 401: "Invalid credentials." |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | users | id, email, password_hash | Credential lookup |
| Session | sessions | id, user_id, token | Token storage |
| LoginAttempt | login_attempts | id, email, ip | Brute-force tracking |

## Related Artifacts

- **Screens** (from ScreenList): SCR001_LoginForm
- **User Stories** (from UserStories): US001_Login
- **Routes** (from RouteList): POST /login
- **Data Models** (from DataModel): User
- **Background Logic** (from BackgroundLogic): none
- **Permissions** (from Permissions): none

## Spec Documents

- [x] [System Overview](docs/specs/system-overview.md)
- [x] [Feature List](docs/specs/feature-list.md) — F001_Auth

## Assumptions

- Password hashing uses bcrypt.
- Sessions expire after 24 hours.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| LoginController | `app/Http/Controllers/LoginController.php:1-80` | Credential validation |
| User | `app/Models/User.php:1-50` | User entity |
| Session | `app/Models/Session.php:1-30` | Session token storage |

## Unresolved Questions

1. **Token expiry**: Is 24h session lifetime configurable per environment?
