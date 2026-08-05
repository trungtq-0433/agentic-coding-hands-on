"""Shared helpers for rebuild-spec validators. Stdlib only.
Schema: ../references/canonical-fcode-schema.md
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path
from typing import Iterator

SLUG_RE = re.compile(r"^F\d{3}_[A-Za-z0-9]+$")

# ---------------------------------------------------------------------------
# Frontmatter readers (stdlib re only — no PyYAML)
# ---------------------------------------------------------------------------

_FM_STATUS_RE = re.compile(r"^status:\s*(draft|implemented)\b", re.MULTILINE)
_FM_AUTHORED_RE = re.compile(r"^authored_by:\s*(\S+)", re.MULTILINE)
_MAX_FM_LINES = 30  # scan only first N lines to avoid reading large files


def _read_frontmatter(path: Path) -> str:
    """Return the leading YAML frontmatter block as a string, or '' if absent/unreadable."""
    try:
        lines = []
        with path.open(encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= _MAX_FM_LINES:
                    break
                lines.append(line)
        text = "".join(lines)
    except (OSError, FileNotFoundError):
        return ""
    # Must start with ---
    if not text.startswith("---"):
        return ""
    # Find closing ---
    rest = text[3:]
    end = rest.find("\n---")
    if end == -1:
        return rest
    return rest[: end + 1]


def read_spec_status(path: Path) -> str:
    """Parse leading YAML frontmatter for ``status:`` value.

    Returns ``'draft'`` or ``'implemented'``.
    Default when absent or file not found: ``'implemented'`` — fully backwards-compatible.
    """
    fm = _read_frontmatter(path)
    m = _FM_STATUS_RE.search(fm)
    return m.group(1) if m else "implemented"


def read_authored_by(path: Path) -> str:
    """Parse leading YAML frontmatter for ``authored_by:`` value.

    Returns the value with any surrounding YAML quotes stripped
    (e.g. ``'takumi'`` from ``authored_by: "takumi"``).
    Default when absent or file not found: ``'rebuild-spec'``.
    """
    fm = _read_frontmatter(path)
    m = _FM_AUTHORED_RE.search(fm)
    return m.group(1).strip("'\"") if m else "rebuild-spec"
FCODE_RE = re.compile(r"^F\d{3}$")
FEATURE_LIST_ROW_RE = re.compile(r"^\|\s*(F\d{3}_\w+)\s*\|")
_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")
_MAX_CAMEL = 36


def derive_slug(fcode: str, name: str) -> str:
    """Per canonical-fcode-schema.md § Slug Grammar."""
    if not FCODE_RE.match(fcode):
        raise ValueError(f"invalid fcode: {fcode!r}")
    tokens = [t for t in _NON_ALNUM.split((name or "").strip().replace("&", " And ")) if t]
    camel = "".join(t[:1].upper() + t[1:].lower() for t in tokens)[:_MAX_CAMEL]
    if not camel:
        raise ValueError(f"name yields empty slug: {name!r}")
    return f"{fcode}_{camel}"


def is_valid_slug(slug: str) -> bool:
    return bool(SLUG_RE.match(slug))

def load_canonical(plan_dir: Path) -> dict | None:
    """Read `_canonical-fcodes.json`; None if absent."""
    path = plan_dir / "artifacts" / "_canonical-fcodes.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON at {path}: {exc}") from exc

def parse_feature_list_fallback(flist_path: Path) -> list[dict]:
    """Regex-extract F### slugs from feature-list.md hierarchy table."""
    if not flist_path.is_file():
        return []
    out, seen = [], set()
    for line in flist_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = FEATURE_LIST_ROW_RE.match(line)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append({"fcode": m.group(1).split("_")[0], "slug": m.group(1), "name": "", "priority": "", "type": ""})
    return sorted(out, key=lambda f: f["fcode"])

FEATURE_FILES = ("technical-spec.md", "business-context.md", "screens.md", "edge-cases.md")


def iter_technical_specs(plan_dir: Path) -> Iterator[Path]:
    """Yield each `technical-spec.md` under `artifacts/features/*/` sorted by slug.
    Skips folders with `.pending` marker (W6 partial write — caught by W7b reviewer)."""
    root = plan_dir / "artifacts" / "features"
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "technical-spec.md").is_file() and not (child / ".pending").is_file():
                yield child / "technical-spec.md"


def iter_docs_technical_specs(project_root: Path) -> Iterator[Path]:
    """Yield each ``technical-spec.md`` under ``<project_root>/docs/features/*/`` sorted by slug.

    Mirrors ``iter_technical_specs`` semantics but targets the docs tree where takumi drafts live.
    Skips folders with a ``.pending`` marker (consistent with iter_technical_specs).

    Stage 1.5 (Phase 3) invokes validators via ``--docs-root <project_root>`` which uses this
    iterator — the existing ``plan_dir/artifacts/...`` glob does not reach ``docs/features/``.
    """
    root = project_root / "docs" / "features"
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if (child.is_dir()
                    and (child / "technical-spec.md").is_file()
                    and not (child / ".pending").is_file()):
                yield child / "technical-spec.md"


def iter_feature_dirs(plan_dir: Path) -> Iterator[Path]:
    """Yield each `artifacts/features/{slug}/` directory sorted by name.
    Yields all dirs matching SLUG_RE regardless of completeness — caller decides."""
    root = plan_dir / "artifacts" / "features"
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if child.is_dir() and SLUG_RE.match(child.name):
                yield child

def resolve_project_root(arg: str | None) -> Path:
    """CLI arg → git toplevel → CWD."""
    if arg:
        return Path(arg).resolve()
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5, check=False)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return Path.cwd().resolve()


def assert_under(child: Path, parent: Path) -> None:
    """Path-traversal guard."""
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"{child} is not under {parent}") from exc
