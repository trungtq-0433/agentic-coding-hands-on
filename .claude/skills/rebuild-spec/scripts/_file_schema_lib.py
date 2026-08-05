"""Shared file-exchange vocab + populated **File Schema** detection. Stdlib only.

Single source of truth for the heuristic used by BOTH:
  - validate_behavior_logic.py  (rule BehaviorLogic.file_schema_missing)
  - validate_feature_spec.py    (rule FeatureSpec.alg_file_schema_missing, ALG-### blocks only)

Detection is deterministic (regex/string match), never semantic:
  1. is_file_exchange(text)          — does the block's text match import/export vocab?
  2. has_populated_file_schema(body) — does the block have an actual **File Schema** table,
                                        as opposed to the vague placeholder or the literal
                                        "N/A — not a file-exchange type" string?

N/A-misuse (vocab match TRUE but block declares the N/A string anyway — a contradiction)
is treated as "not populated" from the caller's perspective: has_populated_file_schema()
returns False for it, so both validators inherit the same warning behavior for free.
"""
from __future__ import annotations

import re

FILE_EXCHANGE_VOCAB = frozenset({
    "import", "export", "csv", "xlsx", "upload", "download", "bulk",
})

# Word-boundary match so "important"/"reporting" never match "import"/"port".
_VOCAB_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in FILE_EXCHANGE_VOCAB) + r")\b",
    re.IGNORECASE,
)

_FILE_SCHEMA_LABEL_RE = re.compile(r"\*\*File Schema\*\*", re.IGNORECASE)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_NA_STRING_RE = re.compile(r"N/A\s*—\s*not a file-exchange type", re.IGNORECASE)


def is_file_exchange(text: str) -> bool:
    """True if text contains an import/export vocab word (case-insensitive, \\b-bounded).

    Does NOT match substrings like "important" or "reporting" — the word-boundary regex
    requires 'import'/'port' to appear as a standalone word.
    """
    return bool(_VOCAB_RE.search(text))


def has_populated_file_schema(body: str) -> bool:
    """True if body has a **File Schema** label followed by an actual markdown table row.

    False when:
      - the label is absent entirely,
      - the label is present but followed only by the vague template placeholder
        (no real table row — e.g. still contains the literal `{` `}` placeholder syntax
        or the N/A string),
      - the label is present but the N/A string is used (contradiction/misuse — this is
        "not populated" regardless of vocab match; callers decide whether to warn).
    """
    m = _FILE_SCHEMA_LABEL_RE.search(body)
    if not m:
        return False

    # Look at the text following the label (rest of body from the label onward).
    after_label = body[m.end():]

    # N/A string used → not populated (misuse is handled by the caller via is_file_exchange).
    if _NA_STRING_RE.search(after_label.splitlines()[0] if after_label.splitlines() else ""):
        return False

    # Placeholder braces still present right after the label → template not filled in.
    stripped = after_label.lstrip(" :*")
    if stripped.startswith("{"):
        return False

    # Require an actual markdown table row (| ... |) somewhere after the label.
    return bool(_TABLE_ROW_RE.search(after_label))
