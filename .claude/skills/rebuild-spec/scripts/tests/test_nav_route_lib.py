# layout-exempt: rebuild-spec nav route-link tests — docs/features|generated paths are output targets
"""Tests for the per-feature Route/API table (Phase 4, v25.0.0).

Mirrors test_nav_feature_readme.py's Screen-table test shape: presence-pruning (no
ROUTE### citation → no section), resolvable citation → correct table row, missing/
pre-migration route-list.md → graceful omission (nav is best-effort, never crashes).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_feature_lib import build_feature_readme  # noqa: E402
from _nav_route_lib import build_route_table_rows, route_label_map  # noqa: E402
from _nav_strings_en import STRINGS as STRINGS_EN  # noqa: E402
from _nav_strings_ja import STRINGS as STRINGS_JA  # noqa: E402
from _nav_strings_vi import STRINGS as STRINGS_VI  # noqa: E402

TS = "2026-01-01T00:00:00Z"

ROUTE_LIST_MD = """# Route List

## Backend Routes

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /api/users | ROUTE001 | F001 | UsersController@index | auth |
| POST | /api/users | ROUTE002 | F001 | UsersController@store | auth |
"""

ROUTE_LIST_MD_PRE_MIGRATION = """# Route List

## Backend Routes

| Method | Path | Handler | Middleware |
|--------|------|---------|------------|
| GET | /api/users | UsersController@index | auth |
"""

# route-list.md's documented shape: one Backend Routes sub-table per `### File:`
# heading, not a single monolithic table. A route defined in the SECOND sub-table
# must still resolve to a Method+Path label (regression fixture for the multi-table
# fix — route_label_map() must loop over every sub-table, not just the first).
ROUTE_LIST_MD_MULTI_TABLE = """# Route List

## Backend Routes

### File: routes/users.php

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /api/users | ROUTE001 | F001 | UsersController@index | auth |

### File: routes/orders.php

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| POST | /api/orders | ROUTE010 | F002 | OrdersController@store | auth |
"""

# C5 (PR #165 max-review): no `|---|` separator row — the ONLY data row must
# still resolve, not be silently dropped by a positional table[2:] slice.
ROUTE_LIST_MD_NO_SEPARATOR = """# Route List

## Backend Routes

| Method | Path | Code | Owner F### | Handler | Middleware |
| GET | /api/users | ROUTE001 | F001 | UsersController@index | auth |
"""

TECH_SPEC_SECOND_TABLE_ROUTE = """# Technical Spec — F002

## Artifact References

| Artifact | Codes Used |
|----------|------------|
| route-list.md | ROUTE010 |
"""

TECH_SPEC_WITH_ROUTE = """# Technical Spec — F001

## Artifact References

| Artifact | Codes Used |
|----------|------------|
| route-list.md | ROUTE001, ROUTE002 |
"""

TECH_SPEC_UNRESOLVED_ROUTE = """# Technical Spec — F001

## Artifact References

| Artifact | Codes Used |
|----------|------------|
| route-list.md | ROUTE999 |
"""

TECH_SPEC_NO_ROUTE = """# Technical Spec — F001

## Artifact References

