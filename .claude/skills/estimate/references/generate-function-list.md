# Generate Function List — Workflow Reference

Generate detailed Function List from Screen List and Screen Flow by breaking down features into atomic, estimable functions. Must be run after generating screen flow.

## Data Provider

All queries use the **configured data provider** (default: `clio_query` MCP tool via Clio Knowledge Graph).
See `SKILL.md` → Data Provider section for setup and configuration.

---

## Purpose

Automatically break down screen-level features into detailed function lists by:
1. Reading existing **Screen List (CSV)** and **Screen Flow (Markdown)** files
2. Querying **project data source** for detailed feature information
3. Decomposing each screen into atomic functions
4. Categorizing functions by type (UI/CRUD/API/Validation/Navigation/Logic)
5. Identifying dependencies between functions
6. Outputting structured **Function List (CSV)** for estimation purposes

---

## Execution Workflow

### SEQUENTIAL STEPS (Do NOT run queries in parallel)

---

### Step 0: Check for Project Configuration

**Check for config file in the current directory:**
1. **Look for `.estimate.yml`** — if exists, read and extract `project_id`
2. **If not found, look for `.clio.yml`** — if exists, read and extract `project_id`
3. **If neither exists:** Ask user for `project_id`

---

### Step 1: Scan and Load Screen Files

**Scan `outputs/` directory for existing screen files:**
- Look for `screen_list_*.csv` files
- Look for `screen_flow_*.md` files
- Match pairs by project_id and timestamp

**If multiple projects found, present options to user.**

---

### Step 2: Parse Screen List (CSV)

**Read and parse CSV file:**
- Extract Screen ID, Name, Type
- Extract Key Features list
- Extract Navigation relationships (Incoming From, Outgoing To)
- Extract Screen descriptions

**Build screen inventory with total screens and type breakdown.**

---

### Step 3: Parse Screen Flow (Markdown)

**Read markdown file and extract:**
1. Mermaid diagram → Parse navigation paths
2. Screen Details sections → Additional feature context
3. Critical Paths → Important user journeys
4. Navigation Matrix → Screen-to-screen connections

---

### Step 4: Query Data Source for Detailed Features

For each screen, query the project data source using the data provider tool (default: `clio_query`):

**Query 1: Screen Features & Functionalities**
```
query: "Screen: [SCREEN_NAME]. What are all the features, functionalities, user actions, buttons, input fields, form fields, interactive elements, UI components, data operations, workflows on this screen?"
```

**Query 2: Data Operations & API Calls**
```
query: "Screen: [SCREEN_NAME]. What API calls, API endpoints, data fetching, data submission, CRUD operations, backend services are used?"
```

**Query 3: Validation & Business Logic**
```
query: "Screen: [SCREEN_NAME]. What are the validation rules, input validations, form validations, business rules, business logic, calculation logic?"
```

**Query 4: Navigation & Routing**
```
query: "Screen: [SCREEN_NAME]. What are the navigation actions, routing logic, screen transitions, page navigation?"
```

**Query 5: Shared Components & Dependencies**
```
query: "What are the shared components, common UI components, reusable functions, utility functions, helper methods, shared services used across multiple screens?"
```

---

### Step 5: Break Down Screens into Functions

#### Function Categories:

**1. UI Functions** — Display/render components, show/hide elements, styling, responsive layout, lists/tables, forms, modals

**2. CRUD Functions**
- Create: Form submission for new records, data creation API calls
- Read: Fetch data on load, search/filter, pagination, refresh
- Update: Edit form submission, patch/update API calls
- Delete: Delete confirmation, soft/hard delete

**3. Validation Functions** — Required field checks, format validation, length validation, pattern matching, cross-field validation, business validation, range checks

**4. API Functions** — Construct API requests, set headers/auth, parse responses, handle success/error, retry logic

**5. Navigation Functions** — Route navigation, pass parameters, conditional navigation, role-based routing, auth guards

**6. Logic Functions** — Data transformation, format data, calculations, state management, caching

---

### Step 6: Generate Function IDs

**ID Convention:**
- Format: `FUNC-XXX` (3-digit zero-padded)
- Sequential numbering: FUNC-001, FUNC-002, ..., FUNC-999
- Group by screen, order by execution flow (UI → Validation → API → Logic → Navigation)

---

### Step 7: Identify Dependencies

**Dependency Types:**
1. **Sequential**: Function B requires Function A to complete first
2. **Data**: Function B needs data produced by Function A
3. **Shared**: Multiple functions use the same utility/service

**Notation:** Semicolon-separated list: `FUNC-001;FUNC-002;FUNC-003`

---

### Step 8: Generate CSV Output

**CSV Structure:**
```csv
Function ID,Function Name,Screen,Category,Description,Dependencies,Notes
FUNC-001,Display Login Form,Login Screen,UI,"Render email and password input fields, login button, and forgot password link",,
FUNC-002,Validate Email Format,Login Screen,Validation,Check email field matches valid email pattern,,Use regex
FUNC-003,Call Authentication API,Login Screen,API,POST to /api/auth/login with credentials,FUNC-002,Handle errors
...
```

**File:** `outputs/function_list_{project_id}_{timestamp}.csv`

---

### Step 9: Generate Summary Report

Create markdown summary with:
- Statistics: Total functions, by category, by screen
- Functions by Screen tables
- Dependency Analysis: High-dependency functions, independent functions, sequential chains
- Reusable Functions table
- Notes & Recommendations

**File:** `outputs/function_summary_{project_id}_{timestamp}.md`

---

### Step 10: Final Output

```
Function List Generation Complete!

Summary:
- Total Screens Analyzed: [N]
- Total Functions Generated: [N]
- Functions by Category: UI [N], CRUD [N], API [N], Validation [N], Navigation [N], Logic [N]

Files Generated:
- outputs/function_list_{project_id}_{timestamp}.csv
- outputs/function_summary_{project_id}_{timestamp}.md
```

---

## Granularity Guidelines

### Too Granular (Avoid)
- Set email input value, Set password input value, Enable login button

### Too Coarse (Avoid)
- Handle entire login process

### Just Right
Each function should:
- Have a clear input and output
- Perform a single responsibility
- Be estimable (typically a few hours to 2 days)
- Be unit-testable independently

---

## Edge Cases

- **Empty screen list:** Query data source directly for screens or ask user
- **Insufficient data:** Generate basic functions based on screen type and common patterns
- **Too many functions (>200):** Offer to consolidate or focus on critical screens
- **Circular dependencies:** Highlight and suggest restructuring
