#!/usr/bin/env python3
"""Wave 6.85 — process-flow deterministic validator.
Checks flows/*.md against process-flow-researcher-contract rules.
Regex + frontmatter parsing; stdlib only.
Exit codes: 0 (no critical), 1 (critical), 2 (internal).
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, load_summary, recalculate_totals, derive_overall_status  # noqa: E402
from _flow_sm_lib import scan_entity_state_machines  # noqa: E402

VALIDATOR = "process_flow"

FLOW_CODE_RE = re.compile(r"^FLOW\d{3}_[A-Za-z0-9]+$")
FLOW_HEADING_RE = re.compile(r"^#\s+(FLOW\d{3})", re.MULTILINE)
CITATION_RE = re.compile(r"`[^`]+:\d+")
TRANSITION_ROW_RE = re.compile(r"^\|\s*[A-Z]\d+\s*\|")
TRIGGER_TYPES = {"user-action", "scheduled", "event", "derived"}
SM_REF_RE = re.compile(r"SM-\d{3}")
EDGE_SPLIT_RE = re.compile(r"-+>")
# pseudo-states that are not real stored states (entry/exit placeholders)
_NON_STATES = {"null", "unseen", "none", "---", ""}

# system-flow specific regexes
HANDOFF_ROW_RE = re.compile(r"^\|\s*H\d+\s*\|")
# Tighter than CITATION_RE: filename portion must be non-whitespace (rejects `event bus:1`)
HANDOFF_CITE_RE = re.compile(r"`\S+:\d+")
FLOW_REF_RE = re.compile(r"FLOW\d{3}_[A-Za-z0-9]+")

_MULTILINE_LIST_ITEM_RE = re.compile(r"^\s+-\s+(.+)$")


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^<!--.*?-->\s*\n?---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    fm_lines = m.group(1).splitlines()
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if ":" not in line or line.strip().startswith("#"):
            i += 1
            continue
        key, val = line.split(":", 1)
        key = key.strip().lstrip("# ")
        val = val.split("#")[0].strip()
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
        elif val == "":
            # Look ahead for multiline YAML list items (  - item)
            items = []
            j = i + 1
            while j < len(fm_lines):
                item_m = _MULTILINE_LIST_ITEM_RE.match(fm_lines[j])
                if item_m:
                    item = item_m.group(1).strip()
                    # strip inline comment
                    item = item.split("#")[0].strip()
                    # strip surrounding backticks or quotes
                    item = item.strip("`").strip('"').strip("'")
                    if item:
                        items.append(item)
                    j += 1
                else:
                    break
            if items:
                val = items
                i = j
                fm[key] = val
                continue
        fm[key] = val
        i += 1
    return fm


def _parse_states_table(lines: list[str]) -> list[str]:
    states = []
    in_states = False
    past_header = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## States") or stripped.startswith("## The persisted machine"):
            in_states = True
            past_header = False
            continue
        if in_states and stripped.startswith("## "):
            break
        if in_states and stripped.startswith("|"):
            if re.match(r"^\|\s*[-:]+", stripped):
                past_header = True
                continue
            if not past_header:
                continue
            cells = [c.strip() for c in stripped.split("|")]
            cells = [c for c in cells if c]
            if cells:
                state = cells[0].strip("`").strip()
                if state and state.lower() not in ("state", "---"):
                    states.append(state)
    return states


def _is_placeholder(state: str) -> bool:
    """Bracketed pseudo-states ([new], [any...]) and null/unseen are not real states."""
    s = state.strip()
    return s.startswith("[") or s.lower() in _NON_STATES


def _parse_edge(cell: str) -> tuple[str | None, str | None]:
    """Parse a 'From --> To' transition cell into (from, to). None if unparseable."""
    c = cell.strip().strip("`").strip()
    parts = EDGE_SPLIT_RE.split(c)
    if len(parts) != 2:
        return None, None
    return parts[0].strip().strip("`").strip(), parts[1].strip().strip("`").strip()


def _parse_terminal_states(lines: list[str]) -> set[str]:
    """Collect backtick-quoted state tokens on prose lines that declare terminality.

    Conservative: any line mentioning 'terminal'/'absorbing' contributes its tokens.
    Over-collecting only suppresses warnings (safer for a heuristic warning)."""
    terms: set[str] = set()
    for line in lines:
        low = line.lower()
        if "terminal" in low or "absorbing" in low:
            for tok in re.findall(r"`([^`]+)`", line):
                t = tok.split("(")[0].strip()
                if t and not _is_placeholder(t):
                    terms.add(t.lower())
    return terms


def _parse_transitions(lines: list[str]) -> list[dict]:
    transitions = []
    for line in lines:
        if not TRANSITION_ROW_RE.match(line.strip()):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) < 6:
            continue
        trigger_type = cells[2].strip().strip("*").strip().lower()
        source = cells[-1].strip() if len(cells) >= 6 else ""
        frm, to = _parse_edge(cells[1])
        transitions.append({
            "id": cells[0].strip(),
            "trigger_type": trigger_type,
            "source": source,
            "from": frm,
            "to": to,
            "line": line,
        })
    return transitions


def _parse_section_rows(lines: list[str], heading: str) -> list[str]:
    """Return data-row strings under the given ## heading, stopping at the next ## heading."""
    rows = []
    in_section = False
    past_header = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if stripped.startswith(f"## {heading}") or stripped == f"## {heading}":
                in_section = True
                past_header = False
                continue
            elif in_section:
                break
        if in_section and stripped.startswith("|"):
            if re.match(r"^\|\s*[-:]+", stripped):
                past_header = True
                continue
            if not past_header:
                continue
            rows.append(stripped)
    return rows


