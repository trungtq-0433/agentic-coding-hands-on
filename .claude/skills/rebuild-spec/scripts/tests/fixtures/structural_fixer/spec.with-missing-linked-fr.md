# Feature Specification: F001_Auth

**Priority**: P0
**Type**: mixed
**Generated**: 2026-05-20

## Overview

Authentication feature handling login, registration, and session management.

## Why This Exists

Provides secure access control for all platform users.

## Who Uses It

- **Admin** — manages user accounts (PERM001_Admin)
- **User** — logs in and manages own session

## Business Workflow

```
1. User submits credentials → AuthController@login validates input
2. System checks password hash → users.password_hash column
3. On success → session token generated → sessions table insert
4. On failure → failed_logins counter incremented
```

## User Stories

### US001_Login — User Login (Priority: P0)

**What happens:** User submits email and password; system validates and creates session.
**Why this priority:** Core access gate for all platform features.
**Independent Test:** POST /login with valid credentials returns 200 + session token.

**Acceptance Scenarios:**

1. **Given** valid credentials, **When** POST /login, **Then** 200 + token returned.
2. **Given** invalid password, **When** POST /login, **Then** 401 returned.

**Requirements fulfilled:**
- **FR-001** Validate credentials — `POST /login` via `AuthController@login`

**Rules enforced:**

### BR-001_MaxLoginAttempts
**Source:** `src/controllers/AuthController.php:45-60`
**Applies to:** POST /login
**Rule:** Block login after 5 consecutive failed attempts within 15 minutes.

**Pseudocode:**
```text
if failed_attempts >= 5 and last_attempt within 15min:
    return 429 Too Many Requests
```

**Verification:**
- **SC-001** Locked account returns 429 (covers FR-001, BR-001)

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | `users` | id, email, password_hash | Authentication subject |
| Session | `sessions` | id, user_id, token, expires_at | Active session tracking |
| FailedLogin | `failed_logins` | user_id, attempted_at | Brute-force detection |

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| AuthController | `src/controllers/AuthController.php:1-120` | Login/logout handlers |
| User | `src/models/User.php:1-80` | User entity + auth relations |
| Session | `src/models/Session.php:1-40` | Session entity |

## Unresolved Questions

1. **Session expiry**: Default TTL not confirmed from source code.
