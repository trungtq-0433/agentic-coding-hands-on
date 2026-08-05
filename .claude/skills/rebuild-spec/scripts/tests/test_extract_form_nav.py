"""Tests for extract_form_nav.py and _form_nav_lib.py (Phase 03).

Fixture project:
  main.dpr        — Application.CreateForm(TMainForm, MainForm) as root
  MainForm.pas    — TMainForm; navigates to TFormA via Show
  FormA.pas       — TFormA; navigates to TFormB via ShowModal
  FormB.pas       — TFormB; navigates to TFormC via TFormC.Create(...).Show
  FormC.pas       — TFormC (leaf — no outbound nav)
  OrphanForm.pas  — TOrphanForm (no inbound edge; reach:unverified)
  Dynamic.pas     — form with a commented-out fake nav call (must NOT emit edge)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_form_nav.py"
sys.path.insert(0, str(SCRIPTS_DIR))

import _form_nav_lib as lib  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(root: Path, plan_dir: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--plan-dir", str(plan_dir)]
        + (extra or []),
        capture_output=True, text=True, timeout=60,
    )


def _digest(plan_dir: Path) -> dict:
    p = plan_dir / "artifacts" / "_digest_extract_form_nav.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture Delphi sources
# ---------------------------------------------------------------------------

_DPR = """\
program TestApp;
uses
  Forms,
  MainForm in 'MainForm.pas' {MainForm},
  FormA in 'FormA.pas' {FormA},
  FormB in 'FormB.pas' {FormB},
  FormC in 'FormC.pas' {FormC},
  OrphanForm in 'OrphanForm.pas' {OrphanForm},
  Dynamic in 'Dynamic.pas' {Dynamic};
{$R *.res}
begin
  Application.Initialize;
  Application.CreateForm(TMainForm, MainForm);
  Application.CreateForm(TOrphanForm, OrphanForm);
  Application.Run;
end.
"""

_MAIN_FORM_PAS = """\
unit MainForm;
interface
uses Forms;
type
  TMainForm = class(TForm)
  private
    procedure OpenA;
  end;
var
  MainForm: TMainForm;
implementation
procedure TMainForm.OpenA;
begin
  FormA.Show;
end;
end.
"""

_FORM_A_PAS = """\
unit FormA;
interface
uses Forms;
type
  TFormA = class(TForm)
  private
    procedure OpenB;
  end;
var
  FormA: TFormA;
implementation
uses FormB;
procedure TFormA.OpenB;
begin
  FormB.ShowModal;
end;
end.
"""

_FORM_B_PAS = """\
unit FormB;
interface
uses Forms;
type
  TFormB = class(TForm)
  private
    procedure OpenC;
  end;
var
  FormB: TFormB;
implementation
procedure TFormB.OpenC;
begin
  TFormC.Create(nil).Show;
end;
end.
"""

_FORM_C_PAS = """\
unit FormC;
interface
uses Forms;
type
  TFormC = class(TForm)
  end;
var
  FormC: TFormC;
implementation
end.
"""

_ORPHAN_PAS = """\
unit OrphanForm;
interface
uses Forms;
type
  TOrphanForm = class(TForm)
  end;
var
  OrphanForm: TOrphanForm;
implementation
end.
"""

# Dynamic.pas: has a commented-out fake nav call that MUST NOT be emitted.
# Also has an indirect/dynamic show that should be unverified or ignored.
_DYNAMIC_PAS = """\
unit Dynamic;
interface
uses Forms;
type
  TDynamicForm = class(TForm)
  end;
var
  DynamicForm: TDynamicForm;
implementation
procedure ShowSomething(F: TForm);
begin
  // FakeForm.Show;   <-- this is a comment, must NOT produce an edge
  F.Show;           { block-comment-proof: } { also not a static nav }
