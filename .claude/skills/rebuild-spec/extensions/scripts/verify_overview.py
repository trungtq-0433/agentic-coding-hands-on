#!/usr/bin/env python3
"""Deterministic token-leak gate for the rebuild-spec --overview pass (OV.3).

The --overview deliverable is client-facing: every system/technical identifier must have
been replaced with business terminology (see the OV.2 client-ify mapping in overview-pass.md).
This script is the HARD, machine gate behind the OV.3 reviewer — it greps the assembled
Markdown for a PINNED set of system tokens and exits non-zero if any survive. Unlike an LLM
reviewer, it is repeatable and cannot "miss" a leak.

Stdlib only. Usage:
    python3 verify_overview.py docs/<ProjectName>_System_Overview.md

Exit 0 = clean (no leftover system tokens). Exit 2 = leak(s) found (report printed).
Exit 1 = usage/IO error.

Scope note: patterns are GENERIC by construction — NO project-specific vocabulary. A client-facing
System Overview is business English, where snake_case identifiers, ID codes, and file:line citations
NEVER legitimately appear. Detecting those classes generically catches leaks on ANY project/stack
(mobile, Rails, Node, Go…) without a hardcoded — and per-project-wrong — token list. The generic
snake_case rule subsumes every former project-specific token (`app_type`, `before_edit`,
`by_permissions`, …) AND any other project's equivalents. Ambiguous bare words such as `editing` /
`published` are intentionally NOT grepped (they collide with business terms "In Editing" /
"Published"); catching those stays the OV.3 reviewer's job.
"""
import re
import sys

# (label, compiled-regex). Generic — stack/project-agnostic. Case-sensitive: lowercase system
# tokens won't fire on the capitalized business terms they map to (e.g. "Published").
LEAK_PATTERNS = [
    # any lowercase snake_case identifier — the universal signal of a leaked system token
    # (column/flag/enum/scope/method names). Replaces the old hardcoded foreign-project lists.
    ("snake_case identifier", re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")),
    ("entity ID code", re.compile(r"\b(F|SCR|BL|PERM)\d{3}\b")),
    ("model / discriminator code", re.compile(r"\b(MODEL|DISC)-\d{3}\b")),
    # file:line citation — extension list covers mobile (kt/swift) + backend + web stacks
    ("file:line citation", re.compile(
        r"\b[\w/.-]+\.(rb|rake|erb|haml|slim|py|tsx|ts|jsx|js|mjs|cjs|vue|yml|yaml|"
        r"kt|kts|swift|java|scala|go|rs|m|mm|cs|php|c|cc|cpp|h|hpp|dart|ex|exs):\d+\b")),
]


_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")   # ](url) → drop the target, keep link text
_URL_RE = re.compile(r"https?://\S+")


def scan(text):
    """Return list of (lineno, label, matched_text, line) for every leak found.

    Fenced code blocks and link/URL targets are excluded: a snake_case identifier or
    file:line inside a code example or a URL path is not a leaked token in client-facing
    prose, and firing on them produces false FAILs that block legitimate overviews.
    """
    findings = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        scrubbed = _LINK_TARGET_RE.sub("](", line)   # strip ](url) targets, keep [text]
        scrubbed = _URL_RE.sub("", scrubbed)          # strip bare URLs
        for label, rx in LEAK_PATTERNS:
            for m in rx.finditer(scrubbed):
                findings.append((lineno, label, m.group(0), line.strip()))
    return findings


def main(argv):
    if len(argv) != 1:
        sys.stderr.write("usage: verify_overview.py <system-overview.md>\n")
        return 1
    path = argv[0]
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        sys.stderr.write(f"ERROR: cannot read {path}: {e}\n")
        return 1

    findings = scan(text)
    if not findings:
        print(f"RESULT: CLEAN — 0 leftover system tokens in {path}.")
        return 0

    print(f"=== SYSTEM-TOKEN LEAKS ({len(findings)}) — client-ify incomplete ===")
    print(f"{'line':>5}  {'category':<28} token")
    for lineno, label, token, _line in findings[:200]:
        print(f"{lineno:>5}  {label:<28} {token}")
    if len(findings) > 200:
        print(f"... +{len(findings) - 200} more")
    print("\nFix: replace each system token with its business term (see overview-pass.md § OV.2 "
          "client-ify rule), then re-run.")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
