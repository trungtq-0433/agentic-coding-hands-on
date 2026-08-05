"""Pure-Python helpers for propose-improvements Step 7 (apply-verdicts).

Authoritative implementation of `claude/skills/propose-improvements/references/apply-validations.md`.
No I/O orchestration here — see `apply_verdicts.py` for the wrapper that handles
filesystem reads, atomic writes, and stdout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_ATX_H1_RE = re.compile(r"^ {0,3}# (?!#)")
_ATX_H2_RE = re.compile(r"^ {0,3}## (?!#)")
_ATX_H3_RE = re.compile(r"^ {0,3}### (?!#)")
_ATX_H4_RE = re.compile(r"^ {0,3}#### (?!#)")
_ATX_H5_RE = re.compile(r"^ {0,3}##### (?!#)")
_ATX_H6_RE = re.compile(r"^ {0,3}###### (?!#)")
_REVISED_ITEM_HDR_RE = re.compile(r"^ {0,3}#\s+Revised\s+item\s*$")
_TRAILING_DEDUP_RE = re.compile(r"\n*<!--\s*dedup:[^>]*-->\s*\n?$", re.IGNORECASE)
_VALUE_BULLET_RE = re.compile(
    r"^\s{0,3}[-*+]\s+\*\*Value:\*\*\s+(high|medium|low)", re.IGNORECASE,
)
_EFFORT_BULLET_RE = re.compile(
    r"^\s{0,3}[-*+]\s+\*\*Engineering effort hint:\*\*\s+(no|very-low|low|medium|high)", re.IGNORECASE,
)
_VERDICT_FILENAME_RE = re.compile(r"^item-(\d+)-([a-z0-9][a-z0-9\-]*)\.md$")
_REQUIRED_BULLETS = ("Value", "Need", "Benefits", "Proposed solution", "Engineering effort hint")
_VALUE_ORDER = {"high": 0, "medium": 1, "low": 2}
_EFFORT_ORDER = {"no": 0, "very-low": 1, "low": 2, "medium": 3, "high": 4}


@dataclass
class Verdict:
    item_index: int
    item_slug: str
    decision: str  # "KEEP" | "REVISE" | "DROP"
    revised_body: str | None
    source_filename: str


@dataclass
class Item:
    index: int
    title: str
    track: str
    block: str  # entire #### block, fence-aware


@dataclass
class ApplyResult:
    text: str
    warns: list[str] = field(default_factory=list)
    drops: list[str] = field(default_factory=list)
    revises: list[str] = field(default_factory=list)
    unvalidated_count: int = 0


# ---------------------------------------------------------------------------
# Combined-file split + dedup-marker strip
# ---------------------------------------------------------------------------

def strip_dedup_marker(text: str) -> str:
    return _TRAILING_DEDUP_RE.sub("", text)


def split_combined(text: str) -> tuple[str, str | None, str | None]:
    """Return (header, technical_body, business_body). Either body may be None
    when its track isn't present. Header is everything before the first track
    H2.

    Walks fence-aware so a fenced `## technical` line doesn't trigger.
    """
    lines = text.splitlines()
    in_fence = False
    fence_char = ""
    fence_len = 0

    tech_start: int | None = None
    biz_start: int | None = None

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
        if _ATX_H2_RE.match(line):
            head = line.lstrip(" #").strip().lower().rstrip()
            if head.startswith("technical") and tech_start is None:
                tech_start = i
            elif head.startswith("business") and biz_start is None:
                biz_start = i

    if tech_start is None and biz_start is None:
        return text, None, None

    first_split = min(s for s in (tech_start, biz_start) if s is not None)
    header = "\n".join(lines[:first_split]).rstrip()

    technical_body: str | None = None
    business_body: str | None = None
    if tech_start is not None and biz_start is not None:
        if tech_start < biz_start:
            technical_body = "\n".join(lines[tech_start:biz_start]).rstrip()
            business_body = "\n".join(lines[biz_start:]).rstrip()
        else:
            business_body = "\n".join(lines[biz_start:tech_start]).rstrip()
            technical_body = "\n".join(lines[tech_start:]).rstrip()
    elif tech_start is not None:
        technical_body = "\n".join(lines[tech_start:]).rstrip()
    else:
        business_body = "\n".join(lines[biz_start:]).rstrip()
    return header, technical_body, business_body


# ---------------------------------------------------------------------------
# Verdict loading
# ---------------------------------------------------------------------------

def load_verdicts(validation_dir: Path) -> tuple[dict[int, Verdict], list[str]]:
    """Walk validation_dir for verdict files. Returns (verdicts_by_index, warns)."""
    verdicts: dict[int, Verdict] = {}
    warns: list[str] = []
    if not validation_dir.is_dir():
        return verdicts, warns
    for p in sorted(validation_dir.iterdir()):
        if not p.is_file():
            continue
        m = _VERDICT_FILENAME_RE.match(p.name)
        if not m:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            warns.append(f"warn: malformed verdict at {p.name} — ignored")
            continue
        v = _parse_verdict(text, p.name)
        if v is None:
            warns.append(f"warn: malformed verdict at {p.name} — ignored")
            continue
        if v.item_index in verdicts:
            prev = verdicts[v.item_index]
            warns.append(
                f"warn: duplicate item_index {v.item_index} in {p.name} — "
                f"overwrites {prev.item_slug}"
            )
        verdicts[v.item_index] = v
    return verdicts, warns


def _parse_verdict(text: str, filename: str) -> Verdict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end < 0:
        return None
    fm: dict[str, str] = {}
    for ln in lines[1:end]:
        if ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        fm[key.strip()] = val.strip()
    try:
        item_index = int(fm.get("item_index", ""))
    except ValueError:
        return None
    item_slug = fm.get("item_slug", "")
    decision = fm.get("decision", "").upper()
    if decision not in {"KEEP", "REVISE", "DROP"}:
        return None
    revised_body: str | None = None
    if decision == "REVISE":
        revised_body = _extract_revised_body(lines[end + 1:])
    return Verdict(item_index=item_index, item_slug=item_slug, decision=decision,
                   revised_body=revised_body, source_filename=filename)


def _extract_revised_body(lines: list[str]) -> str | None:
    """Extract the `# Revised item` H1 body. Returns None when absent/empty."""
    in_fence = False
    fence_char = ""
    fence_len = 0
    start: int | None = None
    end = len(lines)
    for i, ln in enumerate(lines):
        if in_fence:
            m = _FENCE_OPEN_RE.match(ln)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                in_fence = False
            continue
        fm = _FENCE_OPEN_RE.match(ln)
        if fm:
            in_fence = True
            fence_char = fm.group(1)[0]
            fence_len = len(fm.group(1))
            continue
        if start is None:
            if _REVISED_ITEM_HDR_RE.match(ln):
                start = i + 1
        else:
            if _ATX_H1_RE.match(ln):
                end = i
                break
    if start is None:
        return None
    body = "\n".join(lines[start:end]).strip("\n")
    return body if body.strip() else None


# ---------------------------------------------------------------------------
# Item walker (per track)
# ---------------------------------------------------------------------------

def parse_track_items(track_body: str, track: str, start_index: int) -> list[Item]:
    """Walk #### H4 blocks fence-aware. Indices are continuous (start_index, +1, ...)."""
    if not track_body:
        return []
    lines = track_body.splitlines()
    in_fence = False
    fence_char = ""
    fence_len = 0
    items: list[Item] = []
    block_start: int | None = None
    block_title = ""
    next_idx = start_index

    def flush(end_line: int) -> None:
        nonlocal block_start, block_title, next_idx
        if block_start is None:
            return
        body = "\n".join(lines[block_start:end_line])
        items.append(Item(index=next_idx, title=block_title, track=track, block=body))
        next_idx += 1
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
        if _ATX_H4_RE.match(line):
            flush(i)
            block_title = line.lstrip(" #").strip()
            block_start = i
            continue
    flush(len(lines))
    return items


