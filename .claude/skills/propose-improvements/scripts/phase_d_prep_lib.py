"""Pure-Python helpers for propose-improvements Step 5c (validation prep).

Splits combined-initial.md into one per-item validation payload + a manifest.
Each payload carries ONLY the proposal item (the item's markdown); the validator
self-verifies it against the real repo and writes a verdict per
`templates/validation-item.md`. The manifest tells the orchestrator how many
items exist and where each verdict goes.

No I/O orchestration here — see `phase_d_prep.py` for the wrapper that handles
filesystem reads, atomic writes, manifest construction, and stdout.

Fence-awareness reuses `combine_lib._FENCE_OPEN_RE` so item walking matches
the same CommonMark rules as Step 5a's combine routine.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

# Re-use the fence-tracking regex from combine_lib for consistency with Step 5a.
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_ATX_H2_RE = re.compile(r"^ {0,3}## (?!#)")
_ATX_H4_RE = re.compile(r"^ {0,3}#### (?!#)")
_SLUG_VALIDATE_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*$")


@dataclass
class Item:
    index: int
    title: str
    slug: str
    track: str  # "technical" | "business"
    body: str  # the full block from #### onwards, fence-aware
    line_no: int  # 0-based start of the #### line in combined-initial.md


# ---------------------------------------------------------------------------
# SHA + slug + path safety
# ---------------------------------------------------------------------------

def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def title_to_slug(title: str) -> str:
    """Verbatim regex from apply-validations.md step 6."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


def validate_filename_slug(slug: str) -> bool:
    """Per spec: `<slug>` matches `^[a-z0-9][a-z0-9\\-]*$`."""
    return bool(_SLUG_VALIDATE_RE.match(slug))


def assert_under_plans(path: Path, plans_root: Path) -> None:
    """Reject paths that escape plans_root via .. or null bytes."""
    s = str(path)
    if "\x00" in s or ".." in path.parts:
        raise ValueError(f"unsafe path component in {path!r}")
    # Resolve against plans_root; require it's inside.
    try:
        path.resolve().relative_to(plans_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path {path} escapes plans_root {plans_root}") from exc


# ---------------------------------------------------------------------------
# Item walker (fence-aware)
# ---------------------------------------------------------------------------

def parse_items(combined_text: str) -> list[Item]:
    """Walk combined-initial.md fence-aware. Collect each `#### <title>` block
    and tag it with its enclosing `## Technical` / `## Business` parent. Item
    indices are 1-based in document order (Technical first if present). Items
    outside a Technical/Business section are ignored (combine only emits
    active-track sections, so every real item is always under one of the two).
    """
    lines = combined_text.splitlines()
    in_fence = False
    fence_char = ""
    fence_len = 0

    items: list[Item] = []
    current_track: str | None = None
    block_start: int | None = None
    block_title: str = ""

    def flush(end_line: int) -> None:
        nonlocal block_start, block_title
        if block_start is None:
            return
        body = "\n".join(lines[block_start:end_line]).rstrip("\n")
        # Trailing newline preserved by writer if needed.
        if current_track is None:
            block_start = None
            return
        items.append(Item(
            index=len(items) + 1,
            title=block_title,
            slug=title_to_slug(block_title),
            track=current_track,
            body=body,
            line_no=block_start,
        ))
        block_start = None
        block_title = ""

    for i, line in enumerate(lines):
        if in_fence:
            m = _FENCE_OPEN_RE.match(line)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                in_fence = False
            continue
        fm = _FENCE_OPEN_RE.match(line)
        if fm:
            in_fence = True
            fence_char = fm.group(1)[0]
            fence_len = len(fm.group(1))
            continue

        # Track-switch on `## Technical` / `## Business`.
        if _ATX_H2_RE.match(line):
            flush(i)
            stripped = line.lstrip(" #").strip().lower()
            if stripped.startswith("technical"):
                current_track = "technical"
            elif stripped.startswith("business"):
                current_track = "business"
            else:
                current_track = None
            continue

        if _ATX_H4_RE.match(line):
            flush(i)
            block_title = line.lstrip(" #").strip()
            block_start = i
            continue

    flush(len(lines))
    return items


# ---------------------------------------------------------------------------
# Item-markdown rewrite
# ---------------------------------------------------------------------------

def rewrite_h4_to_h2(item_body: str) -> str:
    """Rewrite the leading `^ {0,3}#### <title>` → `## <title>` (first
    occurrence only) so the validator sees the item as a standalone H2 document.
    Preserve the rest verbatim.
    """
    return re.sub(r"^( {0,3})#### ", lambda m: f"{m.group(1)}## ", item_body, count=1)
