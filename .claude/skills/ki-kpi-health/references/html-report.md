# KPI health HTML report

Load this reference only when the user explicitly requests `--html`.

## Output contract

- Write one self-contained UTF-8 HTML file under `reports/`.
- Keep chat as the primary summary and return the file path.
- Do not upload, publish, or auto-open the file.
- Never include credentials, authorization headers, hidden IDs, or raw MCP
  error payloads.
- Use the same value/status/quality interpretation as the chat response.
- Use server-returned bands and flags; do not hard-code KPI thresholds.

## File names

| Scope | File |
|---|---|
| Project | `reports/kpi-health-<project>-<period>.html` |
| SDM | `reports/kpi-health-sdm-<label>-<yyyy-mm>.html` |
| Division | `reports/kpi-health-<division>-<yyyy-mm>.html` |

Sanitize path components. If a file already exists, ask before overwriting or
choose a timestamped suffix.

## Page structure

Render in this order:

1. Scope, period, source freshness.
2. Executive verdict.
3. Up to three items needing attention.
4. Measured KPI table.
5. Data-quality/unmeasured section.
6. Optional intent-specific section:
   - burndown;
   - team capacity;
   - milestones;
   - integration.

7. Method note listing MCP tools used.

For SDM/division, show project-level roll-ups. Do not add ticket-level or member
detail.

## Minimal template

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>KPI Health · {{scope}}</title>
  <style>
    :root {
      --ink: #172033;
      --muted: #667085;
      --paper: #f7f8fb;
      --panel: #ffffff;
      --line: #d9deea;
      --good: #18794e;
      --warn: #a15c00;
      --risk: #b42318;
      --info: #175cd3;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 32px; color: var(--ink); background: var(--paper);
      font: 15px/1.5 Inter, "Segoe UI", Arial, sans-serif;
    }
    main { max-width: 1100px; margin: auto; }
    header, section {
      background: var(--panel); border: 1px solid var(--line);
      border-radius: 12px; padding: 20px; margin-bottom: 16px;
    }
    h1, h2 { margin-top: 0; }
    .meta { color: var(--muted); }
    .callout { border-left: 5px solid var(--info); }
    .good { border-left-color: var(--good); }
    .warn { border-left-color: var(--warn); }
    .risk { border-left-color: var(--risk); }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px; border-bottom: 1px solid var(--line); text-align: left; }
    th { color: var(--muted); font-weight: 600; }
    .nowrap { white-space: nowrap; }
  </style>
</head>
<body>
<main>
  <header>
    <h1>{{scope}}</h1>
    <p class="meta">{{period}} · refreshed {{freshness}}</p>
  </header>
  <section class="callout {{verdict_class}}">
    <h2>Verdict</h2>
    <p>{{verdict}}</p>
  </section>
  {{attention_section}}
  {{kpi_table}}
  {{data_caveats}}
  {{optional_section}}
  {{method_note}}
</main>
</body>
</html>
```

## Rendering rules

- Escape all tool-returned text before inserting it into HTML.
- Keep original customer-language quotations only in survey skills, not health.
- Use text labels with color; never rely on color alone.
- Mark null values `No data`, not zero.
- Mark open-sprint measurements as in progress when the response says the
  sprint is incomplete.
- For `get_team_effort`, show aggregate MM/headcount/job-type shape only.
- If no optional mode was requested, omit the optional section.

## Google Docs compatibility

If the user intends to import the HTML into Google Docs:

- use simple tables;
- avoid scripts, SVG, canvas, fixed positioning, and external fonts;
- use inline text labels for status;
- keep layouts single-column.
