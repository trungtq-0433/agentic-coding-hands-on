"""Review-report mutation helpers for Wave 7.5 structural fixer.

Handles decrementing `failed:` frontmatter and appending RESOLVED-BY-W7.5
markers to critical-issue subsections that mention 'Linked FR'. Stdlib only.
"""
from __future__ import annotations
import re
from pathlib import Path

FRONTMATTER_FAILED_RE = re.compile(r"^(failed:\s*)(\d+)", re.MULTILINE)
FRONTMATTER_RESULT_RE = re.compile(r"^(result:\s*)\S+", re.MULTILINE)
CRITICAL_SECTION_RE = re.compile(r"^## Critical Issues", re.MULTILINE)
LINKED_FR_ISSUE_RE = re.compile(r"Linked FR", re.IGNORECASE)
ISSUE_TITLE_RE = re.compile(r"^(###\s+.+?)(\s*)$", re.MULTILINE)
RESOLVED_MARKER = " — RESOLVED-BY-W7.5"


def count_linked_fr_critical(report_text: str) -> int:
    """Count unresolved ### titles in ## Critical Issues that mention 'Linked FR'."""
    m = CRITICAL_SECTION_RE.search(report_text)
    if not m:
        return 0
    section = report_text[m.end():]
    next_h2 = re.search(r"^## ", section, re.MULTILINE)
    if next_h2:
        section = section[: next_h2.start()]
    return sum(
        1 for ln in section.splitlines()
        if ln.startswith("### ") and LINKED_FR_ISSUE_RE.search(ln) and RESOLVED_MARKER not in ln
    )


def mutate_review_report(report_path: Path, blocks_fixed: int, atomic_write_fn) -> None:
    """Decrement failed; mark resolved critical issues; set result: PASS if failed reaches 0.

    atomic_write_fn(path, text) must be provided by caller to avoid circular imports.
    """
    text = report_path.read_text(encoding="utf-8")
    delta = min(blocks_fixed, count_linked_fr_critical(text))
    if delta == 0:
        return

    fm_match = FRONTMATTER_FAILED_RE.search(text)
    if fm_match:
        new_val = max(0, int(fm_match.group(2)) - delta)
        text = text[: fm_match.start(2)] + str(new_val) + text[fm_match.end(2):]
        if new_val == 0:
            missing_match = re.search(r"^missing:\s*(\d+)", text, re.MULTILINE)
            missing_val = int(missing_match.group(1)) if missing_match else 0
            if missing_val == 0:
                res_match = FRONTMATTER_RESULT_RE.search(text)
                if res_match:
                    text = text[: res_match.start(1)] + res_match.group(1) + "PASS" + text[res_match.end():]

    resolved = 0

    def _mark(m: re.Match) -> str:
        nonlocal resolved
        title = m.group(1)
        if LINKED_FR_ISSUE_RE.search(title) and RESOLVED_MARKER not in title and resolved < delta:
            resolved += 1
            return title + RESOLVED_MARKER + m.group(2)
        return m.group(0)

    crit_m = CRITICAL_SECTION_RE.search(text)
    if crit_m:
        before = text[: crit_m.end()]
        after = text[crit_m.end():]
        next_h2 = re.search(r"^## ", after, re.MULTILINE)
        if next_h2:
            text = before + ISSUE_TITLE_RE.sub(_mark, after[: next_h2.start()]) + after[next_h2.start():]
        else:
            text = before + ISSUE_TITLE_RE.sub(_mark, after)

    atomic_write_fn(report_path, text)
