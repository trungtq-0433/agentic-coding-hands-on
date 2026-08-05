## Detected Language
PHP [MULTI_STACK] (JS/TS secondary)

## File Inventory
src/controllers/Auth.php	controller
src/views/login.blade.php	screen
web/src/pages/Dashboard.vue	screen

## Background Logic Source Inventory
BL-001_SendVerificationEmail	src/Jobs/SendVerificationEmail.php:1-45	dispatched by AuthController@register
BL-002_ProcessPayment	src/Jobs/ProcessPayment.php:1-80	dispatched by OrderController@checkout
BL-003_GenerateReport	src/Jobs/GenerateReport.php:1-60	scheduled daily via Kernel

## Data Model Summary
users	id, email, password, role, created_at
orders	id, user_id, total, status, created_at
products	id, name, price, stock, category_id
