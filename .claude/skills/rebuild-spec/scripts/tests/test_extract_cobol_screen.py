"""Tests for extract_cobol_screen.py + _cobol_dispatch_lib.py (Phase 01 foundation).

Covers the router's dispatch discipline (macro-shaped anchored regex, not naive substring),
the EBCDIC/binary sanity guard (never a silent zero-screen result), the exit-0-always /
accumulate-then-finalize contract, and the cobol.json stack-profile registration
(load_profiles + detect_stack_profile recommending "cobol").
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_cobol_screen.py"
DETECT_SCRIPT = SCRIPTS_DIR / "detect_stack_profile.py"
sys.path.insert(0, str(SCRIPTS_DIR))

import _cobol_dispatch_lib as dispatch  # noqa: E402
import _stack_profile_lib as stacklib  # noqa: E402
import extract_cobol_screen as ecs  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture source snippets
# ---------------------------------------------------------------------------

_SCREEN_SECTION_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROG1.
       DATA DIVISION.
       SCREEN SECTION.
       01 SCR1.
           05 FIELD1 LINE 1 COLUMN 1 PIC X(10).
       PROCEDURE DIVISION.
           DISPLAY SCR1.
           STOP RUN.
"""

# DFHMDI appears ONLY inside a comment line — must NOT dispatch to the BMS lib.
_COMMENT_ONLY_DFHMDI_SRC = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROG2.
       DATA DIVISION.
       SCREEN SECTION.
      * this comment mentions DFHMDI but is not a macro line
       01 SCR2.
           05 FIELD1 LINE 1 COLUMN 1 PIC X(10).
       PROCEDURE DIVISION.
           DISPLAY SCR2.
           STOP RUN.
