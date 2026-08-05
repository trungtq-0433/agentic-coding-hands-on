"""Tests for incremental_planner.py --feature-specs, --flows, --glossary modes.

Also covers build_source_to_fcode.py cursor isolation (--cursor) and
build_index() v4 technical-spec.md compatibility.

Covers:
- [RT-C1] --feature-specs: absent _source-to-fcode.json → all fcodes, exit 0 (no halt)
- [RT-C1] --feature-specs: present index + valid SHA → only affected fcodes
- [RT-C1] --feature-specs: present index + bad/missing SHA → all fcodes (fallback)
- [preflight] --flows / --glossary: always returns all-features payload
- [V7] core incremental: changed source that maps to F### → stale_features True
- [V7] core incremental: changed source NOT in index → stale_features False, no markers written
- [V7] stale_flows / stale_glossary derivation rules
- [② cursor isolation] build_source_to_fcode.py --cursor flows advances last_flows_run_sha
                       and leaves last_rebuild_sha UNCHANGED (and vice versa)
- [③ reverse-index] build_index() over v4 4-file dir (technical-spec.md, no spec.md) → non-empty
- [③ reverse-index] build_index() over empty docs/features/ → empty + exit 0
- [RT-C6] incremental_planner constants: Wave6.8 / Wave6.9 absent from WAVE_ORDER + CASCADE_CHAINS
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

FIXTURES_DIR = _TESTS_DIR / "fixtures"
INCREMENTAL_FIXTURES = FIXTURES_DIR / "incremental"
PLANNER_SCRIPT = _SCRIPTS_DIR / "incremental_planner.py"
BUILD_INDEX_SCRIPT = _SCRIPTS_DIR / "build_source_to_fcode.py"
PYTHON = sys.executable
REPO_ROOT = Path(__file__).resolve().parents[5]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_git_repo(d: Path) -> str:
    """Create a git repo with one commit; return HEAD SHA."""
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "t@t.com"],
                   capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                   capture_output=True, check=True)
    (d / "init.txt").write_text("init")
    subprocess.run(["git", "-C", str(d), "add", "."], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-m", "init"],
                   capture_output=True, check=True)
    r = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _make_canonical_json(fcodes: list[str]) -> dict:
    return {
        "generated_at": "2026-06-01T08:00:00Z",
        "plan": "test-plan",
        "features": [
            {"fcode": fc, "slug": f"{fc}_Feat", "name": fc, "priority": "P0",
             "type": "ui", "related": {}}
            for fc in fcodes
        ],
    }


def _seed_planner_base(tmp: Path) -> dict:
    """Create minimal planner env without git init. Returns paths dict."""
    plan_dir = tmp / "plans" / "test-plan"
    artifacts = plan_dir / "artifacts"
    docs_root = tmp / "docs"
    docs_generated = docs_root / "generated"
    docs_features_f001 = docs_root / "features" / "F001_Auth"

    artifacts.mkdir(parents=True)
    docs_generated.mkdir(parents=True)
    docs_features_f001.mkdir(parents=True)

    # Scout report
    shutil.copy(INCREMENTAL_FIXTURES / "synthetic-scout-report.md",
                artifacts / "scout-report.md")
    # Canonical fcodes
    canonical = _make_canonical_json(["F001", "F005"])
    (artifacts / "_canonical-fcodes.json").write_text(json.dumps(canonical))
    (docs_root / "_canonical-fcodes.json").write_text(json.dumps(canonical))
    # Reverse index
    shutil.copy(INCREMENTAL_FIXTURES / "synthetic-reverse-index.json",
                docs_root / "_source-to-fcode.json")
    # Stub core artifacts
    (docs_generated / "route-list.md").write_text("# route-list\nstub\n")
    (docs_generated / "entities.md").write_text("# data-model\nstub\n")
    # Feature spec stub
    (docs_features_f001 / "spec.md").write_text("# F001 Auth\n")

    out = str(artifacts / ".incremental-plan.json")
    return {
        "plan_dir": str(plan_dir),
        "docs_root": str(docs_root),
        "out": out,
    }


# ---------------------------------------------------------------------------
# [RT-C1] --feature-specs: absent index → all fcodes, exit 0
# ---------------------------------------------------------------------------

class TestFeatureSpecsAbsentIndex:
    def test_absent_index_returns_all_fcodes_exit_0(self, tmp_path):
        """[RT-C1] No _source-to-fcode.json → all fcodes returned, exit 0."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)
        # Remove the reverse index
        ri_path = Path(env["docs_root"]) / "_source-to-fcode.json"
        ri_path.unlink()

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "feature-specs"
        assert payload["fallback_reason"] == "index_absent"
        # All canonical fcodes must be returned
        assert set(payload["affected_fcodes"]) == {"F001", "F005"}

    def test_absent_index_does_not_halt(self, tmp_path):
        """[RT-C1] Missing index must not exit 1 (hard halt was the pre-fix behavior)."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)
        ri_path = Path(env["docs_root"]) / "_source-to-fcode.json"
        ri_path.unlink()

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        # exit 1 = hard halt (forbidden by RT-C1); exit 0 = correct
        assert r.returncode != 1, \
            f"--feature-specs must never exit 1 on absent index (RT-C1); stderr: {r.stderr}"


# ---------------------------------------------------------------------------
# [RT-C1] --feature-specs: present index + unreachable SHA → all fcodes
# ---------------------------------------------------------------------------

class TestFeatureSpecsUnreachableSha:
    def test_unreachable_sha_fallback_to_all_fcodes(self, tmp_path):
        """[RT-C1] If last_feature_spec_run_sha is unreachable → all fcodes (not halt)."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)
        # Write state with a bad feature-specs cursor SHA
        state = {
            "last_feature_spec_run_sha": "0000000000000000000000000000000000000000",
            "last_rebuild_sha": "0000000000000000000000000000000000000000",
            "mode": "full",
        }
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert set(payload["affected_fcodes"]) == {"F001", "F005"}, \
            "All fcodes expected when SHA unreachable"

    def test_missing_sha_fallback_to_all_fcodes(self, tmp_path):
        """[RT-C1] State has no last_feature_spec_run_sha (first run) → all fcodes."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)
        # State with no feature-specs cursor key (first --feature-specs run)
        state = {"mode": "full"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert set(payload["affected_fcodes"]) == {"F001", "F005"}


# ---------------------------------------------------------------------------
# [RT-C1] --feature-specs: present index + valid SHA → only affected fcodes
# ---------------------------------------------------------------------------

class TestFeatureSpecsIncrementalReverse:
    def test_reverse_index_resolution_produces_affected_fcodes(self, tmp_path):
        """[RT-C1] Changed source file maps to F001 via index → only F001 affected."""
        env = _seed_planner_base(tmp_path)
        sha = _init_git_repo(tmp_path)
        # Write valid state: feature-specs cursor at the pre-change commit
        state = {"last_feature_spec_run_sha": sha, "last_rebuild_sha": sha, "mode": "full"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))

        # Commit a change to a file that maps to F001 in the synthetic index
        # synthetic-reverse-index.json: "api/app/Http/Controllers/AuthController.php" → F001
        src_file = tmp_path / "api" / "app" / "Http" / "Controllers" / "AuthController.php"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("<?php // changed")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "change auth"],
                       capture_output=True, check=True)

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert "F001" in payload["affected_fcodes"], \
            "F001 must be affected when AuthController.php changed"

    def test_unrelated_change_yields_empty_fcodes(self, tmp_path):
        """[RT-C1] A change not in the reverse index yields empty affected_fcodes."""
        env = _seed_planner_base(tmp_path)
        sha = _init_git_repo(tmp_path)
        state = {"last_feature_spec_run_sha": sha, "last_rebuild_sha": sha, "mode": "full"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))

        # Commit a docs/ change that won't map to any fcode
        (tmp_path / "docs" / "README.md").write_text("# Docs\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "readme"],
                       capture_output=True, check=True)

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["affected_fcodes"] == [], \
            "No fcodes expected when the changed file isn't in the reverse index"

    def test_core_cursor_set_but_feature_cursor_empty_returns_all(self, tmp_path):
        """[regression] last_rebuild_sha set (reachable) but last_feature_spec_run_sha empty
        must process ALL fcodes — NOT diff from the core cursor. The pre-fix code read
        last_rebuild_sha and diffed HEAD..HEAD → empty → 0 specs generated on first run."""
        env = _seed_planner_base(tmp_path)
        sha = _init_git_repo(tmp_path)
        # Core has run (last_rebuild_sha = HEAD, reachable) but feature-specs never has.
        state = {"last_rebuild_sha": sha, "mode": "full"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--feature-specs"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["fallback_reason"] == "first_run"
        assert set(payload["affected_fcodes"]) == {"F001", "F005"}, \
            "first --feature-specs run must process ALL fcodes regardless of last_rebuild_sha"


# ---------------------------------------------------------------------------
# [preflight] --flows and --glossary always-all-features behavior
# ---------------------------------------------------------------------------

class TestFlowsGlossaryModes:
    def test_flows_mode_payload(self, tmp_path):
        """--flows emits mode=flows with affected_flows list (can be empty)."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--flows"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "flows"
        assert "affected_flows" in payload
        assert isinstance(payload["affected_flows"], list)

    def test_flows_mode_includes_existing_flow_files(self, tmp_path):
        """--flows lists all flow files present in docs/flows/."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)
        # Add flow files to docs/flows/
        flows_dir = Path(env["docs_root"]) / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "flow-auth.md").write_text("# Auth Flow\n")
        (flows_dir / "flow-checkout.md").write_text("# Checkout Flow\n")

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--flows"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert "flow-auth.md" in payload["affected_flows"]
        assert "flow-checkout.md" in payload["affected_flows"]

    def test_glossary_mode_payload(self, tmp_path):
        """--glossary emits mode=glossary."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--glossary"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "glossary"

    def test_flows_mode_exit_0_even_with_empty_flows_dir(self, tmp_path):
        """--flows exits 0 when docs/flows/ is absent (no flows yet generated)."""
        env = _seed_planner_base(tmp_path)
        _init_git_repo(tmp_path)
        # Ensure docs/flows/ does not exist
        flows_dir = Path(env["docs_root"]) / "flows"
        if flows_dir.exists():
            shutil.rmtree(flows_dir)

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"],
             "--out", env["out"],
             "--flows"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["affected_flows"] == []


