# F001: Authentication

## Why This Exists

Handles user login and session management.

## Business Workflow

**Source:** `api/app/Http/Controllers/AuthController.php:10-50`

User submits credentials → server validates → session created.

**Source:** `api/app/Http/Middleware/AuthMiddleware.php:5-20`

## Source Code References

| File | Lines | Purpose |
|------|-------|---------|
| `api/app/Http/Controllers/AuthController.php:10-50` | 10-50 | Login endpoint |
| `api/app/Models/User.php` | all | User entity |
| `web/src/pages/Login.vue` | all | Login page |