"""

_BMS_SRC = """\
MAPSET1  DFHMSD TYPE=&SYSPARM,MODE=INOUT,LANG=COBOL,STORAGE=AUTO
MAP1     DFHMDI SIZE=(24,80),LINE=1,COLUMN=1
FIELDA   DFHMDF POS=(1,1),LENGTH=10,ATTRB=(NORM)
"""


def _run(root: Path, plan_dir: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--plan-dir", str(plan_dir)]
        + (extra or []),
        capture_output=True, text=True, timeout=60,
    )


def _digest(plan_dir: Path) -> dict:
    p = plan_dir / "artifacts" / "_digest_extract_cobol_screen.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _manifest(plan_dir: Path) -> dict:
    p = plan_dir / "artifacts" / "_extraction-manifest.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Dispatch sniffing (unit-level, no subprocess)
# ---------------------------------------------------------------------------

class TestDispatchSniff:
    def test_bms_macro_line_detected(self):
        lines = _BMS_SRC.splitlines()
        assert dispatch.matches_bms_macro(lines) is True

    def test_screen_section_detected(self):
        lines = _SCREEN_SECTION_SRC.splitlines()
        assert dispatch.matches_screen_section(lines) is True

    def test_dfhmdi_only_in_comment_does_not_match_bms(self):
        # [Medium fix] anchored macro-shaped dispatch, not a bare substring check.
        lines = _COMMENT_ONLY_DFHMDI_SRC.splitlines()
        assert dispatch.matches_bms_macro(lines) is False
        assert dispatch.matches_screen_section(lines) is True

    def test_valid_cobol_passes_sanity_check(self):
        assert dispatch.looks_like_cobol(_SCREEN_SECTION_SRC.splitlines()) is True
        assert dispatch.looks_like_cobol(_BMS_SRC.splitlines()) is True  # DFHMSD token

    def test_garbled_bytes_fail_sanity_check(self):
        garbled = ["\x00\x01\xfe\xff not cobol at all", "more garbage bytes here"]
        assert dispatch.looks_like_cobol(garbled) is False


# ---------------------------------------------------------------------------
# _process_file routing (unit-level — stubs always return [] from finalize(),
# so routing correctness must be observed via which lib got fed).
# ---------------------------------------------------------------------------

class TestProcessFileRouting:
    def test_comment_only_dfhmdi_file_feeds_section_lib_only(self, tmp_path):
        root = tmp_path
        f = root / "PROG2.cbl"
        f.write_text(_COMMENT_ONLY_DFHMDI_SRC, encoding="utf-8")
        section_lib = ecs.ScreenSectionLib()
        bms_lib = ecs.BmsLib()
        warns = ecs._process_file(f, root, section_lib, bms_lib, "utf-8", "latin-1")
        assert warns == []
        assert len(section_lib._fed) == 1
        assert len(bms_lib._fed) == 0

    def test_both_match_feeds_both_libs(self, tmp_path):
        root = tmp_path
        # A file with both a SCREEN SECTION declaration and a real (non-comment) BMS macro line.
        both_src = _SCREEN_SECTION_SRC + "\n" + _BMS_SRC
        f = root / "BOTH.cbl"
        f.write_text(both_src, encoding="utf-8")
        section_lib = ecs.ScreenSectionLib()
        bms_lib = ecs.BmsLib()
        warns = ecs._process_file(f, root, section_lib, bms_lib, "utf-8", "latin-1")
        assert warns == []
        assert len(section_lib._fed) == 1
        assert len(bms_lib._fed) == 1

    def test_bms_extension_always_routes_to_bms_lib(self, tmp_path):
        root = tmp_path
        f = root / "MAP1.bms"
        f.write_text(_BMS_SRC, encoding="utf-8")
        section_lib = ecs.ScreenSectionLib()
        bms_lib = ecs.BmsLib()
        ecs._process_file(f, root, section_lib, bms_lib, "utf-8", "latin-1")
        assert len(bms_lib._fed) == 1

    def test_ebcdic_binary_guard_skips_file_no_lib_fed(self, tmp_path):
        root = tmp_path
        f = root / "GARBLE.cbl"
        f.write_bytes(bytes([0xC1, 0xC2, 0xC3, 0x40, 0x00, 0xFF, 0xFE] * 50))
        section_lib = ecs.ScreenSectionLib()
        bms_lib = ecs.BmsLib()
        warns = ecs._process_file(f, root, section_lib, bms_lib, "utf-8", "latin-1")
        assert any(w.startswith("possible_ebcdic_or_binary:") for w in warns)
        assert len(section_lib._fed) == 0
        assert len(bms_lib._fed) == 0


# ---------------------------------------------------------------------------
# End-to-end router CLI (exit-0-always, digest + manifest contract)
# ---------------------------------------------------------------------------

class TestRouterCLI:
    def test_router_exits_zero_writes_digest_and_manifest(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "PROG1.cbl").write_text(_SCREEN_SECTION_SRC, encoding="utf-8")
        (root / "MAP1.bms").write_text(_BMS_SRC, encoding="utf-8")

        r = _run(root, plan)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["status"] == "ok"
        # Phase 02 (screen-section) + Phase 03 (BMS) have both landed since this test was
        # written: PROG1.cbl's SCREEN SECTION now yields 1 screen (SCR1), and MAP1.bms's
        # DFHMDI now yields 1 screen (MAP1) — see test_cobol_screen_section.py /
        # test_cobol_bms.py for paradigm-specific coverage of each.
        assert out["screens"] == 2

        digest = _digest(plan)
        assert digest["extractor"] == "extract_cobol_screen"
        assert {s["screen"] for s in digest["screens"]} == {"SCR1", "MAP1"}

        manifest = _manifest(plan)
        assert manifest["extract_cobol_screen"]["completed"] is True
        assert manifest["extract_cobol_screen"]["file_count"] == 2
        assert manifest["extract_cobol_screen"]["error_count"] == 0

    def test_garbled_bytes_emit_warning_not_silent_empty(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "GARBLE.cbl").write_bytes(bytes([0xC1, 0xC2, 0xC3, 0x40, 0x00, 0xFF, 0xFE] * 50))

        r = _run(root, plan)
        assert r.returncode == 0, r.stderr
        digest = _digest(plan)
        assert any(w.startswith("possible_ebcdic_or_binary:") for w in digest["warnings"])

    def test_comment_only_dfhmdi_end_to_end_no_crash(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "PROG2.cbl").write_text(_COMMENT_ONLY_DFHMDI_SRC, encoding="utf-8")

        r = _run(root, plan)
        assert r.returncode == 0, r.stderr
        digest = _digest(plan)
        assert digest["warnings"] == []

    def test_malformed_root_never_crashes(self, tmp_path):
        # Nonexistent root directory: os.walk yields nothing — still exit 0.
        root = tmp_path / "does-not-exist"
        plan = tmp_path / "plan"
        r = _run(root, plan)
        assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# cobol.json stack-profile registration (additive-only regression check)
# ---------------------------------------------------------------------------

class TestCobolProfileLoad:
    def test_cobol_json_loads_alongside_all_existing_profiles(self):
        profiles = stacklib.load_profiles()
        assert {"web-js-ts", "delphi-vcl", "oracle-plsql", "generic-source", "cobol"} <= set(profiles)

    def test_cobol_screen_source_and_extractors(self):
        # Phase 11 (second release, Tracks B/C/D): crud-matrix/db-objects flipped
        # skip->produce + extract_cobol_data added — was screens-only at Phase 01/4b.
        profiles = stacklib.load_profiles()
        cobol = profiles["cobol"]
        assert cobol["screen_source"] == "cobol-screen"
        assert cobol["extractors"] == ["extract_cobol_screen", "extract_cobol_data"]
        # Self-consistency rule: screen_source != none => screen-list/flow produce.
        assert cobol["artifact_map"]["screen-list"]["action"] == "produce"
        assert cobol["artifact_map"]["screen-flow"]["action"] == "produce"
        assert cobol["artifact_map"]["crud-matrix"]["action"] == "produce"
        assert cobol["artifact_map"]["db-objects"]["action"] == "produce"

    def test_extract_cobol_extractors_in_allowlist(self):
        assert "extract_cobol_screen" in stacklib.ALLOWED_EXTRACTORS
        assert "extract_cobol_data" in stacklib.ALLOWED_EXTRACTORS

    def test_cobol_screen_and_ui_sniff_valid_screen_sources(self):
        assert "cobol-screen" in stacklib._VALID_SCREEN_SOURCES
        assert "ui-sniff" in stacklib._VALID_SCREEN_SOURCES


class TestDetectStackProfileCobol:
    def _run_detect(self, root: Path) -> dict:
        r = subprocess.run(
            [sys.executable, str(DETECT_SCRIPT), "--root", str(root)],
            capture_output=True, text=True, timeout=60, cwd=str(root),
        )
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)

    def test_cobol_tree_recommends_cobol(self, tmp_path):
        (tmp_path / "PROG1.cbl").write_text(_SCREEN_SECTION_SRC, encoding="utf-8")
        (tmp_path / "MAP1.bms").write_text(_BMS_SRC, encoding="utf-8")
        out = self._run_detect(tmp_path)
        assert out["recommended_profile"] == "cobol"
        assert out["detected_language_heading"] == "COBOL"

    def test_web_tree_unchanged(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"x"}', encoding="utf-8")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "index.ts").write_text("export const x = 1;", encoding="utf-8")
        out = self._run_detect(tmp_path)
        assert out["recommended_profile"] == "web-js-ts"

    def test_delphi_tree_unchanged(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "Main.dpr").write_text("program Main; begin end.")
        (tmp_path / "src" / "Unit1.pas").write_text("unit Unit1; interface implementation end.")
        (tmp_path / "App.dproj").write_text("<Project></Project>")
        out = self._run_detect(tmp_path)
        assert out["recommended_profile"] == "delphi-vcl"
