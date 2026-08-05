#!/usr/bin/env python3
"""Pure markdown parsers for the llms.txt generator — no filesystem walking, pure stdlib.
Separated from discovery.py (which owns the ladder + fs traversal) so parsing stays testable
in isolation.
"""
import re
from pathlib import Path

DESC_MAX = 160


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def h1_title(content: str, fallback: Path) -> str:
    """First H1 OUTSIDE a fenced code block; else the file stem, title-cased."""
    in_fence = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            m = re.match(r"#\s+(.+)$", line.strip())
            if m:
                return m.group(1).strip()
    return fallback.stem.replace("-", " ").replace("_", " ").title()


def extract_description(content: str) -> str:
    """Baseline description: first prose paragraph after the H1, skipping frontmatter,
    headings, lists, bold-key metadata (`**Key**:`), and fenced code blocks (a blockquote
    counts). Truncated to DESC_MAX chars. The LLM step enriches this."""
    seen_h1 = in_fence = False
    para = []
    for raw in content.splitlines():
        s = raw.strip()
        if s.startswith("```"):
            if para:
                break
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not seen_h1:
            if s.startswith("# "):
                seen_h1 = True
            continue
        if not s:
            if para:
                break
            continue
        if s.startswith("#") or s.startswith("---"):
            if para:
                break
            continue
        if s.startswith(">"):
            para.append(s.lstrip("> ").strip())
            continue
        if s.startswith(("- ", "* ", "| ")):
            if para:
                break
            continue
        if re.match(r"\*\*[^*]+\*\*:\s", s):  # bold-key metadata (**Project**: …) — not prose
            continue
        para.append(s)
    desc = " ".join(para).strip()
    if len(desc) > DESC_MAX:
        desc = desc[: DESC_MAX - 1].rsplit(" ", 1)[0] + "…"
    return desc


def project_field(content: str) -> str:
    """Product name from the `**Project**: X` line of a rebuild-spec overview (its H1 is the
    hardcoded '# System Overview'). Ignored if still an unfilled placeholder ({...})."""
    m = re.search(r"^\*\*Project\*\*:\s*(.+)$", content, re.MULTILINE)
    if m:
        val = m.group(1).strip()
        if val and not (val.startswith("{") and val.endswith("}")):
            return val
    return ""
