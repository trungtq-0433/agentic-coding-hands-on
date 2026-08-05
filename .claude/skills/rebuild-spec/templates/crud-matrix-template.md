<!-- layout-exempt: rebuild-spec owns docs/generated/crud-matrix.md — this is the LLM template -->
<!-- Output path: docs/generated/crud-matrix.md -->
<!-- Sharding: shard by F### feature range (RT-DOC-b). Each shard covers a contiguous F### range.
     Cross-Module section is built in a POST-MERGE pass over the merged matrix — never per-shard.
     Source: _digest_extract_data_flow.json -->

# CRUD Matrix

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Shard**: {SHARD_LABEL} (e.g. F001–F050)

> **Citation contract:** every CRUD cell MUST carry a `**Source:** \`path:line\`` citation.
> Op tokens are strictly `C` (INSERT), `R` (SELECT), `U` (UPDATE), `D` (DELETE).
> MERGE/UPSERT → emit both `C` and `U`. Dynamic SQL marked `[UNVERIFIED]`.
> Identifier sanitization: table/column names with `|` are escaped as `\|` before rendering.

## Feature × Table Matrix

{POPULATED_BY_FRAGMENTS}

### Feature: {F001_FEATURE_NAME}

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| {TABLE_1} | ✓ | ✓ |   |   | id, name | **Source:** `src/Feature1.pas:42` |
| {TABLE_2} |   | ✓ |   |   | id, status | **Source:** `src/Feature1.pas:87` |

### Feature: {F002_FEATURE_NAME}

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| {TABLE_1} |   | ✓ | ✓ |   | id, total | **Source:** `src/Feature2.pas:15` |
| {TABLE_3} | ✓ |   |   |   | id, ref_id | **Source:** `src/Feature2.pas:99` |

---

## Cross-Module Tables

> **Built in post-merge pass only.** Tables touched by ≥ 2 features.
> Do NOT populate this section per-shard — only after merging all shards.

| Table | Features | Operations | Source |
|-------|----------|------------|--------|
| {TABLE_1} | F001, F002 | C, R, U | **Source:** `src/Feature1.pas:42` |
