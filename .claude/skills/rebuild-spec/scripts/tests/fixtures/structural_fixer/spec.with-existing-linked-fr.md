# Feature Specification: F002_Profile

**Priority**: P1
**Type**: ui
**Generated**: 2026-05-20

## Overview

User profile management feature for viewing and editing personal information.

## Why This Exists

Allows users to maintain accurate account information.

## Who Uses It

- **User** — views and edits own profile (PERM002_User)

## Business Workflow

```
1. User navigates to /profile → ProfileController@show loads user record
2. User submits edit form → ProfileController@update validates input
3. System updates users table → profile_updated_at refreshed
```

## User Stories

### US001_ViewProfile — View Profile (Priority: P1)

**What happens:** User loads profile page showing current account details.
**Why this priority:** Basic account management capability.
**Independent Test:** GET /profile returns 200 with user data.

**Acceptance Scenarios:**

1. **Given** authenticated user, **When** GET /profile, **Then** 200 + profile data.

**Requirements fulfilled:**
- **FR-010** Load profile data — `GET /profile` via `ProfileController@show`

**Rules enforced:**

### BR-001_OwnProfileOnly
**Linked FR:** FR-010
**Source:** `src/controllers/ProfileController.php:20-30`
**Applies to:** GET /profile, PUT /profile
**Rule:** Users may only view and edit their own profile.

**Pseudocode:**
```text
if request.user.id != profile.user_id:
    return 403 Forbidden
```

**Verification:**
- **SC-010** Cross-user access returns 403 (covers FR-010, BR-001)

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | `users` | id, name, email, avatar_url | Profile subject |

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| ProfileController | `src/controllers/ProfileController.php:1-80` | Profile CRUD |
| User | `src/models/User.php:1-80` | User entity |

## Unresolved Questions

1. **Avatar upload**: Storage backend not confirmed from source.
