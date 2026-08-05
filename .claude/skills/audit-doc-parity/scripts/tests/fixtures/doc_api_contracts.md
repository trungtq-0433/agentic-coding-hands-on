# API Contracts

## Orders — GET /api/orders/export

**Auth:** requires admin role
**Request:** query params: format=csv
**Response:** CSV file stream
**Status codes:** 200, 403, 500
**Error envelope:** {error: string, code: int}
**Source:** `claude/skills/audit-doc-parity/scripts/tests/fixtures/source_plain.py:6-8`

## Auth — POST /api/login

**Auth:** none
**Request:** {email, password}
**Response:** {token, user}
**Status codes:** 200, 401
**Error envelope:** {error: string}
