"""Tests for graph_to_drafts.py + graph_spec_coverage.py (graphify W1 drafts + coverage)."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
DRAFTS = SCRIPTS / "graph_to_drafts.py"
COVERAGE = SCRIPTS / "graph_spec_coverage.py"

GRAPH = {
    "nodes": [
        {"id": "f_user", "label": "user.py", "source_file": "app/models/user.py", "source_location": "L1"},
        {"id": "c_user", "label": "User", "source_file": "app/models/user.py", "source_location": "L8"},
        {"id": "c_base", "label": "Base", "source_file": "app/models/base.py", "source_location": "L3"},
        {"id": "f_routes", "label": "users.py", "source_file": "app/routes/users.py", "source_location": "L1"},
        {"id": "fn_list", "label": "list_users()", "source_file": "app/routes/users.py", "source_location": "L10"},
    ],
    "links": [
        {"relation": "inherits", "source": "c_user", "target": "c_base", "confidence": "EXTRACTED"},
        {"relation": "imports", "source": "f_routes", "target": "f_user", "confidence": "EXTRACTED"},
        {"relation": "imports", "source": "f_user", "target": "f_routes", "confidence": "INFERRED"},
    ],
}


def _mk_graph(tmp_path):
    gdir = tmp_path / "graphify-out"
    gdir.mkdir()
    (gdir / "graph.json").write_text(json.dumps(GRAPH))
    return gdir / "graph.json"


def _run(script, args):
    return subprocess.run([sys.executable, str(script)] + args,
                          capture_output=True, text=True, timeout=60)


def test_drafts_generated_with_classes_and_mermaid(tmp_path):
    gp = _mk_graph(tmp_path)
    out = tmp_path / "_graph-drafts"
    r = _run(DRAFTS, ["--graph", str(gp), "--outdir", str(out)])
    assert r.returncode == 0, r.stderr
    dm = (out / "data-model-draft.md").read_text()
    assert "class `User`" in dm and "inherits: Base" in dm and "TO-VERIFY" in dm
    ar = (out / "architecture-draft.md").read_text()
    assert "```mermaid" in ar and "app_models" in ar and "app_routes" in ar


def test_drafts_use_extracted_edges_only(tmp_path):
    """The INFERRED models->routes import edge must NOT appear in the module graph."""
    gp = _mk_graph(tmp_path)
    out = tmp_path / "d"
    _run(DRAFTS, ["--graph", str(gp), "--outdir", str(out)])
    ar = (out / "architecture-draft.md").read_text()
    assert "app_routes -->|1| app_models" in ar
    assert "app_models -->|1| app_routes" not in ar


def test_drafts_fail_cleanly_without_graph(tmp_path):
    r = _run(DRAFTS, ["--graph", str(tmp_path / "none.json"), "--outdir", str(tmp_path / "d")])
    assert r.returncode == 1


def test_coverage_warns_on_missing_class_and_route(tmp_path):
    gp = _mk_graph(tmp_path)
    (tmp_path / "app" / "routes").mkdir(parents=True)
    (tmp_path / "app" / "routes" / "users.py").write_text("x = 1\n")
    docs = tmp_path / "docs" / "generated"
    docs.mkdir(parents=True)
    (docs / "entities.md").write_text("## MODEL001 Base\nBase model only.\n")  # User missing
    (docs / "route-list.md").write_text("| GET | /none | other.py |\n")        # users.py missing
    r = _run(COVERAGE, ["--graph", str(gp), "--repo", str(tmp_path), "--docs", str(tmp_path / "docs")])
    assert r.returncode == 0  # advisory: never blocks
    assert "WARNING" in r.stdout and "User" in r.stdout and "users.py" in r.stdout


def test_coverage_ok_when_spec_complete(tmp_path):
    gp = _mk_graph(tmp_path)
    (tmp_path / "app" / "routes").mkdir(parents=True)
    (tmp_path / "app" / "routes" / "users.py").write_text("x = 1\n")
    docs = tmp_path / "docs" / "generated"
    docs.mkdir(parents=True)
    (docs / "entities.md").write_text("MODEL001 User, MODEL002 Base\n")
    (docs / "route-list.md").write_text("| GET | /users | app/routes/users.py |\n")
    r = _run(COVERAGE, ["--graph", str(gp), "--repo", str(tmp_path), "--docs", str(tmp_path / "docs")])
    assert r.returncode == 0
    assert "OK" in r.stdout and "WARNING" not in r.stdout
