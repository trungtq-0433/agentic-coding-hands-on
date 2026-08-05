# Summarize Workflow

Reach for the `tkm:scan-codebase` skill to read the codebase, refresh `docs/codebase-summary.md`, and hand back a summary report.

## Arguments
$1: Focused topics (default: all)
$2: Should scan codebase (`Boolean`, default: `false`)

## Focused Topics
<focused_topics>$1</focused_topics>

## Should Scan Codebase
<should_scan_codebase>$2</should_scan_codebase>

## Important
- Treat `docs/` as the source of truth for documentation.
- Hold off on scanning the whole codebase unless the user asks for it outright.
- **Do not** start implementing.
