"""Tests for the [GRAPHIFY-INTEGRATION] conditional directive in build_session_context.py.

The graphify directive must appear in _session-context.md ONLY when a knowledge graph
(graphify-out/graph.json) exists in the cwd — guaranteeing zero impact for users who do
not use graphify.
"""
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "build_session_context.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "session_context"
MARKER = "Knowledge Graph (graphify)"


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, timeout=30, cwd=str(cwd),
    )


def _copy_scout(tmp_path, name="scout-report.minimal.md"):
    dst = tmp_path / name
    shutil.copy2(str(FIXTURES / name), str(dst))
    return dst


def _build(tmp_path):
    scout = _copy_scout(tmp_path)
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    result = _run(
        ["--plan-dir", str(plan_dir), "--scout-report", str(scout), "--stack-note", "PHP monolith"],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    return (plan_dir / "artifacts" / "_session-context.md").read_text()


def test_graphify_directive_absent_without_graph(tmp_path):
    """No graphify-out/graph.json -> directive must NOT appear (zero-impact default)."""
    content = _build(tmp_path)
    assert MARKER not in content


def test_graphify_directive_present_with_graph(tmp_path):
    """graphify-out/graph.json present -> directive MUST appear, with graphify CLI commands."""
    gdir = tmp_path / "graphify-out"
    gdir.mkdir()
    (gdir / "graph.json").write_text("{}")
    content = _build(tmp_path)
    assert MARKER in content
    assert "graphify query" in content
    assert "graphify explain" in content


def test_existing_fields_unchanged_with_graph(tmp_path):
    """Adding the directive must not break the normal session-context fields."""
    gdir = tmp_path / "graphify-out"
    gdir.mkdir()
    (gdir / "graph.json").write_text("{}")
    content = _build(tmp_path)
    assert "detectedStack: PHP" in content
    assert "feature_count: <pending-W5>" in content


def test_opt_out_env_suppresses_directive_even_with_graph(tmp_path):
    """REBUILD_NO_GRAPH=1 must suppress the directive even when a graph exists (code-enforced opt-out)."""
    import os
    gdir = tmp_path / "graphify-out"
    gdir.mkdir()
    (gdir / "graph.json").write_text("{}")
    scout = _copy_scout(tmp_path)
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    env = dict(os.environ, REBUILD_NO_GRAPH="1")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--plan-dir", str(plan_dir),
         "--scout-report", str(scout), "--stack-note", "PHP monolith"],
        capture_output=True, text=True, timeout=30, cwd=str(tmp_path), env=env,
    )
    assert result.returncode == 0, result.stderr
    content = (plan_dir / "artifacts" / "_session-context.md").read_text()
    assert MARKER not in content