# ---------------------------------------------------------------------------
# [V7] Selective staleness flags in core incremental payload
# ---------------------------------------------------------------------------

class TestSelectiveStaleness:
    """Tests for _compute_stale_flags — imported directly for unit-level assertions."""

    def test_stale_features_when_source_in_index(self):
        """[V7] A changed source that maps to an fcode → stale_features True."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        ri = {"index": {"api/auth.php": ["F001"]}}
        stale_f, stale_fl, stale_gl = _compute_stale_flags(
            affected_waves=[], affected_fcodes=[], reverse_index=ri,
            all_changed=["api/auth.php"],
        )
        assert stale_f is True

    def test_no_stale_when_change_not_in_index(self):
        """[V7] A changed file not in the index → all stale flags False."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        ri = {"index": {"api/auth.php": ["F001"]}}
        stale_f, stale_fl, stale_gl = _compute_stale_flags(
            affected_waves=[], affected_fcodes=[], reverse_index=ri,
            all_changed=["docs/README.md"],
        )
        assert stale_f is False
        assert stale_fl is False
        assert stale_gl is False

    def test_stale_flows_when_features_stale(self):
        """[V7] stale_flows = True when stale_features = True (per derivation rule)."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        ri = {"index": {"api/auth.php": ["F001"]}}
        _, stale_fl, _ = _compute_stale_flags(
            affected_waves=[], affected_fcodes=[], reverse_index=ri,
            all_changed=["api/auth.php"],
        )
        assert stale_fl is True

    def test_stale_glossary_when_features_stale(self):
        """[V7] stale_glossary = True when stale_features = True."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        ri = {"index": {"api/auth.php": ["F001"]}}
        _, _, stale_gl = _compute_stale_flags(
            affected_waves=[], affected_fcodes=[], reverse_index=ri,
            all_changed=["api/auth.php"],
        )
        assert stale_gl is True

    def test_stale_flows_when_screen_flow_wave_fires(self):
        """[V7] stale_flows = True when screen-flow wave fires (even if no features touched)."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        stale_f, stale_fl, stale_gl = _compute_stale_flags(
            affected_waves=["Wave2: screen-list + screen-flow"],
            affected_fcodes=[], reverse_index={"index": {}},
            all_changed=["some/screen.vue"],
        )
        assert stale_fl is True
        # features NOT stale (screen file not in index)
        assert stale_f is False

    def test_stale_glossary_when_data_model_wave_fires(self):
        """[V7] stale_glossary = True when data-model wave fires."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        _, _, stale_gl = _compute_stale_flags(
            affected_waves=["Wave1: data-model"],
            affected_fcodes=[], reverse_index={"index": {}},
            all_changed=["api/models/User.php"],
        )
        assert stale_gl is True

    def test_stale_flows_when_data_model_wave_fires(self):
        """[V7] stale_flows = True when data-model wave fires."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        _, stale_fl, _ = _compute_stale_flags(
            affected_waves=["Wave1: data-model"],
            affected_fcodes=[], reverse_index={"index": {}},
            all_changed=["api/models/User.php"],
        )
        assert stale_fl is True

    def test_no_stale_flags_on_empty_diff(self):
        """[V7] No changed files → no stale flags."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        stale_f, stale_fl, stale_gl = _compute_stale_flags(
            affected_waves=[], affected_fcodes=[], reverse_index={"index": {}},
            all_changed=[],
        )
        assert stale_f is False
        assert stale_fl is False
        assert stale_gl is False

    def test_stale_features_set_by_affected_fcodes(self):
        """[V7] Non-empty affected_fcodes (from W5 rerun) → stale_features True."""
        from incremental_planner import _compute_stale_flags  # noqa: PLC0415
        stale_f, _, _ = _compute_stale_flags(
            affected_waves=["Wave5: feature-list"],
            affected_fcodes=["F001"],
            reverse_index={"index": {}},
            all_changed=[],
        )
        assert stale_f is True