def _issue(sev, rid, flow_file, root, line_num, msg):
    try:
        loc = str(flow_file.relative_to(root))
    except ValueError:
        loc = str(flow_file)
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": loc, "line": line_num}, "message": msg}


def _validate_system_flow_file(flow_file: Path, root: Path, composed_state_fields: set[str]) -> list[dict]:
    """Validate a system-flow.md file against FL.2 deterministic rules."""
    assert_under(flow_file, root)
    issues = []
    text = flow_file.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    fm = _parse_frontmatter(text)

    # Rule: SystemFlow.composes_missing — frontmatter composes absent or empty
    composes_raw = fm.get("composes", "")
    if isinstance(composes_raw, str):
        composes = [composes_raw] if composes_raw else []
    else:
        composes = [c for c in composes_raw if c]

    if not composes:
        issues.append(_issue("critical", "SystemFlow.composes_missing",
                             flow_file, root, 1,
                             "system-flow frontmatter has no 'composes:' list or it is empty"))
        return issues  # early return: rest of checks depend on composes

    # Rule: SystemFlow.composes_insufficient — <2 flows composed
    if len(composes) < 2:
        issues.append(_issue("critical", "SystemFlow.composes_insufficient",
                             flow_file, root, 1,
                             f"system-flow composes only {len(composes)} flow(s); "
                             f"cross-flow synthesis requires >=2"))

    # Rule: SystemFlow.handoffs_missing — zero rows in Cross-Flow Handoffs section
    handoff_rows = _parse_section_rows(lines, "Cross-Flow Handoffs")
    handoff_data_rows = [r for r in handoff_rows if HANDOFF_ROW_RE.match(r)]
    if not handoff_data_rows:
        issues.append(_issue("critical", "SystemFlow.handoffs_missing",
                             flow_file, root, 1,
                             "system-flow has no rows in ## Cross-Flow Handoffs section"))
    else:
        # Rule: SystemFlow.handoff_citation_missing — per row, last cell must match HANDOFF_CITE_RE
        for row in handoff_data_rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            source_cell = cells[-1] if cells else ""
            if not HANDOFF_CITE_RE.search(source_cell):
                # Extract H<n> id from first cell
                h_id = cells[0].strip() if cells else "?"
                issues.append(_issue("critical", "SystemFlow.handoff_citation_missing",
                                     flow_file, root, 1,
                                     f"handoff row {h_id} Source cell has no `file:line` citation "
                                     f"(got: '{source_cell}')"))

    # Rule: SystemFlow.inventory_missing — no State-Field Inventory table or zero data rows
    inventory_rows = _parse_section_rows(lines, "State-Field Inventory")
    # Also accept the heading "State-Field Inventory (stored vs derived audit)"
    if not inventory_rows:
        inventory_rows = _parse_section_rows(lines, "State-Field Inventory (stored vs derived audit)")
    if not inventory_rows:
        issues.append(_issue("critical", "SystemFlow.inventory_missing",
                             flow_file, root, 1,
                             "system-flow has no ## State-Field Inventory section or it has no data rows"))
    else:
        # Build set of inventory Field cells (first cell, backtick-stripped, lowercased)
        inventory_fields: set[str] = set()
        for row in inventory_rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if cells:
                field = cells[0].strip("`").strip().lower()
                if field and field not in ("field", "---"):
                    inventory_fields.add(field)

        # Rule: SystemFlow.inventory_incomplete — composed Tier-1 state-field missing from inventory
        if composed_state_fields:
            for f in sorted(composed_state_fields):
                if f.lower() not in inventory_fields:
                    issues.append(_issue("warning", "SystemFlow.inventory_incomplete",
                                         flow_file, root, 1,
                                         f"composed Tier-1 state-field '{f}' not found in "
                                         f"State-Field Inventory (case-insensitive match)"))

    # Rule: SystemFlow.phantom_flow_ref — FLOW### in Lanes/Mermaid not in composes
    composes_set = set(composes)
    # Scan Lanes section and Master Composition Diagram section for FLOW refs
    lanes_rows = _parse_section_rows(lines, "Lanes")
    diagram_rows = _parse_section_rows(lines, "Master Composition Diagram")
    # Also scan raw lines in those sections (including mermaid code blocks)
    scan_sections = set()
    _in_scan = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Lanes") or stripped.startswith("## Master Composition Diagram"):
            _in_scan = True
            continue
        if _in_scan and stripped.startswith("## "):
            _in_scan = False
        if _in_scan:
            for ref in FLOW_REF_RE.findall(line):
                scan_sections.add(ref)
    for row in lanes_rows + diagram_rows:
        for ref in FLOW_REF_RE.findall(row):
            scan_sections.add(ref)

    for ref in sorted(scan_sections):
        if ref not in composes_set:
            issues.append(_issue("warning", "SystemFlow.phantom_flow_ref",
                                 flow_file, root, 1,
                                 f"flow reference '{ref}' appears in Lanes/Diagram but is not "
                                 f"listed in 'composes:' frontmatter"))

    return issues


