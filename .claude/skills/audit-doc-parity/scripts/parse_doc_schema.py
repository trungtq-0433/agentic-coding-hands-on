#!/usr/bin/env python3
"""Step 1b — Extract the doc-side comparable field set.

Reads doc-units.json (from scope_doc_units.py), parses each doc's structured
tables/fields, and emits per-unit schema JSON matching the regen-schema-contract.md
shape: {unit, artifact, items:[{kind, id, fields, evidence}]}.

Regex / markdown-table parsing only. Stdlib only. No verdicts.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import read_text_safe, resolve_project_root  # noqa: E402

# ---------------------------------------------------------------------------
# Low-level markdown helpers
# ---------------------------------------------------------------------------

def _table_rows(text: str, section_heading: str) -> list[list[str]]:
    """Extract pipe-delimited table rows under a heading (any depth ## through ######).

    Returns list of lists of cell strings. Skips header and separator rows.
    Stops at the next heading of equal or lower depth.
    Supports headings up to 6 levels (####) so nested SM-002 Transitions tables
    under a ### SM block are captured correctly.
    """
    heading_re = re.compile(
        r"^(#{1,6})\s+" + re.escape(section_heading), re.IGNORECASE
    )
    rows: list[list[str]] = []
    in_section = False
    heading_depth = 0
    for line in text.splitlines():
        if not in_section:
            m = heading_re.match(line)
            if m:
                in_section = True
                heading_depth = len(m.group(1))
            continue
        # Stop at next heading of same or lower depth
        m2 = re.match(r"^(#{1,6})\s+", line)
        if m2 and len(m2.group(1)) <= heading_depth:
            break
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # Skip separator rows (---|---|)
        if all(re.match(r"^-+$", c.strip("-").strip()) or c.strip("-").strip() == ""
               for c in cells if c):
            continue
        rows.append(cells)
    # Remove the header row (first row)
    if len(rows) > 1:
        return rows[1:]
    return []


def _find_block(text: str, heading_pattern: str) -> str:
    """Return text content of a ## heading block matching pattern (regex).

    Content runs until the next same-level heading.
    """
    lines = text.splitlines()
    result: list[str] = []
    in_block = False
    block_depth = 0
    pat = re.compile(r"^(#{1,3})\s+" + heading_pattern, re.IGNORECASE)
    end_pat: re.Pattern | None = None

    for line in lines:
        if not in_block:
            m = pat.match(line)
            if m:
                in_block = True
                block_depth = len(m.group(1))
                end_pat = re.compile(r"^#{1," + str(block_depth) + r"}\s+")
                continue
        else:
            if end_pat and end_pat.match(line):
                # Check it's not a deeper heading
                depth = len(re.match(r"^(#+)", line).group(1))
                if depth <= block_depth:
                    break
            result.append(line)

    return "\n".join(result)


def _extract_field(text: str, label: str) -> str | None:
    """Extract **Label:** value from block text."""
    m = re.search(r"\*\*" + re.escape(label) + r":\*\*\s*(.+)", text)
    return m.group(1).strip() if m else None


def _extract_output_subfields(block_text: str) -> dict | None:
    """Parse **Output:** / **Payload:** sub-fields from a block.

    Returns dict with keys: format, columns, encoding, naming,
    response_shape, payload — each populated only if found.
    Returns None if no Output/Payload marker found.
    """
    output_marker = re.search(
        r"\*\*(Output|Payload):\*\*\s*(.+?)(?:\n|$)", block_text
    )
    if not output_marker:
        return None

    out: dict = {}
    raw = output_marker.group(2).strip()
    # Try to extract sub-fields from the output description
    for key in ("format", "columns", "encoding", "naming", "response_shape", "payload"):
        m = re.search(rf"\b{key}\b[:\s]+([^,;\n]+)", raw, re.IGNORECASE)
        if m:
            out[key] = m.group(1).strip()
    if not out:
        # Store the raw value under response_shape as fallback
        out["response_shape"] = raw
    return out


def _citation_from_block(block_text: str) -> str | None:
    """Extract the first **Source:** citation string from a block."""
    from _citation_lib import CITATION_RE
    m = CITATION_RE.search(block_text)
    if m:
        path = m.group(1).strip()
        start = m.group(2)
        end = m.group(3) if m.group(3) else start
        return f"{path}:{start}-{end}"
    return None


# ---------------------------------------------------------------------------
# Per-artifact parsers
# ---------------------------------------------------------------------------

def _parse_technical_spec(text: str, unit: str, doc_path: str) -> list[dict]:
    items: list[dict] = []

    # Track IDs already emitted to prevent duplicates across form variants
    _seen_fr: set[str] = set()
    _seen_br: set[str] = set()
    _seen_sc: set[str] = set()

    # --- FR: LIST form (dominant in real template) ---
    # Pattern: - **FR-001** {DESCRIPTION} — `{METHOD} {PATH}` via `{Handler::method}`
    #            **Source:** `{path:line-line}`
    fr_list_re = re.compile(
        r"^-\s+\*\*(FR-\d+)\*\*\s+(.*?)\s+—\s+`([A-Z]+\s+[^\s`]+)`\s+via\s+`([^`]+)`"
    )
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = fr_list_re.match(line)
        if not m:
            continue
        fr_id = m.group(1)
        if fr_id in _seen_fr:
            continue
        _seen_fr.add(fr_id)
        desc = m.group(2).strip()
        endpoint = m.group(3).strip()
        handler = m.group(4).strip()
        fields: dict = {
            "description": desc,
            "endpoint": endpoint,
            "handler": handler,
            "verifiable": "yes",
        }
        # Look for **Source:** on the immediately following non-empty lines
        evidence: str = doc_path
        for j in range(i + 1, min(i + 4, len(lines))):
            src_m = re.search(r"\*\*Source:\*\*\s*`([^`]+)`", lines[j])
            if src_m:
                evidence = src_m.group(1).strip()
                break
            if lines[j].strip() and not lines[j].startswith(" ") and not lines[j].startswith("\t"):
                break
        output = _extract_output_subfields("\n".join(lines[i:i + 5]))
        if output:
            fields["output"] = output
        items.append({"kind": "FR", "id": fr_id, "fields": fields, "evidence": evidence})

    # --- FR: TABLE form (Cross-Cutting Requirements section) ---
    # Pattern: | FR-0XX | Description | METHOD /path | handler | yes/no |
    fr_table_re = re.compile(
        r"^\|\s*(FR-\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    for line in text.splitlines():
        m = fr_table_re.match(line)
        if not m:
            continue
        fr_id = m.group(1).strip()
        if fr_id in _seen_fr:
            continue
        _seen_fr.add(fr_id)
        desc = m.group(2).strip()
        endpoint = m.group(3).strip()
        handler = m.group(4).strip()
        verifiable = m.group(5).strip()
        fields: dict = {
            "description": desc,
            "endpoint": endpoint,
            "handler": handler,
            "verifiable": verifiable,
        }
        fr_block = _find_block(text, re.escape(fr_id))
        output = _extract_output_subfields(fr_block)
        if output:
            fields["output"] = output
        evidence = _citation_from_block(fr_block) or doc_path
        items.append({"kind": "FR", "id": fr_id, "fields": fields, "evidence": evidence})

    # --- BR: BLOCK form (### BR-001_{Slug} with field lines) ---
    # Template: ### BR-001_{NameSlug} / **Linked FR:** / **Source:** / **Applies to:** / **Rule:**
    for m in re.finditer(r"^#{2,4}\s+(BR-\d+)(?:_\w+)?", text, re.MULTILINE):
        br_id = m.group(1)
        if br_id in _seen_br:
            continue
        _seen_br.add(br_id)
        block = _find_block(text, re.escape(br_id) + r"(?:_\w+)?")
        linked = _extract_field(block, "Linked FR") or ""
        applies = _extract_field(block, "Applies to") or _extract_field(block, "Applies") or ""
        rule = _extract_field(block, "Rule") or ""
        evidence = _citation_from_block(block) or doc_path
        items.append({
            "kind": "BR", "id": br_id,
            "fields": {"applies_to": applies, "rule": rule, "linked_fr": linked},
            "evidence": evidence,
        })

    # --- BR: TABLE form (fallback for Cross-Cutting section) ---
    # Pattern: | BR-001 | applies_to | rule | linked_fr |
    br_table_re = re.compile(
        r"^\|\s*(BR-\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    for line in text.splitlines():
        m = br_table_re.match(line)
        if not m:
            continue
        br_id = m.group(1).strip()
        if br_id in _seen_br:
            continue
        _seen_br.add(br_id)
        applies = m.group(2).strip()
        rule = m.group(3).strip()
        linked = m.group(4).strip()
        items.append({
            "kind": "BR", "id": br_id,
            "fields": {"applies_to": applies, "rule": rule, "linked_fr": linked},
            "evidence": doc_path,
        })

    # --- DEC: Decision Logic blocks (### DEC-001_{Slug} or ## DEC-001) ---
    for m in re.finditer(r"^#{2,4}\s+(DEC-\d+)", text, re.MULTILINE):
        dec_id = m.group(1)
        block = _find_block(text, re.escape(dec_id) + r"(?:_\w+)?")
        subtype = _extract_field(block, "subtype") or _extract_field(block, "Subtype") or _extract_field(block, "Type") or ""
        triggers_in = _extract_field(block, "Triggers in") or _extract_field(block, "Trigger") or ""
        involved = _extract_field(block, "Involved entities") or _extract_field(block, "Entities") or ""
        outcome = _extract_field(block, "user_visible_outcome") or _extract_field(block, "User visible outcome") or _extract_field(block, "Outcome") or ""
        evidence = _citation_from_block(block) or doc_path
        items.append({
            "kind": "DEC", "id": dec_id,
            "fields": {
                "subtype": subtype, "triggers_in": triggers_in,
                "involved_entities": involved, "user_visible_outcome": outcome,
            },
            "evidence": evidence,
        })

    # --- SM: State Machines (### SM-001_{Slug} or ## SM-001) ---
    for m in re.finditer(r"^#{2,4}\s+(SM-\d+)", text, re.MULTILINE):
        sm_id = m.group(1)
        block = _find_block(text, re.escape(sm_id) + r"(?:_\w+)?")
        kind_val = _extract_field(block, "kind") or _extract_field(block, "Kind") or _extract_field(block, "Type") or ""
        states_raw = _extract_field(block, "States") or ""
        states = [s.strip() for s in re.split(r"[,|]", states_raw) if s.strip()]
        # Parse transitions from table rows: From | To | Guard | Side effect (4-col SM-002 form)
        # row[0]=From, row[1]=To, row[2]=Guard, row[3]=Side effect
        # SM-001 bullet "Transition rules:" form yields no table rows — acceptable, no crash.
        transitions: list[dict] = []
        for row in _table_rows(block, "Transitions"):
            if len(row) >= 1:
                transitions.append({
                    "from_to": f"{row[0]}→{row[1]}" if len(row) > 1 else row[0],
                    "guard": row[2] if len(row) > 2 else "",
                    "side_effect": row[3] if len(row) > 3 else "",
                })
        evidence = _citation_from_block(block) or doc_path
        items.append({
            "kind": "SM", "id": sm_id,
            "fields": {"kind": kind_val, "states": states, "transitions": transitions},
            "evidence": evidence,
        })

    # --- ALG: Algorithms (### ALG-001_{Slug} or ## ALG-001) ---
    # _REAL_OUTPUT_KEYS: sub-field keys that indicate genuine structured output.
    # The bare {"response_shape": <raw>} fallback is NOT a real sub-field — keep
    # output as a scalar string in that case to avoid type-mismatch diff noise.
    _REAL_OUTPUT_KEYS = {"format", "columns", "encoding", "naming", "payload"}
    for m in re.finditer(r"^#{2,4}\s+(ALG-\d+)", text, re.MULTILINE):
        alg_id = m.group(1)
        block = _find_block(text, re.escape(alg_id) + r"(?:_\w+)?")
        inp = _extract_field(block, "Input") or ""
        out_val = _extract_field(block, "Output") or ""
        complexity = _extract_field(block, "Complexity") or ""
        desc = _extract_field(block, "Description") or ""
        fields: dict = {"input": inp, "output": out_val, "complexity": complexity, "description": desc}
        output_sub = _extract_output_subfields(block)
        # Only override scalar output with dict when genuine sub-fields were found.
        # Skip the override when the only key is the raw-fallback "response_shape"
        # (i.e. no recognised structured sub-field keywords were present).
        if output_sub and _REAL_OUTPUT_KEYS.intersection(output_sub):
            fields["output"] = output_sub
        evidence = _citation_from_block(block) or doc_path
        items.append({"kind": "ALG", "id": alg_id, "fields": fields, "evidence": evidence})

    # --- INT: External Integrations (### INT-001_{Slug} or ## INT-001) ---
    for m in re.finditer(r"^#{2,4}\s+(INT-\d+)", text, re.MULTILINE):
        int_id = m.group(1)
        block = _find_block(text, re.escape(int_id) + r"(?:_\w+)?")
        int_type = _extract_field(block, "Type") or ""
        target = _extract_field(block, "Target") or ""
        trigger = _extract_field(block, "Trigger") or ""
        payload = _extract_field(block, "Payload") or ""
        failure = _extract_field(block, "Failure handling") or _extract_field(block, "Failure") or ""
        fields: dict = {
            "type": int_type, "target": target, "trigger": trigger,
            "payload": payload, "failure_handling": failure,
        }
        output_sub = _extract_output_subfields(block)
        if output_sub:
            fields["output"] = output_sub
        evidence = _citation_from_block(block) or doc_path
        items.append({"kind": "INT", "id": int_id, "fields": fields, "evidence": evidence})

    # --- ENTITY: Key Entities table (4-column: Entity | Table | Key Columns | Purpose) ---
    # Template: | {ModelName} | `{table_name}` | {col1, col2} | {free-text purpose} |
    # id = ENTITY-{table_name} (backticks stripped)
    # Also supports old 3-column form: | table | key_cols | read|write|read/write |
    in_key_entities = False
    entity_section_depth = 0
    key_entities_re = re.compile(r"^(#{1,3})\s+Key Entities", re.IGNORECASE)
    # Collect lines under ## Key Entities section only to avoid false matches
    key_entity_lines: list[str] = []
    in_ke_section = False
    ke_depth = 0
    for line in text.splitlines():
        km = key_entities_re.match(line)
        if km:
            in_ke_section = True
            ke_depth = len(km.group(1))
            continue
        if in_ke_section:
            depth_m = re.match(r"^(#+)\s+", line)
            if depth_m and len(depth_m.group(1)) <= ke_depth:
                break
            key_entity_lines.append(line)

    # 4-column form: | Entity | Table | Key Columns | Purpose |
    entity_4col_re = re.compile(
        r"^\|\s*([A-Za-z][A-Za-z0-9_]*)\s*\|\s*`?([A-Za-z][A-Za-z0-9_]*)`?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
    )
    # 3-column form (legacy): | table | key_cols | read/write |
    entity_3col_re = re.compile(
        r"^\|\s*([A-Za-z_]\w*)\s*\|\s*([^|]+?)\s*\|\s*(read|write|read/write|r/w)\s*\|",
        re.IGNORECASE,
    )
    seen_entity_tables: set[str] = set()
    ke_source = key_entity_lines if key_entity_lines else text.splitlines()
    for line in ke_source:
        # Skip header and separator rows
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        # Skip separator rows
        if all(re.match(r"^-+$", c.replace(":", "").strip()) or not c for c in cells):
            continue
        # Skip header row: first cell is "Entity" or "Table" (case-insensitive)
        if cells[0].lower() in ("entity", "model", "table"):
            continue

        # Try 4-column form first
        m4 = entity_4col_re.match(line)
        if m4 and len(cells) >= 4:
            entity_name = m4.group(1).strip()
            table_name = m4.group(2).strip().strip("`")
            key_cols = m4.group(3).strip()
            purpose = m4.group(4).strip()
            eid = f"ENTITY-{table_name}"
            if eid not in seen_entity_tables:
                seen_entity_tables.add(eid)
                items.append({
                    "kind": "ENTITY", "id": eid,
                    "fields": {
                        "entity": entity_name,
                        "table": table_name,
                        "key_columns": key_cols,
                        "purpose": purpose,
                    },
                    "evidence": doc_path,
                })
            continue

        # Try 3-column form (legacy: table, key_cols, read/write purpose)
        m3 = entity_3col_re.match(line)
        if m3:
            table_name = m3.group(1).strip()
            key_cols = m3.group(2).strip()
            purpose = m3.group(3).strip()
            eid = f"ENTITY-{table_name}"
            if eid not in seen_entity_tables:
                seen_entity_tables.add(eid)
                items.append({
                    "kind": "ENTITY", "id": eid,
                    "fields": {"table": table_name, "key_columns": key_cols, "purpose": purpose},
                    "evidence": doc_path,
                })

    # --- SC: LIST form (dominant in real template) ---
    # Pattern: - **SC-001** {condition} (covers FR-0XX, ...)
    sc_list_re = re.compile(
        r"^-\s+\*\*(SC-\d+)\*\*\s+(.*?)\s+\(covers\s+([^)]+)\)"
    )
    for line in text.splitlines():
        m = sc_list_re.match(line)
        if not m:
            continue
        sc_id = m.group(1)
        if sc_id in _seen_sc:
            continue
        _seen_sc.add(sc_id)
        condition = m.group(2).strip()
        covers = m.group(3).strip()
        items.append({
            "kind": "SC", "id": sc_id,
            "fields": {"condition": condition, "covers": covers},
            "evidence": doc_path,
        })

    # --- SC: TABLE form (fallback for Cross-Cutting section) ---
    sc_table_re = re.compile(
        r"^\|\s*(SC-\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
    )
    for line in text.splitlines():
        m = sc_table_re.match(line)
        if not m:
            continue
        sc_id = m.group(1).strip()
        if sc_id in _seen_sc:
            continue
        _seen_sc.add(sc_id)
        condition = m.group(2).strip()
        covers = m.group(3).strip()
        items.append({
            "kind": "SC", "id": sc_id,
            "fields": {"condition": condition, "covers": covers},
            "evidence": doc_path,
        })

    return items


def _parse_behavior_logic(text: str, unit: str, doc_path: str) -> list[dict]:
    """Extract BL### blocks per behavior-logic-template.md."""
    items: list[dict] = []
    for m in re.finditer(r"^##\s+(BL\d+)", text, re.MULTILINE):
        bl_id = m.group(1)
        block = _find_block(text, re.escape(bl_id))
        bl_type = _extract_field(block, "Type") or ""
        trigger = _extract_field(block, "Trigger") or ""
        payload = _extract_field(block, "Payload") or ""
        source_symbol = (
            _extract_field(block, "Source Symbol")
            or _extract_field(block, "Source symbol")
            or ""
        )
        related_routes = _extract_field(block, "Related routes") or ""
        related_models = _extract_field(block, "Related models") or ""
        evidence = _citation_from_block(block) or f"{doc_path}"
        items.append({
            "kind": "BL", "id": bl_id,
            "fields": {
                "type": bl_type,
                "trigger": trigger,
                "payload": payload,
                "source_symbol": source_symbol,
                "related_routes": related_routes,
                "related_models": related_models,
            },
            "evidence": evidence,
        })
    return items


def _parse_api(text: str, unit: str, doc_path: str) -> list[dict]:
    """Extract ENDPOINT, GQL, GRPC items."""
    items: list[dict] = []

    # REST endpoints: ## or ### {ROUTE} — {METHOD} {/path}
    endpoint_heading_re = re.compile(
        r"^#{2,3}\s+.*?—\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[^\s]*)",
        re.IGNORECASE | re.MULTILINE,
    )
    for m in endpoint_heading_re.finditer(text):
        method = m.group(1).upper()
        path_val = m.group(2)
        endpoint_id = f"{method} {path_val}"
        # Extract the block after this heading, skipping past the heading line itself
        start_pos = m.start()
        eol = text.find("\n", start_pos)
        search_from = eol + 1 if eol != -1 else len(text)
        next_heading = re.search(r"^#{1,3}\s", text[search_from:], re.MULTILINE)
        if next_heading:
            block = text[start_pos: search_from + next_heading.start()]
        else:
            block = text[start_pos:]

        auth = _extract_field(block, "Auth") or _extract_field(block, "Authorization") or ""
        req_shape = _extract_field(block, "Request") or _extract_field(block, "Request body") or ""
        resp_shape = _extract_field(block, "Response") or _extract_field(block, "Response body") or ""
        status_codes = _extract_field(block, "Status codes") or _extract_field(block, "Status") or ""
        error_env = _extract_field(block, "Error envelope") or _extract_field(block, "Errors") or ""
        fields: dict = {
            "method": method, "path": path_val, "auth": auth,
            "request_shape": req_shape, "response_shape": resp_shape,
            "status_codes": status_codes, "error_envelope": error_env,
        }
        output_sub = _extract_output_subfields(block)
        if output_sub:
            fields["output"] = output_sub
        evidence = _citation_from_block(block) or f"{doc_path}"
        items.append({
            "kind": "ENDPOINT", "id": endpoint_id,
            "fields": fields, "evidence": evidence,
        })

    # GQL: look for "query |mutation" + name pattern
    gql_re = re.compile(
        r"^\|\s*(query|mutation)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        m = gql_re.match(line)
        if not m:
            continue
        op = m.group(1).strip()
        name = m.group(2).strip()
        args = m.group(3).strip()
        return_shape = m.group(4).strip()
        items.append({
            "kind": "GQL", "id": f"GQL-{name}",
            "fields": {"operation": op, "name": name, "args": args, "return_shape": return_shape},
            "evidence": f"{doc_path}",
        })

    # gRPC: look for service_method pattern
    grpc_re = re.compile(
        r"^\|\s*([A-Za-z]\w*\.[A-Za-z]\w*)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    for line in text.splitlines():
        m = grpc_re.match(line)
        if not m:
            continue
        service_method = m.group(1).strip()
        streaming = m.group(2).strip()
        request = m.group(3).strip()
        response = m.group(4).strip()
        items.append({
            "kind": "GRPC", "id": f"GRPC-{service_method}",
            "fields": {
                "service_method": service_method, "streaming": streaming,
                "request": request, "response": response,
            },
            "evidence": f"{doc_path}",
        })

    return items


def _parse_data_models(text: str, unit: str, doc_path: str) -> list[dict]:
    """Extract ENTITY, DISC, VALIDATION items."""
    items: list[dict] = []

    # ENTITY: ### {ENTITY_NAME} attribute tables (## or ### accepted)
    entity_heading_re = re.compile(r"^#{2,3}\s+([A-Za-z_]\w*)", re.MULTILINE)
    for m in entity_heading_re.finditer(text):
        entity_name = m.group(1)
        start_pos = m.start()
        # Skip past the current heading line before searching for the next heading
        eol = text.find("\n", start_pos)
        search_from = eol + 1 if eol != -1 else len(text)
        next_heading = re.search(r"^#{1,3}\s", text[search_from:], re.MULTILINE)
        if next_heading:
            block = text[start_pos: search_from + next_heading.start()]
        else:
            block = text[start_pos:]

        # Parse attribute table: | column | type | constraints |
        attr_re = re.compile(
            r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|"
        )
        attributes: list[dict] = []
        for line in block.splitlines():
            am = attr_re.match(line)
            if not am:
                continue
            col = am.group(1).strip()
            typ = am.group(2).strip()
            constraint = am.group(3).strip()
            # Skip separator and header rows
            if re.match(r"^-+$", col.replace("|", "").strip()):
                continue
            if col.lower() in ("column", "field", "attribute", "name"):
                continue
            attributes.append({"name": col, "type": typ, "constraints": constraint})

        # Relationships
        rels = _extract_field(block, "Relationships") or ""

        if attributes or rels:
            items.append({
                "kind": "ENTITY", "id": f"ENTITY-{entity_name}",
                "fields": {"attributes": attributes, "relationships": rels},
                "evidence": f"{doc_path}",
            })

    # DISC: Discriminator Fields table | field | values |
    disc_re = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
    )
    disc_section = _find_block(text, r"Discriminator Fields?")
    for line in disc_section.splitlines():
        m = disc_re.match(line)
        if not m:
            continue
        field = m.group(1).strip()
        values = m.group(2).strip()
        if field.lower() in ("field", "column") or re.match(r"^-+$", field):
            continue
        items.append({
            "kind": "DISC", "id": f"DISC-{field}",
            "fields": {"field": field, "values": values},
            "evidence": f"{doc_path}",
        })

    # VALIDATION: | field | constraint | error_message |
    val_re = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|"
    )
    val_section = _find_block(text, r"Validation Rules?")
    for line in val_section.splitlines():
        m = val_re.match(line)
        if not m:
            continue
        field = m.group(1).strip()
        constraint = m.group(2).strip()
        error_msg = m.group(3).strip()
        if field.lower() in ("field", "column", "attribute") or re.match(r"^-+$", field):
            continue
        items.append({
            "kind": "VALIDATION", "id": f"VAL-{field}",
            "fields": {"field": field, "constraint": constraint, "error_message": error_msg},
            "evidence": f"{doc_path}",
        })

    return items


def _parse_screen_spec(text: str, unit: str, doc_path: str) -> list[dict]:
    """Extract FLOW_BRANCH, DATA_FIELD, UI_STATE, VALIDATION items."""
    items: list[dict] = []

    # FLOW_BRANCH: Branches table | decision_point | condition | outcome |
    branch_section = _find_block(text, r"Branches|User Flow")
    br_re = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
    for line in branch_section.splitlines():
        m = br_re.match(line)
        if not m:
            continue
        dp = m.group(1).strip()
        cond = m.group(2).strip()
        outcome = m.group(3).strip()
        if dp.lower() in ("decision point", "decision", "branch") or re.match(r"^-+$", dp):
            continue
        items.append({
            "kind": "FLOW_BRANCH", "id": f"BRANCH-{dp[:30]}",
            "fields": {"decision_point": dp, "condition": cond, "outcome": outcome},
            "evidence": f"{doc_path}",
        })

    # DATA_FIELD: Data Inventory table | binding | source | format | empty_behavior | cross_ref |
    data_section = _find_block(text, r"Data Inventory")
    df_re = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    for line in data_section.splitlines():
        m = df_re.match(line)
        if not m:
            continue
        binding = m.group(1).strip()
        source = m.group(2).strip()
        fmt = m.group(3).strip()
        empty_beh = m.group(4).strip()
        cross_ref = m.group(5).strip()
        if binding.lower() in ("binding", "field", "data field") or re.match(r"^-+$", binding):
            continue
        items.append({
            "kind": "DATA_FIELD", "id": f"FIELD-{binding[:30]}",
            "fields": {
                "binding": binding, "source": source, "format": fmt,
                "empty_behavior": empty_beh, "cross_ref": cross_ref,
            },
            "evidence": f"{doc_path}",
        })

    # UI_STATE: UI States table | state | trigger | visual_behavior | user_action |
    state_section = _find_block(text, r"UI States?")
    st_re = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    for line in state_section.splitlines():
        m = st_re.match(line)
        if not m:
            continue
        state = m.group(1).strip()
        trigger = m.group(2).strip()
        visual_beh = m.group(3).strip()
        user_action = m.group(4).strip()
        if state.lower() in ("state", "ui state") or re.match(r"^-+$", state):
            continue
        items.append({
            "kind": "UI_STATE", "id": f"STATE-{state[:30]}",
            "fields": {
                "state": state, "trigger": trigger,
                "visual_behavior": visual_beh, "user_action": user_action,
            },
            "evidence": f"{doc_path}",
        })

    # VALIDATION: | field | required | constraints | error_message | async_check |
    val_section = _find_block(text, r"Validation")
    val_re = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    for line in val_section.splitlines():
        m = val_re.match(line)
        if not m:
            continue
        field = m.group(1).strip()
        required = m.group(2).strip()
        constraints = m.group(3).strip()
        error_msg = m.group(4).strip()
        async_check = m.group(5).strip()
        if field.lower() in ("field", "input") or re.match(r"^-+$", field):
            continue
        items.append({
            "kind": "VALIDATION", "id": f"VAL-{field[:30]}",
            "fields": {
                "field": field, "required": required, "constraints": constraints,
                "error_message": error_msg, "async_check": async_check,
            },
            "evidence": f"{doc_path}",
        })

    return items


_ARTIFACT_PARSERS = {
    "technical-spec": _parse_technical_spec,
    "behavior-logic": _parse_behavior_logic,
    "api":            _parse_api,
    "data-models":    _parse_data_models,
    "screen-spec":    _parse_screen_spec,
}


def _atomic_write(path: Path, data: object) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def parse_unit(unit: dict, project_root: Path) -> dict:
    """Parse one unit's doc files and return schema JSON."""
    artifact = unit.get("artifact", "technical-spec")
    parser = _ARTIFACT_PARSERS.get(artifact, _parse_technical_spec)
    all_items: list[dict] = []

    for rel_doc_path in unit.get("doc_paths", []):
        doc_path = project_root / rel_doc_path
        read_result = read_text_safe(doc_path)
        if read_result is None:
            continue
        doc_text, _ = read_result
        items = parser(doc_text, unit["unit"], rel_doc_path)
        all_items.extend(items)

    return {
        "unit": unit["unit"],
        "artifact": artifact,
        "items": all_items,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Parse doc structured fields into schema JSON")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--units", metavar="FILE",
                   help="Path to doc-units.json (from scope_doc_units.py)")
    g.add_argument("--path", metavar="DOC",
                   help="Process a single doc file directly")
    p.add_argument("--artifact", default="technical-spec",
                   choices=list(_ARTIFACT_PARSERS.keys()),
                   help="Artifact type (used with --path; default: technical-spec)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--out", default="doc-schema.json", metavar="FILE",
                   help="Output path (default: doc-schema.json)")
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    schemas: list[dict] = []

    if args.path:
        doc_path = Path(args.path).resolve()
        if not doc_path.is_file():
            print(f"[ERROR] --path is not a file: {doc_path}", file=sys.stderr)
            return 2
        read_result = read_text_safe(doc_path)
        if read_result is None:
            print(f"[ERROR] cannot read {doc_path}", file=sys.stderr)
            return 2
        doc_text, _ = read_result
        parser = _ARTIFACT_PARSERS[args.artifact]
        try:
            rel = str(doc_path.relative_to(project_root))
        except ValueError:
            rel = str(doc_path)
        items = parser(doc_text, doc_path.parent.name, rel)
        schemas.append({
            "unit": doc_path.parent.name,
            "artifact": args.artifact,
            "items": items,
        })
    else:
        units_path = Path(args.units).resolve()
        if not units_path.is_file():
            print(f"[ERROR] --units file not found: {units_path}", file=sys.stderr)
            return 2
        try:
            units = json.loads(units_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[ERROR] cannot load {units_path}: {exc}", file=sys.stderr)
            return 2
        for unit in units:
            schemas.append(parse_unit(unit, project_root))

    out_path = Path(args.out).resolve()
    _atomic_write(out_path, schemas)
    total_items = sum(len(s["items"]) for s in schemas)
    print(f"[parse_doc_schema] wrote {len(schemas)} unit(s), {total_items} item(s) → {out_path}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
