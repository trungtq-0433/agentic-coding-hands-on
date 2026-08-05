# Breakdown JSON Schema

The AI outputs this JSON as the single source of truth. Renderers transform it into overview markdown and per-team task files.

## Structure

```json
{
  "project_name": "string",
  "breakdown_level": 1 | 2 | 3,
  "language": "en | vi | ja",
  "source": "pre-estimate | post-estimate",
  "source_file": "string",
  "generated_date": "YYYY-MM-DD",
  "active_roles": ["fe", "be", "qa_manual"],
  "role_names": { "fe": "Frontend", "be": "Backend", "qa_manual": "QA (Manual)" },
  "epics": [
    {
      "id": "E1",
      "name": "Authentication",
      "description": "User authentication and authorization",
      "total_md": null,
      "stories": [
        {
          "id": "S1.1",
          "name": "User can login via email/password",
          "description": "Basic email/password authentication",
          "estimate_ref": "2.1",
          "total_md": null,
          "tasks": [
            {
              "id": "FE-1.1.1",
              "name": "Login form UI",
              "role": "fe",
              "md": null,
              "description": "Login page with email/password form",
              "checklist": ["Email input with validation", "Password input with toggle"],
              "acceptance_criteria": ["Form validates email format"]
            }
          ]
        }
      ]
    }
  ]
}
```

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_name` | string | yes | Project name |
| `breakdown_level` | integer | yes | 1, 2, or 3 |
| `language` | string | yes | `en`, `vi`, or `ja` |
| `source` | string | yes | `pre-estimate` or `post-estimate` |
| `source_file` | string | no | Source document or JSON path |
| `generated_date` | string | yes | `YYYY-MM-DD` format |
| `active_roles` | array | yes | Ordered role slugs (min 1) |
| `role_names` | object | yes | Slug -> display name mapping |
| `epics` | array | yes | Epic list (min 1) |

## Epic Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Epic ID (e.g. `E1`, `E2`) |
| `name` | string | yes | Epic name |
| `description` | string | no | Brief description |
| `total_md` | number/null | no | Sum of story MDs. `null` in pre-estimate |
| `stories` | array | no | Story list. Omit for L1-only |

## Story Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Story ID (e.g. `S1.1`) |
| `name` | string | yes | Story name (user story format preferred) |
| `description` | string | no | Brief description |
| `estimate_ref` | string/null | no | Estimate JSON task ID link (post-estimate only) |
| `total_md` | number/null | no | Sum of task MDs. `null` in pre-estimate |
| `tasks` | array | no | Task list. Omit for L1/L2-only |

## Task Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Task ID (e.g. `FE-1.1.1`, `BE-1.2.3`) |
| `name` | string | yes | Task name |
| `role` | string | yes | Role slug (must be in `active_roles`) |
| `md` | number/null | no | Man-days. `null` in pre-estimate |
| `description` | string | no | Detailed task description |
| `checklist` | array | no | Implementation steps (L3 only) |
| `acceptance_criteria` | array | no | Definition of done (L3 only) |

## ID Conventions

- **Epic**: `E{n}` — `E1`, `E2`, `E3`
- **Story**: `S{epic}.{n}` — `S1.1`, `S1.2`, `S2.1`
- **Task**: `{PREFIX}-{epic}.{story}.{n}` — `FE-1.1.1`, `BE-1.2.3`, `QA-2.1.1`

### Role Slug to Task ID Prefix

| Slug | Prefix | Example |
|------|--------|---------|
| `fe` | `FE` | `FE-1.1.1` |
| `be` | `BE` | `BE-1.1.1` |
| `qa_manual` | `QA` | `QA-1.1.1` |
| `qa_auto` | `QAA` | `QAA-1.1.1` |
| `design` | `DSG` | `DSG-1.1.1` |
| `pm` | `PM` | `PM-1.1.1` |
| `brse` | `BRSE` | `BRSE-1.1.1` |
| `infra` | `INFRA` | `INFRA-1.1.1` |

## Pre-estimate vs Post-estimate

| Field | Pre-estimate | Post-estimate |
|-------|-------------|---------------|
| `total_md` (epic/story) | `null` | Sum of constituent MDs |
| `md` (task) | `null` | Inherited from estimate JSON |
| `estimate_ref` | `null` | Estimate JSON task ID |
| `active_roles` | User-selected | From JSON `parameters.active_roles` |
| `role_names` | From knowledge-base | From JSON `parameters.role_names` |

## Available Role Slugs

From `knowledge-base/roles-config-defaults.yaml`:

| Slug | Display Name |
|------|-------------|
| `fe` | Frontend |
| `be` | Backend |
| `qa_manual` | QA (Manual) |
| `qa_auto` | QA (Automation) |
| `design` | UI/UX Design |
| `pm` | Project Management |
| `brse` | Bridge SE |
| `infra` | Infrastructure |

## Validation Rules

- Every role in task `role` must be in `active_roles`
- Post-estimate: `estimate_ref` must reference valid task IDs from source JSON
- Post-estimate: `md` must match source estimate JSON values
- Pre-estimate: `md`, `total_md`, `estimate_ref` must be `null`
- L3 tasks should include `checklist` and `acceptance_criteria`
- At least one epic required

## Rendering

```bash
python3 scripts/render-breakdown.py breakdown.json -o output/<project>/breakdown/
```
