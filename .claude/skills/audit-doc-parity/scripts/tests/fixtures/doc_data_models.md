# Data Models

### Order

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint | PK, NOT NULL |
| user_id | bigint | FK users.id, NOT NULL |
| total | decimal(10,2) | NOT NULL |
| status | varchar(32) | NOT NULL |

**Relationships:** belongs_to User, has_many OrderItem

### User

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint | PK, NOT NULL |
| email | varchar(255) | UNIQUE, NOT NULL |

## Discriminator Fields

| Field | Values |
|-------|--------|
| status | pending, paid, cancelled, refunded |
| role | admin, user, guest |

## Validation Rules

| Field | Constraint | Error message |
|-------|-----------|---------------|
| email | format:email | Invalid email address |
| total | min:0 | Total must be non-negative |
