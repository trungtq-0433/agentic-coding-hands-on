"""Tests for _content_sniff_lib.py + _content_sniff_signals_lib.py (Phase 07,
Track D -- generic content-sniff fallback for ANY unrecognized stack).

Covers: tiering (0/1/2), the menu-loop structural detector, all three
false-positive guards (ACCEPT FROM DATE, fgets-on-non-stdin-stream standing in
for "read() on a socket/file", CICS-embedded DISPLAY), the generic-secret scrub
(fix 7), the per-file byte cap (fix 9), and the aggregate wall-clock deadline
(fix 11).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _content_sniff_lib as sniff_lib  # noqa: E402
import _content_sniff_signals_lib as signals_lib  # noqa: E402


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Tier 0 -- no hit at all
# ---------------------------------------------------------------------------

class TestTier0NoHit:
    def test_pure_batch_code_is_silent(self, tmp_path):
        _write(tmp_path, "batch.py", "total = sum(x * 2 for x in range(100))\nprint(total)\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 0
        assert result["signals"] == []


# ---------------------------------------------------------------------------
# Tier 1 -- single keyword, no structural corroboration
# ---------------------------------------------------------------------------

class TestTier1LoneKeyword:
    def test_lone_input_call_is_tier1(self, tmp_path):
        _write(tmp_path, "greet.py", 'name = input("Enter your name: ")\nprint(f"Hello {name}")\n')
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 1
        assert len(result["signals"]) == 1
        assert result["signals"][0]["family"] == "python_input"
        assert result["signals"][0]["token"] == "input("
        assert result["signals"][0]["structural"] is False
        assert "greet.py:1" in result["signals"][0]["citation"]


# ---------------------------------------------------------------------------
# Tier 2 -- keyword + menu-loop structural corroboration
# ---------------------------------------------------------------------------

class TestTier2MenuLoop:
    def test_c_menu_loop_with_scanf_and_switch_is_tier2(self, tmp_path):
        content = (
            "int choice;\n"
            "while (1) {\n"
            '    printf("1. Add record\\n");\n'
            '    printf("2. Delete record\\n");\n'
            '    printf("3. Exit\\n");\n'
            '    scanf("%d", &choice);\n'
            "    switch (choice) {\n"
            "        case 1: add_record(); break;\n"
            "        case 2: delete_record(); break;\n"
            "        case 3: return 0;\n"
            "    }\n"
            "}\n"
        )
        _write(tmp_path, "menu.c", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 2
        structural = [s for s in result["signals"] if s["structural"]]
        assert len(structural) == 1
        assert structural[0]["family"] == "menu_loop"
        assert "menu.c:2" in structural[0]["citation"]
        # code-vs-comment provenance marker (fix C8).
        assert "[code]" in structural[0]["citation"]
        keyword_families = {s["family"] for s in result["signals"] if not s["structural"]}
        assert "c_stdin" in keyword_families

    def test_gui_toolkit_import_blocks_tier2(self, tmp_path):
        """Same menu-loop shape, but the file also imports a real GUI toolkit --
        Tier 2 must NOT fire (the 'no GUI-toolkit import' clause)."""
        content = (
            "import tkinter\n"
            "while (True):\n"
            '    print("1. Add")\n'
            '    print("2. Quit")\n'
            "    choice = input('> ')\n"
            "    if choice == '1':\n"
            "        pass\n"
            "    elif choice == '2':\n"
            "        break\n"
        )
        _write(tmp_path, "menu_gui.py", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 1
        assert any(s["family"] == "menu_loop" for s in result["signals"])

    def test_c_menu_loop_with_for_loop_is_tier2(self, tmp_path):
        """`for(...)` idiom (not just `while(...)`) must still corroborate."""
        content = (
            "int choice;\n"
            "for (;;) {\n"
            '    printf("1. Add record\\n");\n'
            '    printf("2. Delete record\\n");\n'
            '    scanf("%d", &choice);\n'
            "    switch (choice) {\n"
            "        case 1: break;\n"
            "    }\n"
            "}\n"
        )
        _write(tmp_path, "menu_for.c", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 2


# ---------------------------------------------------------------------------
# False-positive guards
# ---------------------------------------------------------------------------

class TestGuardAcceptFromDate:
    def test_accept_from_date_suppressed(self, tmp_path):
        _write(tmp_path, "clock.cbl", "       ACCEPT WS-CURRENT-DATE FROM DATE.\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 0
        assert result["signals"] == []

    def test_real_accept_is_not_suppressed(self, tmp_path):
        _write(tmp_path, "menu.cbl", "       ACCEPT WS-USER-CHOICE.\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 1
        assert result["signals"][0]["family"] == "cobol_ish"
        assert result["signals"][0]["token"] == "ACCEPT"


class TestGuardSocketOrFileRead:
    """The C stdin family's fgets() is the concrete stand-in for the phase-07
    'read() on a socket/file (not stdin)' guard -- fgets() genuinely takes a
    stream argument that may be a file/socket handle rather than stdin."""

    def test_fgets_on_socket_stream_suppressed(self, tmp_path):
        _write(tmp_path, "reader.c", "char buf[100];\nfgets(buf, 100, socket_fp);\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 0
        assert result["signals"] == []

    def test_fgets_on_stdin_is_not_suppressed(self, tmp_path):
        _write(tmp_path, "reader.c", "char buf[100];\nfgets(buf, 100, stdin);\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 1
        assert result["signals"][0]["token"] == "fgets("


class TestGuardCicsDisplay:
    def test_display_inside_cics_block_suppressed(self, tmp_path):
        content = (
            "       EXEC CICS\n"
            "           SEND MAP('MAP1')\n"
            "       END-EXEC.\n"
            "       DISPLAY 'HELLO'.\n"
        )
        _write(tmp_path, "cics.cbl", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        # EXEC CICS itself still counts as a hit; DISPLAY must be suppressed.
        tokens = {s["token"] for s in result["signals"]}
        assert "DISPLAY" not in tokens
        assert "EXEC CICS" in tokens

    def test_display_without_cics_is_not_suppressed(self, tmp_path):
        _write(tmp_path, "report.cbl", "       DISPLAY 'DAILY REPORT'.\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["signals"][0]["token"] == "DISPLAY"


# ---------------------------------------------------------------------------
# Generic-secret scrub (fix 7) -- must never reach the citation
# ---------------------------------------------------------------------------

class TestGenericSecretScrub:
    def test_cli_short_password_flag_scrubbed_before_citation(self, tmp_path):
        content = 'dialog --title "Login" --password=hunter2secret --menu "Choose:" 20 60 4\n'
        _write(tmp_path, "login.sh", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert len(result["signals"]) == 1
        citation = result["signals"][0]["citation"]
        assert "hunter2secret" not in citation
        assert "<redacted>" in citation

    def test_scrub_generic_secret_unit_cli_short_flag(self):
        scrubbed = signals_lib.scrub_generic_secret("mysql -uroot -pMySecretPw123 < dump.sql")
        assert "MySecretPw123" not in scrubbed
        assert "-p<redacted>" in scrubbed

    def test_scrub_generic_secret_unit_api_key_literal(self):
        scrubbed = signals_lib.scrub_generic_secret('api_key = "sk_live_ABC123DEF456"')
        assert "sk_live_ABC123DEF456" not in scrubbed

    def test_scrub_generic_secret_unit_env_fallback(self):
        scrubbed = signals_lib.scrub_generic_secret(
            'password = os.environ.get("DB_PASSWORD", "fallback_secret_val")'
        )
        assert "fallback_secret_val" not in scrubbed

    def test_scrub_generic_secret_leaves_safe_flags_untouched(self):
        """`-p` prefixed long-flag words unrelated to passwords must survive."""
        line = "run --parallel 4 --port 8080 --profile release"
        assert signals_lib.scrub_generic_secret(line) == line


# ---------------------------------------------------------------------------
# C6 -- widened secret scrub: the 9 realistic shapes the review leaked, plus
# dual-scrub routing (_excerpt() must run BOTH scrub_generic_secret AND
# _sql_parse_lib.scrub_credentials) and a benign-line over-redaction guard.
# ---------------------------------------------------------------------------

class TestC6WidenedSecretShapes:
    """Each of these 9 shapes leaked verbatim before fix C6 (only the CLI
    short `-p<value>` flag was caught). All must come out redacted now."""

    def test_shape1_password_literal(self):
        scrubbed = signals_lib.scrub_generic_secret('password = "hunter2CorrectHorse"')
        assert "hunter2CorrectHorse" not in scrubbed

    def test_shape2_secret_key(self):
        scrubbed = signals_lib.scrub_generic_secret('SECRET_KEY = "django-insecure-abc123XYZ"')
        assert "django-insecure-abc123XYZ" not in scrubbed

    def test_shape3_aws_secret_access_key(self):
        scrubbed = signals_lib.scrub_generic_secret(
            'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
        )
        assert "wJalrXUtnFEMI" not in scrubbed

    def test_shape4_pem_header_block(self):
        line = (
            'PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----'
            '\\nMIIEowIBAAKCAQEAxxxxxxxxxxxxxxxxxxxxxxxx'
            '\\n-----END RSA PRIVATE KEY-----"'
        )
        scrubbed = signals_lib.scrub_generic_secret(line)
        assert "MIIEowIBAAKCAQEAxxxxxxxxxxxxxxxxxxxxxxxx" not in scrubbed
        assert "-----BEGIN RSA PRIVATE KEY-----" in scrubbed  # marker kept

    def test_shape5_bearer_token(self):
        scrubbed = signals_lib.scrub_generic_secret(
            "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.fake.tok"
        )
        assert "eyJhbGciOiJIUzI1NiJ9.fake.tok" not in scrubbed
        assert "Bearer <redacted>" in scrubbed

    def test_shape6_uri_credential(self):
        scrubbed = signals_lib.scrub_generic_secret(
            "postgres://admin:SuperSecretPass1@db.example.com:5432/mydb"
        )
        assert "SuperSecretPass1" not in scrubbed

    def test_shape7_client_secret(self):
        scrubbed = signals_lib.scrub_generic_secret('client_secret = "0oa1b2c3d4e5f6g7h8i9"')
        assert "0oa1b2c3d4e5f6g7h8i9" not in scrubbed

    def test_shape8_cli_long_password_flag(self):
        scrubbed = signals_lib.scrub_generic_secret("--password=CorrectHorseBatteryStaple")
        assert "CorrectHorseBatteryStaple" not in scrubbed

    def test_shape9_colon_delimited_token(self):
        scrubbed = signals_lib.scrub_generic_secret('token: "ghp_1234567890abcdefFAKE"')
        assert "ghp_1234567890abcdefFAKE" not in scrubbed

    def test_benign_lines_pass_through_unchanged(self):
        """Suffix-tolerant keyword matching must not sweep up ordinary
        identifiers that merely contain "secret"/"token" as a substring."""
        assert signals_lib.scrub_generic_secret(
            "secretary_name = 'Jane Doe'"
        ) == "secretary_name = 'Jane Doe'"
        assert signals_lib.scrub_generic_secret(
            "run --parallel 4 --port 8080 --profile release"
        ) == "run --parallel 4 --port 8080 --profile release"

    def test_excerpt_routes_through_both_scrubbers(self):
        """`_excerpt()` must run BOTH scrub_generic_secret AND
        `_sql_parse_lib.scrub_credentials` -- an Oracle `IDENTIFIED BY` shape
        (SQL-only, no api_key/token/secret/password keyword) is invisible to
        `scrub_generic_secret` alone but must still be redacted end to end."""
        line = "GRANT CONNECT IDENTIFIED BY oracle_secret_pw123"
        assert "oracle_secret_pw123" in signals_lib.scrub_generic_secret(line)  # not this scrub's job
        assert "oracle_secret_pw123" not in sniff_lib._excerpt(line)  # but _excerpt covers it


# ---------------------------------------------------------------------------
# Per-file byte cap (fix 9)
# ---------------------------------------------------------------------------

class TestByteCap:
    def test_oversized_file_is_skipped_without_crash(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sniff_lib, "_MAX_FILE_BYTES", 10)
        _write(tmp_path, "big.py", 'name = input("this file is well over the ten byte cap")\n')
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 0
        assert result["signals"] == []


# ---------------------------------------------------------------------------
# Aggregate wall-clock deadline (fix 11)
# ---------------------------------------------------------------------------

class TestAggregateDeadline:
    def test_deadline_returns_partial_verdict_not_hang(self, tmp_path):
        for i in range(5):
            _write(tmp_path, f"file_{i}.py", f'x_{i} = input("prompt {i}")\n')
        result = sniff_lib.sniff_ui(str(tmp_path), deadline_seconds=0.0)
        assert isinstance(result, dict)
        assert "tier" in result and "signals" in result and "summary" in result
        assert "sniff_deadline_reached" in result["summary"]


# ---------------------------------------------------------------------------
# C7 -- intra-file deadline: a single dense file must no longer blow past the
# deadline (original repro: one 8.3MB file took 14.8s against a 0.5s deadline,
# ~30x overrun, because the deadline was only checked between files).
# ---------------------------------------------------------------------------

class TestIntraFileDeadline:
    def test_single_dense_file_bounded_by_deadline_not_30x_overrun(self, tmp_path):
        # Menu-loop-shaped filler on every line -- worst case for the
        # per-candidate window scan -- big enough that a full unbounded scan
        # would run far past the deadline, but still under the 10MB byte cap.
        line = "while (1) { do_thing(); } // kept for reference filler text pad\n"
        _write(tmp_path, "dense.c", line * 140_000)

        deadline_seconds = 0.5
        slack = 2.0  # generous CI-safe slack; still far under the ~30x-overrun shape
        t0 = time.monotonic()
        result = sniff_lib.sniff_ui(str(tmp_path), deadline_seconds=deadline_seconds)
        elapsed = time.monotonic() - t0

        assert elapsed <= deadline_seconds + slack, (
            f"intra-file deadline not honored: {elapsed:.2f}s "
            f"vs {deadline_seconds + slack:.2f}s bound"
        )
        assert "sniff_deadline_reached" in result["summary"]


# ---------------------------------------------------------------------------
# C8 -- comment/prose exclusion: Tier-2 must only ever be reached from a
# code-shaped, non-comment loop-start line.
# ---------------------------------------------------------------------------

class TestCommentExclusionFromTier2:
    def test_commented_out_menu_and_english_comment_do_not_reach_tier2(self, tmp_path):
        """A commented-out fake menu (including a genuine `while (1) {` shape,
        just prefixed with `#`) plus an unrelated real `input()` call must NOT
        corroborate to Tier 2 -- the review's exact repro shape."""
        content = (
            "# kept for reference -- old dialog menu, removed\n"
            "# while (1) {\n"
            '#     print("1. Add record")\n'
            '#     print("2. Delete record")\n'
            "#     choice = input('> ')\n"
            "#     switch(choice) { case 1: break; }\n"
            "# }\n"
            'name = input("Enter name: ")\n'
            "print(f\"Hello {name}\")\n"
        )
        _write(tmp_path, "dead_menu.py", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 1
        assert not any(s["family"] == "menu_loop" for s in result["signals"])

    def test_genuine_uncommented_loop_still_reaches_tier2(self, tmp_path):
        """Sanity companion: the same shape, uncommented, still corroborates."""
        content = (
            "while (1) {\n"
            '    print("1. Add record")\n'
            '    print("2. Delete record")\n'
            "    choice = input('> ')\n"
            "    if choice == '1':\n"
            "        pass\n"
            "    elif choice == '2':\n"
            "        break\n"
            "}\n"
        )
        _write(tmp_path, "live_menu.py", content)
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 2
        structural = [s for s in result["signals"] if s["structural"]]
        assert len(structural) == 1
        assert "[code]" in structural[0]["citation"]


# ---------------------------------------------------------------------------
# Walk discipline -- skip-dirs + citation shape sanity
# ---------------------------------------------------------------------------

class TestWalkDiscipline:
    def test_skip_dirs_not_scanned(self, tmp_path):
        _write(tmp_path, "node_modules/pkg/index.js", 'input("should not be scanned")\n')
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["tier"] == 0
        assert result["signals"] == []

    def test_every_signal_has_file_line_citation(self, tmp_path):
        _write(tmp_path, "shell/login.sh", "whiptail --menu \"pick\" 10 40 3\n")
        result = sniff_lib.sniff_ui(str(tmp_path))
        assert result["signals"], "expected at least one signal"
        for s in result["signals"]:
            path_part = s["citation"].split(":", 1)[0]
            assert path_part  # non-empty path component present
            assert set(s.keys()) >= {"family", "token", "citation", "structural"}
