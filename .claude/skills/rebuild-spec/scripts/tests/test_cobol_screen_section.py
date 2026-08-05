"""Tests for `_cobol_screen_section_lib.py` (Phase 02) + router integration.

Primary fixtures are anonymized real AcuCOBOL samples (Validation Session 1
decision: real over synthetic, for fidelity to the actual SCREEN SECTION
shape) — see `fixtures/cobol_real_sample/README.md`. A few small synthetic
snippets cover edge cases the real samples don't reach (path-escape via
symlink, an empty copybook, one paragraph displaying two records) per the
phase file's "may ALSO add synthetic fixtures" allowance.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "extract_cobol_screen.py"
REAL_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "cobol_real_sample"

sys.path.insert(0, str(SCRIPTS_DIR))
import _cobol_screen_section_lib as lib  # noqa: E402
import _cobol_screen_section_parse_lib as parselib  # noqa: E402


def _run(root: Path, plan_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--plan-dir", str(plan_dir)],
        capture_output=True, text=True, timeout=60,
    )


def _digest(plan_dir: Path) -> dict:
    p = plan_dir / "artifacts" / "_digest_extract_cobol_screen.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _by_screen(screens: list[dict], name: str) -> dict:
    matches = [s for s in screens if s["screen"] == name]
    assert matches, f"{name!r} not in {[s['screen'] for s in screens]}"
    return matches[0]


def _copy_fixture_into(root: Path, *names: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in names:
        (root / name).write_text((REAL_FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")


# ---------------------------------------------------------------------------
# Real fixture: inline_screen.cbl (two inline 01 records, comment-noise,
# PERFORM chain across two SECTIONs, reachability via two different paragraphs)
# ---------------------------------------------------------------------------

class TestInlineScreenRealFixture:
    def test_router_end_to_end_surfaces_both_screens_with_citations(self, tmp_path):
        root = tmp_path / "root"
        _copy_fixture_into(root, "inline_screen.cbl")
        plan = tmp_path / "plan"

        r = _run(root, plan)
        assert r.returncode == 0, r.stderr
        screens = _digest(plan)["screens"]
        assert len(screens) == 2

        menu = _by_screen(screens, "MENU-SCREEN")
        assert menu["kind"] == "screen-section"
        assert menu["reachable"] is True
        assert menu["unverified"] is False
        assert menu["entry_citation"] == "inline_screen.cbl:44"  # DISPLAY MENU-SCREEN.

        item = _by_screen(screens, "ITEM-ENQUIRY-SCREEN")
        assert item["reachable"] is True
        assert item["entry_citation"] == "inline_screen.cbl:54"  # DISPLAY ITEM-ENQUIRY-SCREEN.

    def test_perform_chain_yields_form_to_form_flow_edge_like_delphi_shape(self, tmp_path):
        root = tmp_path / "root"
        _copy_fixture_into(root, "inline_screen.cbl")
        plan = tmp_path / "plan"
        _run(root, plan)
        screens = _digest(plan)["screens"]

        menu = _by_screen(screens, "MENU-SCREEN")
        assert menu["flow_edges"] == [{
            "from": "MENU-SCREEN",
            "to": "ITEM-ENQUIRY-SCREEN",
            "kind": "performs",
            "file": "inline_screen.cbl",
            "line": 47,  # PERFORM CA000-ITEM-ENQUIRY
        }]
        assert _by_screen(screens, "ITEM-ENQUIRY-SCREEN")["flow_edges"] == []

    def test_comment_noise_disabled_menu_option_creates_no_extra_screen(self, tmp_path):
        root = tmp_path / "root"
        _copy_fixture_into(root, "inline_screen.cbl")
        plan = tmp_path / "plan"
        _run(root, plan)
        names = {s["screen"] for s in _digest(plan)["screens"]}
        assert names == {"MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"}


# ---------------------------------------------------------------------------
# Real fixture: copy_split_screen.cbl (COPY-only SCREEN SECTION) +
# STOCKHDR.CRT (resolvable) + LEGACYFOOTER.CRT (deliberately absent)
# ---------------------------------------------------------------------------

class TestCopySplitScreenRealFixture:
    def test_router_end_to_end_resolvable_copy_resolves_unresolvable_stays_unverified(self, tmp_path):
        # The router passes `root=` to `ScreenSectionLib` (fixed after the Wave 2 review --
        # was previously a known limitation where COPY resolution always degraded in a
        # router-driven run). STOCKHDR.CRT resolves for real here; LEGACYFOOTER.CRT stays
        # unverified since it genuinely doesn't exist anywhere in the tree.
        root = tmp_path / "root"
        _copy_fixture_into(root, "copy_split_screen.cbl", "STOCKHDR.CRT")
        plan = tmp_path / "plan"

        r = _run(root, plan)
        assert r.returncode == 0, r.stderr
        screens = _digest(plan)["screens"]
        by_name = {s["screen"]: s for s in screens}
        assert set(by_name) == {"S-HDR", "LEGACYFOOTER"}

        s_hdr = by_name["S-HDR"]
        assert s_hdr["unverified"] is False
        assert s_hdr["reachable"] is True
        assert s_hdr["raw"]["copy_target"] == "STOCKHDR.CRT"

        assert by_name["LEGACYFOOTER"]["unverified"] is True
        assert by_name["LEGACYFOOTER"]["reachable"] is False

    def test_unresolvable_copy_cites_the_copy_statement_never_a_crash(self, tmp_path):
        root = tmp_path / "root"
        _copy_fixture_into(root, "copy_split_screen.cbl", "STOCKHDR.CRT")
        plan = tmp_path / "plan"
        r = _run(root, plan)
        assert r.returncode == 0, r.stderr
        legacy = _by_screen(_digest(plan)["screens"], "LEGACYFOOTER")
        assert legacy["unverified"] is True
        assert legacy["entry_citation"] == "copy_split_screen.cbl:20"  # COPY LEGACYFOOTER.CRT.
        assert legacy["raw"]["copy_target"] == "LEGACYFOOTER.CRT"

    def test_resolvable_copy_resolves_when_root_is_supplied_directly(self, tmp_path):
        root = tmp_path / "root"
        _copy_fixture_into(root, "copy_split_screen.cbl", "STOCKHDR.CRT")
        text = (root / "copy_split_screen.cbl").read_text(encoding="utf-8")

        section_lib = lib.ScreenSectionLib(root=root)
        section_lib.feed("copy_split_screen.cbl", text.splitlines())
        recs = section_lib.finalize()
        by_name = {r["screen"]: r for r in recs}
        assert set(by_name) == {"S-HDR", "LEGACYFOOTER"}

        s_hdr = by_name["S-HDR"]
        assert s_hdr["unverified"] is False
        assert s_hdr["reachable"] is True
        assert s_hdr["entry_citation"] == "copy_split_screen.cbl:25"  # DISPLAY S-HDR.
        assert s_hdr["raw"]["copy_target"] == "STOCKHDR.CRT"

        assert by_name["LEGACYFOOTER"]["unverified"] is True


# ---------------------------------------------------------------------------
# Synthetic edge cases beyond the 3 real fixtures
# ---------------------------------------------------------------------------

class TestCopyPathContainmentSynthetic:
    def test_symlinked_copy_target_escaping_root_is_treated_as_unresolved(self, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "SECRET.CRT"
        secret.write_text("       01  SECRET-REC.\n", encoding="utf-8")

        root = tmp_path / "root"
        root.mkdir()
        (root / "SECRET.CRT").symlink_to(secret)

        src = (
            "       SCREEN SECTION.\n"
            "       COPY SECRET.CRT.\n"
            "       PROCEDURE DIVISION.\n"
            "           STOP RUN.\n"
        )
        section_lib = lib.ScreenSectionLib(root=root)
        section_lib.feed("escape1.cbl", src.splitlines())
        recs = section_lib.finalize()
        assert len(recs) == 1
        assert recs[0]["unverified"] is True
        assert recs[0]["reachable"] is False
        assert recs[0]["raw"]["reason"] == "unresolved_or_escaped"


class TestEmptyCopybookSynthetic:
    def test_copybook_resolves_but_has_no_01_record_degrades_gracefully(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        (root / "EMPTY.CRT").write_text("      * just a comment, no 01 record\n", encoding="utf-8")
        src = (
            "       SCREEN SECTION.\n"
            "       COPY EMPTY.CRT.\n"
            "       PROCEDURE DIVISION.\n"
            "           STOP RUN.\n"
        )
        section_lib = lib.ScreenSectionLib(root=root)
        section_lib.feed("prog.cbl", src.splitlines())
        recs = section_lib.finalize()
        assert len(recs) == 1
        assert recs[0]["raw"]["reason"] == "no_01_record_in_copybook"
        assert recs[0]["unverified"] is True


class TestMultiRecordPerParagraphSynthetic:
    def test_one_paragraph_displaying_two_records_fans_out_flow_edges(self, tmp_path):
        # Phase file "Edge handling": multi-record-per-paragraph -> one flow
        # node (the PERFORM), multiple screen refs (both records that
        # paragraph displays get an outgoing edge to the PERFORM's target).
        src = (
            "       IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. MULTI1.\n"
            "       DATA DIVISION.\n"
            "       SCREEN SECTION.\n"
            "       01  REC-A.\n"
            "           03  LINE 1 COLUMN 1 VALUE \"A\".\n"
            "       01  REC-B.\n"
            "           03  LINE 2 COLUMN 1 VALUE \"B\".\n"
            "       01  REC-C.\n"
            "           03  LINE 3 COLUMN 1 VALUE \"C\".\n"
            "       PROCEDURE DIVISION.\n"
            "       AA010.\n"
            "           DISPLAY REC-A.\n"
            "           DISPLAY REC-B.\n"
            "           PERFORM BB010.\n"
            "           STOP RUN.\n"
            "       BB010.\n"
            "           DISPLAY REC-C.\n"
        )
        section_lib = lib.ScreenSectionLib()
        section_lib.feed("multi.cbl", src.splitlines())
        recs = section_lib.finalize()
        by_name = {r["screen"]: r for r in recs}
        assert set(by_name) == {"REC-A", "REC-B", "REC-C"}
        assert by_name["REC-A"]["reachable"] is True
        assert by_name["REC-B"]["reachable"] is True

        edge_pairs = {(e["from"], e["to"]) for r in recs for e in r["flow_edges"]}
        assert edge_pairs == {("REC-A", "REC-C"), ("REC-B", "REC-C")}


class TestNoScreenSectionFileYieldsNoScreens:
    def test_feed_without_screen_section_returns_empty(self):
        section_lib = lib.ScreenSectionLib()
        section_lib.feed("plain.cbl", [
            "       IDENTIFICATION DIVISION.",
            "       PROCEDURE DIVISION.",
            "           STOP RUN.",
        ])
        assert section_lib.finalize() == []


# ---------------------------------------------------------------------------
# Direct unit coverage of the pure parse-lib functions against the real
# fixture text (documents/locks the hand-traced boundary math).
# ---------------------------------------------------------------------------

class TestParseLibDirectOnRealFixture:
    def test_screen_section_bounds_span_both_01_records(self):
        lines = (REAL_FIXTURES / "inline_screen.cbl").read_text(encoding="utf-8").splitlines()
        start, end = parselib.find_screen_section_bounds(lines)
        records = parselib.collect_inline_records(lines, start, end)
        assert [name for name, _ in records] == ["MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"]

    def test_copy_statements_collected_in_order(self):
        lines = (REAL_FIXTURES / "copy_split_screen.cbl").read_text(encoding="utf-8").splitlines()
        start, end = parselib.find_screen_section_bounds(lines)
        copies = parselib.collect_copy_statements(lines, start, end)
        assert [token for token, _ in copies] == ["STOCKHDR.CRT", "LEGACYFOOTER.CRT"]


# ---------------------------------------------------------------------------
# C3 — ReDoS in `_HEADER_RE`: golden-set (byte-identical header detection
# before/after the regex rewrite) + linear-time timing assert.
# ---------------------------------------------------------------------------

class TestHeaderRegexGoldenSet:
    """Locks the exact header shapes `find_blocks` produces on both real fixtures.
    Any future `_HEADER_RE` edit that drifts from these values fails loudly here,
    satisfying the phase file's "byte-identical before/after" countermove."""

    def test_inline_screen_headers_unchanged(self):
        lines = (REAL_FIXTURES / "inline_screen.cbl").read_text(encoding="utf-8").splitlines()
        proc_start = parselib.find_procedure_division_start(lines)
        assert parselib.find_blocks(lines, proc_start) == [
            ("AA000-MAIN", True, 36),
            ("AA000-INIT", False, 37),
            ("BA000-SHOW-MENU", True, 41),
            ("BA010", False, 42),
            ("CA000-ITEM-ENQUIRY", True, 51),
            ("CA010", False, 52),
        ]

    def test_copy_split_screen_headers_unchanged(self):
        lines = (REAL_FIXTURES / "copy_split_screen.cbl").read_text(encoding="utf-8").splitlines()
        proc_start = parselib.find_procedure_division_start(lines)
        assert parselib.find_blocks(lines, proc_start) == [
            ("AA000-MAIN", True, 22),
            ("AA010", False, 23),
        ]

    def test_statement_lines_still_never_match_as_headers(self):
        # Non-header PROCEDURE DIVISION statements from the real fixtures must
        # continue to be rejected by the rewritten regex (no false positives).
        for line in (
            "              PERFORM BA000-SHOW-MENU.",
            "              STOP RUN.",
            "              DISPLAY MENU-SCREEN.",
            "              ACCEPT MENU-SCREEN.",
            '            IF WS-OPTION = "1" OR "2"',
            "                    GO TO BA010.",
        ):
            assert parselib._HEADER_RE.match(line) is None, line


