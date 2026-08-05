"""Tests for extract_data_flow.py + _sql_parse_lib.py DML/dynamic-SQL paths (Phase B)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_data_flow.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import _sql_dml_lib as lib   # noqa: E402 — DML + dynamic-SQL helpers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_cli(root: Path, plan_dir: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--root", str(root),
         "--plan-dir", str(plan_dir)] + (extra or []),
        capture_output=True, text=True, timeout=60,
    )


def _load_digest(plan_dir: Path) -> dict:
    p = plan_dir / "artifacts" / "_digest_extract_data_flow.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture Delphi source files
# ---------------------------------------------------------------------------

_DELPHI_STATIC_SQL = """\
unit Orders;
interface
uses DB, OrderTypes;

implementation

procedure TOrderForm.SaveOrder;
begin
  with FQuery do begin
    SQL.Text := 'INSERT INTO ORDERS (ID, CUSTOMER_ID, TOTAL) VALUES (:id, :cust, :total)';
    ExecSQL;
  end;

  with FQuery2 do begin
    SQL.Text := 'SELECT ID, STATUS FROM ORDERS WHERE CUSTOMER_ID = :cust';
    Open;
  end;

  with FQuery3 do begin
    SQL.Text := 'UPDATE ORDERS SET STATUS = :s WHERE ID = :id';
    ExecSQL;
  end;

  with FQuery4 do begin
    SQL.Text := 'DELETE FROM ORDERS WHERE ID = :id';
    ExecSQL;
  end;
end;

end.
"""

_DELPHI_DYNAMIC_SQL = """\
unit DynQuery;
interface
implementation

procedure TDynForm.BuildQuery(const TableName: string);
var
  sSQL: string;
begin
  sSQL := 'SELECT * FROM ';
  sSQL := sSQL + TableName;
  FQuery.SQL.Add(sSQL);
  FQuery.Open;
end;

procedure TDynForm.FormatQuery(const Cond: string);
begin
  FQuery.SQL.Text := Format('SELECT * FROM ORDERS WHERE STATUS = %s', [Cond]);
  FQuery.Open;
end;

end.
"""

_DELPHI_WITH_CRED = """\
unit ConnStr;
interface
implementation

const
  CONN_STR = 'Data Source=myserver;User Id=app;Password=secret123;';

procedure TConnForm.Connect;
begin
  FConn.ConnectionString := CONN_STR;
  FConn.Open;
  FQuery.SQL.Text := 'SELECT ID FROM ORDERS';
  FQuery.Open;
end;

end.
"""

_PAS_WITH_PIPE_TABLE = """\
unit PipeTest;
interface
implementation

procedure TForm1.Load;
begin
  FQuery.SQL.Text := 'SELECT * FROM ORDER|LINE';
  FQuery.Open;
end;

