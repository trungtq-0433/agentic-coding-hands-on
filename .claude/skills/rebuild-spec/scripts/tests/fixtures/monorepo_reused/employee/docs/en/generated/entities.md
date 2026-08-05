# Entities

## Employee

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| name | string | Employee name |
| email | string | Email address |
| department_id | uuid | FK to Department |

## Department

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| name | string | Department name |
