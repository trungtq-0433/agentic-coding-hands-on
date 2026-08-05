#!/usr/bin/env python3
"""Spec scaffolder — emits a correct-by-construction greenfield spec tree.

Also the classification chokepoint: reads plans/<plan_dir>/spec/.intent-enum.json
and refuses (exit 2) unless the artifact is present and consistent with --mode.

Exit codes:
  0 — success
  1 — validation error (bad slug/args/collision/over-length/fcode+feature-names)
  2 — chokepoint refusal (missing/inconsistent .intent-enum.json, under-decomp,
      RP1.5a not approved) OR fs error (exists w/o --force)
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under  # noqa: E402
from _spec_constants import (  # noqa: E402
    A3_HEADING,
    B4_HEADING,
    EDGE_CASES_SKELETON,
    REQUIRED_CCL_H3,
    REQUIRED_H2_BC,
    REQUIRED_H2_SCR,
    REQUIRED_H2_TECH,
)

# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

_DRAFT_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_DRAFT_SLUG_MAX = 64
_FCODE_RE = re.compile(r"^F\d{3}$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def kebab(name: str) -> str:
    """Convert an arbitrary name to kebab-case draft slug segment.

    NFKD-folds accented Latin so VI/diacritic names transliterate instead of
    silently dropping (café -> cafe, Nâng cấp -> nang-cap). Names with no ASCII
    representation at all (pure CJK, e.g. 日本語機能) fold to '' — the caller
    must detect the empty result and surface a targeted error. [MED-2]
    """
    folded = unicodedata.normalize("NFKD", name)
    folded = folded.encode("ascii", "ignore").decode("ascii")
    lowered = folded.lower()
    result = _NON_ALNUM_RE.sub("-", lowered)
    result = result.strip("-")
    # Collapse consecutive hyphens
    result = re.sub(r"-{2,}", "-", result)
    return result


def is_valid_draft_slug(s: str) -> bool:
    """Draft slug: kebab-case, max 64 chars. Different from promoted SLUG_RE."""
    if len(s) > _DRAFT_SLUG_MAX:
        return False
    return bool(_DRAFT_SLUG_RE.match(s))


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Frontmatter rendering
# ---------------------------------------------------------------------------

def _render_frontmatter(*, status: str, authored_by: str, created: str,
                         lang: str, fcode: str | None) -> str:
    lines = [
        "---",
        f"status: {status}",
        f"authored_by: {authored_by}",
        f"created: {created}",
        f"lang: {lang}",
    ]
    if fcode:
        lines.append(f"fcode: {fcode}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _render_feature_list_frontmatter(*, status: str, authored_by: str,
                                      created: str) -> str:
    lines = [
        "---",
        f"status: {status}",
        f"authored_by: {authored_by}",
        f"created: {created}",
        "---",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Spec content renderers
# ---------------------------------------------------------------------------

def _render_technical_spec(slug: str, frontmatter: str, fcode: str | None) -> str:
    """Render a draft technical-spec.md skeleton.

    The validator requires a `# F###_Slug` heading even for drafts (structural
    rule, not relaxed for draft status).  When fcode is known, use it; otherwise
    use the placeholder `F000_Placeholder` which is valid per FCODE_HEADING_RE.
    """
    fcode_part = fcode if fcode else "F000"
    # Derive a CamelCase heading label from the draft slug
    label = "".join(w.capitalize() for w in slug.replace("-", "_").split("_")) or "Placeholder"
    heading = f"# {fcode_part}_{label}"
    sections = [frontmatter, heading, ""]
    for h2 in REQUIRED_H2_TECH:
        sections.append(h2)
        if h2 == "## Cross-Cutting Logic":
            for h3 in REQUIRED_CCL_H3:
                sections.append(h3)
                sections.append("")
                sections.append("None.")
                sections.append("")
            sections.append("**Client behavior:** see behavior-logic.md, permissions.md, screen-flow.md")
        elif h2 == "## User Stories":
            # FeatureSpec.edge_cases: ### Edge Cases required under ## User Stories
            sections.append("")
            sections.append("### Edge Cases")
            sections.append("")
            sections.append("See edge-cases.md.")
        sections.append("")

    # F3 (v26.0.0): scaffold_spec.py renders from REQUIRED_H2_TECH, not from the template
    # files, so a fresh draft would otherwise permanently lack A3/B4. Decision 2 forbids
    # adding these headings to REQUIRED_H2_TECH itself (no degradation window on that
    # exact-order check) — append them here instead, after the loop, so they never enter
    # that check. Placeholder-heavy body (curly braces) so the dedicated validator classifies
    # a fresh draft as WARN *.unmapped, not CRITICAL *.malformed.
    sections.append(A3_HEADING)
    sections.append("")
    sections.append(
        "{Ordered reading list (data model -> entry point -> view -> logic), 1 file per "
        "step, with a 1-sentence \"why start here.\"}"
    )
    sections.append("")
    sections.append("1. **File:** `{path/to/file.ext:start-end}` — {why read this first}")
    sections.append("")
    sections.append("### Call Hierarchy")
    sections.append("")
    sections.append("```text")
    sections.append("{entry point -> handler -> data layer call chain}")
    sections.append("```")
    sections.append("")
    sections.append(
        "**Related files:** see `## Source Code References` above (Order column added "
        "there — F15 DRY, one table not two)."
    )
    sections.append("")
    sections.append(B4_HEADING)
    sections.append("")
    sections.append(
        "{One row per user action/endpoint that writes to the database. Source cites "
        "`file:line` or `[INFERRED]`.}"
    )
    sections.append("")
    sections.append("| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |")
    sections.append("|-----------------|-------|---------|-----------|-------------------|--------|")
    sections.append(
        "| {METHOD /path or event name} | `{table_name}` | {col1, col2} | "
        "{INSERT\\|UPDATE\\|DELETE} | {how the value is computed} | "
        "`{path/to/handler.ext:line — or an INFERRED tag if not citable}` |"
    )
    sections.append("")
    return "\n".join(sections)


def _render_business_context(frontmatter: str) -> str:
    sections = [frontmatter]
    for h2 in REQUIRED_H2_BC:
        sections.append(h2)
        sections.append("")
    return "\n".join(sections)


def _render_screens(frontmatter: str) -> str:
    sections = [frontmatter]
    for h2 in REQUIRED_H2_SCR:
        sections.append(h2)
        sections.append("")
    return "\n".join(sections)


def _render_edge_cases(frontmatter: str) -> str:
    return frontmatter + "\n" + EDGE_CASES_SKELETON


# ---------------------------------------------------------------------------
# Chokepoint: .intent-enum.json validation
# ---------------------------------------------------------------------------

def _load_intent_enum(plan_dir: Path) -> dict:
    """Load and parse .intent-enum.json. Raises SystemExit(2) on any failure."""
    path = plan_dir / "spec" / ".intent-enum.json"
    if not path.exists():
        print(f"[CHOKEPOINT] missing: {path}", file=sys.stderr)
        print("exit 2: .intent-enum.json not found — run intent-enum step first", file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[CHOKEPOINT] garbled .intent-enum.json: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("[CHOKEPOINT] .intent-enum.json must be a JSON object", file=sys.stderr)
        sys.exit(2)
    if "mode" not in data or "intents" not in data:
        print("[CHOKEPOINT] .intent-enum.json missing required keys: mode, intents", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["intents"], list):
        print("[CHOKEPOINT] .intent-enum.json intents must be a list", file=sys.stderr)
        sys.exit(2)
    return data


def _enforce_chokepoint(plan_dir: Path, mode: str) -> None:
    """Enforce classification gate. Exits 2 on refusal."""
    data = _load_intent_enum(plan_dir)
    artifact_mode = data.get("mode", "")
    intents = data["intents"]
    justification = data.get("justification", "")
    n = len(intents)

    if artifact_mode != mode:
        print(
            f"[CHOKEPOINT] mode mismatch: --mode={mode} but .intent-enum.json mode={artifact_mode!r}",
            file=sys.stderr,
        )
        sys.exit(2)

    if mode == "single":
        if n > 1 and not justification:
            print(
                f"under-decomposition: {n} intents enumerated, mode=single, no justification",
                file=sys.stderr,
            )
            sys.exit(2)

    elif mode == "system":
        sentinel = plan_dir / ".rp-1.5a-pending"
        if sentinel.exists():
            print(
                "[CHOKEPOINT] RP1.5a not approved: sentinel plans/<plan_dir>/.rp-1.5a-pending is present",
                file=sys.stderr,
            )
            sys.exit(2)
        if n < 2:
            print(
                f"[CHOKEPOINT] system mode requires ≥2 intents; only {n} enumerated",
                file=sys.stderr,
            )
            sys.exit(2)


# ---------------------------------------------------------------------------
# Fcode clobber check (RT-10)
# ---------------------------------------------------------------------------

def _warn_fcode_clobber(project_root: Path, fcode: str) -> None:
    """Warn if fcode already referenced in .spec-promote-pending.json."""
    pending = project_root / "docs" / ".spec-promote-pending.json"
    if not pending.exists():
        return
    try:
        data = json.loads(pending.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if isinstance(data, dict):
        entries = data.get("pending", [])
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and entry.get("fcode") == fcode:
                    print(
                        f"[WARN] fcode {fcode} already referenced in docs/.spec-promote-pending.json "
                        "(documented limitation: no lock — proceeding)",
                        file=sys.stderr,
                    )
                    return


# ---------------------------------------------------------------------------
# Scaffold: single feature
# ---------------------------------------------------------------------------

def _scaffold_feature(
    spec_root: Path,
    slug: str,
    frontmatter: str,
    *,
    force: bool,
) -> list[Path]:
    """Scaffold 4 files + marker for one feature. Returns list of created paths."""
    feature_dir = spec_root / slug
    marker = feature_dir / ".scaffold-complete"

    # RT-4: skip-if-exists keyed on MARKER, not directory
    if marker.exists() and not force:
        return []

    # Path-traversal guard BEFORE any filesystem write (defense-in-depth even
    # if _scaffold_feature is called without the outer main() guard)
    assert_under(feature_dir, spec_root)

    feature_dir.mkdir(parents=True, exist_ok=True)

    # Extract fcode from frontmatter if present (parse the `fcode:` line)
    _fcode_fm = None
    for _line in frontmatter.splitlines():
        if _line.startswith("fcode:"):
            _fcode_fm = _line.split(":", 1)[1].strip()
            break

    files = {
        "technical-spec.md": _render_technical_spec(slug, frontmatter, _fcode_fm),
        "business-context.md": _render_business_context(frontmatter),
        "screens.md": _render_screens(frontmatter),
        "edge-cases.md": _render_edge_cases(frontmatter),
    }

    created: list[Path] = []
    for fname, content in files.items():
        fpath = feature_dir / fname
        assert_under(fpath, spec_root)
        # RT-4: re-scaffold only absent files when marker is missing
        if not fpath.exists() or force:
            _atomic_write_text(fpath, content)
            created.append(fpath)

    # Write marker LAST (after all 4 files land)
    _atomic_write_text(marker, "")
    created.append(marker)
    return created


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# RT-14: SYSTEM folder-count machine check
# ---------------------------------------------------------------------------

_FCODE_ROW_RE = re.compile(r"^\|\s*F\d{3}")


def check_folder_count(plan_dir: Path) -> int:
    """Compare feature folder count vs feature-list.md row count.

    Prints a one-line result to stdout.
    Returns 0 on match, 1 on mismatch, 2 on missing inputs.
    """
    spec_root = plan_dir / "spec"
    feature_list = spec_root / "feature-list.md"
    if not feature_list.exists():
        print(
            f"[ERROR] feature-list.md not found: {feature_list}",
            file=sys.stderr,
        )
        return 2

    # Count ONLY scaffolded feature dirs — those carrying the `.scaffold-complete`
    # marker the scaffolder writes last. Stray dirs (research/, flows/,
    # .review-archive/, …) must NOT inflate the count, or RT-14 reports a false
    # MISMATCH and blocks an otherwise-correct SYSTEM scaffold. [H1]
    folder_count = sum(
        1 for p in spec_root.iterdir()
        if p.is_dir() and (p / ".scaffold-complete").is_file()
    )

    try:
        rows = [
            line
            for line in feature_list.read_text(encoding="utf-8").splitlines()
            if _FCODE_ROW_RE.match(line)
        ]
    except OSError as exc:
        print(f"[ERROR] cannot read feature-list.md: {exc}", file=sys.stderr)
        return 2

    row_count = len(rows)
    if folder_count == row_count:
        print(f"OK folder-count={folder_count} matches feature-list rows={row_count}")
        return 0
    else:
        print(
            f"MISMATCH folders={folder_count} feature-list rows={row_count}",
            file=sys.stderr,
        )
        return 1


def main(argv: list[str]) -> int:  # noqa: C901
    p = argparse.ArgumentParser(description="Scaffold a greenfield spec tree")
    p.add_argument("--plan-dir", required=True)
    p.add_argument("--mode", required=True, choices=["single", "system"])
    p.add_argument("--lang", required=True)
    p.add_argument("--slug", default=None)
    p.add_argument("--feature-names", default=None)
    p.add_argument("--fcode", default=None)
    p.add_argument("--date", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument(
        "--check-folder-count",
        action="store_true",
        help="[RT-14] Compare feature folder count vs feature-list.md rows. "
             "No files created. Exit 0 = match, 1 = mismatch, 2 = error.",
    )
    args = p.parse_args(argv)

    # RT-14: check-only mode — resolve plan-dir then delegate, skip all scaffold logic.
    if args.check_folder_count:
        if ".." in Path(args.plan_dir).parts:
            print("[ERROR] --plan-dir must not contain '..'", file=sys.stderr)
            return 1
        return check_folder_count(Path(args.plan_dir).resolve())

    # RT-3: path-traversal guard on --plan-dir
    if ".." in Path(args.plan_dir).parts:
        print("[ERROR] --plan-dir must not contain '..'", file=sys.stderr)
        return 1

    plan_dir = Path(args.plan_dir).resolve()
    spec_root = plan_dir / "spec"

    # RT-3: path-traversal guard on --slug
    if args.slug and ".." in args.slug:
        print("[ERROR] --slug must not contain '..'", file=sys.stderr)
        return 1

    # RT-1/RT-2: Chokepoint — FIRST substantive action after '..' rejection
    _enforce_chokepoint(plan_dir, args.mode)

    # Mode/arg coherence
    if args.mode == "single" and not args.slug:
        print("[ERROR] --mode single requires --slug", file=sys.stderr)
        return 1
    if args.mode == "system" and not args.feature_names:
        print("[ERROR] --mode system requires --feature-names", file=sys.stderr)
        return 1
    if args.fcode and args.feature_names:
        print("[ERROR] --fcode and --feature-names are mutually exclusive", file=sys.stderr)
        return 1
    if args.fcode:
        if args.mode != "single":
            print("[ERROR] --fcode requires --mode single", file=sys.stderr)
            return 1
        if not _FCODE_RE.match(args.fcode):
            print(f"[ERROR] --fcode must match ^F\\d{{3}}$, got: {args.fcode!r}", file=sys.stderr)
            return 1

    # Validate/derive date
    created_date = args.date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")

    if args.mode == "single":
        slug = args.slug
        if len(slug) > _DRAFT_SLUG_MAX:
            print(
                f"[ERROR] --slug exceeds {_DRAFT_SLUG_MAX} characters: {slug!r}",
                file=sys.stderr,
            )
            return 1
        if not is_valid_draft_slug(slug):
            print(
                f"[ERROR] --slug is not valid kebab-case: {slug!r}",
                file=sys.stderr,
            )
            return 1

        # RT-10: fcode clobber check
        if args.fcode:
            _warn_fcode_clobber(plan_dir.parent.parent, args.fcode)

        frontmatter = _render_frontmatter(
            status="draft",
            authored_by="takumi",
            created=created_date,
            lang=args.lang,
            fcode=args.fcode,
        )

        if args.dry_run:
            feature_dir = spec_root / slug
            tree = [
                str(feature_dir / "technical-spec.md"),
                str(feature_dir / "business-context.md"),
                str(feature_dir / "screens.md"),
                str(feature_dir / "edge-cases.md"),
                str(feature_dir / ".scaffold-complete"),
            ]
            print(json.dumps(tree))
            return 0

        # RT-3: assert spec_root boundary
        try:
            assert_under(spec_root / slug, spec_root)
        except ValueError as exc:
            print(f"[ERROR] path traversal detected: {exc}", file=sys.stderr)
            return 2

        created = _scaffold_feature(spec_root, slug, frontmatter, force=args.force)
        all_paths = [str(p) for p in created]
        print(json.dumps(all_paths))
        return 0

    else:  # system
        names = [n.strip() for n in args.feature_names.split(",") if n.strip()]
        if not names:
            print(
                "[ERROR] --feature-names contained no non-empty names",
                file=sys.stderr,
            )
            return 1

        # RT-9: derive slugs first, dedup check before any write
        slugs: list[str] = []
        slug_to_names: dict[str, list[str]] = {}
        for name in names:
            derived = kebab(name)
            if not derived:
                # Name has no ASCII representation (e.g. pure CJK) — slugs are
                # ASCII-only. Don't blame the user for kebab-case; tell them how
                # to proceed. [MED-2]
                print(
                    f"[ERROR] feature name {name!r} has no ASCII representation; "
                    f"slugs are ASCII-only — pass an explicit ASCII --slug "
                    f"(single mode) or rename the feature with Latin characters.",
                    file=sys.stderr,
                )
                return 1
            if len(derived) > _DRAFT_SLUG_MAX:
                print(
                    f"[ERROR] derived slug exceeds {_DRAFT_SLUG_MAX} characters for name {name!r}: {derived!r}",
                    file=sys.stderr,
                )
                return 1
            if not is_valid_draft_slug(derived):
                print(
                    f"[ERROR] derived slug is not valid kebab-case for name {name!r}: {derived!r}",
                    file=sys.stderr,
                )
                return 1
            slugs.append(derived)
            slug_to_names.setdefault(derived, []).append(name)

        collisions = {slug: names_list for slug, names_list in slug_to_names.items()
                      if len(names_list) > 1}
        if collisions:
            collision_detail = "; ".join(
                f"{slug!r} <- {names_list}" for slug, names_list in collisions.items()
            )
            print(f"[ERROR] slug collisions: {collision_detail}", file=sys.stderr)
            return 1

        if args.dry_run:
            tree: list[str] = [str(spec_root / "feature-list.md")]
            for slug in slugs:
                feature_dir = spec_root / slug
                tree += [
                    str(feature_dir / "technical-spec.md"),
                    str(feature_dir / "business-context.md"),
                    str(feature_dir / "screens.md"),
                    str(feature_dir / "edge-cases.md"),
                    str(feature_dir / ".scaffold-complete"),
                ]
            print(json.dumps(tree))
            return 0

        # Write feature-list.md stub (no lang, no fcode) — ONLY when absent (or --force).
        # The decomposition researcher writes a richer feature-list.md in Step 0a (BEFORE the
        # scaffolder runs in the RP1.5a APPROVED branch); clobbering it here would destroy the
        # confirmed feature breakdown and trip a false RT-14 folder-count MISMATCH (rows=0).
        fl_path = spec_root / "feature-list.md"
        assert_under(fl_path, spec_root)
        spec_root.mkdir(parents=True, exist_ok=True)

        all_paths: list[str] = []
        if not fl_path.exists() or args.force:
            fl_fm = _render_feature_list_frontmatter(
                status="draft",
                authored_by="takumi",
                created=created_date,
            )
            _atomic_write_text(fl_path, fl_fm)
            all_paths.append(str(fl_path))

        for slug in slugs:
            frontmatter = _render_frontmatter(
                status="draft",
                authored_by="takumi",
                created=created_date,
                lang=args.lang,
                fcode=None,
            )
            try:
                assert_under(spec_root / slug, spec_root)
            except ValueError as exc:
                print(f"[ERROR] path traversal detected: {exc}", file=sys.stderr)
                return 2
            created = _scaffold_feature(spec_root, slug, frontmatter, force=args.force)
            all_paths.extend(str(p) for p in created)

        print(json.dumps(all_paths))
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
