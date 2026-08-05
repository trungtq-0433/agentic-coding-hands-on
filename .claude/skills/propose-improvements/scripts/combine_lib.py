"""Pure-Python helpers for propose-improvements Step 5a (combine-proposals).

Authoritative implementation of the procedure described in
`claude/skills/propose-improvements/references/combine-proposals.md`. No I/O happens here;
all functions operate on strings / Path objects. The CLI wrapper
(`combine_proposals.py`) handles filesystem reads, atomic writes, and stdout.

CommonMark-compliance highlights:
  - ATX headings allow 0-3 leading spaces (regex `^ {0,3}#`).
  - Heading demotion skips lines inside fenced code blocks. Fence tracking
    matches the opening fence character (backtick or tilde) and requires the
    closing fence to use the same character with run-length >= opening
    (CommonMark Section 4.5).
  - H1 stripping handles ATX (`# Title`) and setext (`Title\n====`).
  - HTML comments (`<!-- ... -->`) pass through verbatim regardless of
    location; we never strip or rewrite them.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

# Heading regexes - 0-3 leading spaces per CommonMark.
_ATX_H1_RE = re.compile(r"^ {0,3}# (?!#)")
_ATX_H2_RE = re.compile(r"^ {0,3}## (?!#)")
_ATX_H3_RE = re.compile(r"^ {0,3}### (?!#)")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_USE_CONTEXT_RE = re.compile(
    r"^\s*\*\*Use context:\*\*\s+(internal|hybrid|customer-facing)\s*$",
    re.IGNORECASE,
)
_HTML_COMMENT_LINE_RE = re.compile(r"^\s*<!--.*-->\s*$")
VALID_USE_CONTEXTS = {"internal", "hybrid", "customer-facing"}


def parse_use_context_marker(body: str) -> str | None:
    """Scan the header region (first 10 lines or until first `## ` heading)
    for the `**Use context:** <value>` marker. Returns the lowercase value or
    None when missing/invalid.
    """
    for idx, line in enumerate(body.splitlines()):
        if idx >= 10:
            break
        if _ATX_H2_RE.match(line):
            break
        m = _USE_CONTEXT_RE.match(line)
        if m:
            return m.group(1).lower()
    return None


def strip_h1_and_use_context(body: str) -> str:
    """Remove leading H1 (ATX or setext) plus the `**Use context:**` line that
    follows it, including blank-line padding and an optional surrounding
    HTML comment immediately above or below the marker.

    Behaviour mirrors `combine-proposals.md` Procedure step 5 (intro) and
    `Heading detection` rules:
      - Strip ATX `# Title` (with 0-3 leading spaces) OR setext
        `Title\\n====` (underline of `=` or `-`).
      - Then strip the `**Use context:** X` line (optional blank line(s)
        between H1 and marker).
      - HTML comments surrounding the use-context line are stripped
        only when adjacent to it. Comments elsewhere pass through.
    """
    lines = body.splitlines()
    n = len(lines)
    i = 0

    # Skip leading blank lines.
    while i < n and lines[i].strip() == "":
        i += 1

    if i >= n:
        return body

    # Try ATX H1 first.
    stripped_h1 = False
    if _ATX_H1_RE.match(lines[i]):
        i += 1
        stripped_h1 = True
    elif i + 1 < n and _is_setext_underline(lines[i + 1]):
        # Setext: a non-blank text line followed by `===` or `---` underline.
        i += 2
        stripped_h1 = True

    if not stripped_h1:
        return body

    # Optional blank line(s) + optional preceding HTML comment + use-context line +
    # optional trailing HTML comment.
    j = i
    while j < n and lines[j].strip() == "":
        j += 1
    pre_comment = -1
    if j < n and _HTML_COMMENT_LINE_RE.match(lines[j]) and "use context" not in lines[j].lower():
        pre_comment = j
        j += 1
        while j < n and lines[j].strip() == "":
            j += 1
    if j < n and _USE_CONTEXT_RE.match(lines[j]):
        use_ctx_line = j
        j += 1
        # Optional trailing comment IMMEDIATELY after the marker (no blank in
        # between). The template emits marker + comment on adjacent lines; a
        # blank-separated comment is treated as document content and passes
        # through verbatim per the "HTML comments pass through" rule.
        post_comment = -1
        if j < n and _HTML_COMMENT_LINE_RE.match(lines[j]) and "use context" not in lines[j].lower():
            post_comment = j
        # Remove H1 + use-context (+ adjacent comments) + their surrounding blanks.
        drop = set()
        # Everything from 0..i (H1 + leading blanks already passed) is dropped.
        for x in range(0, i):
            drop.add(x)
        # The blanks between H1 and (comment|use-context).
        for x in range(i, j):
            drop.add(x)
        if pre_comment >= 0:
            drop.add(pre_comment)
        drop.add(use_ctx_line)
        if post_comment >= 0:
            drop.add(post_comment)
        kept = [ln for idx, ln in enumerate(lines) if idx not in drop]
        return _trim_leading_blanks(kept)

    # H1 stripped but no use-context line - drop H1 only, keep rest.
    return _trim_leading_blanks(lines[i:])


def _is_setext_underline(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s[0] not in "=-":
        return False
    return all(ch == s[0] for ch in s)


def _trim_leading_blanks(lines: list[str]) -> str:
    start = 0
    while start < len(lines) and lines[start].strip() == "":
        start += 1
    out = "\n".join(lines[start:])
    return out


def demote_headings(body: str) -> str:
    """Apply Procedure step 5a then 5b in strict order.

    - Pass A: every `### <title>` ATX H3 -> `#### <title>` H4.
    - Pass B: every `## <title>` ATX H2  -> `### <title>` H3.

    Lines inside fenced code blocks are NOT touched. Fence char + run-length
    matched per CommonMark Section 4.5.
    Order is critical: running B first would catch the freshly-demoted
    `### <Item>` lines and double-demote them.
    """
    return _demote_pass(_demote_pass(body, _ATX_H3_RE, "###", "####"),
                        _ATX_H2_RE, "##", "###")


def _demote_pass(body: str, pattern: re.Pattern[str], old_prefix: str, new_prefix: str) -> str:
    """Run one demotion pass over the body, skipping fenced code regions."""
    lines = body.splitlines(keepends=False)
    fence_char: str | None = None
    fence_len = 0
    out: list[str] = []
    for line in lines:
        if fence_char is None:
            fm = _FENCE_OPEN_RE.match(line)
            if fm:
                marker = fm.group(1)
                fence_char = marker[0]
                fence_len = len(marker)
                out.append(line)
                continue
            if pattern.match(line):
                # Replace only the leading hash run; preserve any leading whitespace and trailing content.
                # `### Foo` -> `#### Foo`; `   ## Bar` -> `   ### Bar`.
                stripped = line.lstrip(" ")
                lead_ws = line[: len(line) - len(stripped)]
                # stripped starts with old_prefix + ' '
                out.append(f"{lead_ws}{new_prefix}{stripped[len(old_prefix):]}")
            else:
                out.append(line)
        else:
            # Inside a fence - look for matching close.
            cm = _FENCE_OPEN_RE.match(line)
            if cm:
                marker = cm.group(1)
                if marker[0] == fence_char and len(marker) >= fence_len:
                    fence_char = None
                    fence_len = 0
            out.append(line)
    # Preserve trailing newline behaviour of input.
    suffix = "\n" if body.endswith("\n") else ""
    return "\n".join(out) + suffix


def validate_paths(*, plans_root: Path, output_path: Path, input_paths: Iterable[Path]) -> None:
    """Reject paths containing null bytes or escaping CWD / plans_root.

    Raises ValueError on the first violation.
    plans_root must be an absolute path inside CWD.
    output_path must resolve inside plans_root.
    Each input path must resolve inside CWD (but not necessarily inside plans/).
    """
    cwd = Path.cwd().resolve()
    plans_resolved = plans_root.resolve()
    if not _is_inside(plans_resolved, cwd):
        raise ValueError(f"plans_root must sit inside CWD: {plans_root}")

    for p in (output_path, *input_paths):
        s = str(p)
        if "\x00" in s:
            raise ValueError(f"null byte in path: {p!r}")

    out_resolved = output_path.resolve()
    if not _is_inside(out_resolved, plans_resolved):
        raise ValueError(f"output_path escapes plans/: {output_path}")

    for p in input_paths:
        resolved = p.resolve()
        if not _is_inside(resolved, cwd):
            raise ValueError(f"input path escapes workspace: {p}")


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def build_combined(
    *,
    project_name: str,
    iso_date: str,
    use_context: str | None,
    tech_body: str | None,
    biz_body: str | None,
) -> str:
    """Assemble the final combined markdown per spec Procedure step 6.

    - Header: `# Improvement Proposal - <project_name>`.
    - Subline: `_Generated <date>. Use context: **<value>**. Based on repository analysis._`
      with the `Use context: **<value>**. ` fragment omitted when use_context is None.
    - `## Technical` section: present only when tech_body provided.
    - `## Business` section: present only when biz_body provided.
    - Trailer: ALWAYS `<!-- dedup: pending -->` regardless of single/multi track.

    tech_body / biz_body should already be demoted and H1-stripped.
    """
    if not tech_body and not biz_body:
        raise ValueError("at least one of tech_body / biz_body must be provided")
    parts: list[str] = []
    parts.append(f"# Improvement Proposal — {project_name}")
    parts.append("")
    if use_context:
        parts.append(f"_Generated {iso_date}. Use context: **{use_context}**. Based on repository analysis._")
    else:
        parts.append(f"_Generated {iso_date}. Based on repository analysis._")
    parts.append("")
    if tech_body is not None:
        parts.append("## Technical")
        parts.append("")
        parts.append(tech_body.rstrip("\n"))
        parts.append("")
    if biz_body is not None:
        parts.append("## Business")
        parts.append("")
        parts.append(biz_body.rstrip("\n"))
        parts.append("")
    parts.append("<!-- dedup: pending -->")
    return "\n".join(parts) + "\n"


def prepare_track_body(raw: str) -> str:
    """Strip H1 + use-context line, then demote headings (3->4, 2->3).

    Convenience function combining `strip_h1_and_use_context` and
    `demote_headings`. Used by the CLI for each track input.
    """
    return demote_headings(strip_h1_and_use_context(raw))
