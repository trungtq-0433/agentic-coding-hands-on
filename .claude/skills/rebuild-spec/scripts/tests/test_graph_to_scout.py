"""Tests for scripts/graph_to_scout.py — deterministic scout-report from graph.json."""
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "graph_to_scout.py"


def _mk_repo(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname='x'\n")
    (tmp_path / "app" / "routes").mkdir(parents=True)
    (tmp_path / "app" / "models").mkdir(parents=True)
    (tmp_path / "app" / "routes" / "users.py").write_text("def list_users(): pass\n")
    (tmp_path / "app" / "models" / "user.py").write_text("class User: pass\n")
    (tmp_path / "app" / "worker.py").write_text("from celery import shared_task\n@shared_task\ndef job(): pass\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_users.py").write_text("def test(): pass\n")
    g = {"nodes": [
        {"label": "users.py", "source_file": "app/routes/users.py", "source_location": "L1"},
        {"label": "User", "source_file": "app/models/user.py", "source_location": "L1"},
    ], "links": []}
    gdir = tmp_path / "graphify-out"
    gdir.mkdir()
    (gdir / "graph.json").write_text(json.dumps(g))
    return tmp_path


def _run(repo, out):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--graph", str(repo / "graphify-out" / "graph.json"),
         "--repo", str(repo), "--out", str(out)],
        capture_output=True, text=True, timeout=60,
    )


def test_generates_contract_sections(tmp_path):
    repo = _mk_repo(tmp_path)
    out = tmp_path / "plan" / "scout-report.md"
    r = _run(repo, out)
    assert r.returncode == 0, r.stderr
    txt = out.read_text()
    for section in ("## Detected Language", "## Scanned Directories", "## File Inventory",
                    "## Background Logic Source Inventory", "## Detected API Kind", "## Notes"):
        assert section in txt, f"missing {section}"
    assert "Python" in txt


def test_inventory_covers_all_source_excludes_tests(tmp_path):
    repo = _mk_repo(tmp_path)
    out = tmp_path / "scout.md"
    _run(repo, out)
    txt = out.read_text()
    rows = dict(re.findall(r"^([\w./-]+\.py)\t(\w+)$", txt, re.MULTILINE))
    assert "app/routes/users.py" in rows and rows["app/routes/users.py"] == "route"
    assert "app/models/user.py" in rows and rows["app/models/user.py"] == "model"
    assert "app/worker.py" in rows
    assert "tests/test_users.py" not in rows


def test_bl_inventory_finds_markers(tmp_path):
    repo = _mk_repo(tmp_path)
    out = tmp_path / "scout.md"
    _run(repo, out)
    txt = out.read_text()
    assert "app/worker.py" in txt.split("## Background Logic Source Inventory")[1]


def test_fails_cleanly_without_graph(tmp_path):
    (tmp_path / "pyproject.toml").write_text("x")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--graph", str(tmp_path / "nope.json"),
         "--repo", str(tmp_path), "--out", str(tmp_path / "o.md")],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 1
    assert not (tmp_path / "o.md").exists()
