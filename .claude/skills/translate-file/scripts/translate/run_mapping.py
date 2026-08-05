#!/usr/bin/env python3
"""run-mapping.py - Shared format-agnostic run-mapping helpers.

Used by both docx_mapping.py (DOCX) and pptx_mapping.py (PPTX).
Callers must ensure scripts/docx/ is on sys.path before calling normalize_component.
"""
from __future__ import annotations

_MAP_CHUNK_BATCH = 4000  # max combined translated_text chars per MAP batch


def are_all_equal(components: list[dict]) -> bool:
    """True when all components share the same non-text attributes."""
    if len(components) <= 1:
        return True
    ref = {k: v for k, v in components[0].items() if k != "text"}
    return all(
        {k: v for k, v in c.items() if k != "text"} == ref
        for c in components[1:]
    )


def handle_empty_text(components: list[dict]) -> list[dict]:
    """Merge whitespace-only runs into neighbours; remove trailing whitespace runs."""
    processed: list[dict] = []
    for i, run in enumerate(components):
        if not run.get("text", "").strip():
            if processed:
                processed[-1] = dict(processed[-1], text=processed[-1]["text"] + run.get("text", ""))
            elif i + 1 < len(components):
                components[i + 1] = dict(
                    components[i + 1],
                    text=run.get("text", "") + components[i + 1].get("text", ""),
                )
        else:
            processed.append(run)
    return processed


def synthesize_single_run(translated_text: str, components: list[dict]) -> list[dict]:
    """Single-format path: one run with first component's attributes."""
    base = dict(components[0]) if components else {}
    base["text"] = translated_text
    return [base]


def validate_concat(item_id: str, translated_text: str, mapped: list[dict]) -> bool:
    """Return True if concat(mapped[].text) == translated_text; print warning if not."""
    concat = "".join(c.get("text", "") for c in mapped)
    if concat != translated_text:
        print(
            f"Warning: concat mismatch id={item_id} "
            f"(got {repr(concat[:60])!r} != expected {repr(translated_text[:60])!r})"
        )
        return False
    return True


def batch_items(items: list, batch_size: int = _MAP_CHUNK_BATCH) -> list[list]:
    """Batch items by combined translated_general_text char size."""
    chunks: list[list] = []
    current: list = []
    size = 0
    for item in items:
        item_size = len(item.get("translated_general_text", ""))
        if size + item_size > batch_size and current:
            chunks.append(current)
            current, size = [], 0
        current.append(item)
        size += item_size
    if current:
        chunks.append(current)
    return chunks


def normalize_component(c: dict) -> dict:
    """Normalize attribute types from LLM output via TextAttr round-trip.

    Caller must have scripts/docx/ on sys.path.
    """
    from docx_xml_model import TextAttr
    return TextAttr.from_dict(c).to_dict()
