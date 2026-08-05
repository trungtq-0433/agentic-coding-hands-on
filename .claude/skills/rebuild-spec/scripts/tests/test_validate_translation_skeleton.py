"""Tests for validate_translation_skeleton.py — skeleton-identity validator."""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_translation_skeleton import extract_skeleton, validate


@pytest.fixture
def tmp_files(tmp_path):
    """Helper to create primary/mirror file pairs."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    return _write


class TestExtractSkeleton:
    def test_headings_extracted(self):
        lines = ["# Title", "", "Some prose.", "## Section", "More prose."]
        skel = extract_skeleton(lines)
        skeleton_lines = [s for _, s in skel]
        assert "# Title" in skeleton_lines
        assert "## Section" in skeleton_lines

    def test_fenced_code_is_skeleton(self):
        lines = ["```python", "def foo():", "    pass", "```"]
        skel = extract_skeleton(lines)
        skeleton_lines = [s for _, s in skel]
        assert "```python" in skeleton_lines
        assert "def foo():" in skeleton_lines
        assert "```" in skeleton_lines

    def test_code_tokens_extracted(self):
        lines = ["This feature F001 links to US002 and SCR003."]
        skel = extract_skeleton(lines)
        skeleton_lines = [s for _, s in skel]
        assert any("F001" in s and "SCR003" in s and "US002" in s for s in skeleton_lines)

    def test_field_labels_extracted(self):
        lines = ["**Linked FR:** FR-001", "Some narrative text."]
        skel = extract_skeleton(lines)
        skeleton_lines = [s for _, s in skel]
        assert any("**Linked FR:**" in s for s in skeleton_lines)

    def test_table_headers_extracted(self):
        lines = [
            "| Name | Type | Description |",
            "|------|------|-------------|",
            "| foo  | str  | A thing     |",
        ]
        skel = extract_skeleton(lines)
        skeleton_lines = [s for _, s in skel]
        assert any("| Name | Type | Description |" in s for s in skeleton_lines)
        assert any("|------|------|-------------|" in s for s in skeleton_lines)

    def test_frontmatter_extracted(self):
        lines = ["---", "title: Test", "status: draft", "---", "# Body"]
        skel = extract_skeleton(lines)
        skeleton_lines = [s for _, s in skel]
        assert "---" in skeleton_lines
        assert "title: Test" in skeleton_lines


class TestValidate:
    def test_identical_files_pass(self, tmp_files):
        content = """\
            # Feature F001
            ## Overview
            This is a test feature.
            **Linked FR:** FR-001
            ```python
            def example():
                pass
            ```
        """
        primary = tmp_files("primary.md", content)
        mirror = tmp_files("mirror.md", content)
        issues = validate(primary, mirror)
        assert issues == []

    def test_prose_only_translation_passes(self, tmp_files):
        primary = tmp_files(
            "primary.md",
            """\
            # Feature F001
            ## Overview
            This is a test feature with English prose.
            **Linked FR:** FR-001
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # Feature F001
            ## Overview
            Đây là tính năng thử nghiệm với tiếng Việt.
            **Linked FR:** FR-001
            """,
        )
        issues = validate(primary, mirror)
        assert issues == []

    def test_translated_heading_detected(self, tmp_files):
        primary = tmp_files(
            "primary.md",
            """\
            # Feature F001
            ## Overview
            Some prose.
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # Feature F001
            ## Tổng quan
            Một số văn bản.
            """,
        )
        issues = validate(primary, mirror)
        assert len(issues) > 0
        assert any("critical" in i["severity"] for i in issues)

    def test_altered_code_token_detected(self, tmp_files):
        primary = tmp_files(
            "primary.md",
            """\
            # Feature F001
            Links to US001 and SCR002.
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # Feature F001
            Liên kết với US001 và SCR999.
            """,
        )
        issues = validate(primary, mirror)
        assert len(issues) > 0
        assert any("critical" in i["severity"] for i in issues)

    def test_reordered_sections_detected(self, tmp_files):
        primary = tmp_files(
            "primary.md",
            """\
            # Title
            ## Section A
            Prose A.
            ## Section B
            Prose B.
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # Title
            ## Section B
            Prose B translated.
            ## Section A
            Prose A translated.
            """,
        )
        issues = validate(primary, mirror)
        assert len(issues) > 0

    def test_missing_primary_returns_error(self, tmp_path):
        mirror = tmp_path / "mirror.md"
        mirror.write_text("# Title\n", encoding="utf-8")
        primary = tmp_path / "nonexistent.md"
        issues = validate(primary, mirror)
        assert len(issues) > 0
        assert "cannot read primary" in issues[0]["message"]

    def test_fenced_code_alteration_detected(self, tmp_files):
        primary = tmp_files(
            "primary.md",
            """\
            # API
            ```json
            {"key": "value"}
            ```
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # API
            ```json
            {"khoa": "gia_tri"}
            ```
            """,
        )
        issues = validate(primary, mirror)
        assert len(issues) > 0
        assert any("critical" in i["severity"] for i in issues)


class TestBodyRatioGuard:
    def test_dropped_prose_paragraph_detected(self, tmp_files):
        # Same skeleton; mirror omits most prose → body-size drift FAIL.
        primary = tmp_files(
            "primary.md",
            """\
            # Feature F001
            ## Overview
            Paragraph one with several words of meaningful prose content here.
            Paragraph two also carries real explanatory prose worth translating.
            Paragraph three completes the section with yet more descriptive text.
            Paragraph four adds even more narrative so the body is clearly large.
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # Feature F001
            ## Overview
            Đoạn một.
            """,
        )
        issues = validate(primary, mirror)
        assert any("body-size drift" in i["message"] for i in issues)

    def test_proportional_translation_passes_ratio(self, tmp_files):
        primary = tmp_files(
            "primary.md",
            """\
            # Feature F001
            ## Overview
            One line of prose here.
            Another line of prose here.
            """,
        )
        mirror = tmp_files(
            "mirror.md",
            """\
            # Feature F001
            ## Overview
            Một dòng văn bản ở đây.
            Một dòng văn bản khác ở đây.
            """,
        )
        issues = validate(primary, mirror)
        assert issues == []
