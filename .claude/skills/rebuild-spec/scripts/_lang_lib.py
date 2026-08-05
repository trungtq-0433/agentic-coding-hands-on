"""Language resolution helpers for rebuild-spec output language support.

Stdlib only, mirrors _slug_lib.py style.
"""
from __future__ import annotations

import re
from pathlib import Path

_LANG_RE = re.compile(r"^[a-z]{2,3}(-[a-z0-9]{2,8})*$")


_PATH_UNSAFE_RE = re.compile(r"[/\\.]")

# Common non-ISO aliases → canonical ISO 639-1 codes. Kept tiny and explicit
# (D1): only unambiguous, frequently-typed aliases. Never put a valid ISO/region
# tag (en, ja, vi, zh-cn, pt-br, ...) on the left — those must pass through untouched.
_ALIASES: dict[str, str] = {
    "jp": "ja",
    "japan": "ja",
    "cn": "zh",
    "china": "zh",
    "kr": "ko",
    "korea": "ko",
    "vn": "vi",
    "vietnam": "vi",
}

# Sentinel filename written by migrate_docs_layout.py once an en-primary repo's
# content has been flipped to docs/<primary>/. Authoritative per-lang signal.
LAYOUT_SENTINEL = ".layout-migrated"

# Sentinel written by _component_migrate_lib.migrate_components_to_lang once the
# v23 one-time component migration has run (root docs/components/ → docs/<primary>/components/).
# Placed at docs/<primary>/.components-migrated-v23 (alongside LAYOUT_SENTINEL).
COMPONENTS_V23_SENTINEL = ".components-migrated-v23"


def normalize_lang(code: str | None) -> str:
    """Normalize a language code: None/empty → "en"; else lowercase+trim+de-alias.

    Flow: trim → lower → path-unsafe guard → alias the primary subtag → re-run the
    path-unsafe guard on the reassembled code (region suffix is not covered by the
    first guard once we split/rejoin) → return.

    Raises ValueError if the code contains path-separator characters (/, \\, .)
    to prevent path-traversal when used in docs/<lang>/ construction.
    """
    if not code or not code.strip():
        return "en"
    normalized = code.strip().lower()
    if _PATH_UNSAFE_RE.search(normalized):
        raise ValueError(
            f"language code contains unsafe path characters: {code!r}"
        )
    # Alias only the bare primary subtag; preserve any region suffix (zh-cn stays zh-cn).
    primary, sep, suffix = normalized.partition("-")
    if primary in _ALIASES:
        primary = _ALIASES[primary]
    reassembled = primary + sep + suffix
    # [Red-team C/Sec-F1] Re-validate the reassembled code so a crafted suffix
    # cannot smuggle traversal characters past the alias step.
    if _PATH_UNSAFE_RE.search(reassembled):
        raise ValueError(
            f"language code contains unsafe path characters: {code!r}"
        )
    return reassembled


def detect_layout_mode(
    primary_lang: str,
    docs_base: str = "docs",
    state: dict | None = None,
) -> str:
    """Return the docs layout mode: "single" or "per-lang".

    Per-lang iff a secondary language is registered (state.translations has a key
    other than the primary) OR the layout sentinel docs/<primary>/.layout-migrated
    exists. Bare docs/<primary>/ directory existence is NOT a signal — a non-en
    primary repo is already at docs/<primary>/ in single-lang mode (see C2), so
    directory presence would misfire.
    """
    primary = normalize_lang(primary_lang)
    state = state or {}
    translations = state.get("translations") or {}
    for key in translations:
        try:
            if normalize_lang(key) != primary:
                return "per-lang"
        except ValueError:
            continue
    sentinel = Path(docs_base) / primary / LAYOUT_SENTINEL
    if sentinel.exists():
        return "per-lang"
    return "single"


def resolve_docs_root(
    lang: str | None,
    primary_lang: str | None = None,
    *,
    multilang: bool = False,
) -> str:
    """Return the docs root path for a language.

    - single-lang en-primary (multilang=False, lang==primary=="en") → "docs"
    - everything else → "docs/<lang>"

    Back-compat: called single-arg (primary_lang=None, multilang=False) it
    reproduces the legacy rule exactly — en → "docs", any other code → "docs/<lang>"
    — because primary_lang defaults to the resolved lang itself, so a missed caller
    degrades to today's behavior instead of crashing.
    """
    lang_n = normalize_lang(lang)
    primary_n = normalize_lang(primary_lang) if primary_lang is not None else lang_n
    if not multilang and lang_n == "en" and primary_n == "en":
        return "docs"
    return f"docs/{lang_n}"


def looks_unusual(lang: str) -> bool:
    """Return True if the normalized lang code looks non-standard (warn, don't abort).

    Catches ValueError from normalize_lang (path-unsafe codes) and treats them as unusual.
    """
    try:
        return not bool(_LANG_RE.match(normalize_lang(lang)))
    except ValueError:
        return True
