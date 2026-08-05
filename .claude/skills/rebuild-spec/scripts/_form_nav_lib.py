#!/usr/bin/env python3
r"""Form-navigation parsing helpers for extract_form_nav.py.

LIMITATION: `with` blocks / aliased form vars defeat naive regex →
conservative unverified emit. Reuses _DELPHI_COMMENT (DRY). Stdlib only.
"""
from __future__ import annotations

import re
from typing import Any

from _sql_dml_lib import _DELPHI_COMMENT


def strip_line_comment(line: str) -> str:
    return _DELPHI_COMMENT.sub("", line).rstrip()


def strip_block_comments(text: str) -> str:
    """Remove { } and (* *) block comments; preserve newlines for line numbering."""
    result: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if depth == 0:
            if text[i] == '{':
                depth += 1; i += 1; continue
            if text[i:i+2] == '(*':
                depth += 1; i += 2; continue
            result.append(text[i]); i += 1
        else:
            if text[i] == '}':
                depth -= 1; i += 1; continue
            if text[i:i+2] == '*)':
                depth -= 1; i += 2; continue
            if text[i] == '\n':
                result.append('\n')
            i += 1
    return ''.join(result)


# Nav-call patterns
_RE_VAR_SHOW = re.compile(r'\b(\w+)\.(Show(?:Modal)?)\s*[;(]', re.IGNORECASE)
_RE_CREATE_FORM = re.compile(
    r'\bApplication\.CreateForm\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', re.IGNORECASE
)
_RE_CLASS_CREATE_SHOW = re.compile(
    r'\b(T\w+)\.Create\s*\([^)]*\)\.(Show(?:Modal)?)\s*[;(]', re.IGNORECASE
)

# uses clause
_RE_USES_BLOCK = re.compile(r'\buses\b(.*?);', re.IGNORECASE | re.DOTALL)
_RE_IDENT = re.compile(r'\b([A-Za-z_]\w*)\b')

# Form class / var declarations
_RE_FORM_TYPE = re.compile(
    r'\b(T\w+)\s*=\s*class\s*\(\s*T(?:Form|CustomForm)\w*\s*\)', re.IGNORECASE
)
_RE_VAR_DECL = re.compile(r'\b(\w+)\s*:\s*(T\w+)\s*;', re.IGNORECASE)

# .dpr / unit name
_RE_DPR_CREATE = re.compile(
    r'\bApplication\.CreateForm\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', re.IGNORECASE
)
_RE_UNIT_DECL = re.compile(r'^\s*unit\s+(\w+)\s*;', re.IGNORECASE)


def extract_uses(text: str) -> list[str]:
    units: list[str] = []
    for m in _RE_USES_BLOCK.finditer(text):
        clause = ' '.join(strip_line_comment(ln) for ln in m.group(1).split('\n'))
        units.extend(_RE_IDENT.findall(clause))
    return units


def extract_form_declarations(text: str) -> dict[str, str]:
    """Return {var_name: class_name} for global form var declarations."""
    form_classes = {m.group(1) for m in _RE_FORM_TYPE.finditer(text)}
    return {
        m.group(1): m.group(2)
        for m in _RE_VAR_DECL.finditer(text)
        if m.group(2) in form_classes
    }


def extract_dpr_forms(dpr_text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _RE_DPR_CREATE.finditer(dpr_text)]


def parse_nav_line(
    line: str,
    line_no: int,
    rel_path: str,
    var_to_class: dict[str, str],
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for m in _RE_VAR_SHOW.finditer(line):
        var, method = m.group(1), m.group(2).lower()
        kind = "showmodal" if "modal" in method else "shows"
        cls = var_to_class.get(var)
        edges.append({"to_class": cls or var, "kind": kind,
                      "file": rel_path, "line": line_no, "unverified": cls is None})
    for m in _RE_CREATE_FORM.finditer(line):
        edges.append({"to_class": m.group(1), "kind": "creates",
                      "file": rel_path, "line": line_no, "unverified": False})
    for m in _RE_CLASS_CREATE_SHOW.finditer(line):
        method = m.group(2).lower()
        kind = "showmodal" if "modal" in method else "shows"
        edges.append({"to_class": m.group(1), "kind": kind,
                      "file": rel_path, "line": line_no, "unverified": False})
    return edges


def analyse_unit(
    path: Any,  # pathlib.Path; avoid import cycle
    root: Any,
    text: str,
    warns: list[str],
) -> dict[str, Any]:
    """Parse one .pas file text into a unit analysis dict."""
    rel = str(path.relative_to(root))
    stripped = strip_block_comments(text)
    lines = stripped.splitlines()

    unit_name: str = path.stem
    for ln in lines[:10]:
        m = _RE_UNIT_DECL.match(ln)
        if m:
            unit_name = m.group(1); break

    var_to_class = extract_form_declarations(stripped)
    form_classes = [m.group(1) for m in _RE_FORM_TYPE.finditer(stripped)]

    # class → line number of its declaration
    class_decl_line: dict[str, int] = {}
    raw_edges: list[dict[str, Any]] = []
    for line_no, raw in enumerate(lines, 1):
        clean = strip_line_comment(raw)
        if not clean.strip():
            continue
        for cls in form_classes:
            if cls not in class_decl_line:
                m2 = re.search(r'\b' + re.escape(cls) + r'\s*=\s*class', clean, re.IGNORECASE)
                if m2:
                    class_decl_line[cls] = line_no
        raw_edges.extend(parse_nav_line(clean, line_no, rel, var_to_class))

    return {
        "unit_name": unit_name,
        "file": rel,
        "form_classes": form_classes,
        "var_to_class": var_to_class,
        "class_decl_line": class_decl_line,
        "uses": extract_uses(stripped),
        "raw_edges": raw_edges,
    }
