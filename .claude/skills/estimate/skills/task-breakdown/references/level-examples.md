# Breakdown Level Examples

Three granularity levels for task breakdown output. Choose based on audience and purpose.

## L1 — Epic Overview

Quick summary for stakeholder/client review. Shows scope at a glance.

### JSON

```json
{
  "project_name": "E-Commerce Platform",
  "breakdown_level": 1,
  "language": "en",
  "source": "pre-estimate",
  "source_file": "spec.pdf",
  "generated_date": "2026-04-27",
  "active_roles": ["fe", "be", "qa_manual"],
  "role_names": { "fe": "Frontend", "be": "Backend", "qa_manual": "QA (Manual)" },
  "epics": [
    { "id": "E1", "name": "Authentication", "description": "User login, registration, OAuth", "total_md": null },
    { "id": "E2", "name": "Product Catalog", "description": "Product listing, search, filters", "total_md": null },
    { "id": "E3", "name": "Shopping Cart & Checkout", "description": "Cart management, payment integration", "total_md": null }
  ]
}
```

### Rendered Markdown

```markdown
# Task Breakdown: E-Commerce Platform

**Date**: 2026-04-27 | **Source**: pre-estimate | **Level**: L1

---

## E1: Authentication
User login, registration, OAuth
Stories: 0 | Roles: Frontend, Backend, QA (Manual)

## E2: Product Catalog
Product listing, search, filters
Stories: 0 | Roles: Frontend, Backend, QA (Manual)

## E3: Shopping Cart & Checkout
Cart management, payment integration
Stories: 0 | Roles: Frontend, Backend, QA (Manual)
```

---

## L2 — Epic + Stories

For team leads to review scope and priorities. Shows what each epic contains.

### JSON

```json
{
  "project_name": "E-Commerce Platform",
  "breakdown_level": 2,
  "language": "en",
  "source": "pre-estimate",
  "source_file": "spec.pdf",
  "generated_date": "2026-04-27",
  "active_roles": ["fe", "be", "qa_manual"],
  "role_names": { "fe": "Frontend", "be": "Backend", "qa_manual": "QA (Manual)" },
  "epics": [
    {
      "id": "E1",
      "name": "Authentication",
      "description": "User login, registration, OAuth",
      "total_md": null,
      "stories": [
        { "id": "S1.1", "name": "User can login via email/password", "description": "Basic email/password authentication", "total_md": null },
        { "id": "S1.2", "name": "User can login via OAuth (Google, GitHub)", "description": "Social login integration", "total_md": null },
        { "id": "S1.3", "name": "User can reset password", "description": "Password reset via email link", "total_md": null }
      ]
    },
    {
      "id": "E2",
      "name": "Product Catalog",
      "description": "Product listing, search, filters",
      "total_md": null,
      "stories": [
        { "id": "S2.1", "name": "User can browse products by category", "description": "Category-based product listing", "total_md": null },
        { "id": "S2.2", "name": "User can search products", "description": "Full-text search with filters", "total_md": null },
        { "id": "S2.3", "name": "User can view product detail", "description": "Product detail page with images/specs", "total_md": null }
      ]
    }
  ]
}
```

### Rendered Markdown

```markdown
# Task Breakdown: E-Commerce Platform

**Date**: 2026-04-27 | **Source**: pre-estimate | **Level**: L2

---

## E1: Authentication
User login, registration, OAuth
Stories: 3 | Roles: Frontend, Backend, QA (Manual)

### S1.1: User can login via email/password
Basic email/password authentication

### S1.2: User can login via OAuth (Google, GitHub)
Social login integration

### S1.3: User can reset password
Password reset via email link

## E2: Product Catalog
Product listing, search, filters
Stories: 3 | Roles: Frontend, Backend, QA (Manual)

### S2.1: User can browse products by category
Category-based product listing

### S2.2: User can search products
Full-text search with filters

### S2.3: User can view product detail
Product detail page with images/specs
```

---

## L3 — Epic + Stories + Tasks per Role

For developers/testers to start working. Each task has checklist and acceptance criteria.

### JSON (Post-estimate with MD)

