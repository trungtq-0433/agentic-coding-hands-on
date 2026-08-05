"""Tests for extract_cobol_data.py + _cobol_data_lib/_cobol_verb_lib/_cobol_sql_lib/
_cobol_unit_parse_lib (Phase 05, Track C).

Covers: FILE-CONTROL/FD symbol-table join + OPEN-mode/ACCESS-MODE-gated CRUD
classification (sequential, indexed/DYNAMIC, RANDOM, REWRITE-after-READ state), the
EXEC SQL/cursor pass (static DML, DECLARE/OPEN/FETCH/CLOSE, EXECUTE IMMEDIATE ->
[UNVERIFIED] never a fabricated table), dataset vs table db_objects, and the
exit-0-always / byte-cap contract (fixes 5 and 9).

Fixture (b) (STOCK) reproduces the shape of a real AcuCOBOL FILE-CONTROL/FD/verb-set
confirmed by the target accounting system (flat-file/indexed I/O only, zero EXEC SQL) --
see phase-05-cobol-data-extractor.md. EXEC SQL fixtures are synthetic (the real target
has none) per the phase's dialect-agnostic requirement.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_cobol_data.py"
sys.path.insert(0, str(SCRIPTS_DIR))

import _cobol_data_lib as data_lib  # noqa: E402
import _cobol_dispatch_lib as dispatch_lib  # noqa: E402
import _cobol_sql_lib as sql_lib  # noqa: E402
import _cobol_unit_parse_lib as unit_lib  # noqa: E402

# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _run_cli(root: Path, plan_dir: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--plan-dir", str(plan_dir)] + (extra or []),
        capture_output=True, text=True, timeout=60,
    )


def _data_flow_digest(plan_dir: Path) -> dict:
    return json.loads((plan_dir / "artifacts" / "_digest_extract_data_flow.json").read_text(encoding="utf-8"))


def _sql_schema_digest(plan_dir: Path) -> dict:
    return json.loads((plan_dir / "artifacts" / "_digest_extract_sql_schema.json").read_text(encoding="utf-8"))


def _manifest(plan_dir: Path) -> dict:
    return json.loads((plan_dir / "artifacts" / "_extraction-manifest.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture (a): sequential-file CRUD (LINE SEQUENTIAL) — WRITE/READ only legal;
# REWRITE/DELETE illegal-for-mode -> WARN, never a false classification.
# ---------------------------------------------------------------------------

_SEQ_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SEQPROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT STKQNT  ASSIGN DISK
                  STATUS WS-STATUS
                  ACCESS SEQUENTIAL
                  ORGANIZATION LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  STKQNT
           LABEL RECORD STANDARD.
       01  QNT-RECORD1.
           03  QNT-CODE    PIC X(14).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN OUTPUT STKQNT.
           WRITE QNT-RECORD1.
           CLOSE STKQNT.
           OPEN INPUT STKQNT.
           READ STKQNT.
           CLOSE STKQNT.
           OPEN I-O STKQNT.
           REWRITE QNT-RECORD1.
           DELETE STKQNT.
           STOP RUN.
"""

# ---------------------------------------------------------------------------
# Fixture (b): real AcuCOBOL STOCK shape — indexed/DYNAMIC access, full verb set.
# ---------------------------------------------------------------------------