def title_to_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


# ---------------------------------------------------------------------------
# Revised body schema validation + H2 -> H4 demotion
# ---------------------------------------------------------------------------

def validate_revised_body(body: str) -> bool:
    """Per spec 'Revised body schema'. Returns True iff well-formed."""
    lines = body.splitlines()
    in_fence = False
    fence_char = ""
    fence_len = 0
    h2_count = 0
    bullets_found: list[str] = []
    for line in lines:
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
        if _ATX_H1_RE.match(line):
            return False
        if _ATX_H2_RE.match(line):
            h2_count += 1
            continue
        if (_ATX_H3_RE.match(line) or _ATX_H4_RE.match(line)
                or _ATX_H5_RE.match(line) or _ATX_H6_RE.match(line)):
            return False
        bm = re.match(r"^ {0,3}[-*+]\s+\*\*([^*]+):\*\*", line)
        if bm:
            label = bm.group(1).strip()
            bullets_found.append(label)
    if h2_count != 1:
        return False
    # Required bullets present, in order, with no `Category:` interleaved.
    if "Category" in bullets_found:
        return False
    # Filter to known required labels; preserve discovery order.
    seen_required = [b for b in bullets_found if b in _REQUIRED_BULLETS]
    return seen_required == list(_REQUIRED_BULLETS)


