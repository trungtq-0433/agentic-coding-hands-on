"""Synthesize a minimal OpenAPI 3.0 spec from rebuild-spec artifacts (project-agnostic).

Used by the --api-doc pass when a project has NO swagger/openapi file. route-list.md is the
required source (method + path — agnostic across every stack rebuild-spec supports); api-map.md
and api-contracts.md enrich categories and request/response detail when present.

Output: a valid OpenAPI 3.0 YAML (paths + operations + path params + responses) that the existing
extract_api_content.py consumes UNCHANGED — so the whole downstream pipeline (incl. the A1/A2
fixes) is reused with zero duplication.

Infra / non-API routes (health, sidekiq, api-docs, mounted Rack engines) are filtered out and
REPORTED (never silently dropped). Deterministic: exactly one operation per kept API route row.

Usage:
  python artifacts2openapi.py --project-root DIR [--out openapi.yaml]
      [--route-list PATH] [--api-map PATH] [--api-contracts PATH]
"""
from __future__ import annotations

import os
import re
import sys
import argparse
try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML is required — install with `pip install pyyaml`, "
             "or run via the kit venv: .claude/skills/.venv/bin/python3")
from extract_api_content import load_apimap, norm_path

HTTP = ("GET", "POST", "PUT", "PATCH", "DELETE")
# substrings that mark a route as infra / non-API → excluded from the client API design doc
INFRA = ("/sidekiq", "api-docs", "healthcheck", "rails/health", "rswag", "::engine", "::web")


def is_infra(path, handler):
    # Denylist only (incl. ::engine/::web mounts). NOT "no '#' in handler" — that is Rails-specific
    # and would misclassify Express/FastAPI/Go function-name handlers; better keep a route than drop it.
    return any(s in f"{path} {handler}".lower() for s in INFRA)


def to_openapi_path(path):
    """`/api/v1/dashboards/:id` → `/api/v1/dashboards/{id}` (Rails/Express style → OpenAPI)."""
    return re.sub(r":(\w+)", r"{\1}", path)


def parse_route_list(text):
    """Return (api_rows, infra_rows). Each api_row = {method, path, handler, category}.

    Combined methods (`PATCH/PUT`) collapse to the first HTTP verb so coverage stays 1:1 with rows.
    """
    api_rows, infra_rows, category = [], [], None
    for line in text.splitlines():
        h = re.match(r"^#{2,4}\s+(.*)", line.strip())
        if h:
            category = re.sub(r"\s*\(.*?\)\s*$", "", h.group(1)).strip()   # drop "(Viewer)" etc.
            continue
        # path cell may be wrapped in backticks (rebuild-spec route-list emits `/path`); tolerate them
        m = re.match(r"^\|\s*([A-Za-z/]+)\s*\|\s*`?\s*(/[^|`]*?)\s*`?\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|", line)
        if not m:
            continue
        methods = [v for v in m.group(1).split("/") if v.upper() in HTTP]
        if not methods:                       # header row ("Method") or non-verb
            continue
        path, handler = m.group(2).strip(), m.group(3).strip().strip("`")
        row = {"method": methods[0].upper(), "path": path, "handler": handler,
               "category": category or "API", "auth": m.group(4).strip()}
        (infra_rows if is_infra(path, handler) else api_rows).append(row)
    return api_rows, infra_rows


# param-table header tokens — these are header rows, never real fields (A2 skip)
_HEADER_NAMES = {"field", "param", "key", "name", "parameter", "type name"}
_ROW_RE = r"^\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$"


def _contract_region(blk, label_re):
    """Text of one `- **Request — <label>:**` region: from the marker to the next bullet/heading.
    Returns '' when the marker is absent (so a missing Body or Path/Query section just yields [])."""
    m = re.search(label_re, blk)
    if not m:
        return ""
    rest = blk[m.end():]
    stop = re.search(r"\n\s*-\s*\*\*|\n#{2,4}\s", rest)   # next bullet (**Response/**Errors/...) or heading
    return rest[:stop.start()] if stop else rest


def _parse_param_rows(seg):
    """Parse a markdown param table → [{name, type, required, constraint}].
    A1: strip backtick-wrapped field names. A2: skip header + separator rows."""
    rows = []
    for r in re.finditer(_ROW_RE, seg, re.M):
        name = r.group(1).strip().strip("`").strip()
        typ = r.group(2).strip()
        req = r.group(3).strip().lower()
        if (not name or name.lower() in _HEADER_NAMES
                or typ.lower() in ("type", "data type") or set(name) <= set("-")):
            continue
        rows.append({"name": name, "type": typ.lower(),
                     "required": req.startswith("y"), "constraint": r.group(4).strip()})
    return rows