_STOCK_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. STOCKPROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT NOT OPTIONAL
                  STOCK   ASSIGN DISK
                          LOCK MANUAL
                          WITH LOCK ON MULTIPLE RECORDS
                          STATUS WS-STATUS
                          ACCESS DYNAMIC
                          ORGANIZATION INDEXED
                          RECORD STK-CODE
                          ALTERNATE RECORD STK-ACODE DUPLICATES
                          ALTERNATE RECORD STK-BSEQ = STK-BIN STK-CODE
                          ALTERNATE RECORD STK-DKEY DUPLICATES.
       DATA DIVISION.
       FILE SECTION.
       FD  STOCK     IS EXTERNAL
           LABEL RECORD STANDARD
           VALUE OF FILE-ID W02-STOCKF.
       01  STK-RECORD1.
           03  STK-CODE.
               05  STK-ITEM     PIC X(14).
               05  STK-PLU REDEFINES STK-ITEM PIC 9(14).
           03  STK-ACODE   PIC X(10).
           03  STK-QUANT   PIC S9(09)V9(04) COMP-3.
       PROCEDURE DIVISION.
       OPEN-STOCK.
           OPEN I-O STOCK.

       READ-STOCK.
           READ STOCK  WITH IGNORE LOCK
               KEY IS STK-CODE.
         IF WS-STATUS = "00"
             MOVE ZERO   TO WS-F-ERROR
             GO TO READ-STOCK-EXIT.
         IF WS-STATUS = "23"
             MOVE 22     TO WS-F-ERROR
             GO TO READ-STOCK-EXIT.
       READ-STOCK-EXIT.
           EXIT.

       START-AT-STOCK-CODE.
           START STOCK
               KEY >= STK-CODE.
           GO TO STOCK-CHECK-STATUS.

       STOCK-CHECK-STATUS.
           EXIT.

       REWRITE-STOCK.
           REWRITE STK-RECORD1.
         IF WS-STAT1 NOT = "0"
             MOVE 22     TO WS-F-ERROR
             PERFORM WRITE-ERROR.
           GO TO WRITE-STOCK-EXIT.

       DELETE-STOCK-REC.
           DELETE STOCK.
         IF WS-STAT1 NOT = "0"
             MOVE 22     TO WS-F-ERROR
             PERFORM WRITE-ERROR.
           UNLOCK STOCK.
           GO TO WRITE-STOCK-EXIT.

       WRITE-STOCK.
           WRITE STK-RECORD1.
         IF WS-STAT1 NOT = "0"
             MOVE 22     TO WS-F-ERROR
             PERFORM WRITE-ERROR.
       WRITE-STOCK-EXIT.
           EXIT.

       WRITE-ERROR.
           EXIT.
"""

# ---------------------------------------------------------------------------
# Fixture (c): I-O REWRITE with NO prior READ in this open session -> WARN, not U.
# ---------------------------------------------------------------------------

_NO_PRIOR_READ_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. NOPRIORREAD.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTMAST ASSIGN DISK
                  ACCESS DYNAMIC
                  ORGANIZATION INDEXED.
       DATA DIVISION.
       FILE SECTION.
       FD  CUSTMAST.
       01  CUST-RECORD1.
           03  CUST-ID  PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN I-O CUSTMAST.
           REWRITE CUST-RECORD1.
           STOP RUN.
"""

# ---------------------------------------------------------------------------
# Fixture (d): RANDOM access mode — full verb set, correctly classified.
# ---------------------------------------------------------------------------

_RANDOM_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. RANDPROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ORDMAST ASSIGN DISK
                  ACCESS RANDOM
                  ORGANIZATION INDEXED
                  RECORD KEY IS ORD-KEY.
       DATA DIVISION.
       FILE SECTION.
       FD  ORDMAST.
       01  ORD-RECORD1.
           03  ORD-KEY  PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN I-O ORDMAST.
           READ ORDMAST.
           REWRITE ORD-RECORD1.
           DELETE ORDMAST.
           WRITE ORD-RECORD1.
           STOP RUN.
"""

# ---------------------------------------------------------------------------
# VSAM/dataset fixture -> db_objects kind: "dataset".
# ---------------------------------------------------------------------------

_VSAM_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. VSAMPROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT VSAM-FILE ASSIGN TO VSAMDD
                  ORGANIZATION IS INDEXED
                  ACCESS MODE IS DYNAMIC
                  RECORD KEY IS VS-KEY
                  FILE STATUS IS WS-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  VSAM-FILE
           LABEL RECORDS ARE STANDARD.
       01  VS-RECORD.
           05  VS-KEY PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           STOP RUN.
"""

# ---------------------------------------------------------------------------
# Synthetic EXEC SQL fixture: static SELECT/INSERT/UPDATE/DELETE + cursor +
# EXECUTE IMMEDIATE dynamic SQL. The real target has zero EXEC SQL (flat-file only);
# this exercises the dialect-agnostic (DB2/Pro*COBOL-shape) requirement.
# ---------------------------------------------------------------------------

