# layout-exempt: rebuild-spec feature↔API/route link validator tests — docs paths are managed targets
"""Tests for validate_feature_api_link.py (Phase 2, v25.0.0).

Covers the degradation contract: pre-migration (no Code/Owner columns) → WARN;
migrated + unresolvable → FAIL; migrated + empty cell → soft WARN; multi-owner
resolution; twin-consistency owner-mismatch (the PR #158-analogue regression
test); missing inventory → WARN never FAIL; exit codes; summary merge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import validate_feature_api_link as v  # noqa: E402
import _route_link_lib as lib  # noqa: E402

ROUTE_INV = {"ROUTE001", "ROUTE002"}
FEAT_INV = {"F001", "F002"}

# route-list.md's normal shape: one sub-table per `### File:` sub-heading under
# Backend Routes — NOT one single table. Regression fixture for the multi-table
# blind spot (reviewer-flagged, confirmed by e2e: a feature citing a code defined
# only in table 2 got a false critical because only table 1 was ever scanned).
TWO_TABLE_MIGRATED = (
    "## Backend Routes\n\n"
    "### File: routes/web.php\n\n"
    "| Method | Path | Code | Owner F### | Handler |\n|---|---|---|---|---|\n"
    "| GET | /orders | ROUTE001 | F001 | OrdersController@index |\n"
    "| POST | /orders | ROUTE002 | F001 | OrdersController@store |\n\n"
    "### File: routes/api.php\n\n"
    "| Method | Path | Code | Owner F### | Handler |\n|---|---|---|---|---|\n"
    "| GET | /api/invoices | ROUTE003 | F002 | InvoicesController@index |\n"
)

TWO_TABLE_HALF_MIGRATED = (
    "## Backend Routes\n\n"
    "### File: routes/web.php\n\n"
    "| Method | Path | Code | Owner F### | Handler |\n|---|---|---|---|---|\n"
    "| GET | /orders | ROUTE001 | F001 | OrdersController@index |\n"
    "| POST | /orders | ROUTE002 | F001 | OrdersController@store |\n\n"
    "### File: routes/api.php\n\n"
    "| Method | Path | Handler |\n|---|---|---|\n"
    "| GET | /api/invoices | InvoicesController@index |\n"
)

TWO_TABLE_PRE_MIGRATION = (
    "## Backend Routes\n\n"
    "### File: routes/web.php\n\n"
    "| Method | Path | Handler |\n|---|---|---|\n"
    "| GET | /orders | OrdersController@index |\n\n"
    "### File: routes/api.php\n\n"
    "| Method | Path | Handler |\n|---|---|---|\n"
    "| GET | /api/invoices | InvoicesController@index |\n"
)

ARTIFACT_REFS_TABLE = (
    "## Artifact References\n\n"
    "| Artifact | File | Codes Used | Reviewed |\n"
    "|----------|------|------------|----------|\n"
    "| Feature List | [feature-list.md](x) | {F001} | [x] |\n"
    "| API Map | [api-map.md](x) | {ROUTE001} | [ ] |\n"
    "| Screens | [screens.md](x) | {SCR001, SCR001/REG001} | [ ] |\n"
)


def _sev(issues, rid):
    return [i for i in issues if i["rule_id"] == rid]


# ---------------------------------------------------------------------------
# PR #165 max-review Critical regressions (C1, C3, C4, C5)
# ---------------------------------------------------------------------------

# C1: a fenced ```markdown``` example table under Backend Routes, documenting the
# expected shape with a FABRICATED ROUTE999/F999 row. Must be excluded from both
# the inventory and the owner map — it is documentation, not a real sub-table.
FENCED_EXAMPLE_ROUTE_LIST = (
    "## Backend Routes\n\n"
    "Example shape:\n\n"
    "```markdown\n"
    "| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
    "| GET | /fake | ROUTE999 | F999 |\n"
    "```\n\n"
    "### File: routes/web.php\n\n"
    "| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
    "| GET | /login | ROUTE001 | F001 |\n"
)

# C4: the SAME ROUTE005 declared in two `### File:` sub-tables with DIFFERENT
# owners — must union owners (not last-wins) AND surface a route_duplicate.
DUPLICATE_ROUTE_LIST = (
    "## Backend Routes\n\n"
    "### File: routes/web.php\n\n"
    "| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
    "| GET | /a | ROUTE005 | F001 |\n\n"
    "### File: routes/api.php\n\n"
    "| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
    "| GET | /b | ROUTE005 | F002 |\n"
)

# C5: Backend Routes table with NO `|---|` separator row — the first (and only)
# data row must still resolve, not be silently dropped by a positional table[2:].
NO_SEPARATOR_ROUTE_LIST = (
    "## Backend Routes\n\n"
    "### File: routes/web.php\n\n"
    "| Method | Path | Code | Owner F### |\n"
    "| GET | /login | ROUTE001 | F001 |\n"
)


class TestCriticalRegressions:
    def test_c1_fenced_example_table_excluded_from_inventory(self):
        inv = lib.build_route_inventory(FENCED_EXAMPLE_ROUTE_LIST)
        assert inv == {"ROUTE001"}
        assert "ROUTE999" not in inv

    def test_c1_fenced_example_table_excluded_from_owner_map(self, tmp_path):
        generated = tmp_path / "docs" / "generated"
        generated.mkdir(parents=True)
        (generated / "route-list.md").write_text(FENCED_EXAMPLE_ROUTE_LIST)
        owner_map = lib.build_route_owner_map(tmp_path / "docs")
        assert "ROUTE999" not in owner_map
        assert owner_map.get("ROUTE001") == {"F001"}

    def test_c1_fenced_example_does_not_produce_feature_unresolved(self, tmp_path):
        """A fabricated F999 owner inside the fenced example must NOT fail
        link.feature_unresolved against a real feature-list.md that lacks F999."""
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "route-list.md").write_text(FENCED_EXAMPLE_ROUTE_LIST)
        (docs / "generated" / "feature-list.md").write_text("F001_Login — login feature\n")
        result = v.validate(docs)
        assert not any("F999" in i["message"] for i in result["issues"]), result["issues"]
        assert result["summary"]["critical"] == 0

    def test_c3_route1000_does_not_collapse_to_route100(self):
        """The pre-fix bare `\\bROUTE\\d{3}` pattern truncated ROUTE1000 to the
        false code ROUTE100 (silent collision). The token_re-guarded pattern must
        never produce that false match — ROUTE1000 is simply not a 3-digit code."""
        codes = lib.cited_routes("cites ROUTE1000 in prose")
        assert "ROUTE100" not in codes

    def test_c3_three_digit_boundary_still_matches(self):
        """Sanity: the fix must not regress the normal 3-digit case."""
        assert lib.cited_routes("cites ROUTE042 here") == {"ROUTE042"}

    def test_c4_duplicate_route_unions_owners(self, tmp_path):
        generated = tmp_path / "docs" / "generated"
        generated.mkdir(parents=True)
        (generated / "route-list.md").write_text(DUPLICATE_ROUTE_LIST)
        owner_map, dups = lib.build_route_owner_map_with_dups(tmp_path / "docs")
        assert owner_map["ROUTE005"] == {"F001", "F002"}
        assert dups == {"ROUTE005"}

    def test_c4_duplicate_route_emits_route_duplicate_critical(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "route-list.md").write_text(DUPLICATE_ROUTE_LIST)
        (docs / "generated" / "feature-list.md").write_text(
            "F001_Orders — orders feature\nF002_Invoices — invoices feature\n")
        result = v.validate(docs)
        dup_issues = _sev(result["issues"], "link.route_duplicate")
        assert len(dup_issues) == 1
        assert dup_issues[0]["severity"] == "critical"
        assert "ROUTE005" in dup_issues[0]["message"]
        assert result["status"] == "FAIL"

    def test_c5_missing_separator_row_still_resolves(self):
        """No `|---|` row: the naive table[2:] slice would drop the ONLY data row.
        Inventory must still see ROUTE001."""
        inv = lib.build_route_inventory(NO_SEPARATOR_ROUTE_LIST)
        assert inv == {"ROUTE001"}

    def test_c5_missing_separator_row_owner_rows_still_resolve(self):
        rows = lib.iter_route_owner_rows(NO_SEPARATOR_ROUTE_LIST)
        assert rows is not None
        codes = {code for code, _owner in rows}
        assert codes == {"ROUTE001"}

    def test_c5_missing_separator_validator_no_false_unresolved(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "route-list.md").write_text(NO_SEPARATOR_ROUTE_LIST)
        (docs / "generated" / "feature-list.md").write_text("F001_Login — login feature\n")
        feat = docs / "features" / "F001_Login"
        feat.mkdir(parents=True)
        (feat / "technical-spec.md").write_text(
            "## Artifact References\n\n| Artifact | File | Codes Used | Reviewed |\n"
            "|----------|------|------------|----------|\n"
            "| API Map | [api-map.md](x) | {ROUTE001} | [ ] |\n")
        result = v.validate(docs)
        assert not _sev(result["issues"], "link.route_unresolved"), result["issues"]
        assert result["status"] == "PASS", result["issues"]


# ---------------------------------------------------------------------------
# _route_link_lib multi-table blind-spot regression (reviewer-flagged)
# ---------------------------------------------------------------------------

class TestMultiTableBackendRoutes:
    def test_inventory_unions_codes_across_all_sub_tables(self):
        inv = lib.build_route_inventory(TWO_TABLE_MIGRATED)
        assert inv == {"ROUTE001", "ROUTE002", "ROUTE003"}

    def test_owner_rows_aggregate_across_all_sub_tables(self):
        rows = lib.iter_route_owner_rows(TWO_TABLE_MIGRATED)
        codes = {code for code, _owner in rows}
        assert codes == {"ROUTE001", "ROUTE002", "ROUTE003"}

    def test_owner_map_resolves_route_from_second_table(self, tmp_path):
        generated = tmp_path / "docs" / "generated"
        generated.mkdir(parents=True)
        (generated / "route-list.md").write_text(TWO_TABLE_MIGRATED)
        owner_map = lib.build_route_owner_map(tmp_path / "docs")
        assert owner_map.get("ROUTE003") == {"F002"}  # table 2's owner, not just table 1's

    def test_half_migrated_yields_rows_from_migrated_table_only(self):
        rows = lib.iter_route_owner_rows(TWO_TABLE_HALF_MIGRATED)
        assert rows is not None  # NOT pure pre-migration — table 1 IS migrated
        codes = {code for code, _owner in rows}
        assert codes == {"ROUTE001", "ROUTE002"}  # table 2 (un-migrated) contributes nothing

    def test_pure_pre_migration_two_tables_returns_none(self):
        assert lib.iter_route_owner_rows(TWO_TABLE_PRE_MIGRATION) is None

    def test_backend_routes_table_stays_first_table_only(self):
        """Back-compat: the single-table accessor intentionally still returns
        only the first sub-table (nav's route_label_map depends on this shape)."""
        table = lib.backend_routes_table(TWO_TABLE_MIGRATED)
        joined = "\n".join(table)
        assert "ROUTE001" in joined
        assert "ROUTE003" not in joined


# ---------------------------------------------------------------------------
# forward: technical-spec.md / behavior-logic.md {ROUTE###} citations
# ---------------------------------------------------------------------------

class TestTechnicalSpecForward:
    def test_resolvable_citation_passes(self):
        assert v.check_technical_spec(ARTIFACT_REFS_TABLE, ROUTE_INV, "f") == []

    def test_unresolvable_route_fails(self):
        text = ARTIFACT_REFS_TABLE.replace("{ROUTE001}", "{ROUTE999}")
        issues = v.check_technical_spec(text, ROUTE_INV, "f")
        assert len(_sev(issues, "link.route_unresolved")) == 1
        assert issues[0]["severity"] == "critical"

    def test_no_table_is_noop(self):
        assert v.check_technical_spec("# no table here\n", ROUTE_INV, "f") == []

    def test_multi_row_table_does_not_bleed_other_codes(self):
        """The Screens row's SCR###/REG### compound tokens must not be mistaken
        for ROUTE### codes, and must not affect the ROUTE row's own check."""
        issues = v.check_technical_spec(ARTIFACT_REFS_TABLE, ROUTE_INV, "f")
        assert issues == []
        # Sanity: a broken ROUTE citation on its own row still fires, proving the
        # other rows (Feature List / Screens) were correctly ignored, not merged.
        text = ARTIFACT_REFS_TABLE.replace("{ROUTE001}", "{ROUTE999}")
        issues = v.check_technical_spec(text, ROUTE_INV, "f")
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# reverse: route-list.md Owner F### column
# ---------------------------------------------------------------------------

class TestRouteListOwnersReverse:
    def test_no_columns_is_pre_migration_warn(self):
        text = ("## Backend Routes\n\n| Method | Path | Handler |\n|---|---|---|\n"
                "| GET | /x | XController@index |\n")
        issues = v.check_route_list_owners(text, FEAT_INV, "f")
        assert len(_sev(issues, "link.pre_migration")) == 1
        assert all(i["severity"] == "warning" for i in issues)

    def test_resolvable_single_owner_passes(self):
        text = ("## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
                "| GET | /x | ROUTE001 | F001 |\n")
        assert v.check_route_list_owners(text, FEAT_INV, "f") == []

    def test_unresolvable_owner_fails(self):
        text = ("## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
                "| GET | /x | ROUTE001 | F999 |\n")
        issues = v.check_route_list_owners(text, FEAT_INV, "f")
        assert len(_sev(issues, "link.feature_unresolved")) == 1
        assert issues[0]["severity"] == "critical"

    def test_empty_owner_cell_is_soft_unmapped_warn(self):
        text = ("## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
                "| GET | /x | ROUTE001 | — |\n")
        issues = v.check_route_list_owners(text, FEAT_INV, "f")
        assert len(_sev(issues, "link.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_multi_owner_cell_both_resolve(self):
        text = ("## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
                "| GET | /x | ROUTE001 | F001, F002 |\n")
        assert v.check_route_list_owners(text, FEAT_INV, "f") == []

    def test_multi_owner_cell_one_unresolvable_fails(self):
        text = ("## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
                "| GET | /x | ROUTE001 | F001, F999 |\n")
        issues = v.check_route_list_owners(text, FEAT_INV, "f")
        assert len(_sev(issues, "link.feature_unresolved")) == 1

    def test_placeholder_template_row_skipped(self):
        text = ("## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
                "| {METHOD} | {PATH} | {ROUTE###} | {F###} |\n")
        assert v.check_route_list_owners(text, FEAT_INV, "f") == []


# ---------------------------------------------------------------------------
# twin-consistency: check_owner_consistency (THE most important test file section)
# ---------------------------------------------------------------------------

class TestOwnerConsistency:
    def test_matching_owner_passes(self):
        route_owner = {"ROUTE001": {"F001"}}
        assert v.check_owner_consistency(ARTIFACT_REFS_TABLE, "F001_Login", route_owner, "f") == []

    def test_owner_mismatch_fails(self):
        """The PR #158-analogue regression test: a feature cites ROUTE001 but
        route-list.md's Owner F### set says a DIFFERENT feature owns it."""
        route_owner = {"ROUTE001": {"F002"}}
        issues = v.check_owner_consistency(ARTIFACT_REFS_TABLE, "F001_Login", route_owner, "f")
        assert len(_sev(issues, "link.owner_mismatch")) == 1
        assert issues[0]["severity"] == "critical"

    def test_multi_owner_membership_passes(self):
        route_owner = {"ROUTE001": {"F001", "F003"}}
        assert v.check_owner_consistency(ARTIFACT_REFS_TABLE, "F001_Login", route_owner, "f") == []

    def test_unclaimed_owner_is_not_a_mismatch(self):
        """Owner F### is `—` (empty set) -> unclaimed, NOT a twin-consistency FAIL."""
        route_owner = {"ROUTE001": set()}
        assert v.check_owner_consistency(ARTIFACT_REFS_TABLE, "F001_Login", route_owner, "f") == []

    def test_unresolved_route_is_not_a_mismatch(self):
        """A route absent from route_owner (never resolved) is not double-reported
        as a mismatch — check_technical_spec already reports link.route_unresolved."""
        assert v.check_owner_consistency(ARTIFACT_REFS_TABLE, "F001_Login", {}, "f") == []

    def test_invalid_feature_dir_name_is_noop(self):
        assert v.check_owner_consistency(ARTIFACT_REFS_TABLE, "NotAFeatureDir", {"ROUTE001": set()}, "f") == []


# ---------------------------------------------------------------------------
# integration: validate() + main() exit codes + summary merge
# ---------------------------------------------------------------------------

def _make_docs(base: Path, owner_cell="F001", route_cite="{ROUTE001}") -> Path:
    docs = base / "docs"
    (docs / "generated").mkdir(parents=True)
    (docs / "generated" / "route-list.md").write_text(
        "## Backend Routes\n\n| Method | Path | Code | Owner F### |\n|---|---|---|---|\n"
        f"| GET | /x | ROUTE001 | {owner_cell} |\n")
    (docs / "generated" / "feature-list.md").write_text("F001_Login — login feature\n")
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "technical-spec.md").write_text(
        "## Artifact References\n\n| Artifact | File | Codes Used | Reviewed |\n"
        "|----------|------|------------|----------|\n"
        f"| API Map | [api-map.md](x) | {route_cite} | [ ] |\n")
    return docs


class TestIntegration:
    def test_validate_passes_on_migrated_docs(self, tmp_path):
        docs = _make_docs(tmp_path)
        result = v.validate(docs)
        assert result["status"] == "PASS", result["issues"]

    def test_validate_fails_on_forward_drift(self, tmp_path):
        docs = _make_docs(tmp_path, route_cite="{ROUTE999}")
        result = v.validate(docs)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "link.route_unresolved" for i in result["issues"])

    def test_pre_migration_route_list_with_citations_warns_not_fails(self, tmp_path):
        """Regression: route-list.md EXISTS but is pre-migration (no Code/Owner
        columns) while technical-spec.md already cites ROUTE### codes — the exact
        advertised-but-unimplemented state this release fixes. Must WARN, never
        FAIL, with exactly one link.pre_migration per direction (not a per-citation
        critical for each cited code)."""
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "route-list.md").write_text(
            "## Backend Routes\n\n| Method | Path | Handler | Middleware |\n|---|---|---|---|\n"
            "| GET | /api/orders | OrdersController@index | auth |\n")
        (docs / "generated" / "feature-list.md").write_text("F001_Orders — orders feature\n")
        feat = docs / "features" / "F001_Orders"
        feat.mkdir(parents=True)
        (feat / "technical-spec.md").write_text(
            "## Artifact References\n\n| Artifact | File | Codes Used | Reviewed |\n"
            "|----------|------|------------|----------|\n"
            "| API Map | [api-map.md](x) | {ROUTE001, ROUTE002} | [ ] |\n")
        result = v.validate(docs)
        assert result["status"] == "WARN", result["issues"]
        assert result["summary"]["critical"] == 0
        pre_migration = _sev(result["issues"], "link.pre_migration")
        assert len(pre_migration) == 2  # one per direction (forward + reverse)
        assert not _sev(result["issues"], "link.route_unresolved")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_validate_fails_on_owner_mismatch(self, tmp_path):
        docs = _make_docs(tmp_path, owner_cell="F002")
        result = v.validate(docs)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "link.owner_mismatch" for i in result["issues"])

    def test_absent_inventory_warns_not_fails(self, tmp_path):
        docs = _make_docs(tmp_path)
        (docs / "generated" / "feature-list.md").unlink()
        result = v.validate(docs)
        assert result["status"] != "FAIL", result["issues"]
        assert any(i["rule_id"] == "link.inventory_absent" for i in result["issues"])

    def test_absent_route_list_warns_not_fails(self, tmp_path):
        docs = _make_docs(tmp_path)
        (docs / "generated" / "route-list.md").unlink()
        result = v.validate(docs)
        assert result["status"] != "FAIL", result["issues"]
        assert any(i["rule_id"] == "link.inventory_absent" for i in result["issues"])

    def test_main_exit_zero_on_pre_migration_warn(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "route-list.md").write_text(
            "## Backend Routes\n\n| Method | Path | Handler |\n|---|---|---|\n| GET | /x | X@i |\n")
        (docs / "generated" / "feature-list.md").write_text("F001 x\n")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_main_exit_one_on_critical(self, tmp_path):
        docs = _make_docs(tmp_path, route_cite="{ROUTE999}")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 1

    def _multi_table_docs(self, base: Path, route_list_text: str, f2_cites="{ROUTE003}") -> Path:
        docs = base / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "route-list.md").write_text(route_list_text)
        (docs / "generated" / "feature-list.md").write_text(
            "F001_Orders — orders feature\nF002_Invoices — invoices feature\n")
        f1 = docs / "features" / "F001_Orders"
        f1.mkdir(parents=True)
        (f1 / "technical-spec.md").write_text(
            "## Artifact References\n\n| Artifact | File | Codes Used | Reviewed |\n"
            "|----------|------|------------|----------|\n"
            "| API Map | [api-map.md](x) | {ROUTE001, ROUTE002} | [ ] |\n")
        f2 = docs / "features" / "F002_Invoices"
        f2.mkdir(parents=True)
        (f2 / "technical-spec.md").write_text(
            "## Artifact References\n\n| Artifact | File | Codes Used | Reviewed |\n"
            "|----------|------|------------|----------|\n"
            f"| API Map | [api-map.md](x) | {f2_cites} | [ ] |\n")
        return docs

    def test_e2e_two_table_migrated_no_false_route_unresolved(self, tmp_path):
        """(a) Fully-migrated 2-sub-table route-list.md: F002 cites ROUTE003, which
        is defined ONLY in the second `### File:` sub-table. Must validate clean —
        this is the exact reviewer-flagged repro that used to FAIL."""
        docs = self._multi_table_docs(tmp_path, TWO_TABLE_MIGRATED)
        result = v.validate(docs)
        assert result["status"] == "PASS", result["issues"]
        assert not _sev(result["issues"], "link.route_unresolved")
        assert not _sev(result["issues"], "link.owner_mismatch")

    def test_e2e_two_table_half_migrated_never_worse_than_warn(self, tmp_path):
        """(b) Table 1 migrated (has Code/Owner, defines ROUTE001), table 2 not
        migrated yet (no Code column at all — its route isn't citable by code
        yet). F001 cites only ROUTE001 (table 1's migrated code) and must resolve
        cleanly; the un-migrated table 2 contributes no codes to the inventory but
        must not push the OVERALL result to a worse state than the pre-fix
        single-table baseline already produced — i.e. never FAIL purely because a
        sibling sub-table hasn't been migrated yet."""
        docs = self._multi_table_docs(tmp_path, TWO_TABLE_HALF_MIGRATED, f2_cites="")
        result = v.validate(docs)
        f1_issues = [i for i in result["issues"] if "F001_Orders" in i["location"]["file"]]
        assert not any(i["severity"] == "critical" for i in f1_issues), f1_issues
        assert result["status"] != "FAIL", result["issues"]

    def test_e2e_two_table_pre_migration_single_warn_per_direction(self, tmp_path):
        """(c) Fully pre-migration 2-sub-table file (existing behavior preserved):
        iter_route_owner_rows is None, exactly one pre_migration WARN per direction,
        never FAIL, regardless of how many sub-tables exist."""
        docs = self._multi_table_docs(tmp_path, TWO_TABLE_PRE_MIGRATION, f2_cites="")
        result = v.validate(docs)
        assert result["status"] == "WARN", result["issues"]
        assert result["summary"]["critical"] == 0
        assert len(_sev(result["issues"], "link.pre_migration")) == 2
        assert not _sev(result["issues"], "link.route_unresolved")

    def test_summary_merge(self, tmp_path):
        docs = _make_docs(tmp_path)
        sp = tmp_path / "validation-summary.json"
        v.main(["--docs-root", str(docs), "--project-root", str(tmp_path),
                "--summary-out", str(sp)])
        data = json.loads(sp.read_text())
        assert "feature_api_link" in data["validators"]
