#!/usr/bin/env python3
"""Skeleton-identity validator for translation mirrors.

Compares a primary-language artifact against its translated mirror and asserts
that the "skeleton" (headings, code tokens, field labels, table-header rows,
fenced-code blocks, frontmatter keys) is byte-identical. Only prose differs.

Exit codes: 0 = PASS, 1 = CRITICAL (skeleton drift), 2 = arg/IO error.
Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _spec_parse import parse_headings_and_blocks  # noqa: E402

CODE_TOKEN_RE = re.compile(
    r"\b(?:F\d{3,4}|US\d{3,4}|SCR\d{3,4}[a-z]?|BL\d{3,4}|PERM\d{3,4}"
    r"|DEC-\d{3,4}|DISC-\d{3,4}|MODEL\d{3,4}|FLOW\d{3,4}"
    r"|REG\d{3,4}|INT-\d{3,4}|BR-\d{3,4}|SM-\d{3,4}|ALG-\d{3,4})\b"
)
FIELD_LABEL_RE = re.compile(r"^\s*\*\*[A-Za-z][A-Za-z0-9 _/-]+:\*\*")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
FRONTMATTER_FENCE = "---"

# [Sec-F6] Body-ratio guard. The skeleton check proves structure is identical but
# cannot tell whether the translator silently dropped a prose paragraph. A translated
# body more than this fraction shorter/longer than the source body is a soft FAIL
# (same handling as skeleton drift: exit 1 → retry). Catches gross omission/padding
# without a semantic oracle.
BODY_RATIO_TOLERANCE = 0.30


def extract_skeleton(lines: list[str]) -> list[tuple[int, str]]:
    """Extract ordered skeleton signature from markdown lines.

    Returns list of (line_number, skeleton_line) where skeleton_line is one of:
    - heading line (verbatim)
    - table-header row (line before a separator row)
    - table separator row
    - fenced code block content (``` opener/closer + body)
    - field label line (e.g. **Linked FR:**)
    - frontmatter fence lines (---)
    - lines containing code tokens (F###, US###, etc.) — the tokens only
    """
    skeleton: list[tuple[int, str]] = []
    headings, blocks = parse_headings_and_blocks(lines)

    in_frontmatter = False
    frontmatter_done = False
    in_fence = False
    fence_start = -1

    for i, line in enumerate(lines):
        stripped = line.rstrip()

        # Frontmatter detection (only at start of file)
        if i == 0 and stripped == FRONTMATTER_FENCE:
            in_frontmatter = True
            skeleton.append((i, stripped))
            continue
        if in_frontmatter and not frontmatter_done:
            if stripped == FRONTMATTER_FENCE:
                frontmatter_done = True
                in_frontmatter = False
            skeleton.append((i, stripped))
            continue

        # Fenced code blocks — entire content is skeleton
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = i
                skeleton.append((i, stripped))
            else:
                in_fence = False
                skeleton.append((i, stripped))
            continue
        if in_fence:
            skeleton.append((i, stripped))
            continue

        # Headings (outside fences — already filtered by parse_headings_and_blocks)
        if stripped.startswith("#"):
            skeleton.append((i, stripped))
            continue

        # Table separator rows
        if TABLE_SEP_RE.match(stripped):
            skeleton.append((i, stripped))
            # The line before a separator is the header row
            if i > 0:
                prev = lines[i - 1].rstrip()
                if prev.startswith("|"):
                    skeleton.append((i - 1, prev))
            continue

        # Field labels (**Label:**)
        if FIELD_LABEL_RE.match(stripped):
            skeleton.append((i, stripped))
            continue

        # Lines with code tokens — extract tokens only for comparison
        tokens = CODE_TOKEN_RE.findall(stripped)
        if tokens:
            skeleton.append((i, " ".join(sorted(tokens))))

    # Sort by line number and deduplicate
    seen: set[int] = set()
    result: list[tuple[int, str]] = []
    for lineno, content in sorted(skeleton, key=lambda x: x[0]):
        if lineno not in seen:
            seen.add(lineno)
            result.append((lineno, content))

    return result


def count_body_lines(lines: list[str], skeleton: list[tuple[int, str]]) -> int:
    """Count prose (body) lines: non-blank lines that are NOT part of the skeleton."""
    skel_linenos = {lineno for lineno, _ in skeleton}
    return sum(
        1 for i, line in enumerate(lines)
        if line.strip() and i not in skel_linenos
    )


def check_body_ratio(
    primary_lines: list[str],
    mirror_lines: list[str],
    primary_skel: list[tuple[int, str]],
    mirror_skel: list[tuple[int, str]],
) -> dict | None:
    """Return an issue dict if the translated body deviates beyond tolerance, else None."""
    primary_body = count_body_lines(primary_lines, primary_skel)
    mirror_body = count_body_lines(mirror_lines, mirror_skel)
    if primary_body == 0:
        return None  # nothing to compare (skeleton-only artifact)
    ratio = mirror_body / primary_body
    if ratio < (1 - BODY_RATIO_TOLERANCE) or ratio > (1 + BODY_RATIO_TOLERANCE):
        return {
            "line": 0,
            "message": (
                f"body-size drift: mirror has {mirror_body} prose lines vs primary {primary_body} "
                f"(ratio {ratio:.2f}, tolerance ±{BODY_RATIO_TOLERANCE:.0%}) — likely omitted or "
                f"padded prose"
            ),
            "severity": "critical",
        }
    return None


def validate(primary_path: Path, mirror_path: Path) -> list[dict]:
    """Compare skeletons + body size. Returns list of issues (empty = PASS)."""
    issues: list[dict] = []

    try:
        primary_lines = primary_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return [{"line": 0, "message": f"cannot read primary: {e}", "severity": "critical"}]

    try:
        mirror_lines = mirror_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return [{"line": 0, "message": f"cannot read mirror: {e}", "severity": "critical"}]

    primary_skel = extract_skeleton(primary_lines)
    mirror_skel = extract_skeleton(mirror_lines)

    # Compare skeleton lengths
    if len(primary_skel) != len(mirror_skel):
        issues.append({
            "line": 0,
            "message": (
                f"skeleton length mismatch: primary has {len(primary_skel)} elements, "
                f"mirror has {len(mirror_skel)}"
            ),
            "severity": "critical",
        })
        # Still compare as far as possible
        max_len = max(len(primary_skel), len(mirror_skel))
    else:
        max_len = len(primary_skel)

    for idx in range(min(len(primary_skel), len(mirror_skel))):
        p_line, p_content = primary_skel[idx]
        m_line, m_content = mirror_skel[idx]
        if p_content != m_content:
            issues.append({
                "line": m_line + 1,
                "message": (
                    f"skeleton drift at element {idx}: "
                    f"primary L{p_line + 1}={p_content!r} vs mirror L{m_line + 1}={m_content!r}"
                ),
                "severity": "critical",
            })
            break  # Report first divergence only

    # Extra elements in one side
    if len(primary_skel) > len(mirror_skel):
        extra = primary_skel[len(mirror_skel)]
        issues.append({
            "line": extra[0] + 1,
            "message": f"primary has extra skeleton element at L{extra[0] + 1}: {extra[1]!r}",
            "severity": "critical",
        })
    elif len(mirror_skel) > len(primary_skel):
        extra = mirror_skel[len(primary_skel)]
        issues.append({
            "line": extra[0] + 1,
            "message": f"mirror has extra skeleton element at L{extra[0] + 1}: {extra[1]!r}",
            "severity": "critical",
        })

    # [Sec-F6] Body-size guard — catches dropped/padded prose the skeleton check misses.
    body_issue = check_body_ratio(primary_lines, mirror_lines, primary_skel, mirror_skel)
    if body_issue:
        issues.append(body_issue)

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skeleton-identity validator for translation mirrors")
    parser.add_argument("--primary", required=True, help="Path to primary-language artifact")
    parser.add_argument("--mirror", required=True, help="Path to translated mirror artifact")
    args = parser.parse_args(argv)

    primary = Path(args.primary)
    mirror = Path(args.mirror)

    if not primary.is_file():
        print(f"[ERROR] primary not found: {primary}", file=sys.stderr)
        return 2
    if not mirror.is_file():
        print(f"[ERROR] mirror not found: {mirror}", file=sys.stderr)
        return 2

    issues = validate(primary, mirror)
    if not issues:
        print(f"PASS — skeleton identical: {primary.name} ↔ {mirror.name}")
        return 0

    for issue in issues:
        print(f"[{issue['severity'].upper()}] L{issue['line']}: {issue['message']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
