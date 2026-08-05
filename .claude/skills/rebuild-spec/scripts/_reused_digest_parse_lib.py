"""Markdown parsers for synth_digest_from_docs.py (Phase 07).

Parse structural markers (tables, headings, route patterns) in rebuild-spec generated docs
to extract rpc[], topic[], and entity[] arrays for the neutral-digest schema.

LANGUAGE-NEUTRAL: we parse IDs, routes, and entity names — never prose.  The same parser
works on en/vi/jp docs because it targets table structure and route patterns, not keywords.

Signal convention: EXISTING `[SIGNAL_INFERRED]` marker from api-contract-source-patterns.md.
  An unparseable section → empty arrays + the marker note; never fabricate an edge or entity.

Stdlib only.
"""
from __future__ import annotations

import re
from typing import Any

from _system_synthesis_lib import _canonical_entity_name  # shared denylist + MODEL-prefix strip

# The existing signal marker for unparseable sections (reuse — do not invent a new one).
SIGNAL_INFERRED = "[SIGNAL_INFERRED]"

# Matches a Markdown table row: | cell | cell | ...
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
# Matches a table separator row: | :--- | :--- | ...
_TABLE_SEP_RE = re.compile(r"^\|\s*[-:]+[-|\s:]*\|?\s*$")
# HTTP method pattern (case-insensitive) used in route tables
_HTTP_METHOD_RE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*$", re.IGNORECASE)
# Route path pattern: must start with /
_ROUTE_PATH_RE = re.compile(r"^/[\w\-/:{}.*]*$")
# Markdown heading
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$")


def _split_table_row(line: str) -> list[str]:
    """Split a Markdown table row into stripped cell values."""
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _parse_table_blocks(text: str) -> list[list[list[str]]]:
    """Extract all Markdown tables from text.

    Returns a list of tables; each table is a list of rows (list of cell strings).
    Header row is index 0; separator is skipped; data rows follow.
    """
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if _TABLE_ROW_RE.match(stripped):
            if _TABLE_SEP_RE.match(stripped):
                in_table = True  # separator confirms table started
                continue
            cells = _split_table_row(stripped)
            if cells:
                current.append(cells)
        else:
            if in_table and current:
                tables.append(current)
            current = []
            in_table = False
    if in_table and current:
        tables.append(current)
    return tables


def parse_route_list(text: str) -> tuple[list[dict[str, Any]], str]:
    """Parse route-list.md → inbound rpc entries.

    Returns (rpc_list, signal) where signal is "" when at least one route was parsed,
    or SIGNAL_INFERRED when nothing could be extracted.

    Each rpc entry: {"name": "<METHOD> <path>", "direction": "inbound"}.
    Only rows with a recognisable HTTP method AND a /path are emitted.
    """
    rpcs: list[dict[str, Any]] = []
    tables = _parse_table_blocks(text)
    for table in tables:
        if not table:
            continue
        header = table[0]
        # Find method and path columns by examining header names and first data cells
        method_col = _find_method_col(header, table[1:] if len(table) > 1 else [])
        path_col = _find_path_col(header, table[1:] if len(table) > 1 else [])
        if method_col is None or path_col is None:
            continue
        for row in table[1:]:
            if len(row) <= max(method_col, path_col):
                continue
            method = row[method_col].strip().upper()
            path = row[path_col].strip()
            if not method or not path:
                continue
            # Accept methods that look like HTTP verbs
            if not re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$", method, re.IGNORECASE):
                continue
            # Accept paths that start with /
            if not path.startswith("/"):
                continue
            name = f"{method} {path}"
            rpcs.append({"name": name, "direction": "inbound"})
    signal = "" if rpcs else SIGNAL_INFERRED
    return rpcs, signal


def _find_method_col(header: list[str], data_rows: list[list[str]]) -> int | None:
    """Return column index most likely to hold HTTP methods."""
    for i, cell in enumerate(header):
        if re.search(r"method|http|verb|phương\s*thức|メソッド", cell, re.IGNORECASE):
            return i
    # Fallback: scan data rows for a column that has HTTP-method-like values
    for i in range(len(header)):
        hits = 0
        for row in data_rows[:5]:
            if i < len(row) and re.match(
                r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$", row[i].strip(), re.IGNORECASE
            ):
                hits += 1
        if hits > 0:
            return i
    return None


def _find_path_col(header: list[str], data_rows: list[list[str]]) -> int | None:
    """Return column index most likely to hold route paths."""
    for i, cell in enumerate(header):
        if re.search(r"path|route|endpoint|url|đường\s*dẫn|パス", cell, re.IGNORECASE):
            return i
    # Fallback: scan data rows for a column containing /... values
    for i in range(len(header)):
        hits = 0
        for row in data_rows[:5]:
            if i < len(row) and row[i].strip().startswith("/"):
                hits += 1
        if hits > 0:
            return i
    return None


