"""Shared scheme registry and rewrite helpers for rebuild-spec ID renumbering.
Stdlib only.

Scheme shapes:
  WORD###  — US / SCR / BL / PERM / F / MODEL / FLOW / ROUTE (sep="")
  WORD-### — DISC (sep="-")
  REG###   — per-screen; scope="per-screen"; NEVER global-renumbered.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# prefix → {sep, scope}
SCHEMES: Dict[str, Dict[str, str]] = {
    "US":    {"sep": "",  "scope": "global"},
    "SCR":   {"sep": "",  "scope": "global"},
    "BL":    {"sep": "",  "scope": "global"},
    "PERM":  {"sep": "",  "scope": "global"},
    "F":     {"sep": "",  "scope": "global"},
    "MODEL": {"sep": "",  "scope": "global"},
    "FLOW":  {"sep": "",  "scope": "global"},
    "DISC":  {"sep": "-", "scope": "global"},   # check-only by default
    "REG":   {"sep": "",  "scope": "per-screen"},  # NEVER global-renumber
    "ROUTE": {"sep": "",  "scope": "global"},
}

# artifact name → list of owned prefixes to RENUMBER
# REG is per-screen (never global); DISC renumber requires explicit future entry.
ARTIFACT_OWNS: Dict[str, List[str]] = {
    "data-model":         ["MODEL"],
    "screen-list":        ["SCR"],
    "behavior-logic":     ["BL"],
    "permissions-matrix": ["PERM"],
    "user-stories":       ["US"],
    "feature-list":       ["F"],
    "process-flows":      ["FLOW"],
    "route-list":         ["ROUTE"],
}

# scheme prefix → list of sibling filenames that may reference those codes.
# Evidence comments cite template/checklist lines proving the file contains the token.
# Entries without provable evidence have been REMOVED (F7 guard).
# Script applies the map ONLY to siblings that EXIST on disk at run time.
SIBLING_MATRIX: Dict[str, List[str]] = {
    # feature-list references MODEL### (member-model refs);
    # api-contracts references MODEL### in response shapes.
    # Both usually absent at W1 → skipped via on-disk gate.
    "MODEL": ["feature-list.md", "api-contracts.md"],

    # screen-flow.md references SCR### in node labels (template: SCR###_NameSlug).
    # user-stories.md references SCR### in acceptance criteria (template: SCR### trigger).
    # feature-list.md references SCR### in screen column.
    # behavior-logic.md REMOVED: cross-task race (BL agent concurrent with SCR owner).
    "SCR":   ["screen-flow.md", "user-stories.md", "feature-list.md"],

    # feature-list.md references BL### in behavior column (template confirmed).
    "BL":    ["feature-list.md"],

    # feature-list.md references US### in story column (template confirmed).
    # behavior-logic.md + screen-flow.md REMOVED: templates contain NO US### tokens.
    "US":    ["feature-list.md"],

    # No downstream draft directly embeds PERM### codes.
    "PERM":  [],

    # process-flows.md references F### in flow header (template confirmed).
    # glossary.md references F### in term definitions (template confirmed).
    "F":     ["process-flows.md", "glossary.md"],

    # No sibling drafts reference FLOW### codes directly at wave time.
    "FLOW":  [],

    # feature-list.md references ROUTE### in its checklist line "All route
    # references are valid (ROUTE### in RouteList)" (template confirmed,
    # feature-list-template.md:168).
    # behavior-logic.md references ROUTE### in its checklist line "All related
    # route references are valid (ROUTE### in RouteList)" (template confirmed,
    # behavior-logic-template.md:175).
    # technical-spec.md is per-feature (not a top-level artifacts/ sibling file
    # resolved by this script's plan_dir/artifacts/<name> lookup) — its
    # {ROUTE###} citation (technical-spec-template.md:297) is real but out of
    # scope for this global-artifact SIBLING_MATRIX; excluded, not omitted by
    # oversight.
    # screen-flow.md REMOVED: no ROUTE### citation found — its only "route"
    # mention (GUARD-### heading: "on {ROUTE### or path}") is an optional
    # either/or, not a hard ROUTE### cite (F7 guard).
    "ROUTE": ["feature-list.md", "behavior-logic.md"],
}

# ---------------------------------------------------------------------------
# Compiled token regex cache  (prefix, sep) → compiled pattern
# ---------------------------------------------------------------------------
_REGEX_CACHE: Dict[Tuple[str, str], re.Pattern] = {}


def token_re(prefix: str, sep: str) -> re.Pattern:
    """Return compiled regex matching exactly 3-digit codes, word-boundary safe.

    Slug tail like ``US001_Login`` is preserved — only prefix+digits are captured
    and replaced by the caller; the ``_Slug`` part follows after the match.

    Pattern: ``(?<![A-Za-z0-9])PREFIX(sep)(\\d{3})(?![0-9])``
    """
    key = (prefix, sep)
    if key not in _REGEX_CACHE:
        _REGEX_CACHE[key] = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(prefix)}{re.escape(sep)}(\d{{3}})(?![0-9])"
        )
    return _REGEX_CACHE[key]


# ---------------------------------------------------------------------------
# Core public helpers
# ---------------------------------------------------------------------------

def find_codes(text: str, prefix: str, sep: str) -> List[str]:
    """Scan *entire* text (fences included) for 3-digit tokens.

    Returns document-order unique list of full codes, e.g. ``["US001", "US005"]``.
    """
    pat = token_re(prefix, sep)
    seen: dict[str, None] = {}  # ordered set via dict
    for m in pat.finditer(text):
        full = f"{prefix}{sep}{m.group(1)}"
        if full not in seen:
            seen[full] = None
    return list(seen.keys())


def find_codes_scoped(text: str, prefix: str, sep: str) -> List[str]:
    """Scan only prose and mermaid regions for 3-digit tokens.

    Identical to :func:`find_codes` but skips non-mermaid code fences so that
    IDs mentioned only in e.g. a ``python`` or ``bash`` fence are excluded from
    the renumber map.  This mirrors the scope used by the validator and
    :func:`rewrite_text`, keeping map, rewriter, and validator consistent.

    IDs found exclusively inside a skipped code fence are NOT entered into the
    map; callers should emit a ``[WARN]`` via :func:`find_fence_only_codes` if
    they want to notify the user about skipped tokens.

    Returns document-order unique list of full codes, e.g. ``["US001", "US005"]``.
    """
    pat = token_re(prefix, sep)
    seen: dict[str, None] = {}
    for kind, chunk in segment_text(text):
        if kind in ("prose", "mermaid"):
            for m in pat.finditer(chunk):
                full = f"{prefix}{sep}{m.group(1)}"
                if full not in seen:
                    seen[full] = None
    return list(seen.keys())


def find_fence_only_codes(text: str, prefix: str, sep: str) -> List[str]:
    """Return codes that appear ONLY inside non-mermaid code fences (not in prose/mermaid).

    These codes are skipped by :func:`find_codes_scoped` and therefore never
    enter the renumber map.  Callers use this to emit ``[WARN]`` messages so
    users know which IDs were deliberately excluded.
    """
    scoped = set(find_codes_scoped(text, prefix, sep))
    return [c for c in find_codes(text, prefix, sep) if c not in scoped]


def build_renumber_map(codes: List[str], prefix: str, sep: str) -> Dict[str, str]:
    """Map first-appearance ordered codes to contiguous 001..N.

    Returns ONLY entries where old ≠ new (skips already-contiguous slots).
    """
    mapping: Dict[str, str] = {}
    for new_num, old_full in enumerate(codes, start=1):
        new_full = f"{prefix}{sep}{new_num:03d}"
        if old_full != new_full:
            mapping[old_full] = new_full
    return mapping


def find_overflow_tokens(text: str, prefix: str, sep: str) -> List[str]:
    """Return all 4+-digit tokens for *prefix* (not matched by 3-digit regex).

    These are NOT renumbered. The renumber script warns; phase-02 validator
    escalates to CRITICAL.
    """
    pat = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(prefix)}{re.escape(sep)}(\d{{4,}})(?![0-9])"
    )
    seen: dict[str, None] = {}
    for m in pat.finditer(text):
        full = f"{prefix}{sep}{m.group(1)}"
        if full not in seen:
            seen[full] = None
    return list(seen.keys())


# ---------------------------------------------------------------------------
# Fence segmentation
# ---------------------------------------------------------------------------

_FENCE_OPEN = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<lang>[^\s`]*)")


def segment_text(text: str) -> Iterator[Tuple[str, str]]:
    """Split *text* into alternating regions.

    Yields ``(kind, content)`` tuples where *kind* is one of:
      - ``"prose"``   — normal prose / table lines
      - ``"mermaid"`` — content of a ```mermaid``` fence (including delimiters)
      - ``"code"``    — content of any other fenced block (including delimiters)
    """
    lines = text.splitlines(keepends=True)
    i, n = 0, len(lines)
    prose_buf: list[str] = []

    while i < n:
        m = _FENCE_OPEN.match(lines[i])
        if m:
            if prose_buf:
                yield ("prose", "".join(prose_buf))
                prose_buf = []
            fence_char = m.group("fence")[0]
            fence_len = len(m.group("fence"))
            lang = (m.group("lang") or "").strip().lower()
            kind = "mermaid" if lang == "mermaid" else "code"
            fence_buf = [lines[i]]
            i += 1
            while i < n:
                close = _FENCE_OPEN.match(lines[i])
                fence_buf.append(lines[i])
                if (
                    close
                    and close.group("fence")[0] == fence_char
                    and len(close.group("fence")) >= fence_len
                    and not close.group("lang")
                ):
                    i += 1
                    break
                i += 1
            yield (kind, "".join(fence_buf))
        else:
            prose_buf.append(lines[i])
            i += 1

    if prose_buf:
        yield ("prose", "".join(prose_buf))


# ---------------------------------------------------------------------------
# Two-phase sentinel rewrite (prevents chain collision)
# ---------------------------------------------------------------------------

SENTINEL_BASE = "\x00RN"


def pre_flight_sentinel_check(text: str, path: Path) -> None:
    """Raise RuntimeError if sentinel bytes already exist in text (F11)."""
    if SENTINEL_BASE in text:
        raise RuntimeError(
            f"sentinel collision in {path}: text already contains '\\x00RN' bytes; "
            "aborting before any write"
        )


def apply_map(text: str, mapping: Dict[str, str], prefix: str, sep: str) -> str:
    """Two-phase sentinel rewrite — prevents US005→US003 clobbering existing US003.

    Pass A: old code → unique NUL-byte sentinel.
    Pass B: sentinel → new code.
    """
    if not mapping:
        return text
    tmp = text
    sentinels: Dict[str, str] = {}
    for i, (old, new) in enumerate(mapping.items()):
        sentinel = f"{SENTINEL_BASE}{i}\x00"
        sentinels[sentinel] = new
        escaped_old = re.escape(old)
        tmp = re.sub(rf"(?<![A-Za-z0-9]){escaped_old}(?![0-9])", sentinel, tmp)
    for sentinel, new in sentinels.items():
        tmp = tmp.replace(sentinel, new)
    return tmp


def rewrite_text(
    text: str,
    mapping: Dict[str, str],
    prefix: str,
    sep: str,
    source_path: Path,
) -> str:
    """Apply *mapping* to prose/tables and mermaid fences; leave other code fences intact.

    Emits ``[WARN]`` to stderr for old-ID tokens found inside skipped code fences.
    """
    if not mapping:
        return text
    old_codes = set(mapping.keys())
    three_digit_pat = token_re(prefix, sep)
    out_parts: list[str] = []
    for kind, chunk in segment_text(text):
        if kind in ("prose", "mermaid"):
            out_parts.append(apply_map(chunk, mapping, prefix, sep))
        else:
            for m in three_digit_pat.finditer(chunk):
                full = f"{prefix}{sep}{m.group(1)}"
                if full in old_codes:
                    print(
                        f"[WARN] possible stale ID {full} inside skipped code fence "
                        f"in {source_path} — manual review",
                        file=sys.stderr,
                    )
            out_parts.append(chunk)
    return "".join(out_parts)


# ---------------------------------------------------------------------------
# Multi-file artifact resolution
# ---------------------------------------------------------------------------

def resolve_artifact_files(plan_dir: Path, artifact: str) -> List[Path]:
    """Return the ordered list of files that make up *artifact*.

    Default: ``[plan_dir/artifacts/<artifact>.md]`` (single-file layout).

    Special cases:
    - ``process-flows``: sorted glob of ``artifacts/flows/*.md``.
      Skips the ``.completed`` marker and any non-``.md`` files.
      Missing directory or zero ``.md`` files → empty list (caller treats as no-op).

    Returns only paths that exist on disk.
    """
    if artifact == "process-flows":
        flows_dir = plan_dir / "artifacts" / "flows"
        if not flows_dir.is_dir():
            return []
        files = sorted(flows_dir.glob("*.md"))
        return [f for f in files if f.is_file()]
    # Default: single-file
    candidate = plan_dir / "artifacts" / f"{artifact}.md"
    if candidate.is_file():
        return [candidate]
    return []


# ---------------------------------------------------------------------------
# Atomic write helpers (mirror _summary_lib.py:76-81)
# ---------------------------------------------------------------------------

def atomic_write_text(path: Path, content: str) -> None:
    """Write *content* to *path* atomically via a .tmp sibling + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(path))


def atomic_write_json(path: Path, data: object) -> None:
    """Write *data* as JSON to *path* atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(str(tmp), str(path))
