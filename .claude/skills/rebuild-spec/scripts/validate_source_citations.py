#!/usr/bin/env python3
"""Wave 6.5 — source citation validator.
Verifies `**Source:** path:N-M` references in spec.md files: file exists, range
within bounds, no path traversal. Stdlib only.
Exit codes: 0 (no critical), 1 (critical), 2 (internal).

Modes:
  source (default): accepts only real source paths with line ranges (original behaviour).
  spec-driven: additionally accepts spec:// URIs and specsRoot-relative paths.
               Citations tagged [FROM_CODE] always validated as source paths (not weakened).
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
    assert_under, iter_docs_technical_specs, iter_technical_specs,
    read_authored_by, read_spec_status, resolve_project_root,
)
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, merge_validator_result, recalculate_totals,
)

VALIDATOR = "citation"
# Extension-agnostic by design: CITATION_RE/`_resolve_citation` never filter on file suffix —
# only existence + line-range + traversal are checked. This already covers COBOL sources
# (.cbl/.cob/.cpy/.bms) and `ui-sniff` leads (which cite whatever arbitrary source file the
# accept-path session inspected) with no extra allowlist entry (Phase 04, cobol-stack-and-
# generic-fallback plan). Do not add a suffix allowlist here — it would narrow, not widen.
CITATION_RE = re.compile(r"\*\*Source:\*\*\s+`?([^`\n:]+):(\d+)(?:-(\d+))?`?")
# Matches spec:// URIs: spec://NNN-feature/file.md or spec://NNN-feature/file.md#section
# NNN = one or more digits; feature name = word chars/hyphens; file = any non-whitespace chars
SPEC_URI_RE = re.compile(r"^spec://[A-Za-z0-9][\w\-]*/[^\s#]+(?:#[^\s]*)?$")


def _issue(sev, rid, spec, root, line, msg):
    try:
        loc = str(spec.relative_to(root))
    except ValueError:
        loc = str(spec)
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": loc, "line": line}, "message": msg}


def _resolve_citation(raw: str, spec_path: Path, project_root: Path) -> Path | None:
    """Try project_root/raw, then spec.parent/raw. Return resolved path or None."""
    for base in (project_root, spec_path.parent):
        candidate = (base / raw).resolve()
        try:
            assert_under(candidate, project_root)
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def _is_traversal(raw: str) -> bool:
    """Return True if raw path looks like a traversal or absolute path."""
    return ".." in raw.split("/") or raw.startswith("/") or "\x00" in raw


def _check_spec_uri(raw: str, specs_root: Path | None, root: Path) -> str | None:
    """In spec-driven mode, validate a spec:// URI or specsRoot-relative path.

    Returns None if the citation passes; a rule_id string if it fails.
    """
    # spec:// URI form: logical reference, no file-existence check required
    if raw.startswith("spec://"):
        if not SPEC_URI_RE.match(raw):
            return "citation.spec_uri_invalid"
        # Reject traversal segments inside the URI path (hygiene; SPEC_URI_RE's
        # broad [^\s#]+ would otherwise admit `spec://x/../../etc/passwd`).
        path_part = raw[len("spec://"):].split("#", 1)[0]
        if any(seg in ("..", ".") for seg in path_part.split("/")):
            return "citation.spec_uri_invalid"
        return None  # valid spec-URI — accept
    # specsRoot-relative path: resolved candidate must stay under the PROJECT root
    # (a wider, safer containment than specs_root alone; specs_root itself is
    # already guarded under root at CLI startup).
    if specs_root is not None:
        candidate = (specs_root / raw).resolve()
        try:
            assert_under(candidate, root)
        except ValueError:
            return "citation.path_traversal"
        if candidate.is_file():
            return None  # valid spec file
        return "citation.spec_file_missing"
    return "citation.file_missing"


def _check_citations(spec: Path, root: Path, mode: str = "source",
                     specs_root: Path | None = None) -> list[dict]:
    out: list[dict] = []
    # F8: draft provenance relaxes ONLY the 3 citation rules below; path_traversal stays critical always.
    # Relaxation requires BOTH status: draft AND authored_by: takumi — a draft from any other
    # author is anomalous and gets full strict validation.
    is_draft = read_spec_status(spec) == "draft" and read_authored_by(spec) == "takumi"
    # F8: draft → warning; implemented → critical (path_traversal stays critical regardless).
    src_sev = "warning" if is_draft else "critical"
    lines = spec.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence = False
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = CITATION_RE.search(ln)
        if not m:
            # In spec-driven mode, also check for bare spec:// URIs not matching the
            # standard CITATION_RE (which requires :N-M). These appear as plain **Source:** values.
            if mode == "spec-driven":
                bare = re.search(r"\*\*Source:\*\*\s+`?([^`\n]+)`?", ln)
                if bare:
                    raw = bare.group(1).strip()
                    # [FROM_CODE] is a code citation and MUST carry a source path
                    # + line range (which matches CITATION_RE). Reaching the bare
                    # branch means it lacks :N-M → malformed; never weaken it.
                    if "[FROM_CODE]" in ln:
                        out.append(_issue("critical", "citation.from_code_no_range", spec, root, i + 1,
                                          f"[FROM_CODE] citation requires a source path with line range: {raw!r}"))
                        continue
                    if raw.startswith("spec://") or (specs_root is not None and not raw.startswith("/")):
                        if _is_traversal(raw) and not raw.startswith("spec://"):
                            out.append(_issue("critical", "citation.path_traversal", spec, root, i + 1,
                                              f"citation path looks like traversal/absolute: {raw!r}"))
                        else:
                            rule_id = _check_spec_uri(raw, specs_root, root)
                            if rule_id is not None:
                                msg = (f"spec-URI invalid: {raw!r}" if rule_id == "citation.spec_uri_invalid"
                                       else f"cited spec file not found under specsRoot: {raw!r}")
                                out.append(_issue("critical", rule_id, spec, root, i + 1, msg))
            continue
        raw_path, start_s, end_s = m.group(1).strip(), m.group(2), m.group(3)

        # [FROM_CODE] citations always validated as real source paths (never weakened)
        force_source = "[FROM_CODE]" in ln

        # path-traversal guard before resolving
        if _is_traversal(raw_path):
            out.append(_issue("critical", "citation.path_traversal", spec, root, i + 1,
                              f"citation path looks like traversal/absolute: {raw_path!r}"))
            continue

        # spec-driven mode: try spec-URI / specsRoot branch unless [FROM_CODE] forces source path
        if mode == "spec-driven" and not force_source:
            if raw_path.startswith("spec://") or (
                specs_root is not None and not _resolve_citation(raw_path, spec, root)
            ):
                rule_id = _check_spec_uri(raw_path, specs_root, root)
                if rule_id is None:
                    continue  # accepted
                msg = (f"spec-URI invalid: {raw_path!r}" if rule_id == "citation.spec_uri_invalid"
                       else f"cited spec file not found under specsRoot: {raw_path!r}")
                out.append(_issue("critical", rule_id, spec, root, i + 1, msg))
                continue

        # Source-path validation (default mode and [FROM_CODE] in spec-driven mode)
        resolved = _resolve_citation(raw_path, spec, root)
        if resolved is None:
            out.append(_issue(src_sev, "citation.file_missing", spec, root, i + 1,
                              f"cited file not found under project root: {raw_path!r}"))
            continue
        try:
            file_lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
            count = len(file_lines)
        except (OSError, UnicodeDecodeError):
            out.append(_issue("warning", "citation.unreadable", spec, root, i + 1,
                              f"cited file unreadable: {raw_path!r}"))
            continue
        start = int(start_s); end = int(end_s) if end_s else start
        if start < 1 or end > count:
            out.append(_issue(src_sev, "citation.range_invalid", spec, root, i + 1,
                              f"range {start}-{end} out of bounds (file has {count} lines): {raw_path!r}"))
        elif end < start:
            out.append(_issue(src_sev, "citation.range_inverted", spec, root, i + 1,
                              f"inverted range {start}-{end}: {raw_path!r}"))
    return out


# RE-mode citation-density check (Phase C, re-output-contract.md).
# A "structural claim" is any non-blank, non-heading, non-fence line that could
# carry a **Source:** citation — i.e. lines inside prose/table/list context.
# We use a conservative heuristic: lines that start with a bullet, table cell,
# or are plain prose paragraphs (not blank, not heading, not fence) are candidates.
_CLAIM_LINE_RE = re.compile(r"^\s*[-*|]|^\s*\w")
_HEADING_RE = re.compile(r"^#{1,6}\s")


def _count_structural_claims(spec: Path) -> tuple[int, int]:
    """Return (total_claim_lines, cited_claim_lines) for RE-mode density check.

    A claim line is any non-blank, non-heading, non-fence content line.
    A cited claim line is one that contains a **Source:** citation.
    """
    lines = spec.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence = False
    total = 0
    cited = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            continue
        if _HEADING_RE.match(stripped):
            continue
        # Count as structural claim candidate
        total += 1
        if CITATION_RE.search(ln):
            cited += 1
    return total, cited


def _check_citation_density(spec: Path, root: Path, density_min: float) -> list[dict]:
    """Emit a WARN issue if cited fraction of structural claims is below density_min."""
    try:
        total, cited = _count_structural_claims(spec)
    except OSError:
        return []
    if total == 0:
        return []
    density = cited / total
    if density < density_min:
        try:
            loc = str(spec.relative_to(root))
        except ValueError:
            loc = str(spec)
        return [{
            "validator": VALIDATOR,
            "severity": "warning",
            "rule_id": "citation_density_low",
            "location": {"file": loc, "line": 0},
            "message": (
                f"RE-mode citation density {density:.1%} below threshold "
                f"{density_min:.0%} ({cited}/{total} claim lines cited)"
            ),
        }]
    return []


def validate(plan_dir: Path, root: Path, single: Path | None,
             mode: str = "source", specs_root: Path | None = None,
             docs_root: Path | None = None,
             re_mode: bool = False, density_min: float = 0.8) -> dict:
    if single:
        paths = [single]
    elif docs_root is not None:
        paths = list(iter_docs_technical_specs(docs_root))
    else:
        paths = list(iter_technical_specs(plan_dir))
    per_spec = {}
    for sp in paths:
        try:
            rel = str(sp.relative_to(root))
        except ValueError:
            rel = str(sp)
        issues = _check_citations(sp, root, mode=mode, specs_root=specs_root)
        # RE-mode density check: appended AFTER existing citation issues (WARN only)
        if re_mode:
            issues = issues + _check_citation_density(sp, root, density_min)
        per_spec[sp.parent.name] = {
            "spec_path": rel,
            "issues": issues,
        }
    # [v21.0.0] RE-mode also counts the core screen artifacts toward the citation-density check —
    # screen-list/screen-flow carry structural claims (each screen, each nav edge). They are scanned
    # ONLY when present on disk (i.e. the profile produced them: screen_source != none); a headless
    # run never emits them, so this no-ops there. Density-only (no source-mode citation check — these
    # are core artifacts, not feature technical-specs). Advisory WARN, never HALT.
    if re_mode and single is None and docs_root is None:
        for name in ("screen-list.md", "screen-flow.md"):
            ap = plan_dir / "artifacts" / name
            if not ap.is_file():
                continue
            try:
                rel = str(ap.relative_to(root))
            except ValueError:
                rel = str(ap)
            per_spec[ap.stem] = {
                "spec_path": rel,
                "issues": _check_citation_density(ap, root, density_min),
            }
    return {"validator": VALIDATOR,
            "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "plan_dir": str(plan_dir), "specs": per_spec}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.5 source-citation validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir"); g.add_argument("--spec"); g.add_argument("--docs-root")
    p.add_argument("--project-root", default=None); p.add_argument("--summary-out", default=None)
    p.add_argument("--mode", choices=("source", "spec-driven"), default="source",
                   help="Validation mode: 'source' (default, original behaviour) or "
                        "'spec-driven' (also accepts spec:// URIs and specsRoot-relative paths).")
    p.add_argument("--specs-root", default=None,
                   help="Path to specs root directory (used only with --mode spec-driven). "
                        "Relative citations that resolve here are accepted without line-range check.")
    p.add_argument("--re-mode", action="store_true", default=False,
                   help="RE mode: also check citation density (WARN when below --density-min). "
                        "Without this flag behaviour is byte-for-byte unchanged.")
    _density_raw = __import__("os").environ.get("REBUILD_CITATION_DENSITY_MIN", "0.8")
    try:
        _density_default = float(_density_raw)
    except ValueError:
        print(f"[WARN] invalid REBUILD_CITATION_DENSITY_MIN={_density_raw!r}; using 0.8",
              file=sys.stderr)
        _density_default = 0.8
    p.add_argument("--density-min", type=float, default=_density_default,
                   help="Minimum fraction of structural claims that must carry a citation "
                        "(RE mode only, default 0.8 or env REBUILD_CITATION_DENSITY_MIN).")
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
        single = Path(args.spec).resolve(); plan_dir = single.parent.parent.parent
        if not single.is_file():
            print(f"[ERROR] --spec is not a file: {single}", file=sys.stderr); return 2
        if single.name in ("business-context.md", "screens.md", "edge-cases.md"):
            print("[SKIP] citations only validated on technical-spec.md"); return 0
    try:
        if args.docs_root:
            assert_under(docs_root_path, root)
        else:
            assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr); return 2
    specs_root: Path | None = None
    if args.specs_root:
        specs_root = Path(args.specs_root).resolve()
        try:
            assert_under(specs_root, root)
        except ValueError as exc:
            print(f"[ERROR] --specs-root outside project root: {exc}", file=sys.stderr); return 2
    try:
        result = validate(plan_dir, root, single, mode=args.mode,
                          specs_root=specs_root, docs_root=docs_root_path,
                          re_mode=args.re_mode, density_min=args.density_min)
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
