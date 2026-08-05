#!/usr/bin/env python3
"""Wave 6.5 — feature spec structural validator.
Checks `spec.md` files against verification-checklist.md FeatureSpec rules.
Regex + fence-state tracking; stdlib only.
Exit codes: 0 (no critical), 1 (critical), 2 (internal).
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations
import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import (  # noqa: E402
    assert_under, iter_docs_technical_specs, iter_feature_dirs, iter_technical_specs,
    read_authored_by, read_spec_status, resolve_project_root,
)
from _spec_parse import parse_headings_and_blocks, strip_html_comments  # noqa: E402
from _spec_block_lib import find_blocks_missing_linked_fr  # noqa: E402
from _file_schema_lib import has_populated_file_schema, is_file_exchange  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, merge_validator_result, recalculate_totals,
)
from _spec_constants import REQUIRED_H2_TECH, REQUIRED_H2_BC, REQUIRED_H2_SCR, REQUIRED_CCL_H3  # noqa: E402

VALIDATOR = "feature_spec"
LEGACY_H2 = {"## Related Artifacts", "## Spec Documents"}  # CRITICAL: legacy format no longer accepted
FORBIDDEN_BC_RE = re.compile(
    r"BL\d{3}|SCR\d{3}|REG\d{3}|US\d{3}|ROUTE\d{3}|MODEL\d{3}|PERM\d{3}"
    r"|FR-\d{3}|BR-\d{3}|SM-\d{3}|ALG-\d{3}|INT-\d{3}|SC-\d{3}"
    r"|HTTP \d{3}|\bGET\b|\bPOST\b|\bPUT\b|\bDELETE\b|\bPATCH\b"
)
DEPRECATED_H2 = {"## Requirements", "## Business Rules", "## State Machines", "## Algorithms", "## External Integrations", "## Success Criteria", "## How It Works"}
PLACEHOLDER_RE = re.compile(r"\{[A-Z][A-Z0-9_/|]*\}")
FCODE_HEADING_RE = re.compile(r"^#\s+F\d{3}_[A-Za-z0-9]+")
SCREEN_FLOW_OK_RE = re.compile(r"^\*\*See:\*\*\s+ScreenFlow\s+§\s+F\d{3}_\w+|^N/A —")
SM_BLOCK_RE = re.compile(r"^###\s+SM-\d{3}_")
NUMBERED_STEP_RE = re.compile(r"^\s*\d+\.\s+\S")
DEC_BLOCK_RE = re.compile(r"^####\s+DEC-\d{3}_")
VALID_SUBTYPES = {"render", "interaction", "flow"}
DISC_SUBSECTION_RE = re.compile(r"^### DISC-\d{3}")
BOOLEAN_VALUE_RE = re.compile(r"^\|\s*(true|false|yes|no|1|0)\s*\|", re.IGNORECASE)
_DISC_TABLE_HEADER_RE = re.compile(r"^\|\s*value\b", re.IGNORECASE)
_DISC_TABLE_SEP_RE = re.compile(r"^\|\s*[-:]+\s*\|")

# Lazy-N/A grep patterns — JSX-ternary and framework conditionals
LAZY_NA_PATTERNS = [
    re.compile(r"\{[^}]*\?[^:]*:[^}]*\}"),   # JSX ternary
    re.compile(r"v-if=|v-else=|v-show="),      # Vue conditionals
    re.compile(r"@if\s*\(|@else"),             # Blade
    re.compile(r"<%\s*if\b|<%\s*else\b"),      # ERB
]


def _bounds(h2, name, total):
    for i, (idx, h) in enumerate(h2):
        if h == name:
            return idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else total)
    return None


def _check_dec_blocks(lines: list[str], headings: list, blocks: list, b_ccl: tuple | None) -> list[dict]:
    """Check DEC-### block structural validity within ## Cross-Cutting Logic."""
    issues: list[dict] = []
    if not b_ccl:
        return issues
    ccl_lines = lines[b_ccl[0]:b_ccl[1]]
    ccl_offset = b_ccl[0]

    # Find Decision Logic H3 bounds — use next H3 sibling (not H4 children) as dl_end
    ccl_headings = [(idx, h) for idx, h in headings if b_ccl[0] <= idx < b_ccl[1]]
    ccl_h3 = [(idx, h) for idx, h in ccl_headings if h.startswith("### ")]
    dl_start = dl_end = None
    for i, (idx, h) in enumerate(ccl_h3):
        if h == "### Decision Logic":
            dl_start = idx + 1
            dl_end = ccl_h3[i + 1][0] if i + 1 < len(ccl_h3) else b_ccl[1]
            break

    if dl_start is None:
        return issues  # CCL section check handles missing Decision Logic H3

    dl_content = "\n".join(lines[dl_start:dl_end]).strip()
    if dl_content.startswith("N/A"):
        # Warn: lazy N/A check — look for JSX ternary patterns in spec file (conservative)
        full_text = "\n".join(lines)
        hits = []
        for pat in LAZY_NA_PATTERNS:
            if pat.search(full_text):
                hits.append(pat.pattern)
        if hits:
            issues.append({
                "severity": "warning", "rule_id": "FeatureSpec.dec_lazy_na",
                "location": {"file": None, "line": dl_start + 1},
                "message": f"Decision Logic is N/A but spec contains conditional patterns matching DEC signatures ({hits[:2]}); reviewer should verify"
            })
        return issues

    # Check each DEC-### block
    dec_heads = [(idx, h) for idx, h in headings if DEC_BLOCK_RE.match(h) and dl_start <= idx < dl_end]
    for k, (idx, raw) in enumerate(dec_heads):
        nxt = dec_heads[k + 1][0] if k + 1 < len(dec_heads) else dl_end
        block_lines = lines[idx:nxt]
        block_text = "\n".join(block_lines)

        required_fields = ["**subtype:**", "**Triggers in:**", "**Involved entities:**",
                           "**user_visible_outcome:**", "**Source:**"]
        for field in required_fields:
            if field not in block_text:
                issues.append({
                    "severity": "critical", "rule_id": "FeatureSpec.dec_blocks_well_formed",
                    "location": {"file": None, "line": idx + 1},
                    "message": f"{raw} missing required field {field!r}"
                })

        # Check subtype values
        subtype_match = re.search(r"\*\*subtype:\*\*\s*(.+)", block_text)
        if subtype_match:
            declared = {s.strip() for s in subtype_match.group(1).split(",")}
            invalid = declared - VALID_SUBTYPES
            if invalid:
                issues.append({
                    "severity": "critical", "rule_id": "FeatureSpec.dec_blocks_well_formed",
                    "location": {"file": None, "line": idx + 1},
                    "message": f"{raw} invalid subtype(s): {invalid}; valid: render, interaction, flow"
                })

        # Check pseudocode ≤8 lines
        dec_blocks = [(s, e, l) for s, e, l in blocks if idx <= s < nxt]
        for start, end, lang in dec_blocks:
            if lang != "mermaid" and (end - start - 1) > 8:
                issues.append({
                    "severity": "warning", "rule_id": "FeatureSpec.dec_blocks_well_formed",
                    "location": {"file": None, "line": start + 1},
                    "message": f"{raw} pseudocode block {end - start - 1} lines > 8"
                })

    return issues


