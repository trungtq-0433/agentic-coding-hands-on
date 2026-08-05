# Feature Specification: F002_Profile

**Priority**: P1
**Type**: ui
**Generated**: 2026-05-20

## Overview

User profile management for viewing and editing personal data.

## Why This Exists

Allows users to maintain accurate account information.

## Who Uses It

- **User** — edits own profile (PERM002_User)

## Business Workflow

```
1. User navigates to /profile → ProfileController@show
2. User submits edit form → ProfileController@update
3. System updates users table
```

## User Stories

### US001_ViewProfile — View Profile (Priority: P1)

**What happens:** User views current profile data.
**Why this priority:** Basic account management.
**Independent Test:** GET /profile returns 200 + user data.

**Acceptance Scenarios:**

1. **Given** authenticated user, **When** GET /profile, **Then** 200 + data.

**Requirements fulfilled:**
- **FR-010** Load profile — `GET /profile` via `ProfileController@show`

**Rules enforced:**

### BR-001_OwnProfileOnly
**Linked FR:** FR-010
**Source:** `src/ProfileController.php:20-30`
**Applies to:** GET /profile
**Rule:** Users may only view own profile.

**Pseudocode:**
```text
if request.user.id != profile.user_id: return 403
```

**Verification:**
- **SC-010** Cross-user returns 403 (covers FR-010, BR-001)

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | `users` | id, name, email | Profile subject |
| Avatar | `avatars` | user_id, url | Profile image |
| Preference | `preferences` | user_id, key, value | User settings |

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| ProfileController | `src/ProfileController.php:1-80` | Profile CRUD |
| User | `src/models/User.php:1-80` | User entity |
| Avatar | `src/models/Avatar.php:1-30` | Avatar entity |

## Unresolved Questions

1. **Avatar storage**: Backend not confirmed from source.
