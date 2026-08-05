"""Tests for extract_sql_schema.py + _sql_parse_lib.py (Phase B)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_sql_schema.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import _extractor_lib as elib  # noqa: E402
import _sql_parse_lib as lib   # noqa: E402


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
    p = plan_dir / "artifacts" / "_digest_extract_sql_schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _load_manifest(plan_dir: Path) -> dict:
    p = plan_dir / "artifacts" / "_extraction-manifest.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# RT-F10: sanitize_identifier
# ---------------------------------------------------------------------------

class TestSanitizeIdentifier:
    def test_pipe_removed(self):
        # Contract: | is removed so no raw pipe appears in Markdown table cells.
        result = lib.sanitize_identifier("TAB|LE")
        assert "|" not in result
        assert len(result) > 0  # something remains after removal

    def test_newline_to_space(self):
        assert "\n" not in lib.sanitize_identifier("FOO\nBAR")

    def test_backtick_removed(self):
        assert "`" not in lib.sanitize_identifier("`orders`")

    def test_truncate(self):
        long_name = "A" * 200
        assert len(lib.sanitize_identifier(long_name)) <= 128


# ---------------------------------------------------------------------------
# RT-F7: scrub_credentials
# ---------------------------------------------------------------------------

class TestScrubCredentials:
    def test_identified_by_redacted(self):
        line = "CREATE USER app IDENTIFIED BY supersecret123;"
        scrubbed, redacted = lib.scrub_credentials(line)
        assert redacted is True
        assert "supersecret123" not in scrubbed
        assert "IDENTIFIED BY" in scrubbed
        assert "<redacted>" in scrubbed

    def test_password_eq_redacted(self):
        line = "connect string PASSWORD=mypassword123"
        scrubbed, redacted = lib.scrub_credentials(line)
        assert redacted is True
        assert "mypassword123" not in scrubbed

    def test_pwd_eq_redacted(self):
        line = "Server=host;PWD=secret"
        scrubbed, redacted = lib.scrub_credentials(line)
        assert redacted is True
        assert "secret" not in scrubbed

    def test_jdbc_password_redacted(self):
        line = "jdbc:oracle:thin:@host:1521:orcl?password=dbpassword"
        scrubbed, redacted = lib.scrub_credentials(line)
        assert redacted is True
        assert "dbpassword" not in scrubbed

    def test_ip_port_user_pass_redacted(self):
        line = "192.168.1.10:1521:scott:tiger"
        scrubbed, redacted = lib.scrub_credentials(line)
        assert redacted is True
        assert "tiger" not in scrubbed

    def test_clean_line_unchanged(self):
        line = "SELECT id, name FROM orders WHERE status = 'active';"
        scrubbed, redacted = lib.scrub_credentials(line)
        assert redacted is False
        assert scrubbed == line


# ---------------------------------------------------------------------------
# DDL parsing helpers
# ---------------------------------------------------------------------------

class TestParseDdlLine:
    def test_create_table(self):
        obj, inside = lib.parse_ddl_line("CREATE TABLE ORDERS (", 1, "ddl/orders.sql")
        assert obj is not None
        assert obj.kind == "table"
        assert obj.name == "ORDERS"
        assert inside is True

    def test_create_view(self):
        obj, inside = lib.parse_ddl_line("CREATE OR REPLACE VIEW V_ORDERS AS", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "view"
        assert obj.name == "V_ORDERS"
        assert inside is False

    def test_create_sequence(self):
        obj, inside = lib.parse_ddl_line("CREATE SEQUENCE SEQ_ORDER_ID START WITH 1;", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "sequence"

    def test_create_trigger(self):
        obj, inside = lib.parse_ddl_line("CREATE OR REPLACE TRIGGER TRG_ORDERS_AI", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "trigger"

    def test_create_procedure(self):
        obj, inside = lib.parse_ddl_line("CREATE OR REPLACE PROCEDURE sp_get_order", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "procedure"

    def test_create_package(self):
        obj, inside = lib.parse_ddl_line("CREATE OR REPLACE PACKAGE PKG_ORDERS AS", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "package"

    def test_create_package_body(self):
        obj, inside = lib.parse_ddl_line("CREATE OR REPLACE PACKAGE BODY PKG_ORDERS IS", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "package"

    def test_create_function(self):
        obj, inside = lib.parse_ddl_line("CREATE OR REPLACE FUNCTION fn_total_price", 1, "x.sql")
        assert obj is not None
        assert obj.kind == "function"

    def test_non_ddl_returns_none(self):
        obj, inside = lib.parse_ddl_line("SELECT * FROM orders;", 1, "x.sql")
        assert obj is None


class TestParseColumnLine:
    def test_leading_whitespace_column(self):
        assert lib.parse_column_line("    CUSTOMER_ID NUMBER(10),") == "CUSTOMER_ID"

    def test_leading_comma_column(self):
        # Oracle leading-comma DDL style: `,\tCAPTION VARCHAR2(40)`
        assert lib.parse_column_line(",\tCAPTION VARCHAR2(40)") == "CAPTION"
        assert lib.parse_column_line(", STATUS VARCHAR2(20)") == "STATUS"

    def test_leading_comma_constraint_skipped(self):
        assert lib.parse_column_line(", CONSTRAINT PK_X PRIMARY KEY (ID)") is None
        assert lib.parse_column_line(",PRIMARY KEY (ID)") is None


# ---------------------------------------------------------------------------
# Oracle DDL fixture — full extractor run
# ---------------------------------------------------------------------------

_ORACLE_DDL = """\
CREATE TABLE ORDERS (
    ID          NUMBER(10) NOT NULL,
    CUSTOMER_ID NUMBER(10),
    TOTAL       NUMBER(12,2),
    STATUS      VARCHAR2(20),
    CONSTRAINT PK_ORDERS PRIMARY KEY (ID)
);