def parse_api_contracts(text):
    """Optional enrichment. Key = (METHOD, normalized-path) → {body, query, responses}.

    A3: splits the `**Request — Body:**` and `**Request — Path/Query:**` tables so body fields
    become a requestBody and query fields become `in:query` params downstream. Tolerant of the
    api-contracts template format; returns {} if the file is absent/unparseable.
    """
    if not text:
        return {}
    out, blocks = {}, re.split(r"^###\s+", text, flags=re.M)
    head = re.compile(r".*?---\s+([A-Z/]+)\s+(\S+)\s+---")
    for blk in blocks:
        hm = head.match(blk)
        if not hm:
            continue
        method = hm.group(1).split("/")[0].upper()
        key = (method, norm_path(hm.group(2)))
        body = _parse_param_rows(_contract_region(blk, r"\*\*Request\s*[—–-]\s*Body:\*\*"))
        query = _parse_param_rows(_contract_region(blk, r"\*\*Request\s*[—–-]\s*Path/Query:\*\*"))
        responses = sorted({rs.group(1) for rs in re.finditer(r"\*\*Response\s+(\d{3})", blk)})
        out[key] = {"body": body, "query": query, "responses": responses}
    return out


OA_TYPES = {"integer": "integer", "int": "integer", "number": "number", "float": "number",
            "boolean": "boolean", "bool": "boolean", "array": "array", "string": "string"}


def oa_type(t):
    t = (t or "string").lower()
    for k, v in OA_TYPES.items():
        if k in t:
            return v
    return "string"


def oa_schema(t):
    """Free-text contract type → OpenAPI schema. Detects arrays FIRST (`Array<Float>`, `List<x>`,
    `x[]`) before scalar element types — else `oa_type` matches `float` inside `Array<Float>` and
    wrongly collapses the array to a scalar. Emits `items` so extract's array-handling preserves it."""
    tl = (t or "string").lower()
    if "array" in tl or "list" in tl or tl.strip().endswith("[]"):
        # element type follows array/list after any of space, backslash, < ( [ (api-contracts uses `Array\<Float\>`)
        m = re.search(r"(?:array|list)[\s\\<(\[]*([a-z]+)", tl)
        return {"type": "array", "items": {"type": oa_type(m.group(1) if m else "string")}}
    return {"type": oa_type(t)}


def inferred_error_codes(row):
    """Inferred 4xx codes from the route-list Auth column (NOT source-documented): 401 when the
    route is authenticated; +403 when it also names an authorization gate (permission/policy/
    role/admin). Empty for public / none-auth rows. Callers MUST label these inferred in the
    response description (audience includes the client deliverable)."""
    auth = (row.get("auth") or "").lower()
    authed = (any(k in auth for k in ("auth", "jwt", "token", "bearer"))
              and "public" not in auth and "none" not in auth)
    if not authed:
        return []
    codes = ["401"]
    if any(k in auth for k in ("permission", "policy", "role", "admin")):
        codes.append("403")
    return codes


def _query_tokens_from_purpose(text):
    """Fallback (A3): pull `?a=&b=` query names from a route-list Purpose string when the contract
    has no Path/Query table. Conservative — literal `?...` token only, never inferred."""
    m = re.search(r"\?([A-Za-z0-9_=&]+)", text or "")
    if not m:
        return []
    return [t.split("=")[0] for t in m.group(1).split("&") if t.split("=")[0]]


def _op_description(row):
    """A6: op description = route purpose + a security note when the Auth column flags no-auth /
    divergence (quoted from route-list §Security Flag, not invented)."""
    purpose = (row.get("handler") or "").strip()
    auth = row.get("auth") or ""
    note = ""
    if "none" in auth.lower() or "⚠" in auth:
        note = (" ⚠️ Security: auth divergence — iOS=NONE / Android=Bearer; biometric data "
                "submitted unauthenticated on iOS. Needs security sign-off.")
    return (purpose + note).strip()