end.
"""


# ---------------------------------------------------------------------------
# DML parse_dml_line unit tests
# ---------------------------------------------------------------------------

class TestParseDmlLine:
    def test_insert_op(self):
        ops = lib.parse_dml_line(
            "INSERT INTO ORDERS (ID, TOTAL) VALUES (1, 99.0);", 10, "u.pas"
        )
        assert len(ops) == 1
        assert ops[0].op == "C"
        assert ops[0].table == "ORDERS"
        assert "ID" in ops[0].columns
        assert ops[0].line == 10

    def test_select_op(self):
        ops = lib.parse_dml_line("SELECT ID, STATUS FROM ORDERS WHERE ID = 1;", 5, "u.pas")
        assert len(ops) == 1
        assert ops[0].op == "R"
        assert ops[0].table == "ORDERS"

    def test_update_op(self):
        ops = lib.parse_dml_line("UPDATE ORDERS SET STATUS = 'X' WHERE ID = 1;", 7, "u.pas")
        assert len(ops) == 1
        assert ops[0].op == "U"
        assert ops[0].table == "ORDERS"

    def test_delete_op(self):
        ops = lib.parse_dml_line("DELETE FROM ORDERS WHERE ID = 1;", 8, "u.pas")
        assert len(ops) == 1
        assert ops[0].op == "D"

    def test_merge_emits_c_and_u(self):
        ops = lib.parse_dml_line("MERGE INTO ORDERS USING src ON (ORDERS.ID = src.ID);", 1, "u.sql")
        assert len(ops) == 2
        ops_set = {o.op for o in ops}
        assert "C" in ops_set
        assert "U" in ops_set

    def test_citation_format(self):
        ops = lib.parse_dml_line("INSERT INTO T (A) VALUES (1);", 42, "path/to/file.pas")
        assert ops[0].citation == "path/to/file.pas:42"

    def test_non_dml_returns_empty(self):
        ops = lib.parse_dml_line("-- this is a comment", 1, "u.pas")
        assert ops == []

    def test_insert_without_columns(self):
        ops = lib.parse_dml_line("INSERT INTO LOG VALUES (1, 'msg');", 1, "u.pas")
        assert len(ops) == 1
        assert ops[0].op == "C"
        assert ops[0].table == "LOG"


# ---------------------------------------------------------------------------
# RT-F8: dynamic SQL detection
# ---------------------------------------------------------------------------

class TestDynamicSqlDetection:
    def test_tquery_sql_add(self):
        assert lib.is_dynamic_sql_line("  FQuery.SQL.Add(sSQL);")

    def test_sql_text_assign(self):
        assert lib.is_dynamic_sql_line("  FQuery.SQL.Text := someVar;")

    def test_format_with_percent_s(self):
        assert lib.is_dynamic_sql_line("  FQuery.SQL.Text := Format('SELECT * FROM ORDERS WHERE STATUS = %s', [x]);")

    def test_string_concat_sql(self):
        assert lib.is_dynamic_sql_line("  sSQL := sSQL + TableName;")

    def test_execute_direct_var(self):
        assert lib.is_dynamic_sql_line("  ExecuteDirect(sSQL);")

    def test_plain_sql_not_dynamic(self):
        assert not lib.is_dynamic_sql_line("  FQuery.SQL.Text := 'SELECT * FROM ORDERS';")

    def test_comment_not_dynamic(self):
        assert not lib.is_dynamic_sql_line("  // FQuery.SQL.Add('test');")


# ---------------------------------------------------------------------------
# Full extractor: static SQL fixture
# ---------------------------------------------------------------------------

class TestDataFlowStaticSql:
    def test_insert_select_update_delete_detected(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr

        digest = _load_digest(plan_dir)
        assert len(digest["units"]) >= 1

        unit = digest["units"][0]
        ops = unit["db_ops"]
        op_types = {o["op"] for o in ops}

        # INSERT → C
        assert "C" in op_types
        # SELECT → R
        assert "R" in op_types
        # UPDATE → U
        assert "U" in op_types
        # DELETE → D
        assert "D" in op_types

    def test_all_ops_reference_orders_table(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        for op in unit["db_ops"]:
            assert op["table"] == "ORDERS"

    def test_insert_op_has_columns(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        insert_ops = [o for o in unit["db_ops"] if o["op"] == "C"]
        assert insert_ops
        assert insert_ops[0]["columns"]  # non-empty column list

    def test_op_has_line_number(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        for op in unit["db_ops"]:
            assert isinstance(op["line"], int)
            assert op["line"] > 0

    def test_citations_reference_file(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        for op in unit["db_ops"]:
            assert "Orders.pas" in op["citation"]
            assert ":" in op["citation"]


# ---------------------------------------------------------------------------
# RT-F8: dynamic SQL fixture
# ---------------------------------------------------------------------------

class TestDynamicSqlFixture:
    def test_dynamic_sql_detected_true(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "DynQuery.pas").write_text(_DELPHI_DYNAMIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr

        digest = _load_digest(plan_dir)
        unit = digest["units"][0]
        assert unit["parse_coverage"]["dynamic_sql_detected"] is True

    def test_dynamic_sql_confidence_low(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "DynQuery.pas").write_text(_DELPHI_DYNAMIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        assert unit["parse_coverage"]["confidence"] == "low"

    def test_dynamic_ops_marked_unverified(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        # File has both static and dynamic SQL
        mixed = _DELPHI_STATIC_SQL + "\n" + _DELPHI_DYNAMIC_SQL
        (src / "Mixed.pas").write_text(mixed, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        if unit["parse_coverage"]["dynamic_sql_detected"]:
            for op in unit["db_ops"]:
                assert op["confidence"] == "low"
                assert op.get("unverified") is True


# ---------------------------------------------------------------------------
# RT-F7: credential scrub in data flow
# ---------------------------------------------------------------------------

class TestCredentialScrubDataFlow:
    def test_password_not_in_digest(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Conn.pas").write_text(_DELPHI_WITH_CRED, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr

        digest = _load_digest(plan_dir)
        digest_text = json.dumps(digest)

        assert "secret123" not in digest_text
        assert any("potential_credential_in_citation" in w for w in digest["warnings"])

    def test_extraction_continues_after_cred_line(self, tmp_path):
        """SELECT after the credential line must still be captured."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "Conn.pas").write_text(_DELPHI_WITH_CRED, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        all_ops = [op for u in digest["units"] for op in u["db_ops"]]
        assert any(op["table"] == "ORDERS" and op["op"] == "R" for op in all_ops)


