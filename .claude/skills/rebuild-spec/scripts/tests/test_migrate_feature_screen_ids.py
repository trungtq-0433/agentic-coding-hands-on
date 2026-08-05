# layout-exempt: rebuild-spec feature↔screen migration tests — docs paths are managed targets
"""Tests for migrate-feature-screen-ids.py (Phase B, v24.0.0).

Covers: forward column backfill from screen-list.md, reverse Feature backlink from the
screen-flow bridge, idempotency (2nd run = no change), missing-bridge non-destructive
exit, and hand-edited prose preservation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

# Hyphenated module name → load via importlib.
_spec = importlib.util.spec_from_file_location(
    "migrate_feature_screen_ids", SCRIPTS / "migrate-feature-screen-ids.py")
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

SCREEN_FLOW = """# Screen Flow

## Feature Entry Points

### F001_Login
- **Entry screen**: SCR001_Login — `/login`
- **Owned screens**:
  - SCR001_Login — `/login` (atomic)
  - SCR002_Dashboard — `/dashboard` (composite)
- **Exit screens**: SCR009_Other (on success)

## Screen Transitions
"""

SCREEN_LIST = """# Screen List

## Screen Index

| Code | Name | Type |
|------|------|------|
| SCR001_Login | Login Form | atomic |
| SCR002_Dashboard | Dashboard | composite |
"""

SCREENS_MD = """# Screens — F001_Login

## Screen List

| Screen Name | What User Sees | What User Can Do |
|-------------|----------------|------------------|
| Login Form | the login page | enter creds |
| Dashboard | the home | view |
"""

SPEC_MD = """# SCR001_Login — Screen Spec

**Screen**: SCR001: Login
**Type**: atomic
**Route**: /login

