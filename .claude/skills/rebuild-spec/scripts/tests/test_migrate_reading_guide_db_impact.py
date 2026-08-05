# layout-exempt: rebuild-spec A3/B4 migration tests — docs paths are managed targets
"""Tests for migrate-reading-guide-db-impact.py (v26.0.0, acsim-learnings phase-03).

Covers: no-op when both families/headings already present, WARN print + exit 0 when
missing, missing-corpus non-destructive exit, and idempotency (never writes to disk).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

_spec = importlib.util.spec_from_file_location(
    "migrate_reading_guide_db_impact", SCRIPTS / "migrate-reading-guide-db-impact.py")
mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mig)

_TECH_MIGRATED = "## Source Walkthrough\n\nreal content\n\n## DB Impact per Event\n\nN/A\n"
_SCREEN_MIGRATED = "## Source Walkthrough\n\nreal content\n"


def _make_corpus(tmp_path: Path, tech_body: str, screen_body: str) -> Path:
    docs = tmp_path / "docs"
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "technical-spec.md").write_text(tech_body, encoding="utf-8")
    scr = docs / "screens" / "SCR001_Login"
    scr.mkdir(parents=True)
    (scr / "spec.md").write_text(screen_body, encoding="utf-8")
    return docs


class TestNoOp:
    def test_fully_migrated_corpus_is_no_op(self, tmp_path, capsys):
        docs = _make_corpus(tmp_path, _TECH_MIGRATED, _SCREEN_MIGRATED)
        rc = mig.migrate(docs)
        out = capsys.readouterr().out
        assert rc == 0
        assert "already migrated" in out

    def test_no_op_does_not_modify_files(self, tmp_path):
        docs = _make_corpus(tmp_path, _TECH_MIGRATED, _SCREEN_MIGRATED)
        tech = docs / "features" / "F001_Login" / "technical-spec.md"
        before = tech.read_text(encoding="utf-8")
        mig.migrate(docs)
        assert tech.read_text(encoding="utf-8") == before


class TestUnmigrated:
    def test_missing_technical_spec_sections_warn(self, tmp_path, capsys):
        docs = _make_corpus(tmp_path, "## Overview\n\nx\n", _SCREEN_MIGRATED)
        rc = mig.migrate(docs)
        out = capsys.readouterr().out
        assert rc == 0
        assert "missing" in out
        assert "Source Walkthrough" in out
        assert "DB Impact per Event" in out

    def test_missing_screen_spec_section_warn(self, tmp_path, capsys):
        docs = _make_corpus(tmp_path, _TECH_MIGRATED, "## Purpose\n\nx\n")
        rc = mig.migrate(docs)
        out = capsys.readouterr().out
        assert rc == 0
        assert "missing" in out

    def test_never_writes_to_disk(self, tmp_path):
        docs = _make_corpus(tmp_path, "## Overview\n\nx\n", "## Purpose\n\nx\n")
        tech = docs / "features" / "F001_Login" / "technical-spec.md"
        before = tech.read_text(encoding="utf-8")
        mig.migrate(docs)
        assert tech.read_text(encoding="utf-8") == before

    def test_idempotent_second_run_same_result(self, tmp_path, capsys):
        docs = _make_corpus(tmp_path, "## Overview\n\nx\n", "## Purpose\n\nx\n")
        mig.migrate(docs)
        out1 = capsys.readouterr().out
        rc2 = mig.migrate(docs)
        out2 = capsys.readouterr().out
        assert rc2 == 0
        assert out1 == out2


class TestMissingCorpus:
    def test_empty_docs_root_exits_zero_no_changes(self, tmp_path, capsys):
        docs = tmp_path / "docs"
        docs.mkdir()
        rc = mig.migrate(docs)
        out = capsys.readouterr().out
        assert rc == 0
        assert "no changes made" in out


class TestUnreadableFile:
    """v26.0.0 rework regression: 'exit 0 always' must hold even when a spec file is
    unreadable (reviewer chmod-000'd one and got an uncaught PermissionError, exit 1)."""

    def test_unreadable_spec_warns_and_exits_zero(self, tmp_path, capsys):
        import os
        import pytest as _pytest
        if os.geteuid() == 0:
            _pytest.skip("root reads chmod-000 files; permission case unreproducible")
        docs = _make_corpus(tmp_path, "## Overview\n\nx\n", _SCREEN_MIGRATED)
        tech = docs / "features" / "F001_Login" / "technical-spec.md"
        tech.chmod(0o000)
        try:
            rc = mig.migrate(docs)
        finally:
            tech.chmod(0o644)
        out_err = capsys.readouterr()
        assert rc == 0
        assert "unreadable, skipping" in out_err.out

    def test_unreadable_spec_reported_in_its_own_summary_category(self, tmp_path, capsys):
        """Minor fix: an unreadable spec must be tallied under its own `unreadable`
        category in the summary line, not silently dropped from the missing tally
        (previously indistinguishable from an already-compliant spec)."""
        import os
        import pytest as _pytest
        if os.geteuid() == 0:
            _pytest.skip("root reads chmod-000 files; permission case unreproducible")
        docs = _make_corpus(tmp_path, _TECH_MIGRATED, _SCREEN_MIGRATED)
        tech = docs / "features" / "F001_Login" / "technical-spec.md"
        tech.chmod(0o000)
        try:
            rc = mig.migrate(docs)
        finally:
            tech.chmod(0o644)
        out = capsys.readouterr().out
        assert rc == 0
        assert "1 unreadable" in out
        # The exit-0 "already migrated" branch must NOT fire when a file was skipped
        # unread — that would falsely claim full compliance.
        assert "already migrated" not in out
