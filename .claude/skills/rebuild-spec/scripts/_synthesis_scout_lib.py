# layout-exempt: rebuild-spec synthesis scout — docs/system is this skill's own output target
"""Scout-report builder for Phase D system synthesis (v19).

Python computes FACTS (DATA tables only), never builds documents directly.
The LLM system-researcher authors all documents, tables, AND Mermaid diagrams.

`build_scout_facts` returns a dict of named Markdown-string blocks (DATA tables;
no Mermaid blocks — those are authored by the researcher).
`assemble_scout_report` assembles the .system-scout-report.md from those blocks
(DATA sections only — no ```mermaid fences).

Stdlib only. All writes via _synthesis_io_lib.atomic_write.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from _system_synthesis_lib import (
    entity_ownership,
    event_flows,
    fan_in_out,
    sanitize_field,
    self_loop_topics,
)


# ---------------------------------------------------------------------------
# Table-block builders
# ---------------------------------------------------------------------------


def _build_edge_table_block(edges: list[dict[str, Any]]) -> str:
    lines = [
        "| From | To | Type | Label | Status |",
        "|------|----|------|-------|--------|",
    ]
    if not edges:
        lines.append("| _(none detected)_ | | | | |")
    else:
        for e in edges:
            src = sanitize_field(e.get("from", ""))
            tgt = sanitize_field(e.get("to", ""))
            etype = sanitize_field(e.get("type", ""))
            label = sanitize_field(e.get("label", ""))
            status = "[UNVERIFIED]" if not e.get("verified") else "verified"
            lines.append(f"| {src} | {tgt} | {etype} | {label} | {status} |")
    return "\n".join(lines) + "\n"


def _build_fan_in_out_table_block(
    digests: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> str:
    fan_out, fan_in = fan_in_out(edges)
    lines = [
        "| Service | Fan-out (calls) | Fan-in (called by) |",
        "|---------|-----------------|--------------------|",
    ]
    for d in sorted(digests, key=lambda x: str(x.get("service", ""))):
        raw = str(d.get("service", ""))
        svc = sanitize_field(raw)
        lines.append(f"| {svc} | {fan_out.get(raw, 0)} | {fan_in.get(raw, 0)} |")
    return "\n".join(lines) + "\n"


def _build_self_loop_topics_block(digests: list[dict[str, Any]]) -> str:
    loops = self_loop_topics(digests)
    if not loops:
        return "_(none — no service both produces and consumes the same topic)_\n"
    lines: list[str] = []
    for svc, topic in loops:
        lines.append(f"- **{sanitize_field(svc)}** ↻ `{sanitize_field(topic)}`")
    return "\n".join(lines) + "\n"


def _build_entity_ownership_table_block(digests: list[dict[str, Any]]) -> str:
    ownership = entity_ownership(digests)
    lines = [
        "| Entity | Owner Service | ID Field | ID Type | Visibility |",
        "|--------|---------------|----------|---------|------------|",
    ]
    if not ownership:
        lines.append("| _(no entities declared)_ | | | | |")
    else:
        for row in ownership:
            lines.append(
                f"| {sanitize_field(row['name'])} | {sanitize_field(row['owner'])} "
                f"| {sanitize_field(row['id_field'])} | {sanitize_field(row['id_type'])} "
                f"| {sanitize_field(row['visibility'])} |"
            )
    return "\n".join(lines) + "\n"


def _build_correlation_table_block(suggestions: list[dict[str, Any]]) -> str:
    lines = [
        "| Entity A (Service) | Entity B (Service) | Match Reason | Status |",
        "|--------------------|--------------------|--------------| -------|",
    ]
    if not suggestions:
        lines.append("| _(no correlations detected)_ | | | |")
    else:
        for s in suggestions:
            a, b = s["entity_a"], s["entity_b"]
            ea = f"{sanitize_field(a['name'])} ({sanitize_field(a['service'])})"
            eb = f"{sanitize_field(b['name'])} ({sanitize_field(b['service'])})"
            reason = sanitize_field(s.get("match_reason", ""))
            lines.append(f"| {ea} | {eb} | {reason} | [UNVERIFIED] |")
    return "\n".join(lines) + "\n"


def _build_event_flow_table_block(digests: list[dict[str, Any]]) -> str:
    flows = event_flows(digests)
    lines = [
        "| Topic | Producer(s) | Consumer(s) |",
        "|-------|-------------|-------------|",
    ]
    if not flows:
        lines.append("| _(no topics detected)_ | | |")
    else:
        for f in flows:
            producers = ", ".join(sanitize_field(s) for s in f["producers"]) or "_(none)_"
            consumers = ", ".join(sanitize_field(s) for s in f["consumers"]) or "_(none)_"
            lines.append(
                f"| {sanitize_field(f['topic'])} | {producers} | {consumers} |"
            )
    return "\n".join(lines) + "\n"


def _build_services_table(digests: list[dict[str, Any]], comp_base: str) -> str:
    """Services table for the scout report: service, role, stack, reused, docs_path (absolute)."""
    lines = [
        "| Service | Role | Stack | Reused | Docs path |",
        "|---------|------|-------|--------|-----------|",
    ]
    if not digests:
        lines.append("| _(no services)_ | | | | |")
    else:
        for d in sorted(digests, key=lambda x: str(x.get("service", ""))):
            raw = str(d.get("service", ""))
            svc = sanitize_field(raw)
            role = sanitize_field(d.get("role", "")) or "_(unknown)_"
            stack = sanitize_field(d.get("stack", "")) or "unknown"
            is_reused = d.get("provenance", "extracted") == "docs-derived"
            reused = "yes" if is_reused else "no"
            # Absolute path to the component docs tree (the researcher reads this).
            docs_path = os.path.join(comp_base, raw)
            lines.append(
                f"| {svc} | {role} | {stack} | {reused} | {sanitize_field(docs_path)} |"
            )
    return "\n".join(lines) + "\n"


def _build_confidence_table(digests: list[dict[str, Any]]) -> str:
    """Compact confidence summary for the scout report footer."""
    lines = [
        "| Service | Confidence | Signals |",
        "|---------|------------|---------|",
    ]
    for d in sorted(digests, key=lambda x: str(x.get("service", ""))):
        is_reused = d.get("provenance", "extracted") == "docs-derived"
        raw_svc = sanitize_field(d.get("service", ""))
        svc = f"{raw_svc} (reused)" if is_reused else raw_svc
        n_rpc = len([r for r in d.get("rpc", []) if isinstance(r, dict)])
        n_topic = len([t for t in d.get("topic", []) if isinstance(t, dict)])
        n_entity = len([e for e in d.get("entity", []) if isinstance(e, dict)])
        total = n_rpc + n_topic + n_entity
        confidence = sanitize_field(d.get("extraction_confidence", ""))
        if not confidence:
            if is_reused:
                confidence = "docs-derived"
            else:
                confidence = "high" if total >= 3 else "medium" if total >= 1 else "low"
        lines.append(f"| {svc} | {confidence} | rpc={n_rpc} topic={n_topic} entity={n_entity} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_scout_facts(
    digests: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    suggestions: list[dict[str, Any]],
    snap: str,
    abs_root: str,
    layout_mode: str,
    primary_lang: str,
) -> dict[str, str]:
    """Build the facts dict of named Markdown blocks (DATA tables only — no Mermaid).

    Block names are used internally by assemble_scout_report. The scout report
    is DATA only in v19 — all Mermaid diagrams are authored by the LLM researcher.

    `abs_root`, `layout_mode`, `primary_lang` are used to compute the absolute docs path
    for each component in the Services table (required by the researcher).
    """
    # Compute per-component absolute docs path.
    # In per-lang mode: <abs_root>/docs/<primary_lang>/components/<name>/
    # In single-lang mode: <abs_root>/docs/components/<name>/
    if layout_mode == "per-lang":
        comp_base = os.path.join(abs_root, "docs", primary_lang, "components")
    else:
        comp_base = os.path.join(abs_root, "docs", "components")

    return {
        "snapshot-hash": snap,
        "edge-table": _build_edge_table_block(edges),
        "fan-in-out-table": _build_fan_in_out_table_block(digests, edges),
        "self-loop-topics": _build_self_loop_topics_block(digests),
        "entity-ownership-table": _build_entity_ownership_table_block(digests),
        "correlation-table": _build_correlation_table_block(suggestions),
        "event-flow-table": _build_event_flow_table_block(digests),
        # Internal-only keys for the services + per-component-confidence tables in the
        # scout report itself (prefixed with _ to distinguish from researcher-facing blocks).
        "_services_table": _build_services_table(digests, comp_base),
        "_confidence_table": _build_confidence_table(digests),
    }


def assemble_scout_report(
    facts: dict[str, str],
    timestamp: str,
) -> str:
    """Assemble the .system-scout-report.md from the facts dict.

    v19: DATA tables only — no Mermaid fences. The LLM researcher draws all diagrams.
    """
    lines: list[str] = [
        "# System Scout Report (facts — do not edit)",
        "",
        f"<!-- generated by rebuild-spec synthesize_system — {timestamp} -->",
        f"<!-- snapshot-hash: {facts['snapshot-hash']} -->",
        "",
        "## Services",
        "<!-- per component: name, role, stack, reused flag, ABSOLUTE docs path -->",
        "",
        facts["_services_table"],
        "## Edges (statically observed — [UNVERIFIED])",
        "",
        facts["edge-table"],
        "## Fan-in / Fan-out",
        "",
        facts["fan-in-out-table"],
        "## Self-loop Topics",
        "",
        facts["self-loop-topics"],
        "## Entity Ownership",
        "",
        facts["entity-ownership-table"],
        "## Cross-Service Correlation Suggestions",
        "",
        facts["correlation-table"],
        "## Event Flows (producer → consumers)",
        "",
        facts["event-flow-table"],
        "## Per-component Confidence",
        "",
        facts["_confidence_table"],
    ]
    return "\n".join(lines)
