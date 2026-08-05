# layout-exempt: rebuild-spec synthesis scaffolds — docs/system is this skill's own output target
"""Post-fill validator and shared constants for Phase D system synthesis (v19).

v19 BREAKING: validate_filled_scaffold retargeted to a single-arg signature — the
scaffold-vs-filled H2-header-lock comparison is DROPPED entirely (gone since v18).
The function now takes only the authored draft and returns violations when:
  (a) any {{FILL}}/[FILL]/{{SCOUT}} marker remains, OR
  (b) lint_mermaid_safety(draft) returns any violation.

NEW: lint_mermaid_safety(markdown) — scans every ```mermaid fenced block for unsafe
chars that could break out of a node label (raw `"`, backtick, `<`, `>`). Returns a
list of violation strings (empty = safe). Reuses the escape conventions from
_system_synthesis_lib.mermaid_safe_label to decide what counts as "already safe".

`has_unfilled_markers` is extended to also catch {{SCOUT}} markers (belt-and-suspenders
for the promote gate — a leftover {{SCOUT}} means the researcher skipped a block).

DRAFT_SUFFIX, _BANNER, _BANNER_NOTE are kept for backward compat (imported by other modules).

Stdlib only.
"""
from __future__ import annotations

import re

DRAFT_SUFFIX = ".draft.md"

# Marker regex — catches {{FILL...}}, [FILL], AND {{SCOUT...}}.
# The promote gate flags ANY remaining marker of either kind.
_MARKER_RE = re.compile(r"\{\{FILL\b|\[FILL\]|\{\{SCOUT\b")

_BANNER = (
    "<!-- AI-DRAFT: rebuild-spec narrative scaffold — the fill agent completes every "
    "{{FILL:...}} marker, then the orchestrator promotes this to the no-suffix file. -->"
)
_BANNER_NOTE = (
    "> **AI-DRAFT** — prose marked `{{FILL:...}}` is completed by the narrative-fill "
    "agent from each component's `overview.md`. An unfilled marker means no source was "
    "available — keep it verbatim, never hallucinate."
)


def has_unfilled_markers(content: str) -> bool:
    """True if any `{{FILL` / `[FILL]` / `{{SCOUT` marker remains.

    Drives the unfilled_scaffold WARN and the promote gate. {{SCOUT}} markers that were
    not substituted (in v18 style) are treated as unfilled (belt-and-suspenders guard
    against a missed substitution step).
    """
    return bool(_MARKER_RE.search(content))


# ---------------------------------------------------------------------------
# Mermaid-safety lint (v19)
# ---------------------------------------------------------------------------

# Fence splitter — yields the content between ```mermaid and the closing ```.
_MERMAID_FENCE_RE = re.compile(r"```mermaid\b[^\n]*\n(.*?)```", re.DOTALL)

# Unsafe raw character patterns in Mermaid labels (pragmatic, not a full parser).
#
# The safe label form is A["label text"] or |"label text"|. The structural delimiters
# are `["`, `"]`, `|"`, `"|` — these should NOT be flagged. We flag:
#
# 1. A raw `"` that is NOT a structural delimiter: not immediately preceded by `[`
#    or `|`, and not immediately followed by `]` or `|`.
#    Pattern: `"` preceded by [^[|] and followed by [^]|] (using lookahead/behind).
# 2. Raw backtick `` ` `` anywhere inside a fence (could start a code-fence in Markdown).
# 3. Raw `<` not immediately followed by `!` (Mermaid comment start `<!`).
# 4. Raw `>` NOT preceded by `-` (excludes Mermaid arrow syntax `-->`, `-->>`, `->>`).

_UNSAFE_INNER_QUOTE_RE = re.compile(r'(?<![|\[])\"(?![|\]])')
_UNSAFE_BACKTICK_RE = re.compile(r'`')
_UNSAFE_LT_RE = re.compile(r'<(?!!)')       # < not followed by !
_UNSAFE_GT_RE = re.compile(r'(?<![->])>')   # > not preceded by - or > (excludes arrows: --> -->> ->>)


def lint_mermaid_safety(markdown: str) -> list[str]:
    """Scan every ```mermaid fenced block; return a list of violation strings.

    Returns an empty list if all fences are safe. A non-empty list means at least
    one fence has a raw character that could break out of a node label or diagram.

    Rules checked (pragmatic — not a full Mermaid parser):
    - Raw `"` inside label text (unescaped; safe form is #quot;). The structural
      delimiters `["` and `"]` and `|"` and `"|` are NOT flagged.
    - Raw backtick `` ` `` anywhere inside a fence (could open a Markdown code-fence).
    - Raw `<` not followed by `!` (unescaped; could inject HTML in some renderers).
    - Raw `>` (no safe structural use inside a Mermaid node label).
    """
    violations: list[str] = []
    for match in _MERMAID_FENCE_RE.finditer(markdown):
        fence_content = match.group(1)
        for line in fence_content.splitlines():
            stripped = line.strip()
            # Skip pure comment lines and diagram-type declaration lines.
            if stripped.startswith("%%") or stripped.startswith("//"):
                continue
            for pattern, tag in (
                (_UNSAFE_INNER_QUOTE_RE, '"'),
                (_UNSAFE_BACKTICK_RE, '`'),
                (_UNSAFE_LT_RE, '<'),
                (_UNSAFE_GT_RE, '>'),
            ):
                m = pattern.search(line)
                if m:
                    violations.append(
                        f"unsafe_mermaid_label: char {tag!r} "
                        f"at col {m.start()} in: {line!r}"
                    )
                    break  # one violation per line is enough
    return violations


# ---------------------------------------------------------------------------
# Phase-04 — post-fill structural validator (gate before promote, v19)
# ---------------------------------------------------------------------------


def validate_filled_scaffold(draft: str) -> list[str]:
    """Return a list of structural violations (empty = OK to promote).

    v19 signature change: single arg — the authored draft only. The old two-arg
    (scaffold, filled) form that compared H2 headers is REMOVED.

    Violation conditions:
    (a) any {{FILL}}/[FILL]/{{SCOUT}} marker remains in `draft`.
    (b) lint_mermaid_safety(draft) returns any violation (unsafe chars in Mermaid fences).
    """
    violations: list[str] = []
    if has_unfilled_markers(draft):
        violations.append("unfilled_markers: a {{FILL}}/[FILL]/{{SCOUT}} marker still remains")
    violations.extend(lint_mermaid_safety(draft))
    return violations