def demote_h2_to_h4(body: str) -> str:
    """Demote `^ {0,3}## ` → `#### ` fence-aware."""
    out_lines: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in body.splitlines():
        if in_fence:
            m = _FENCE_OPEN_RE.match(line)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                in_fence = False
            out_lines.append(line)
            continue
        fm = _FENCE_OPEN_RE.match(line)
        if fm:
            in_fence = True
            fence_char = fm.group(1)[0]
            fence_len = len(fm.group(1))
            out_lines.append(line)
            continue
        out_lines.append(re.sub(r"^( {0,3})## ", lambda m: f"{m.group(1)}#### ", line, count=1))
    return "\n".join(out_lines)


# ---------------------------------------------------------------------------
# Per-item value/effort parse
# ---------------------------------------------------------------------------

def parse_value_effort(block: str) -> tuple[str | None, str | None]:
    """Return (value, effort) found in the block's bullets (lower-cased), or None."""
    value: str | None = None
    effort: str | None = None
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in block.splitlines():
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
        vm = _VALUE_BULLET_RE.match(line)
        if vm and value is None:
            value = vm.group(1).lower()
        em = _EFFORT_BULLET_RE.match(line)
        if em and effort is None:
            effort = em.group(1).lower()
    return value, effort


# ---------------------------------------------------------------------------
# Rollup recompute + within-aspect sort
# ---------------------------------------------------------------------------

@dataclass
class RollupBlock:
    rollup_heading: str | None  # original `### ...` line, or None for items before any H3
    aspect_comment: str | None  # `<!-- aspect-id: ... -->` line
    items: list[str]  # each item block (full `#### ...` text)
    leading_blanks: int = 0


def split_rollups(track_body: str) -> tuple[str, list[RollupBlock]]:
    """Split a track body (starts with `## Technical` / `## Business`) into:
    (track_header, [RollupBlock]). The track_header is the H2 line + any prose
    before the first `### ` rollup heading. Each RollupBlock holds its rollup
    heading + aspect comment + item blocks.
    """
    if not track_body:
        return "", []
    lines = track_body.splitlines()
    # Walk fence-aware. First line should be the `## ` header.
    in_fence = False
    fence_char = ""
    fence_len = 0
    track_header_end = 0
    first_h3 = None
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
        if _ATX_H3_RE.match(line):
            first_h3 = i
            break
    track_header_end = first_h3 if first_h3 is not None else len(lines)
    track_header = "\n".join(lines[:track_header_end]).rstrip()

    rollups: list[RollupBlock] = []
    if first_h3 is None:
        return track_header, rollups

    # Find each ### rollup + its aspect-id comment + its #### children.
    i = first_h3
    in_fence = False
    fence_char = ""
    fence_len = 0
    while i < len(lines):
        line = lines[i]
        if not _ATX_H3_RE.match(line):
            i += 1
            continue
        rollup_heading = line
        # Look at next non-blank line for the aspect-id comment.
        aspect_comment: str | None = None
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and re.match(r"^\s*<!--\s*aspect-id:.*-->\s*$", lines[j]):
            aspect_comment = lines[j]
            j += 1
        # Items: walk until next ### or ## (fence-aware) collecting #### blocks.
        items_block_start = j
        block_end = len(lines)
        inf = False
        fc = ""
        fl = 0
        for k in range(j, len(lines)):
            ln = lines[k]
            if inf:
                m = _FENCE_OPEN_RE.match(ln)
                if m and m.group(1)[0] == fc and len(m.group(1)) >= fl:
                    inf = False
                continue
            fm = _FENCE_OPEN_RE.match(ln)
            if fm:
                inf = True
                fc = fm.group(1)[0]
                fl = len(fm.group(1))
                continue
            if _ATX_H3_RE.match(ln) or _ATX_H2_RE.match(ln):
                block_end = k
                break

        # Extract individual `#### ...` blocks from items_block_start..block_end.
        items = _extract_item_blocks(lines[items_block_start:block_end])
        rollups.append(RollupBlock(rollup_heading=rollup_heading,
                                   aspect_comment=aspect_comment,
                                   items=items))
        i = block_end
    return track_header, rollups


