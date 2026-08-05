# Technical Spec — F001_Orders

**Priority**: P1
**Type**: background
**Generated**: 2026-06-26

## User Stories

### US001 — Manage orders (Priority: P1)

**What happens:** Staff list and export orders.

**Requirements fulfilled:**
- **FR-001** Listing orders requires the user to be authenticated — `GET /orders` via `list_orders`
  **Source:** `code/orders.py:6-10`
- **FR-002** Listing orders is restricted to the admin role — `GET /orders` via `list_orders`
  **Source:** `code/orders.py:6-10`

**Rules enforced:**

### BR-001_AuthRequired
**Linked FR:** FR-001
**Source:** `code/orders.py:6-10`
**Applies to:** GET /orders endpoint
**Rule:** User must be authenticated before any order listing is permitted.

**Pseudocode:**
```text
if not current_user.is_authenticated:
    raise HTTP 401
```

**Algorithms:**

### ALG-001_OrderCsvExport
**Linked FR:** FR-003
**Source:** `code/orders.py:13-22`
**Input:** all orders queryset
**Output:** a file (CSV format, UTF-8 encoded)
**Complexity:** O(n)
**Description:** Serializes orders to a downloadable CSV file.

**Pseudocode:**
```text
rows = [order.to_csv_row() for order in orders]
return csv_response(rows)
```

**Verification:**
- **SC-001** Authenticated user can list orders (covers FR-001)

---

### US002 — Export orders (Priority: P2)

**What happens:** Admin exports order list to CSV.

**Requirements fulfilled:**
- **FR-003** Export orders to CSV — `GET /orders/export` via `export_orders_csv`
  **Source:** `code/orders.py:13-22`

**Verification:**
- **SC-002** CSV download contains all orders (covers FR-002, FR-003)

---

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Order | `orders` | id, total, status | read + export operations |

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| list_orders | `code/orders.py:6-10` | list endpoint |
| export_orders_csv | `code/orders.py:13-22` | CSV export |
