"""Citation parsing and resolution helpers for audit-doc-parity.

Extracts **Source:** citations from doc files, resolves them to real paths,
validates ranges, and reads source content encoding-safely.

Stdlib only. No verdicts — returns status tags; callers decide UNVERIFIABLE.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

# VERBATIM from rebuild-spec/scripts/validate_source_citations.py
CITATION_RE = re.compile(r"\*\*Source:\*\*\s+`?([^`\n:]+):(\d+)(?:-(\d+))?`?")

# Non-source extensions that are VALID citation targets (legacy group B)
# Binaries are handled by read_text_safe returning None (undecodable)
_NON_SOURCE_EXTS = {
    ".sql", ".xml", ".sh", ".htaccess", ".erb", ".jsp", ".php",
    ".cfg", ".conf", ".config", ".ini", ".toml", ".yaml", ".yml",
    ".crontab", ".html", ".htm", ".css", ".json",
}

# Status tags returned by resolve_and_validate / read_text_safe
STATUS_OK = "ok"
STATUS_FILE_MISSING = "file_missing"
STATUS_RANGE_INVALID = "range_invalid"
STATUS_UNREADABLE = "unreadable"
STATUS_TRAVERSAL = "traversal"
STATUS_STALE = "stale"


class CitationRef(NamedTuple):
    raw_path: str
    start: int
    end: int        # equals start when no range given
    line_no: int    # 1-based line in the doc


def _is_traversal(raw: str) -> bool:
    """Return True if the raw path looks like a traversal or absolute path."""
    return ".." in raw.split("/") or raw.startswith("/") or "\x00" in raw


def _assert_under(child: Path, parent: Path) -> None:
    """Path-traversal guard. Raises ValueError if child is not under parent."""
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"{child} is not under {parent}") from exc


def resolve_project_root(arg: str | None) -> Path:
    """CLI arg → git toplevel → CWD."""
    if arg:
        return Path(arg).resolve()
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return Path.cwd().resolve()


def _find_state_file(docs_dir: Path) -> Path | None:
    """Locate the rebuild-state file under docs/.

    Canonical en-primary location is ``docs/.rebuild-state.json``; a non-en
    primary repo keeps it inside its resolved docs root (``docs/<primary>/``),
    so fall back to the first ``docs/<lang>/.rebuild-state.json``. The contents
    (primary_lang) determine the result regardless of which dir held the file.
    """
    direct = docs_dir / ".rebuild-state.json"
    if direct.is_file():
        return direct
    # Tie-break: first match in alphabetical directory order. rebuild-spec writes
    # exactly one state file, so >1 here is anomalous; the result is driven by the
    # file's primary_lang content, not by which dir held it.
    for sub in sorted(docs_dir.glob("*/.rebuild-state.json")):
        if sub.is_file():
            return sub
    return None


_LAYOUT_SENTINEL = ".layout-migrated"


def resolve_docs_root(project_root: Path) -> Path:
    """Resolve the docs root layout-aware: ``docs/`` vs ``docs/<primary>/``.

    Reads ``primary_lang``/``translations`` from the rebuild-state file and
    defers the single-vs-per-lang decision to rebuild-spec's canonical
    ``_lang_lib`` (the single source of truth for the resolution rule — see
    ``_shared/docs-canonical-mapping.md`` § Language Layout). Cases:
      - en-primary single-lang      → ``docs/``
      - non-en primary (e.g. vi)    → ``docs/<primary>/``
      - per-lang (secondary langs)  → ``docs/<primary>/``

    Degrades gracefully to bare ``docs/`` when no state file exists (legacy
    en-primary behavior) or when ``_lang_lib`` cannot be imported (audit-doc-parity
    installed without rebuild-spec).
    """
    docs_dir = project_root / "docs"
    state_file = _find_state_file(docs_dir)
    if state_file is None:
        return docs_dir

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return docs_dir

    primary = state.get("primary_lang") or "en"

    lang_lib = _import_lang_lib()
    if lang_lib is None:
        # No canonical resolver available — apply the documented rule directly
        # (_shared/docs-canonical-mapping.md § Language Layout): per-lang iff a
        # secondary translation key exists OR the docs/<primary>/.layout-migrated
        # sentinel is present; en single-lang stays at docs/, any other primary
        # lives at docs/<primary>. Guard primary against path-unsafe values.
        if "/" in primary or "\\" in primary or "." in primary:
            return docs_dir
        per_lang = bool(state.get("translations") or {}) \
            or (docs_dir / primary / _LAYOUT_SENTINEL).is_file()
        if primary == "en" and not per_lang:
            return docs_dir
        return docs_dir / primary

    # _lang_lib.normalize_lang raises ValueError on path-unsafe lang codes
    # (e.g. a corrupt/adversarial "../evil"); never let that abort the tool.
    try:
        mode = lang_lib.detect_layout_mode(primary, str(docs_dir), state)
        rel = lang_lib.resolve_docs_root(primary, primary, multilang=(mode == "per-lang"))
    except ValueError:
        return docs_dir
    return project_root / rel


def _import_lang_lib():
    """Import rebuild-spec's _lang_lib (sibling skill); None if unavailable."""
    lang_lib_dir = Path(__file__).resolve().parent.parent.parent / "rebuild-spec" / "scripts"
    if not (lang_lib_dir / "_lang_lib.py").is_file():
        return None
    if str(lang_lib_dir) not in sys.path:
        sys.path.insert(0, str(lang_lib_dir))
    try:
        import _lang_lib  # type: ignore
        return _lang_lib
    except ImportError:
        return None


