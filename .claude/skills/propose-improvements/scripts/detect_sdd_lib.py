"""Pure-Python helpers for propose-improvements Step 1 (SDD detection).

Authoritative implementation of the procedure described in
`claude/skills/propose-improvements/references/sdd-detection.md`. No CLI / I/O orchestration
here — see `detect_sdd.py` for the wrapper that handles stdout, idempotency,
and the atomic JSON write.

Detection rule (from sdd-detection.md):
    isSDD = true when (>= 1 PRIMARY hit) OR (>= 2 distinct SECONDARY categories).
    Otherwise false.

Signals returned mirror the schema declared in `templates/sdd-detection.md`:
    {"kind": <tag>, "path": <relpath>, "weight": 1|2|3}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# Directory names never descended during file scans.
PRUNE_DIRS: frozenset[str] = frozenset({
    "node_modules", ".venv", "venv", ".git", ".hg", ".svn",
    "dist", "build", ".next", ".nuxt", "out", "target", "vendor",
    "__pycache__", ".cache", ".pytest_cache", ".tox", ".gradle",
    ".idea", ".vscode",
})

# PRIMARY signals.
# rebuild-spec v4.0.0 promotes into layered docs/ namespaces (system/generated/features/flows),
# replacing the pre-v4 flat docs/specs/ layout.
# layout-exempt: detection sentinel — checks single-lang docs/ root; per-lang root detection deferred to a future phase
_PRIMARY_DIRS: tuple[str, ...] = (
    "specs", ".specify",
    "docs/system", "docs/generated", "docs/features", "docs/flows",
)
_PRIMARY_ROOT_FILES: tuple[str, ...] = (
    "spec.md", "SPEC.md", "specs.md", "SPECIFICATION.md",
    "specify.config.yml", "specify.yaml",
)

# SECONDARY signal #1: spec-kit filename prefixes.
_SPEC_FILENAME_PREFIXES: tuple[str, ...] = (
    "feature-", "user-story-", "us-", "fr-", "scr-", "perm-",
)

# SECONDARY signal #2: heading keyword -> emitted `kind`.
# Order matters only for kind selection; presence is what counts toward the secondary tally.
_HEADING_KEYWORD_KIND: dict[str, str] = {
    "featurelist": "feature-list",
    "userstories": "user-stories",
    "screenlist": "screen-list",
    "screenflow": "screen-list",  # screen-* artifacts share the heading-keyword bucket.
    "datamodel": "data-model",
    "systemoverview": "system-overview",
    "permissions": "permissions",
    "behaviorlogic": "behavior-logic",
    "routelist": "route-list",
}

# SECONDARY signal #3: tooling markers (anchored regex).
_TOOLING_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\btkm:rebuild-spec\b"),
    re.compile(r"\bspeckit\b"),
    re.compile(r"\bspecify\s+(init|check|run|install|plan)\b"),
    re.compile(r"\bnpx\s+specify\b"),
)
_TOOLING_SEARCH_FILES: tuple[str, ...] = (
    "package.json", "pyproject.toml", "CLAUDE.md",
)


@dataclass(frozen=True)
class Signal:
    """Evidence entry matching templates/sdd-detection.md."""
    kind: str
    path: str
    weight: int

    def to_dict(self) -> dict:
        return {"kind": self.kind, "path": self.path, "weight": self.weight}


# ---------------------------------------------------------------------------
# Primary detection
# ---------------------------------------------------------------------------

def primary_signals(repo_root: Path) -> list[Signal]:
    """Run all PRIMARY checks; return one Signal per hit."""
    hits: list[Signal] = []

    for rel in _PRIMARY_DIRS:
        d = repo_root / rel
        if d.is_dir() and _dir_has_content(d, rel):
            # layered docs/* + specs need md content; .specify accepts any file.
            hits.append(Signal(kind="specs-dir", path=f"{rel}/", weight=3))

    for fname in _PRIMARY_ROOT_FILES:
        p = repo_root / fname
        if p.is_file():
            hits.append(Signal(kind="spec-file", path=fname, weight=2))

    return hits


def _dir_has_content(d: Path, rel: str) -> bool:
    """specs/ + layered docs/* require >=1 .md file (any depth); .specify/ any file."""
    if rel == ".specify":
        return any(_iter_files(d))
    return any(_iter_md(d))


# ---------------------------------------------------------------------------
# Secondary detection
# ---------------------------------------------------------------------------

def secondary_signals(repo_root: Path) -> list[Signal]:
    """Run all SECONDARY checks; return one Signal per fired source.

    Categories (each unique hit category counts once toward classify()):
      1. spec-kit filename prefixes under docs/ or specs/
      2. spec-artifact heading keywords in .md under docs/ or specs/
      3. tooling markers in package.json / pyproject.toml / CLAUDE.md / .github/workflows/
      4. spec-kit plan dir under plans/<dir>/ with phase-*.md + plan.md
    """
    hits: list[Signal] = []
    hits.extend(_filename_prefix_signals(repo_root))
    hits.extend(_heading_keyword_signals(repo_root))
    hits.extend(_tooling_marker_signals(repo_root))
    hits.extend(_plan_dir_signals(repo_root))
    return hits


def _filename_prefix_signals(repo_root: Path) -> list[Signal]:
    out: list[Signal] = []
    for search_root in ("docs", "specs"):
        base = repo_root / search_root
        if not base.is_dir():
            continue
        for p in _iter_md(base, max_depth=6):
            name = p.name.lower()
            if any(name.startswith(prefix) for prefix in _SPEC_FILENAME_PREFIXES):
                rel = p.relative_to(repo_root).as_posix()
                out.append(Signal(kind="spec-file", path=rel, weight=1))
    return out


def _heading_keyword_signals(repo_root: Path) -> list[Signal]:
    out: list[Signal] = []
    for search_root in ("docs", "specs"):
        base = repo_root / search_root
        if not base.is_dir():
            continue
        for p in _iter_md(base, max_depth=6):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            matched = False
            for line in text.splitlines():
                if not line.startswith("#"):
                    continue
                # Strip leading #'s + spaces; match a single keyword (longest wins).
                stripped = line.lstrip("#").strip().lower().replace(" ", "")
                for kw, kind in _HEADING_KEYWORD_KIND.items():
                    if kw in stripped:
                        rel = p.relative_to(repo_root).as_posix()
                        out.append(Signal(kind=kind, path=rel, weight=1))
                        matched = True
                        break  # one keyword per heading is enough.
                if matched:
                    break  # one heading-keyword hit per file is enough.
    return out


def _tooling_marker_signals(repo_root: Path) -> list[Signal]:
    out: list[Signal] = []
    candidates = [repo_root / fn for fn in _TOOLING_SEARCH_FILES]
    workflows = repo_root / ".github" / "workflows"
    if workflows.is_dir():
        for ext in ("*.yml", "*.yaml", "*.json", "*.md"):
            candidates.extend(workflows.glob(ext))
    for p in candidates:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for marker in _TOOLING_MARKERS:
            m = marker.search(text)
            if m:
                line_no = text.count("\n", 0, m.start()) + 1
                rel = p.relative_to(repo_root).as_posix()
                out.append(Signal(kind="spec-file", path=f"{rel}:{line_no}", weight=1))
                break  # one marker hit per file is enough.
    return out


def _plan_dir_signals(repo_root: Path) -> list[Signal]:
    """Look for plans/<dir>/{phase-*.md AND plan.md} where plan.md mentions
    >=2 distinct spec-kit keywords. Bar avoids generic project-plan dirs.
    """
    plans = repo_root / "plans"
    if not plans.is_dir():
        return []
    out: list[Signal] = []
    keywords = ("featurelist", "userstories", "screenlist", "screenflow",
                "datamodel", "feature-spec", "routelist", "backgroundlogic", "permissions")
    for child in plans.iterdir():
        if not child.is_dir() or child.name in PRUNE_DIRS:
            continue
        plan_md = child / "plan.md"
        if not plan_md.is_file():
            continue
        # Need at least one phase-*.md sibling.
        if not any(child.glob("phase-*.md")):
            continue
        try:
            text = plan_md.read_text(encoding="utf-8", errors="ignore").lower().replace(" ", "")
        except OSError:
            continue
        distinct = {kw for kw in keywords if kw in text}
        if len(distinct) >= 2:
            rel = plan_md.relative_to(repo_root).as_posix()
            out.append(Signal(kind="spec-file", path=rel, weight=1))
    return out


# ---------------------------------------------------------------------------
# Classification + specsRoot
# ---------------------------------------------------------------------------

def classify(primary: Iterable[Signal], secondary: Iterable[Signal]) -> bool:
    """Apply the documented rule: >=1 PRIMARY OR >=2 distinct SECONDARY categories.

    "Distinct category" = unique generator function. We count by checking which
    of the four secondary helpers contributed. Since each helper emits at most
    one entry per source-file (filename) / one tooling marker / one plan-dir
    hit, we approximate categories by `kind` buckets: spec-file from filenames,
    heading kinds (any of feature-list, user-stories, ...), spec-file from
    tooling, spec-file from plan-dir. This is approximate; the canonical
    interpretation is `categories = {1: filename, 2: heading, 3: tooling, 4: plan-dir}`
    fired-or-not, computed by callers via the secondary_categories() helper.
    """
    primary_list = list(primary)
    if primary_list:
        return True
    return secondary_categories(secondary) >= 2


def secondary_categories(secondary: Iterable[Signal]) -> int:
    """Count the number of distinct SECONDARY categories that produced hits."""
    fired_filename = False
    fired_heading = False
    fired_tooling = False
    fired_plan_dir = False
    heading_kinds = set(_HEADING_KEYWORD_KIND.values())
    for sig in secondary:
        # plan-dir: kind=spec-file AND path startswith plans/
        if sig.kind == "spec-file" and sig.path.startswith("plans/"):
            fired_plan_dir = True
        # tooling: kind=spec-file AND path contains ":" (we appended :line)
        elif sig.kind == "spec-file" and ":" in sig.path:
            fired_tooling = True
        # filename-prefix: kind=spec-file AND path startswith docs/ or specs/
        elif sig.kind == "spec-file" and (sig.path.startswith("docs/") or sig.path.startswith("specs/")):
            fired_filename = True
        elif sig.kind in heading_kinds:
            fired_heading = True
    return sum([fired_filename, fired_heading, fired_tooling, fired_plan_dir])


def resolve_specs_root(repo_root: Path) -> str:
    """Pick the first present + content-bearing directory; else empty string."""
    if (repo_root / "specs").is_dir() and any(_iter_md(repo_root / "specs")):
        return "specs/"
    for layered in ("system", "generated", "features", "flows"):
        d = repo_root / "docs" / layered
        if d.is_dir() and any(_iter_md(d)):
            return "docs/"
    if (repo_root / ".specify").is_dir() and any(_iter_files(repo_root / ".specify")):
        return ".specify/"
    return ""


# ---------------------------------------------------------------------------
# User-supplied spec folder override
# ---------------------------------------------------------------------------

def verify_spec_folder(repo_root: Path, spec_folder: str) -> tuple[bool, str]:
    """Verify a user-supplied spec folder relative to repo_root.

    Returns ``(is_valid, error_reason)``. On success, ``error_reason`` is empty.
    Rules (security + content):
      1. Path must be non-empty, relative, free of ``..`` and null bytes,
         and the resolved location must stay inside ``repo_root``.
      2. Path must exist as a directory.
      3. Directory must contain ≥1 ``*.md`` file (any depth, prune-respecting).
    """
    if not spec_folder or "\x00" in spec_folder:
        return False, "spec folder path is empty or contains null bytes"

    candidate = Path(spec_folder)
    if candidate.is_absolute():
        return False, f"spec folder must be relative to the repo root (got: {spec_folder})"
    if ".." in candidate.parts:
        return False, f"spec folder must not contain '..' (got: {spec_folder})"

    repo_resolved = repo_root.resolve()
    folder_resolved = (repo_resolved / candidate).resolve(strict=False)
    try:
        folder_resolved.relative_to(repo_resolved)
    except ValueError:
        return False, f"spec folder escapes repository root: {spec_folder}"

    if not folder_resolved.is_dir():
        return False, f"spec folder does not exist or is not a directory: {spec_folder}"

    # Require ≥1 .md whose resolved path stays inside repo_resolved.
    # _iter_md follows symlinks via is_dir()/is_file(); re-resolve each match
    # so an internal symlink pointing out of the repo cannot satisfy the bar.
    for md in _iter_md(folder_resolved):
        try:
            md.resolve().relative_to(repo_resolved)
        except ValueError:
            continue
        return True, ""

    return False, f"spec folder contains no in-repo .md files: {spec_folder}"


def normalize_spec_folder(spec_folder: str) -> str:
    """Normalize a user-supplied spec folder to the ``<path>/`` form used in JSON output."""
    return spec_folder.replace("\\", "/").rstrip("/") + "/"


# ---------------------------------------------------------------------------
# Pruned iteration
# ---------------------------------------------------------------------------

def _iter_files(root: Path, max_depth: int = 6):
    """Yield files under root, skipping PRUNE_DIRS at any depth."""
    yield from _walk(root, max_depth, file_filter=lambda p: True)


def _iter_md(root: Path, max_depth: int = 6):
    """Yield *.md files under root, skipping PRUNE_DIRS."""
    yield from _walk(root, max_depth, file_filter=lambda p: p.suffix.lower() == ".md")


def _walk(root: Path, max_depth: int, *, file_filter):
    if not root.is_dir():
        return
    root_depth = len(root.parts)
    stack: list[Path] = [root]
    while stack:
        cur = stack.pop()
        try:
            entries = list(cur.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_dir():
                if e.name in PRUNE_DIRS:
                    continue
                if len(e.parts) - root_depth >= max_depth:
                    continue
                stack.append(e)
            elif e.is_file() and file_filter(e):
                yield e
