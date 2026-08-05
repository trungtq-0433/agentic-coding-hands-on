# layout-exempt: rebuild-spec feature↔screen link validator tests — docs paths are managed targets
"""Tests for validate_feature_screen_link.py (Phase B, v24.0.0).

Covers the degradation contract: pre-migration (no column/line) → WARN; migrated +
unresolvable → FAIL; migrated + empty cell → soft WARN; prefix-tolerant resolution;
exit codes; summary merge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import validate_feature_screen_link as v  # noqa: E402

SCR_INV = {"SCR001", "SCR002"}
FEAT_INV = {"F001", "F002"}


def _sev(issues, rid):
    return [i for i in issues if i["rule_id"] == rid]


# ---------------------------------------------------------------------------
# forward: screens.md SCR### column
# ---------------------------------------------------------------------------

class TestScreensForward:
    def test_no_column_is_pre_migration_warn(self):
        text = ("## Screen List\n\n| Screen Name | What User Sees |\n|---|---|\n"
                "| Login | the page |\n")
        issues = v.check_screens_md(text, SCR_INV, "f")
        assert len(_sev(issues, "link.pre_migration")) == 1
        assert all(i["severity"] == "warning" for i in issues)

    def test_resolvable_column_passes(self):
        text = ("## Screen List\n\n| Screen Name | SCR### | What User Sees |\n|---|---|---|\n"
                "| Login | SCR001_LoginForm | x |\n| Dash | SCR002 | y |\n")
        assert v.check_screens_md(text, SCR_INV, "f") == []

    def test_unresolvable_scr_fails(self):
        text = ("## Screen List\n\n| Screen Name | SCR### | x |\n|---|---|---|\n"
                "| Ghost | SCR999_Nope | z |\n")
        issues = v.check_screens_md(text, SCR_INV, "f")
        assert len(_sev(issues, "link.scr_unresolved")) == 1
        assert issues[0]["severity"] == "critical"

    def test_empty_cell_is_soft_unmapped_warn(self):
        text = ("## Screen List\n\n| Screen Name | SCR### | x |\n|---|---|---|\n"
                "| Login | — | z |\n")
        issues = v.check_screens_md(text, SCR_INV, "f")
        assert len(_sev(issues, "link.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_background_feature_is_na(self):
        text = "## Screen List\n\nN/A — background feature; no user-facing screens.\n"
        assert v.check_screens_md(text, SCR_INV, "f") == []

    def test_placeholder_template_row_skipped(self):
        text = ("## Screen List\n\n| Screen Name | SCR### | x |\n|---|---|---|\n"
                "| {ScreenName} | {SCR###} | y |\n")
        assert v.check_screens_md(text, SCR_INV, "f") == []


# ---------------------------------------------------------------------------
# reverse: screen-spec **Feature** backlink
# ---------------------------------------------------------------------------

class TestSpecReverse:
    def test_no_feature_line_is_pre_migration_warn(self):
        text = "# SCR001_Login — Screen Spec\n\n**Screen**: SCR001: Login\n**Type**: atomic\n"
        issues = v.check_screen_spec(text, FEAT_INV, "s")
        assert len(_sev(issues, "link.pre_migration")) == 1

    def test_resolvable_feature_passes(self):
        text = "**Screen**: SCR001: Login\n**Feature**: F001_Login\n**Type**: atomic\n"
        assert v.check_screen_spec(text, FEAT_INV, "s") == []

    def test_unresolvable_feature_fails(self):
        text = "**Screen**: SCR001: Login\n**Feature**: F999_Ghost\n"
        issues = v.check_screen_spec(text, FEAT_INV, "s")
        assert len(_sev(issues, "link.feature_unresolved")) == 1
        assert issues[0]["severity"] == "critical"

    def test_unfilled_feature_is_soft_warn(self):
        text = "**Screen**: SCR001: Login\n**Feature**: {F###_NAME}\n"
        issues = v.check_screen_spec(text, FEAT_INV, "s")
        assert len(_sev(issues, "link.unmapped")) == 1


class TestInventory:
    def test_build_inventory_extracts_prefixes(self):
        text = "| SCR001_LoginForm | ... |\n| SCR042_Dashboard | ... |\n"
        assert v.build_inventory(text, v._SCR_PREFIX) == {"SCR001", "SCR042"}


# ---------------------------------------------------------------------------
# integration: validate() + main() exit codes + summary merge
# ---------------------------------------------------------------------------

def _make_docs(base: Path, scr_cell="SCR001_LoginForm", feature="F001_Login") -> Path:
    docs = base / "docs"
    (docs / "generated").mkdir(parents=True)
    (docs / "generated" / "screen-list.md").write_text(
        "## Screen Index\n\n| Code | Name |\n|---|---|\n| SCR001_LoginForm | Login |\n")
    (docs / "generated" / "feature-list.md").write_text("F001_Login — login feature\n")
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "screens.md").write_text(
        f"## Screen List\n\n| Screen Name | SCR### | x |\n|---|---|---|\n| Login | {scr_cell} | y |\n")
    spec = docs / "screens" / "SCR001_LoginForm"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text(
        f"**Screen**: SCR001: Login\n**Feature**: {feature}\n**Type**: atomic\n")
    return docs


class TestIntegration:
    def test_validate_passes_on_migrated_docs(self, tmp_path):
        docs = _make_docs(tmp_path)
        result = v.validate(docs)
        assert result["status"] == "PASS", result["issues"]

    def test_validate_fails_on_drift(self, tmp_path):
        docs = _make_docs(tmp_path, scr_cell="SCR999_Ghost")
        result = v.validate(docs)
        assert result["status"] == "FAIL"

    def test_absent_inventory_warns_not_fails(self, tmp_path):
        """A migrated doc whose inventory file is missing must WARN (skip), never FAIL."""
        docs = _make_docs(tmp_path)  # valid migrated docs
        (docs / "generated" / "feature-list.md").unlink()  # remove reverse inventory
        result = v.validate(docs)
        assert result["status"] != "FAIL", result["issues"]
        assert any(i["rule_id"] == "link.inventory_absent" for i in result["issues"])

    def test_main_exit_zero_on_warn(self, tmp_path, capsys):
        # pre-migration docs (no column) → WARN → exit 0 (never break un-migrated builds)
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "screen-list.md").write_text("## Screen Index\n\n| Code |\n|---|\n| SCR001 |\n")
        (docs / "generated" / "feature-list.md").write_text("F001 x\n")
        feat = docs / "features" / "F001_Login"
        feat.mkdir(parents=True)
        (feat / "screens.md").write_text("## Screen List\n\n| Screen Name | x |\n|---|---|\n| Login | y |\n")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_main_exit_one_on_critical(self, tmp_path):
        docs = _make_docs(tmp_path, scr_cell="SCR999_Ghost")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 1

    def test_summary_merge(self, tmp_path):
        docs = _make_docs(tmp_path)
        sp = tmp_path / "validation-summary.json"
        v.main(["--docs-root", str(docs), "--project-root", str(tmp_path),
                "--summary-out", str(sp)])
        data = json.loads(sp.read_text())
        assert "feature_screen_link" in data["validators"]