# ---------------------------------------------------------------------------
# [② cursor isolation] build_source_to_fcode.py --cursor advances ONLY the named cursor
# ---------------------------------------------------------------------------

class TestCursorIsolation:
    """[② cursor isolation] Each --cursor value advances ONLY its own state field."""

    def _make_repo_with_features(self, tmp_path: Path) -> tuple[Path, Path, Path]:
        """Create git repo, feature spec, state/index out paths. Returns (repo, state_out, index_out)."""
        repo = tmp_path / "repo"
        feat_dir = repo / "docs" / "features" / "F001_Auth"
        feat_dir.mkdir(parents=True)
        (feat_dir / "technical-spec.md").write_text(
            "# F001 Technical Spec\n\n"
            "## Source Code References\n\n"
            "| File | Purpose |\n"
            "| `api/AuthController.php` | auth logic |\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"],
                       capture_output=True, check=True)
        state_out = repo / "docs" / ".rebuild-state.json"
        index_out = repo / "docs" / "_source-to-fcode.json"
        return repo, state_out, index_out

    def _run_index_script(self, repo: Path, state_out: Path, index_out: Path,
                          cursor: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [PYTHON, str(BUILD_INDEX_SCRIPT),
             "--specs-root", str(repo / "docs" / "features"),
             "--docs-root", str(repo / "docs"),
             "--state-out", str(state_out),
             "--index-out", str(index_out),
             "--mode", "full",
             "--cursor", cursor],
            capture_output=True, text=True, timeout=30, cwd=str(repo),
        )

    def test_cursor_flows_advances_only_flows_sha(self, tmp_path):
        """[②] --cursor flows advances last_flows_run_sha, leaves last_rebuild_sha unchanged."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        prior_rebuild_sha = "aabbccdd" * 5  # 40 hex chars

        # Seed prior state with a known last_rebuild_sha
        prior_state = {
            "last_rebuild_sha": prior_rebuild_sha,
            "last_feature_spec_run_sha": "",
            "last_flows_run_sha": "",
            "last_glossary_run_sha": "",
        }
        state_out.parent.mkdir(parents=True, exist_ok=True)
        state_out.write_text(json.dumps(prior_state))

        r = self._run_index_script(repo, state_out, index_out, cursor="flows")
        assert r.returncode == 0, r.stderr

        state = json.loads(state_out.read_text())
        # last_rebuild_sha must be UNCHANGED
        assert state["last_rebuild_sha"] == prior_rebuild_sha, \
            "--cursor flows must not modify last_rebuild_sha [② cursor isolation]"
        # last_flows_run_sha must have been updated to HEAD
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        assert state["last_flows_run_sha"] == head, \
            "--cursor flows must advance last_flows_run_sha to HEAD"

    def test_cursor_core_advances_only_rebuild_sha(self, tmp_path):
        """[②] --cursor core advances last_rebuild_sha, leaves other cursors unchanged."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        prior_flows_sha = "deadbeef" * 5  # 40 hex chars

        prior_state = {
            "last_rebuild_sha": "",
            "last_feature_spec_run_sha": "",
            "last_flows_run_sha": prior_flows_sha,
            "last_glossary_run_sha": "",
        }
        state_out.parent.mkdir(parents=True, exist_ok=True)
        state_out.write_text(json.dumps(prior_state))

        r = self._run_index_script(repo, state_out, index_out, cursor="core")
        assert r.returncode == 0, r.stderr

        state = json.loads(state_out.read_text())
        # last_flows_run_sha must be UNCHANGED
        assert state["last_flows_run_sha"] == prior_flows_sha, \
            "--cursor core must not modify last_flows_run_sha [② cursor isolation]"
        # last_rebuild_sha must have been updated
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        assert state["last_rebuild_sha"] == head

    def test_cursor_glossary_advances_only_glossary_sha(self, tmp_path):
        """[②] --cursor glossary advances last_glossary_run_sha, preserves others."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        prior_rebuild_sha = "cafebabe" * 5  # 40 hex chars

        prior_state = {
            "last_rebuild_sha": prior_rebuild_sha,
            "last_feature_spec_run_sha": "",
            "last_flows_run_sha": "",
            "last_glossary_run_sha": "",
        }
        state_out.parent.mkdir(parents=True, exist_ok=True)
        state_out.write_text(json.dumps(prior_state))

        r = self._run_index_script(repo, state_out, index_out, cursor="glossary")
        assert r.returncode == 0, r.stderr

        state = json.loads(state_out.read_text())
        assert state["last_rebuild_sha"] == prior_rebuild_sha, \
            "--cursor glossary must not modify last_rebuild_sha [② cursor isolation]"
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        assert state["last_glossary_run_sha"] == head

    def test_cursor_jobs_advances_only_jobs_sha(self, tmp_path):
        """[F1/v26.1.0] --cursor jobs advances last_jobs_run_sha, preserves others."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        prior_rebuild_sha = "beefcafe" * 5  # 40 hex chars

        prior_state = {
            "last_rebuild_sha": prior_rebuild_sha,
            "last_feature_spec_run_sha": "",
            "last_flows_run_sha": "",
            "last_glossary_run_sha": "",
            "last_jobs_run_sha": "",
        }
        state_out.parent.mkdir(parents=True, exist_ok=True)
        state_out.write_text(json.dumps(prior_state))

        r = self._run_index_script(repo, state_out, index_out, cursor="jobs")
        assert r.returncode == 0, r.stderr

        state = json.loads(state_out.read_text())
        assert state["last_rebuild_sha"] == prior_rebuild_sha, \
            "--cursor jobs must not modify last_rebuild_sha [cursor isolation]"
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        assert state["last_jobs_run_sha"] == head

    def test_cursor_test_cases_advances_only_test_cases_sha(self, tmp_path):
        """[F1/v26.1.0] --cursor test-cases advances last_test_cases_run_sha, preserves others."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        prior_rebuild_sha = "decafbad" * 5  # 40 hex chars

        prior_state = {
            "last_rebuild_sha": prior_rebuild_sha,
            "last_feature_spec_run_sha": "",
            "last_flows_run_sha": "",
            "last_glossary_run_sha": "",
            "last_jobs_run_sha": "",
            "last_test_cases_run_sha": "",
        }
        state_out.parent.mkdir(parents=True, exist_ok=True)
        state_out.write_text(json.dumps(prior_state))

        r = self._run_index_script(repo, state_out, index_out, cursor="test-cases")
        assert r.returncode == 0, r.stderr

        state = json.loads(state_out.read_text())
        assert state["last_rebuild_sha"] == prior_rebuild_sha, \
            "--cursor test-cases must not modify last_rebuild_sha [cursor isolation]"
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        assert state["last_test_cases_run_sha"] == head

    def test_cursor_feature_specs_advances_only_feature_sha(self, tmp_path):
        """[②] --cursor feature-specs advances last_feature_spec_run_sha only."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        prior_flows_sha = "11223344" * 5  # 40 hex chars

        prior_state = {
            "last_rebuild_sha": "",
            "last_feature_spec_run_sha": "",
            "last_flows_run_sha": prior_flows_sha,
            "last_glossary_run_sha": "",
        }
        state_out.parent.mkdir(parents=True, exist_ok=True)
        state_out.write_text(json.dumps(prior_state))

        r = self._run_index_script(repo, state_out, index_out, cursor="feature-specs")
        assert r.returncode == 0, r.stderr

        state = json.loads(state_out.read_text())
        assert state["last_flows_run_sha"] == prior_flows_sha, \
            "--cursor feature-specs must not modify last_flows_run_sha [② cursor isolation]"
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        assert state["last_feature_spec_run_sha"] == head

    def test_last_rebuild_sha_override_ignored_for_non_core_cursor(self, tmp_path):
        """[② guard] --last-rebuild-sha is a core-cursor override only. Combined with a non-core
        --cursor it must NOT land in that cursor (silent misroute); HEAD is stamped + a warning."""
        repo, state_out, index_out = self._make_repo_with_features(tmp_path)
        bogus_override = "deadbeef" * 5  # 40 hex chars, NOT a real commit

        r = subprocess.run(
            [PYTHON, str(BUILD_INDEX_SCRIPT),
             "--specs-root", str(repo / "docs" / "features"),
             "--docs-root", str(repo / "docs"),
             "--state-out", str(state_out),
             "--index-out", str(index_out),
             "--mode", "full",
             "--cursor", "flows",
             "--last-rebuild-sha", bogus_override],
            capture_output=True, text=True, timeout=30, cwd=str(repo),
        )
        assert r.returncode == 0, r.stderr
        assert "only meaningful with --cursor core" in r.stderr

        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True
        ).stdout.strip()
        state = json.loads(state_out.read_text())
        assert state["last_flows_run_sha"] == head, \
            "non-core cursor must be stamped with HEAD, not the --last-rebuild-sha override"
        assert state["last_flows_run_sha"] != bogus_override, \
            "--last-rebuild-sha must not contaminate last_flows_run_sha"


