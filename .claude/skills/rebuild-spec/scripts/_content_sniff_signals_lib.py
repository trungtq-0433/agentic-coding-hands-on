#!/usr/bin/env python3
"""Signal-family keyword table, false-positive guard predicates, generic-secret
scrub, and the menu-loop structural detector for Track D content-sniffing
(Phase 07, phase-07-content-sniff-library.md).

Secret scrub here is independent of `_sql_parse_lib.scrub_credentials`
(SQL/connection-string shaped): CLI password flags, api_key/token/secret/
password literal assignments, Bearer tokens, PEM blocks, URI credentials,
env-var-fallback defaults (fix 7 / fix C6) -- the non-SQL shapes Track D's
targets carry. The orchestrator routes every citation through BOTH scrubs.

Stdlib only.
"""
from __future__ import annotations

import re
from typing import NamedTuple


class FamilyPattern(NamedTuple):
    family: str
    token: str
    regex: re.Pattern


# Signal families (v1 -- don't invent more, per phase-07 spec).
SIGNAL_FAMILIES: list[FamilyPattern] = [
    FamilyPattern("c_stdin", "scanf(", re.compile(r"\bscanf\s*\(")),
    FamilyPattern("c_stdin", "gets(", re.compile(r"\bgets\s*\(")),
    FamilyPattern("c_stdin", "fgets(", re.compile(r"\bfgets\s*\(")),
    FamilyPattern("python_input", "input(", re.compile(r"\binput\s*\(")),
    FamilyPattern("perl_stdin", "<STDIN>", re.compile(r"<STDIN>")),
    FamilyPattern("perl_stdin", "CGI.pm", re.compile(r"\bCGI\.pm\b")),
    FamilyPattern("java_scanner", "Scanner(System.in)", re.compile(r"Scanner\s*\(\s*System\.in\s*\)")),
    FamilyPattern("vb6_inputbox", "InputBox", re.compile(r"\bInputBox\b")),
    FamilyPattern("tui", "curses", re.compile(r"\bn?curses\b", re.IGNORECASE)),
    FamilyPattern("tui", "npyscreen", re.compile(r"\bnpyscreen\b")),
    FamilyPattern("tui", "urwid", re.compile(r"\burwid\b")),
    FamilyPattern("tui", "Textual", re.compile(r"\bTextual\b")),
    FamilyPattern("shell_dialog", "dialog", re.compile(r"\bdialog\b")),
    FamilyPattern("shell_dialog", "whiptail", re.compile(r"\bwhiptail\b")),
    FamilyPattern("shell_dialog", "zenity", re.compile(r"\bzenity\b")),
    FamilyPattern("web_cgi", "<form>", re.compile(r"<form\b", re.IGNORECASE)),
    FamilyPattern("web_cgi", "cgi-bin", re.compile(r"cgi-bin")),
    FamilyPattern("cobol_ish", "ACCEPT", re.compile(r"\bACCEPT\b", re.IGNORECASE)),
    FamilyPattern("cobol_ish", "DISPLAY", re.compile(r"\bDISPLAY\b", re.IGNORECASE)),
    FamilyPattern("cobol_ish", "EXEC CICS", re.compile(r"EXEC\s+CICS", re.IGNORECASE)),
]

# Tokens = actual *captured user input* ops -- required for Tier-2 corroboration.
STDIN_READ_TOKENS = {
    "scanf(", "gets(", "fgets(", "input(", "<STDIN>",
    "Scanner(System.in)", "InputBox", "ACCEPT",
}

VB6_FORM_SUFFIX = ".frm"   # VB6 form FILE marker, checked by extension.

# GUI-toolkit imports disqualify Tier 2 -- a real windowed GUI already exists,
# so a stray console menu isn't the hidden-UI case.
_GUI_TOOLKIT_RE = re.compile(
    r"\bimport\s+tkinter\b|\bfrom\s+tkinter\b|\bimport\s+PyQt\d*\b|\bfrom\s+PyQt\d*\b|"
    r"\bimport\s+PySide\d*\b|\bfrom\s+PySide\d*\b|\bimport\s+wx\b|\bfrom\s+wx\b|"
    r"javax\.swing|System\.Windows\.Forms|gi\.repository\.Gtk|\bimport\s+kivy\b",
)