def _validate_flow_file(flow_file: Path, root: Path, entity_sms: list[dict] | None = None) -> list[dict]:
    issues = []
    text = flow_file.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    fm = _parse_frontmatter(text)

    kind = fm.get("kind", "process-flow")
    # system-flow is handled by _validate_system_flow_file — skip here
    if kind == "system-flow":
        return []

    flow_code = None
    for i, line in enumerate(lines):
        m = FLOW_HEADING_RE.match(line)
        if m:
            flow_code = m.group(1)
            raw_heading = line.strip().lstrip("# ").split("—")[0].split("---")[0].strip()
            if not FLOW_CODE_RE.match(raw_heading):
                issues.append(_issue("critical", "ProcessFlow.flow_code_invalid",
                                     flow_file, root, i + 1,
                                     f"FLOW code '{raw_heading}' doesn't match ^FLOW\\d{{3}}_[A-Za-z0-9]+$"))
            break

    if not flow_code:
        issues.append(_issue("critical", "ProcessFlow.flow_code_invalid",
                             flow_file, root, 1, "no FLOW### heading found"))
        return issues

    state_field = fm.get("state_field", "")
    state_fields = fm.get("state_fields", [])
    if isinstance(state_fields, str):
        state_fields = [state_fields]
    if state_field and not state_fields:
        state_fields = [state_field]
    derived_views = fm.get("derived_views", [])
    if isinstance(derived_views, str):
        derived_views = [derived_views]
    depth = fm.get("depth", "")

    if depth == "thin":
        return issues

    states = _parse_states_table(lines)
    transitions = _parse_transitions(lines)

    for t in transitions:
        if not CITATION_RE.search(t["source"]):
            issues.append(_issue("critical", "ProcessFlow.citation_missing",
                                 flow_file, root, None,
                                 f"transition {t['id']} has no file:line citation in Source column"))

    trigger_types_found = set()
    for t in transitions:
        for tt in TRIGGER_TYPES:
            if tt in t["trigger_type"]:
                trigger_types_found.add(tt)

    if len(transitions) < 2 or len(trigger_types_found) < 2:
        issues.append(_issue("critical", "ProcessFlow.sub_threshold_flow",
                             flow_file, root, 1,
                             f"flow has {len(transitions)} transitions and {len(trigger_types_found)} trigger types; "
                             f"gate requires >=2 of each (should have been hard-omitted)"))

    all_known = set()
    for sf in state_fields:
        all_known.add(sf)
    for dv in derived_views:
        all_known.add(dv)

    if states and state_fields:
        enum_values_raw = set()
        for line in lines:
            if "**Enum source:**" in line or "**Enum:**" in line:
                m = re.search(r"[`—–-]\s*(.+?)$", line)
                if m:
                    for v in re.split(r"[,→\s]+", m.group(1).strip().rstrip("`")):
                        v = v.strip().strip("`").strip()
                        if v and v not in ("→", "—", "-"):
                            enum_values_raw.add(v)

        known_states = enum_values_raw | all_known
        if known_states:
            for state in states:
                normalized = state.split("(")[0].strip()
                if normalized and normalized.lower() not in {s.lower() for s in known_states}:
                    if normalized.lower() not in ("null", "unseen", "none", "---"):
                        issues.append(_issue("critical", "ProcessFlow.fabricated_state",
                                             flow_file, root, None,
                                             f"state '{normalized}' not found in frontmatter state_fields, "
                                             f"derived_views, or enum source"))

    # B2 — stuck-state (liveness backstop): a state that is a transition target
    # but never a source, and is not declared terminal, may be unreachable-from
    # (no exit). Warning only — researcher adds a LIVENESS: note or marks it terminal.
    froms = {t["from"] for t in transitions if t["from"] and not _is_placeholder(t["from"])}
    tos = {t["to"] for t in transitions if t["to"] and not _is_placeholder(t["to"])}
    terminal = _parse_terminal_states(lines)
    for sink in sorted(tos - froms):
        norm = sink.split("(")[0].strip()
        if _is_placeholder(norm) or norm.lower() in terminal:
            continue
        issues.append(_issue("warning", "ProcessFlow.possible_stuck_state",
                             flow_file, root, None,
                             f"state '{norm}' is a transition target with no outgoing transition and is "
                             f"not declared terminal — possible stuck-state; add a LIVENESS: note in "
                             f"Open Questions or mark it terminal"))

    # B3 — SM/FLOW DRY cross-ref: if this flow's states overlap an entity-kind
    # SM-### already documented in a feature spec, the flow MUST cite it
    # (`see SM-### in F###`) rather than re-stating the transition table.
    if entity_sms and states and not SM_REF_RE.search(text):
        flow_states = {s.split("(")[0].strip().lower() for s in states}
        flow_states -= _NON_STATES
        for sm in entity_sms:
            overlap = len(flow_states & {s.lower() for s in sm["states"]})
            if overlap >= 3:
                issues.append(_issue("warning", "ProcessFlow.sm_crossref_missing",
                                     flow_file, root, None,
                                     f"flow states overlap entity {sm['code']} in {sm['feature']} by "
                                     f"{overlap} states but the flow body has no SM-### token "
                                     f"(SM/FLOW DRY boundary — add `see {sm['code']} in {sm['feature'].split('_')[0]}`)"))
                break

    return issues