```json
{
  "project_name": "E-Commerce Platform",
  "breakdown_level": 3,
  "language": "en",
  "source": "post-estimate",
  "source_file": "ecommerce-estimate-260427-1030.json",
  "generated_date": "2026-04-27",
  "active_roles": ["fe", "be", "qa_manual"],
  "role_names": { "fe": "Frontend", "be": "Backend", "qa_manual": "QA (Manual)" },
  "epics": [
    {
      "id": "E1",
      "name": "Authentication",
      "description": "User login, registration, OAuth",
      "total_md": 7,
      "stories": [
        {
          "id": "S1.1",
          "name": "User can login via email/password",
          "description": "Basic email/password authentication",
          "estimate_ref": "2.1",
          "total_md": 7,
          "tasks": [
            {
              "id": "FE-1.1.1",
              "name": "Login form UI",
              "role": "fe",
              "md": 2,
              "description": "Login page with email/password form",
              "checklist": [
                "Email input with validation",
                "Password input with show/hide toggle",
                "Submit button with loading state",
                "Error message display",
                "Forgot password link"
              ],
              "acceptance_criteria": [
                "Form validates email format, shows inline errors",
                "Disables submit during request",
                "Redirects to dashboard on success"
              ]
            },
            {
              "id": "BE-1.1.1",
              "name": "Auth API + JWT",
              "role": "be",
              "md": 4,
              "description": "Authentication endpoint with JWT token management",
              "checklist": [
                "POST /api/auth/login endpoint",
                "Password hashing with bcrypt",
                "JWT access + refresh token generation",
                "Token refresh endpoint",
                "Rate limiting on login attempts"
              ],
              "acceptance_criteria": [
                "Returns JWT on valid credentials",
                "Returns 401 on invalid credentials",
                "Refresh token rotates on use"
              ]
            },
            {
              "id": "QA-1.1.1",
              "name": "Login flow testing",
              "role": "qa_manual",
              "md": 1,
              "description": "Test cases for login functionality",
              "checklist": [
                "Valid login test",
                "Invalid email format test",
                "Wrong password test",
                "Account lockout after N attempts",
                "Remember me functionality"
              ],
              "acceptance_criteria": [
                "All test cases documented and executed",
                "Bug reports created for failures"
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Rendered Per-Team Files

#### fe-tasks.md

```markdown
# Frontend Tasks: E-Commerce Platform

**Date**: 2026-04-27 | **Total**: 2 MD

---

## E1: Authentication

### S1.1: User can login via email/password (2 MD)

#### FE-1.1.1: Login form UI (2 MD)
Login page with email/password form

- [ ] Email input with validation
- [ ] Password input with show/hide toggle
- [ ] Submit button with loading state
- [ ] Error message display
- [ ] Forgot password link

**AC:**
- Form validates email format, shows inline errors
- Disables submit during request
- Redirects to dashboard on success
```

#### be-tasks.md

```markdown
# Backend Tasks: E-Commerce Platform

**Date**: 2026-04-27 | **Total**: 4 MD

---

## E1: Authentication

### S1.1: User can login via email/password (4 MD)

#### BE-1.1.1: Auth API + JWT (4 MD)
Authentication endpoint with JWT token management

- [ ] POST /api/auth/login endpoint
- [ ] Password hashing with bcrypt
- [ ] JWT access + refresh token generation
- [ ] Token refresh endpoint
- [ ] Rate limiting on login attempts

**AC:**
- Returns JWT on valid credentials
- Returns 401 on invalid credentials
- Refresh token rotates on use
```

---

## Level Selection Guide

| Level | Audience | Purpose | When to use |
|-------|----------|---------|-------------|
| L1 | Stakeholders, clients | Scope overview, high-level review | Early discussions, proposals |
| L2 | Team leads, PMs | Scope validation, priority planning | Sprint planning, backlog grooming |
| L3 | Developers, testers | Actionable task assignment | Implementation, sprint execution |

## Pre-estimate vs Post-estimate at Each Level

| Level | Pre-estimate | Post-estimate |
|-------|-------------|---------------|
| L1 | Epics only, no MD | Epics with total MD |
| L2 | Epics + stories, no MD | Epics + stories with MD |
| L3 | Full hierarchy, no MD | Full hierarchy with MD from estimate |