def is_gui_toolkit_import(line: str) -> bool:
    return bool(_GUI_TOOLKIT_RE.search(line))

# Comment/prose-prefixed lines (fix C8) -- excluded both as menu-loop
# candidates and from corroboration counting. Generic language-agnostic
# markers only (this track targets unrecognized stacks).
_COMMENT_LINE_RE = re.compile(r"^\s*(?:#|//|/\*|\*(?!/))")


def is_comment_line(line: str) -> bool:
    return bool(_COMMENT_LINE_RE.match(line))

# False-positive guards -- run BEFORE a keyword hit counts.
_ACCEPT_FROM_CLOCK_RE = re.compile(r"\bACCEPT\b[^.\n]*\bFROM\s+(?:DATE|DAY|TIME)\b", re.IGNORECASE)
_FGETS_STREAM_RE = re.compile(r"fgets\s*\([^,]+,[^,]+,\s*([^)]+)\)")


def guard_accept_from_clock(line: str) -> bool:
    """True == suppress. `ACCEPT ... FROM DATE/DAY/TIME` reads the clock, not input."""
    return bool(_ACCEPT_FROM_CLOCK_RE.search(line))

def guard_fgets_not_stdin(line: str) -> bool:
    """True == suppress. `fgets(buf, n, fp)` on a non-stdin stream is a
    file/socket read (unparsable calls let through as false-negative)."""
    m = _FGETS_STREAM_RE.search(line)
    return bool(m) and m.group(1).strip() != "stdin"

def guard_cics_display(line: str, file_has_exec_cics: bool) -> bool:
    """True == suppress. Inside CICS, DISPLAY is a screen-buffer op (BMS), not console I/O."""
    return file_has_exec_cics and bool(re.search(r"\bDISPLAY\b", line, re.IGNORECASE))

def apply_guards(family: str, token: str, line: str, file_has_exec_cics: bool) -> bool:
    """True == suppress this hit before it becomes a signal."""
    if family == "cobol_ish" and token == "ACCEPT":
        return guard_accept_from_clock(line)
    if family == "c_stdin" and token == "fgets(":
        return guard_fgets_not_stdin(line)
    if family == "cobol_ish" and token == "DISPLAY":
        return guard_cics_display(line, file_has_exec_cics)
    return False

# Generic-secret scrub (fix 7 / fix C6) -- NOT _sql_parse_lib.scrub_credentials.
# Safe `-p<word>` continuations that must NOT be treated as a password flag.
_SAFE_DASH_P_PREFIXES = (
    "arallel", "ort", "ath", "refix", "attern", "rivate", "ublic", "roxy",
    "rint", "lugin", "roject", "rovider", "rofile", "rogram",
)


def _scrub_cli_short_password(match: re.Match) -> str:
    value = match.group(1)
    if any(value.lower().startswith(p) for p in _SAFE_DASH_P_PREFIXES):
        return match.group(0)
    return "-p<redacted>"