def validate(plan_dir: Path, root: Path, single_file: Path | None = None) -> dict:
    flows_dir = plan_dir / "artifacts" / "flows"
    issues: list[dict] = []
    flow_codes: dict[str, str] = {}

    if single_file:
        flow_files = [single_file] if single_file.is_file() else []
    elif flows_dir.is_dir():
        flow_files = sorted(f for f in flows_dir.glob("*.md") if f.name != ".completed")
    else:
        flow_files = []

    entity_sms = scan_entity_state_machines(plan_dir / "artifacts" / "features")

    # Pass A — index Tier-1 flows: map FLOW### code -> set of state fields
    tier1_fields_by_code: dict[str, set[str]] = {}
    for ff in flow_files:
        text = ff.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        if fm.get("kind", "process-flow") == "system-flow":
            continue
        m = FLOW_HEADING_RE.search(text)
        if m:
            code = m.group(1)
            state_field = fm.get("state_field", "")
            state_fields = fm.get("state_fields", [])
            if isinstance(state_fields, str):
                state_fields = [state_fields] if state_fields else []
            fields: set[str] = set()
            if state_field:
                fields.add(state_field)
            fields.update(state_fields)
            tier1_fields_by_code[code] = fields

    # Pass B — validate each file
    for ff in flow_files:
        text = ff.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        kind = fm.get("kind", "process-flow")

        if kind == "system-flow":
            # Build composed_state_fields: union of state fields from composed Tier-1 flows only
            composes_raw = fm.get("composes", "")
            if isinstance(composes_raw, str):
                composes_list = [composes_raw] if composes_raw else []
            else:
                composes_list = [c for c in composes_raw if c]
            composed_state_fields: set[str] = set()
            for c in composes_list:
                # Match on FLOW### prefix (the code portion before underscore suffix)
                flow_code_prefix = re.match(r"(FLOW\d{3})", c)
                if flow_code_prefix:
                    prefix = flow_code_prefix.group(1)
                    for code, fields in tier1_fields_by_code.items():
                        if code == prefix:
                            composed_state_fields |= fields
            file_issues = _validate_system_flow_file(ff, root, composed_state_fields)
            issues.extend(file_issues)
        else:
            file_issues = _validate_flow_file(ff, root, entity_sms)
            issues.extend(file_issues)

        # track flow codes for duplicate check (system-flow has no FLOW### heading)
        m = FLOW_HEADING_RE.search(text)
        if m:
            code = m.group(1)
            if code in flow_codes:
                try:
                    loc = str(ff.relative_to(root))
                except ValueError:
                    loc = str(ff)
                issues.append({"validator": VALIDATOR, "severity": "critical",
                               "rule_id": "ProcessFlow.flow_code_duplicate",
                               "location": {"file": loc, "line": 1},
                               "message": f"FLOW code {code} also used in {flow_codes[code]}"})
            else:
                try:
                    flow_codes[code] = str(ff.relative_to(root))
                except ValueError:
                    flow_codes[code] = str(ff)

    completed = flows_dir / ".completed" if flows_dir.is_dir() else None
    if not single_file and (not completed or not completed.exists()):
        issues.append({"validator": VALIDATOR, "severity": "critical",
                       "rule_id": "ProcessFlow.completed_missing",
                       "location": {"file": "flows/.completed", "line": 0},
                       "message": "flows/.completed marker not found"})

    return {"validator": VALIDATOR,
            "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "plan_dir": str(plan_dir),
            "status": "FAIL" if any(i["severity"] == "critical" for i in issues) else "PASS",
            "summary": {
                "critical": sum(1 for i in issues if i["severity"] == "critical"),
                "warning": sum(1 for i in issues if i["severity"] == "warning"),
            },
            "issues": issues,
            "flow_codes": flow_codes}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.85 process-flow validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--flow-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
    else:
        single = Path(args.flow_file).resolve()
        # single = <plan>/artifacts/flows/<file>.md → plan root is three levels up,
        # so scan_entity_state_machines(plan_dir/artifacts/features) resolves correctly.
        plan_dir = single.parent.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(plan_dir, root, single)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    crit = result["summary"]["critical"]

    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"],
                "summary": result["summary"],
                "issues": result["issues"],
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2

    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