_EXEC_SQL_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SQLPROG.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ID       PIC X(10).
       01  WS-NAME     PIC X(30).
       01  WS-DYN-SQL  PIC X(80).
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC SQL
               SELECT CUST_NAME INTO :WS-NAME
               FROM CUSTOMERS
               WHERE CUST_ID = :WS-ID
           END-EXEC.

           EXEC SQL
               INSERT INTO CUSTOMERS (CUST_ID, CUST_NAME)
               VALUES (:WS-ID, :WS-NAME)
           END-EXEC.

           EXEC SQL
               UPDATE CUSTOMERS SET CUST_NAME = :WS-NAME
               WHERE CUST_ID = :WS-ID
           END-EXEC.

           EXEC SQL
               DELETE FROM CUSTOMERS
               WHERE CUST_ID = :WS-ID
           END-EXEC.

           EXEC SQL
               DECLARE CUST-CUR CURSOR FOR
               SELECT CUST_ID, CUST_NAME FROM CUSTOMERS
               WHERE CUST_NAME LIKE 'A%'
           END-EXEC.

           EXEC SQL
               OPEN CUST-CUR
           END-EXEC.

           EXEC SQL
               FETCH CUST-CUR INTO :WS-ID, :WS-NAME
           END-EXEC.

           EXEC SQL
               CLOSE CUST-CUR
           END-EXEC.

           EXEC SQL
               EXECUTE IMMEDIATE :WS-DYN-SQL
           END-EXEC.

           STOP RUN.
