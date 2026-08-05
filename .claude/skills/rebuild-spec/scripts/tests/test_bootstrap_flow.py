"""Tests for bootstrap-from-git flow (build_source_to_fcode.py --last-rebuild-sha)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "build_source_to_fcode.py"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, timeout=30, cwd=str(cwd),
    )


def _make_v2x_repo(tmp_path: Path) -> Path:
    """Build a minimal v2.x-style docs/specs/ tree under a git repo."""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
    repo = tmp_path / "repo"
    docs_specs = repo / "docs" / "specs"
    feat_dir = docs_specs / "features" / "F001_Auth"
    feat_dir.mkdir(parents=True)
    (docs_specs / "system-overview.md").write_text("# System Overview\n", encoding="utf-8")
    (docs_specs / "feature-list.md").write_text(
        "# Feature List\n## Feature Details\n### F001: Auth\n", encoding="utf-8"
    )
    (feat_dir / "spec.md").write_text(
        "# F001: Auth\n\n**Source:** `src/auth.py:1-50`\n\n"
        "## Source Code References\n\n| File | Purpose |\n"
        "| `src/auth.py:1-50` | Auth logic |\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "initial"],
        cwd=repo, check=True, capture_output=True,
    )
    return repo


class TestBootstrapEmitsCorrectState:
    def test_state_uses_provided_sha(self, tmp_path):
        repo = _make_v2x_repo(tmp_path)
        state_out = repo / "docs" / "specs" / ".rebuild-state.json"
        index_out = repo / "docs" / "specs" / "_source-to-fcode.json"
        result = _run([
            "--specs-root", str(repo / "docs" / "specs" / "features"),
            "--docs-root", str(repo / "docs" / "specs"),
            "--state-out", str(state_out),
            "--index-out", str(index_out),
            "--mode", "full",
            "--last-rebuild-sha", "deadbeefcafe",
        ], cwd=repo)
        assert result.returncode == 0, result.stderr
        state = json.loads(state_out.read_text(encoding="utf-8"))
        assert state["last_rebuild_sha"] == "deadbeefcafe"
        assert state["mode"] == "full"
        index = json.loads(index_out.read_text(encoding="utf-8"))
        assert len(index["index"]) > 0


class TestBootstrapEmptyFeaturesDir:
    def test_empty_features_exits_0_with_empty_index(self, tmp_path):
        # [RT-C5] Contract change (v5.0.0): empty docs/features/ is valid for core-only runs.
        # build_source_to_fcode.py now exits 0 and emits an empty-but-valid index {}.
        # Previous contract: exit 1 when no spec files found.
        # New contract: exit 0, empty index — allows core pass to complete cleanly.
        repo = _make_v2x_repo(tmp_path)
        # Remove the spec file to simulate empty features dir
        feat_dir = repo / "docs" / "specs" / "features" / "F001_Auth"
        (feat_dir / "spec.md").unlink()
        feat_dir.rmdir()
        state_out = repo / "docs" / "specs" / ".rebuild-state.json"
        index_out = repo / "docs" / "specs" / "_source-to-fcode.json"
        result = _run([
            "--specs-root", str(repo / "docs" / "specs" / "features"),
            "--docs-root", str(repo / "docs" / "specs"),
            "--state-out", str(state_out),
            "--index-out", str(index_out),
            "--mode", "full",
            "--last-rebuild-sha", "deadbeefcafe",
        ], cwd=repo)
        assert result.returncode == 0, result.stderr
        index = json.loads(index_out.read_text(encoding="utf-8"))
        assert index["index"] == {}


class TestShaValidation:
    def test_invalid_sha_rejected(self, tmp_path):
        repo = _make_v2x_repo(tmp_path)
        result = _run([
            "--specs-root", str(repo / "docs" / "specs" / "features"),
            "--docs-root", str(repo / "docs" / "specs"),
            "--state-out", str(tmp_path / "state.json"),
            "--index-out", str(tmp_path / "index.json"),
            "--mode", "full",
            "--last-rebuild-sha", "not-a-sha!!",
        ], cwd=repo)
        assert result.returncode == 2
        assert "invalid format" in result.stderr

    def test_uppercase_sha_normalized(self, tmp_path):
        repo = _make_v2x_repo(tmp_path)
        state_out = repo / "docs" / "specs" / ".rebuild-state.json"
        index_out = repo / "docs" / "specs" / "_source-to-fcode.json"
        result = _run([
            "--specs-root", str(repo / "docs" / "specs" / "features"),
            "--docs-root", str(repo / "docs" / "specs"),
            "--state-out", str(state_out),
            "--index-out", str(index_out),
            "--mode", "full",
            "--last-rebuild-sha", "DEADBEEF",
        ], cwd=repo)
        assert result.returncode == 0, result.stderr
        state = json.loads(state_out.read_text(encoding="utf-8"))
        assert state["last_rebuild_sha"] == "deadbeef"

    def test_no_flag_uses_git_head(self, tmp_path):
        repo = _make_v2x_repo(tmp_path)
        state_out = repo / "docs" / "specs" / ".rebuild-state.json"
        index_out = repo / "docs" / "specs" / "_source-to-fcode.json"
        result = _run([
            "--specs-root", str(repo / "docs" / "specs" / "features"),
            "--docs-root", str(repo / "docs" / "specs"),
            "--state-out", str(state_out),
            "--index-out", str(index_out),
            "--mode", "full",
        ], cwd=repo)
        assert result.returncode == 0, result.stderr
        state = json.loads(state_out.read_text(encoding="utf-8"))
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert state["last_rebuild_sha"] == head
