"""Deterministic semantic lint for the --api-doc derive pipeline (Phase B1).

A pure-Python HARD GATE that turns silent corruption into loud failure. Runs in the driver AFTER
extract, BEFORE build/SEAL. The format verifier (verify_format.py) proves the workbook is STYLE-
perfect; this proves the CONTENT is structurally faithful to the source. Together: SEALED = format
+ semantic. 7 checks (L1-L7), each guarding a known defect class fixed in Phase A.

Reads the deterministic intermediates (NOT the xlsx): openapi.yaml + api-content.json + route-list.md
(ground truth for coverage). Mirrors verify_format.py conventions: positional args, main()->int,
sys.exit(main()); driver's run() aborts the pass on non-zero.

Usage:
  python verify_semantics.py OPENAPI.yaml API_CONTENT.json [--route-list route-list.md]
"""
import os
import re
import sys
import json
import argparse
try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML is required — install with `pip install pyyaml`, "
             "or run via the kit venv: .claude/skills/.venv/bin/python3")
from artifacts2openapi import is_infra, parse_route_list, _query_tokens_from_purpose
from extract_api_content import norm_path

# header tokens that are NEVER a legitimate field name (A2 guard). Deliberately excludes
# "type"/"name"/"key"/"notes" — those ARE real param names (e.g. the ad `type` query param).
HEADER_TOKENS = {"param", "field", "type name", "parameter"}
# substrings that mark a category as the leaked route-list `### File: ...` heading (A5 guard)
FILE_EXTS = (".kt", ".swift", ".py", ".ts", ".java", ".go", ".rb")


def _ops(doc):
    """Yield (METHOD, raw_path, norm, op) for every operation in an OpenAPI doc."""
    for path, methods in (doc.get("paths") or {}).items():
        for m, op in (methods or {}).items():
            if m.lower() in ("get", "post", "put", "patch", "delete"):
                yield m.upper(), path, norm_path(path), op


def _body_props(op):
    rb = op.get("requestBody") or {}
    for mv in (rb.get("content") or {}).values():
        return list(((mv.get("schema") or {}).get("properties") or {}).keys())
    return []


def _query_names(op):
    return [p.get("name", "") for p in (op.get("parameters") or []) if p.get("in") == "query"]


def l1_no_backtick_key(doc, content):
    bad = [c["key"] for rec in content for c in rec.get("params", []) if "`" in c.get("key", "")]
    bad += [k for _, _, _, op in _ops(doc) for k in _body_props(op) + _query_names(op) if "`" in k]
    return (not bad, "clean" if not bad else f"backtick in keys: {bad[:6]}")


def l2_no_header_field(doc, content):
    bad = [c["key"] for rec in content for c in rec.get("params", [])
           if c.get("key", "").strip().lower() in HEADER_TOKENS]
    bad += [k for _, _, _, op in _ops(doc) for k in _body_props(op)
            if k.strip().lower() in HEADER_TOKENS]
    return (not bad, "clean" if not bad else f"header-row leaked as field: {bad[:6]}")


def l3_get_no_body(doc):
    bad = [f"{m} {p}" for m, p, _, op in _ops(doc) if m in ("GET", "DELETE") and op.get("requestBody")]
    return (not bad, "clean" if not bad else f"GET/DELETE with requestBody: {bad[:6]}")


def l4_authed_has_4xx(doc, auth_by_key):
    bad = []
    for m, p, nz, op in _ops(doc):
        auth = (auth_by_key.get((m, nz)) or "").lower()
        authed = "bearer" in auth and "none" not in auth          # NONE-auth rows exempt (A4 decision)
        if authed and not any(str(c).startswith("4") for c in (op.get("responses") or {})):
            bad.append(f"{m} {p}")
    return (not bad, "clean" if not bad else f"Bearer endpoints missing 4xx: {bad[:6]}")


def l5_query_classified(doc, purpose_by_key):
    bad = []
    for m, p, nz, op in _ops(doc):
        path_names = set(re.findall(r"\{(\w+)\}", p))
        qnames, bprops = set(_query_names(op)), set(_body_props(op))
        for tok in _query_tokens_from_purpose(purpose_by_key.get((m, nz), "")):
            if tok in path_names:
                continue
            if tok in bprops:
                bad.append(f"{m} {p}:{tok} in body (should be query)")
            elif tok not in qnames:
                bad.append(f"{m} {p}:{tok} unclassified (should be query)")
    return (not bad, "clean" if not bad else "; ".join(bad[:6]))


def l6_coverage(doc, route_list_text):
    if not route_list_text:
        return (True, "skipped — no route-list.md (swagger-sourced project)")
    api_rows, _ = parse_route_list(route_list_text)
    have = {(m, nz) for m, _, nz, _ in _ops(doc)}
    missing = [f"{r['method']} {r['path']}" for r in api_rows
               if not is_infra(r["path"], r["handler"]) and (r["method"], norm_path(r["path"])) not in have]
    return (not missing, f"{len(have)} ops cover all route-list endpoints"
            if not missing else f"dropped endpoints: {missing[:6]}")


def l7_category_not_file(doc, content):
    cats = {t for _, _, _, op in _ops(doc) for t in (op.get("tags") or [])}
    cats |= {rec.get("category", "") for rec in content}
    bad = [c for c in cats if c.startswith("File:") or "`" in c
           or any(ext in c.lower() for ext in FILE_EXTS)]
    return (not bad, "clean" if not bad else f"file-path leaked as category: {bad[:4]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("openapi")
    ap.add_argument("api_content")
    ap.add_argument("--route-list")
    args = ap.parse_args()

    with open(args.openapi, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    content = json.load(open(args.api_content, encoding="utf-8")) if os.path.exists(args.api_content) else []
    rl_text = ""
    if args.route_list and os.path.exists(args.route_list):
        with open(args.route_list, encoding="utf-8") as f:
            rl_text = f.read()
    auth_by_key, purpose_by_key = {}, {}
    if rl_text:
        rows, _ = parse_route_list(rl_text)
        for r in rows:
            auth_by_key[(r["method"], norm_path(r["path"]))] = r.get("auth", "")
            purpose_by_key[(r["method"], norm_path(r["path"]))] = r.get("handler", "")

    checks = [
        ("L1 no-backtick-key", l1_no_backtick_key(doc, content)),
        ("L2 no-header-field", l2_no_header_field(doc, content)),
        ("L3 GET-no-body", l3_get_no_body(doc)),
        ("L4 authed-has-4xx", l4_authed_has_4xx(doc, auth_by_key)),
        ("L5 query-classified", l5_query_classified(doc, purpose_by_key)),
        ("L6 coverage-no-drops", l6_coverage(doc, rl_text)),
        ("L7 category-not-file", l7_category_not_file(doc, content)),
    ]
    print("=== SEMANTIC LINT ===")
    failed = []
    for name, (ok, detail) in checks:
        print(f"  {'✓' if ok else '✗'} {name} — {detail}")
        if not ok:
            failed.append(name)
    if failed:
        print(f"=== SEMANTIC LINT FAILED: {len(failed)} check(s) — {', '.join(failed)} ===")
        return 2
    print("=== SEMANTIC LINT PASSED — 7/7 checks ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