# ---------------------------------------------------------------------------
# [③ reverse-index] build_index() v4 technical-spec.md compatibility
# ---------------------------------------------------------------------------

class TestBuildIndexV4:
    """build_index() must read */technical-spec.md for v4 4-file feature dirs."""

    def test_v4_technical_spec_yields_nonempty_index(self, tmp_path):
        """[③] technical-spec.md present (no spec.md) → non-empty index returned."""
        from build_source_to_fcode import build_index  # noqa: PLC0415

        feat_dir = tmp_path / "F001_Auth"
        feat_dir.mkdir()
        (feat_dir / "technical-spec.md").write_text(
            "# F001 Technical Spec\n\n"
            "## Source Code References\n\n"
            "| File | Purpose |\n"
            "| `api/app/Http/Controllers/AuthController.php` | auth logic |\n",
            encoding="utf-8",
        )
        # No spec.md in this directory — pure v4 layout
        assert not (feat_dir / "spec.md").exists()

        index = build_index(tmp_path)
        assert len(index) > 0, \
            "build_index() must read technical-spec.md for v4 4-file layout [③]"
        assert "api/app/Http/Controllers/AuthController.php" in index

    def test_v4_fcode_correctly_extracted_from_dir_name(self, tmp_path):
        """[③] Fcode 'F001' correctly extracted from 'F001_Auth' dir name."""
        from build_source_to_fcode import build_index  # noqa: PLC0415

        feat_dir = tmp_path / "F001_Auth"
        feat_dir.mkdir()
        (feat_dir / "technical-spec.md").write_text(
            "## Source Code References\n\n"
            "| `api/auth.php` | auth |\n",
            encoding="utf-8",
        )
        index = build_index(tmp_path)
        assert "api/auth.php" in index
        assert "F001" in index["api/auth.php"]

    def test_v4_ignores_spec_md_when_technical_spec_present(self, tmp_path):
        """[③] When technical-spec.md exists, legacy spec.md is NOT double-counted."""
        from build_source_to_fcode import build_index  # noqa: PLC0415

        feat_dir = tmp_path / "F001_Auth"
        feat_dir.mkdir()
        (feat_dir / "technical-spec.md").write_text(
            "## Source Code References\n\n"
            "| `api/auth.php` | auth |\n",
            encoding="utf-8",
        )
        # Also add a legacy spec.md (should be ignored — technical-spec.md takes precedence)
        (feat_dir / "spec.md").write_text(
            "## Source Code References\n\n"
            "| `legacy/path.php` | old |\n",
            encoding="utf-8",
        )
        index = build_index(tmp_path)
        # legacy/path.php must NOT appear — it's in spec.md which is overshadowed
        assert "legacy/path.php" not in index, \
            "spec.md must be ignored when technical-spec.md is present in the same dir [③]"

    def test_empty_features_dir_returns_empty_index_exit_0(self, tmp_path):
        """[RT-C5] Empty docs/features/ → build_index returns {} (exit 0 when called as subprocess)."""
        from build_source_to_fcode import build_index  # noqa: PLC0415

        # Unit-level test: build_index on empty dir
        assert build_index(tmp_path) == {}, \
            "build_index() must return {} for empty dir (RT-C5 / [③])"

    def test_empty_dir_subprocess_exits_0(self, tmp_path):
        """[RT-C5] Subprocess call on empty features dir exits 0 (not 1)."""
        repo = tmp_path / "repo"
        repo.mkdir()
        features_dir = repo / "docs" / "features"
        features_dir.mkdir(parents=True)
        # Git needs at least one tracked file to commit
        (repo / "init.txt").write_text("init")

        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"],
                       capture_output=True, check=True)

        state_out = repo / "docs" / ".rebuild-state.json"
        index_out = repo / "docs" / "_source-to-fcode.json"
        r = subprocess.run(
            [PYTHON, str(BUILD_INDEX_SCRIPT),
             "--specs-root", str(features_dir),
             "--docs-root", str(repo / "docs"),
             "--state-out", str(state_out),
             "--index-out", str(index_out),
             "--mode", "full",
             "--last-rebuild-sha", "abcd1234"],
            capture_output=True, text=True, timeout=30, cwd=str(repo),
        )
        assert r.returncode == 0, \
            f"build_source_to_fcode.py must exit 0 on empty features/ dir [RT-C5]; stderr={r.stderr}"
        index = json.loads(index_out.read_text())
        assert index["index"] == {}