| Artifact | Codes Used |
|----------|------------|
| feature-list.md | F001 |
"""


def _make_feature_tree(base: Path, tech_spec: str | None = TECH_SPEC_WITH_ROUTE,
                       route_list: str | None = ROUTE_LIST_MD) -> Path:
    docs = base / "docs"
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    if tech_spec is not None:
        (feat / "technical-spec.md").write_text(tech_spec)
    if route_list is not None:
        (docs / "generated").mkdir(parents=True, exist_ok=True)
        (docs / "generated" / "route-list.md").write_text(route_list)
    return docs


# ---------------------------------------------------------------------------
# _nav_route_lib resolution helpers
# ---------------------------------------------------------------------------

class TestRouteLabelMap:
    def test_maps_code_to_method_and_path(self):
        labels = route_label_map(ROUTE_LIST_MD)
        assert labels["ROUTE001"] == ("GET", "/api/users")
        assert labels["ROUTE002"] == ("POST", "/api/users")

    def test_empty_on_pre_migration_table(self):
        assert route_label_map(ROUTE_LIST_MD_PRE_MIGRATION) == {}

    def test_empty_on_no_table(self):
        assert route_label_map("# nothing here\n") == {}

    def test_resolves_route_in_second_sub_table(self):
        """route-list.md's real shape is multiple ### File: sub-tables — a route
        defined only in the SECOND table must still resolve (regression: an earlier
        implementation used the first-table-only accessor and missed this)."""
        labels = route_label_map(ROUTE_LIST_MD_MULTI_TABLE)
        assert labels["ROUTE001"] == ("GET", "/api/users")
        assert labels["ROUTE010"] == ("POST", "/api/orders")

    def test_c5_resolves_route_when_separator_row_missing(self):
        """PR #165 max-review C5: a table missing its `|---|` separator must not
        have its first (and only) data row silently dropped by table[2:]."""
        labels = route_label_map(ROUTE_LIST_MD_NO_SEPARATOR)
        assert labels["ROUTE001"] == ("GET", "/api/users")


class TestBuildRouteTableRows:
    def test_resolves_cited_routes(self):
        rows = build_route_table_rows(TECH_SPEC_WITH_ROUTE, ROUTE_LIST_MD)
        codes = {r["code"] for r in rows}
        assert codes == {"ROUTE001", "ROUTE002"}
        row = next(r for r in rows if r["code"] == "ROUTE001")
        assert row["method"] == "GET"
        assert row["path"] == "/api/users"

    def test_no_citations_yields_no_rows(self):
        assert build_route_table_rows(TECH_SPEC_NO_ROUTE, ROUTE_LIST_MD) == []

    def test_unresolvable_citation_yields_unresolved_row(self):
        rows = build_route_table_rows(TECH_SPEC_UNRESOLVED_ROUTE, ROUTE_LIST_MD)
        assert len(rows) == 1
        assert rows[0]["code"] == "ROUTE999"
        assert rows[0]["method"] is None
        assert rows[0]["path"] is None

    def test_missing_route_list_yields_unresolved_rows(self):
        rows = build_route_table_rows(TECH_SPEC_WITH_ROUTE, None)
        assert len(rows) == 2
        assert all(r["method"] is None for r in rows)


# ---------------------------------------------------------------------------
# build_feature_readme integration — presence pruning
# ---------------------------------------------------------------------------

class TestFeatureReadmeRouteSection:
    def test_renders_route_table_when_citations_present(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "ROUTE001" in out
        assert "GET" in out
        assert "/api/users" in out
        assert "../../generated/route-list.md" in out

    def test_no_section_when_no_citations(self, tmp_path):
        docs = _make_feature_tree(tmp_path, tech_spec=TECH_SPEC_NO_ROUTE)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "ROUTE" not in out

    def test_no_section_when_no_technical_spec(self, tmp_path):
        docs = _make_feature_tree(tmp_path, tech_spec=None)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "ROUTE" not in out

    def test_graceful_omission_when_route_list_missing(self, tmp_path):
        docs = _make_feature_tree(tmp_path, route_list=None)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        # best-effort: citation exists but route-list.md absent → unresolved row, no crash
        assert "ROUTE001" in out
        assert "—" in out

    def test_graceful_omission_when_route_list_pre_migration(self, tmp_path):
        docs = _make_feature_tree(tmp_path, route_list=ROUTE_LIST_MD_PRE_MIGRATION)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "ROUTE001" in out
        assert "—" in out

    def test_resolves_citation_from_second_sub_table(self, tmp_path):
        docs = _make_feature_tree(
            tmp_path, tech_spec=TECH_SPEC_SECOND_TABLE_ROUTE,
            route_list=ROUTE_LIST_MD_MULTI_TABLE,
        )
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "ROUTE010" in out
        assert "POST" in out
        assert "/api/orders" in out
        assert "../../generated/route-list.md" in out


# ---------------------------------------------------------------------------
# locale parity — route table column keys
# ---------------------------------------------------------------------------

class TestRouteTableLocaleParity:
    _LOCALES = {"en": STRINGS_EN, "vi": STRINGS_VI, "ja": STRINGS_JA}

    def test_feature_readme_route_keys_parity(self):
        sets = {lang: set(s.get("feature_readme", {})) for lang, s in self._LOCALES.items()}
        assert sets["en"] == sets["vi"] == sets["ja"], f"feature_readme key drift: {sets}"
        # route-table keys specifically must be present in all locales
        for lang, s in self._LOCALES.items():
            fr = s["feature_readme"]
            assert "routes_heading" in fr, f"{lang}: missing routes_heading"
            assert "col_route" in fr, f"{lang}: missing col_route"
            assert "col_route_owner" in fr, f"{lang}: missing col_route_owner"
            assert "col_route_spec" in fr, f"{lang}: missing col_route_spec"

    def test_relationship_map_equal_line_count(self):
        counts = {lang: len(s["relationship_map"]) for lang, s in self._LOCALES.items()}
        assert counts["en"] == counts["vi"] == counts["ja"], f"line-count drift: {counts}"

    def test_relationship_map_mentions_route_list_and_unbound_views(self):
        joined = " ".join(STRINGS_EN["relationship_map"])
        assert "route-list.md" in joined
        assert "api-map.md" in joined or "api-contracts.md" in joined
