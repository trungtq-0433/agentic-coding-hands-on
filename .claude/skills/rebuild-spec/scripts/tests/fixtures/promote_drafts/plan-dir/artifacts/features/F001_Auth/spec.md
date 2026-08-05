# Feature Specification: F001_Auth

**Priority**: P0
**Type**: mixed
**Generated**: 2026-05-20

## Overview

Authentication feature for login and session management.

## Why This Exists

Core access control for the platform.

## Who Uses It

- **User** — logs in (PERM001_User)

## Business Workflow

```
1. User submits credentials → AuthController@login
2. System validates → users table lookup
3. On success → session created
```

## User Stories

### US001_Login — Login (Priority: P0)

**What happens:** User authenticates.
**Why this priority:** Core gate.
**Independent Test:** POST /login returns token.

**Acceptance Scenarios:**

1. **Given** valid creds, **When** POST /login, **Then** 200 + token.

**Requirements fulfilled:**
- **FR-001** Validate credentials — `POST /login` via `AuthController@login`

**Rules enforced:**

### BR-001_MaxAttempts
**Linked FR:** FR-001
**Source:** `src/AuthController.php:45-60`
**Applies to:** POST /login
**Rule:** Block after 5 failed attempts.

**Pseudocode:**
```text
if attempts >= 5: return 429
```

**Verification:**
- **SC-001** Lockout returns 429 (covers FR-001, BR-001)

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | `users` | id, email | Auth subject |
| Session | `sessions` | id, token | Active sessions |
| FailedLogin | `failed_logins` | user_id | Brute-force tracking |

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| AuthController | `src/AuthController.php:1-120` | Auth handlers |
| User | `src/models/User.php:1-80` | User entity |
| Session | `src/models/Session.php:1-40` | Session entity |

## Unresolved Questions

1. **Token TTL**: Default not confirmed from source.
