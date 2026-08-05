# Generate Project Profile — Workflow Reference

Generate full project profile matching the Sun* **Project Profile** template (BM-2-901-64).

## Data Provider

All queries use the **configured data provider** (default: `clio_query` MCP tool via Clio Knowledge Graph).
See `SKILL.md` → Data Provider section for setup and configuration.

---

## Input

The user provides the **Project Name or ID** (e.g. `ca496048`) via `.estimate.yml` or `.clio.yml` config file.

## Behaviour

- Perform each step **SEQUENTIALLY** (total: 15 steps).
- After each tool call, reason carefully about the result and infer the most accurate value **before** moving to the next step.
- Do **NOT** run queries in parallel.
- If a query returns empty (`[]`) or unclear results, immediately run one **secondary query** with broader context (e.g. "project overview, description, purpose") and reason again.
- If still unknown after both queries, set value = `unknown`.
- After all steps are complete, assemble the full CSV document and save it.

---

## Tool Call Format

Use data provider tool (default: `clio_query`) with:
- `project_id`: `<Project Name or ID>`
- `query`: `<FIELD-SPECIFIC PROMPT>`

---

## Sequential Steps

### Step 0: Check for Project Configuration

**Check for config file in the current directory:**

1. **Look for `.estimate.yml`** — if exists, read and extract `project_id`
2. **If not found, look for `.clio.yml`** — if exists, read and extract `project_id`
3. **If neither exists:** Ask user for `project_id`

---

### Step 1 — Project Overview (Basic Info)

Query for: project name in Sun*, client name, website, location, client's business domain.

→ `query`: `"Project basic information: project name, client name, website URL, office location, business domain or industry of the client."`
→ Extract each sub-field individually. Mark any missing sub-field as `unknown`.

---

### Step 2 — Type of Service

Infer the **Type of Service**. Choose **one or more** from:
`SaaS (Software as a Service)`, `E-commerce`, `PaaS`, `On-demand Service`, `Social Networking`.

→ `query`: `"Type of service: SaaS, E-commerce, PaaS, On-demand Service, Social Networking. What kind of service model does this project use?"`
→ Fallback: `unknown`.

---

### Step 3 — Target Audience & Scale

Infer:
- **Type of target audience** (choose one or more): `BtoB`, `BtoC`, `BtoE (employee)`, `BtoG (government)`, `CtoC`, `GtoC`
- **Number of employees** at the client company (approximate range or exact)
- **Number of users** of the product/service (approximate range or exact)

→ `query`: `"Target audience type (BtoB, BtoC, BtoE, BtoG, CtoC, GtoC), number of employees at the client, and estimated number of end users."`

---

### Step 4 — Client Overview

Write a concise client overview covering:
- Special characteristics of the client (e.g. aesthetics, technical depth)
- Product Owner (PO) profile (technical / non-technical background)
- Any other relevant client context

→ `query`: `"Client overview: client characteristics, Product Owner background, key stakeholders, client communication style or expectations."`

---

### Step 5 — Overview Requirements

Infer the client's expectations and project context:
- What does the client expect from building this system/product?
- Priority: `Quality` / `Cost` / `Delivery` / `Scope`
- Project type: `New development` / `Revamp of an existing system` / `Enhancement / adding new features`
- Advantages of the current system (if any)
- Restrictions / limitations of the current system

→ `query`: `"Overview requirements: client expectations, project priority (Quality/Cost/Delivery/Scope), project type (new development, revamp, enhancement), current system advantages, current system restrictions or limitations."`

---

### Step 6 — Objectives & Scope of Work

Infer:
- **Primary objective** — what must be achieved first, what problem it solves, next objectives
- **Scope of work** — phases (Requirement / Design / Development / Testing / Release), functional items, non-functional items
- **Out of scope**

→ `query`: `"Project objectives (primary goal, problem to solve, next objectives), scope of work (development phases, functional and non-functional items), and out-of-scope items."`

---

### Step 7 — Project Industry & Service Categories