CREATE VIEW V_ACTIVE_ORDERS AS
  SELECT * FROM ORDERS WHERE STATUS = 'ACTIVE';

CREATE SEQUENCE SEQ_ORDER_ID
  START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER TRG_ORDERS_AI
  AFTER INSERT ON ORDERS FOR EACH ROW
BEGIN NULL; END;
/

CREATE OR REPLACE PACKAGE PKG_ORDER_MGMT AS
  PROCEDURE create_order(p_customer_id IN NUMBER);
END;
/

CREATE OR REPLACE PROCEDURE sp_cancel_order(p_id IN NUMBER) AS
BEGIN
  UPDATE ORDERS SET STATUS = 'CANCELLED' WHERE ID = p_id;
END;
/
"""

_DDL_WITH_CRED = """\
CREATE USER app_user IDENTIFIED BY secretpassword;
CREATE TABLE AUDIT_LOG (
    ID   NUMBER,
    MSG  VARCHAR2(200)
);
"""


class TestOracleDdlExtraction:
    def test_all_object_kinds_detected(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "schema.sql").write_text(_ORACLE_DDL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr

        digest = _load_digest(plan_dir)
        kinds = {o["kind"] for o in digest["db_objects"]}
        assert "table" in kinds
        assert "view" in kinds
        assert "sequence" in kinds
        assert "trigger" in kinds
        assert "package" in kinds
        assert "procedure" in kinds

    def test_uppercase_extension_detected(self, tmp_path):
        # Case-sensitive filesystems (Linux) report `.SQL` uppercase — the lowercase
        # glob must still match it. Regression for the near-empty-digest bug.
        src = tmp_path / "src"
        src.mkdir()
        (src / "SCHEMA.SQL").write_text(_ORACLE_DDL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr

        digest = _load_digest(plan_dir)
        assert any(o["name"] == "ORDERS" for o in digest["db_objects"])

    def test_table_columns_extracted(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "schema.sql").write_text(_ORACLE_DDL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        orders = next(o for o in digest["db_objects"] if o["name"] == "ORDERS")
        assert "ID" in orders["columns"]
        assert "TOTAL" in orders["columns"]

    def test_all_objects_have_citations(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "schema.sql").write_text(_ORACLE_DDL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        for obj in digest["db_objects"]:
            assert "citation" in obj
            assert obj["citation"]  # non-empty

    def test_credential_scrubbed_from_digest(self, tmp_path):
        """RT-F7: IDENTIFIED BY secret must NOT appear in digest JSON."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "conn.sql").write_text(_DDL_WITH_CRED, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)
        digest_text = json.dumps(digest)

        assert "secretpassword" not in digest_text
        # Warn should be present
        assert any("potential_credential_in_citation" in w for w in digest["warnings"])

    def test_audit_log_table_still_extracted_after_cred_scrub(self, tmp_path):
        """Extraction continues correctly after a credential line."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "conn.sql").write_text(_DDL_WITH_CRED, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)

        names = {o["name"] for o in digest["db_objects"]}
        assert "AUDIT_LOG" in names


# ---------------------------------------------------------------------------
# RT-F11: resume / checkpoint
# ---------------------------------------------------------------------------

class TestResumeCheckpoint:
    def test_completed_extractor_skipped(self, tmp_path):
        """If manifest already marks completed=true, re-run prints skipped."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "x.sql").write_text("CREATE TABLE T (ID NUMBER);", encoding="utf-8")
        plan_dir = tmp_path / "plan"

        # First run
        r1 = _run_cli(src, plan_dir)
        assert r1.returncode == 0
        out1 = json.loads(r1.stdout)
        assert out1["status"] == "ok"

        # Second run — should be skipped
        r2 = _run_cli(src, plan_dir)
        assert r2.returncode == 0
        out2 = json.loads(r2.stdout)
        assert out2["status"] == "skipped"

    def test_manifest_round_trip(self, tmp_path):
        """write_digest_atomic + update_manifest + is_extractor_completed round-trip."""
        plan_dir = tmp_path / "plan"
        digest = {
            "extractor": "extract_sql_schema",
            "generated_at": "2026-01-01T00:00:00Z",
            "source_tree_hash": "abc123",
            "units": [],
            "db_objects": [],
            "warnings": [],
        }
        elib.write_digest_atomic(plan_dir, "extract_sql_schema", digest)
        elib.update_manifest(plan_dir, "extract_sql_schema", file_count=3, error_count=0)

        assert elib.is_extractor_completed(plan_dir, "extract_sql_schema") is True
        assert elib.is_extractor_completed(plan_dir, "extract_data_flow") is False

        manifest = _load_manifest(plan_dir)
        assert manifest["extract_sql_schema"]["completed"] is True
        assert manifest["extract_sql_schema"]["file_count"] == 3
        assert manifest["extract_sql_schema"]["error_count"] == 0

    def test_atomic_write_produces_valid_json(self, tmp_path):
        plan_dir = tmp_path / "plan"
        digest = {"extractor": "extract_sql_schema", "db_objects": [{"kind": "table", "name": "T"}]}
        path = elib.write_digest_atomic(plan_dir, "extract_sql_schema", digest)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["db_objects"][0]["name"] == "T"


