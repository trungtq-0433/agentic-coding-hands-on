"""speckit_parse_lib.py — pure, importable helpers for parsing Spec-Kit / SDD project trees.

No side-effects. No CLI. No non-stdlib imports.
"""
from __future__ import annotations

import os
import re
from typing import Optional

# NNN-feature-name dir pattern
_FEATURE_DIR_RE = re.compile(r"^(\d{3})-(.+)$")

# H2 headings in research.md — used to generate spec-URI anchors
_H2_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

# User-story detection patterns
_US_LINE_RE = re.compile(r"\bAs (a|an)\b", re.IGNORECASE)
_US_HEADING_RE = re.compile(r"^#+\s+User Story", re.MULTILINE | re.IGNORECASE)

# Functional-requirement detection patterns (FR- prefix or **FR prefix or numbered list
# under a Requirements/Functional heading)
_FR_INLINE_RE = re.compile(
    r"(?:^|\s)(?:FR-\d+|FR\d+|\*\*FR[-\s]?\d+|\*\*FR\b)", re.MULTILINE | re.IGNORECASE
)
_REQUIREMENTS_HEADING_RE = re.compile(
    r"^#+\s+(?:Functional\s+)?Requirements?\s*$", re.MULTILINE | re.IGNORECASE
)
_NUMBERED_LINE_RE = re.compile(r"^\s*\d+\.\s+\S", re.MULTILINE)


def _slug_from_raw(raw_name: str) -> str:
    """Convert 'NNN-some-feature-name' to 'some-feature-name' (kebab, strip NNN prefix)."""
    m = _FEATURE_DIR_RE.match(raw_name)
    if m:
        return m.group(2).lower()
    return raw_name.lower()


def _parse_research_sections(research_path: Optional[str]) -> list[str]:
    """Return list of H2 heading text strings from a research.md file.

    Used to build spec-URI anchors like spec://NNN/research.md#section.
    Defensive: missing/unreadable file returns empty list.
    """
    if not research_path:
        return []
    try:
        with open(research_path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return []
    return [m.group(1).strip() for m in _H2_HEADING_RE.finditer(content)]


def enumerate_features(specs_root: str) -> list[dict]:
    """Scan specs_root for NNN-* dirs and return feature metadata list.

    Each dict: {nnn, raw_name, slug, has_spec, has_plan, has_tasks,
                has_data_model, has_contracts, contracts_src, has_research,
                research_src, research_sections}
    - contracts_src: absolute path to the contracts/ dir if present, else None.
    - has_research: True when research.md exists in the feature dir.
    - research_src: absolute path to research.md if present, else None.
    - research_sections: list of H2 heading strings from research.md (for spec-URI anchors), or [].
    Sorted by nnn ascending.
    """
    features: list[dict] = []
    try:
        entries = os.listdir(specs_root)
    except OSError:
        return []

    for entry in entries:
        m = _FEATURE_DIR_RE.match(entry)
        if not m:
            continue
        full = os.path.join(specs_root, entry)
        if not os.path.isdir(full):
            continue

        nnn = m.group(1)
        raw_name = entry
        slug = _slug_from_raw(raw_name)

        def _has(filename: str) -> bool:
            return os.path.isfile(os.path.join(full, filename))

        def _has_dir(dirname: str) -> bool:
            return os.path.isdir(os.path.join(full, dirname))

        has_contracts = _has_dir("contracts")
        contracts_src = os.path.join(full, "contracts") if has_contracts else None

        has_research = _has("research.md")
        research_src = os.path.join(full, "research.md") if has_research else None
        research_sections = _parse_research_sections(research_src) if has_research else []

        features.append({
            "nnn": nnn,
            "raw_name": raw_name,
            "slug": slug,
            "has_spec": _has("spec.md"),
            "has_plan": _has("plan.md"),
            "has_tasks": _has("tasks.md"),
            "has_data_model": _has("data-model.md"),
            "has_contracts": has_contracts,
            "contracts_src": contracts_src,
            "has_research": has_research,
            "research_src": research_src,
            "research_sections": research_sections,
        })

    features.sort(key=lambda f: f["nnn"])
    return features


def parse_spec_md(path: str) -> dict:
    """Parse a spec.md and return {title, us_count, fr_count}.

    Defensive: missing/unreadable file returns zeros and empty title.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return {"title": "", "us_count": 0, "fr_count": 0}

    # Title: first H1 or H2 line
    title = ""
    for line in content.splitlines():
        stripped = line.lstrip("#").strip()
        if line.startswith("#") and stripped:
            title = stripped
            break

    # User-story count: lines matching "As a/an" OR "### User Story" headings
    us_lines = set(i for i, ln in enumerate(content.splitlines())
                   if _US_LINE_RE.search(ln))
    us_headings = len(_US_HEADING_RE.findall(content))
    us_count = max(len(us_lines), us_headings)

    # FR count: explicit FR-NNN tags first
    fr_tags = len(_FR_INLINE_RE.findall(content))
    if fr_tags:
        fr_count = fr_tags
    else:
        # Fallback: count numbered list items under a Requirements/Functional heading
        req_match = _REQUIREMENTS_HEADING_RE.search(content)
        if req_match:
            after = content[req_match.end():]
            # Stop at next heading
            next_heading = re.search(r"^#+\s", after, re.MULTILINE)
            section = after[:next_heading.start()] if next_heading else after
            fr_count = len(_NUMBERED_LINE_RE.findall(section))
        else:
            fr_count = 0

    return {"title": title, "us_count": us_count, "fr_count": fr_count}


def find_constitution(repo_root: str, specs_root: str) -> Optional[str]:
    """Return absolute path to constitution.md, or None if not found.

    Checks (in order):
      1. <specs_root>/../.specify/memory/constitution.md  (canonical speckit location)
      2. <repo_root>/.specify/memory/constitution.md
      3. <repo_root>/constitution.md
    """
    candidates = [
        os.path.join(specs_root, "..", ".specify", "memory", "constitution.md"),
        os.path.join(repo_root, ".specify", "memory", "constitution.md"),
        os.path.join(repo_root, "constitution.md"),
    ]
    for c in candidates:
        norm = os.path.normpath(c)
        if os.path.isfile(norm):
            return norm
    return None
