# Data Model — Create Taskify

## Task

| Field       | Type     | Notes              |
|-------------|----------|--------------------|
| id          | UUID     | Primary key        |
| title       | string   | Required, max 255  |
| description | text     | Optional           |
| created_at  | datetime | Auto-set on insert |
| user_id     | UUID     | FK → users.id      |
