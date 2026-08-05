"""Credential-scrub pass for service config files (Phase D, RT2-F12).

SEPARATE pass — NOT inherited from Phase B _sql_parse_lib. This pass covers a
NEW surface: application.yml / .properties / .env files containing broker URLs,
SASL jaas config, passwords, tokens.

Signal → action:
  broker URL with embedded creds (scheme://user:pass@host) → redact password
  sasl.jaas.config = ...                                    → redact entire value
  *.password = <value>                                      → redact value
  *.token = <value>                                         → redact value
  Authorization: Bearer <token>                             → redact token
  secret= / api_key= / apikey= <value>                      → redact value
  Environment=<KEY>=<value> (systemd unit, KEY matches       → redact value
    pass/pwd/secret/token/key/credential/dsn/auth vocabulary) (v26.1.0 F6, v26.2.x C4)

Also used as a hard CRITICAL gate over rendered doc output via `assert_no_secrets()`
(e.g. `validate_job_list.py` — a job description or schedule/config field must never
echo a literal secret value). `.service`/`.timer` systemd unit files are recognised by
`is_config_file()` so a config-surface walk (`collect_scrubbed_config`) picks them up
alongside `application.yml`/`.env`. `EnvironmentFile=<path>` lines reference a SEPARATE
file (not inline) — nothing to redact on that line itself; the referenced file is
scrubbed only if its own filename independently matches this module's recognized set.

TWO INDEPENDENT PATTERN SETS (v26.2.x, review C4) — sharing one pattern list between
the scrub and gate uses caused both a false-negative and a false-positive:

  - `_SCRUB_PATTERNS` (`scrub_line` / `collect_scrubbed_config`) is RECALL-focused:
    over-redacting a config-surface walk is safe (the output is audit-only/discarded),
    so it stays broad.
  - `_GATE_PATTERNS` (`assert_no_secrets`) is PRECISION-focused: it is a hard CRITICAL
    gate over rendered doc PROSE, so a false positive permanently blocks promotion of
    clean docs. It flags only explicit assignment shapes carrying a literal
    secret-looking value — placeholder values (`<...>`, `<redacted>`) and bare
    `Bearer <token>` / `username: ...` prose are deliberately exempt.

Both sides share segment-boundary matching for the systemd `Environment=<KEY>=<value>`
form: KEY is split on `[._-]` and each segment is compared to the credential vocab as a
whole word (case-insensitive prefix match), so `BYPASS_HEALTHCHECK` (segment `BYPASS`)
and `OAUTH_ENABLED` (segment `OAUTH`) do NOT match, while `DB_PASS`, `REDIS_AUTH`, and
`DB_PASSWORD` DO. Quoted `Environment="KEY=VALUE"` redaction preserves the closing
quote (value character class excludes `"`).

Stdlib only.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Shared: systemd Environment=<KEY>=<VALUE> assignment parsing
# ---------------------------------------------------------------------------

# Credential-ish KEY segments recognised in Environment=<KEY>=<value> assignments.
# Segment-boundary matching (v26.2.x, review C4): KEY is split on separators and
# each segment is compared against this vocabulary as a whole word (prefix match) —
# substring-anywhere matching previously let `BYPASS_HEALTHCHECK` false-positive on
# "pass" while leaving the intended `OAUTH_ENABLED` vs `REDIS_AUTH` distinction
# unenforced. `auth` added here per C4 (closes the REDIS_AUTH false-negative).
_ENV_KEY_VOCAB = (
    "pass", "pwd", "secret", "token", "key", "credential", "dsn", "auth",
)

_ENV_KEY_SEGMENT_RE = re.compile(r"[_.\-]")

# Environment=<KEY>=<value>, optionally wrapped in a single pair of quotes around the
# whole KEY=VALUE (systemd unit files write both forms). Value excludes `"` so a
# trailing quote is never swallowed into the matched/replaced span. Groups:
#   1: "Environment=" prefix as written (whitespace preserved)
#   2: opening quote, if any
#   3: KEY
#   4: "=" separator as written (whitespace preserved)
#   5: VALUE (no whitespace/quote)
#   6: closing quote, if any
_ENV_ASSIGN_RE = re.compile(
    r'(Environment\s*=\s*)(")?([\w.\-]+)(\s*=\s*)([^"\s]*)(")?',
    re.IGNORECASE,
)


def _key_has_credential_segment(key: str) -> bool:
    """True if any `[_.-]`-delimited segment of key starts with a vocab word.

    Prefix match (not exact equality) so `DB_PASSWORD` matches vocab word `pass`
    via its `PASSWORD` segment, while `BYPASS_HEALTHCHECK`'s `BYPASS` segment does
    NOT (it does not *start with* `pass`) and `OAUTH_ENABLED`'s `OAUTH` segment does
    NOT match `auth` (does not start with `auth`).
    """
    segments = [seg.lower() for seg in _ENV_KEY_SEGMENT_RE.split(key) if seg]
    return any(seg.startswith(word) for seg in segments for word in _ENV_KEY_VOCAB)


def _is_secret_looking_value(value: str) -> bool:
    """True if value looks like a literal secret rather than a placeholder/prose token.

    Empty values and angle-bracket placeholders (`<...>`, including `<redacted>`)
    are NOT secret-looking — only a literal assigned value is a leak.
    """
    value = value.strip()
    if not value:
        return False
    return not (value.startswith("<") and value.endswith(">"))


def _scrub_environment_assignment(match: re.Match) -> str:
    """`_ENV_ASSIGN_RE` replacement callback — redact only credential-ish KEYs."""
    prefix, open_q, key, eq, _value, close_q = match.groups()
    if not _key_has_credential_segment(key):
        return match.group(0)
    return f"{prefix}{open_q or ''}{key}{eq}<redacted>{close_q or ''}"


# ---------------------------------------------------------------------------
# Scrub patterns (forbidden in digest output) — RECALL-focused, see module
# docstring. Consumed by `scrub_line` / `collect_scrubbed_config`.
# ---------------------------------------------------------------------------

_SCRUB_PATTERNS: list[tuple[re.Pattern, object]] = [
    # broker URL with embedded creds: protocol://user:pass@host
    (re.compile(r'(//[^:/@\s]+):[^@/\s]+@'), r'\1:<redacted>@'),
    # sasl.jaas.config = org.apache.kafka...PlainLoginModule ... password=...
    (re.compile(r'(sasl\.jaas\.config\s*[=:]\s*).*', re.IGNORECASE), r'\1<redacted>'),
    # sasl.jaas (short form)
    (re.compile(r'(sasl\.jaas\s*[=:]\s*).*', re.IGNORECASE), r'\1<redacted>'),
    # *.password = secret  (any dotted key ending in .password or just password)
    (re.compile(r'((?:[\w.\-]+\.)?password\s*[=:]\s*)[^"\s]+', re.IGNORECASE), r'\1<redacted>'),
    # *.token = value
    (re.compile(r'((?:[\w.\-]+\.)?token\s*[=:]\s*)[^"\s]+', re.IGNORECASE), r'\1<redacted>'),
    # Authorization: Bearer <token>
    (re.compile(r'(Bearer\s+)[^"\s]+', re.IGNORECASE), r'\1<redacted>'),
    # secret= / api_key= / apikey=
    (re.compile(r'((?:secret|api[_-]?key|apikey)\s*[=:]\s*)[^"\s]+', re.IGNORECASE), r'\1<redacted>'),
    # SASL SCRAM/PLAIN principal (review H1): sasl.username= / *.user.name= / *.username=
    (re.compile(r'((?:[\w.\-]+\.)?user(?:name|\.name)?\s*[=:]\s*)[^"\s]+', re.IGNORECASE), r'\1<redacted>'),
    # systemd unit Environment=<KEY>=<value> where KEY has a credential-ish segment
    # (segment-boundary match — see _key_has_credential_segment). EnvironmentFile=<path>
    # lines carry no inline value to redact — deliberately not matched here.
    (_ENV_ASSIGN_RE, _scrub_environment_assignment),
]

_CONFIG_FILENAMES = frozenset({
    "application.yml", "application.yaml", "application.properties",
    ".env", ".env.local", ".env.production", ".env.staging",
})

# systemd unit file extensions — recognised alongside _CONFIG_FILENAMES so a config-surface
# walk picks up .service/.timer pairs (v26.1.0 jobs pass, F6).
_UNIT_FILE_SUFFIXES = (".service", ".timer")

_SKIP_DIRS = frozenset({".git", "node_modules", "vendor", "dist", "build", "target", "__pycache__"})


def scrub_line(line: str) -> str:
    """Apply all credential-scrub patterns to a single line; return scrubbed line."""
    for pattern, replacement in _SCRUB_PATTERNS:
        line = pattern.sub(replacement, line)
    return line


def is_config_file(filename: str) -> bool:
    """Return True if filename is a recognised service config file."""
    return (
        filename in _CONFIG_FILENAMES
        or filename.startswith(".env")
        or filename.endswith(_UNIT_FILE_SUFFIXES)
    )


def collect_scrubbed_config(component_root: str) -> str:
    """Read all config files under component_root, scrubbed line-by-line.

    Returns combined scrubbed text — an audit-only scrub walk over the service's config surface
    (NOT written to the digest, NOT hashed). The caller asserts on it / discards it; the digest's
    own `source_sha` is computed separately from the structural source tree.
    """
    parts: list[str] = []
    for dp, dirnames, filenames in os.walk(str(component_root), followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            if is_config_file(fn):
                fp = Path(dp) / fn
                try:
                    raw = fp.read_text(encoding="utf-8", errors="replace")
                    scrubbed = "\n".join(scrub_line(ln) for ln in raw.splitlines())
                    parts.append(scrubbed)
                except OSError:
                    pass
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Gate patterns (`assert_no_secrets`) — PRECISION-focused, see module docstring.
# Flags ONLY assignment-shaped leaks with a secret-looking value (see
# `_is_secret_looking_value`); bare `Bearer <token>` / `username: ...` prose and
# placeholder values are deliberately exempt so clean docs never trip the gate.
# ---------------------------------------------------------------------------

# Negative-lookahead guard: only match a value that is NOT an angle-bracket
# placeholder (`<...>`, including the literal `<redacted>`).
_SECRET_VALUE_GUARD = r'(?!\s*<[^>]*>)(?!\s*<redacted>)\S+'

_GATE_PATTERNS: list[re.Pattern] = [
    # broker URL with embedded creds: protocol://user:pass@host
    re.compile(r'(//[^:/@\s]+):[^@/\s]+@'),
    # sasl.jaas(.config) = <non-placeholder value>
    re.compile(r'sasl\.jaas(?:\.config)?\s*[=:]\s*' + _SECRET_VALUE_GUARD, re.IGNORECASE),
    # *.password / *.pwd = <non-placeholder value>
    re.compile(r'(?:[\w.\-]+\.)?(?:password|pwd)\s*[=:]\s*' + _SECRET_VALUE_GUARD, re.IGNORECASE),
    # *.token / secret / api_key / apikey / credential / dsn = <non-placeholder value>
    re.compile(
        r'(?:[\w.\-]+\.)?(?:token|secret|api[_-]?key|apikey|credential|dsn)'
        r'\s*[=:]\s*' + _SECRET_VALUE_GUARD,
        re.IGNORECASE,
    ),
]


def _gate_environment_leaks(text: str) -> list[str]:
    """Flag systemd `Environment=<KEY>=<VALUE>` assignments with a real secret value.

    Reuses the same segment-boundary KEY vocab as the scrub side, but additionally
    requires the value to be secret-looking (not empty, not a `<...>` placeholder) —
    the precision half of the split that `scrub_line`'s recall-focused redaction
    does not need.
    """
    warnings: list[str] = []
    for match in _ENV_ASSIGN_RE.finditer(text):
        _prefix, _open_q, key, _eq, value, _close_q = match.groups()
        if _key_has_credential_segment(key) and _is_secret_looking_value(value):
            warnings.append(
                "Possible credential leak detected in digest "
                f"(pattern: 'Environment=<credential-key>=<value>', key={key!r})"
            )
    return warnings


def assert_no_secrets(digest_json: str) -> list[str]:
    """Scan final digest JSON / rendered doc prose for credential leaks.

    PRECISION-focused hard CRITICAL gate (`validate_job_list.py` F6) — a false
    positive here permanently blocks promotion of clean docs, so this iterates
    `_GATE_PATTERNS` (NOT `_SCRUB_PATTERNS`): bare `Bearer <token>` / `username: ...`
    prose and placeholder values never trigger a warning here, only literal
    assignment-shaped secrets do. Returns a list of warning strings (empty when clean).
    """
    warnings: list[str] = []
    for pattern in _GATE_PATTERNS:
        if pattern.search(digest_json):
            warnings.append(
                f"Possible credential leak detected in digest "
                f"(pattern: {pattern.pattern[:50]!r})"
            )
    warnings.extend(_gate_environment_leaks(digest_json))
    return warnings
