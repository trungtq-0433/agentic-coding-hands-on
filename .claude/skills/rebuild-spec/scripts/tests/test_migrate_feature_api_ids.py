# layout-exempt: rebuild-spec feature↔API migration tests — docs paths are managed targets
"""Tests for migrate-feature-api-ids.py (Phase 3, v25.0.0).

Covers: citation-scan from technical-spec.md's Artifact References table (via
_route_link_lib.artifact_ref_cited_routes), forward Code + reverse Owner F###
backfill into route-list.md's Backend Routes table(s), PER-TABLE idempotency on
multi-`### File:` route-list.md (reviewer C1 regression), non-destructive cells,
absent-bridge WARN+noop, multi-owner attribution, zero-citation "—", and EOL
preservation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

_spec = importlib.util.spec_from_file_location(
    "migrate_feature_api_ids", SCRIPTS / "migrate-feature-api-ids.py")
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

TECH_SPEC_F001 = """# Technical Spec — F001_Login

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../docs/system/system-overview.md) | — | [x] |
| API Map | [api-map.md](../../docs/generated/api-map.md) | ROUTE001, ROUTE002 | [ ] |
| Entities | [entities.md](../../docs/generated/entities.md) | MODEL001 | [ ] |

## Assumptions
x
"""

TECH_SPEC_F002 = """# Technical Spec — F002_Dashboard

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| API Map | [api-map.md](../../docs/generated/api-map.md) | ROUTE002 | [ ] |

## Assumptions
x
"""

ROUTE_LIST = """# Route List

## Backend Routes

### File: routes/web.php

| Method | Path | Handler | Middleware |
|--------|------|---------|------------|
| GET | /login | LoginController@show | guest |
| POST | /login | LoginController@store | guest |
| GET | /health | HealthController@ping | — |

## Frontend Routes/Pages
"""

# Two Backend Routes sub-tables, BOTH un-migrated — the real-world multi-file
# shape `_locate_backend_routes_tables` was built to handle (reviewer C1 gap:
# the original ROUTE_LIST fixture had only one such table).
ROUTE_LIST_MULTI_UNMIGRATED = """# Route List

## Backend Routes

### File: routes/web.php

| Method | Path | Handler | Middleware |
|--------|------|---------|------------|
| GET | /login | LoginController@show | guest |
| POST | /login | LoginController@store | guest |

### File: routes/api.php

| Method | Path | Handler | Middleware |
|--------|------|---------|------------|
| GET | /orders | OrdersController@index | auth |

## Frontend Routes/Pages
"""

# Table 1 (web.php) already migrated; table 2 (api.php) is NOT.
ROUTE_LIST_TABLE1_DONE = """# Route List

## Backend Routes

### File: routes/web.php

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /login | ROUTE001 | F001 | LoginController@show | guest |
| POST | /login | ROUTE002 | F001 | LoginController@store | guest |

### File: routes/api.php

| Method | Path | Handler | Middleware |
|--------|------|---------|------------|
| GET | /orders | OrdersController@index | auth |

## Frontend Routes/Pages
"""

# Table 1 (web.php) is NOT migrated; table 2 (api.php) already IS.
ROUTE_LIST_TABLE2_DONE = """# Route List

## Backend Routes

### File: routes/web.php

| Method | Path | Handler | Middleware |
|--------|------|---------|------------|
| GET | /login | LoginController@show | guest |
| POST | /login | LoginController@store | guest |

### File: routes/api.php

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /orders | ROUTE001 | F001 | OrdersController@index | auth |

## Frontend Routes/Pages
"""


# C1 (PR #165 max-review): fenced ```markdown``` example table under Backend
# Routes, with a fabricated ROUTE999 row — must be excluded from span detection
# entirely (not migrated, not counted toward numbering).
ROUTE_LIST_FENCED_EXAMPLE = """# Route List

## Backend Routes

Example shape:

```markdown
| Method | Path | Code | Owner F### |
|---|---|---|---|
| GET | /fake | ROUTE999 | F999 |
```

### File: routes/web.php

| Method | Path | Handler |
|--------|------|---------|
| GET | /login | LoginController@show |

## Frontend Routes/Pages
"""

# C2 (PR #165 max-review): a Path cell with an UNESCAPED `|` — splitting naively
# on `|` corrupts the row's cell count. The corrupted row must be left untouched
# (byte-identical) and WARNed; the clean sibling row still migrates normally.
ROUTE_LIST_PIPE_IN_CELL = """# Route List

## Backend Routes

### File: routes/web.php

| Method | Path | Handler |
|--------|------|---------|
| GET | /api/x\\|y | XController@show |
| GET | /clean | CleanController@show |

