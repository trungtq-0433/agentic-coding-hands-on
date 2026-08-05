# Architecture

## Service Interactions

| From | To | Method | Description |
|------|----|--------|-------------|
| employee-frontend | employee-backend | GET /api/employees | Fetch employee list |
| employee-backend | auth | POST /auth/verify | Verify JWT token |

## Events

| Topic | Role | Event |
|-------|------|-------|
| employee.created | producer | EmployeeCreated |
| employee.updated | producer | EmployeeUpdated |
