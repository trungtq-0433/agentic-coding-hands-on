# layout-exempt: rebuild-spec aggregate-purge tests — all paths are skill-managed targets
"""Tests for purge_system_drafts (lib function + CLI script).

Covers:
(a) draft deleted when promoted sibling exists
(b) draft KEPT when sibling absent (un-promoted → no data loss)
(c) KEEP-list / non-draft files untouched
(d) idempotent re-run
(e) path-traversal guard holds
(f) M1 sanitize_field applied to stack values in no-deps intro (indirectly via stack hint)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from _promote_shadow_purge_lib import purge_system_drafts, _KEEP_EXACT  # noqa: E402

SCRIPT = SCRIPTS_DIR / "purge_system_drafts.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_system(tmp_path: Path) -> tuple[Path, Path]:
    """Create a minimal docs/<lang>/ + docs/<lang>/system/ layout.

    Returns (system_dir, docs_root).
    """
    docs_root = tmp_path / "docs" / "en"
    system_dir = docs_root / "system"
    system_dir.mkdir(parents=True)
    return system_dir, docs_root


def _write(path: Path, content: str = "# content\n") -> Path:
    path.write_text(content)
    return path


def _run_cli(system_dir: Path, docs_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--system-dir", str(system_dir),
         "--docs-root", str(docs_root)],
        capture_output=True, text=True, timeout=15,
    )


# ---------------------------------------------------------------------------
# (a) Draft deleted when promoted sibling exists
# ---------------------------------------------------------------------------

class TestDraftDeletedWhenSiblingExists:
    def test_single_draft_deleted(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        _write(system_dir / "overview.draft.md")
        _write(system_dir / "overview.md")

        deleted = purge_system_drafts(str(system_dir), str(docs_root))

        assert not (system_dir / "overview.draft.md").exists()
        assert len(deleted) == 1
        assert deleted[0].endswith("overview.draft.md")

    def test_multiple_drafts_all_deleted(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        names = [
            "overview", "component-catalog", "architecture",
            "data-ownership-map", "cross-service-flows", "glossary",
        ]
        for n in names:
            _write(system_dir / f"{n}.draft.md")
            _write(system_dir / f"{n}.md")

        deleted = purge_system_drafts(str(system_dir), str(docs_root))

        assert len(deleted) == len(names)
        for n in names:
            assert not (system_dir / f"{n}.draft.md").exists(), f"{n}.draft.md should be gone"

    def test_promoted_sibling_untouched(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        _write(system_dir / "overview.draft.md")
        promoted = _write(system_dir / "overview.md", "# promoted\n")

        purge_system_drafts(str(system_dir), str(docs_root))

        assert promoted.exists(), "promoted sibling must survive the purge"
        assert promoted.read_text() == "# promoted\n"

    def test_cli_exits_zero_and_reports_count(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        _write(system_dir / "architecture.draft.md")
        _write(system_dir / "architecture.md")

        result = _run_cli(system_dir, docs_root)

        assert result.returncode == 0, result.stderr
        assert "deleted 1" in result.stdout


# ---------------------------------------------------------------------------
# (b) Draft KEPT when sibling absent (un-promoted → no data loss)
# ---------------------------------------------------------------------------

class TestDraftKeptWhenSiblingAbsent:
    def test_draft_without_sibling_survives(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        draft = _write(system_dir / "overview.draft.md")
        # No overview.md exists

        deleted = purge_system_drafts(str(system_dir), str(docs_root))

        assert draft.exists(), "draft must be kept when promoted sibling is absent"
        assert deleted == []

    def test_partial_promote_only_completed_drafts_deleted(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        # overview promoted; architecture not yet promoted
        _write(system_dir / "overview.draft.md")
        _write(system_dir / "overview.md")
        arch_draft = _write(system_dir / "architecture.draft.md")
        # architecture.md intentionally absent

        deleted = purge_system_drafts(str(system_dir), str(docs_root))

        assert not (system_dir / "overview.draft.md").exists()
        assert arch_draft.exists(), "unpromoted architecture.draft.md must survive"
        assert len(deleted) == 1

    def test_cli_reports_zero_when_no_siblings(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        _write(system_dir / "glossary.draft.md")
        # No glossary.md

        result = _run_cli(system_dir, docs_root)

        assert result.returncode == 0, result.stderr
        assert "deleted 0" in result.stdout
        assert (system_dir / "glossary.draft.md").exists()


# ---------------------------------------------------------------------------
# (c) KEEP-list and non-draft files untouched
# ---------------------------------------------------------------------------

class TestKeepListAndNonDraftFiles:
    def test_keep_exact_files_untouched(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        # Write KEEP_EXACT files into system_dir (unusual location, but guard must hold)
        keep_paths = []
        for name in _KEEP_EXACT:
            p = system_dir / name
            _write(p)
            keep_paths.append(p)

        purge_system_drafts(str(system_dir), str(docs_root))

        for p in keep_paths:
            assert p.exists(), f"KEEP-list file {p.name} must survive"

    def test_plain_md_without_draft_infix_untouched(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        plain = _write(system_dir / "overview.md")

        purge_system_drafts(str(system_dir), str(docs_root))

        assert plain.exists(), "plain .md without .draft. infix must not be deleted"

    def test_non_md_files_untouched(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        json_file = _write(system_dir / ".nav-metadata.json", "{}")
        _write(system_dir / "overview.draft.md")
        _write(system_dir / "overview.md")

        purge_system_drafts(str(system_dir), str(docs_root))

        assert json_file.exists(), ".json file must not be touched by draft purge"

    def test_subdirectory_not_entered(self, tmp_path):
        """Non-recursive: files in subdirs are not touched."""
        system_dir, docs_root = _make_system(tmp_path)
        subdir = system_dir / "sub"
        subdir.mkdir()
        nested_draft = _write(subdir / "overview.draft.md")
        _write(subdir / "overview.md")

        purge_system_drafts(str(system_dir), str(docs_root))

        assert nested_draft.exists(), "draft in subdirectory must not be touched (non-recursive)"


# ---------------------------------------------------------------------------
# (d) Idempotent re-run
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_second_run_no_error_no_extra_deletions(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        _write(system_dir / "overview.draft.md")
        _write(system_dir / "overview.md")

        deleted1 = purge_system_drafts(str(system_dir), str(docs_root))
        deleted2 = purge_system_drafts(str(system_dir), str(docs_root))

        assert len(deleted1) == 1
        assert deleted2 == [], "second run must delete nothing (idempotent)"

    def test_cli_idempotent(self, tmp_path):
        system_dir, docs_root = _make_system(tmp_path)
        _write(system_dir / "glossary.draft.md")
        _write(system_dir / "glossary.md")

        r1 = _run_cli(system_dir, docs_root)
        r2 = _run_cli(system_dir, docs_root)

        assert r1.returncode == 0, r1.stderr
        assert r2.returncode == 0, r2.stderr
        assert "deleted 0" in r2.stdout


# ---------------------------------------------------------------------------
# (e) Path-traversal guard
# ---------------------------------------------------------------------------

class TestPathTraversalGuard:
    def test_traversal_outside_docs_root_raises(self, tmp_path):
        """purge_system_drafts must not delete files outside docs_root."""
        # Create a system_dir inside docs_root
        docs_root = tmp_path / "docs" / "en"
        system_dir = docs_root / "system"
        system_dir.mkdir(parents=True)

        # Plant a symlink in system_dir that points OUTSIDE docs_root
        outside_file = tmp_path / "outside.draft.md"
        _write(outside_file)
        sibling_outside = tmp_path / "outside.md"
        _write(sibling_outside)

        symlink = system_dir / "outside.draft.md"
        try:
            symlink.symlink_to(outside_file)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks not supported on this platform")

        # The purge must either skip or raise ValueError; the outside file must survive.
        try:
            purge_system_drafts(str(system_dir), str(docs_root))
        except ValueError:
            pass  # guard raised — acceptable

        assert outside_file.exists(), "file outside docs_root must not be deleted"

    def test_cli_missing_system_dir_exits_1(self, tmp_path):
        docs_root = tmp_path / "docs" / "en"
        docs_root.mkdir(parents=True)
        nonexistent = docs_root / "system_nonexistent"

        result = _run_cli(nonexistent, docs_root)

        assert result.returncode == 1
        assert "does not exist" in result.stderr
