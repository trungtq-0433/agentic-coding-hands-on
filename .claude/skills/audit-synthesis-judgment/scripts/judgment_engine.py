#!/usr/bin/env python3
"""Engine 3 — adversarial judgment residue (WARN-only).

The genuinely-subjective residue neither deterministic coverage nor IPE conformance can settle:
inference validity ("why"/"so that"), boundary naming, granularity, and "restates w/o added why".
Judged by LLM subagents whose findings must survive a refutation pass. This Python plumbs the
deterministic scaffolding around those LLM judges, in two modes:

  prepare  — extract judge CANDIDATES from the artifacts, each pinned to a computed anchor, plus the
             deterministic granularity-outlier stat. Emits candidates JSON. (No LLM; testable.)
  assemble — read the judged candidates back (verdicts + refutations from the LLM judges) → apply the
             anchor gate + refutation-survival + completion accounting → Engine-3 findings JSON.

The LLM orchestrator (see references/pipeline.md + judgment-rubric.md) runs the judges/refuters
BETWEEN prepare and assemble. Engine 3 emits WARN only — NEVER FAIL, NEVER an Engine-1 count.
design-intent candidates are WARN-capped + flagged experimental.

Stdlib only. Exit 0 always.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import read_text_safe, resolve_docs_root, resolve_project_root  # noqa: E402
import _granularity_lib as gran  # noqa: E402
import _ipe_parse_lib as ipe_parse  # noqa: E402
import locate_synthesis_artifacts as locator  # noqa: E402

_INFERRED_RE = re.compile(r"\[INFERRED\]")
# Blast-radius keywords: a WARN touching one of these domains is high-severity (verdict-taxonomy.md).
_BLAST_RADIUS_RE = re.compile(
    r"\b(auth|authz|authn|permission|role|rbac|acl|login|password|token|secret|"
    r"payment|money|price|billing|invoice|charge|refund|"
    r"delete|drop|purge|mutation|persist|encrypt|security)\b", re.I)


def _severity(dimension: str, text: str, experimental: bool) -> str:
    """Blast radius, not taste. High only when the WARN touches an auth/data/security/money domain."""
    if _BLAST_RADIUS_RE.search(text or ""):
        return "high"
    if dimension in ("inference-validity", "granularity"):
        return "medium"
    return "low"
_SO_THAT_RE = re.compile(r"so that\s+(.+?)(?:\.|$)", re.I)
_CITATION_HINT_RE = re.compile(r"\*\*Source:\*\*|ADR-\d+")


# ---------------------------------------------------------------- prepare
def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _extract_inference_candidates(artifacts: list[dict]) -> list[dict]:
    cands: list[dict] = []
    idx = 0
    for art in artifacts:
        if not art.get("present") or not art.get("path"):
            continue
        kind = art["kind"]
        if kind not in ("design-intent", "user-stories"):
            continue
        read = read_text_safe(Path(art["path"]))
        if read is None:
            continue
        text, _ = read
        experimental = (kind == "design-intent")
        if kind == "design-intent":
            for line in text.splitlines():
                if _INFERRED_RE.search(line) and len(line.strip()) > 20:
                    cands.append({
                        "id": f"inference-{idx}", "dimension": "inference-validity",
                        "target": kind, "text": line.strip(),
                        "anchor": "tagged [INFERRED] — judge whether the inferential leap has a traceable warrant",
                        "experimental": experimental})
                    idx += 1
        for m in _SO_THAT_RE.finditer(text):
            benefit = m.group(1).strip()
            if len(benefit) > 8:
                cands.append({
                    "id": f"inference-{idx}", "dimension": "inference-validity",
                    "target": kind, "text": f"so that {benefit}",
                    "anchor": "US benefit clause — judge whether the claimed benefit is traceable to evidence",
                    "experimental": False})
                idx += 1
    return cands


def _extract_restatement_candidates(artifacts: list[dict]) -> list[dict]:
    cands: list[dict] = []
    idx = 0
    for art in artifacts:
        if art.get("kind") != "design-intent" or not art.get("present") or not art.get("path"):
            continue
        read = read_text_safe(Path(art["path"]))
        if read is None:
            continue
        text, _ = read
        for para in _paragraphs(text):
            if para.startswith("#") or len(para) < 120:
                continue
            if _CITATION_HINT_RE.search(para):
                continue  # citation-adjacent (mandated ADR quote / DRY-cite) — exempt [FM-F4]
            if _INFERRED_RE.search(para):
                continue  # already an inference candidate
            cands.append({
                "id": f"restates-{idx}", "dimension": "restates-w/o-why",
                "target": "design-intent", "text": para[:280],
                "anchor": "design-intent Non-Duplication boundary — judge whether this restates "
                          "business-rules/architecture with no added 'why' (citation-adjacent spans exempt)",
                "experimental": True})
            idx += 1
    return cands


def _extract_naming_candidates(artifacts: list[dict]) -> list[dict]:
    cands: list[dict] = []
    for art in artifacts:
        if art.get("kind") != "user-stories" or not art.get("present") or not art.get("path"):
            continue
        read = read_text_safe(Path(art["path"]))
        if read is None:
            continue
        parsed = ipe_parse.parse(read[0])
        for code, title in sorted(parsed.us_titles.items()):
            cands.append({
                "id": f"naming-{code}", "dimension": "naming", "target": code, "text": title,
                "anchor": "IPE Step-4 anti-CRUD — judge only genuinely-ambiguous titles "
                          "(clear violations already deterministic in Engine 2)",
                "experimental": False})
    return cands


def _feature_metrics(docs_root: Path) -> dict[str, float]:
    """Per-feature cited-symbol span proxy: count of **Source:** citations in each technical-spec.md."""
    metrics: dict[str, float] = {}
    feat_dir = docs_root / "features"
    if not feat_dir.is_dir():
        return metrics
    for spec in sorted(feat_dir.glob("*/technical-spec.md")):
        read = read_text_safe(spec)
        if read is None:
            continue
        metrics[spec.parent.name] = float(len(re.findall(r"\*\*Source:\*\*", read[0])))
    return metrics


def _extract_granularity_candidates(docs_root: Path) -> list[dict]:
    metrics = _feature_metrics(docs_root)
    if len(metrics) < 3:
        return []
    stat = gran.find_outliers(metrics)
    return [{
        "id": f"granularity-{o['feature']}", "dimension": "granularity", "target": o["feature"],
        "text": f"{o['feature']} is a {o['direction']} outlier ({o['value']} vs median {stat['median']})",
        "anchor": o["anchor"], "experimental": False,
    } for o in stat["outliers"]]


def prepare(project_root: Path, scope: str, docs_root_override: str | None, plan_dir: str | None) -> dict:
    docs_root = (Path(docs_root_override).resolve() if docs_root_override
                 else resolve_docs_root(project_root))
    loc = locator.locate(project_root, scope, docs_root_override, plan_dir)
    artifacts = loc["artifacts"]
    candidates = (_extract_inference_candidates(artifacts)
                  + _extract_restatement_candidates(artifacts)
                  + _extract_naming_candidates(artifacts)
                  + _extract_granularity_candidates(docs_root))
    return {"engine": "judgment", "mode": "prepare", "expected_count": len(candidates),
            "candidates": candidates}


# ---------------------------------------------------------------- assemble
def _survived_refutation(cand: dict, level: str) -> bool:
    refs = cand.get("refutations", [])
    if not refs:
        return False
    not_refuted = sum(1 for r in refs if not r.get("refuted", True))
    if level == "low":
        return not_refuted >= 1  # single-pass at --level low
    # medium/high/max: ≥2-refuter majority must say NOT refuted
    return len(refs) >= 2 and not_refuted > (len(refs) / 2)


def assemble(judged: dict, level: str) -> dict:
    candidates = judged.get("candidates", [])
    expected = judged.get("expected_count", len(candidates))
    findings: list[dict] = []
    dropped: list[dict] = []
    returned = 0

    for cand in candidates:
        verdict = cand.get("verdict")
        if verdict is None:
            continue  # judge never returned this one (dead subagent) — counts toward PARTIAL
        returned += 1
        if verdict != "WARN":
            continue
        anchor = cand.get("anchor", "")
        if not anchor:
            dropped.append({"id": cand.get("id"), "reason": "no computed anchor (Iron Law #2)"})
            continue
        confidence = cand.get("confidence", 1.0)
        if confidence < 0.5:
            dropped.append({"id": cand.get("id"), "reason": f"confidence {confidence} < 0.5 floor → UNVERIFIABLE"})
            continue
        if not _survived_refutation(cand, level):
            dropped.append({"id": cand.get("id"), "reason": "did not survive refutation pass"})
            continue
        findings.append({
            "engine": "judgment", "kind": _KIND_BY_DIM.get(cand["dimension"], "UNSUPPORTED"),
            "dimension": cand["dimension"], "target": cand.get("target"),
            "severity": _severity(cand["dimension"], cand.get("text", ""), bool(cand.get("experimental"))),
            "verdict": "WARN", "adjudicated": True, "anchor": anchor,
            "evidence": cand.get("text", ""), "experimental": bool(cand.get("experimental")),
            "confidence": confidence,
        })

    if returned == 0 and expected > 0:
        status = "FAILED"
    elif returned < expected:
        status = "PARTIAL"
    else:
        status = "OK"

    return {"engine": "judgment", "judgment_status": status, "level": level,
            "expected": expected, "returned": returned,
            "findings": findings, "dropped": dropped}


_KIND_BY_DIM = {
    "inference-validity": "UNSUPPORTED",
    "restates-w/o-why": "RESTATES",
    "naming": "NAMING",
    "granularity": "GRANULARITY",
}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Engine 3 — adversarial judgment residue (WARN-only)")
    p.add_argument("mode", choices=["prepare", "assemble"])
    p.add_argument("--project-root", default=None)
    p.add_argument("--docs-root", default=None)
    p.add_argument("--scope", default="all",
                   choices=["feature-list", "user-stories", "design-intent", "system", "all"])
    p.add_argument("--plan-dir", default=None)
    p.add_argument("--judged", default=None, help="assemble: path to judged-candidates JSON")
    p.add_argument("--level", default="medium", choices=["low", "medium", "high", "max"])
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)

    if args.mode == "prepare":
        project_root = resolve_project_root(args.project_root)
        result = prepare(project_root, args.scope, args.docs_root, args.plan_dir)
    else:
        if not args.judged or not Path(args.judged).is_file():
            print("[ERROR] assemble requires --judged <file>", file=sys.stderr)
            return 2
        judged = json.loads(Path(args.judged).read_text(encoding="utf-8"))
        result = assemble(judged, args.level)

    payload = json.dumps(result, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(out)
        print(f"[judgment_engine] wrote → {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