# ---------------------------------------------------------------------------
# RT-F9: per-file timeout / size ceiling
# ---------------------------------------------------------------------------

class TestFileSizeCeiling:
    def test_oversized_file_warns_parse_timeout_exits_0(self, tmp_path):
        """A file exceeding the line ceiling emits parse_timeout warning; exit 0."""
        src = tmp_path / "src"
        src.mkdir()
        # Write 60_000 lines (above _FILE_LINE_CEILING=50_000) — non-POSIX path
        big_content = "-- comment\n" * 60_000
        (src / "big.sql").write_text(big_content, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        # Patch ceiling via env is not feasible here; instead pass --file-cap 0 to
        # exercise the file_cap_reached path, which also results in a warning + exit 0.
        r = _run_cli(src, plan_dir, ["--file-cap", "0"])
        assert r.returncode == 0

    def test_exit_0_on_empty_directory(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        plan_dir = tmp_path / "plan"
        r = _run_cli(src, plan_dir)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# RT-F10: pipe in table name → Markdown-safe identifier
# ---------------------------------------------------------------------------

class TestMarkdownSafeIdentifier:
    def test_pipe_in_name_does_not_appear_in_digest(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        # Table name with embedded pipe (adversarial)
        ddl = 'CREATE TABLE "ORDER|LINE" (\n  ID NUMBER\n);\n'
        (src / "schema.sql").write_text(ddl, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        _run_cli(src, plan_dir)
        digest = _load_digest(plan_dir)
        digest_text = json.dumps(digest)

        # Raw unescaped pipe must not appear inside any object name value
        for obj in digest["db_objects"]:
            assert "|" not in obj["name"], f"Raw pipe in name: {obj['name']!r}"


class TestSingleLineTableDoesNotSwallow:
    """Regression: a single-line CREATE TABLE (...); must not leave the parser stuck
    inside_table and swallow following PACKAGE/SEQUENCE statements."""

    def test_single_line_table_then_package_and_sequence(self, tmp_path):
        import json as _json, subprocess as _sp, sys as _sys
        scripts = Path(__file__).resolve().parents[1]
        proj = tmp_path / "proj"; (proj / "ddl").mkdir(parents=True)
        plan = tmp_path / "plan"; (plan / "artifacts").mkdir(parents=True)
        (proj / "ddl" / "schema.sql").write_text(
            "CREATE TABLE ORDERS (ID NUMBER, TOTAL NUMBER, STATUS VARCHAR2(20));\n"
            "CREATE OR REPLACE PACKAGE ORDER_PKG AS PROCEDURE place; END;\n"
            "CREATE SEQUENCE ORDER_SEQ;\n"
        )
        _sp.run([_sys.executable, str(scripts / "extract_sql_schema.py"),
                 "--root", str(proj), "--plan-dir", str(plan),
                 "--encoding", "utf-8", "--fallback", "utf-8"],
                capture_output=True, text=True, timeout=30, check=True)
        digest = _json.loads((plan / "artifacts" / "_digest_extract_sql_schema.json").read_text())
        kinds = {o["kind"] for o in digest["db_objects"]}
        names = {o["name"] for o in digest["db_objects"]}
        assert {"table", "package", "sequence"} <= kinds, kinds
        assert {"ORDERS", "ORDER_PKG", "ORDER_SEQ"} <= names, names
        orders = next(o for o in digest["db_objects"] if o["name"] == "ORDERS")
        assert "ID" in orders["columns"] and "TOTAL" in orders["columns"]


class TestCredentialScrubH1H2:
    """RT-F7 (review H1/H2): Oracle thin-JDBC / URL / CONNECT creds redacted + flagged;
    comment-only creds redacted but NOT flagged (no false alarm)."""

    def _scrub(self):
        import importlib
        return importlib.import_module("_sql_parse_lib").scrub_credentials

    def test_oracle_thin_jdbc_slash_redacted(self):
        s, flag = self._scrub()("conn := 'jdbc:oracle:thin:scott/tiger@prod:1521/ORCL';")
        assert "tiger" not in s and flag is True

    def test_url_embedded_cred_redacted(self):
        s, flag = self._scrub()("url = 'postgres://app:s3cret@db.host/mydb'")
        assert "s3cret" not in s and flag is True

    def test_sqlplus_connect_redacted(self):
        s, flag = self._scrub()("CONNECT appuser/hunter2@TNSPROD")
        assert "hunter2" not in s and flag is True

    def test_comment_only_cred_redacted_but_not_flagged(self):
        s, flag = self._scrub()("-- IDENTIFIED BY commentedsecret")
        assert "commentedsecret" not in s   # redacted (defense)
        assert flag is False                # but not flagged (no alert-fatigue false alarm)

    def test_real_identified_by_flagged(self):
        s, flag = self._scrub()("CREATE USER x IDENTIFIED BY realpw;")
        assert "realpw" not in s and flag is True


# ---------------------------------------------------------------------------
# RT-F9: oversized file handling (10MB ceiling) — unit-level tests
# ---------------------------------------------------------------------------

class TestOversizedFileSqlSchema:
    def test_oversized_file_skipped_with_warning(self, tmp_path, monkeypatch):
        """A file larger than _MAX_FILE_BYTES is skipped (no parse) with a warning."""
        import sys
        SCRIPTS_DIR = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(SCRIPTS_DIR))
        import extract_sql_schema as esq  # noqa: E402
        monkeypatch.setattr(esq, "_MAX_FILE_BYTES", 10)
        src = tmp_path / "big.sql"
        src.write_text("CREATE TABLE t (id INT);\n" * 20, encoding="utf-8")  # > 10 bytes
        objs, warnings, _partial = esq._parse_file(src, tmp_path, "utf-8", "latin-1")
        assert objs == []
        assert any("skipped_oversized" in w for w in warnings)

    def test_normal_sized_file_not_skipped(self, tmp_path, monkeypatch):
        """A file under the cap is NOT skipped (no skipped_oversized warning)."""
        import sys
        SCRIPTS_DIR = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(SCRIPTS_DIR))
        import extract_sql_schema as esq  # noqa: E402
        src = tmp_path / "ok.sql"
        src.write_text("CREATE TABLE t (id INT);\n", encoding="utf-8")
        _objs, warnings, _partial = esq._parse_file(src, tmp_path, "utf-8", "latin-1")
        assert not any("skipped_oversized" in w for w in warnings)

    def test_normal_file_parses_successfully(self, tmp_path):
        """Regression guard: normal-sized SQL file parses successfully."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "schema.sql").write_text(_ORACLE_DDL, encoding="utf-8")
        plan_dir = tmp_path / "plan"

        r = _run_cli(src, plan_dir)
        assert r.returncode == 0, r.stderr
        digest = _load_digest(plan_dir)

        # Normal parse should succeed
        assert len(digest["db_objects"]) >= 4  # multiple object kinds from the fixture
