# layout-exempt: rebuild-spec per-feature README tests — docs/features|screens paths are output targets
"""Tests for the per-feature README + features index (Phases A4/A5).

A4: docs/features/F###_Slug/README.md carries a presence-pruned 4-file reading
order and a best-effort Screen → SCR### → spec table (resolved by name against
generated/screen-list.md, or read from an SCR### column directly — Phase B).
A5: docs/features/README.md indexes every F###_Slug/ subfolder; suppressed when
there is no F### subdir.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_feature_lib import (  # noqa: E402
    build_feature_readme, build_features_index, write_feature_pass,
)
from _nav_table_parse_lib import index_screen_list, parse_screen_names  # noqa: E402
from _nav_strings_en import STRINGS as STRINGS_EN  # noqa: E402
from _nav_strings_vi import STRINGS as STRINGS_VI  # noqa: E402
from _nav_strings_ja import STRINGS as STRINGS_JA  # noqa: E402

TS = "2026-01-01T00:00:00Z"

SCREENS_MD = """# Screens — F001_Login

## Screen List

| Screen Name | What User Sees | What User Can Do |
|-------------|----------------|------------------|
| Login Form | the login page | enter credentials |
| Dashboard | the home dashboard | view widgets |
"""

SCREEN_LIST_MD = """# Screen List

## Screen Index

