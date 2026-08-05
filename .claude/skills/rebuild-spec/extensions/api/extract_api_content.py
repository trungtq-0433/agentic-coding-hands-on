"""Extract API content from an rswag/OpenAPI swagger file into intermediate JSON.

Project-agnostic (rebuild-spec --api-doc extension). Produces in --out-dir:
  api-content.json   one record per operation (meta + params + responses)
  api-list.json      rows for the 'API List' sheet
  status-codes.json  distinct status codes used, for the 'Status code' sheet

Param scope: path + query + requestBody props only. Universal auth/locale headers are
excluded (covered once in 'Common Conventions'; keeps every param table within the
template's fixed 10-row area).

Usage:
  python extract_api_content.py --swagger PATH [--api-map PATH] --out-dir DIR
  python extract_api_content.py --project-root DIR --out-dir DIR   # auto-detect swagger
"""
import os
import sys
import re
import json
import argparse
try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML is required — install with `pip install pyyaml`, "
             "or run via the kit venv: .claude/skills/.venv/bin/python3")

PARAM_TYPE = {"path": "Path Parameters", "query": "Query Parameters"}
DATA_TYPE = {"integer": "Integer", "number": "Integer", "string": "string",
             "text": "text", "boolean": "boolean", "file": "file"}
STATUS_DESC = {"200": "OK", "201": "Created", "202": "Accepted", "204": "No Content",
               "400": "Bad request", "401": "Authentication failure",
               "403": "Forbidden", "404": "Resource not found",
               "409": "Conflict", "422": "Unprocessable Entity",
               "500": "Internal Server Error", "503": "Service Unavailable"}


def find_swagger(root):
    """All swagger/openapi files (heavy dirs pruned), best candidate first.

    Rank: inside a swagger/openapi/api-docs dir > .yaml over .json > larger file > shallower.
    Returns the sorted list (caller picks [0] and may warn if >1)."""
    skip = {"node_modules", ".git", "vendor", "tmp", "dist", "build", ".bundle"}
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for fn in filenames:
            low = fn.lower()
            if low.startswith(("swagger", "openapi")) and low.endswith((".yaml", ".yml", ".json")):
                hits.append(os.path.join(dirpath, fn))

    def score(p):
        segs = [s.lower() for s in p.split(os.sep)[:-1]]
        in_api_dir = any(s in ("swagger", "openapi", "api-docs", "apidocs") for s in segs)
        is_yaml = p.lower().endswith((".yaml", ".yml"))
        try:
            size = os.path.getsize(p)
        except OSError:
            size = 0
        return (in_api_dir, is_yaml, size, -p.count(os.sep))

    return sorted(hits, key=score, reverse=True)


def norm_path(p):
    p = re.sub(r"\{[^}]+\}", "*", p)
    p = re.sub(r":[A-Za-z_]+", "*", p)
    return p.rstrip("/").lower()


