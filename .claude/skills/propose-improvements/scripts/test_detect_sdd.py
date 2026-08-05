"""Tests for propose-improvements Step 1 SDD detection script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "detect_sdd.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(repo_root: Path, output_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--repo-root", str(repo_root),
         "--output-path", str(output_path),
         *extra],
        capture_output=True, text=True, check=False,
    )


def _read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Library-level tests
# ---------------------------------------------------------------------------

from detect_sdd_lib import (  # noqa: E402
    Signal,
    classify,
    normalize_spec_folder,
    primary_signals,
    resolve_specs_root,
    secondary_categories,
    secondary_signals,
    verify_spec_folder,
)


def test_no_signals_returns_false(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello")
    assert primary_signals(tmp_path) == []
    assert secondary_signals(tmp_path) == []
    assert classify([], []) is False
    assert resolve_specs_root(tmp_path) == ""


def test_primary_specs_dir_with_md_fires(tmp_path: Path) -> None:
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "feature-list.md").write_text("# FeatureList")
    hits = primary_signals(tmp_path)
    assert any(s.kind == "specs-dir" and s.path == "specs/" for s in hits)
    assert classify(hits, []) is True
    assert resolve_specs_root(tmp_path) == "specs/"


def test_primary_dotspecify_dir_with_any_file_fires(tmp_path: Path) -> None:
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify" / "config.toml").write_text("")
    hits = primary_signals(tmp_path)
    assert any(s.path == ".specify/" for s in hits)
    assert classify(hits, []) is True


def test_primary_root_spec_file_fires(tmp_path: Path) -> None:
    (tmp_path / "SPECIFICATION.md").write_text("...")
    hits = primary_signals(tmp_path)
    assert any(s.kind == "spec-file" and s.path == "SPECIFICATION.md" for s in hits)
    assert classify(hits, []) is True


def test_one_secondary_only_returns_false(tmp_path: Path) -> None:
    # Just spec-kit prefix filename under docs/ -> only secondary category #1 fires.
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "feature-billing.md").write_text("# Billing")
    secondary = secondary_signals(tmp_path)
    assert secondary_categories(secondary) == 1
    assert classify([], secondary) is False


def test_two_distinct_secondary_categories_fires(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    # Category 1: spec-kit filename prefix.
    (docs / "feature-foo.md").write_text("# Foo")
    # Category 2: spec-artifact heading keyword.
    (docs / "design.md").write_text("# UserStories\nbody")
    secondary = secondary_signals(tmp_path)
    assert secondary_categories(secondary) >= 2
    assert classify([], secondary) is True


def test_heading_keyword_found_in_h2_after_h1_title(tmp_path: Path) -> None:
    # Regression: previously _heading_keyword_signals broke out of the line
    # loop after the FIRST `#` line regardless of match, so standard markdown
    # (H1 title + H2 section) was silently skipped.
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "spec.md").write_text("# Spec Document\n\n## FeatureList\n\nbody")
    secondary = secondary_signals(tmp_path)
    hits = [s for s in secondary if s.path == "docs/spec.md"]
    assert hits, "expected heading-keyword signal from H2 after H1"
    assert hits[0].kind == "feature-list"


def test_tooling_marker_in_claude_md_fires_third_category(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("Run /tkm:rebuild-spec on the repo.")
    secondary = secondary_signals(tmp_path)
    tooling_hit = [s for s in secondary if s.path.startswith("CLAUDE.md:")]
    assert tooling_hit, "expected tooling-marker signal from CLAUDE.md"


def test_plan_dir_signal_requires_phase_and_keyword_bar(tmp_path: Path) -> None:
    pd = tmp_path / "plans" / "260101-sample"
    pd.mkdir(parents=True)
    (pd / "phase-01.md").write_text("...")
    # Below the keyword bar: only 1 distinct -> NO signal.
    (pd / "plan.md").write_text("# Plan\nThis touches the FeatureList.")
    assert not [s for s in secondary_signals(tmp_path) if s.path.startswith("plans/")]

    # Above bar: 2 distinct keywords -> signal fires.
    (pd / "plan.md").write_text("# Plan\nTouches FeatureList and UserStories.")
    fired = [s for s in secondary_signals(tmp_path) if s.path.startswith("plans/")]
    assert fired


def test_specs_root_priority_specs_over_layered_docs(tmp_path: Path) -> None:
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "x.md").write_text("# x")
    (tmp_path / "docs" / "generated").mkdir(parents=True)
    (tmp_path / "docs" / "generated" / "y.md").write_text("# y")
    assert resolve_specs_root(tmp_path) == "specs/"


def test_primary_layered_docs_dir_fires(tmp_path: Path) -> None:
    # rebuild-spec v4.0.0 layered output → PRIMARY signal; specsRoot resolves to docs/.
    # layout-exempt: test for single-lang detection logic; per-lang root detection is deferred
    (tmp_path / "docs" / "system").mkdir(parents=True)
    (tmp_path / "docs" / "system" / "overview.md").write_text("# SystemOverview")
    hits = primary_signals(tmp_path)
    assert any(s.kind == "specs-dir" and s.path == "docs/system/" for s in hits)
    assert classify(hits, []) is True
    assert resolve_specs_root(tmp_path) == "docs/"


def test_specs_root_empty_when_no_signals(tmp_path: Path) -> None:
    assert resolve_specs_root(tmp_path) == ""


def test_prune_dirs_not_descended(tmp_path: Path) -> None:
    nm = tmp_path / "node_modules" / "specs"
    nm.mkdir(parents=True)
    (nm / "spec.md").write_text("# x")
    # No specs/ at root, only inside node_modules -> nothing.
    assert primary_signals(tmp_path) == []


# ---------------------------------------------------------------------------
# CLI-level tests
# ---------------------------------------------------------------------------

def test_cli_writes_valid_json_and_status_done(tmp_path: Path) -> None:
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "feature-list.md").write_text("# FeatureList")
    output = tmp_path / "out" / "sdd.json"

    res = _run(tmp_path, output)
    assert res.returncode == 0, res.stderr
    assert "Status: DONE" in res.stdout
    assert "done: step-1" in res.stdout

    payload = _read_json(output)
    assert payload["isSDD"] is True
    assert payload["specsRoot"] == "specs/"
    assert isinstance(payload["signals"], list) and payload["signals"]


def test_cli_idempotency_skips_when_output_exists(tmp_path: Path) -> None:
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "x.md").write_text("# x")
    output = tmp_path / "sdd.json"
    output.write_text('{"isSDD": false, "signals": [], "specsRoot": ""}')

    res = _run(tmp_path, output)
    assert res.returncode == 0
    assert "skip: step-1" in res.stdout
    # File unchanged.
    assert _read_json(output)["isSDD"] is False


def test_cli_writes_false_when_no_signals(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("nothing here")
    output = tmp_path / "sdd.json"

    res = _run(tmp_path, output)
    assert res.returncode == 0
    payload = _read_json(output)
    assert payload["isSDD"] is False
    assert payload["specsRoot"] == ""
    assert payload["signals"] == []


def test_signal_to_dict_shape() -> None:
    s = Signal(kind="specs-dir", path="specs/", weight=3)
    assert s.to_dict() == {"kind": "specs-dir", "path": "specs/", "weight": 3}


# ---------------------------------------------------------------------------
# --spec-folder override
# ---------------------------------------------------------------------------

def test_verify_spec_folder_success_md_file(tmp_path: Path) -> None:
    (tmp_path / "my-specs").mkdir()
    (tmp_path / "my-specs" / "feature-billing.md").write_text("# Billing")
    ok, reason = verify_spec_folder(tmp_path, "my-specs")
    assert ok and reason == ""


def test_verify_spec_folder_missing_dir(tmp_path: Path) -> None:
    ok, reason = verify_spec_folder(tmp_path, "nope")
    assert not ok
    assert "does not exist" in reason


def test_verify_spec_folder_no_md(tmp_path: Path) -> None:
    (tmp_path / "blank").mkdir()
    (tmp_path / "blank" / "config.toml").write_text("")
    ok, reason = verify_spec_folder(tmp_path, "blank")
    assert not ok
    assert "no in-repo .md" in reason


def test_verify_spec_folder_rejects_absolute_path(tmp_path: Path) -> None:
    ok, reason = verify_spec_folder(tmp_path, "/etc")
    assert not ok
    assert "relative" in reason


def test_verify_spec_folder_rejects_parent_traversal(tmp_path: Path) -> None:
    ok, reason = verify_spec_folder(tmp_path, "../etc")
    assert not ok
    assert ".." in reason


def test_verify_spec_folder_rejects_null_byte(tmp_path: Path) -> None:
    ok, reason = verify_spec_folder(tmp_path, "spec\x00s")
    assert not ok
    assert "null" in reason


def test_normalize_spec_folder_appends_slash() -> None:
    assert normalize_spec_folder("docs/specs") == "docs/specs/"
    assert normalize_spec_folder("docs/specs/") == "docs/specs/"
    assert normalize_spec_folder("docs\\specs") == "docs/specs/"


def test_cli_spec_folder_success_forces_sdd_true(tmp_path: Path) -> None:
    (tmp_path / "my-specs").mkdir()
    (tmp_path / "my-specs" / "feature.md").write_text("# Feature")
    output = tmp_path / "sdd.json"

    res = _run(tmp_path, output, "--spec-folder", "my-specs")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "done: step-1" in res.stdout
    assert "spec-folder: my-specs/ (verified" in res.stdout
    assert "Status: DONE" in res.stdout

    payload = _read_json(output)
    assert payload["isSDD"] is True
    assert payload["specsRoot"] == "my-specs/"
    assert payload["signals"] == [
        {"kind": "specs-dir", "path": "my-specs/", "weight": 3}
    ]


def test_cli_spec_folder_failure_blocks(tmp_path: Path) -> None:
    output = tmp_path / "sdd.json"

    res = _run(tmp_path, output, "--spec-folder", "missing")
    assert res.returncode == 2
    assert "Status: BLOCKED" in res.stdout
    assert "--spec-folder verification failed" in res.stdout
    # Must NOT write a fallback artifact on verification failure.
    assert not output.exists()


def test_cli_spec_folder_ignored_when_output_already_exists(tmp_path: Path) -> None:
    (tmp_path / "my-specs").mkdir()
    (tmp_path / "my-specs" / "x.md").write_text("# x")
    output = tmp_path / "sdd.json"
    output.write_text('{"isSDD": false, "signals": [], "specsRoot": ""}')

    res = _run(tmp_path, output, "--spec-folder", "my-specs")
    assert res.returncode == 0
    assert "skip: step-1" in res.stdout
    # Idempotency wins — existing JSON unchanged.
    assert _read_json(output)["isSDD"] is False


def test_cli_without_spec_folder_runs_detection(tmp_path: Path) -> None:
    # Sanity: existing detection path still works when --spec-folder is absent.
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "feature-list.md").write_text("# FeatureList")
    output = tmp_path / "sdd.json"

    res = _run(tmp_path, output)
    assert res.returncode == 0
    payload = _read_json(output)
    assert payload["isSDD"] is True
    assert "spec-folder:" not in res.stdout


def test_cli_spec_folder_empty_string_blocks(tmp_path: Path) -> None:
    # Regression: empty `--spec-folder ""` must BLOCK, not silently auto-detect.
    # Triggered by shell expansion of unset env vars (`--spec-folder "$SPEC_DIR"`).
    output = tmp_path / "sdd.json"

    res = _run(tmp_path, output, "--spec-folder", "")
    assert res.returncode == 2
    assert "Status: BLOCKED" in res.stdout
    assert "--spec-folder verification failed" in res.stdout
    assert not output.exists()


def test_verify_spec_folder_rejects_symlink_only_content(tmp_path: Path) -> None:
    # Regression: an empty in-repo spec dir whose only .md content lives behind
    # an internal symlink to an out-of-repo directory must NOT verify — otherwise
    # specsRoot points downstream subagents at out-of-tree files.
    external = tmp_path.parent / (tmp_path.name + "-external")
    external.mkdir()
    (external / "leak.md").write_text("# external")
    spec_dir = tmp_path / "my-specs"
    spec_dir.mkdir()
    (spec_dir / "linked").symlink_to(external)

    ok, reason = verify_spec_folder(tmp_path, "my-specs")
    assert not ok
    assert "no in-repo .md" in reason


def test_verify_spec_folder_accepts_in_repo_md_with_external_symlink_sibling(tmp_path: Path) -> None:
    # Companion to the above: a real in-repo .md still verifies even when an
    # unrelated external symlink also exists in the same dir.
    external = tmp_path.parent / (tmp_path.name + "-external2")
    external.mkdir()
    (external / "leak.md").write_text("# external")
    spec_dir = tmp_path / "my-specs"
    spec_dir.mkdir()
    (spec_dir / "real.md").write_text("# real")
    (spec_dir / "linked").symlink_to(external)

    ok, reason = verify_spec_folder(tmp_path, "my-specs")
    assert ok and reason == ""