Infer:
- **Project Industry Category** (choose **one**): `Agriculture - Forestry`; `Fishery`; `Mining - quarrying`; `Construction industry`; `Manufacturing industry`; `Electricity - gas - heat supply - water supply`; `Information and communication industry`; `Transportation - postal service`; `Wholesale and Retail`; `Finance - insurance`; `Real estate - goods rental`; `Academic research - specialized / technical service`; `Accommodation - food service`; `Lifestyle-related service - entertainment`; `Education - learning support`; `Medical care`; `Employment placement - worker dispatching`; `Service industry`; `Public affairs`; `Unclassifiable industry`
- **Project Service Category** (choose **one**): `Art & Design`; `Events`; `Entertainment`; `Personalization`; `Comics`; `Shopping`; `Sports`; `Social`; `Tools`; `News & Magazines`; `Business`; `Finance`; `Food & Drink`; `Lifestyle`; `Libraries & Demo`; `Medical`; `Music & Audio`; `Education`; `Health & Fitness`; `Productivity`; `Auto & Vehicles`; `Photography`; `House & Home`; `Dating`; `Parenting`; `Books & Reference`; `Maps & Navigation`; `Communication`; `Weather`; `Video Players & Editors`; `Beauty`; `Travel & Local`; `Game`; `Parents & Children`
- **Project Business Category** (choose **one**): `B2B`, `B2C`, `B2E (employee)`, `B2G (government)`, `C2C`
- **Project Business Size** (choose **one**): `Enterprise Size`, `Small and Medium-Sized`

→ `query`: `"Project Industry Category, Project Service Category, Project Business Category (B2B/B2C/B2E/B2G/C2C), and Project Business Size (Enterprise or SME). Use all available context."`

---

### Step 8 — Timeline & Development Model

Infer:
- **Project Duration** (start date, end date, or total months)
- **Development Model** (choose one or more): `Waterfall`, `Scrum`, `Agile`, `MVP/POC`

→ `query`: `"Project timeline: start date, end date, total duration in months. Development model used: Waterfall, Scrum, Agile, MVP/POC."`

---

### Step 9 — Tech Stack

Infer:
- **Programming Languages** (frontend + backend)
- **Frameworks** (frontend + backend)
- **Web rendering method** (SSR, CSR, SSG, etc.)

→ `query`: `"Tech stack: programming languages (frontend, backend), frameworks, web rendering method (SSR, CSR, SSG, hybrid)."`

---

### Step 10 — Infrastructure

Infer:
- **Server model**: server-based or serverless
- **Infrastructure diagram** summary
- **Infrastructure cost** (approximate)
- **IaC tool** (Terraform, CDK, Pulumi, etc.)
- **Third-party services** (AWS, GCP, Azure, Stripe, Twilio, etc.)

→ `query`: `"Infrastructure: server or serverless architecture, infrastructure components, estimated cost, IaC tools used, third-party services and APIs integrated."`

---

### Step 11 — Project Organization Structure

Infer the team roles and names/counts for:
`Product Owner`, `PM SJP`, `Architect Lead`, `PSM`, `BrSE`, `Dev Lead Frontend`, `Dev Lead Backend`, `QA Lead`, `Infrastructure Engineer`

→ `query`: `"Project team organization: Product Owner, PM, Architect Lead, PSM, BrSE, Frontend Dev Lead, Backend Dev Lead, QA Lead, Infrastructure engineer — names or headcount."`

---

### Step 12 — Dependencies & Constraints

Infer:
- **Dependencies** (technical dependencies, external system integrations, third-party contracts)
- **Constraints** (time constraints, budget constraints, regulatory constraints)

→ `query`: `"Project dependencies (technical, external systems, third-party) and constraints (time, budget, legal, regulatory)."`

---

### Step 13 — Risk Management

Infer relevant risks across categories:
`Financial Risk`, `Operation Risk`, `Information Security Risk`, `Compliance Risk`, `Human Risk`, `Event Risk`, `Rumor Risk`

→ `query`: `"Project risk management: financial risks, operational risks, information security risks, compliance risks, human resource risks, event risks, reputation or rumor risks."`

---

### Step 14 — Service Introduction (Reasoning Only — No Query)

Do **NOT** call any tool.
Synthesise a concise English paragraph (7–10 sentences) summarising the entire project using all prior results.
Include: main product/service purpose, target users, key features, tech highlights, and business value.
If most prior values are `unknown`, output: `unknown`.

