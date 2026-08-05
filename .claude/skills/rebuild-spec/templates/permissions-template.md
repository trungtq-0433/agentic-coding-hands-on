# Permissions

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

> **Curated, plain-language view.** This document is for PM, BA, and client audiences who
> need to understand access without reading raw codes. The raw PERM### matrix lives at
> [permissions-matrix.md](../generated/permissions-matrix.md). Derive this prose FROM that matrix.
> No PERM### codes and no matrix tables belong here.

## Authorization System Type

**System Type**: {AUTH_SYSTEM_TYPE}

The primary authorization system used by this project:

| System Type | Description |
|-------------|-------------|
| `rbac` | Role-Based Access Control — roles (admin, user, manager) drive access |
| `abac` | Attribute-Based Access Control — policies on attributes (department, owner, status) |
| `acl` | Access Control List — explicit per-user permissions |
| `ownership` | Resource Ownership — owner_id / created_by / can_edit rules |
| `hybrid` | Mixed — roles combined with ownership checks |
| `other` | Custom permission logic |

**Identified Roles**:
- {ROLE_1}
- {ROLE_2}
- {ROLE_3}

## Curated View

{Plain-language summary of who can do what in this system. No PERM### codes.}

- **{Role name}** can {plain-language action list}.
- **{Role name}** can {plain-language action list} but cannot {restriction}.
- **{Role name}** can only {limited plain-language action}.

## Access Boundaries

{Describe the high-level access boundaries between roles — what separates an admin from a
regular user, what ownership means for resource access, etc. Write for a PM/BA audience.}

## Special Conditions

{Describe any conditional access rules in plain language — time-based restrictions, IP-based
rules, feature flags that gate functionality, environment-specific behavior, etc. If none,
write "No special conditions identified." Raw per-gate detail belongs in
[permissions-matrix.md](../generated/permissions-matrix.md).}
