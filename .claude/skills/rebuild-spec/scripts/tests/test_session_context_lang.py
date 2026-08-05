"""Tests for build_session_context.py language directive — generate/translate modes."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS_DIR / "build_session_context.py"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


def _build_context(tmp_path, mode="generate", lang=None):
    """Run build_session_context.py inside tmp_path (satisfies path-traversal guard)."""
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)

    scout_report = tmp_path / "scout-report.md"
    scout_report.write_text(
        "# Scout Report\n\n## Detected Language\nJS/TS\n\n## Files\n- src/index.ts\n",
        encoding="utf-8",
    )

    cmd = [
        "--plan-dir", str(plan_dir),
        "--scout-report", str(scout_report),
        "--stack-note", "JS/TS monorepo",
        "--mode", mode,
    ]
    if lang:
        cmd.extend(["--lang", lang])

    result = _run(cmd, cwd=tmp_path)
    if result.returncode != 0:
        pytest.fail(f"build_session_context.py failed: {result.stderr}")

    out_path = plan_dir / "artifacts" / "_session-context.md"
    return out_path.read_text(encoding="utf-8")


class TestGenerateMode:
    def test_default_en_no_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="generate")
        assert "Language Directive" not in content

    def test_generate_en_explicit_no_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="generate", lang="en")
        assert "Language Directive" not in content

    def test_generate_vi_has_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="generate", lang="vi")
        assert "## Language Directive (generation mode)" in content
        assert "prose_lang: vi" in content
        assert "Write all prose in vi" in content
        assert "English (canonical skeleton)" in content

    def test_generate_jp_has_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="generate", lang="jp")
        assert "prose_lang: jp" in content


class TestTranslateMode:
    def test_translate_vi_has_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="translate", lang="vi")
        assert "## Language Directive (translate mode)" in content
        assert "target_lang: vi" in content
        assert "BYTE-IDENTICAL" in content
        assert "translation-contract.md" in content

    def test_translate_jp_has_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="translate", lang="jp")
        assert "target_lang: jp" in content

    def test_translate_without_lang_no_directive(self, tmp_path):
        content = _build_context(tmp_path, mode="translate")
        assert "Language Directive" not in content


class TestRegressionEnDefault:
    """Default en path must be byte-identical to pre-v5.1 output (no lang directive injected)."""

    def test_no_lang_arg_unchanged(self, tmp_path):
        content = _build_context(tmp_path)
        assert "# Session Context — rebuild-spec" in content
        assert "detectedStack: JS/TS" in content
        assert "feature_count: <pending-W5>" in content
        assert "Language Directive" not in content
