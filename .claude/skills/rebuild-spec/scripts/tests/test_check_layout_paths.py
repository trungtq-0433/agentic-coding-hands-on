"""Tests for check_layout_paths.py.

Covers:
- Un-exempt hardcoded docs/system|features|generated|flows path → scan returns offence
- Inline layout-exempt annotation on same line → scan ignores
- layout-exempt on the preceding line → scan ignores
- Exit code 1 when offences found, 0 when clean
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Locate the guard script relative to this test file.
_SCRIPT = Path(__file__).resolve().parent.parent / "check_layout_paths.py"


# ---------------------------------------------------------------------------
# Unit-level tests for the scan() helper
# ---------------------------------------------------------------------------

def _run_scan(tmp_path: Path, content: str, filename: str = "test.md"):
    """Write content to tmp_path/<filename> and run scan() against tmp_path."""
    (tmp_path / filename).write_text(content, encoding="utf-8")
    # Import lazily so we can point it at tmp fixtures.
    import importlib.util, sys as _sys
    spec = importlib.util.spec_from_file_location("check_layout_paths", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.scan(tmp_path)


class TestUnexemptPath:
    def test_md_hardcoded_system_raises_offence(self, tmp_path):
        content = "Read the file at docs/system/overview.md for details.\n"
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1
        assert offences[0][1] == 1  # line 1

    def test_md_hardcoded_features_raises_offence(self, tmp_path):
        content = "See docs/features/auth/technical-spec.md.\n"
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1

    def test_md_hardcoded_generated_raises_offence(self, tmp_path):
        content = "Load docs/generated/feature-list.md.\n"
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1

    def test_md_hardcoded_flows_raises_offence(self, tmp_path):
        content = "See docs/flows/checkout.md.\n"
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1

    def test_md_hardcoded_screens_raises_offence(self, tmp_path):
        # screens is a moved language layer (migrate_docs_layout LANGUAGE_LAYERS),
        # so the guard MUST cover it like the other layers.
        content = "Promoted to docs/screens/SCR001_Login/spec.md.\n"
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1

    def test_md_hardcoded_components_raises_offence(self, tmp_path):
        # components is a moved language layer (Phase 02: migrate_docs_layout LANGUAGE_LAYERS),
        # so the guard MUST cover it.
        content = "See docs/components/auth-service/spec.md for details.\n"
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1

    def test_py_hardcoded_raises_offence(self, tmp_path):
        content = 'root = "docs/system"\n'
        offences = _run_scan(tmp_path, content, filename="check.py")
        assert len(offences) == 1


class TestExemptInline:
    def test_inline_layout_exempt_suppresses(self, tmp_path):
        content = "Read docs/system/overview.md.  <!-- layout-exempt: owner skill -->\n"
        offences = _run_scan(tmp_path, content)
        assert offences == []

    def test_inline_hash_layout_exempt_suppresses_py(self, tmp_path):
        content = 'root = "docs/generated"  # layout-exempt: sentinel check\n'
        offences = _run_scan(tmp_path, content, filename="check.py")
        assert offences == []

    def test_preceding_line_layout_exempt_suppresses(self, tmp_path):
        # Annotation on line N-1 should cover line N.
        content = "# layout-exempt: rebuild-spec owns this path\ndocs/features/auth/\n"
        offences = _run_scan(tmp_path, content)
        assert offences == []

    def test_preceding_html_comment_suppresses(self, tmp_path):
        content = "<!-- layout-exempt: manage-docs carve-out -->\ndocs/flows/checkout.md\n"
        offences = _run_scan(tmp_path, content)
        assert offences == []


class TestMultipleLines:
    def test_block_annotation_covers_contiguous_lines(self, tmp_path):
        # A layout-exempt annotation covers the entire contiguous block that follows.
        # Preamble (60+ lines) ensures we're past the file-level exemption window,
        # so we're testing block-level propagation, not file-level exemption.
        preamble = "# doc header\n" * 60
        content = (
            preamble
            + "<!-- layout-exempt: example -->\n"
            + "docs/generated/feature-list.md\n"   # exempt via block annotation
            + "docs/system/overview.md\n"           # also exempt — same block
        )
        offences = _run_scan(tmp_path, content)
        assert offences == []

    def test_unexempt_line_after_blank_separator_is_flagged(self, tmp_path):
        # A blank line separating the annotation from the offending line breaks the block.
        # Preamble (60+ lines) ensures we're past the file-level exemption window.
        preamble = "# doc header\n" * 60
        content = (
            preamble
            + "<!-- layout-exempt: example -->\n"
            + "docs/generated/feature-list.md\n"   # exempt via preceding annotation
            + "\n"                                  # blank line breaks the block
            + "docs/system/overview.md\n"           # NOT covered → offence
        )
        offences = _run_scan(tmp_path, content)
        assert len(offences) == 1
        # Line number = preamble (60) + annotation (1) + feature-list (1) + blank (1) + system (1) = 64
        assert offences[0][1] == 64


class TestPruning:
    def test_skips_pycache(self, tmp_path):
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "bad.py").write_text('root = "docs/system"\n')
        offences = _run_scan(tmp_path, "clean content\n")
        assert offences == []

    def test_skips_venv(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        subdir = venv / "lib"
        subdir.mkdir()
        (subdir / "bad.py").write_text('root = "docs/features"\n')
        offences = _run_scan(tmp_path, "clean content\n")
        assert offences == []


# ---------------------------------------------------------------------------
# Integration tests via subprocess (tests the exit code contract)
# ---------------------------------------------------------------------------

class TestExitCodes:
    def _run(self, tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT), "--root", str(tmp_path), *extra_args],
            capture_output=True,
            text=True,
        )

    def test_exit_0_on_clean_tree(self, tmp_path):
        (tmp_path / "clean.md").write_text("No hardcoded paths here.\n")
        result = self._run(tmp_path)
        assert result.returncode == 0

    def test_exit_1_on_un_exempt_path(self, tmp_path):
        (tmp_path / "bad.md").write_text("See docs/system/overview.md.\n")
        result = self._run(tmp_path)
        assert result.returncode == 1
        assert "bad.md" in result.stdout

    def test_exit_0_when_all_exempt(self, tmp_path):
        content = (
            "# layout-exempt: rebuild-spec owns these\n"
            "See docs/generated/feature-list.md.\n"
        )
        (tmp_path / "ok.md").write_text(content)
        result = self._run(tmp_path)
        assert result.returncode == 0

    def test_exit_1_bad_root(self, tmp_path):
        result = self._run(tmp_path / "nonexistent")
        assert result.returncode == 1