def _check_linked_fr(spec: Path, root: Path, lines: list[str]) -> list[dict]:
    """Check every BR/SM/ALG/INT block has **Linked FR:** line (rule: FeatureSpec.linked_fr_missing)."""
    text = "\n".join(lines)
    missing = find_blocks_missing_linked_fr(text)
    issues = []
    for blk in missing:
        try:
            loc = str(spec.relative_to(root))
        except ValueError:
            loc = str(spec)
        issues.append({
            "validator": VALIDATOR,
            "severity": "critical",
            "rule_id": "FeatureSpec.linked_fr_missing",
            "location": {"file": loc, "line": blk["heading_line"] + 1},
            "message": f"{blk['code']} block missing required '**Linked FR:**' line"
        })
    return issues


def _issue(sev, rid, spec, root, line, msg):
    try:
        loc = str(spec.relative_to(root))
    except ValueError:
        loc = str(spec)
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": loc, "line": line}, "message": msg}


_SOURCE_LINE_RE = re.compile(r"^\*\*Source:\*\*\s+`?[^`\n:]+:\d+", re.MULTILINE)
# Canonical `## Source Code References` table-row citation: a Markdown table row whose
# cells contain a backtick-wrapped `path:N` / `path:N-M`. This is the format emitted by
# templates/technical-spec-template.md (| Symbol | Path | Purpose |) and parsed for SHA
# tracking (see references/incremental-state-schema.md). Header/separator rows carry no
# backtick path:line and are correctly ignored.
_SOURCE_TABLE_ROW_RE = re.compile(r"^\s*\|.*`[^`\n:]+:\d+", re.MULTILINE)
_BLOCK_HEADING_RE = re.compile(r"^### (BR|SM|ALG|INT)-\d{3}_")