end;
end.
"""


def _make_project(tmp_path: Path) -> tuple[Path, Path]:
    src = tmp_path / "src"
    src.mkdir()
    (src / "TestApp.dpr").write_text(_DPR, encoding="utf-8")
    (src / "MainForm.pas").write_text(_MAIN_FORM_PAS, encoding="utf-8")
    (src / "FormA.pas").write_text(_FORM_A_PAS, encoding="utf-8")
    (src / "FormB.pas").write_text(_FORM_B_PAS, encoding="utf-8")
    (src / "FormC.pas").write_text(_FORM_C_PAS, encoding="utf-8")
    (src / "OrphanForm.pas").write_text(_ORPHAN_PAS, encoding="utf-8")
    (src / "Dynamic.pas").write_text(_DYNAMIC_PAS, encoding="utf-8")
    plan_dir = tmp_path / "plan"
    return src, plan_dir


# ---------------------------------------------------------------------------
# _form_nav_lib unit tests
# ---------------------------------------------------------------------------

class TestStripLineComment:
    def test_strips_double_slash_comment(self):
        assert lib.strip_line_comment("  FormA.Show; // fake nav") == "  FormA.Show;"

    def test_no_comment_unchanged(self):
        assert lib.strip_line_comment("  FormA.Show;") == "  FormA.Show;"

    def test_full_comment_line_returns_empty(self):
        result = lib.strip_line_comment("  // FakeForm.Show;")
        assert result.strip() == ""


class TestStripBlockComments:
    def test_brace_comment_removed(self):
        text = "begin { fake nav FormA.Show } end;"
        result = lib.strip_block_comments(text)
        assert "FormA.Show" not in result

    def test_paren_star_comment_removed(self):
        text = "begin (* fake nav FormB.ShowModal *) end;"
        result = lib.strip_block_comments(text)
        assert "FormB.ShowModal" not in result

    def test_newlines_preserved(self):
        text = "a;\n{ comment }\nb;"
        result = lib.strip_block_comments(text)
        assert result.count('\n') == 2


class TestExtractDprForms:
    def test_detects_root_form(self):
        creates = lib.extract_dpr_forms(_DPR)
        assert len(creates) >= 1
        assert creates[0][0] == "TMainForm"


class TestParseNavLine:
    def test_var_show(self):
        edges = lib.parse_nav_line("  FormA.Show;", 10, "main.pas", {"FormA": "TFormA"})
        assert len(edges) == 1
        assert edges[0]["to_class"] == "TFormA"
        assert edges[0]["kind"] == "shows"
        assert edges[0]["line"] == 10
        assert edges[0]["file"] == "main.pas"
        assert not edges[0]["unverified"]

    def test_var_showmodal(self):
        edges = lib.parse_nav_line("  FormB.ShowModal;", 5, "a.pas", {"FormB": "TFormB"})
        assert edges[0]["kind"] == "showmodal"

    def test_class_create_show(self):
        edges = lib.parse_nav_line("  TFormC.Create(nil).Show;", 3, "b.pas", {})
        assert len(edges) == 1
        assert edges[0]["to_class"] == "TFormC"
        assert not edges[0]["unverified"]

    def test_application_create_form(self):
        edges = lib.parse_nav_line(
            "  Application.CreateForm(TMainForm, MainForm);", 1, "app.dpr", {}
        )
        assert len(edges) == 1
        assert edges[0]["to_class"] == "TMainForm"
        assert edges[0]["kind"] == "creates"

    def test_unknown_var_marked_unverified(self):
        edges = lib.parse_nav_line("  UnknownVar.Show;", 7, "x.pas", {})
        assert len(edges) == 1
        assert edges[0]["unverified"] is True

    def test_comment_stripped_before_matching(self):
        # Strip comment externally (as caller does) before calling parse_nav_line
        line = lib.strip_line_comment("  // FakeForm.Show;")
        edges = lib.parse_nav_line(line, 1, "x.pas", {})
        assert edges == []


# ---------------------------------------------------------------------------
# Full extractor integration tests
# ---------------------------------------------------------------------------

class TestExtractorCLI:
    def test_exit_0(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        r = _run(src, plan_dir)
        assert r.returncode == 0, r.stderr

    def test_status_ok(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        r = _run(src, plan_dir)
        out = json.loads(r.stdout)
        assert out["status"] == "ok"

    def test_digest_written(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        assert (plan_dir / "artifacts" / "_digest_extract_form_nav.json").exists()


class TestFormNodes:
    def test_all_form_units_listed(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        names = {f["name"] for f in d["forms"]}
        assert "TMainForm" in names
        assert "TFormA" in names
        assert "TFormB" in names
        assert "TFormC" in names
        assert "TOrphanForm" in names

    def test_orphan_tagged_unverified(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        orphan = next(f for f in d["forms"] if f["name"] == "TOrphanForm")
        assert orphan["reach"] == "unverified"

    def test_reachable_chain_tagged_static(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        reach_map = {f["name"]: f["reach"] for f in d["forms"]}
        assert reach_map["TMainForm"] == "static"
        assert reach_map["TFormA"] == "static"
        assert reach_map["TFormB"] == "static"
        assert reach_map["TFormC"] == "static"

    def test_every_form_node_has_file_and_line(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        for form in d["forms"]:
            assert "file" in form and form["file"]
            assert "line" in form and isinstance(form["line"], int) and form["line"] >= 1

    def test_root_form_identified(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        assert d["root_form"] == "TMainForm"


class TestEdges:
    def test_edges_have_file_and_line(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        for edge in d["edges"]:
            assert "file" in edge and edge["file"]
            assert "line" in edge and isinstance(edge["line"], int) and edge["line"] >= 1

    def test_edges_have_from_to_kind(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        for edge in d["edges"]:
            assert "from" in edge and edge["from"]
            assert "to" in edge and edge["to"]
            assert edge["kind"] in ("shows", "showmodal", "creates")

    def test_commented_nav_not_emitted(self, tmp_path):
        """// FakeForm.Show; in Dynamic.pas must NOT produce a static edge to FakeForm."""
        src, plan_dir = _make_project(tmp_path)
        _run(src, plan_dir)
        d = _digest(plan_dir)
        static_edges = [e for e in d["edges"] if not e.get("unverified")]
        targets = {e["to"] for e in static_edges}
        assert "FakeForm" not in targets


