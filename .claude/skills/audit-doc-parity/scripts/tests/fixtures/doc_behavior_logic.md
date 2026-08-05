# Behavior Logic

## BL001
**Type:** event-listener
**Trigger:** order.placed
**Payload:** {order_id, user_id, total}
**Source Symbol:** handle_order_placed
**Related routes:** POST /api/orders
**Related models:** Order, User
**Source:** `claude/skills/audit-doc-parity/scripts/tests/fixtures/source_plain.py:6-8`

## BL002
**Type:** scheduled-job
**Trigger:** daily 02:00 UTC
**Payload:** none
**Source Symbol:** run_daily_export
**Related routes:** none
**Related models:** Order
