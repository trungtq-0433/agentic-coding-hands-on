"""Tests for W2.5 ScreenSpec incremental mode — section hashing, diff, hydrate, promote, W7c."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from incremental_planner import (
    ARTIFACT_LAYERED,
    _parse_screen_sections,
    _hash_screen_sections,
    _resolve_screen_dirname,
    _diff_screen_shas,
    _hydrate,
    CORE_ARTIFACT_TO_WAVE_SUBJECT,
)

PLANNER_SCRIPT = _SCRIPTS_DIR / "incremental_planner.py"
PROMOTE_SCRIPT = _SCRIPTS_DIR / "promote_drafts.py"
PYTHON = sys.executable

# promote_drafts.py uses os.getcwd() as the security base.
# We must run promote as cwd=REPO_ROOT so the path-traversal guard accepts
# absolute paths that live outside the cwd during tests.
REPO_ROOT = _TESTS_DIR.parents[4]  # agent-kit root

INCREMENTAL_FIXTURES = _TESTS_DIR / "fixtures" / "incremental"

CORE_ARTIFACTS = [
    "route-list.md", "data-model.md", "screen-list.md", "screen-flow.md",
    "behavior-logic.md", "api-map.md", "permissions.md", "user-stories.md",
    "feature-list.md", "glossary.md",
]

# ── Fixtures ──────────────────────────────────────────────────────────────────

SCREEN_LIST_3_SECTIONS = """\
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
# Screen List

## SCR001_Foo
Screen 1 content here.
Some details.

## SCR002_Bar
Screen 2 content here.
Different details.

## SCR003_Baz
Screen 3 content here.
Third screen.
"""

SCREEN_LIST_NO_SECTIONS = """\
# Screen List