"""


# ---------------------------------------------------------------------------
# _cobol_data_lib.parse_file_verbs — direct unit tests
# ---------------------------------------------------------------------------

class TestSequentialFileVerbLegality:
    def test_write_read_classified_rewrite_delete_warn(self):
        db_ops, objs, warns = data_lib.parse_file_verbs(_SEQ_SRC.splitlines(), "seq.cbl")
        ops_by_op = {op["op"]: op for op in db_ops}
        assert set(ops_by_op) == {"C", "R"}
        assert ops_by_op["C"]["table"] == "STKQNT"
        assert ops_by_op["R"]["table"] == "STKQNT"
        assert all(op["citation"].startswith("seq.cbl:") for op in db_ops)
        assert any("REWRITE" in w and "LINE SEQUENTIAL" in w for w in warns)
        assert any("DELETE" in w and "illegal_verb_for_mode" in w for w in warns)
        assert {o["kind"] for o in objs} == {"dataset"}
        assert objs[0]["name"] == "STKQNT"


class TestIndexedDynamicAccessFullVerbSet:
    def test_all_four_crud_ops_classified_and_cited(self):
        db_ops, objs, warns = data_lib.parse_file_verbs(_STOCK_SRC.splitlines(), "stock.cbl")
        ops_by_op = {op["op"]: op for op in db_ops}
        assert set(ops_by_op) == {"C", "R", "U", "D"}
        for op in db_ops:
            assert op["table"] == "STOCK"
            assert op["citation"].startswith("stock.cbl:")
            assert op["confidence"] == "high"
        assert warns == []
        assert objs == [{"kind": "dataset", "name": "STOCK", "columns": [], "citation": "stock.cbl:6"}]


class TestRewriteWithoutPriorReadWarns:
    def test_rewrite_without_read_is_warn_not_false_update(self):
        db_ops, _objs, warns = data_lib.parse_file_verbs(_NO_PRIOR_READ_SRC.splitlines(), "noread.cbl")
        assert db_ops == []  # never a false U
        assert any("REWRITE" in w and "without prior READ" in w for w in warns)


class TestRandomAccessMode:
    def test_full_verb_set_classified(self):
        db_ops, _objs, warns = data_lib.parse_file_verbs(_RANDOM_SRC.splitlines(), "rand.cbl")
        ops_by_op = {op["op"]: op for op in db_ops}
        assert set(ops_by_op) == {"C", "R", "U", "D"}
        assert all(op["table"] == "ORDMAST" for op in db_ops)
        assert warns == []


class TestVsamDataset:
    def test_vsam_file_emits_dataset_kind(self):
        _db_ops, objs, _warns = data_lib.parse_file_verbs(_VSAM_SRC.splitlines(), "vsam.cbl")
        assert objs == [{"kind": "dataset", "name": "VSAM-FILE", "columns": [], "citation": "vsam.cbl:6"}]


# ---------------------------------------------------------------------------
# _cobol_sql_lib.parse_exec_sql — direct unit tests
# ---------------------------------------------------------------------------

class TestExecSqlStaticDmlAndCursor:
    def test_static_dml_and_cursor_fetch_classified(self):
        db_ops, objs, warns, dynamic = sql_lib.parse_exec_sql(_EXEC_SQL_SRC.splitlines(), "sqlprog.cbl")
        ops_by_op = {}
        for op in db_ops:
            ops_by_op.setdefault(op["op"], []).append(op)
        # C / U / D each appear once (INSERT / UPDATE / DELETE); R appears twice
        # (the static SELECT and the cursor FETCH), both against CUSTOMERS.
        assert set(ops_by_op) == {"C", "R", "U", "D"}
        assert len(ops_by_op["R"]) == 2
        assert all(op["table"] == "CUSTOMERS" for ops in ops_by_op.values() for op in ops)
        assert ops_by_op["C"][0]["columns"] == ["CUST_ID", "CUST_NAME"]
        assert objs == []
        assert dynamic is True
        assert any("dynamic_sql_detected" in w for w in warns)

    def test_execute_immediate_never_fabricates_a_table(self):
        _db_ops, _objs, _warns, dynamic = sql_lib.parse_exec_sql(_EXEC_SQL_SRC.splitlines(), "sqlprog.cbl")
        assert dynamic is True
        # No db_op anywhere carries a synthesized table for the EXECUTE IMMEDIATE block.
        db_ops, *_ = sql_lib.parse_exec_sql(_EXEC_SQL_SRC.splitlines(), "sqlprog.cbl")
        assert all(op["citation"] != "sqlprog.cbl:49" for op in db_ops)

    def test_exec_sql_create_table_emits_table_kind_db_object(self):
        """SQL tables from an embedded DDL statement -> db_objects kind: 'table' (reuses
        _sql_parse_lib.parse_ddl_line/extract_inline_columns, same as extract_sql_schema.py)."""
        src = """\
        PROCEDURE DIVISION.
        MAIN-PARA.
            EXEC SQL
                CREATE TABLE ORDERS (
                    ID INTEGER,
                    TOTAL DECIMAL(10,2)
                )
            END-EXEC.
            STOP RUN.
        """
        db_ops, objs, _warns, _dyn = sql_lib.parse_exec_sql(src.splitlines(), "ddl.cbl")
        assert db_ops == []
        assert objs == [{"kind": "table", "name": "ORDERS", "columns": ["ID", "TOTAL"], "citation": "ddl.cbl:3"}]

    def test_unknown_cursor_fetch_warns_not_fabricated(self):
        src = """\
        PROCEDURE DIVISION.
        MAIN-PARA.
            EXEC SQL
                FETCH NOSUCH-CUR INTO :WS-ID
            END-EXEC.
            STOP RUN.
        """
        db_ops, objs, warns, _dyn = sql_lib.parse_exec_sql(src.splitlines(), "f.cbl")
        assert db_ops == []
        assert objs == []
        assert any("unknown_cursor" in w for w in warns)

    def test_host_var_strip_is_quote_aware_does_not_corrupt_time_literal(self):
        """Regression (Wave 3 review): a colon inside a quoted SQL literal (e.g. a time
        literal '08:00:00') is data, not a host-var marker -- a naive whole-string strip
        would corrupt it into '080000'."""
        src = """\
        PROCEDURE DIVISION.
        MAIN-PARA.
            EXEC SQL
                SELECT CUST_ID FROM ORDERS
                WHERE ORDER_TIME > '08:00:00' AND CUST_ID = :WS-CUST-ID
            END-EXEC.
            STOP RUN.
        """
        db_ops, _objs, _warns, _dyn = sql_lib.parse_exec_sql(src.splitlines(), "timelit.cbl")
        assert len(db_ops) == 1
        assert db_ops[0]["op"] == "R"
        assert db_ops[0]["table"] == "ORDERS"


# ---------------------------------------------------------------------------
# _cobol_unit_parse_lib.parse_file — combined pass + dynamic-SQL confidence downgrade
# ---------------------------------------------------------------------------

class TestUnitLevelDynamicDowngrade:
    def test_dynamic_sql_downgrades_unit_confidence_and_flags_unverified(self, tmp_path):
        src = tmp_path / "sqlprog.cbl"
        src.write_text(_EXEC_SQL_SRC, encoding="utf-8")
        unit, _objs, _warns = unit_lib.parse_file(src, tmp_path, "utf-8", "latin-1")
        assert unit is not None
        assert unit["parse_coverage"]["dynamic_sql_detected"] is True
        assert unit["parse_coverage"]["confidence"] == "low"
        assert all(op["confidence"] == "low" and op.get("unverified") is True for op in unit["db_ops"])

    def test_static_only_unit_is_high_confidence(self, tmp_path):
        src = tmp_path / "stock.cbl"
        src.write_text(_STOCK_SRC, encoding="utf-8")
        unit, _objs, _warns = unit_lib.parse_file(src, tmp_path, "utf-8", "latin-1")
        assert unit["parse_coverage"]["dynamic_sql_detected"] is False
        assert unit["parse_coverage"]["confidence"] == "high"
        assert all(op["confidence"] == "high" and "unverified" not in op for op in unit["db_ops"])


# ---------------------------------------------------------------------------
# [Red-team fix 9] oversized-file byte cap — skip before read, no crash.
# ---------------------------------------------------------------------------

class TestOversizedFileByteCap:
    def test_oversized_file_skipped_with_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr(unit_lib, "_MAX_FILE_BYTES", 10)
        src = tmp_path / "big.cbl"
        src.write_text("x" * 200, encoding="utf-8")
        unit, objs, warnings = unit_lib.parse_file(src, tmp_path, "utf-8", "latin-1")
        assert unit is None
        assert objs == []
        assert any("skipped_oversized" in w for w in warnings)

    def test_normal_sized_file_not_skipped(self, tmp_path):
        src = tmp_path / "ok.cbl"
        src.write_text(_SEQ_SRC, encoding="utf-8")
        unit, _objs, warnings = unit_lib.parse_file(src, tmp_path, "utf-8", "latin-1")
        assert unit is not None
        assert not any("skipped_oversized" in w for w in warnings)


# ---------------------------------------------------------------------------
# [Red-team fix 5] malformed construct -> [WARN] parse_error, exit-0 always, no crash.
# ---------------------------------------------------------------------------

class TestMalformedConstructNeverCrashes:
    def test_forced_parse_exception_is_caught_as_warn(self, tmp_path, monkeypatch):
        """Fault-injection: force the file-verb pass to raise mid-parse (a genuinely
        malformed/unexpected construct could trip any parser). The per-file guard must
        catch it -> `[WARN] parse_error`, never propagate, unit skipped."""
        def _boom(_lines, _rel):
            raise ValueError("simulated malformed COBOL construct")

        monkeypatch.setattr(unit_lib, "parse_file_verbs", _boom)
        src = tmp_path / "malformed.cbl"
        src.write_text(_SEQ_SRC, encoding="utf-8")
        unit, objs, warnings = unit_lib.parse_file(src, tmp_path, "utf-8", "latin-1")
        assert unit is None
        assert objs == []
        assert any(w.startswith("parse_error:") for w in warnings)

    def test_unterminated_select_and_exec_sql_no_crash_end_to_end(self, tmp_path):
        """Genuinely malformed source: an unterminated FILE-CONTROL SELECT (no closing
        period) and an unterminated EXEC SQL block (no END-EXEC) — the CLI must still
        exit 0 and surface WARNs, never crash."""
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "BROKEN.cbl").write_text(
            "       IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. BROKEN.\n"
            "       ENVIRONMENT DIVISION.\n"
            "       INPUT-OUTPUT SECTION.\n"
            "       FILE-CONTROL.\n"
            "           SELECT BADFILE ASSIGN DISK\n"
            "                  ACCESS DYNAMIC\n"
            "       PROCEDURE DIVISION.\n"
            "           EXEC SQL\n"
            "               SELECT 1 FROM DUAL\n"
            "           STOP RUN.\n",
            encoding="utf-8",
        )
        r = _run_cli(root, plan)
        assert r.returncode == 0, r.stderr
        digest = _data_flow_digest(plan)
        assert any("unterminated_select" in w for w in digest["warnings"]) or \
            any("unterminated_exec_sql" in w for w in digest["warnings"])

    def test_nonexistent_root_never_crashes(self, tmp_path):
        root = tmp_path / "does-not-exist"
        plan = tmp_path / "plan"
        r = _run_cli(root, plan)
        assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# End-to-end CLI: shard filenames + manifest key (fix 2 — shard_name override).
# ---------------------------------------------------------------------------

class TestEndToEndDigestShardsAndManifest:
    def test_shards_write_canonical_filenames_manifest_keys_extract_cobol_data(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "STOCK.cbl").write_text(_STOCK_SRC, encoding="utf-8")
        (root / "SQLPROG.cbl").write_text(_EXEC_SQL_SRC, encoding="utf-8")

        r = _run_cli(root, plan)
        assert r.returncode == 0, r.stderr

        data_flow = _data_flow_digest(plan)
        sql_schema = _sql_schema_digest(plan)
        assert data_flow["extractor"] == "extract_cobol_data"
        assert sql_schema["extractor"] == "extract_cobol_data"
        assert len(data_flow["units"]) == 2
        assert data_flow["db_objects"] == []
        assert sql_schema["units"] == []
        # STOCK.cbl contributes a dataset db_object; SQLPROG.cbl has EXEC SQL DML only
        # (no CREATE TABLE), so no "table" kind object is present.
        assert sql_schema["db_objects"] == [
            {"kind": "dataset", "name": "STOCK", "columns": [], "citation": "STOCK.cbl:6"}
        ]

        manifest = _manifest(plan)
        assert manifest["extract_cobol_data"]["completed"] is True
        assert manifest["extract_cobol_data"]["file_count"] == 2

    def test_resume_skips_already_completed(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "STOCK.cbl").write_text(_STOCK_SRC, encoding="utf-8")
        r1 = _run_cli(root, plan)
        assert r1.returncode == 0, r1.stderr
        r2 = _run_cli(root, plan)
        assert r2.returncode == 0, r2.stderr
        assert json.loads(r2.stdout)["status"] == "skipped"


# ---------------------------------------------------------------------------
# Phase 01 regressions (C1, C2, H1, H2, H3) -- each reproduces the review's exact
# attack (plans/260718-2112-cobol-stack-critical-high-fixes/phase-01-crud-data-fixes.md)
# and asserts the safe/correct post-fix behavior.
# ---------------------------------------------------------------------------

# C1: a whole EXEC SQL...END-EXEC block commented out with col-7 `*` (each physical
# line indented so the 7th column holds the indicator) must never be scanned for
# EXEC SQL boundaries -- it used to be treated as live SQL, fabricating a DELETE.
_C1_COMMENTED_EXEC_SQL_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. C1PROG.
       PROCEDURE DIVISION.
       MAIN-PARA.
      * EXEC SQL
      *    DELETE FROM CUSTOMERS
      * END-EXEC.
           STOP RUN.
"""