_SECRET_PATTERNS: list[tuple[re.Pattern, object]] = [
    # CLI short flag: -p<value> (mysql/psql-style, no space, no `=`).
    (re.compile(r"(?<![\w-])-p(?!\s)(\S+)"), _scrub_cli_short_password),
    # CLI long flag: --password=<value> / --password <value>.
    (re.compile(r"(--password[=\s]+)\S+", re.IGNORECASE), r"\1<redacted>"),
    # env-var fallback default (runs BEFORE the general assignment pattern
    # below -- `password = os.environ.get(...)` would otherwise let that
    # broader pattern consume the anchor here first, unredacted).
    (re.compile(
        r'(os\.(?:environ\.get|getenv)\(\s*["\'][^"\']*["\']\s*,\s*)["\'][^"\']+["\']',
        re.IGNORECASE,
    ), r"\1'<redacted>'"),
    # Literal assignment, suffix-tolerant (fix C6): password/api_key/apikey/
    # token/secret + SECRET_KEY/aws_secret_access_key/client_secret. Suffix
    # must start with `_`/`-` (not a bare letter) so "secretary_name" is safe.
    (re.compile(
        r"((?:api[_-]?key|apikey|token|secret|password)(?:[_-]\w*)?\s*[=:]\s*)"
        r"[\"']?[^\"'\s]+[\"']?",
        re.IGNORECASE,
    ), r"\1<redacted>"),
    # Bearer <token> (HTTP Authorization header shape).
    (re.compile(r"\bBearer\s+\S+", re.IGNORECASE), "Bearer <redacted>"),
    # scheme://user:pass@host URI-credential (defense-in-depth alongside
    # `_sql_parse_lib.scrub_credentials`, which the orchestrator also runs).
    (re.compile(r"(\w+://[^:/@\s]+):[^@/\s]+@"), r"\1:<redacted>@"),
    # PEM private-key/certificate block embedded on one physical line (e.g. an
    # env-var default with escaped `\n`) -- redact the body, keep the markers.
    (re.compile(r"(-----BEGIN [A-Z ]+-----)(.+?)(-----END [A-Z ]+-----)"), r"\1<redacted>\3"),
]


def scrub_generic_secret(line: str) -> str:
    """Redact non-SQL secret shapes from a line before it becomes a citation."""
    result = line
    for pattern, repl in _SECRET_PATTERNS:
        result = pattern.sub(repl, result)
    return result

# Menu-loop structural detector -- built on the primitives above, not the orchestrator.
_MENU_LOOP_WINDOW = 40        # bounded lines scanned after a loop-start candidate
_DEADLINE_CHECK_EVERY = 512   # intra-scan deadline check cadence (fix C7)

_MENU_OPTION_RE = re.compile(r'["\']\s*\d{1,2}[.\):]\s+\S')       # "1. Foo" / "2) Bar"
_DISPATCH_RE = re.compile(r'\b(?:switch|case|elif|else\s+if|EVALUATE|WHEN|goto)\b', re.IGNORECASE)
# Tightened (fix C8): require code-shaped context -- `for(`/`while(`/`while:`
# -- not bare `\bfor\b`/`\bwhile\b`/`\bdo\b`, which matched prose ("kept for
# reference"). Dropping bare `do` + requiring parens/colon is an accepted
# false-negative trade (a paren-less Python `while cond:` misses) for killing
# prose/dead-code corroboration.
_LOOP_START_RE = re.compile(r'for\s*\(|while\s*[(:]|PERFORM\b.*\bUNTIL\b', re.IGNORECASE)

def scan_menu_loop(lines, file_has_exec_cics, deadline_check=lambda: False):
    """A loop wrapping a printed-menu block (>=2 enumerated option lines) plus a
    captured-choice dispatch, within a bounded window after the loop start.
    Returns (1-based loop-start line or None, deadline_hit). Coarse by design.

    Guard-suppressed stdin matches must NOT count toward `has_stdin`. Comment
    lines (fix C8) are excluded both as loop-start candidates and from the
    corroboration window. Deadline (fix C7) is checked every
    `_DEADLINE_CHECK_EVERY` lines, not just between files."""
    for i, line in enumerate(lines):
        if i % _DEADLINE_CHECK_EVERY == 0 and deadline_check():
            return None, True
        if is_comment_line(line) or not _LOOP_START_RE.search(line):
            continue
        window = [wl for wl in lines[i: i + _MENU_LOOP_WINDOW] if not is_comment_line(wl)]
        if sum(1 for wl in window if _MENU_OPTION_RE.search(wl)) < 2:
            continue
        has_stdin = any(
            fp.regex.search(wl) and not apply_guards(fp.family, fp.token, wl, file_has_exec_cics)
            for wl in window
            for fp in SIGNAL_FAMILIES
            if fp.token in STDIN_READ_TOKENS
        )
        if has_stdin and any(_DISPATCH_RE.search(wl) for wl in window):
            return i + 1, False
    return None, False