def load_apimap(path):
    cat = {}
    if not path or not os.path.exists(path):
        return cat
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    domain = None
    for line in lines:
        h = re.match(r"^#{2,4}\s+(.*)", line.strip())   # A5: api-map uses ## (h2) domain headings
        if h:
            domain = h.group(1).strip()
            continue
        m = re.match(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`", line.strip())
        if m and domain:
            cat[norm_path(m.group(2))] = domain
    return cat


def data_type_annot(schema):
    """Map an OpenAPI schema to (dropdown_value, annotation).

    dropdown_value is ALWAYS one of the template's 5 allowed Data Type values
    {Integer, string, text, boolean, file} — so the cell stays a valid dropdown choice and
    style fidelity holds. annotation captures the precise type the dropdown cannot express
    (decimal `number`, `array<elem>`) and is appended to the param description, keeping the
    mapping lossless. Returns "" annotation for types the dropdown represents exactly.
    """
    s = schema or {}
    t = s.get("type", "string")
    if t == "array":
        items = s.get("items") or {}
        if "$ref" in items:
            return "string", "[array<object>]"
        et = items.get("type", "string")
        return DATA_TYPE.get(et, "string"), f"[array<{et}>]"
    if t == "number":                     # no 'number/decimal' option in the dropdown
        fmt = s.get("format")
        return "Integer", (f"[number({fmt})]" if fmt else "[number]")
    return DATA_TYPE.get(t, "string"), ""


def with_annot(desc, annot):
    """Append a type annotation to a description without losing either piece."""
    desc = desc or ""
    return f"{desc} {annot}".strip() if annot else desc


def resolve(ref, schemas):
    return schemas.get(ref.split("/")[-1], {})


def schema_example(schema, schemas, depth=0):
    if schema is None or depth > 6:
        return None
    if "$ref" in schema:
        return schema_example(resolve(schema["$ref"], schemas), schemas, depth + 1)
    if "example" in schema:
        return schema["example"]
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        out = {}
        for k, v in (schema.get("properties") or {}).items():
            if "$ref" in v:
                out[k] = schema_example(v, schemas, depth + 1)
            elif v.get("type") == "array":
                out[k] = [schema_example(v.get("items", {}), schemas, depth + 1)]
            elif "example" in v:
                out[k] = v["example"]
            else:
                out[k] = v.get("type", "string")
        return out
    if t == "array":
        return [schema_example(schema.get("items", {}), schemas, depth + 1)]
    return schema.get("example", t or "string")


def example_json(resp, schemas):
    for mt, mv in (resp.get("content") or {}).items():
        obj = schema_example(mv.get("schema"), schemas, 0)
        if obj is not None:
            return json.dumps(obj, ensure_ascii=False, indent=2)
    return ""


def sheet_name(idx, method, path, used):
    segs = [s for s in path.split("/") if s and s not in ("api", "v1")
            and not s.startswith("{") and not s.startswith(":")]
    hint = "_".join(segs[-2:]) if segs else "root"
    base = re.sub(r"[/{}:?*\[\]\\']", "", f"{idx:02d}.{method[:3]} {hint}")[:31].rstrip()
    name, i = base, 1
    while name.lower() in used:
        sfx = f"~{i}"
        name = base[:31 - len(sfx)] + sfx
        i += 1
    used.add(name.lower())
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--swagger")
    ap.add_argument("--api-map")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    swagger = args.swagger
    if not swagger:
        cands = find_swagger(args.project_root)
        if not cands:
            sys.exit(f"ERROR: no swagger/openapi found under {args.project_root}. Pass --swagger PATH.")
        swagger = cands[0]
        if len(cands) > 1:
            print(f"NOTE: {len(cands)} swagger files found; using best match: {swagger}")
            print("      others: " + ", ".join(cands[1:4]) + "  (override with --swagger if wrong)")
    if not os.path.exists(swagger):
        sys.exit(f"ERROR: swagger not found: {swagger}")
    api_map = args.api_map
    if not api_map:
        cand = os.path.join(args.project_root, "docs", "generated", "api-map.md")
        api_map = cand if os.path.exists(cand) else None
    os.makedirs(args.out_dir, exist_ok=True)
    print(f"swagger: {swagger}")
    print(f"api-map: {api_map or '(none — categories from tags)'}")

    try:
        with open(swagger, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except (yaml.YAMLError, UnicodeDecodeError) as e:
        sys.exit(f"ERROR: failed to parse {swagger}: {e}\n  Pass a valid --swagger PATH.")
    schemas = (doc.get("components") or {}).get("schemas", {})
    cats = load_apimap(api_map)
    content, api_list, status_used, used = [], [], set(), set()

    for path, methods in (doc.get("paths") or {}).items():
        for method, op in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            M = method.upper()
            summary = re.sub(r"^API:\s*", "", (op.get("summary") or "").strip()) or f"{M} {path}"
            category = cats.get(norm_path(path)) or (op.get("tags") or ["Common"])[0]
            params = []
            for pp in op.get("parameters", []) or []:
                if pp.get("in") == "header":
                    continue
                dt, annot = data_type_annot(pp.get("schema"))
                params.append({
                    "param_type": PARAM_TYPE.get(pp.get("in"), "Query Parameters"),
                    "key": pp.get("name", ""), "data_type": dt,
                    "values": str(pp.get("example", "")),
                    "description": with_annot(pp.get("description", ""), annot),
                    "note": "[required]" if pp.get("required") else "",
                })
            media = "application/json"
            rb = op.get("requestBody")
            if rb:
                for mt, mv in (rb.get("content") or {}).items():
                    media = mt
                    sch = mv.get("schema", {})
                    if "$ref" in sch:
                        sch = resolve(sch["$ref"], schemas)
                    ptype = "Form Parameters" if ("form" in mt or "multipart" in mt) else "Body"
                    for k, v in (sch.get("properties") or {}).items():
                        dt, annot = data_type_annot(v)
                        ex = "" if "$ref" in v else str(v.get("example", ""))
                        params.append({"param_type": ptype, "key": k, "data_type": dt,
                                       "values": ex,
                                       "description": with_annot(v.get("description", ""), annot),
                                       "note": ""})
                    break
            responses = []
            for code, resp in (op.get("responses") or {}).items():
                status_used.add(code)
                responses.append({"status": code,
                                  "description": resp.get("description") or STATUS_DESC.get(code, ""),
                                  "example": example_json(resp, schemas), "note": ""})
            responses.sort(key=lambda r: r["status"])
            sn = sheet_name(len(content) + 1, M, path, used)
            content.append({"sheet_name": sn, "category": category, "screen_feature": summary,
                            "api_name": summary, "endpoint": path, "method": M,
                            "description": (op.get("description") or summary),   # A6: carry security note
                            "media_type": media,
                            "params": params, "responses": responses})
            api_list.append({"category": category, "screen_feature": summary,
                             "api_url": f"{M} {path}", "detail_description": summary,
                             "note": "", "sheet_name": sn})

    status_codes = [{"code": c, "description": STATUS_DESC.get(c, "")}
                    for c in sorted(status_used, key=lambda x: (len(x), x))]
    for fn, data in [("api-content.json", content), ("api-list.json", api_list),
                     ("status-codes.json", status_codes)]:
        with open(os.path.join(args.out_dir, fn), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    if not content:
        print("WARNING: no operations parsed — JSON written empty.")
        return
    trunc = [c["sheet_name"] for c in content if len(c["responses"]) > 7]
    print(f"ops: {len(content)} | max params: {max(len(c['params']) for c in content)} | "
          f"max responses: {max(len(c['responses']) for c in content)}")
    if any(len(c["params"]) > 10 for c in content):
        print("WARNING: some ops have >10 params (param overflow NOT handled by builder).")
    if trunc:
        print(f"WARNING: builder caps responses at 7 — WILL truncate: {trunc}")


if __name__ == "__main__":
    main()