# ---------------------------------------------------------------------------
# [RT-C6] Wave6.8 / Wave6.9 purge from planner constants
# ---------------------------------------------------------------------------

class TestWavePurge:
    """[RT-C6] Wave6.8 (process-flow) and Wave6.9 (glossary) must be absent from
    the core cascade constants. These were removed in v5.0.0 and are now
    standalone passes (--flows, --glossary).
    """

    def test_wave6_8_absent_from_wave_order(self):
        """[RT-C6] WAVE_ORDER must not contain Wave6.8."""
        from incremental_planner import WAVE_ORDER  # noqa: PLC0415
        wave_keys = " ".join(WAVE_ORDER).lower()
        assert "wave6.8" not in wave_keys, \
            "Wave6.8: process-flow must be absent from WAVE_ORDER (RT-C6)"

    def test_wave6_9_absent_from_wave_order(self):
        """[RT-C6] WAVE_ORDER must not contain Wave6.9."""
        from incremental_planner import WAVE_ORDER  # noqa: PLC0415
        wave_keys = " ".join(WAVE_ORDER).lower()
        assert "wave6.9" not in wave_keys, \
            "Wave6.9: glossary must be absent from WAVE_ORDER (RT-C6)"

    def test_wave6_8_absent_from_cascade_chains(self):
        """[RT-C6] No cascade chain should contain Wave6.8."""
        from incremental_planner import CASCADE_CHAINS  # noqa: PLC0415
        for ftype, chain in CASCADE_CHAINS.items():
            chain_str = " ".join(chain).lower()
            assert "wave6.8" not in chain_str, \
                f"Wave6.8 found in cascade chain for '{ftype}' (RT-C6)"

    def test_wave6_9_absent_from_cascade_chains(self):
        """[RT-C6] No cascade chain should contain Wave6.9."""
        from incremental_planner import CASCADE_CHAINS  # noqa: PLC0415
        for ftype, chain in CASCADE_CHAINS.items():
            chain_str = " ".join(chain).lower()
            assert "wave6.9" not in chain_str, \
                f"Wave6.9 found in cascade chain for '{ftype}' (RT-C6)"

    def test_pipeline_md_wave68_absent_from_cascade_section(self):
        """[RT-C6] pipeline.md must not reference Wave6.8/6.9 in cascade/reconcile constants."""
        pipeline_path = _SCRIPTS_DIR.parent / "references" / "pipeline.md"
        if not pipeline_path.is_file():
            pytest.skip("pipeline.md not found — skipping file-level grep test")
        content = pipeline_path.read_text(encoding="utf-8")
        # Wave6.8 and Wave6.9 should only appear in on-demand-loading comments/references,
        # NOT in RECONCILE_MAP or cascade constant definitions.
        # We test by checking the reconcile/cascade sections specifically.
        # A simple presence check: if Wave6.8 appears in RECONCILE_MAP definition, that's a bug.
        import re
        reconcile_block_match = re.search(
            r"RECONCILE_MAP.*?(?=\n\s*\n|\Z)", content, re.DOTALL
        )
        if reconcile_block_match:
            block = reconcile_block_match.group(0)
            assert "Wave6.8" not in block, \
                "Wave6.8 found in RECONCILE_MAP block in pipeline.md (RT-C6)"
            assert "Wave6.9" not in block, \
                "Wave6.9 found in RECONCILE_MAP block in pipeline.md (RT-C6)"
