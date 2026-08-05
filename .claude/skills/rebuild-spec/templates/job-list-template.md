<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Job List

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

**Code Format**: All codes MUST follow `JOB###_NameSlug` format (e.g., JOB001_NightlyReportExport,
JOB002_SendWelcomeEmail). File-global, sequential in order of discovery — do NOT reset per type.

**Scope**: One row/section per `behavior-logic.md` (`BL###`) entry whose `**Type**` is
`scheduled-job`, `queue-worker`, or `custom-command` (per `references/bl-source-patterns.md`'s
10-type taxonomy). This is a re-projection, not a re-detection — every JOB### traces back to
exactly one BL### (DRY boundary: `behavior-logic.md` is the inventory of record; this file is the
per-job operational detail expansion, same relationship `--screen-specs` has to `screen-list.md`).

**No `docs/jobs/` namespace**: this is a SINGLE artifact (inventory + per-job detail sections in
one file, per F13). Shard only if this file exceeds 800 LOC (`references/artifact-sharding.md`).

---

## Job Index

| Code | Name | BL Ref | Type | Schedule/Trigger |
|------|------|--------|------|-------------------|
| {JOB001_CODE} | {JOB001_NAME} | {BL_REF} | {TYPE} | {SCHEDULE} |
| {JOB002_CODE} | {JOB002_NAME} | {BL_REF} | {TYPE} | {SCHEDULE} |
| {JOB003_CODE} | {JOB003_NAME} | {BL_REF} | {TYPE} | {SCHEDULE} |

---

## {JOB001_CODE}: {JOB001_NAME}

**BL Ref**: {BL_REF} <!-- the single behavior-logic.md BL### this job expands -->
**Type**: {scheduled-job | queue-worker | custom-command}
**Source**: `{relative/path/to/File.ext}:{line}`

### Purpose

{One-paragraph plain-language description of what this job does and why it exists.}

### Schedule / Trigger

{Cron expression | queue name + concurrency | invocation command — cite the exact schedule
definition, e.g. `config/schedule.rb:12` or `@Cron("0 2 * * *")`.}

### Data Touched

- {MODEL_ENTITY or table name} — {read | write | both}

### Failure / Retry Behavior

{Retry policy (max attempts, backoff), dead-letter/failure queue, alerting on exhaustion — cite
source. `N/A — no retry policy found in source.` if genuinely absent (do not invent one).}

---

## {JOB002_CODE}: {JOB002_NAME}

**BL Ref**: {BL_REF}
**Type**: {scheduled-job | queue-worker | custom-command}
**Source**: `{relative/path/to/File.ext}:{line}`

### Purpose

{DESCRIPTION}

### Schedule / Trigger

{SCHEDULE}

### Data Touched

- {MODEL_ENTITY}

### Failure / Retry Behavior

{RETRY_BEHAVIOR}

---

## Summary

- **Total Jobs**: {TOTAL_JOBS}
- **By Type**: scheduled-job: {N}, queue-worker: {N}, custom-command: {N}

---

## Cross-Reference Validation

- [x] All JOB### codes are unique (file-global — never reset)
- [x] Every JOB### traces to exactly one BL### in `behavior-logic.md` (no invented jobs)
- [x] No job content duplicates its source BL### entry verbatim (dedup — operational detail only)
- [x] Every job section has a `**Source**` citation (`file:line`)

<!--
=============================================================================
APPENDIX — WORKED EXAMPLE (Reference Only; DELETE THIS HTML-COMMENT BLOCK
BEFORE SUBMITTING A REAL JOB LIST. Fabricated codes used here must NOT
appear in the generated output.)
=============================================================================

## JOB004_NightlyInvoiceExport

**BL Ref**: BL012_NightlyInvoiceExport
**Type**: scheduled-job
**Source**: `app/jobs/scheduled/invoice_export_job.rb:8`

### Purpose

Exports the previous day's paid invoices to the finance team's shared drive as a CSV so the
finance team does not need direct database access.

### Schedule / Trigger

Runs daily at 02:00 UTC via `config/schedule.rb:14` (`every 1.day, at: '2:00 am'`).

### Data Touched

- Invoice — read
- ExportLog — write

### Failure / Retry Behavior

Sidekiq default retry (25 attempts, exponential backoff); on final failure, writes to the
`sidekiq_dead` queue and pages on-call via the existing alerting integration
(`app/jobs/scheduled/invoice_export_job.rb:41`).
=============================================================================
-->