def read_text_safe(path: Path) -> tuple[str, str] | None:
    """Read a file with encoding auto-detection.

    Tries utf-8-sig (BOM), utf-8, cp932 (Shift-JIS), latin-1 in order.
    Normalises CRLF to LF after decoding.
    Returns (text, encoding_used) or None if the file cannot be decoded.
    """
    raw: bytes
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            text = raw.decode(enc)
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            return (text, enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return None  # all encodings failed → UNVERIFIABLE


def parse_citations(doc_text: str) -> list[CitationRef]:
    """Return all **Source:** citations found outside fenced code blocks.

    Skips citations inside ``` fences (idea from rebuild-spec fence-skip loop).
    Returns list of CitationRef in document order.
    """
    results: list[CitationRef] = []
    in_fence = False
    for line_idx, line in enumerate(doc_text.splitlines()):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = CITATION_RE.search(line)
        if not m:
            continue
        raw_path = m.group(1).strip()
        start = int(m.group(2))
        end = int(m.group(3)) if m.group(3) else start
        results.append(CitationRef(raw_path=raw_path, start=start, end=end, line_no=line_idx + 1))
    return results


def resolve_citation(raw: str, doc_path: Path, project_root: Path) -> Path | None:
    """Try project_root/raw, then doc.parent/raw.

    Returns resolved Path if found and safe, else None.
    Does NOT check traversal — caller should call _is_traversal first.
    """
    for base in (project_root, doc_path.parent):
        candidate = (base / raw).resolve()
        try:
            _assert_under(candidate, project_root)
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def validate_citation(
    ref: CitationRef,
    doc_path: Path,
    project_root: Path,
    symbol_hint: str | None = None,
) -> dict:
    """Fully validate a CitationRef and return a result dict.

    Result shape:
        {
            "status": STATUS_OK | STATUS_TRAVERSAL | STATUS_FILE_MISSING |
                      STATUS_UNREADABLE | STATUS_RANGE_INVALID | STATUS_STALE,
            "resolved_path": Path | None,
            "lines": list[str] | None,   # the cited span (1-based start..end), if ok
            "encoding": str | None,
            "line_count": int | None,    # total lines in the resolved file
        }

    STATUS_STALE fires when symbol_hint is provided and is NOT found in the cited span.
    Caller maps status → UNVERIFIABLE for all non-ok statuses.
    """
    if _is_traversal(ref.raw_path):
        return {"status": STATUS_TRAVERSAL, "resolved_path": None,
                "lines": None, "encoding": None, "line_count": None}

    resolved = resolve_citation(ref.raw_path, doc_path, project_root)
    if resolved is None:
        return {"status": STATUS_FILE_MISSING, "resolved_path": None,
                "lines": None, "encoding": None, "line_count": None}

    result = read_text_safe(resolved)
    if result is None:
        return {"status": STATUS_UNREADABLE, "resolved_path": resolved,
                "lines": None, "encoding": None, "line_count": None}

    text, encoding = result
    all_lines = text.splitlines()
    line_count = len(all_lines)

    start, end = ref.start, ref.end
    if start < 1 or end < start or end > line_count:
        return {"status": STATUS_RANGE_INVALID, "resolved_path": resolved,
                "lines": None, "encoding": encoding, "line_count": line_count}

    span_lines = all_lines[start - 1: end]  # 1-based → 0-based slice

    # Stale-anchor plausibility check (legacy group C)
    if symbol_hint:
        span_text = "\n".join(span_lines)
        if symbol_hint not in span_text:
            return {"status": STATUS_STALE, "resolved_path": resolved,
                    "lines": span_lines, "encoding": encoding, "line_count": line_count}

    return {"status": STATUS_OK, "resolved_path": resolved,
            "lines": span_lines, "encoding": encoding, "line_count": line_count}