def _check_technical_spec(spec: Path, root: Path) -> list[dict]:
    # F8: draft relaxes source-evidence rules only; all structural rules stay critical for drafts.
    # Relaxation requires BOTH status: draft AND authored_by: takumi — a draft from any other
    # author is anomalous and gets full strict validation.
    is_draft = read_spec_status(spec) == "draft" and read_authored_by(spec) == "takumi"
    lines = spec.read_text(encoding="utf-8", errors="replace").splitlines()
    headings, blocks = parse_headings_and_blocks(lines)
    scrubbed = strip_html_comments(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    out: list[dict] = []
    add = lambda s, r, ln, m: out.append(_issue(s, r, spec, root, ln, m))  # noqa: E731

    # F### heading check: look in first 5 lines after any leading YAML frontmatter fence.
    preamble_start = 0
    if lines and lines[0].rstrip() == "---":
        # Skip past the closing ---
        for _fi in range(1, min(len(lines), 30)):
            if lines[_fi].rstrip() == "---":
                preamble_start = _fi + 1
                break
    if not any(FCODE_HEADING_RE.match(lines[i]) for i in range(preamble_start, min(preamble_start + 5, len(lines)))):
        add("critical", "FeatureSpec.f_code_format", 1, "missing/invalid F### heading in preamble")

    for idx, raw in headings:
        if raw in DEPRECATED_H2:
            add("critical", "FeatureSpec.deprecated_headings", idx + 1, f"deprecated H2 {raw!r}")
        if raw in LEGACY_H2:
            add("critical", "FeatureSpec.legacy_artifact_sections", idx + 1,
                f"legacy section {raw!r} — replace both '## Related Artifacts' and '## Spec Documents' with single '## Artifact References' table (no transition window)")
        if raw == "## Appendix":
            add("critical", "FeatureSpec.no_appendix", idx + 1, "## Appendix must be removed")

    h2_names = [h for _, h in h2]
    present = [h for h in h2_names if h in REQUIRED_H2_TECH]
    expected = [h for h in REQUIRED_H2_TECH if h in present]
    if present != expected or set(present) != set(REQUIRED_H2_TECH):
        missing = [h for h in REQUIRED_H2_TECH if h not in present]
        add("critical", "FeatureSpec.required_sections", None,
            f"required H2 missing/out-of-order; missing: {missing}" if missing else "required H2 out of order")

    b_ccl = _bounds(h2, "## Cross-Cutting Logic", len(lines))
    if b_ccl:
        h3 = [(idx, h) for idx, h in headings if b_ccl[0] <= idx < b_ccl[1] and h.startswith("### ")]
        names = [h for _, h in h3]
        present_ccl = [h for h in names if h in REQUIRED_CCL_H3]
        if present_ccl != [h for h in REQUIRED_CCL_H3 if h in present_ccl] or set(present_ccl) != set(REQUIRED_CCL_H3):
            add("critical", "FeatureSpec.ccl_subsections", None,
                f"required CCL H3 missing/out-of-order; have {names}")
        for i, (idx, h) in enumerate(h3):
            end = h3[i + 1][0] if i + 1 < len(h3) else b_ccl[1]
            if not "\n".join(lines[idx + 1:end]).strip():
                add("critical", "FeatureSpec.ccl_blank", idx + 1, f"{h} is blank; write `None.` if empty")

    # Client Behavior Anchor — mandatory in ## Cross-Cutting Logic regardless of N/A content
    if b_ccl:
        ccl_text = "\n".join(lines[b_ccl[0]:b_ccl[1]])
        if "**Client behavior:** see" not in ccl_text:
            add("critical", "FeatureSpec.missing_client_behavior_anchor", None,
                "## Cross-Cutting Logic missing required '**Client behavior:** see' anchor block "
                "(links behavior-logic.md, permissions.md, screen-flow.md — mandatory even when all linked sections are N/A)")

    b_sf = _bounds(h2, "## Screen Flow", len(lines))
    if b_sf:
        for i in range(*b_sf):
            s = lines[i].strip()
            if s and not s.startswith("#") and not s.startswith("<!--"):
                if not SCREEN_FLOW_OK_RE.match(s):
                    add("critical", "FeatureSpec.screen_flow_crossref", i + 1,
                        "Screen Flow first content line must start with '**See:** ScreenFlow § F###_…' or 'N/A —'")
                break

    b_bw = _bounds(h2, "## Business Workflow", len(lines))
    if b_bw:
        steps = sum(1 for i in range(*b_bw) if NUMBERED_STEP_RE.match(lines[i]))
        if steps < 3:
            add("critical", "FeatureSpec.bw_steps", None,
                f"## Business Workflow needs ≥3 numbered steps; found {steps}")

    b_us = _bounds(h2, "## User Stories", len(lines))
    if b_us and not any(h == "### Edge Cases"
                        for idx, h in headings if b_us[0] <= idx < b_us[1] and h.startswith("### ")):
        add("critical", "FeatureSpec.edge_cases", None, "### Edge Cases required under ## User Stories")

    fenced = {i for s, e, _ in blocks for i in range(s, e + 1)}
    for i, raw in enumerate(lines):
        if i in fenced or not PLACEHOLDER_RE.search(scrubbed[i]):
            continue
        add("critical", "Universal.no_placeholder", i + 1, f"placeholder literal in line: {raw.strip()[:80]!r}")
        break

    sm_heads = [(idx, raw) for idx, raw in headings if SM_BLOCK_RE.match(raw)]
    for k, (idx, raw) in enumerate(sm_heads):
        nxt = sm_heads[k + 1][0] if k + 1 < len(sm_heads) else len(lines)
        if not any(idx < start < nxt and lang.startswith("mermaid") for start, _e, lang in blocks):
            add("critical", "FeatureSpec.sm_mermaid", idx + 1, f"{raw} block missing stateDiagram-v2 fence")

    # DISC boolean heuristic — warn if DISC subsection only lists true/false values
    b_poly = _bounds(h2, "## Polymorphic Behavior", len(lines))
    if b_poly:
        poly_headings = [(idx, h) for idx, h in headings
                         if b_poly[0] <= idx < b_poly[1] and DISC_SUBSECTION_RE.match(h)]
        for k, (idx, disc_h) in enumerate(poly_headings):
            end = poly_headings[k + 1][0] if k + 1 < len(poly_headings) else b_poly[1]
            disc_lines = lines[idx:end]
            bool_hits = [ln for ln in disc_lines if BOOLEAN_VALUE_RE.match(ln)]
            non_bool_table = [ln for ln in disc_lines if ln.startswith("|") and not BOOLEAN_VALUE_RE.match(ln)
                              and not _DISC_TABLE_HEADER_RE.match(ln) and not _DISC_TABLE_SEP_RE.match(ln)]
            if bool_hits and not non_bool_table:
                add("warning", "FeatureSpec.disc_boolean",
                    idx + 1,
                    f"{disc_h}: DISC subsection appears to document a boolean field (true/false values only); "
                    f"boolean flags belong in Business Rules, not DISC-### — consider removing this DISC entry")

    for start, end, lang in blocks:
        if lines[start].startswith("```{lang}"):
            add("warning", "FeatureSpec.pseudocode_fence", start + 1, "pseudocode fence uses literal {lang}")
        if end - start - 1 > 20 and lang and lang != "mermaid":
            add("warning", "FeatureSpec.pseudocode_length", start + 1,
                f"pseudocode block {end - start - 1} lines > 20")

    # DEC-### structural checks
    for dec_issue in _check_dec_blocks(lines, headings, blocks, b_ccl):
        dec_issue["validator"] = VALIDATOR
        try:
            dec_issue["location"]["file"] = str(spec.relative_to(root))
        except ValueError:
            dec_issue["location"]["file"] = str(spec)
        out.append(dec_issue)

    # Linked FR presence check — every BR/SM/ALG/INT block must declare Linked FR
    out.extend(_check_linked_fr(spec, root, lines))

    # F8: source-evidence checks — critical for implemented, warning for drafts.
    src_ev_sev = "warning" if is_draft else "critical"

    # (a) ## Source Code References body: must have >= 1 citation for implemented specs —
    # either an inline **Source:** path:N-M line OR a canonical table row citing `path:N-M`.
    # Draft specs are allowed to have an empty body (no citations for code not yet written).
    b_src = _bounds(h2, "## Source Code References", len(lines))
    if b_src:
        src_lines = lines[b_src[0]:b_src[1]]
        src_count = sum(
            1 for ln in src_lines
            if _SOURCE_LINE_RE.match(ln) or _SOURCE_TABLE_ROW_RE.match(ln)
        )
        if src_count == 0:
            add(src_ev_sev, "FeatureSpec.source_refs_empty", b_src[0] + 1,
                "## Source Code References body is empty; implemented specs must have at "
                "least one citation — a **Source:** path:N-M line or a table row citing `path:N-M`")

    # (b) BR/SM/ALG/INT blocks: each must have a **Source:** line.
    block_heads = [(idx, raw) for idx, raw in headings if _BLOCK_HEADING_RE.match(raw)]
    fenced_lines = {i for s, e, _ in blocks for i in range(s, e + 1)}
    # Bound each block at the next H1-H3 heading (not only the next block head) so a
    # **Source:** line in a later section (e.g. ## Source Code References) cannot satisfy
    # the LAST block's check.
    boundaries = sorted(i for i, h in headings if re.match(r"^#{1,3} ", h))
    for idx, raw in block_heads:
        if idx in fenced_lines:
            continue
        nxt = next((b for b in boundaries if b > idx), len(lines))
        block_text = "\n".join(lines[idx + 1:nxt])
        if not _SOURCE_LINE_RE.search(block_text):
            add(src_ev_sev, "FeatureSpec.block_source_missing", idx + 1,
                f"{raw} missing required '**Source:** path:N-M' line")

        # ALG-only: file-exchange algorithms must declare a populated **File Schema**
        # table. BR/SM/INT blocks have no such field and are never checked. Warning
        # severity only — does not affect critical count / exit code (see `main()`).
        if raw.startswith("### ALG-"):
            full_block_text = raw + "\n" + block_text
            if is_file_exchange(full_block_text) and not has_populated_file_schema(block_text):
                add("warning", "FeatureSpec.alg_file_schema_missing", idx + 1,
                    f"{raw} matches file-exchange vocabulary but has no populated "
                    f"'**File Schema**' table")

    return out


def _check_business_context(bc_path: Path, root: Path, is_draft: bool = False) -> list[dict]:
    """Validate business-context.md: required H2s + forbidden tokens."""
    issues = []
    if not bc_path.is_file():
        sev = "warning" if is_draft else "critical"
        issues.append(_issue(sev, "bc.missing", bc_path, root, 0, "business-context.md not found"))
        return issues
    text = bc_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    headings, _ = parse_headings_and_blocks(lines)
    h2_set = {h for _, h in headings if h.startswith("## ")}
    for req in REQUIRED_H2_BC:
        if req not in h2_set:
            issues.append(_issue("critical", "bc.missing_h2", bc_path, root, 0, f"missing required section: {req}"))
    # Forbidden tokens — skip fenced code blocks and HTML comments
    clean_lines = strip_html_comments(lines)
    in_fence = False
    for i, line in enumerate(clean_lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = FORBIDDEN_BC_RE.search(line)
        if m:
            issues.append(_issue("critical", "bc.forbidden_token", bc_path, root, i,
                                 f"forbidden token in business-context: {m.group()!r}"))
    return issues


def _check_screens(scr_path: Path, root: Path, is_draft: bool = False) -> list[dict]:
    """Validate screens.md: required H2s."""
    issues = []
    if not scr_path.is_file():
        sev = "warning" if is_draft else "critical"
        issues.append(_issue(sev, "screens.missing", scr_path, root, 0, "screens.md not found"))
        return issues
    lines = scr_path.read_text(encoding="utf-8", errors="replace").splitlines()
    headings, _ = parse_headings_and_blocks(lines)
    h2_set = {h for _, h in headings if h.startswith("## ")}
    for req in REQUIRED_H2_SCR:
        if req not in h2_set:
            issues.append(_issue("critical", "screens.missing_h2", scr_path, root, 0,
                                 f"missing required section: {req}"))
    return issues


def _check_edge_cases(ec_path: Path, root: Path, is_draft: bool = False) -> list[dict]:
    """Validate edge-cases.md: file exists and has a table with rows."""
    issues = []
    if not ec_path.is_file():
        sev = "warning" if is_draft else "critical"
        issues.append(_issue(sev, "edge_cases.missing", ec_path, root, 0, "edge-cases.md not found"))
        return issues
    lines = ec_path.read_text(encoding="utf-8", errors="replace").splitlines()
    table_rows = [
        l for l in lines
        if l.strip().startswith("|")
        and not re.match(r"^\|\s*[-:]+", l)
        and not re.match(r"^\|\s*Scenario", l, re.IGNORECASE)
    ]
    if len(table_rows) < 1:
        issues.append(_issue("warning", "edge_cases.few_rows", ec_path, root, 0,
                             "edge-cases.md has no data rows in table"))
    return issues


def _check_feature_dir(feature_dir: Path, root: Path) -> list[dict]:
    """Run all 4 per-file validators for a feature directory.

    A takumi draft (technical-spec.md carrying BOTH status:draft AND
    authored_by:takumi) may legitimately defer the satellite files — the
    "draft exit 0" contract. We determine draft-ness ONCE from the canonical
    technical-spec.md and thread it into the satellite checks so a missing
    satellite downgrades critical -> warning instead of failing the run. [MED-1]
    """
    tech_spec = feature_dir / "technical-spec.md"
    is_draft = (
        tech_spec.is_file()
        and read_spec_status(tech_spec) == "draft"
        and read_authored_by(tech_spec) == "takumi"
    )
    issues = []
    issues.extend(_check_technical_spec(tech_spec, root))
    issues.extend(_check_business_context(feature_dir / "business-context.md", root, is_draft))
    issues.extend(_check_screens(feature_dir / "screens.md", root, is_draft))
    issues.extend(_check_edge_cases(feature_dir / "edge-cases.md", root, is_draft))
    return issues


_FEATURE_FILE_NAMES = {"technical-spec.md", "business-context.md", "screens.md", "edge-cases.md"}


def validate(plan_dir, root, single, docs_root=None):
    if single is not None:
        if single.is_dir():
            feature_dir = single
            issues = _check_feature_dir(feature_dir, root)
        elif single.name in _FEATURE_FILE_NAMES:
            # Standard 4-file layout: derive feature dir from parent
            feature_dir = single.parent
            issues = _check_feature_dir(feature_dir, root)
        else:
            # Legacy/standalone spec file: validate directly as technical-spec
            feature_dir = single.parent
            issues = _check_technical_spec(single, root)
        try:
            rel = str(feature_dir.relative_to(root))
        except ValueError:
            rel = str(feature_dir)
        per_spec = {feature_dir.name: {"spec_path": rel, "issues": issues}}
    elif docs_root is not None:
        # F1: --docs-root mode — iterate docs/features/*/technical-spec.md
        per_spec = {}
        for spec_path in iter_docs_technical_specs(docs_root):
            # iter_docs_technical_specs already skips .pending dirs
            feature_dir = spec_path.parent
            try:
                rel = str(feature_dir.relative_to(root))
            except ValueError:
                rel = str(feature_dir)
            per_spec[feature_dir.name] = {
                "spec_path": rel,
                "issues": _check_feature_dir(feature_dir, root),
            }
    else:
        per_spec = {}
        for fd in iter_feature_dirs(plan_dir):
            if (fd / ".pending").is_file():
                continue  # W6 still in progress — skip incomplete feature dirs
            try:
                rel = str(fd.relative_to(root))
            except ValueError:
                rel = str(fd)
            per_spec[fd.name] = {"spec_path": rel, "issues": _check_feature_dir(fd, root)}
    return {"validator": VALIDATOR,
            "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "plan_dir": str(plan_dir), "specs": per_spec}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.5 feature-spec validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir"); g.add_argument("--spec"); g.add_argument("--docs-root")
    p.add_argument("--project-root", default=None); p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)
    docs_root_path: Path | None = None
    if args.docs_root:
        # F1: --docs-root <project_root> mode — scan docs/features/*/technical-spec.md
        docs_root_path = Path(args.docs_root).resolve()
        if not docs_root_path.is_dir():
            print(f"[ERROR] --docs-root is not a directory: {docs_root_path}", file=sys.stderr)
            return 2
        plan_dir = docs_root_path; single = None
    elif args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve(); single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr); return 2
    else:
        single = Path(args.spec).resolve()
        # Accept a feature dir or a .md file inside a feature dir
        if single.is_dir():
            # single = artifacts/features/{slug}/ → plan_dir = two levels up
            plan_dir = single.parent.parent
        elif single.is_file():
            # single = artifacts/features/{slug}/some-file.md → plan_dir = three levels up
            plan_dir = single.parent.parent.parent
        else:
            print(f"[ERROR] --spec is not a file: {single}", file=sys.stderr); return 2
    try:
        if args.docs_root:
            assert_under(docs_root_path, root)
        else:
            assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr); return 2
    try:
        result = validate(plan_dir, root, single, docs_root=docs_root_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr); return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    crit = sum(1 for s in result["specs"].values() for i in s["issues"] if i["severity"] == "critical")
    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            merge_validator_result(summary, VALIDATOR, result)
            recalculate_totals(summary); summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr); return 2
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
