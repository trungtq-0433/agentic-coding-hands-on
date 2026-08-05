"""Tests for `_cobol_bms_lib.py` + `_cobol_bms_grammar_lib.py` (Phase 03).

Fixtures are SYNTHESIZED (per plan.md Validation Session 1 + this phase's Implementation
Steps step 1): the user's confirmed real target repo uses SCREEN SECTION, not CICS BMS
(zero DFHMSD/DFHMDI/DFHMDF/EXEC CICS hits repo-wide), so no real BMS samples exist to draw
from. These decks are authored from standard CICS BMS assembler-macro conventions: label
col1, macro-name ~col10, operands from col16, continuation char col72 (resumes col16), `*`
comment col1.

Most tests call `BmsLib.feed()`/`finalize()` directly (bypassing the router's dispatch sniff),
mirroring the precedent in `test_extract_cobol_screen.py`'s `TestProcessFileRouting`.

Post-Wave-2-review update: the router's is_bms sniff now ALSO routes a file to this lib if it
merely contains `EXEC CICS SEND/RECEIVE MAP` (via `_cobol_dispatch_lib.matches_exec_cics_map`),
even with no BMS macro line of its own -- the normal real-world split between a map deck and
its calling programs. That fix surfaced a second bug (now also fixed): `_parse_copybook` used
to run unconditionally on every fed file, so an ordinary COBOL program's WORKING-STORAGE
`01 ...-IO.`/`01 ...-O.` records were harvested as fake "symbolic map copybook" candidates,
fabricating phantom screens. `_looks_like_bms_source` now gates copybook harvesting to
`.bms`/`.cpy`-suffixed or macro-shaped files only -- see `TestExecCicsOnlyCallerNoPhantomScreens`.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from _cobol_bms_lib import BmsLib  # noqa: E402
import _cobol_bms_grammar_lib as grammar  # noqa: E402

SCRIPT = SCRIPTS_DIR / "extract_cobol_screen.py"

# ---------------------------------------------------------------------------
# Fixed-column line builders (avoid hand-counting spaces in literal strings)
# ---------------------------------------------------------------------------


def _line(label: str = "", macro: str = "", operand: str = "", cont: str = "") -> str:
    """Build one fixed-column statement line: label cols1-8, macro cols10-15, operand col16+.

    A real BMS/HLASM operation field is always followed by at least one blank before the
    operand -- assemblers tokenize on that separator, not on column position alone. Every
    macro name this suite uses (DFHMSD/DFHMDI/DFHMDF) is exactly 6 chars, which previously
    filled the `{macro:<6}` field with zero padding, butting the operand directly against
    the macro name with no separator (e.g. "DFHMDISIZE=(24,80)"). That's unrealistic BMS
    source AND it silently defeated `_cobol_dispatch_lib.matches_bms_macro()` -- the
    anchored, non-substring regex the router itself relies on to route a `.cbl` file
    containing raw embedded macros without a `.bms` extension -- since that regex requires
    a whitespace/comma/EOL boundary right after the macro token. Insert the missing
    separator (harmless to the grammar tokenizer, whose `_operand_chunk` already
    `.strip()`s each split operand) so every fixture built here is dispatch-sniff-real too."""
    sep = " " if operand and not operand[:1] in (" ", "\t") else ""
    text = f"{label:<8} {macro:<6}{sep}{operand}"
    if cont:
        text = text[:71].ljust(71) + cont
    return text


def _cont_line(operand: str, cont: str = "") -> str:
    """Build a continuation line: cols1-15 blank, operand resumes at col16."""
    text = " " * 15 + operand
    if cont:
        text = text[:71].ljust(71) + cont
    return text


# ---------------------------------------------------------------------------
# Flat BMS deck: mapset + one map + fields, all cited
# ---------------------------------------------------------------------------


class TestFlatBmsDeck:
    def test_map_becomes_screen_with_cited_fields(self):
        lib = BmsLib()
        lib.feed("MAP1.bms", [
            _line("MAPSET1", "DFHMSD", "TYPE=&SYSPARM,MODE=INOUT,LANG=COBOL"),
            _line("MAP1", "DFHMDI", "SIZE=(24,80),LINE=1,COLUMN=1"),
            _line("FIELDA", "DFHMDF", "POS=(1,1),LENGTH=10,ATTRB=(NORM),INITIAL='NAME:'"),
            _line("FIELDB", "DFHMDF", "POS=(1,20),LENGTH=20,ATTRB=(UNPROT)"),
        ])
        screens = lib.finalize()
        assert len(screens) == 1
        scr = screens[0]
        assert scr["screen"] == "MAP1"
        assert scr["kind"] == "cics-bms"
        assert scr["raw"]["mapset"] == "MAPSET1"

        fields = {f["name"]: f for f in scr["raw"]["fields"]}
        assert set(fields) == {"FIELDA", "FIELDB"}
        assert fields["FIELDA"]["pos"] == "(1,1)"
        assert fields["FIELDA"]["length"] == "10"
        assert fields["FIELDA"]["attrb"] == "(NORM)"
        assert fields["FIELDA"]["initial"] == "'NAME:'"
        assert fields["FIELDA"]["citation"] == "MAP1.bms:3"
        assert fields["FIELDB"]["pos"] == "(1,20)"
        assert fields["FIELDB"]["length"] == "20"
        # MAPSET->source index is actually consumed: mapset def site is cited too.
        assert scr["raw"]["mapset_citation"] == "MAP1.bms:1"

        # Not referenced by any EXEC CICS -> unreached, entry cited to the DFHMDI def site.
        assert scr["reachable"] is False
        assert scr["unverified"] is True
        assert scr["entry_citation"] == "MAP1.bms:2"

    def test_mapset_name_indexed_by_dfhmsd_label_not_filename(self):
        # File is named ODD_NAME.bms but the MAPSET label inside is MYMAPSET -- the index
        # must key off the DFHMSD label, never the filename (plan's core MAPSET risk).
        lib = BmsLib()
        lib.feed("ODD_NAME.bms", [
            _line("MYMAPSET", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAPX", "DFHMDI", "SIZE=(24,80)"),
            _line("F1", "DFHMDF", "POS=(1,1),LENGTH=4,ATTRB=(NORM)"),
        ])
        screens = lib.finalize()
        assert screens[0]["raw"]["mapset"] == "MYMAPSET"


# ---------------------------------------------------------------------------
# Continuation-line map: col72 continuation reassembly
# ---------------------------------------------------------------------------


class TestContinuation:
    def test_col72_continuation_reassembles_operand(self):
        operand = "POS=(1,1),LENGTH=100,ATTRB=(NORM,BRT),COLOR=BLUE,INITIAL='HELLO WORLD'"
        first, rest = operand[:40], operand[40:]
        lib = BmsLib()
        lib.feed("MAP2.bms", [
            _line("MAPSET2", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP2", "DFHMDI", "SIZE=(24,80)"),
            _line("FIELDA", "DFHMDF", first, cont="X"),
            _cont_line(rest),
        ])
        screens = lib.finalize()
        field = screens[0]["raw"]["fields"][0]
        assert field["pos"] == "(1,1)"
        assert field["length"] == "100"
        assert field["attrb"] == "(NORM,BRT)"
        assert field["color"] == "BLUE"
        assert field["initial"] == "'HELLO WORLD'"


# ---------------------------------------------------------------------------
# Conditional-assembly deck: two mutually-exclusive DFHMDI branches
# ---------------------------------------------------------------------------


class TestConditionalAssemblyGuard:
    def test_fields_inside_conditional_span_are_dropped_not_merged(self):
        lib = BmsLib()
        lib.feed("MAP3.bms", [
            _line("MAPSET3", "DFHMSD", "TYPE=&SYSPARM"),                    # line 1
            _line("", "AIF", "(&VERSION EQ 1).OLDMAP"),                     # line 2
            _line("MAP3", "DFHMDI", "SIZE=(24,80),LINE=1,COLUMN=1"),        # line 3 (branch A)
            _line("FLDA", "DFHMDF", "POS=(1,1),LENGTH=5,ATTRB=(NORM)"),     # line 4 -- excluded
            _line("", "AGO", ".ENDMAP"),                                     # line 5
            _line(".OLDMAP", "ANOP", ""),                                   # line 6
            _line("MAP3", "DFHMDI", "SIZE=(24,80),LINE=1,COLUMN=1"),        # line 7 (branch B)
            _line("FLDB", "DFHMDF", "POS=(1,1),LENGTH=8,ATTRB=(NORM)"),     # line 8 -- excluded
            _line(".ENDMAP", "ANOP", ""),                                   # line 9
        ])
        screens = lib.finalize()
        assert len(screens) == 1  # both branches share the same map name -- ONE screen
        scr = screens[0]
        assert scr["screen"] == "MAP3"
        # Neither exclusive branch's field survives -- no fabricated combined geometry.
        assert scr["raw"]["fields"] == []
        assert scr["raw"]["manual_review"] is True
        assert "excluded" in scr["raw"]["note"]
        assert scr["unverified"] is True

    def test_field_outside_any_span_in_a_conditional_file_still_emitted(self):
        # A field textually outside the AIF..target span in an otherwise-conditional file
        # must still be emitted (only in-span fields are dropped, not the whole file).
        lib = BmsLib()
        lib.feed("MAP4.bms", [
            _line("MAPSET4", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP4", "DFHMDI", "SIZE=(24,80)"),
            _line("FLDSAFE", "DFHMDF", "POS=(1,1),LENGTH=4,ATTRB=(NORM)"),
            _line("", "AIF", "(&V EQ 1).SKIP"),
            _line("FLDCOND", "DFHMDF", "POS=(2,1),LENGTH=4,ATTRB=(NORM)"),
            _line(".SKIP", "ANOP", ""),
        ])
        screens = lib.finalize()
        names = {f["name"] for f in screens[0]["raw"]["fields"]}
        assert names == {"FLDSAFE"}
        assert screens[0]["raw"]["manual_review"] is True


# ---------------------------------------------------------------------------
# Regression (C5): INITIAL scrub was a structural no-op -- `_CREDENTIAL_RE`
# (PASSWORD=/PWD=) can never match `opnds["INITIAL"]` because the operand parser has
# already stripped the `INITIAL=` prefix by the time the value reaches the scrub. Fix
# scrubs by shape (any non-trivial opaque literal), not by keyword.
# ---------------------------------------------------------------------------


class TestInitialShapeScrub:
    def test_prefixed_secret_shape_is_redacted_and_flagged(self):
        # No ATTRB clause: keeping the operand within the fixed-column 16-71 window
        # avoids an accidental non-blank char landing at col 72 (which the tokenizer
        # would misread as a real continuation flag -- see TestContinuation precedent).
        lib = BmsLib()
        lib.feed("MAP6.bms", [
            _line("MAPSET6", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP6", "DFHMDI", "SIZE=(24,80)"),
            _line("FIELDA", "DFHMDF", "POS=(1,1),LENGTH=20,INITIAL='sk-ant-FAKESECRET123'"),
        ])
        field = lib.finalize()[0]["raw"]["fields"][0]
        assert "sk-ant-FAKESECRET123" not in field["initial"]
        assert field["initial"] == "'<redacted>'"
        assert field["manual_review"] is True

    def test_bare_dictionary_word_secret_is_redacted_and_flagged(self):
        # "hunter2" has no recognizable prefix and no KEY=VALUE shape -- a bare secret
        # that a keyword/prefix-only scrub would miss entirely. Shape-based redaction
        # must still catch it: non-trivial, no space, no trailing-colon label shape.
        lib = BmsLib()
        lib.feed("MAP7.bms", [
            _line("MAPSET7", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP7", "DFHMDI", "SIZE=(24,80)"),
            _line("FIELDB", "DFHMDF", "POS=(1,1),LENGTH=10,ATTRB=(NORM),INITIAL='hunter2'"),
        ])
        field = lib.finalize()[0]["raw"]["fields"][0]
        assert "hunter2" not in field["initial"]
        assert field["initial"] == "'<redacted>'"
        assert field["manual_review"] is True

    def test_benign_prose_label_survives_unredacted(self):
        # A widened heuristic must not eat ordinary screen labels: multi-word prose with
        # spaces (and a trailing colon, a common label convention) is NOT secret-shaped.
        # No ATTRB clause: keeps the operand within the fixed-column 16-71 window (see
        # note in test_prefixed_secret_shape_is_redacted_and_flagged above).
        lib = BmsLib()
        lib.feed("MAP8.bms", [
            _line("MAPSET8", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP8", "DFHMDI", "SIZE=(24,80)"),
            _line("FIELDC", "DFHMDF", "POS=(1,1),LENGTH=30,INITIAL='Enter customer name:'"),
        ])
        field = lib.finalize()[0]["raw"]["fields"][0]
        assert field["initial"] == "'Enter customer name:'"
        assert field["manual_review"] is False


# ---------------------------------------------------------------------------
# 2-file join: COBOL program with EXEC CICS SEND/RECEIVE MAP
# ---------------------------------------------------------------------------


class TestExecCicsJoin:
    def test_send_map_resolves_reachability_and_entry_citation(self):
        lib = BmsLib()
        lib.feed("MAP1.bms", [
            _line("MAPSET1", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP1", "DFHMDI", "SIZE=(24,80)"),
            _line("FIELDA", "DFHMDF", "POS=(1,1),LENGTH=10,ATTRB=(NORM)"),
        ])
        lib.feed("PROG1.cbl", [
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. PROG1.",
            "       PROCEDURE DIVISION.",
            "           EXEC CICS SEND MAP('MAP1') MAPSET('MAPSET1') END-EXEC",
            "           STOP RUN.",
        ])
        screens = lib.finalize()
        assert len(screens) == 1
        scr = screens[0]
        assert scr["reachable"] is True
        assert scr["unverified"] is False
        assert scr["entry_citation"] == "PROG1.cbl:4"
        assert scr["flow_edges"] == ["PROG1.cbl:4"]

    def test_receive_map_multiline_exec_block_also_resolves(self):
        lib = BmsLib()
        lib.feed("MAP5.bms", [
            _line("MAPSET5", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP5", "DFHMDI", "SIZE=(24,80)"),
            _line("F1", "DFHMDF", "POS=(1,1),LENGTH=4,ATTRB=(NORM)"),
        ])
        lib.feed("PROG5.cbl", [
            "       PROCEDURE DIVISION.",
            "           EXEC CICS RECEIVE",
            "               MAP('MAP5')",
            "               MAPSET('MAPSET5')",
            "           END-EXEC",
            "           STOP RUN.",
        ])
        screens = lib.finalize()
        assert screens[0]["reachable"] is True
        assert screens[0]["entry_citation"] == "PROG5.cbl:2"


# ---------------------------------------------------------------------------
# Mapset referenced but defined nowhere -> WARN, not a silent skip
# ---------------------------------------------------------------------------


class TestMapsetUndefined:
    def test_undefined_map_reference_surfaces_warn_screen(self):
        lib = BmsLib()
        lib.feed("PROG9.cbl", [
            "       PROCEDURE DIVISION.",
            "           EXEC CICS SEND MAP('GHOST') MAPSET('NOWHERE') END-EXEC",
            "           STOP RUN.",
        ])
        screens = lib.finalize()
        assert len(screens) == 1
        scr = screens[0]
        assert scr["screen"] == "GHOST"
        assert scr["reachable"] is True
        assert scr["unverified"] is True
        assert scr["raw"]["warning"] == "mapset_undefined"
        assert scr["entry_citation"] == "PROG9.cbl:2"


# ---------------------------------------------------------------------------
# Symbolic-copybook-only case: no .bms source, only a generated symbolic map copybook
# ---------------------------------------------------------------------------


class TestCopybookOnly:
    def test_copybook_only_map_surfaces_unverified_and_cited(self):
        lib = BmsLib()
        lib.feed("MAP9.cpy", [
            "      * BMS-generated symbolic map for MAP9 -- no .bms source in this repo",
            "       01  MAP9I.",
            "           05  FIELDAI PIC X(10).",
        ])
        screens = lib.finalize()
        assert len(screens) == 1
        scr = screens[0]
        assert scr["screen"] == "MAP9"
        assert scr["unverified"] is True
        assert scr["raw"]["fields"] == []
        assert "copybook" in scr["raw"]["note"]
        assert scr["entry_citation"] == "MAP9.cpy:2"
        assert scr["reachable"] is False

    def test_copybook_only_map_referenced_by_program_is_reachable(self):
        lib = BmsLib()
        lib.feed("MAP9.cpy", [
            "       01  MAP9O.",
            "           05  FIELDAO PIC X(10).",
        ])
        lib.feed("PROG9.cbl", [
            "       PROCEDURE DIVISION.",
            "           EXEC CICS SEND MAP('MAP9') MAPSET('MAPSET9') END-EXEC",
        ])
        screens = lib.finalize()
        assert len(screens) == 1
        scr = screens[0]
        assert scr["reachable"] is True
        assert scr["entry_citation"] == "PROG9.cbl:2"
        assert scr["raw"]["copybook_citation"] == "MAP9.cpy:1"
        assert "warning" not in scr["raw"]  # a real (if unrecoverable) source was found


# ---------------------------------------------------------------------------
# Regression: EXEC-CICS-only caller must not fabricate phantom screens from its
# own unrelated WORKING-STORAGE records (Wave 2 review Critical finding).
# ---------------------------------------------------------------------------


class TestExecCicsOnlyCallerNoPhantomScreens:
    def test_ordinary_working_storage_io_records_are_not_harvested_as_maps(self):
        lib = BmsLib()
        lib.feed("PROG.cbl", [
            "       IDENTIFICATION DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01  CUSTOMER-IO.",
            "           05  CUST-NAME PIC X(30).",
            "       01  ERR-MSG-O.",
            "           05  MSG-TEXT PIC X(60).",
            "       PROCEDURE DIVISION.",
            "           EXEC CICS SEND MAP('CUSTMAP') END-EXEC.",
        ])
        screens = lib.finalize()
        names = {s["screen"] for s in screens}
        # Only the real (undefined-mapset) reference surfaces -- no phantom
        # CUSTOMER-I / ERR-MSG- screens fabricated from ordinary data records.
        assert names == {"CUSTMAP"}
        assert screens[0]["raw"]["warning"] == "mapset_undefined"

    def test_router_cli_exec_cics_only_caller_no_phantom_screens(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "PROG.cbl").write_text("\n".join([
            "       IDENTIFICATION DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01  CUSTOMER-IO.",
            "           05  CUST-NAME PIC X(30).",
            "       PROCEDURE DIVISION.",
            "           EXEC CICS SEND MAP('CUSTMAP') END-EXEC.",
        ]) + "\n", encoding="utf-8")

        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), "--plan-dir", str(plan)],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0, r.stderr
        digest = json.loads((plan / "artifacts" / "_digest_extract_cobol_screen.json").read_text())
        names = {s["screen"] for s in digest["screens"]}
        assert names == {"CUSTMAP"}

    def test_cpy_with_exec_cics_and_unrelated_io_record_no_phantom_screen(self):
        """Regression (final evidence-gate inspection, second occurrence of the same
        fabrication class): `.cpy` alone is NOT a reliable "genuine symbolic-map copybook"
        signal -- it's COBOL's generic copybook extension. A `.cpy` file carrying BOTH a
        real `EXEC CICS SEND MAP` reference AND an unrelated `01 ...-O.` WORKING-STORAGE
        record (a procedural/shared copybook, not a BMS-generated map fragment) must not
        have that unrelated record harvested as a phantom screen."""
        lib = BmsLib()
        lib.feed("SHARED.cpy", [
            "       01  RETURN-CODE-O.",
            "           05  RC-VALUE PIC X(02).",
            "           EXEC CICS SEND MAP('CUSTMAP') END-EXEC.",
        ])
        screens = lib.finalize()
        names = {s["screen"] for s in screens}
        assert names == {"CUSTMAP"}
        assert screens[0]["raw"]["warning"] == "mapset_undefined"

    def test_pure_symbolic_map_cpy_with_no_exec_cics_still_surfaces(self):
        """A genuine symbolic-map copybook (pure data, no EXEC CICS of its own -- the
        calling program issues EXEC CICS, not the map copybook) must still surface via
        the copybook-only fallback, unaffected by the fix above."""
        lib = BmsLib()
        lib.feed("MAP9.cpy", [
            "      * BMS-generated symbolic map for MAP9 -- no .bms source in this repo",
            "       01  MAP9I.",
            "           05  FIELDAI PIC X(10).",
        ])
        screens = lib.finalize()
        assert {s["screen"] for s in screens} == {"MAP9"}


# ---------------------------------------------------------------------------
# Regression (Phase 10 integration finding): the router's anchored macro-dispatch
# regex must actually fire on `_line()`-built fixtures, not just on `.bms`-suffixed
# files (which bypass the regex via the file-extension short-circuit).
# ---------------------------------------------------------------------------


class TestRouterDispatchSniffCoversLineBuilder:
    def test_line_builder_output_matches_bms_macro_dispatch_regex(self):
        """`_line()` fixtures must be real enough to exercise `matches_bms_macro()` --
        the router's anchored, non-substring dispatch check -- not just the grammar
        tokenizer's fixed-column slicing. A macro name immediately butted against its
        operand with zero separator (unrealistic BMS source) previously passed the
        tokenizer but silently failed the router's dispatch sniff, leaving that
        anchored-regex path with no coverage through real dispatch anywhere."""
        from _cobol_dispatch_lib import matches_bms_macro

        for macro in ("DFHMSD", "DFHMDI", "DFHMDF"):
            line = _line("MAP1", macro, "SIZE=(24,80)")
            assert matches_bms_macro([line]), f"{macro!r} line failed dispatch sniff: {line!r}"


# ---------------------------------------------------------------------------
# Grammar unit tests
# ---------------------------------------------------------------------------


class TestGrammarTokenizer:
    def test_comment_line_skipped(self):
        stmts = grammar.tokenize(["* a comment at col 1", _line("MAP1", "DFHMDI", "SIZE=(24,80)")])
        assert len(stmts) == 1
        assert stmts[0].macro == "DFHMDI"

    def test_split_operands_respects_quotes_and_parens(self):
        opnds = grammar.split_operands("POS=(1,1),INITIAL='A, B (C)',LENGTH=10")
        assert opnds["POS"] == "(1,1)"
        assert opnds["INITIAL"] == "'A, B (C)'"
        assert opnds["LENGTH"] == "10"

    def test_conditional_spans_unresolvable_target_yields_no_span(self):
        stmts = grammar.tokenize([
            _line("", "AIF", "(&V EQ 1).NOWHERE"),
            _line("F1", "DFHMDF", "POS=(1,1),LENGTH=4,ATTRB=(NORM)"),
        ])
        assert grammar.conditional_spans(stmts) == []


# ---------------------------------------------------------------------------
# End-to-end: router really does wire a sniffable .bms deck through to BmsLib
# ---------------------------------------------------------------------------


class TestRouterIntegration:
    def test_router_cli_produces_bms_screen_from_bms_file(self, tmp_path):
        root = tmp_path / "root"
        plan = tmp_path / "plan"
        root.mkdir()
        (root / "MAP1.bms").write_text("\n".join([
            _line("MAPSET1", "DFHMSD", "TYPE=&SYSPARM"),
            _line("MAP1", "DFHMDI", "SIZE=(24,80)"),
            _line("FIELDA", "DFHMDF", "POS=(1,1),LENGTH=10,ATTRB=(NORM)"),
        ]) + "\n", encoding="utf-8")

        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), "--plan-dir", str(plan)],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0, r.stderr
        digest = json.loads((plan / "artifacts" / "_digest_extract_cobol_screen.json").read_text())
        bms_screens = [s for s in digest["screens"] if s["kind"] == "cics-bms"]
        assert len(bms_screens) == 1
        assert bms_screens[0]["screen"] == "MAP1"
        assert bms_screens[0]["raw"]["fields"][0]["name"] == "FIELDA"