class TestResume:
    def test_second_run_skipped(self, tmp_path):
        src, plan_dir = _make_project(tmp_path)
        r1 = _run(src, plan_dir)
        assert json.loads(r1.stdout)["status"] == "ok"
        r2 = _run(src, plan_dir)
        assert json.loads(r2.stdout)["status"] == "skipped"


class TestEmptyProject:
    def test_empty_root_exits_0(self, tmp_path):
        src = tmp_path / "src"; src.mkdir()
        r = _run(src, tmp_path / "plan")
        assert r.returncode == 0


# Two TForm descendants in ONE .pas — non-conventional; nav edges attribute to first (E1 warning).
_MULTI_FORM_PAS = """\
unit MultiForm;
interface
uses Forms;
type
  TFirstForm = class(TForm)
  private
    procedure OpenSecond;
  end;
  TSecondForm = class(TForm)
  end;
var
  FirstForm: TFirstForm;
implementation
procedure TFirstForm.OpenSecond;
begin
  FirstForm.Show;
end;
end.
"""


class TestMultiFormClassWarning:
    def test_multi_form_class_emits_warning(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "App.dpr").write_text(_DPR, encoding="utf-8")
        (src / "MainForm.pas").write_text(_MAIN_FORM_PAS, encoding="utf-8")
        (src / "MultiForm.pas").write_text(_MULTI_FORM_PAS, encoding="utf-8")
        plan_dir = tmp_path / "plan"
        _run(src, plan_dir)
        d = _digest(plan_dir)
        assert any("multi_form_class" in w for w in d["warnings"]), d["warnings"]
        # Both classes still listed as forms (none dropped).
        names = {f["name"] for f in d["forms"]}
        assert {"TFirstForm", "TSecondForm"} <= names