def build_openapi(api_rows, contracts, system_name):
    paths = {}
    for row in api_rows:
        oapath = to_openapi_path(row["path"])
        method = row["method"]
        path_names = re.findall(r"\{(\w+)\}", oapath)
        params = [{"name": p, "in": "path", "required": True, "schema": {"type": "string"}}
                  for p in path_names]
        enrich = contracts.get((method, norm_path(row["path"])), {})
        # A3: query params from the contract Path/Query table, else literal ?a=&b= from the purpose
        query_fields = enrich.get("query") or [
            {"name": q, "type": "string", "required": False, "constraint": ""}
            for q in _query_tokens_from_purpose(row.get("handler", ""))]
        for q in query_fields:
            if q["name"] in path_names:           # already a path param — don't double-list
                continue
            params.append({"name": q["name"], "in": "query", "required": bool(q.get("required")),
                           "schema": oa_schema(q.get("type")),
                           "description": q.get("constraint", "")})
        op = {"summary": re.sub(r"^api/v1/", "", row["handler"]),
              "tags": [row["category"]], "parameters": params}
        desc = _op_description(row)               # A6
        if desc:
            op["description"] = desc
        # A3: only methods that carry a body get one — never GET/DELETE
        if method not in ("GET", "DELETE") and enrich.get("body"):
            props = {b["name"]: {**oa_schema(b["type"]),
                                 "description": b.get("constraint", "")} for b in enrich["body"]}
            op["requestBody"] = {"content": {"application/json": {
                "schema": {"type": "object", "properties": props}}}}
        # A4: documented codes ∪ inferred 4xx (labelled), only when no 4xx documented already
        documented = enrich.get("responses") or ["200"]
        responses = {c: {"description": "OK" if c == "200" else ""} for c in documented}
        if not any(c.startswith("4") for c in responses):
            for c in inferred_error_codes(row):
                label = "Authentication failure" if c == "401" else "Forbidden"
                responses.setdefault(c, {"description": f"{label} (inferred — not in source contract)"})
        op["responses"] = responses
        paths.setdefault(oapath, {})[method.lower()] = op
    return {"openapi": "3.0.1",
            "info": {"title": f"{system_name} API", "version": "0.1",
                     "description": "Synthesized from rebuild-spec artifacts (no source swagger)."},
            "paths": paths, "components": {"schemas": {}}}


def read(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--route-list")
    ap.add_argument("--api-map")
    ap.add_argument("--api-contracts")
    ap.add_argument("--system-name")
    args = ap.parse_args()

    root = os.path.abspath(args.project_root)
    gen = os.path.join(root, "docs", "generated")
    route_list = args.route_list or os.path.join(gen, "route-list.md")
    api_map = args.api_map or os.path.join(gen, "api-map.md")
    api_contracts = args.api_contracts or os.path.join(gen, "api-contracts.md")
    out = args.out or os.path.join(gen, "openapi.yaml")
    sys_name = args.system_name or os.path.basename(root.rstrip("/")) or "System"

    rl_text = read(route_list)
    if not rl_text:
        sys.exit(f"ERROR: route-list.md required but not found: {route_list}\n"
                 "  Run /tkm:rebuild-spec (core pass) first; optionally --api-contracts for richer detail.")
    api_rows, infra_rows = parse_route_list(rl_text)
    if not api_rows:
        sys.exit(f"ERROR: no API routes parsed from {route_list} (only {len(infra_rows)} infra rows).")

    contracts = parse_api_contracts(read(api_contracts))
    cats = load_apimap(api_map if os.path.exists(api_map) else None)
    for row in api_rows:                       # api-map category wins over the route-list heading
        c = cats.get(norm_path(row["path"]))
        if c:
            row["category"] = c

    doc = build_openapi(api_rows, contracts, sys_name)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)

    ops = sum(len(v) for v in doc["paths"].values())
    print(f"route-list : {route_list}")
    print(f"api-contracts: {'used' if contracts else 'absent — params/responses minimal'}")
    print(f"emitted    : {ops} operations from {len(api_rows)} API route rows "
          f"({len(infra_rows)} infra routes excluded)")
    if infra_rows:
        print("  excluded infra: " + ", ".join(f"{r['method']} {r['path']}" for r in infra_rows[:12]))
    if ops != len(api_rows):                    # deterministic coverage: 1 op per kept row
        sys.exit(f"ERROR: coverage drift — {len(api_rows)} rows but {ops} ops emitted.")
    print(f"openapi    : {out}")


if __name__ == "__main__":
    main()
