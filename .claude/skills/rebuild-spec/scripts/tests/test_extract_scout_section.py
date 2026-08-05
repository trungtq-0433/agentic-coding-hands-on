"""Tests for scripts/extract_scout_section.py."""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_scout_section.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "extract_scout_section"

SECTION_NAME = "Background Logic Source Inventory"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


def _copy_scout(tmp_path: Path) -> Path:
    """Copy the multi-stack fixture scout into tmp_path to pass path-traversal guard."""
    import shutil
    dst = tmp_path / "scout.multi-stack.md"
    shutil.copy2(str(FIXTURES / "scout.multi-stack.md"), str(dst))
    return dst


class TestExtractSection:
    def test_exit_code_zero(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "_scout-bl-inventory.md"
        result = _run(
            [
                "--scout-report", str(scout),
                "--section", SECTION_NAME,
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr

    def test_output_file_created(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "_scout-bl-inventory.md"
        _run(
            [
                "--scout-report", str(scout),
                "--section", SECTION_NAME,
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        assert out.is_file()

    def test_extracted_content_contains_section_heading(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "_scout-bl-inventory.md"
        _run(
            [
                "--scout-report", str(scout),
                "--section", SECTION_NAME,
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        content = out.read_text()
        assert f"## {SECTION_NAME}" in content

    def test_extracted_content_has_bl_entries(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "_scout-bl-inventory.md"
        _run(
            [
                "--scout-report", str(scout),
                "--section", SECTION_NAME,
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        content = out.read_text()
        assert "BL-001_SendVerificationEmail" in content

    def test_stops_at_next_h2_heading(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "_scout-bl-inventory.md"
        _run(
            [
                "--scout-report", str(scout),
                "--section", SECTION_NAME,
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        content = out.read_text()
        # "## Data Model Summary" is the next H2 — must not appear in output
        assert "## Data Model Summary" not in content

    def test_does_not_include_preceding_sections(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "_scout-bl-inventory.md"
        _run(
            [
                "--scout-report", str(scout),
                "--section", SECTION_NAME,
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        content = out.read_text()
        assert "## Detected Language" not in content
        assert "## File Inventory" not in content


class TestCrlfLineEndings:
    """M4 regression — CRLF line endings must not break section matching."""

    def test_crlf_line_endings_match(self, tmp_path):
        # Build a scout report that uses \r\n throughout
        lines = [
            "## Detected Language\r\n",
            "PHP\r\n",
            "\r\n",
            "## Background Logic Source Inventory\r\n",
            "BL-001_SendEmail\tsrc/Jobs/SendEmail.php:1-20\tdispatched by Auth\r\n",
            "\r\n",
            "## Data Model Summary\r\n",
            "users\tid, email\r\n",
        ]
        scout = tmp_path / "scout-crlf.md"
        scout.write_bytes(b"".join(ln.encode("utf-8") for ln in lines))

        out = tmp_path / "section-out.md"
        result = _run(
            [
                "--scout-report", str(scout),
                "--section", "Background Logic Source Inventory",
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        # Section must be found — exit code 2 means it was NOT found (the bug)
        assert result.returncode == 0, (
            f"CRLF scout report: section not found (exit {result.returncode}). stderr: {result.stderr}"
        )
        assert out.is_file()
        content = out.read_text(encoding="utf-8")
        assert "Background Logic Source Inventory" in content


class TestMissingSection:
    def test_missing_section_exits_2(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "out.md"
        result = _run(
            [
                "--scout-report", str(scout),
                "--section", "Nonexistent Section Name",
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 2

    def test_missing_section_stderr_message(self, tmp_path):
        scout = _copy_scout(tmp_path)
        out = tmp_path / "out.md"
        result = _run(
            [
                "--scout-report", str(scout),
                "--section", "Nonexistent Section Name",
                "--out", str(out),
            ],
            cwd=tmp_path,
        )
        assert "error" in result.stderr.lower()

    def test_missing_file_exits_2(self, tmp_path):
        result = _run(
            [
                "--scout-report", str(tmp_path / "no-such-file.md"),
                "--section", SECTION_NAME,
                "--out", str(tmp_path / "out.md"),
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 2