def _extract_item_blocks(slice_lines: list[str]) -> list[str]:
    """Yield each `^ {0,3}#### ...` block as a string (fence-aware)."""
    in_fence = False
    fence_char = ""
    fence_len = 0
    starts: list[int] = []
    for i, line in enumerate(slice_lines):
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
        if _ATX_H4_RE.match(line):
            starts.append(i)
    if not starts:
        return []
    blocks: list[str] = []
    for idx, s in enumerate(starts):
        e = starts[idx + 1] if idx + 1 < len(starts) else len(slice_lines)
        blocks.append("\n".join(slice_lines[s:e]).rstrip())
    return blocks


def sort_items_within_aspect(items: list[str]) -> tuple[list[str], list[str]]:
    """Stable sort by Value desc → Effort asc → original order.
    Returns (sorted_items, warns_for_fallbacks).
    """
    decorated: list[tuple[int, int, int, str]] = []
    warns: list[str] = []
    for orig_idx, block in enumerate(items):
        value, effort = parse_value_effort(block)
        v_used = value if value in _VALUE_ORDER else "medium"
        e_used = effort if effort in _EFFORT_ORDER else "medium"
        if value is None or effort is None:
            # Try to extract a title for the warn.
            title = block.lstrip(" #").splitlines()[0].strip()
            warns.append(
                f"warn: sort-fallback for item-?? \"{title}\" — bullet parse failed"
            )
        decorated.append((_VALUE_ORDER[v_used], _EFFORT_ORDER[e_used], orig_idx, block))
    decorated.sort(key=lambda t: (t[0], t[1], t[2]))
    return [t[3] for t in decorated], warns


def recompute_rollup_heading(orig_heading: str, items: list[str]) -> str:
    """Recompute `### <title> · <N> items · max=<X> · effort=<Y>`.
    If items is empty caller drops the rollup entirely; this function is called
    only with surviving items.
    """
    title_part = re.match(r"^ {0,3}### (?P<rest>.*)$", orig_heading)
    if not title_part:
        return orig_heading
    rest = title_part.group("rest")
    title = rest.split(" · ", 1)[0].strip()
    n = len(items)
    item_word = "item" if n == 1 else "items"
    # Compute max value + effort range.
    values: list[str] = []
    efforts: list[str] = []
    for block in items:
        v, e = parse_value_effort(block)
        if v in _VALUE_ORDER:
            values.append(v)
        if e in _EFFORT_ORDER:
            efforts.append(e)
    max_value = min(values, key=lambda v: _VALUE_ORDER[v]) if values else "medium"
    if efforts:
        lo = min(efforts, key=lambda e: _EFFORT_ORDER[e])
        hi = max(efforts, key=lambda e: _EFFORT_ORDER[e])
        effort_str = lo if lo == hi else f"{lo}-{hi}"
    else:
        effort_str = "medium"
    return f"### {title} · {n} {item_word} · max={max_value} · effort={effort_str}"


# ---------------------------------------------------------------------------
# Log-line sanitisation
# ---------------------------------------------------------------------------

def sanitize_title_for_log(title: str) -> str:
    return re.sub(r"[\r\n\t]+", " ", title).strip()
