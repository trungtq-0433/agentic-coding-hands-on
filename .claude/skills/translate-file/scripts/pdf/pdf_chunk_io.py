#!/usr/bin/env python3
"""Serialize PDF elements to chunk*.md files and parse translated output_chunk*.md back.

Chunk format: each line is "[E:{page}_{line}] {text}"
One element per line — sub-agents must NEVER merge adjacent [E:...] lines.
"""
import os
import re

_ELEMENT_RE = re.compile(r"^\[E:([\w]+_\d+)\]\s?(.*)", re.MULTILINE)
_MAX_CHUNK_CHARS = 6000  # default token budget boundary


def write_chunks(elements, temp_dir, max_chars=_MAX_CHUNK_CHARS):
    """Serialize elements into chunk*.md files under temp_dir.

    Splits on element boundaries only — never inside an element.
    Returns list of chunk filenames written (e.g. ['chunk0001.md', ...]).
    """
    chunks = []
    current_lines = []
    current_size = 0
    chunk_idx = 1

    def flush():
        nonlocal current_lines, current_size, chunk_idx
        if not current_lines:
            return
        fname = f"chunk{chunk_idx:04d}.md"
        fpath = os.path.join(temp_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(current_lines) + "\n")
        chunks.append(fname)
        chunk_idx += 1
        current_lines = []
        current_size = 0

    for elem in elements:
        line = f"[E:{elem['id']}] {elem['text']}"
        line_size = len(line) + 1  # +1 for newline
        if current_size + line_size > max_chars and current_lines:
            flush()
        current_lines.append(line)
        current_size += line_size

    flush()
    return chunks


def read_outputs(temp_dir, source_ids):
    """Parse output_chunk*.md files back into {elem_id: translated_text}.

    Validates that every source_id has exactly one matching output.
    Raises ValueError on missing or duplicate ids (hallucination guard).

    Args:
        temp_dir: directory containing output_chunk*.md files
        source_ids: ordered list of element ids from the original extraction

    Returns:
        dict {elem_id: translated_text} in the original element order
    """
    import glob

    output_files = sorted(glob.glob(os.path.join(temp_dir, "output_chunk*.md")))
    if not output_files:
        raise FileNotFoundError(f"No output_chunk*.md found in {temp_dir}")

    found = {}
    for fpath in output_files:
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        for m in _ELEMENT_RE.finditer(content):
            eid, text = m.group(1), m.group(2).strip()
            if eid in found:
                raise ValueError(f"Duplicate element id in outputs: {eid}")
            found[eid] = text

    # Validate completeness
    source_set = set(source_ids)
    found_set = set(found.keys())
    missing = source_set - found_set
    unknown = found_set - source_set

    if missing:
        raise ValueError(
            f"Missing translated ids (sub-agent dropped {len(missing)} elements): "
            + ", ".join(sorted(missing)[:10])
        )
    if unknown:
        raise ValueError(
            f"Unknown ids in output (hallucination guard): "
            + ", ".join(sorted(unknown)[:10])
        )

    return {eid: found[eid] for eid in source_ids}
