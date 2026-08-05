"""Tests for scripts/build_session_context.py."""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "build_session_context.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "session_context"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


def _copy_scout(tmp_path: Path, name: str = "scout-report.minimal.md") -> Path:
    """Copy a fixture scout report into tmp_path so it passes the path-traversal guard."""
    import shutil
    dst = tmp_path / name
    shutil.copy2(str(FIXTURES / name), str(dst))
    return dst


class TestFreshWrite:
    def test_creates_session_context_file(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        out = plan_dir / "artifacts" / "_session-context.md"
        assert out.is_file()

    def test_detected_stack_php(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "detectedStack: PHP" in content

    def test_is_multi_stack_false(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "isMultiStack: False" in content

    def test_feature_count_placeholder(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "feature_count: <pending-W5>" in content

    def test_stack_note_written(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "stackNote: PHP monolith" in content


class TestFeatureCountPatch:
    def test_updates_feature_count_only(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        # First: create fresh file
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        # Then: patch with feature count
        result = _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
                "--feature-count", "42",
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "feature_count: 42" in content

    def test_does_not_duplicate_other_lines(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
                "--feature-count", "42",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        # detectedStack should appear exactly once
        assert content.count("detectedStack:") == 1


class TestFallbackStack:
    def test_fallback_to_js_ts_when_no_detected_language(self, tmp_path):
        # Scout report with no ## Detected Language section — created inside tmp_path
        scout = tmp_path / "scout-no-lang.md"
        scout.write_text("## File Inventory\nsrc/index.js\tcontroller\n")
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "unknown",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "detectedStack: JS/TS" in content


class TestMultiStackDetection:
    def test_multi_stack_sets_is_multi_stack_true(self, tmp_path):
        scout = tmp_path / "scout-multi.md"
        scout.write_text(
            "## Detected Language\nPHP [MULTI_STACK]\n\n## File Inventory\nsrc/app.php\tcontroller\n"
        )
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "multi",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "isMultiStack: True" in content

    def test_no_multi_stack_marker_is_false(self, tmp_path):
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "single",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "isMultiStack: False" in content


class TestSourceEncodingBlock:
    """Phase A: --encoding / --profile-id emit a Source Encoding block; RT-F2 abort."""

    def _delphi_scout(self, tmp_path) -> Path:
        scout = tmp_path / "scout-delphi.md"
        scout.write_text("## Detected Language\nDelphi/VCL\n\n## File Inventory\nsrc/Unit1.pas\tother\n")
        return scout

    def test_encoding_block_emitted(self, tmp_path):
        scout = self._delphi_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "Delphi/VCL",
                "--encoding", "shift_jis",
                "--profile-id", "delphi-vcl",
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "## Source Encoding" in content
        assert "primary: shift_jis" in content
        assert "profile: delphi-vcl" in content
        assert "detectedStack: Delphi/VCL" in content

    def test_no_encoding_block_when_unset(self, tmp_path):
        # Regression: no --encoding / --profile-id → no Source Encoding block (legacy shape).
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "PHP monolith",
            ],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "## Source Encoding" not in content

    def test_profile_id_set_but_no_detected_language_aborts(self, tmp_path):
        # RT-F2: refuse the silent JS/TS fallback when a profile is explicitly selected.
        scout = tmp_path / "scout-no-lang.md"
        scout.write_text("## File Inventory\nsrc/Unit1.pas\tother\n")
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            [
                "--plan-dir", str(plan_dir),
                "--scout-report", str(scout),
                "--stack-note", "Delphi/VCL",
                "--profile-id", "delphi-vcl",
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 2
        assert "RT-F2" in result.stderr or "Detected Language" in result.stderr