# ---------------------------------------------------------------------------
# RT-F10: pipe in table name
# ---------------------------------------------------------------------------

class TestMarkdownSafeTableName:
    def test_pipe_in_table_name_escaped_in_digest(self, tmp_path):
        """RT-F10: raw unescaped | must not appear in db_ops table names."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "PipeTest.pas").write_text(_PAS_WITH_PIPE_TABLE, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr

        digest = _load_digest(plan_dir)
        for unit in digest["units"]:
            for op in unit["db_ops"]:
                assert "|" not in op["table"], f"Raw pipe in table name: {op['table']!r}"


# ---------------------------------------------------------------------------
# RT-F11: resume checkpoint
# ---------------------------------------------------------------------------

class TestResumeDataFlow:
    def test_completed_extractor_skipped_on_rerun(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r1 = _run_cli(src, plan_dir)
        assert r1.returncode == 0
        out1 = json.loads(r1.stdout)
        assert out1["status"] == "ok"

        r2 = _run_cli(src, plan_dir)
        assert r2.returncode == 0
        out2 = json.loads(r2.stdout)
        assert out2["status"] == "skipped"


# ---------------------------------------------------------------------------
# RT-F9: size ceiling / exit 0
# ---------------------------------------------------------------------------

class TestFileSizeCeiling:
    def test_file_cap_zero_exits_0(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir, ["--file-cap", "0"])
        assert r.returncode == 0

    def test_empty_directory_exits_0(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# parse_coverage schema
# ---------------------------------------------------------------------------

class TestParseCoverageSchema:
    def test_parse_coverage_fields_present(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        for unit in digest["units"]:
            pc = unit["parse_coverage"]
            assert "static_sql_found" in pc
            assert "dynamic_sql_detected" in pc
            assert "confidence" in pc
            assert pc["confidence"] in ("high", "medium", "low")

    def test_static_sql_count_correct(self, tmp_path):
        """_DELPHI_STATIC_SQL has 4 DML statements → static_sql_found == 4."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        unit = digest["units"][0]
        assert unit["parse_coverage"]["static_sql_found"] == 4


# ---------------------------------------------------------------------------
# RT-F9: oversized file handling (10MB ceiling) — unit-level tests
# ---------------------------------------------------------------------------

class TestOversizedFileSkipping:
    def test_oversized_file_skipped_with_warning(self, tmp_path, monkeypatch):
        """A file larger than _MAX_FILE_BYTES is skipped (unit None) with a warning."""
        import sys
        SCRIPTS_DIR = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(SCRIPTS_DIR))
        import extract_data_flow as edf  # noqa: E402
        monkeypatch.setattr(edf, "_MAX_FILE_BYTES", 10)
        src = tmp_path / "big.pas"
        src.write_text("x" * 200, encoding="utf-8")  # > 10 bytes
        unit, warnings = edf._parse_file(src, tmp_path, "utf-8", "latin-1")
        assert unit is None
        assert any("skipped_oversized" in w for w in warnings)

    def test_normal_sized_file_not_skipped(self, tmp_path):
        """A file under the cap is NOT skipped (no skipped_oversized warning)."""
        import sys
        SCRIPTS_DIR = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(SCRIPTS_DIR))
        import extract_data_flow as edf  # noqa: E402
        src = tmp_path / "ok.pas"
        src.write_text("procedure Foo; begin end;", encoding="utf-8")
        _unit, warnings = edf._parse_file(src, tmp_path, "utf-8", "latin-1")
        assert not any("skipped_oversized" in w for w in warnings)
        # This is a basic regression test to ensure the feature is in place

    def test_normal_file_parses_successfully(self, tmp_path):
        """Regression guard: normal-sized file still parses successfully."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "Orders.pas").write_text(_DELPHI_STATIC_SQL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr
        digest = _load_digest(plan_dir)

        # Normal parse should succeed
        assert len(digest["units"]) >= 1
        unit = digest["units"][0]
        assert len(unit["db_ops"]) >= 4  # 4 DML statements from the fixture
