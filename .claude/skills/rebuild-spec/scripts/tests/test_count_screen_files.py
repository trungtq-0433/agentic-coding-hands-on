"""Tests for scripts/count_screen_files.py."""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "count_screen_files.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "count_screens"


def _run(scout_path: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scout-report", scout_path],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    """Copy a fixture into tmp_path so it passes the path-traversal guard."""
    import shutil
    dst = tmp_path / name
    shutil.copy2(str(FIXTURES / name), str(dst))
    return dst


class TestCountScreenLines:
    def test_counts_10_screens(self, tmp_path):
        fixture = _copy_fixture(tmp_path, "scout.10_screens.md")
        result = _run(str(fixture), cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "10"

    def test_counts_0_screens(self, tmp_path):
        fixture = _copy_fixture(tmp_path, "scout.0_screens.md")
        result = _run(str(fixture), cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "0"

    def test_inline_screen_tab_pattern(self, tmp_path):
        # Only lines with literal tab + "screen" should be counted
        scout = tmp_path / "scout-inline.md"
        scout.write_text(
            "## File Inventory\n"
            "src/views/login.php\tscreen\n"
            "src/views/dashboard.php\tscreen\n"
            "src/views/notascreen.php\tcontroller\n"
            "# This line mentions screen but has no tab\n"
        )
        result = _run(str(scout), cwd=tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == "2"

    def test_screen_embedded_and_datamodule_excluded(self, tmp_path):
        # v21.0.0 Delphi tags: TFrame→screen-embedded, TDataModule→datamodule must NOT
        # be counted as visual screens; only `screen` (incl. `screen [UNVERIFIED]`) counts.
        scout = tmp_path / "scout-delphi.md"
        scout.write_text(
            "## File Inventory\n"
            "src/MainForm.dfm\tscreen\n"
            "src/EditForm.dfm\tscreen\n"
            "src/Panel.dfm\tscreen-embedded\n"      # TFrame — must NOT count
            "src/Data.dfm\tdatamodule\n"            # TDataModule — must NOT count
            "src/Data2.dfm\tdatamodule [reachable]\n"  # still not a screen
            "src/Legacy.dfm\tscreen [UNVERIFIED]\n"    # binary .dfm marker — MUST count
        )
        result = _run(str(scout), cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "3"


class TestMissingFile:
    def test_missing_file_exits_2(self, tmp_path):
        result = _run(str(tmp_path / "nonexistent.md"), cwd=tmp_path)
        assert result.returncode == 2

    def test_missing_file_stderr_message(self, tmp_path):
        result = _run(str(tmp_path / "nonexistent.md"), cwd=tmp_path)
        assert "error" in result.stderr.lower()