## Purpose
x
"""


def _make_tree(base: Path, with_bridge=True) -> Path:
    docs = base / "docs"
    gen = docs / "generated"
    gen.mkdir(parents=True)
    gen.joinpath("screen-flow.md").write_text(
        SCREEN_FLOW if with_bridge else "# Screen Flow\n\n## Screen Transitions\n")
    gen.joinpath("screen-list.md").write_text(SCREEN_LIST)
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    feat.joinpath("screens.md").write_text(SCREENS_MD)
    spec = docs / "screens" / "SCR001_Login"
    spec.mkdir(parents=True)
    spec.joinpath("spec.md").write_text(SPEC_MD)
    return docs


class TestBridgeParse:
    def test_owned_screens_map_to_owner(self):
        m = mig.parse_entry_points(SCREEN_FLOW)
        assert m["SCR001_Login"] == "F001_Login"
        assert m["SCR002_Dashboard"] == "F001_Login"

    def test_exit_screen_not_owned(self):
        m = mig.parse_entry_points(SCREEN_FLOW)
        assert "SCR009_Other" not in m  # exit screen is not owned by F001

    def test_no_bridge_returns_empty(self):
        assert mig.parse_entry_points("# Screen Flow\n\n## Screen Transitions\n") == {}

    def test_inline_owned_code_captured(self):
        """Reviewer I1: an SCR code inline on the **Owned screens** heading line is captured."""
        sf = ("## Feature Entry Points\n\n### F001_Login\n"
              "- **Owned screens**: SCR001_Login\n\n## Screen Transitions\n")
        m = mig.parse_entry_points(sf)
        assert m.get("SCR001_Login") == "F001_Login"


class TestForward:
    def test_inserts_scr_column_resolved(self):
        idx = mig.index_screen_list(SCREEN_LIST)
        new, changed, miss = mig.backfill_screens_md(SCREENS_MD, idx)
        assert changed and miss == 0
        assert "| Screen Name | SCR### |" in new
        assert "SCR001_Login" in new and "SCR002_Dashboard" in new

    def test_idempotent_when_column_present(self):
        idx = mig.index_screen_list(SCREEN_LIST)
        once, _, _ = mig.backfill_screens_md(SCREENS_MD, idx)
        twice, changed, _ = mig.backfill_screens_md(once, idx)
        assert changed is False and twice == once

    def test_unresolved_left_as_dash(self):
        new, changed, miss = mig.backfill_screens_md(SCREENS_MD, {})  # empty index
        assert changed and miss == 2
        assert "| — |" in new or "| —" in new


class TestForwardRobustness:
    def test_second_identical_table_not_corrupted(self):
        """Reviewer C1: a 2nd table in screens.md with the same header must be untouched."""
        idx = mig.index_screen_list(SCREEN_LIST)
        text = (
            "## Screen List\n\n"
            "| Screen Name | What User Sees | What User Can Do |\n"
            "|---|---|---|\n"
            "| Login Form | x | y |\n\n"
            "## Some Other Section\n\n"
            "| Screen Name | What User Sees | What User Can Do |\n"  # identical header
            "|---|---|---|\n"
            "| Login Form | x | y |\n"
        )
        new, changed, _ = mig.backfill_screens_md(text, idx)
        assert changed
        # exactly ONE SCR### header inserted (the Screen List table only)
        assert new.count("| SCR### |") == 1
        # the second section's table keeps its original 3-column shape
        after_other = new.split("## Some Other Section")[1]
        assert "SCR###" not in after_other

    def test_crlf_eol_preserved(self):
        idx = mig.index_screen_list(SCREEN_LIST)
        text = ("## Screen List\r\n\r\n| Screen Name | x |\r\n|---|---|\r\n| Login Form | y |\r\n")
        new, changed, _ = mig.backfill_screens_md(text, idx)
        assert changed
        # no bare-LF rows introduced into a CRLF file (every table row keeps \r\n)
        assert "\r\n| Screen Name | SCR### |" in new


class TestReverse:
    def test_inserts_feature_backlink(self):
        new, changed = mig.backfill_screen_spec(SPEC_MD, "F001_Login")
        assert changed
        assert "**Feature**: F001_Login" in new
        # inserted right after the **Screen** line
        assert new.index("**Feature**") > new.index("**Screen**")
        assert new.index("**Feature**") < new.index("**Type**")

    def test_idempotent_when_present(self):
        once, _ = mig.backfill_screen_spec(SPEC_MD, "F001_Login")
        twice, changed = mig.backfill_screen_spec(once, "F001_Login")
        assert changed is False and twice == once


class TestEndToEnd:
    def test_full_migration_backfills_both(self, tmp_path):
        docs = _make_tree(tmp_path)
        rc = mig.migrate(docs)
        assert rc == 0
        screens = (docs / "features" / "F001_Login" / "screens.md").read_text()
        spec = (docs / "screens" / "SCR001_Login" / "spec.md").read_text()
        assert "SCR001_Login" in screens
        assert "**Feature**: F001_Login" in spec

    def test_second_run_is_noop(self, tmp_path):
        docs = _make_tree(tmp_path)
        mig.migrate(docs)
        before_s = (docs / "features" / "F001_Login" / "screens.md").read_text()
        before_spec = (docs / "screens" / "SCR001_Login" / "spec.md").read_text()
        mig.migrate(docs)
        assert (docs / "features" / "F001_Login" / "screens.md").read_text() == before_s
        assert (docs / "screens" / "SCR001_Login" / "spec.md").read_text() == before_spec

    def test_missing_bridge_non_destructive(self, tmp_path):
        docs = _make_tree(tmp_path, with_bridge=False)
        before = (docs / "features" / "F001_Login" / "screens.md").read_text()
        rc = mig.migrate(docs)
        assert rc == 0  # non-destructive
        assert (docs / "features" / "F001_Login" / "screens.md").read_text() == before

    def test_hand_edited_prose_preserved(self, tmp_path):
        docs = _make_tree(tmp_path)
        mig.migrate(docs)
        screens = (docs / "features" / "F001_Login" / "screens.md").read_text()
        # The descriptive cells (prose) are untouched by the column insert.
        assert "the login page" in screens
        assert "view" in screens