# C2: a SQL `--` line comment containing the literal text "END-EXEC" must not close
# the block early -- the real DELETE and the real END-EXEC that follow must still
# be captured.
_C2_TRAILING_COMMENT_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. C2PROG.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC SQL
              -- note END-EXEC
              DELETE FROM ACCOUNTS WHERE ACCT_ID = :WS-ACCT
           END-EXEC.
           STOP RUN.
"""

# H1: single-line OPEN naming two files under two different modes -- each file must
# get the mode of its OWN preceding keyword, not the first keyword applied to all.
_H1_MULTI_MODE_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. H1PROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT FILE-A ASSIGN DISK
                  ORGANIZATION LINE SEQUENTIAL.
           SELECT FILE-B ASSIGN DISK
                  ORGANIZATION LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  FILE-A.
       01  FILE-A-REC   PIC X(10).
       FD  FILE-B.
       01  FILE-B-REC   PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT FILE-A, OUTPUT FILE-B.
           WRITE FILE-B-REC.
           STOP RUN.
"""

# H2: same two files/modes as H1, but the OPEN statement is split across a
# continuation line -- the second file's mode must not be lost/None.
_H2_CONTINUATION_OPEN_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. H2PROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT FILE-A ASSIGN DISK
                  ORGANIZATION LINE SEQUENTIAL.
           SELECT FILE-B ASSIGN DISK
                  ORGANIZATION LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  FILE-A.
       01  FILE-A-REC   PIC X(10).
       FD  FILE-B.
       01  FILE-B-REC   PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT FILE-A
                OUTPUT FILE-B.
           WRITE FILE-B-REC.
           STOP RUN.
