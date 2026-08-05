#!/usr/bin/env python3
"""A1 confidence-report derivation — deterministic, no LLM, no source re-read.

Parses ONE already-promoted artifact's own inline `**Source:** file:line` citations
(-> status o, cited) and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker
tags (-> status /\\, uncertain) to emit a companion `confidence-report_<stem>.md` beside it.

F4 boundary: this is a self-reported citation-COVERAGE stat, not a correctness verifier.
See references/confidence-report-contract.md. The shipped `claude/skills/audit-doc-parity/`
is the blind truth-verification tool.

Sidecar contract (Q2 precedent = .nav-metadata.json): always-regenerate, never asserted,
never added to FEATURE_FILES / check_promotion_gate.py / .rebuild-state.json. Best-effort:
any I/O or parse error is swallowed -- this script always exits 0, it must never fail a pass.

Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, strip_disclaimer_blocks  # noqa: E402

CITATION_RE = re.compile(r"\*\*Source:\*\*\s+`?([^`\n:]+):(\d+)(?:-(\d+))?`?")
MARKER_RE = re.compile(r"\[(UNVERIFIED|INFERRED|NEEDS_DOMAIN_CONFIRMATION)\]")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
# `{...}` spans are unfilled template placeholders (scaffold drafts, WARN-*.unmapped rows) --
# their content is instructions, not claims; strip before scanning so a literal marker token
# inside guidance text never inflates claims_total.
PLACEHOLDER_RE = re.compile(r"\{[^{}\n]*\}")
DISCLAIMER = (
    "> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is "
    "derived deterministically by parsing the artifact's own inline `**Source:** file:line` "
    "citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does "
    "NOT verify that citations are accurate or that claims are true. For blind truth verification, "
    "see `claude/skills/audit-doc-parity/`."
)
# --limitation-note synthesis (Decision 3 / Validation Session 1): aggregate/system-synthesis
# artifacts carry sparse, non-standard citations -- this extra header line stops the coverage
# stat from being misread as a quality score on those artifacts. See confidence-report-contract.md.
LIMITATION_NOTES = {
    "synthesis": (
        "> **Synthesis artifact -- coverage stat reflects citation density, which is "
        "structurally lower here; do not compare against per-feature scores.**"
    ),
}


def _claim_text(line: str, span: tuple[int, int], max_len: int = 100) -> str:
    """Line with the matched token removed, collapsed/truncated into a short claim label."""
    text = (line[: span[0]] + line[span[1]:]).strip()
    text = text.lstrip("-*|").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text or "(unlabeled claim)"


def _escape_cell(s: str) -> str:
    """Markdown table cells cannot contain raw pipes or newlines."""
    return s.replace("|", "\\|").replace("\n", " ").strip()


def extract_claims(text: str) -> list[dict]:
    """Walk the artifact per-line (skipping fenced code + the disclaimer banner), tagging
    each citation/marker hit.

    Minor fix (PR #176 phase-01): the disclaimer banner (`<!-- disclaimer:start/end -->`,
    e.g. design-intent.md's EXPERIMENTAL notice) is stripped before scanning — its own
    `[INFERRED]` marker tokens are boilerplate, not claims, and previously inflated
    `claims_total` by 2 on every design-intent artifact. Fence tracking now goes through
    the shared `iter_lines_with_fence` (adds `~~~` support alongside the prior ``` -only
    loop).
    """
    text = strip_disclaimer_blocks(text)
    claims: list[dict] = []
    section = "Preamble"
    for _, line, in_fence in iter_lines_with_fence(text):
        if in_fence:
            continue
        h2 = H2_RE.match(line)
        if h2:
            section = h2.group(1).strip()
            continue
        line = PLACEHOLDER_RE.sub("", line)
        for m in CITATION_RE.finditer(line):
            path, start, end = m.group(1).strip(), m.group(2), m.group(3)
            evidence = f"{path}:{start}-{end}" if end else f"{path}:{start}"
            claims.append({
                "section": section, "claim": _claim_text(line, m.span()),
                "evidence": evidence, "status": "○",
            })
        for m in MARKER_RE.finditer(line):
            claims.append({
                "section": section, "claim": _claim_text(line, m.span()),
                "evidence": "—", "status": "△",
            })
    return claims


def compute_stats(claims: list[dict]) -> tuple[int, int, float | None]:
    total = len(claims)
    with_evidence = sum(1 for c in claims if c["status"] == "○")
    confidence_derived = round(with_evidence / total, 4) if total else None
    return total, with_evidence, confidence_derived


def render_companion(artifact_rel: str, claims: list[dict], total: int, with_evidence: int,
                      confidence_derived: float | None, limitation_note: str | None = None) -> str:
    cd_val = confidence_derived if confidence_derived is not None else "null"
    lines = [
        "---",
        f"source_artifact: {artifact_rel}",
        f"claims_total: {total}",
        f"claims_with_evidence: {with_evidence}",
        f"confidence_derived: {cd_val}",
        "generated_by: derive_confidence_report.py",
        "---",
        "",
        f"# Confidence Report -- {artifact_rel}",
        "",
        DISCLAIMER,
    ]
    if limitation_note and limitation_note in LIMITATION_NOTES:
        lines += ["", LIMITATION_NOTES[limitation_note]]
    lines += [
        "",
        "## Claims ↔ Evidence",
        "",
        "Legend: `○` = cited (Source file:line present) · `△` = marker-tagged "
        "(uncertain, no citation).",
        "",
        "| Claim | Section | Evidence (file:line) | Status ○/△ |",
        "|---|---|---|---|",
    ]
    if not claims:
        lines.append("| _(none detected -- no `**Source:**` citations or marker tags found)_ | — | — | — |")
    else:
        for c in claims:
            lines.append(
                f"| {_escape_cell(c['claim'])} | {_escape_cell(c['section'])} | "
                f"{_escape_cell(c['evidence'])} | {c['status']} |"
            )
    lines += ["", "## Missing Info", "",
              "Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, "
              "not authoritative:", ""]
    triangles = [c for c in claims if c["status"] == "△"]
    if triangles:
        lines += [f"- {_escape_cell(c['section'])}: {_escape_cell(c['claim'])}" for c in triangles]
    else:
        lines.append("_(none -- no marker-tagged claims)_")
    lines += ["", "## Risk Flags", ""]
    if total == 0:
        lines.append("- No detectable claims (no citations or marker tags) -- coverage stat is not "
                      "meaningful for this artifact.")
    elif confidence_derived is not None and confidence_derived < 0.5:
        lines.append(f"- Low citation coverage ({confidence_derived:.0%}) -- most claims are "
                      "marker-tagged, not cited.")
    else:
        lines.append("_(none)_")
    return "\n".join(lines) + "\n"


def derive(artifact: Path, project_root: Path | None = None, limitation_note: str | None = None) -> Path:
    """Parse `artifact` and write its companion beside it. Returns the companion path."""
    text = artifact.read_text(encoding="utf-8", errors="replace")
    claims = extract_claims(text)
    total, with_evidence, confidence_derived = compute_stats(claims)
    try:
        rel = str(artifact.relative_to(project_root)) if project_root else artifact.name
    except ValueError:
        rel = artifact.name
    content = render_companion(rel, claims, total, with_evidence, confidence_derived, limitation_note)
    out_path = artifact.parent / f"confidence-report_{artifact.stem}.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="A1 deterministic confidence-report derivation")
    p.add_argument("--artifact", required=True, help="Path to ONE promoted artifact")
    p.add_argument("--project-root", default=None, help="Used only to relativize source_artifact")
    p.add_argument("--limitation-note", default=None, choices=sorted(LIMITATION_NOTES),
                    help="Inject an extra header caveat line (e.g. 'synthesis' for aggregate artifacts)")
    args = p.parse_args(argv)

    artifact = Path(args.artifact)
    project_root = Path(args.project_root).resolve() if args.project_root else None
    if not artifact.is_file():
        # Best-effort: caller may pass an artifact that a profile-conditional pass never produced.
        print(f"[WARN] derive_confidence_report: artifact not found, skipping: {artifact}", file=sys.stderr)
        return 0
    try:
        out_path = derive(artifact.resolve(), project_root, args.limitation_note)
        print(f"[OK] confidence report written: {out_path}")
    except Exception as exc:  # noqa: BLE001 -- best-effort sidecar, must never fail the pass
        print(f"[WARN] derive_confidence_report: skipping ({exc})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
