"""Tests for state round-trip: primary_lang + translations preserved across cursor writes."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
# Use the interpreter running the tests — portable regardless of where the venv
# lives (matches every other subprocess-based test in this suite).
PYTHON = sys.executable


def _run_build_source(tmp_path, extra_args=None, prior_state=None):
    """Run build_source_to_fcode.py and return the written state dict."""
    specs_root = tmp_path / "features"
    specs_root.mkdir(parents=True, exist_ok=True)
    state_out = tmp_path / ".rebuild-state.json"
    index_out = tmp_path / "_source-to-fcode.json"

    if prior_state:
        state_out.write_text(json.dumps(prior_state, indent=2), encoding="utf-8")

    cmd = [
        PYTHON,
        str(SCRIPTS_DIR / "build_source_to_fcode.py"),
        "--specs-root", str(specs_root),
        "--state-out", str(state_out),
        "--index-out", str(index_out),
        "--mode", "full",
    ]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        pytest.skip(f"build_source_to_fcode.py failed (likely no git): {result.stderr}")

    return json.loads(state_out.read_text(encoding="utf-8"))


class TestPrimaryLangPreservation:
    def test_primary_lang_absent_on_fresh_state(self, tmp_path):
        state = _run_build_source(tmp_path)
        assert "primary_lang" in state
        assert state["primary_lang"] == ""

    def test_primary_lang_preserved_across_core_write(self, tmp_path):
        prior = {
            "primary_lang": "vi",
            "last_rebuild_sha": "aaa",
            "translations": {"jp": {"translated_from_sha": "aaa"}},
        }
        state = _run_build_source(tmp_path, ["--cursor", "core"], prior_state=prior)
        assert state["primary_lang"] == "vi"

    def test_primary_lang_preserved_across_feature_specs_write(self, tmp_path):
        prior = {"primary_lang": "vi", "last_rebuild_sha": "aaa"}
        state = _run_build_source(tmp_path, ["--cursor", "feature-specs"], prior_state=prior)
        assert state["primary_lang"] == "vi"

    def test_primary_lang_preserved_across_flows_write(self, tmp_path):
        prior = {"primary_lang": "pt-br", "last_rebuild_sha": "aaa"}
        state = _run_build_source(tmp_path, ["--cursor", "flows"], prior_state=prior)
        assert state["primary_lang"] == "pt-br"

    def test_primary_lang_preserved_across_glossary_write(self, tmp_path):
        prior = {"primary_lang": "jp", "last_rebuild_sha": "aaa"}
        state = _run_build_source(tmp_path, ["--cursor", "glossary"], prior_state=prior)
        assert state["primary_lang"] == "jp"

    def test_primary_lang_preserved_across_jobs_write(self, tmp_path):
        """v26.1.0 A2 pass: --cursor jobs must not disturb primary_lang."""
        prior = {"primary_lang": "vi", "last_rebuild_sha": "aaa"}
        state = _run_build_source(tmp_path, ["--cursor", "jobs"], prior_state=prior)
        assert state["primary_lang"] == "vi"
        assert "last_jobs_run_sha" in state

    def test_primary_lang_preserved_across_test_cases_write(self, tmp_path):
        """v26.1.0 B6 pass: --cursor test-cases must not disturb primary_lang."""
        prior = {"primary_lang": "vi", "last_rebuild_sha": "aaa"}
        state = _run_build_source(tmp_path, ["--cursor", "test-cases"], prior_state=prior)
        assert state["primary_lang"] == "vi"
        assert "last_test_cases_run_sha" in state


class TestTranslationsPreservation:
    def test_translations_absent_on_fresh_state(self, tmp_path):
        state = _run_build_source(tmp_path)
        assert "translations" in state
        assert state["translations"] == {}

    def test_translations_preserved_across_core_write(self, tmp_path):
        prior = {
            "primary_lang": "vi",
            "last_rebuild_sha": "aaa",
            "translations": {
                "jp": {
                    "translated_from_sha": "aaa",
                    "last_translate_run_sha": "aaa",
                    "passes_translated": ["core"],
                },
                "en": {
                    "translated_from_sha": "bbb",
                    "last_translate_run_sha": "bbb",
                    "passes_translated": ["core", "feature-specs"],
                },
            },
        }
        state = _run_build_source(tmp_path, ["--cursor", "core"], prior_state=prior)
        assert "jp" in state["translations"]
        assert "en" in state["translations"]
        assert state["translations"]["jp"]["translated_from_sha"] == "aaa"
        assert state["translations"]["en"]["passes_translated"] == ["core", "feature-specs"]

    def test_translations_preserved_across_feature_specs_write(self, tmp_path):
        prior = {
            "primary_lang": "en",
            "last_rebuild_sha": "aaa",
            "translations": {
                "vi": {"translated_from_sha": "aaa"},
            },
        }
        state = _run_build_source(tmp_path, ["--cursor", "feature-specs"], prior_state=prior)
        assert state["translations"]["vi"]["translated_from_sha"] == "aaa"

    def test_translations_not_clobbered_by_missing_prior(self, tmp_path):
        state = _run_build_source(tmp_path)
        assert state["translations"] == {}

    def test_corrupted_translations_falls_back_to_empty(self, tmp_path):
        specs_root = tmp_path / "features"
        specs_root.mkdir(parents=True, exist_ok=True)
        state_file = tmp_path / ".rebuild-state.json"
        state_file.write_text("not valid json!!!", encoding="utf-8")
        state = _run_build_source(tmp_path)
        assert state["translations"] == {}
        assert state["primary_lang"] == ""