class TestHeaderRegexReDoSTiming:
    """C3 repro: a header-position line with a large trailing-whitespace run and
    no terminal `.` used to take ~2s (O(n^2)) on 40k spaces; must now be linear."""

    def test_40k_trailing_spaces_no_terminal_period_is_fast_and_does_not_match(self):
        line = "X" + " " * 40_000
        start = time.perf_counter()
        m = parselib._HEADER_RE.match(line)
        elapsed = time.perf_counter() - start
        assert m is None  # no terminal `.` -> correctly not a header
        assert elapsed < 0.1, f"O(n^2) regression: {elapsed:.3f}s"

    def test_40k_trailing_spaces_with_section_keyword_still_fast(self):
        # Same pathological whitespace shape but with the literal SECTION keyword
        # present far into the run and still no terminal `.` -- exercises the
        # branch that has to locate the literal before giving up.
        line = "X" + " " * 20_000 + "SECTION" + " " * 20_000
        start = time.perf_counter()
        m = parselib._HEADER_RE.match(line)
        elapsed = time.perf_counter() - start
        assert m is None
        assert elapsed < 0.1, f"O(n^2) regression: {elapsed:.3f}s"


# ---------------------------------------------------------------------------
# C4 — unbounded flow_edges cross-product: N=400 reachable screens/side across
# a single PERFORM must yield a bounded, deduped `flow_edges` count + warning.
# ---------------------------------------------------------------------------