## Frontend Routes/Pages
"""

# C5 (PR #165 max-review): table missing its `|---|` separator row — the ONLY
# data row must still be treated as data, not overwritten as a fake separator.
ROUTE_LIST_NO_SEPARATOR = """# Route List

## Backend Routes

### File: routes/web.php

| Method | Path | Handler |
| GET | /login | LoginController@show |

## Frontend Routes/Pages
"""


def _make_tree(base: Path, with_specs=True) -> Path:
    docs = base / "docs"
    gen = docs / "generated"
    gen.mkdir(parents=True)
    gen.joinpath("route-list.md").write_text(ROUTE_LIST)
    if with_specs:
        f1 = docs / "features" / "F001_Login"
        f1.mkdir(parents=True)
        f1.joinpath("technical-spec.md").write_text(TECH_SPEC_F001)
        f2 = docs / "features" / "F002_Dashboard"
        f2.mkdir(parents=True)
        f2.joinpath("technical-spec.md").write_text(TECH_SPEC_F002)
    return docs


class TestCitationScan:
    def test_maps_route_to_citing_feature_bare_token(self, tmp_path):
        """Owner cell must be the BARE F### code, never the F###_Slug directory name
        (route-list-template.md's Code Column Contract mandates bare F### tokens,
        matching every other bound ID pair's convention)."""
        docs = _make_tree(tmp_path)
        m = mig.parse_technical_spec_citations(docs)
        assert m["ROUTE001"] == ["F001"]
        assert "F001_Login" not in m["ROUTE001"]

    def test_multi_owner_route_bare_tokens(self, tmp_path):
        docs = _make_tree(tmp_path)
        m = mig.parse_technical_spec_citations(docs)
        assert m["ROUTE002"] == ["F001", "F002"]

    def test_no_specs_returns_empty(self, tmp_path):
        docs = _make_tree(tmp_path, with_specs=False)
        assert mig.parse_technical_spec_citations(docs) == {}


class TestForward:
    def test_inserts_code_and_owner_columns_bare_tokens(self):
        """Owner F### cells hold BARE tokens (F001, F001, F002), never F###_Slug."""
        cmap = {"ROUTE001": ["F001"], "ROUTE002": ["F001", "F002"]}
        new, changed, unattributed, _warnings = mig.backfill_route_list(ROUTE_LIST, cmap)
        assert changed
        assert "| Method | Path | Code | Owner F### | Handler | Middleware |" in new
        assert "| ROUTE001 | F001 |" in new
        assert "| ROUTE002 | F001, F002 |" in new
        assert "F001_Login" not in new and "F002_Dashboard" not in new
        assert unattributed == 1  # /health uncited

    def test_idempotent_when_columns_present(self):
        cmap = {"ROUTE001": ["F001"]}
        once, _, _, _ = mig.backfill_route_list(ROUTE_LIST, cmap)
        twice, changed, _, _ = mig.backfill_route_list(once, cmap)
        assert changed is False and twice == once

    def test_zero_citation_left_as_dash(self):
        new, changed, unattributed, _warnings = mig.backfill_route_list(ROUTE_LIST, {})
        assert changed and unattributed == 3
        assert "| — |" in new or "| —" in new

    def test_non_destructive_cells_preserved(self):
        cmap = {"ROUTE001": ["F001"]}
        new, _, _, _ = mig.backfill_route_list(ROUTE_LIST, cmap)
        assert "LoginController@show" in new
        assert "LoginController@store" in new
        assert "HealthController@ping" in new
        assert "guest" in new

    def test_contiguous_codes_first_appearance_order(self):
        new, _, _, _ = mig.backfill_route_list(ROUTE_LIST, {})
        rows = [ln for ln in new.splitlines() if ln.strip().startswith("| GET") or
                ln.strip().startswith("| POST")]
        assert "ROUTE001" in rows[0]
        assert "ROUTE002" in rows[1]
        assert "ROUTE003" in rows[2]

    def test_crlf_eol_preserved(self):
        text = ("## Backend Routes\r\n\r\n"
                "| Method | Path | Handler | Middleware |\r\n"
                "|---|---|---|---|\r\n"
                "| GET | /x | X@show | — |\r\n")
        new, changed, _, _ = mig.backfill_route_list(text, {})
        assert changed
        assert "\r\n| Method | Path | Code | Owner F### | Handler | Middleware |" in new


class TestMultiTable:
    """Reviewer C1 regression: idempotency + numbering must be decided PER TABLE,
    not just from spans[0]'s header, on a route-list.md with multiple `### File:`
    Backend Routes sub-tables."""

    def test_fully_unmigrated_multi_table_gets_contiguous_codes(self):
        cmap = {"ROUTE001": ["F001"], "ROUTE003": ["F002"]}
        new, changed, unattributed, _warnings = mig.backfill_route_list(ROUTE_LIST_MULTI_UNMIGRATED, cmap)
        assert changed
        assert new.count("| Method | Path | Code | Owner F### | Handler | Middleware |") == 2
        assert "| ROUTE001 | F001 |" in new
        assert "| ROUTE002 | — |" in new
        assert "| ROUTE003 | F002 |" in new  # 2nd table continues the same sequence
        assert unattributed == 1

    def test_table1_migrated_table2_not__table1_untouched_table2_migrated(self):
        """Table 1 already has Code/Owner — must be left BYTE-IDENTICAL (no false
        idempotency-skip of table 2, no double-insert into table 1)."""
        cmap = {"ROUTE003": ["F002"]}
        new, changed, unattributed, _warnings = mig.backfill_route_list(ROUTE_LIST_TABLE1_DONE, cmap)
        assert changed  # NOT a false no-op — table 2 still needs migrating
        # table 1's original rows preserved verbatim, no double Code/Owner columns
        assert "| GET | /login | ROUTE001 | F001 | LoginController@show | guest |" in new
        # neither header row has two Code/Owner pairs (the exact corruption reviewer found)
        assert "Code | Owner F### | Code | Owner F###" not in new
        # table 2 gets the next contiguous code, continuing from table 1's ROUTE002
        assert "| GET | /orders | ROUTE003 | F002 | OrdersController@index | auth |" in new
        assert unattributed == 0

    def test_table1_not_table2_migrated__table2_untouched_no_double_insert(self):
        """Table 2 already has Code/Owner — must be left BYTE-IDENTICAL (previously
        this direction double-inserted columns into table 2, corrupting it)."""
        cmap = {"ROUTE002": ["F001"]}
        new, changed, unattributed, _warnings = mig.backfill_route_list(ROUTE_LIST_TABLE2_DONE, cmap)
        assert changed  # table 1 still needs migrating
        # table 2's original row preserved verbatim — NOT double Code/Owner cells
        assert "| GET | /orders | ROUTE001 | F001 | OrdersController@index | auth |" in new
        # neither header row has two Code/Owner pairs (the exact corruption reviewer found)
        assert "Code | Owner F### | Code | Owner F###" not in new
        assert "ROUTE002 | — | ROUTE001" not in new  # the exact corrupted data row reviewer found
        # table 1 gets codes that do NOT collide with table 2's existing ROUTE001
        assert "| GET | /login | ROUTE002 | F001 | LoginController@show | guest |" in new
        assert "| POST | /login | ROUTE003 | — | LoginController@store | guest |" in new
        assert unattributed == 1  # POST /login uncited in cmap

    def test_idempotent_when_all_tables_already_migrated(self):
        cmap = {"ROUTE001": ["F001"], "ROUTE002": ["F001"]}
        once, _, _, _ = mig.backfill_route_list(ROUTE_LIST_MULTI_UNMIGRATED, cmap)
        twice, changed, _, _ = mig.backfill_route_list(once, cmap)
        assert changed is False and twice == once

    def test_half_migrated_second_run_is_stable(self):
        """Running backfill on an already-half-migrated file a 2nd time changes
        nothing further (table 1's fix-up run is itself idempotent)."""
        cmap = {"ROUTE003": ["F002"]}
        once, _, _, _ = mig.backfill_route_list(ROUTE_LIST_TABLE1_DONE, cmap)
        twice, changed, _, _ = mig.backfill_route_list(once, cmap)
        assert changed is False and twice == once


class TestCriticalRegressions:
    """PR #165 max-review Critical regressions in migration's own scan/write path
    (C1, C2, C5 — C1/C5 do NOT propagate here for free since migration has its own
    header/row scanner, independent of _route_link_lib; C2 is migration-only)."""

    def test_c1_fenced_example_table_not_migrated(self):
        new, changed, unattributed, warnings = mig.backfill_route_list(
            ROUTE_LIST_FENCED_EXAMPLE, {})
        assert changed  # the real table still needs migrating
        # fenced block is documentation-only and stays byte-identical to the source
        fenced_block = new.split("```markdown")[1].split("```")[0]
        src_fenced_block = ROUTE_LIST_FENCED_EXAMPLE.split("```markdown")[1].split("```")[0]
        assert fenced_block == src_fenced_block
        real_block = new.split("### File:")[1]
        assert "ROUTE001" in real_block  # real table numbered starting from 001,
        assert "ROUTE999" not in real_block  # not continuing from the fake ROUTE999

    def test_c2_pipe_in_cell_row_left_untouched_and_warned(self):
        new, changed, unattributed, warnings = mig.backfill_route_list(
            ROUTE_LIST_PIPE_IN_CELL, {})
        assert changed  # the clean row still gets migrated
        assert len(warnings) == 1
        assert "cell-count" in warnings[0]
        # the corrupted row is NOT rewritten: byte-identical to the source line
        src_line = next(ln for ln in ROUTE_LIST_PIPE_IN_CELL.splitlines() if "/api/x" in ln)
        corrupted_line = next(ln for ln in new.splitlines() if "/api/x" in ln)
        assert corrupted_line == src_line
        assert "Code" not in corrupted_line and "Owner" not in corrupted_line
        # the clean sibling row DID get migrated
        clean_line = next(ln for ln in new.splitlines() if "/clean" in ln)
        assert "ROUTE001" in clean_line

    def test_c5_missing_separator_first_row_migrated_not_overwritten(self):
        new, changed, unattributed, warnings = mig.backfill_route_list(
            ROUTE_LIST_NO_SEPARATOR, {})
        assert changed
        assert "LoginController@show" in new  # handler content preserved
        assert "ROUTE001" in new  # the only data row got a real code
        assert "------" not in new  # no synthetic separator cells inserted anywhere


class TestMigrateValidateE2E:
    """migrate -> validate over ONE shared fixture (repo lesson: units alone missed
    cross-contract bugs in the sibling screen-link work). Exercises the plan's
    Constraint 6."""

    def test_migrate_then_validate_passes(self, tmp_path):
        docs = _make_tree(tmp_path)
        rc = mig.migrate(docs)
        assert rc == 0
        sys.path.insert(0, str(SCRIPTS))
        import validate_feature_api_link as val
        result = val.validate(docs)
        assert result["summary"]["critical"] == 0, result["issues"]

    def test_migrate_then_validate_missing_separator_variant(self, tmp_path):
        """C5 parity: migrate a table with NO |---| separator, then validate it —
        both must agree the sole data row resolved, not silently dropped."""
        tech_spec_route001_only = (
            "# Technical Spec — F001_Login\n\n## Artifact References\n\n"
            "| Artifact | File | Codes Used | Reviewed |\n"
            "|----------|------|------------|----------|\n"
            "| API Map | [api-map.md](../../docs/generated/api-map.md) | ROUTE001 | [ ] |\n"
        )
        docs = tmp_path / "docs"
        gen = docs / "generated"
        gen.mkdir(parents=True)
        gen.joinpath("route-list.md").write_text(ROUTE_LIST_NO_SEPARATOR)
        f1 = docs / "features" / "F001_Login"
        f1.mkdir(parents=True)
        f1.joinpath("technical-spec.md").write_text(tech_spec_route001_only)
        rc = mig.migrate(docs)
        assert rc == 0
        sys.path.insert(0, str(SCRIPTS))
        import validate_feature_api_link as val
        result = val.validate(docs)
        assert not [i for i in result["issues"] if i["rule_id"] == "link.route_unresolved"], \
            result["issues"]


class TestEndToEnd:
    def test_full_migration_backfills_route_list(self, tmp_path):
        docs = _make_tree(tmp_path)
        rc = mig.migrate(docs)
        assert rc == 0
        rl = (docs / "generated" / "route-list.md").read_text()
        assert "Code" in rl and "Owner F###" in rl
        assert "| ROUTE001 | F001 |" in rl  # bare token, not F001_Login
        assert "F001_Login" not in rl

    def test_second_run_is_noop(self, tmp_path):
        docs = _make_tree(tmp_path)
        mig.migrate(docs)
        before = (docs / "generated" / "route-list.md").read_text()
        mig.migrate(docs)
        assert (docs / "generated" / "route-list.md").read_text() == before

    def test_missing_bridge_non_destructive(self, tmp_path):
        docs = _make_tree(tmp_path, with_specs=False)
        before = (docs / "generated" / "route-list.md").read_text()
        rc = mig.migrate(docs)
        assert rc == 0
        assert (docs / "generated" / "route-list.md").read_text() == before

    def test_missing_route_list_noop(self, tmp_path):
        docs = tmp_path / "docs"
        f1 = docs / "features" / "F001_Login"
        f1.mkdir(parents=True)
        f1.joinpath("technical-spec.md").write_text(TECH_SPEC_F001)
        rc = mig.migrate(docs)
        assert rc == 0
        assert not (docs / "generated" / "route-list.md").exists()
