# KPI Insight MCP connection

Use this reference whenever a `tkm:ki-*` skill needs KPI Insight.

## Configure

Merge
[`kpi-insight-mcp-config.json`](kpi-insight-mcp-config.json)
into the project's existing `.mcp.json`, or add the same server entry to the
user-level MCP settings. Do not replace an existing config file wholesale.

Set `KPI_INSIGHT_TOKEN` through the environment supported by the MCP client.
Keep project `.env` files ignored. Never place a real token in a skill,
repository setting, prompt, report, or log.

Takumi does not install, merge, or update this connection. The configured
server name must be `kpi-insight`.

## Project identifiers

Use the identifier type named by the live tool schema; project code and Rubato
project id are not interchangeable. For the approved sample mapping:

- `projectCode: "R1764"` for estimate tools.
- `rubato_project_id: "1764"` for project, KPI, quality, incident, and tooling
  tools.

If only one form is known, ask for the corresponding identifier instead of
removing or adding an `R` by assumption.

## Availability check

Before a workflow:

1. Discover the required `mcp__kpi-insight__*` tool and inspect its current
   input schema.
2. If the server is absent, stop and show the setup instructions above.
3. If the server exists but a required tool is absent, report that capability
   as unavailable in this environment. Do not substitute another data source.
4. If a call returns `forbidden`, report that the current role cannot read the
   requested scope and stop that path.

Do not use a different account, database access, SSH, direct GitHub inspection,
or web scraping to reconstruct data rejected by MCP.

## Role boundaries

| Role | Typical accessible scope |
|---|---|
| Project reader | Assigned project health, quality, incidents, and tooling |
| SDM | Own portfolio and monthly SDM reporting |
| Admin/BOD | Named SDM, division, admin, and sensitive customer views |
| Super Admin | Privileged estimate detail/write operations |

The server is authoritative. An absent privileged field is not permission to
infer it from project names or another response.

## Read-only release boundary

The KPI Insight skills in this release are read-only. Never call:

- `kpi_estimate_mine`
- `kpi_issue_estimate_ai_fill`
- `kpi_issue_estimate_write`

`kpi_issue_estimate_ai_fill` is a write operation: it enqueues a job that
generates and stores estimates. It is not a preview tool.

## Result semantics

- `forbidden`: insufficient role/scope; stop.
- Empty array/result: the query succeeded but has no data.
- Null value/threshold: unmeasured or missing; do not supply a static fallback.
- Tool/server error: report the failure and its requested scope; do not invent
  an answer.
