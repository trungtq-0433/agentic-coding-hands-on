"""Tests for build_source_to_fcode.py — reverse-index + state emitter."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from build_source_to_fcode import (
    _compute_doc_shas,
    _normalize_path,
    _parse_citations,
    build_index,
)

FIXTURES_DIR = _TESTS_DIR / "fixtures"
INCREMENTAL_FIXTURES = FIXTURES_DIR / "incremental"


class TestParseCitations:
    def test_inline_source(self):
        text = "**Source:** `api/foo.php:10-20`\nsome text"
        assert "api/foo.php:10-20" in _parse_citations(text)

    def test_table_form_in_section(self):
        text = (
            "## Source Code References\n"
            "| File | Lines |\n"
            "| `web/src/Login.vue` | all |\n"
            "## Next Section\n"
        )
        assert "web/src/Login.vue" in _parse_citations(text)

    def test_citations_outside_section_ignored(self):
        text = (
            "## Other Section\n"
            "| `should/not/match.php` | x |\n"
            "## Source Code References\n"
            "| `inside/section.ts` | y |\n"
            "## End\n"
        )
        paths = _parse_citations(text)
        assert "inside/section.ts" in paths
        assert "should/not/match.php" not in paths

    def test_line_suffix_present(self):
        text = "**Source:** `api/bar.php:44-58`"
        paths = _parse_citations(text)
        assert "api/bar.php:44-58" in paths


class TestNormalizePath:
    def test_strip_line_suffix(self):
        assert _normalize_path("api/foo.php:44-58") == "api/foo.php"

    def test_strip_leading_dot_slash(self):
        assert _normalize_path("./src/index.ts") == "src/index.ts"

    def test_forward_slash_only(self):
        assert "/" not in _normalize_path("api/foo.php") or _normalize_path("api/foo.php") == "api/foo.php"


class TestBuildIndex:
    def test_builds_from_fixture_specs(self):
        specs_root = INCREMENTAL_FIXTURES / "synthetic-specs"
        index = build_index(specs_root)
        assert "api/app/Http/Controllers/AuthController.php" in index
        assert "F001" in index["api/app/Http/Controllers/AuthController.php"]

    def test_empty_dir_returns_empty(self, tmp_path):
        assert build_index(tmp_path) == {}

    def test_multiple_fcodes_sorted(self):
        specs_root = INCREMENTAL_FIXTURES / "synthetic-specs"
        index = build_index(specs_root)
        for fcodes in index.values():
            assert fcodes == sorted(fcodes)


class TestComputeDocShas:
    def test_computes_sha_for_layered_artifacts(self, tmp_path):
        # v4 layered layout: route-list.md lives at generated/route-list.md
        (tmp_path / "generated").mkdir()
        (tmp_path / "generated" / "route-list.md").write_text("hello")
        # data-model.md lives at generated/entities.md (renamed in v4)
        (tmp_path / "generated" / "entities.md").write_text("world")
        shas = _compute_doc_shas(tmp_path)
        assert "route-list.md" in shas
        assert "data-model.md" in shas
        assert shas["route-list.md"] == hashlib.sha256(b"hello").hexdigest()
        assert shas["data-model.md"] == hashlib.sha256(b"world").hexdigest()

    def test_system_layer_artifacts(self, tmp_path):
        (tmp_path / "system").mkdir()
        (tmp_path / "system" / "permissions.md").write_text("perms")
        (tmp_path / "system" / "business-rules.md").write_text("rules")
        shas = _compute_doc_shas(tmp_path)
        assert "permissions.md" in shas
        assert "business-rules.md" in shas

    def test_missing_artifact_excluded(self, tmp_path):
        # No files at all → empty dict
        assert _compute_doc_shas(tmp_path) == {}

    def test_excludes_state_json(self, tmp_path):
        (tmp_path / "state.json").write_text("{}")
        shas = _compute_doc_shas(tmp_path)
        assert "state.json" not in shas

    def test_empty_dir(self, tmp_path):
        assert _compute_doc_shas(tmp_path) == {}

    def test_nonexistent_dir(self, tmp_path):
        assert _compute_doc_shas(tmp_path / "nope") == {}
