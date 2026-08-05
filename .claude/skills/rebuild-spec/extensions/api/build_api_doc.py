"""Driver for the rebuild-spec --api-doc pass: swagger -> Sun* API Design xlsx (verified).

One command runs the full pipeline against any project:
  1. make golden style-fingerprint from the (bundled) template
  2. resolve the API source: explicit --swagger > auto-detected swagger > DERIVE from rebuild-spec
     artifacts (route-list.md [+ api-map/api-contracts]) via artifacts2openapi.py -> openapi.yaml.
     So a project with NO swagger still produces the doc, on any stack.
  3. extract API content -> intermediate JSON   4. build workbook   5. verify style (drift + logo +
     completeness + coverage)   6. container health (zip/OOXML/UTF-8/relationships — opens w/o repair).
     Derived runs are deterministic: 1 operation per API route row.

Usage:
  python build_api_doc.py --project-root /path/to/project [--swagger PATH] [--api-map PATH]
      [--from-artifacts] [--out-dir DIR] [--out FILE.xlsx] [--system-name NAME] [--creator NAME]
      [--date YYYY-MM-DD] [--template T.xlsx] [--logo L.png]
Defaults: out-dir = <project-root>/docs/api ; template/logo = bundled ; system-name = project dir name.
`--from-artifacts` forces the derived path even when a swagger exists (e.g. swagger is stale).
Run with the kit venv python (has openpyxl + PyYAML):
  .claude/skills/.venv/bin/python3 <this> --project-root .
"""
import os
import sys
import subprocess
import argparse
from extract_api_content import find_swagger

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, *cli):
    cmd = [PY, os.path.join(HERE, script), *cli]
    print(f"\n$ {script} {' '.join(cli)}")
    r = subprocess.run(cmd, cwd=HERE)
    if r.returncode != 0:
        sys.exit(f"STEP FAILED: {script} (exit {r.returncode})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--swagger")
    ap.add_argument("--api-map")
    ap.add_argument("--out-dir")
    ap.add_argument("--out")
    ap.add_argument("--system-name")
    ap.add_argument("--creator", default="Sun Asterisk Vietnam")
    ap.add_argument("--date", default="")
    ap.add_argument("--template", default=os.path.join(HERE, "api-design-template.xlsx"))
    ap.add_argument("--logo", default=os.path.join(HERE, "sun-logo.png"))
    ap.add_argument("--from-artifacts", action="store_true",
                    help="force deriving the spec from rebuild-spec docs even if a swagger exists")
    args = ap.parse_args()

    root = os.path.abspath(args.project_root)
    out_dir = os.path.abspath(args.out_dir or os.path.join(root, "docs", "api"))
    sys_name = args.system_name or os.path.basename(root.rstrip("/")) or "System"
    out = os.path.abspath(args.out or os.path.join(out_dir, f"{sys_name} - API Design.xlsx"))
    golden = os.path.join(out_dir, ".golden.json")
    os.makedirs(out_dir, exist_ok=True)

    print(f"project-root : {root}")
    print(f"out          : {out}")
    print(f"system-name  : {sys_name}")

    # 1. golden baseline from the template (style fingerprint)
    run("verify_format.py", args.template, golden, "--make-golden")
    # 2. resolve the API source: explicit swagger > auto-detected swagger > derive from rebuild-spec docs
    swagger = os.path.abspath(args.swagger) if args.swagger else None
    derived = False
    # A8: ignore our own derived openapi.yaml in out_dir — else re-runs consume stale output as "source"
    real_swaggers = [s for s in find_swagger(root)
                     if os.path.abspath(os.path.dirname(s)) != out_dir]
    if not args.from_artifacts and not swagger and not real_swaggers:
        args.from_artifacts = True               # no real swagger anywhere → fall back to artifacts
    if args.from_artifacts:                       # forced (wins over any swagger) or auto-fallback → derive
        openapi = os.path.join(out_dir, "openapi.yaml")
        a2o = ["--project-root", root, "--out", openapi, "--system-name", sys_name]
        if args.api_map:
            a2o += ["--api-map", os.path.abspath(args.api_map)]
        run("artifacts2openapi.py", *a2o)        # ABORTs if route-list.md is also missing
        swagger, derived = openapi, True
    # 3. extract content (from swagger, or auto-detect when neither flag set and a swagger exists)
    ext = ["--project-root", root, "--out-dir", out_dir]
    if swagger:
        ext += ["--swagger", swagger]
    if args.api_map:
        ext += ["--api-map", os.path.abspath(args.api_map)]
    run("extract_api_content.py", *ext)
    # 3b. semantic lint (B1) — hard gate on derived-content fidelity BEFORE build (driver aborts on fail)
    run("verify_semantics.py", swagger, os.path.join(out_dir, "api-content.json"),
        "--route-list", os.path.join(root, "docs", "generated", "route-list.md"))
    # 4. build workbook
    prov = "derived from code analysis (no source swagger)" if derived else "generated from the OpenAPI/swagger spec"
    run("build_api_design.py", "--in-dir", out_dir, "--out", out,
        "--template", args.template, "--logo", args.logo,
        "--system-name", sys_name, "--creator", args.creator, "--date", args.date,
        "--provenance", prov)
    # 5. verify style fidelity (drift + dangling-ref + logo + completeness + coverage)
    run("verify_format.py", golden, out)
    # 6. container health (zip/OOXML/UTF-8/relationships/images) — proves Excel opens without repair
    run("xlsx_health.py", out)
    tag = "derived from code analysis — no source swagger" if derived else "from swagger"
    print(f"\n=== API design doc SEALED ({tag}): {out} ===")


if __name__ == "__main__":
    main()
