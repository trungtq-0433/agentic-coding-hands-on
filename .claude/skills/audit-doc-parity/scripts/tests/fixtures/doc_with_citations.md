# Technical Spec — F001_Example

## Requirements

| FR-001 | Export orders as CSV | GET /api/orders/export | OrderController@export | yes |
**Source:** `claude/skills/audit-doc-parity/scripts/tests/fixtures/source_plain.py:6-8`

| FR-002 | Authenticate user | POST /api/login | AuthController@login | yes |
**Source:** `claude/skills/audit-doc-parity/scripts/tests/fixtures/source_plain.py:1-3`

## Business Rules

| BR-001 | Orders | Only admin can export | FR-001 |

## External Integrations

## INT-001
**Type:** HTTP
**Target:** payment-gateway
**Trigger:** order.paid event
**Payload:** {order_id, amount}
**Output:** response_shape={"status":"ok"}
**Failure handling:** retry 3 times
**Source:** `claude/skills/audit-doc-parity/scripts/tests/fixtures/source_plain.py:6-8`

## Key Entities

| orders | id, user_id | read/write |
| users | id, email | read |

## Verification

| SC-001 | Admin exports CSV | FR-001 |
| SC-002 | Non-admin gets 403 | FR-001 |
