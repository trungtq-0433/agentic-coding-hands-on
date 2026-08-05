<!-- layout-exempt: rebuild-spec owns docs/generated/db-objects.md — this is the LLM template -->
<!-- Output path: docs/generated/db-objects.md -->
<!-- Source: _digest_extract_sql_schema.json (deterministic DDL parse, high confidence) -->
<!-- Cross-reference: data-model (docs/generated/entities.md) by table NAME — never by shared ID -->

# DB-Object Catalog

**Project**: {PROJECT_NAME}
**Generated**: {DATE}

> **Citation contract:** every object row MUST carry a `**Source:** \`path:line\`` citation.
> `kind` values: `table`, `view`, `sequence`, `trigger`, `procedure`, `package`, `function`, `dataset`.
> `dataset` = flat-file/VSAM COBOL data store (no DDL — cited from the `SELECT`/FD clause).
> Cross-reference with `data-model` (entities.md) uses table NAME, not any shared numeric ID.
> Identifier sanitization: names with `|` are escaped as `\|` before rendering.

---

## Tables

| Name | Purpose | Source |
|------|---------|--------|
| {TABLE_NAME} | {purpose derived from DDL comments or column names} | **Source:** `ddl/tables.sql:1` |
| {TABLE_NAME_2} | {purpose derived from DDL comments or column names} | **Source:** `ddl/tables.sql:45` |

---

## Views

| Name | Purpose | Source |
|------|---------|--------|
| {VIEW_NAME} | {purpose derived from view definition} | **Source:** `ddl/views.sql:10` |

---

## Stored Procedures

| Name | Purpose | Source |
|------|---------|--------|
| {PROC_NAME} | {purpose derived from procedure signature/body} | **Source:** `src/procs/orders.pks:1` |

---

## Sequences

| Name | Purpose | Source |
|------|---------|--------|
| {SEQ_NAME} | Auto-increment key generator for {TABLE_NAME} | **Source:** `ddl/sequences.sql:3` |

---

## Triggers

| Name | Purpose | Source |
|------|---------|--------|
| {TRIGGER_NAME} | {purpose: BEFORE/AFTER INSERT/UPDATE/DELETE on TABLE} | **Source:** `ddl/triggers.sql:7` |

---

## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| {DATASET_NAME} | {purpose derived from record layout / FD comments; flat-file or VSAM COBOL data store} | **Source:** `src/CUSTMAST.cbl:42` |

---

## Summary

| Kind | Count |
|------|-------|
| Tables | {N} |
| Views | {N} |
| Stored Procedures | {N} |
| Sequences | {N} |
| Triggers | {N} |
| Datasets | {N} |
| **Total** | **{N}** |