"""

# H3: a seq-numbered comment (`000300*...`) inside a multi-line FILE-CONTROL SELECT
# must be skipped, not bled into the SELECT buffer -- otherwise its bogus
# "ORGANIZATION IS LINE SEQUENTIAL" clobbers the real "ORGANIZATION IS INDEXED"
# clause that follows, which would make a legal DELETE illegal.
_H3_SEQ_NUMBERED_COMMENT_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. H3PROG.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTMAST ASSIGN DISK
000300*  ORGANIZATION IS LINE SEQUENTIAL
                  ACCESS DYNAMIC
                  ORGANIZATION IS INDEXED.
       DATA DIVISION.
       FILE SECTION.
       FD  CUSTMAST.
       01  CUST-RECORD1.
           03  CUST-ID  PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN I-O CUSTMAST.
           DELETE CUSTMAST.
           STOP RUN.
"""


class TestC1CommentedExecSqlNeverFabricatesOp:
    def test_col7_commented_exec_sql_block_yields_zero_db_ops(self):
        db_ops, objs, warns, dynamic = sql_lib.parse_exec_sql(
            _C1_COMMENTED_EXEC_SQL_SRC.splitlines(), "c1.cbl")
        assert db_ops == []
        assert objs == []
        assert dynamic is False
        assert not any("unterminated_exec_sql" in w for w in warns)