---

### Step 15 — Generate Excel Project Profile

After saving the CSV file, call the `clio_project_profile` MCP tool to generate and upload the official Excel Project Profile.

**Action:**
- Pass the **full CSV string** (assembled in the Output Format section) as `csv_content`
- Use the `project_id` extracted from Step 0
- Set `upload_to_clio: true`

**On success**, display:
```
Excel Project Profile generated and uploaded successfully.
Download / View: {url}
```

**On failure**, display:
```
Excel file generated but upload failed: {upload_message}
```

---

## Output Format

After all steps, assemble and save the following CSV file (UTF-8, comma-separated).

**CSV rules:**
- **One header row**: `Section,Field,Value`
- **Three columns**: `Section,Field,Value`
- Each row belongs to a numbered section. Fields that belong to the same section share the same Section value.
- Section values follow the pattern: `N. Section Name` (e.g. `1. Project Overview`, `2. Business and Client context`).
- Any value containing a comma, newline, or double-quote **must** be wrapped in double-quotes (`"`). Internal double-quotes must be escaped as `""`.
- Multi-sentence values go in a single quoted cell in column C (Value).
- Fields that group multiple sub-items must consolidate all sub-items into one cell using line breaks (`\n`) as separators.

```csv
Section,Field,Value
1. Project Overview,Generated,{Date and Time}
1. Project Overview,Template,BM-2-901-64 v1.0
1. Project Overview,Project name in Sun*,…
1. Project Overview,Client Name,…
1. Project Overview,Website,…
1. Project Overview,Location,…
1. Project Overview,Client Business Domain,…
2. Business and Client context,Type of Service,"…"
2. Business and Client context,Type of Target Audience,"…"
2. Business and Client context,Number of Employees,…
2. Business and Client context,Number of Users,…
2. Business and Client context,Client Overview,"…"
3. Project Scope and Goal,Overview Requirements,"What are the client's expectations for building the system/product?
Priority: …
Project type: …
Advantages of the current system: …
Restrictions / limitations of the current system: …"
3. Project Scope and Goal,Objectives,"Primary objective: …
Problem to solve: …
Next objectives: …"
3. Project Scope and Goal,Scope of Work,"Phase: Requirement / Design / Development / Testing / Release
Functional Items: …
Non-functional Items: …"
3. Project Scope and Goal,Out of Scope,…
3. Project Scope and Goal,Project Industries Categories,…
3. Project Scope and Goal,Project Service Categories,…
3. Project Scope and Goal,Project Business Category,…
3. Project Scope and Goal,Project Business Size,…
4. Timeline and Process,Duration,…
4. Timeline and Process,Development Model,…
5. Technical Overview,Tech Stack,"Programming language: …
Framework: …
Web rendering method: …"
5. Technical Overview,Infrastructure,"Server or serverless: …
Infrastructure diagram: …
Infrastructure cost: …
IaC tool: …
Third-party Services: …"
6. Project Organization Structure,Product Owner,…
6. Project Organization Structure,PM SJP,…
6. Project Organization Structure,Architect Lead,…
6. Project Organization Structure,PSM,…
6. Project Organization Structure,BrSE,…
6. Project Organization Structure,Dev Lead Frontend,…
6. Project Organization Structure,Dev Lead Backend,…
6. Project Organization Structure,QA Lead,…
6. Project Organization Structure,Infrastructure Engineer,…
7. Risk and Note,Dependencies and Constraint,"Dependencies: …
Constraint: …"
7. Risk and Note,Risk Management,"Financial Risk: …
Operation Risk: …
Information Security Risk: …
Compliance Risk: …
Human Risk: …
Event Risk: …
Rumor Risk: …"
8. Service Introduction,Summary,"{7–10 sentence synthesis paragraph}"
```

---

## File Naming

```
outputs/project_profile_{project_id}_{timestamp}.csv
```

- `{project_id}`: lowercase, spaces replaced with underscores
- `{timestamp}`: `YYYYMMDD_HHMMSS`

After saving, confirm:
```
Project Profile saved to: outputs/project_profile_{project_id}_{timestamp}.csv
```