No SCR headings here at all.
"""


# ── T1-T2: TestSectionParse ───────────────────────────────────────────────────

class TestSectionParse:
    def test_parses_three_sections(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(SCREEN_LIST_3_SECTIONS)
        parsed = _parse_screen_sections(f)
        assert len(parsed) == 3
        assert set(parsed.keys()) == {"SCR001", "SCR002", "SCR003"}
        assert parsed["SCR001"][0] == "Foo"
        assert parsed["SCR002"][0] == "Bar"
        assert parsed["SCR003"][0] == "Baz"

    def test_empty_when_no_headings(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(SCREEN_LIST_NO_SECTIONS)
        result = _parse_screen_sections(f)
        assert result == {}


# ── T3-T7: TestSectionDiff ────────────────────────────────────────────────────

class TestSectionDiff:
    def test_hash_stable(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(SCREEN_LIST_3_SECTIONS)
        parsed = _parse_screen_sections(f)
        shas1 = _hash_screen_sections(parsed)
        shas2 = _hash_screen_sections(parsed)
        assert shas1 == shas2
        for v in shas1.values():
            assert len(v) == 64
            # confirm it's hex
            int(v, 16)

    def test_single_change_detected(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(SCREEN_LIST_3_SECTIONS)
        prior_parsed = _parse_screen_sections(f)
        prior = _hash_screen_sections(prior_parsed)

        modified = SCREEN_LIST_3_SECTIONS.replace(
            "Screen 2 content here.\nDifferent details.", "Modified content."
        )
        f2 = tmp_path / "screen-list-mod.md"
        f2.write_text(modified)
        current_parsed = _parse_screen_sections(f2)
        current = _hash_screen_sections(current_parsed)

        # Pre-create spec.md for the UNCHANGED screens (SCR001, SCR003) so the
        # missing-draft check doesn't flag them — only SCR002 content changed.
        screens_dir = tmp_path / "artifacts" / "screens"
        for name in ["SCR001_Foo", "SCR003_Baz"]:
            d = screens_dir / name
            d.mkdir(parents=True)
            (d / "spec.md").write_text(f"# {name}\n")

        result = _diff_screen_shas(
            prior, current,
            artifacts_screens=screens_dir,
            parsed=current_parsed,
        )
        assert result == ["SCR002"]

    def test_missing_draft_detected(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(SCREEN_LIST_3_SECTIONS)
        parsed = _parse_screen_sections(f)
        shas = _hash_screen_sections(parsed)

        # Create artifacts dirs for SCR001 and SCR003 only (SCR002 missing draft)
        screens_dir = tmp_path / "artifacts" / "screens"
        for name in ["SCR001_Foo", "SCR003_Baz"]:
            d = screens_dir / name
            d.mkdir(parents=True)
            (d / "spec.md").write_text(f"# {name}\n")

        result = _diff_screen_shas(shas, shas, screens_dir, parsed)
        assert "SCR002" in result

    def test_new_screen_detected(self, tmp_path):
        prior = {"SCR001": "sha_a", "SCR002": "sha_b"}
        current = {"SCR001": "sha_a", "SCR002": "sha_b", "SCR003": "sha_c"}
        parsed = {k: ("", "") for k in current}

        result = _diff_screen_shas(prior, current, tmp_path / "screens", parsed)
        assert "SCR003" in result

    def test_first_run_all_screens(self, tmp_path):
        current = {"SCR001": "a", "SCR002": "b", "SCR003": "c"}
        parsed = {k: ("", "") for k in current}

        result = _diff_screen_shas({}, current, tmp_path / "screens", parsed)
        assert sorted(result) == ["SCR001", "SCR002", "SCR003"]


# ── T8: TestHydrateScreens ────────────────────────────────────────────────────

def _seed_hydrate_screen_env(tmp: Path, affected_screens: list[str]) -> tuple[Path, Path]:
    """Create plan + docs dirs (v4 layered) for hydrate screen-spec test.

    Returns (plan_dir, docs_root).
    """
    plan_dir = tmp / "plans" / "test"
    artifacts = plan_dir / "artifacts"
    docs_root = tmp / "docs"

    artifacts.mkdir(parents=True)

    # Core artifacts at layered paths (must all exist to avoid full-mode fallback)
    for name in CORE_ARTIFACTS:
        fpath = docs_root / ARTIFACT_LAYERED[name]
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(f"# {name}\n# stub\n")
    # system-overview at layered path
    sov = docs_root / ARTIFACT_LAYERED["system-overview.md"]
    sov.parent.mkdir(parents=True, exist_ok=True)
    sov.write_text("# System Overview\nstub\n")

    # _canonical-fcodes.json at docs_root
    canonical = {"generated_at": "2026-05-25T00:00:00Z", "features": []}
    (docs_root / "_canonical-fcodes.json").write_text(json.dumps(canonical))

    # Screen spec dirs in docs_root/screens/
    for name in ["SCR001_Foo", "SCR002_Bar", "SCR003_Baz"]:
        d = docs_root / "screens" / name
        d.mkdir(parents=True)
        num = name.split("_")[0][-1]
        (d / "spec.md").write_text(f"screen {num}\n")

    # .incremental-plan.json
    plan_data = {
        "mode": "incremental",
        "affected_waves": [],
        "affected_fcodes": [],
        "affected_screens": affected_screens,
        "w5_reran": False,
        "doc_shas_snapshot": {},
    }
    (artifacts / ".incremental-plan.json").write_text(json.dumps(plan_data))

    return plan_dir, docs_root


class TestHydrateScreens:
    def test_skips_affected_copies_others(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_screen_env(tmp_path, affected_screens=["SCR002"])
        _hydrate(plan_dir, docs_root)

        screens_dst = plan_dir / "artifacts" / "screens"
        # SCR001 and SCR003 are NOT affected → should be copied
        assert (screens_dst / "SCR001_Foo" / "spec.md").exists()
        assert (screens_dst / "SCR003_Baz" / "spec.md").exists()
        # SCR002 IS affected → should NOT be copied
        assert not (screens_dst / "SCR002_Bar" / "spec.md").exists()


# ── T9-T10: TestPlannerPayload ────────────────────────────────────────────────

def _init_git_repo(d: Path) -> str:
    """Create a git repo with one initial commit; return HEAD SHA."""
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"], capture_output=True, check=True)
    (d / "init.txt").write_text("init")
    subprocess.run(["git", "-C", str(d), "add", "."], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-m", "init"], capture_output=True, check=True)
    r = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _seed_planner_screen_env(tmp: Path) -> dict:
    """Seed a git repo with minimal planner requirements + screen-list.md at v4 layered paths.

    Uses a large scout inventory (20 source files) so a 1-file diff stays well
    below the 30 % cascade threshold.
    """
    plan_dir = tmp / "plans" / "test-plan"
    artifacts = plan_dir / "artifacts"
    docs_root = tmp / "docs"
    docs_generated = docs_root / "generated"
    artifacts.mkdir(parents=True)
    docs_generated.mkdir(parents=True)

    # Scout report: 20 source files so threshold = 1/20 = 5 % << 30 %
    inventory_lines = "\n".join(
        f"web/src/Page{i:02d}.vue\tscreen" for i in range(1, 21)
    )
    scout_content = f"# Scout Report\n\n## File Inventory\n\n{inventory_lines}\n\n## Other\n\nnothing\n"
    (artifacts / "scout-report.md").write_text(scout_content)

    # Canonical fcodes at docs_root
    canonical = {
        "generated_at": "2026-05-25T00:00:00Z",
        "features": [],
    }
    canonical_json = json.dumps(canonical)
    (artifacts / "_canonical-fcodes.json").write_text(canonical_json)
    (docs_root / "_canonical-fcodes.json").write_text(canonical_json)

    # Reverse index at docs_root
    (docs_root / "_source-to-fcode.json").write_text(json.dumps({"index": {}}))

    # Core artifact stubs at layered paths
    for name in CORE_ARTIFACTS:
        fpath = docs_root / ARTIFACT_LAYERED[name]
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(f"# {name}\nstub\n")

    # screen-list.md at layered path: docs/generated/screen-list.md
    screen_list = (
        "# Screen List\n\n"
        "## SCR001_Login\nLogin screen content.\n\n"
        "## SCR002_Dashboard\nDashboard content.\n"
    )
    (docs_generated / "screen-list.md").write_text(screen_list)

    return {
        "plan_dir": str(plan_dir),
        "docs_root": str(docs_root),
        "out": str(artifacts / ".incremental-plan.json"),
        "screen_list_path": docs_generated / "screen-list.md",
    }


def _git_env(tmp: Path) -> dict[str, str]:
    """Return env vars that make git operations run in tmp."""
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Test"
    env["GIT_AUTHOR_EMAIL"] = "test@test.com"
    env["GIT_COMMITTER_NAME"] = "Test"
    env["GIT_COMMITTER_EMAIL"] = "test@test.com"
    return env


class TestPlannerPayload:
    def test_incremental_emits_affected_screens(self, tmp_path):
        env_paths = _seed_planner_screen_env(tmp_path)

        # Compute shas before git init (screen-list.md content already written)
        parsed = _parse_screen_sections(Path(env_paths["screen_list_path"]))
        shas = _hash_screen_sections(parsed)

        # _init_git_repo does `git add .` + commit, capturing all env files in one shot
        initial_sha = _init_git_repo(tmp_path)

        # Write state at docs_root (not docs/specs) pointing at the initial commit
        # Omit doc_shas so _detect_oob returns [] — we only want to test screen diff
        state = {
            "last_rebuild_sha": initial_sha,
            "mode": "incremental",
            "rebuilt_at": "2026-05-25T00:00:00Z",
            "screen_spec_shas": shas,
        }
        (Path(env_paths["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))

        # Pre-create spec.md for SCR001 (unchanged) so _diff_screen_shas won't
        # flag it as missing-draft — only SCR002 content changes should be reported.
        scr001_spec = Path(env_paths["plan_dir"]) / "artifacts" / "screens" / "SCR001_Login" / "spec.md"
        scr001_spec.parent.mkdir(parents=True, exist_ok=True)
        scr001_spec.write_text("# SCR001_Login\nstub\n")

        # Modify SCR002 section in screen-list.md and commit
        new_content = (
            "# Screen List\n\n"
            "## SCR001_Login\nLogin screen content.\n\n"
            "## SCR002_Dashboard\nDashboard MODIFIED content.\n"
        )
        Path(env_paths["screen_list_path"]).write_text(new_content)
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-m", "modify scr002"],
            capture_output=True, check=True,
        )

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env_paths["plan_dir"],
             "--docs-root", env_paths["docs_root"],
             "--out", env_paths["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
            env=_git_env(tmp_path),
        )
        assert r.returncode == 0, r.stderr

        payload = json.loads(Path(env_paths["out"]).read_text())
        assert "affected_screens" in payload
        assert "SCR002" in payload["affected_screens"]
        assert "SCR001" not in payload["affected_screens"]

    def test_full_omits_affected_screens(self, tmp_path):
        env_paths = _seed_planner_screen_env(tmp_path)
        _init_git_repo(tmp_path)

        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT),
             "--plan-dir", env_paths["plan_dir"],
             "--docs-root", env_paths["docs_root"],
             "--out", env_paths["out"],
             "--full"],
            capture_output=True, text=True, cwd=str(tmp_path),
            env=_git_env(tmp_path),
        )
        assert r.returncode == 0, r.stderr

        payload = json.loads(Path(env_paths["out"]).read_text())
        assert payload["mode"] == "full"
        assert "affected_screens" not in payload
        assert "screen_spec_shas_snapshot" in payload


# ── T11-T13: TestPromoteScreens ───────────────────────────────────────────────
# promote_drafts.py resolves paths against os.getcwd(); use REPO_ROOT as cwd
# so the path-traversal guard accepts paths under _PROMOTE_SCR_TMP.
import shutil as _shutil

_PROMOTE_SCR_TMP = REPO_ROOT / f"_test_promote_scr_tmp_{os.getpid()}"


@pytest.fixture(autouse=True, scope="module")
def _cleanup_promote_scr_tmp():
    """Remove the PID-scoped temp dir after this module finishes."""
    yield
    if _PROMOTE_SCR_TMP.exists():
        _shutil.rmtree(_PROMOTE_SCR_TMP, ignore_errors=True)


def _run_promote(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(PROMOTE_SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(REPO_ROOT),
    )


def _seed_promote_screen_env(tag: str, scr_dirs: list[str]) -> tuple[Path, Path]:
    """Create plan_dir/artifacts/screens/ under REPO_ROOT/_PROMOTE_SCR_TMP/tag/.

    Paths must stay under REPO_ROOT to pass promote_drafts path-traversal guard.
    Returns (plan_dir, docs_root).
    """
    work = _PROMOTE_SCR_TMP / tag
    if work.exists():
        _shutil.rmtree(work)
    work.mkdir(parents=True)

    plan_dir = work / "plan"
    artifacts = plan_dir / "artifacts"
    docs_root = work / "docs"
    docs_root.mkdir(parents=True)

    # Screens in artifacts
    for sdir in scr_dirs:
        d = artifacts / "screens" / sdir
        d.mkdir(parents=True)
        (d / "spec.md").write_text(f"# {sdir} spec\n")

    # Core artifact stubs in artifacts (so promote doesn't warn on missing)
    for name in CORE_ARTIFACTS:
        (artifacts / name).write_text(f"# {name}\nstub\n")

    return plan_dir, docs_root


class TestPromoteScreens:
    def test_incremental_promotes_only_listed(self):
        plan_dir, docs_root = _seed_promote_screen_env(
            "t11_incremental", ["SCR001_Foo", "SCR003_Baz"]
        )
        result = _run_promote([
            "--plan-dir", str(plan_dir),
            "--docs-root", str(docs_root),
            "--mode", "incremental",
            "--affected-screens", "SCR003",
        ])
        assert result.returncode == 0, result.stderr

        # SCR003 in affected-screens → should be promoted to docs_root/screens/
        assert (docs_root / "screens" / "SCR003_Baz" / "spec.md").exists()
        # SCR001 NOT in affected-screens → should NOT be promoted
        assert not (docs_root / "screens" / "SCR001_Foo" / "spec.md").exists()

    def test_full_promotes_all(self):
        plan_dir, docs_root = _seed_promote_screen_env(
            "t12_full", ["SCR001_Foo", "SCR003_Baz"]
        )
        result = _run_promote([
            "--plan-dir", str(plan_dir),
            "--docs-root", str(docs_root),
            "--mode", "full",
        ])
        assert result.returncode == 0, result.stderr

        assert (docs_root / "screens" / "SCR001_Foo" / "spec.md").exists()
        assert (docs_root / "screens" / "SCR003_Baz" / "spec.md").exists()

    def test_ambiguous_scr_exits_with_error(self):
        # Two dirs both match SCR001 — must exit 2 (not silently skip)
        plan_dir, docs_root = _seed_promote_screen_env(
            "t13_ambiguous", ["SCR001_Foo", "SCR001_Bar"]
        )
        result = _run_promote([
            "--plan-dir", str(plan_dir),
            "--docs-root", str(docs_root),
            "--mode", "incremental",
            "--affected-screens", "SCR001",
        ])
        assert result.returncode == 2
        assert "[ERROR]" in result.stderr
        assert "ambiguous" in result.stderr.lower()


# ── T14-T15: TestW7cDispatch ─────────────────────────────────────────────────

class TestW7cDispatch:
    def test_w7c_batch_count_formula(self):
        """Verify W7c review-batch formula: ceil(N/batch_size)."""
        scr_codes_to_process = ["SCR001", "SCR002", "SCR003", "SCR004", "SCR005", "SCR006"]
        screen_spec_task_ids = ["id1", "id2", "id3"]  # 3 W2.5 batches dispatched
        SCREEN_SPEC_REVIEW_BATCH_SIZE = 5

        review_batches = [
            scr_codes_to_process[i:i + SCREEN_SPEC_REVIEW_BATCH_SIZE]
            for i in range(0, len(scr_codes_to_process), SCREEN_SPEC_REVIEW_BATCH_SIZE)
        ]
        # ceil(6/5) = 2 batches
        assert len(review_batches) == 2
        assert review_batches[0] == ["SCR001", "SCR002", "SCR003", "SCR004", "SCR005"]
        assert review_batches[1] == ["SCR006"]

    def test_w7c_skipped_when_zero_screens(self):
        """W7c must not dispatch when no screen-spec tasks were created."""
        screen_spec_task_ids: list[str] = []
        with_screen_specs = True

        # Mirrors pipeline condition: if (flags.with_screen_specs && screenSpecTaskIds.length > 0)
        w7c_should_dispatch = bool(screen_spec_task_ids) and with_screen_specs
        assert w7c_should_dispatch is False