class TestC2TrailingCommentDoesNotCloseBlockEarly:
    def test_sql_comment_containing_end_exec_does_not_erase_the_delete(self):
        db_ops, _objs, _warns, _dynamic = sql_lib.parse_exec_sql(
            _C2_TRAILING_COMMENT_SRC.splitlines(), "c2.cbl")
        assert db_ops != []
        assert any(op["op"] == "D" and op["table"] == "ACCOUNTS" for op in db_ops)


class TestH1OpenModeSplitPerFileToken:
    def test_each_file_gets_its_own_preceding_mode_not_the_first_one(self):
        db_ops, _objs, warns = data_lib.parse_file_verbs(_H1_MULTI_MODE_SRC.splitlines(), "h1.cbl")
        assert not any("illegal_verb_for_mode" in w or "unknown_file_verb" in w for w in warns)
        ops_by_op = {op["op"]: op for op in db_ops}
        assert set(ops_by_op) == {"C"}
        assert ops_by_op["C"]["table"] == "FILE-B"


class TestH2OpenContinuationJoinPreservesBothModes:
    def test_continuation_style_open_still_assigns_second_files_mode(self):
        db_ops, _objs, warns = data_lib.parse_file_verbs(
            _H2_CONTINUATION_OPEN_SRC.splitlines(), "h2.cbl")
        assert not any("illegal_verb_for_mode" in w or "unknown_file_verb" in w for w in warns)
        ops_by_op = {op["op"]: op for op in db_ops}
        assert set(ops_by_op) == {"C"}
        assert ops_by_op["C"]["table"] == "FILE-B"


class TestH3SeqNumberedCommentDoesNotBleedIntoSelectBuffer:
    def test_dispatch_lib_recognizes_seq_numbered_comment_at_col7(self):
        assert dispatch_lib.is_comment_line("000300*  ORGANIZATION IS LINE SEQUENTIAL") is True
        assert dispatch_lib.is_comment_line("                  ORGANIZATION IS INDEXED.") is False

    def test_real_organization_indexed_survives_and_delete_stays_legal(self):
        db_ops, _objs, warns = data_lib.parse_file_verbs(
            _H3_SEQ_NUMBERED_COMMENT_SRC.splitlines(), "h3.cbl")
        assert not any("LINE SEQUENTIAL" in w for w in warns)
        assert not any("illegal_verb_for_mode" in w for w in warns)
        ops_by_op = {op["op"]: op for op in db_ops}
        assert set(ops_by_op) == {"D"}
        assert ops_by_op["D"]["table"] == "CUSTMAST"
