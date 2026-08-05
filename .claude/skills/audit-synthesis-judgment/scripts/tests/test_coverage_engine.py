"""Tests for Engine 1 — graph-state, orphan, phantom, redundancy, and the coverage_engine e2e."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import _graph_state_lib as gs  # noqa: E402
import _coverage_orphan_lib as orphan_lib  # noqa: E402
import _coverage_phantom_lib as phantom_lib  # noqa: E402
import _redundancy_lib as redundancy_lib  # noqa: E402
import coverage_engine  # noqa: E402


# --------------------------------------------------------------------------- graph-state
def _write_graph(path: Path, nodes: list[dict], extra: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"nodes": nodes}
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestGraphState:
    def test_absent(self, tmp_path):
        res = gs.classify(tmp_path / "nope.json", tmp_path)
        assert res["status"] == gs.STATUS_ABSENT and res["coverage_status"] == "UNVERIFIABLE"

    def test_empty(self, tmp_path):
        g = tmp_path / "graph.json"
        _write_graph(g, [])
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_EMPTY and res["coverage_status"] == "UNVERIFIABLE"

    def test_malformed_graph_json_is_absent_not_crash(self, tmp_path):
        g = tmp_path / "graph.json"
        g.write_text("{not valid json", encoding="utf-8")
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_ABSENT and res["coverage_status"] == "UNVERIFIABLE"

    def test_graph_without_nodes_key_is_empty(self, tmp_path):
        g = tmp_path / "graph.json"
        g.write_text('{"meta": {}}', encoding="utf-8")  # no "nodes"
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_EMPTY

    def test_ok_all_langs_represented(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("x=1", encoding="utf-8")
        g = tmp_path / "graph.json"
        _write_graph(g, [{"label": "A", "source_file": "src/a.py"}])
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_OK and res["coverage_status"] == "OK"

    def test_partial_graphable_language_missing(self, tmp_path):
        # A GRAPHABLE repo language (javascript) with no graph nodes → PARTIAL.
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("x=1", encoding="utf-8")
        (tmp_path / "src" / "b.js").write_text("var x=1", encoding="utf-8")
        g = tmp_path / "graph.json"
        _write_graph(g, [{"label": "A", "source_file": "src/a.py"}])  # javascript absent
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_PARTIAL
        assert "javascript" in res["unverifiable_languages"]

    def test_nongraphable_language_not_partial(self, tmp_path):
        # A JS/TS app with a migrations/*.sql folder must NOT go PARTIAL — SQL is non-graphable.
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("x=1", encoding="utf-8")
        (tmp_path / "migrations").mkdir()
        (tmp_path / "migrations" / "001.sql").write_text("SELECT 1;", encoding="utf-8")
        g = tmp_path / "graph.json"
        _write_graph(g, [{"label": "A", "source_file": "src/a.py"}])
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_OK and res["coverage_status"] == "OK"
        # SQL is still surfaced as unverifiable (graphify can't index it) — but not a PARTIAL defect.
        assert "plsql" in res["unverifiable_languages"]

    def test_stale_when_commit_differs(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "--allow-empty", "-qm", "init"], cwd=tmp_path, check=True)
        (tmp_path / "a.py").write_text("x=1", encoding="utf-8")
        g = tmp_path / "graph.json"
        _write_graph(g, [{"label": "A", "source_file": "a.py"}], extra={"commit": "deadbeefcafe"})
        res = gs.classify(g, tmp_path)
        assert res["status"] == gs.STATUS_STALE and res["coverage_status"] == "UNVERIFIABLE"


# --------------------------------------------------------------------------- orphans
class TestOrphans:
    def test_planted_orphan_found(self, tmp_path):
        nodes = [{"label": "Widget", "source_file": "src/widget.py"}]
        index = {"index": {"src/other.py": ["F001"]}}
        res = orphan_lib.find_orphans(nodes, index, [], tmp_path, set(), features_dir_present=True)
        assert res["status"] == "OK"
        assert len(res["orphans"]) == 1 and res["orphans"][0]["source_file"] == "src/widget.py"

    def test_empty_index_no_features_is_unverifiable(self, tmp_path):
        nodes = [{"label": "Widget", "source_file": "src/widget.py"}]
        res = orphan_lib.find_orphans(nodes, {"index": {}}, [], tmp_path, set(), features_dir_present=False)
        assert res["status"] == "UNVERIFIABLE" and res["orphans"] == []

    def test_private_symbol_filtered(self, tmp_path):
        nodes = [{"label": "_helper", "source_file": "src/widget.py"}]
        res = orphan_lib.find_orphans(nodes, {"index": {}}, [], tmp_path, set(), features_dir_present=True)
        assert res["orphans"] == []
        assert any(f["symbol"] == "_helper" for f in res["filtered"])

    def test_test_path_filtered(self, tmp_path):
        nodes = [{"label": "TestWidget", "source_file": "tests/test_widget.py"}]
        res = orphan_lib.find_orphans(nodes, {"index": {}}, [], tmp_path, set(), features_dir_present=True)
        assert res["orphans"] == []

    def test_doc_mention_exempts(self, tmp_path):
        nodes = [{"label": "Widget", "source_file": "src/widget.py"}]
        res = orphan_lib.find_orphans(nodes, {"index": {}}, ["see src/widget.py for details"],
                                      tmp_path, set(), features_dir_present=True)
        assert res["orphans"] == []

    def test_partial_language_skipped(self, tmp_path):
        nodes = [{"label": "Proc", "source_file": "src/legacy.cbl"}]
        res = orphan_lib.find_orphans(nodes, {"index": {}}, [], tmp_path, {"cobol"}, features_dir_present=True)
        assert res["orphans"] == []


# --------------------------------------------------------------------------- phantoms
class TestPhantoms:
    def _artifact(self, tmp_path, text: str) -> list[dict]:
        f = tmp_path / "user-stories.md"
        f.write_text(text, encoding="utf-8")
        return [{"path": str(f), "kind": "user-stories", "present": True}]

    def test_phantom_on_complete_graph(self, tmp_path):
        arts = self._artifact(tmp_path, "**Source:** `src/ghost.py:10-20`")
        nodes = [{"label": "Real", "source_file": "src/real.py"}]
        res = phantom_lib.find_phantoms(arts, nodes, tmp_path, "OK", set())
        assert len(res["phantoms"]) == 1 and res["phantoms"][0]["source_file"] == "src/ghost.py"

    def test_resolvable_not_phantom(self, tmp_path):
        arts = self._artifact(tmp_path, "**Source:** `src/real.py:10-20`")
        nodes = [{"label": "Real", "source_file": "src/real.py"}]
        res = phantom_lib.find_phantoms(arts, nodes, tmp_path, "OK", set())
        assert res["phantoms"] == []

    def test_unverifiable_on_partial_language(self, tmp_path):
        arts = self._artifact(tmp_path, "**Source:** `src/legacy.cbl:10-20`")
        nodes = [{"label": "Real", "source_file": "src/real.py"}]
        res = phantom_lib.find_phantoms(arts, nodes, tmp_path, "PARTIAL", {"cobol"})
        assert res["phantoms"] == []
        assert len(res["unverifiable"]) == 1

    def test_absent_graph_all_unverifiable(self, tmp_path):
        arts = self._artifact(tmp_path, "**Source:** `src/ghost.py:10-20`")
        res = phantom_lib.find_phantoms(arts, [], tmp_path, "ABSENT", set())
        assert res["phantoms"] == [] and len(res["unverifiable"]) == 1


# --------------------------------------------------------------------------- redundancy
class TestRedundancy:
    def test_literal_duplicate_flagged(self, tmp_path):
        body = "# Feature X\n" + ("Detailed prose about the feature. " * 20)
        a = tmp_path / "a.md"; b = tmp_path / "b.md"
        a.write_text(body, encoding="utf-8"); b.write_text(body, encoding="utf-8")
        arts = [{"path": str(a), "kind": "feature-spec", "present": True},
                {"path": str(b), "kind": "feature-spec", "present": True}]
        res = redundancy_lib.find_duplicate_artifacts(arts)
        assert len(res["duplicates"]) == 1 and len(res["duplicates"][0]["paths"]) == 2

    def test_stub_below_threshold_exempt(self, tmp_path):
        a = tmp_path / "a.md"; b = tmp_path / "b.md"
        a.write_text("# stub", encoding="utf-8"); b.write_text("# stub", encoding="utf-8")
        arts = [{"path": str(a), "kind": "x", "present": True},
                {"path": str(b), "kind": "x", "present": True}]
        res = redundancy_lib.find_duplicate_artifacts(arts)
        assert res["duplicates"] == [] and len(res["exempted"]) == 2

    def test_distinct_content_not_flagged(self, tmp_path):
        a = tmp_path / "a.md"; b = tmp_path / "b.md"
        a.write_text("# A\n" + ("alpha " * 60), encoding="utf-8")
        b.write_text("# B\n" + ("beta " * 60), encoding="utf-8")
        arts = [{"path": str(a), "kind": "x", "present": True},
                {"path": str(b), "kind": "x", "present": True}]
        res = redundancy_lib.find_duplicate_artifacts(arts)
        assert res["duplicates"] == []


# --------------------------------------------------------------------------- coverage_engine e2e
class TestCoverageEngineE2E:
    def _corpus(self, tmp_path, *, complete_graph=True, empty_index=False):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "features" / "F001_X").mkdir(parents=True)
        (docs / "features" / "F001_X" / "technical-spec.md").write_text(
            "# F001\n\n**Source:** `src/ghost.py:5-9`\n", encoding="utf-8")
        (docs / "generated" / "user-stories.md").write_text("# US", encoding="utf-8")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "widget.py").write_text("class Widget: pass", encoding="utf-8")
        (tmp_path / "src" / "cited.py").write_text("x=1", encoding="utf-8")
        nodes = [{"label": "Widget", "source_file": "src/widget.py"},
                 {"label": "Cited", "source_file": "src/cited.py"}]
        g = tmp_path / "graphify-out" / "graph.json"
        _write_graph(g, nodes if complete_graph else [])
        index = {} if empty_index else {"src/cited.py": ["F001"]}
        (docs / "_source-to-fcode.json").write_text(
            json.dumps({"index": index}), encoding="utf-8")
        return tmp_path, g

    def test_planted_orphan_and_phantom_found(self, tmp_path):
        root, g = self._corpus(tmp_path)
        res = coverage_engine.run(root, "all", None, None, g, False, None,
                                  do_preflight=False, run_validators=False)
        assert res["coverage_status"] == "OK"
        orphan_files = {o["source_file"] for o in res["orphans"]}
        phantom_files = {p["source_file"] for p in res["phantoms"]}
        assert "src/widget.py" in orphan_files   # in graph, not cited, not mentioned
        assert "src/ghost.py" in phantom_files    # cited, no graph node

    def test_empty_index_core_only_not_mass_fail(self, tmp_path):
        # empty index + remove features dir → orphans UNVERIFIABLE, never mass FAIL
        root, g = self._corpus(tmp_path, empty_index=True)
        import shutil
        shutil.rmtree(root / "docs" / "features")
        res = coverage_engine.run(root, "all", None, None, g, False, None,
                                  do_preflight=False, run_validators=False)
        assert res["orphan_status"] == "UNVERIFIABLE"
        assert res["orphans"] == []
        assert res["coverage_status"] == "UNVERIFIABLE"

    def test_absent_graph_unverifiable_not_fail(self, tmp_path):
        root, _g = self._corpus(tmp_path)
        res = coverage_engine.run(root, "all", None, None, tmp_path / "no.json", False, None,
                                  do_preflight=False, run_validators=False)
        assert res["coverage_status"] == "UNVERIFIABLE"
        assert res["orphans"] == [] and res["phantoms"] == []

    def test_strict_coverage_graphable_missing_graph_fails(self, tmp_path):
        root, _g = self._corpus(tmp_path)  # python repo → graphable
        res = coverage_engine.run(root, "all", None, None, tmp_path / "no.json", True, None,
                                  do_preflight=False, run_validators=False)
        assert res["coverage_status"] == "FAIL" and res["strict_fail"] is True

    def test_strict_coverage_nongraphable_no_fail(self, tmp_path):
        root, _g = self._corpus(tmp_path)
        # Force a non-graphable stack profile lookup miss → infer from langs; make repo cobol-only.
        import shutil
        shutil.rmtree(root / "src")
        (root / "src").mkdir()
        (root / "src" / "a.cbl").write_text("IDENTIFICATION DIVISION.", encoding="utf-8")
        res = coverage_engine.run(root, "all", None, None, tmp_path / "no.json", True, None,
                                  do_preflight=False, run_validators=False)
        assert res["graphable"] is False
        assert res["coverage_status"] == "UNVERIFIABLE" and res["strict_fail"] is False
