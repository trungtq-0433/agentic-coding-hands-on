"""Tests for locate_synthesis_artifacts.py — the Phase-01 doc-locator."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import locate_synthesis_artifacts as loc  # noqa: E402


def _mk_single_lang(tmp_path: Path) -> Path:
    """Build a single-lang (en) docs tree with user-stories + feature-list."""
    docs = tmp_path / "docs"
    (docs / "generated").mkdir(parents=True)
    (docs / "system").mkdir(parents=True)
    (docs / "generated" / "user-stories.md").write_text("# US", encoding="utf-8")
    (docs / "generated" / "feature-list.md").write_text("# FL", encoding="utf-8")
    (docs / "system" / "glossary.md").write_text("# G", encoding="utf-8")
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "technical-spec.md").write_text("# spec", encoding="utf-8")
    return tmp_path


def _mk_multi_lang(tmp_path: Path) -> Path:
    """Build a per-lang tree: primary vi, docs under docs/vi/."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / ".rebuild-state.json").write_text(
        json.dumps({"primary_lang": "vi", "translations": {"en": {}}}), encoding="utf-8")
    vi = docs / "vi"
    (vi / "generated").mkdir(parents=True)
    (vi / "generated" / "user-stories.md").write_text("# US vi", encoding="utf-8")
    return tmp_path


class TestSingleLang:
    def test_user_stories_present(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "user-stories", None, None)
        us = [a for a in res["artifacts"] if a["kind"] == "user-stories"]
        assert len(us) == 1 and us[0]["present"] is True

    def test_feature_specs_globbed(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "feature-list", None, None)
        specs = [a for a in res["artifacts"] if a["kind"] == "feature-spec"]
        assert any(a["present"] for a in specs)

    def test_all_scope_includes_system(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "all", None, None)
        kinds = {a["kind"] for a in res["artifacts"]}
        assert {"user-stories", "feature-list", "glossary"} <= kinds

    def test_absent_artifact_recorded_not_error(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "system", None, None)
        entities = [a for a in res["artifacts"] if a["kind"] == "entities"]
        assert entities and entities[0]["present"] is False


class TestMultiLang:
    def test_docs_root_resolves_to_primary(self, tmp_path):
        root = _mk_multi_lang(tmp_path)
        res = loc.locate(root, "user-stories", None, None)
        assert res["docs_root"].endswith("/docs/vi")
        us = [a for a in res["artifacts"] if a["kind"] == "user-stories"]
        assert us[0]["present"] is True


class TestDesignIntent:
    def test_promoted_wins(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        di = root / "docs" / "system" / "design-intent.md"
        di.write_text("# DI", encoding="utf-8")
        res = loc.locate(root, "design-intent", None, None)
        e = [a for a in res["artifacts"] if a["kind"] == "design-intent"][0]
        assert e["present"] is True and e["tier"] == "system"

    def test_explicit_plan_dir(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        pd = root / "plans" / "260721-1043-foo" / "artifacts"
        pd.mkdir(parents=True)
        (pd / "design-intent.md").write_text("# DI", encoding="utf-8")
        res = loc.locate(root, "design-intent", None, "plans/260721-1043-foo")
        e = [a for a in res["artifacts"] if a["kind"] == "design-intent"][0]
        assert e["present"] is True and e["tier"] == "plan"

    def test_single_candidate_used(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        pd = root / "plans" / "260721-1043-foo" / "artifacts"
        pd.mkdir(parents=True)
        (pd / "design-intent.md").write_text("# DI", encoding="utf-8")
        res = loc.locate(root, "design-intent", None, None)
        assert res["ambiguities"] == []
        e = [a for a in res["artifacts"] if a["kind"] == "design-intent"][0]
        assert e["present"] is True

    def test_multiple_candidates_refuse(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        for slug in ("260721-1000-a", "260721-1100-b"):
            pd = root / "plans" / slug / "artifacts"
            pd.mkdir(parents=True)
            (pd / "design-intent.md").write_text("# DI", encoding="utf-8")
        res = loc.locate(root, "design-intent", None, None)
        assert len(res["ambiguities"]) == 1
        e = [a for a in res["artifacts"] if a["kind"] == "design-intent"][0]
        assert e["present"] is False and "ambiguous" in e.get("note", "")

    def test_absent_is_normal(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "design-intent", None, None)
        assert res["ambiguities"] == []
        e = [a for a in res["artifacts"] if a["kind"] == "design-intent"][0]
        assert e["present"] is False
