"""Tests for build_migrate_session_context.py.

CRITICAL: asserts that _session-context.md produced by migrate-aidd has the
SAME set of ## section headings AND the same bullet-key set (detectedStack,
isMultiStack, feature_count) as rebuild-spec's build_session_context.py output.
"""
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "build_migrate_session_context.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# rebuild-spec reference script (read-only — never modified).
# Tree-relative so the test resolves against the SAME skills tree it lives in
# (works under both claude/ source and .claude/ install). parents[3] == skills dir.
SKILLS_DIR = Path(__file__).resolve().parents[3]
REBUILD_SCRIPT = SKILLS_DIR / "rebuild-spec" / "scripts" / "build_session_context.py"
REBUILD_FIXTURES = SKILLS_DIR / "rebuild-spec" / "scripts" / "tests" / "fixtures" / "session_context"


def _run(script: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


def _extract_h2_headings(content: str) -> set[str]:
    """Return all ## Heading titles (stripped, lowercased for comparison)."""
    return {
        m.group(1).strip().lower()
        for m in re.finditer(r"^## (.+)$", content, re.MULTILINE)
    }


def _extract_bullet_keys(content: str) -> set[str]:
    """Return all '- key:' bullet keys found in the document."""
    return {
        m.group(1).strip()
        for m in re.finditer(r"^- ([a-zA-Z_]+):", content, re.MULTILINE)
    }


def _make_minimal_spec_summary(path: Path, stack: str = "PHP") -> None:
    path.write_text(
        f"# Spec Summary\n\n## Detected Language\n{stack}\n\n## Features\n\n### 001 — taskify\n"
    )


def _copy_scout(tmp_path: Path) -> Path:
    """Copy minimal scout report fixture into tmp_path (path-traversal guard)."""
    import shutil
    dst = tmp_path / "scout-report.minimal.md"
    shutil.copy2(str(REBUILD_FIXTURES / "scout-report.minimal.md"), str(dst))
    return dst


class TestFreshWrite:
    def test_creates_session_context_file(self, tmp_path):
        spec_summary = tmp_path / "spec-summary.md"
        _make_minimal_spec_summary(spec_summary)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary), "--stack-note", "PHP monolith"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert (plan_dir / "artifacts" / "_session-context.md").is_file()

    def test_detected_stack_extracted(self, tmp_path):
        spec_summary = tmp_path / "spec-summary.md"
        _make_minimal_spec_summary(spec_summary, stack="PHP")
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary), "--stack-note", "PHP monolith"],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "detectedStack: PHP" in content

    def test_feature_count_placeholder(self, tmp_path):
        spec_summary = tmp_path / "spec-summary.md"
        _make_minimal_spec_summary(spec_summary)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary), "--stack-note", "x"],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "feature_count: <pending-W5>" in content

    def test_stack_note_written(self, tmp_path):
        spec_summary = tmp_path / "spec-summary.md"
        _make_minimal_spec_summary(spec_summary)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary), "--stack-note", "PHP monolith"],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "stackNote: PHP monolith" in content


class TestFeatureCountPatch:
    def test_patches_feature_count(self, tmp_path):
        spec_summary = tmp_path / "spec-summary.md"
        _make_minimal_spec_summary(spec_summary)
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary), "--stack-note", "x"],
            cwd=tmp_path,
        )
        result = _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary),
             "--stack-note", "x", "--feature-count", "5"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        content = (plan_dir / "artifacts" / "_session-context.md").read_text()
        assert "feature_count: 5" in content
        assert content.count("detectedStack:") == 1


class TestSchemaParity:
    """CRITICAL: heading set + bullet-key set must match rebuild-spec output exactly."""

    def _generate_rebuild_output(self, tmp_path: Path) -> str:
        scout = _copy_scout(tmp_path)
        plan_dir = tmp_path / "rebuild-plan"
        plan_dir.mkdir()
        result = _run(
            REBUILD_SCRIPT,
            ["--plan-dir", str(plan_dir), "--scout-report", str(scout), "--stack-note", "PHP monolith"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"rebuild-spec failed: {result.stderr}"
        return (plan_dir / "artifacts" / "_session-context.md").read_text()

    def _generate_migrate_output(self, tmp_path: Path) -> str:
        spec_summary = tmp_path / "spec-summary.md"
        _make_minimal_spec_summary(spec_summary, stack="PHP")
        plan_dir = tmp_path / "migrate-plan"
        plan_dir.mkdir()
        result = _run(
            SCRIPT,
            ["--plan-dir", str(plan_dir), "--spec-summary", str(spec_summary), "--stack-note", "PHP monolith"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"migrate failed: {result.stderr}"
        return (plan_dir / "artifacts" / "_session-context.md").read_text()

    def test_h2_heading_set_parity(self, tmp_path):
        rebuild_content = self._generate_rebuild_output(tmp_path)
        migrate_content = self._generate_migrate_output(tmp_path)

        rebuild_headings = _extract_h2_headings(rebuild_content)
        migrate_headings = _extract_h2_headings(migrate_content)

        assert rebuild_headings == migrate_headings, (
            f"Heading mismatch.\n"
            f"  rebuild-spec only: {rebuild_headings - migrate_headings}\n"
            f"  migrate-aidd only: {migrate_headings - rebuild_headings}"
        )

    def test_bullet_key_set_parity(self, tmp_path):
        rebuild_content = self._generate_rebuild_output(tmp_path)
        migrate_content = self._generate_migrate_output(tmp_path)

        rebuild_keys = _extract_bullet_keys(rebuild_content)
        migrate_keys = _extract_bullet_keys(migrate_content)

        assert rebuild_keys == migrate_keys, (
            f"Bullet-key mismatch.\n"
            f"  rebuild-spec only: {rebuild_keys - migrate_keys}\n"
            f"  migrate-aidd only: {migrate_keys - rebuild_keys}"
        )

    def test_stack_keys_present(self, tmp_path):
        migrate_content = self._generate_migrate_output(tmp_path)
        assert "- detectedStack:" in migrate_content
        assert "- isMultiStack:" in migrate_content
        assert "- feature_count:" in migrate_content