| Code | Name | Type | Components | Data Displayed |
|------|------|------|------------|----------------|
| SCR001_LoginForm | Login Form | atomic | 3 | 2 |
| SCR002_Dashboard | Dashboard | composite | 5 | 8 |
"""


def _make_feature_tree(base: Path, satellites=("business-context.md", "screens.md",
                                               "technical-spec.md", "edge-cases.md"),
                       with_screen_list=True) -> Path:
    docs = base / "docs"
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    for f in satellites:
        if f == "screens.md":
            (feat / f).write_text(SCREENS_MD)
        else:
            (feat / f).write_text(f"# {f}\n")
    if with_screen_list:
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "screen-list.md").write_text(SCREEN_LIST_MD)
    return docs


# ---------------------------------------------------------------------------
# parsers
# ---------------------------------------------------------------------------

class TestParsers:
    def test_parse_screen_names_basic(self):
        rows = parse_screen_names(SCREENS_MD)
        names = [r["name"] for r in rows]
        assert names == ["Login Form", "Dashboard"]
        assert all(r["scr"] is None for r in rows)  # no SCR### column pre-B

    def test_parse_screen_names_with_scr_column(self):
        md = (
            "## Screen List\n\n"
            "| Screen Name | SCR### | What User Sees |\n"
            "|---|---|---|\n"
            "| Login Form | SCR001_LoginForm | the page |\n"
        )
        rows = parse_screen_names(md)
        assert rows[0]["name"] == "Login Form"
        assert rows[0]["scr"] == "SCR001_LoginForm"

    def test_parse_screen_names_background_feature(self):
        assert parse_screen_names("## Screen List\n\nN/A — background feature.\n") == []

    def test_parse_skips_placeholder_rows(self):
        md = ("## Screen List\n\n| Screen Name | x |\n|---|---|\n| {ScreenName} | y |\n")
        assert parse_screen_names(md) == []

    def test_index_screen_list(self):
        idx = index_screen_list(SCREEN_LIST_MD)
        assert idx["login form"] == "SCR001_LoginForm"
        assert idx["dashboard"] == "SCR002_Dashboard"

    def test_index_screen_list_empty_on_no_table(self):
        assert index_screen_list("# Screen List\n\nnothing here\n") == {}


# ---------------------------------------------------------------------------
# A4 — per-feature README content
# ---------------------------------------------------------------------------

class TestFeatureReadmeContent:
    def test_lists_present_reading_order(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        for f in ("business-context.md", "screens.md", "technical-spec.md", "edge-cases.md"):
            assert f in out
        assert "Reading order" in out

    def test_prunes_absent_satellite(self, tmp_path):
        docs = _make_feature_tree(tmp_path, satellites=("screens.md", "technical-spec.md"))
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "business-context.md" not in out
        assert "edge-cases.md" not in out
        assert "technical-spec.md" in out

    def test_omits_test_cases_when_absent(self, tmp_path):
        """v26.1.0 B6 sidecar: absent by default → byte-identical to pre-B6 output."""
        docs = _make_feature_tree(tmp_path)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "test-cases.md" not in out

    def test_includes_test_cases_when_present(self, tmp_path):
        """v26.1.0 B6 sidecar: presence-pruned in, listed last in reading order."""
        docs = _make_feature_tree(
            tmp_path,
            satellites=("business-context.md", "screens.md", "technical-spec.md",
                       "edge-cases.md", "test-cases.md"),
        )
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "test-cases.md" in out
        assert out.index("edge-cases.md") < out.index("test-cases.md")

    def test_screen_table_resolves_scr(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "Login Form" in out
        assert "SCR001_LoginForm" in out
        assert "../../screens/SCR001_LoginForm/spec.md" in out

    def test_screen_table_unresolved_when_no_screen_list(self, tmp_path):
        docs = _make_feature_tree(tmp_path, with_screen_list=False)
        out = build_feature_readme(str(docs / "features" / "F001_Login"), str(docs), "en", TS)
        assert "Login Form" in out
        # unresolved → em dash in both SCR and Spec cells, no dead link
        assert "../../screens/" not in out
        assert "—" in out

    def test_reads_scr_column_directly(self, tmp_path):
        """Phase-B forward-compat: an SCR### column in screens.md is read directly."""
        docs = tmp_path / "docs"
        feat = docs / "features" / "F001_Login"
        feat.mkdir(parents=True)
        (feat / "screens.md").write_text(
            "## Screen List\n\n| Screen Name | SCR### | What User Sees |\n"
            "|---|---|---|\n| Login Form | SCR009_Login | page |\n"
        )
        out = build_feature_readme(str(feat), str(docs), "en", TS)
        assert "SCR009_Login" in out
        assert "../../screens/SCR009_Login/spec.md" in out

    def test_user_tail_preserved(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        fdir = str(docs / "features" / "F001_Login")
        first = build_feature_readme(fdir, str(docs), "en", TS)
        existing = first + "\n## My Notes\n\nKeep this!\n"
        second = build_feature_readme(fdir, str(docs), "en", TS, existing)
        assert "Keep this!" in second


# ---------------------------------------------------------------------------
# A5 — features index content + write pass
# ---------------------------------------------------------------------------

class TestFeaturesIndex:
    def test_index_lists_feature_subdirs(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        (docs / "features" / "F002_Profile").mkdir()
        out = build_features_index(str(docs / "features"), str(docs), "en", TS)
        assert "F001_Login" in out
        assert "F002_Profile" in out

    def test_write_pass_writes_per_feature_and_index(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        write_feature_pass(str(docs), "en", TS)
        assert (docs / "features" / "F001_Login" / "README.md").is_file()
        assert (docs / "features" / "README.md").is_file()

    def test_write_pass_never_recurses_into_screens(self, tmp_path):
        docs = _make_feature_tree(tmp_path)
        (docs / "screens" / "SCR001_LoginForm").mkdir(parents=True)
        (docs / "screens" / "SCR001_LoginForm" / "spec.md").write_text("# spec\n")
        write_feature_pass(str(docs), "en", TS)
        # The pass is scoped to features/*/ — it must NOT write into screens/SCR###/.
        assert not (docs / "screens" / "SCR001_LoginForm" / "README.md").exists()


# ---------------------------------------------------------------------------
# locale parity
# ---------------------------------------------------------------------------

class TestFeatureReadmeLocaleParity:
    _LOCALES = {"en": STRINGS_EN, "vi": STRINGS_VI, "ja": STRINGS_JA}

    def test_feature_readme_key_parity(self):
        sets = {lang: set(s.get("feature_readme", {})) for lang, s in self._LOCALES.items()}
        assert sets["en"] == sets["vi"] == sets["ja"], f"feature_readme key drift: {sets}"

    def test_file_purposes_key_parity(self):
        sets = {lang: set(s["feature_readme"]["file_purposes"]) for lang, s in self._LOCALES.items()}
        assert sets["en"] == sets["vi"] == sets["ja"], f"file_purposes key drift: {sets}"

    def test_features_index_key_parity(self):
        sets = {lang: set(s.get("features_index", {})) for lang, s in self._LOCALES.items()}
        assert sets["en"] == sets["vi"] == sets["ja"], f"features_index key drift: {sets}"