def parse_entities(text: str) -> tuple[list[dict[str, Any]], str]:
    """Parse entities.md → entity[] entries.

    Treats each H2/H3 heading as an entity name; looks for an `id` field row in the
    table immediately below to extract id_field and id_type.  Defaults:
    - id_field: "id" (first column header containing "id" / first row with /^id/i value)
    - id_type: "string" (fallback) or the type cell from the id row
    - visibility: "internal" (default per the contract)

    Returns (entity_list, signal) where signal is SIGNAL_INFERRED when nothing was found.
    """
    entities: list[dict[str, Any]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _HEADING_RE.match(lines[i].strip())
        if m:
            heading_level = len(lines[i]) - len(lines[i].lstrip("#"))
            if heading_level >= 2:
                # Drop doc-section headings ("Summary", "Entities", …) and canonicalize
                # "MODELnnn — Candidate" → "Candidate" via the shared helper (Phase 01).
                entity_name = _canonical_entity_name(m.group(1).strip())
                if entity_name is not None:
                    # Collect the table that follows this heading (skip blank lines)
                    j = i + 1
                    table_lines: list[str] = []
                    while j < len(lines):
                        sl = lines[j].strip()
                        if not sl:
                            j += 1
                            continue
                        if _TABLE_ROW_RE.match(sl):
                            table_lines.append(sl)
                            j += 1
                        elif table_lines:
                            break
                        else:
                            break
                    id_field, id_type = _extract_id_from_table(table_lines)
                    entities.append({
                        "name": entity_name,
                        "id_field": id_field,
                        "id_type": id_type,
                        "visibility": "internal",
                    })
        i += 1
    signal = "" if entities else SIGNAL_INFERRED
    return entities, signal


def _extract_id_from_table(table_lines: list[str]) -> tuple[str, str]:
    """Extract (id_field, id_type) from entity table lines."""
    if not table_lines:
        return "id", "string"
    rows: list[list[str]] = []
    for line in table_lines:
        if _TABLE_SEP_RE.match(line.strip()):
            continue
        rows.append(_split_table_row(line))
    if not rows:
        return "id", "string"
    header = rows[0] if rows else []
    # Find field and type columns in header
    field_col = _find_col_by_name(header, r"field|column|フィールド|trường")
    type_col = _find_col_by_name(header, r"type|typ|kiểu|型")
    # Search data rows for the id row
    for row in rows[1:]:
        if not row:
            continue
        # Check first column or field_col for id-like values
        check_col = field_col if field_col is not None else 0
        if check_col < len(row):
            val = row[check_col].lower().strip()
            if val in ("id", "uuid", "pk") or val.startswith("id"):
                id_field = row[check_col].strip()
                id_type = row[type_col].strip() if type_col is not None and type_col < len(row) else "string"
                return id_field, id_type or "string"
    return "id", "string"


def _find_col_by_name(header: list[str], pattern: str) -> int | None:
    for i, cell in enumerate(header):
        if re.search(pattern, cell, re.IGNORECASE):
            return i
    return None


def parse_architecture(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Parse architecture.md → (rpc_outbound[], topic[], signal).

    Best-effort: looks for interaction tables (columns: From/To/Method) and event tables
    (columns: Topic/Role/Event or similar).  Unparseable → empty arrays + SIGNAL_INFERRED.

    rpc entries (outbound calls declared here):
      {"name": "<method_or_path>", "direction": "outbound"}

    topic entries:
      {"name": "<topic>", "role": "producer"|"consumer", "event": "<event>"}
    """
    rpcs: list[dict[str, Any]] = []
    topics: list[dict[str, Any]] = []

    tables = _parse_table_blocks(text)
    for table in tables:
        if len(table) < 2:
            continue
        header = [c.lower() for c in table[0]]
        header_str = " ".join(header)
        data = table[1:]
        # Interaction / RPC table heuristic (has "from", "to", "method" or similar)
        if _has_interaction_cols(header):
            from_col = _find_col_by_name(table[0], r"from|từ|送信元")
            to_col = _find_col_by_name(table[0], r"^to$|đến|送信先")
            method_col = _find_col_by_name(table[0], r"method|path|endpoint|phương\s*thức|メソッド")
            for row in data:
                if method_col is not None and method_col < len(row):
                    name = row[method_col].strip()
                    if name:
                        rpcs.append({"name": name, "direction": "outbound"})
        # Event / topic table heuristic (has "topic" column and "role"/"producer"/"consumer")
        elif _has_event_cols(header):
            topic_col = _find_col_by_name(table[0], r"topic|chủ\s*đề|トピック|event\s*name")
            role_col = _find_col_by_name(table[0], r"^role$|vai\s*trò|役割|direction")
            event_col = _find_col_by_name(table[0], r"^event$|sự\s*kiện|イベント|payload|message")
            if topic_col is None:
                continue
            for row in data:
                if topic_col >= len(row):
                    continue
                tname = row[topic_col].strip()
                if not tname:
                    continue
                role_raw = (row[role_col].strip().lower() if role_col is not None
                            and role_col < len(row) else "")
                # Normalise role: producer/consumer; default producer when ambiguous
                if "consumer" in role_raw or "consumes" in role_raw:
                    role = "consumer"
                else:
                    role = "producer"
                event = ""
                if event_col is not None and event_col < len(row):
                    event = row[event_col].strip()
                topics.append({"name": tname, "role": role, "event": event})

    signal = ""
    if not rpcs and not topics:
        signal = SIGNAL_INFERRED
    return rpcs, topics, signal


def _has_interaction_cols(header_lower: list[str]) -> bool:
    header_str = " ".join(header_lower)
    return bool(re.search(r"\bfrom\b|\bto\b|\bmethod\b|\bpath\b", header_str))


def _has_event_cols(header_lower: list[str]) -> bool:
    header_str = " ".join(header_lower)
    return bool(re.search(r"\btopic\b|\bevent\b|\bproducer\b|\bconsumer\b", header_str))
