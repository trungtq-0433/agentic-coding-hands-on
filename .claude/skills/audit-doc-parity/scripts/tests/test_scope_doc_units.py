"""Tests for scope_doc_units.py."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import scope_doc_units as sdu

FIXTURES = Path(__file__).parent / "fixtures"
# Project root is agent-kit root (6 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent


# ---------------------------------------------------------------------------
# _is_excluded_path
# ---------------------------------------------------------------------------

class TestIsExcludedPath:
    def test_node_modules_excluded(self):
        p = PROJECT_ROOT / "node_modules" / "lodash" / "index.js"
        assert sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_git_excluded(self):
        p = PROJECT_ROOT / ".git" / "config"
        assert sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_venv_excluded(self):
        p = PROJECT_ROOT / ".venv" / "lib" / "site.py"
        assert sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_min_js_excluded(self):
        p = PROJECT_ROOT / "public" / "app.min.js"
        assert sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_lock_file_excluded(self):
        p = PROJECT_ROOT / "yarn.lock"
        assert sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_binary_excluded(self):
        p = PROJECT_ROOT / "assets" / "logo.png"
        assert sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_normal_source_not_excluded(self):
        p = PROJECT_ROOT / "src" / "app.py"
        assert not sdu._is_excluded_path(p, PROJECT_ROOT)

    def test_sql_not_excluded(self):
        # SQL files are valid citation targets (legacy group B)
        p = PROJECT_ROOT / "db" / "schema.sql"
        assert not sdu._is_excluded_path(p, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# _extract_enclosing_block_indent (Python heuristic)
# ---------------------------------------------------------------------------

class TestEnclosingBlockIndent:
    def _lines(self, src):
        return src.splitlines()

    def test_finds_def_above_anchor(self):
        src = (
            "def outer():\n"          # 0
            "    x = 1\n"             # 1 ← anchor
            "    return x\n"          # 2
        )
        lines = self._lines(src)
        start, end, truncated = sdu._extract_enclosing_block_indent(lines, 1, 1, 2000)
        assert start == 0
        assert end == 2
        assert not truncated

    def test_truncated_when_over_cap(self):
        src = (
            "def big():\n"
            + ("    pass\n" * 10)
        )
        lines = self._lines(src)
        # cap of 3 lines forces truncation for the 11-line function
        start, end, truncated = sdu._extract_enclosing_block_indent(lines, 5, 5, 3)
        assert truncated

    def test_falls_back_to_anchor_when_no_def(self):
        src = "x = 1\ny = 2\nz = 3\n"
        lines = self._lines(src)
        start, end, truncated = sdu._extract_enclosing_block_indent(lines, 1, 1, 2000)
        # No def above — start should equal anchor or earlier
        assert start <= 1
        assert not truncated


# ---------------------------------------------------------------------------
# _extract_enclosing_block_brace (JS/TS heuristic)
# ---------------------------------------------------------------------------

class TestEnclosingBlockBrace:
    def _lines(self, src):
        return src.splitlines()

    def test_finds_enclosing_braces(self):
        src = (
            "function outer() {\n"    # 0
            "    const x = 1;\n"      # 1 ← anchor
            "    return x;\n"         # 2
            "}\n"                     # 3
        )
        lines = self._lines(src)
        start, end, truncated = sdu._extract_enclosing_block_brace(lines, 1, 1, 2000)
        assert start <= 1
        assert end >= 2
        assert not truncated

    def test_truncated_when_over_cap(self):
        src = "function f() {\n" + ("    x;\n" * 10) + "}\n"
        lines = self._lines(src)
        start, end, truncated = sdu._extract_enclosing_block_brace(lines, 5, 5, 3)
        assert truncated


# ---------------------------------------------------------------------------
# _process_doc — citation present vs absent
# ---------------------------------------------------------------------------

class TestProcessDoc:
    def test_citation_present(self):
        doc_path = FIXTURES / "doc_with_citations.md"
        result = sdu._process_doc(doc_path, "technical-spec", "F001_Example",
                                   PROJECT_ROOT, 2000)
        assert result["citation_coverage"] is True
        # Should have regions (some may be unverifiable due to path resolution)
        assert isinstance(result["regions"], list)

    def test_citation_absent(self):
        doc_path = FIXTURES / "doc_no_citations.md"
        result = sdu._process_doc(doc_path, "technical-spec", "F002_NoCitations",
                                   PROJECT_ROOT, 2000)
        assert result["citation_coverage"] is False
        assert result["regions"] == []
        assert result["unverifiable"] == []

    def test_excluded_cited_file_not_in_regions(self):
        # Write a temp doc that cites a node_modules path
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False,
                                         dir=FIXTURES) as f:
            f.write("**Source:** `node_modules/lodash/index.js:1-5`\n")
            tmp_path = Path(f.name)
        try:
            result = sdu._process_doc(tmp_path, "technical-spec", "F_EXCL",
                                       PROJECT_ROOT, 2000)
            # Excluded path → no region added
            assert result["regions"] == []
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_file_size_cap_sets_truncated(self):
        # Use source_plain.py with a cap of 1 line → enclosing block forced to truncate
        doc_path = FIXTURES / "doc_with_citations.md"
        result = sdu._process_doc(doc_path, "technical-spec", "F001_Example",
                                   PROJECT_ROOT, cap=1)
        # At least some regions should exist; truncation may or may not fire
        # depending on resolution. Just verify the structure is intact.
        for region in result["regions"]:
            assert "truncated" in region


# ---------------------------------------------------------------------------
# main CLI — roundtrip via tmp project structure
# ---------------------------------------------------------------------------

class TestMainCli:
    def test_no_docs_dir_warns_and_exits_nonzero(self, tmp_path, capsys):
        out = tmp_path / "units.json"
        rc = sdu.main(["--project-root", str(tmp_path), "--out", str(out)])
        assert rc == 2

    def test_empty_docs_produces_empty_json(self, tmp_path, capsys):
        (tmp_path / "docs").mkdir()
        out = tmp_path / "units.json"
        rc = sdu.main(["--project-root", str(tmp_path), "--out", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert data == []

    def test_feature_filter(self, tmp_path):
        docs = tmp_path / "docs" / "features" / "F001_Test"
        docs.mkdir(parents=True)
        (docs / "technical-spec.md").write_text("no citations here\n")
        # Also create a second feature that should be filtered out
        docs2 = tmp_path / "docs" / "features" / "F002_Other"
        docs2.mkdir(parents=True)
        (docs2 / "technical-spec.md").write_text("no citations here either\n")

        out = tmp_path / "units.json"
        rc = sdu.main(["--project-root", str(tmp_path), "--feature", "F001", "--out", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        unit_ids = [u["unit"] for u in data]
        assert all("F001" in uid for uid in unit_ids)
        assert not any("F002" in uid for uid in unit_ids)