def _fanout_src(n: int) -> str:
    a_records = "".join(f"       01  REC-A{i}.\n           03  LINE 1 COLUMN 1 VALUE \"A\".\n" for i in range(n))
    b_records = "".join(f"       01  REC-B{i}.\n           03  LINE 1 COLUMN 1 VALUE \"B\".\n" for i in range(n))
    a_displays = "".join(f"           DISPLAY REC-A{i}.\n" for i in range(n))
    b_displays = "".join(f"           DISPLAY REC-B{i}.\n" for i in range(n))
    return (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. FANOUT.\n"
        "       DATA DIVISION.\n"
        "       SCREEN SECTION.\n"
        + a_records + b_records +
        "       PROCEDURE DIVISION.\n"
        "       AA010.\n"
        + a_displays +
        "           PERFORM BB010.\n"
        "           STOP RUN.\n"
        "       BB010.\n"
        + b_displays
    )


class TestFlowEdgesCapC4:
    def test_400_per_side_perform_fanout_yields_bounded_deduped_flow_edges(self):
        section_lib = lib.ScreenSectionLib()
        section_lib.feed("fanout.cbl", _fanout_src(400).splitlines())
        recs = section_lib.finalize()
        assert len(recs) == 800  # 400 A + 400 B screens, none fabricated/erased

        total_edges = sum(len(r["flow_edges"]) for r in recs)
        assert 0 < total_edges <= parselib._MAX_FLOW_EDGES_PER_FILE
        # dedup: every kept edge is unique on (from, to, line)
        keys = [(e["from"], e["to"], e["line"]) for r in recs for e in r["flow_edges"]]
        assert len(keys) == len(set(keys))

        truncated = [r for r in recs if r["raw"].get("flow_edges_truncated")]
        assert truncated, "expected at least one record flagged flow_edges_truncated"
        assert truncated[0]["raw"]["flow_edges_truncated"] == "fanout.cbl"

    def test_5000_per_side_fanout_stays_compute_bounded_not_just_output_bounded(self):
        # C4 hardening: pre-hardening, the S x D cross-product was fully materialized
        # (~25M candidate pairs at N=5000) before slicing to the cap -- output was
        # bounded but wall-clock scaled O(n^2). `_iter_candidate_edges` must now stop
        # generating the instant the cap is hit, so this stays fast regardless of N.
        section_lib = lib.ScreenSectionLib()
        section_lib.feed("fanout.cbl", _fanout_src(5000).splitlines())

        start = time.perf_counter()
        recs = section_lib.finalize()
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"compute-time regression: {elapsed:.3f}s for N=5000 (expected O(cap), not O(n^2))"
        assert len(recs) == 10000  # 5000 A + 5000 B screens, none fabricated/erased

        total_edges = sum(len(r["flow_edges"]) for r in recs)
        assert 0 < total_edges <= parselib._MAX_FLOW_EDGES_PER_FILE
        keys = [(e["from"], e["to"], e["line"]) for r in recs for e in r["flow_edges"]]
        assert len(keys) == len(set(keys))  # dedup semantics unchanged


# ---------------------------------------------------------------------------
# H4 — COPY-resolved read had no byte cap; a COPY target over 10MB must
# degrade to an unverified record with reason "oversized_copybook", never read.
# ---------------------------------------------------------------------------

class TestOversizedCopybookH4:
    def test_copy_target_over_10mb_is_not_read_degrades_to_unverified(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        big = root / "BIGCOPY.CRT"
        with open(big, "wb") as f:
            f.truncate(11 * 1024 * 1024)  # sparse — never actually writes 11MB
        src = (
            "       SCREEN SECTION.\n"
            "       COPY BIGCOPY.CRT.\n"
            "       PROCEDURE DIVISION.\n"
            "           STOP RUN.\n"
        )
        section_lib = lib.ScreenSectionLib(root=root)
        section_lib.feed("prog.cbl", src.splitlines())
        recs = section_lib.finalize()
        assert len(recs) == 1
        assert recs[0]["unverified"] is True
        assert recs[0]["reachable"] is False
        assert recs[0]["raw"]["reason"] == "oversized_copybook"
        assert recs[0]["raw"]["copy_target"] == "BIGCOPY.CRT"
