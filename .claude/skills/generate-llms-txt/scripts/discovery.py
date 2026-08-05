#!/usr/bin/env python3
"""Discovery + docs-first ladder for build-llms-skeleton — filesystem traversal, pure stdlib.
Pure markdown parsers live in md_parse.py. Produces per-file metadata: title, section,
and a deterministic baseline description the LLM enriches.
"""
import json
import re
from pathlib import Path

from md_parse import extract_description, h1_title, project_field, read_text

CANONICAL_DIRS = ("system", "generated", "features", "flows")  # rebuild-spec (T1) sentinels
# A real OpenAPI 3.x / Swagger 2.0 document declares its version near the top.
_SPEC_VERSION = re.compile(r'["\']?(openapi["\']?\s*:\s*["\']?3\.|swagger["\']?\s*:\s*["\']?2\.)')

MD_EXT = {".md", ".mdx"}
# Not product docs — excluded from discovery (session logs, deps, test fixtures, build output).
EXCLUDE_DIRS = {"node_modules", "journals", ".git", "tests", "test", "fixtures",
                "vendor", "dist", "build", "__pycache__", ".venv"}
# Section display order in llms.txt (T1 uses Overview/Features/API/Flows; T2 fills the rest).
SECTION_ORDER = ["Overview", "Getting Started", "Features", "Guides", "API",
                 "Flows", "Configuration", "Deployment", "Documentation", "Optional"]

# Keyword → section, checked against path parts + filename stem. First match wins.
_SECTION_GROUPS = {
    "Getting Started": ("getting-started", "quickstart", "quick-start", "setup", "install", "installation"),
    "Guides": ("guide", "guides", "tutorial", "tutorials"),
    "API": ("api", "api-reference", "reference"),
    "Configuration": ("config", "configuration", "settings"),
    "Deployment": ("deploy", "deployment", "hosting"),
    "Overview": ("architecture", "overview", "system"),
    "Features": ("features",),
    "Flows": ("flows",),
    "Optional": ("changelog", "faq", "migration", "contributing", "troubleshoot",
                 "troubleshooting", "decisions", "adr"),
}
SECTION_MAP = {kw: sec for sec, kws in _SECTION_GROUPS.items() for kw in kws}


def within(fp: Path, source: Path) -> bool:
    """True if fp's REAL path stays under source — blocks symlinks escaping the repo."""
    try:
        return fp.resolve().is_relative_to(source.resolve())
    except (OSError, ValueError):
        return False


def docs_root(source: Path, lang: str) -> Path:
    """Mode-aware docs root: use docs/<lang> if it exists, else docs/."""
    if lang and (source / "docs" / lang).is_dir():
        return source / "docs" / lang
    return source / "docs"


def _lang_has_content(source: Path, lang: str) -> bool:
    """docs/<lang> exists AND holds at least one non-excluded markdown file."""
    d = source / "docs" / lang
    if not d.is_dir():
        return False
    return any(fp.suffix in MD_EXT and not any(p in EXCLUDE_DIRS for p in fp.parts)
               for fp in d.rglob("*"))


def actual_lang(source: Path, lang: str) -> str:
    """The language actually used: the requested one only if docs/<lang> has usable content,
    else 'default' (an empty localized dir is a fallback, not a real localized output)."""
    return lang if (lang and _lang_has_content(source, lang)) else "default"


def safe_read(fp: Path, source: Path) -> str:
    """read_text, but only for a real regular file whose path stays under source."""
    return read_text(fp) if (fp.is_file() and within(fp, source)) else ""


def section_for(rel: Path) -> str:
    """Assign a section by rebuild-spec layout + keyword heuristics (SECTION_MAP)."""
    name = rel.stem.lower()
    if "feature-list" in name or "api-map" in name or "route-list" in name:
        return "Features" if "feature" in name else "API"
    for token in [p.lower() for p in rel.parts] + [name]:
        if token in SECTION_MAP:
            return SECTION_MAP[token]
    return "Documentation"


def _entry(fp: Path, rel: str, content: str, section: str) -> dict:
    return {"rel": rel, "abs": str(fp), "title": h1_title(content, fp),
            "desc": extract_description(content), "section": section}


def collect_markdown(root: Path, source: Path):
    """Per-file entries for every .md under root (skip hidden/excluded/empty/escaping-symlink).
    Link paths are relative to `source` (repo root) so they stay valid in an llms.txt written there."""
    out = []
    if not root.is_dir():
        return out
    for fp in sorted(root.rglob("*")):
        if fp.suffix not in MD_EXT or fp.name.startswith("."):
            continue
        if any(part.startswith(".") or part in EXCLUDE_DIRS for part in fp.parts):
            continue
        if not within(fp, source):  # symlink pointing outside the repo
            continue
        content = read_text(fp)
        if not content.strip():
            continue
        out.append(_entry(fp, str(fp.relative_to(source)), content, section_for(fp.relative_to(source))))
    return out


def openapi_specs(source: Path):
    """ALL real OpenAPI/Swagger specs under source, sorted, deduped by resolved path.
    A candidate is a regular file whose name starts with openapi/swagger (any case) AND whose head
    declares an openapi 3.x / swagger 2.0 version — so config files (swagger-config.json) and
    directories are rejected, and a multi-service monorepo keeps every contract, not just one."""
    seen, out = set(), []
    for fp in source.rglob("*"):
        if fp.suffix.lower() not in (".yaml", ".yml", ".json") or not fp.is_file():
            continue
        rel = fp.relative_to(source)
        if any(p in EXCLUDE_DIRS for p in rel.parts) or not within(fp, source):
            continue
        if not fp.stem.lower().startswith(("openapi", "swagger")):
            continue
        real = fp.resolve()
        if real in seen or not _SPEC_VERSION.search(read_text(fp)[:4000]):
            continue
        seen.add(real)
        out.append(rel)
    return sorted(out, key=lambda r: (len(r.parts), str(r)))


def openapi_entries(source: Path):
    """One API-section entry per spec — supplemental, so a contract is never dropped just because
    docs/README also exist. Title is disambiguated by location in multi-spec repos."""
    entries = []
    for rel in openapi_specs(source):
        loc = "" if len(rel.parts) == 1 else f" ({rel.parent})"
        entries.append({"rel": str(rel), "abs": str(source / rel), "title": f"API Reference{loc}",
                        "desc": "OpenAPI specification for the service.", "section": "API"})
    return entries


def _with_openapi(files, source: Path):
    """Append every OpenAPI entry not already among the collected files."""
    have = {f["rel"] for f in files}
    files.extend(e for e in openapi_entries(source) if e["rel"] not in have)
    return files


def _canonical_content(files) -> bool:
    """True if any collected doc is a NON-EMPTY markdown inside a rebuild-spec canonical dir — the
    real T1 signal. An empty docs/system/ dir must NOT promote loose docs to T1."""
    return any(any(p in CANONICAL_DIRS for p in Path(f["rel"]).parts) for f in files)


def resolve_tier(source: Path, lang: str):
    """Docs-first ladder. Returns (tier, root, files). OpenAPI is folded in as supplemental on
    T1/T2 (not only the T3 fallback); T1 requires real content in the canonical dirs."""
    root = docs_root(source, lang)
    files = collect_markdown(root, source)
    if _canonical_content(files):  # genuine rebuild-spec output
        return 1, root, _with_openapi(files, source)
    # T2: loose docs + (language-neutral) README — not mixed into a localized docs/<lang> output.
    if actual_lang(source, lang) == "default":
        readme = next((source / n for n in ("README.md", "readme.md", "Readme.md")
                       if (source / n).is_file() and within(source / n, source)), None)
        if readme:
            files.insert(0, _entry(readme, readme.name, read_text(readme), "Overview"))
    if files:
        return 2, root, _with_openapi(files, source)
    entries = openapi_entries(source)  # T3: OpenAPI is the only source
    if entries:
        return 3, root, entries
    return 4, root, []  # T4 (deep scan) is handled by SKILL.md via LLM agents, not the script


def product_name(source: Path, lang: str) -> str:
    """Product name: overview **Project** field → its H1 (unless 'System Overview') → package.json → dir.
    All filesystem reads go through safe_read so an escaping symlink cannot leak an outside name."""
    c = safe_read(docs_root(source, lang) / "system" / "overview.md", source)
    if c:
        name = project_field(c)
        if name:
            return name
        h1 = h1_title(c, Path("overview.md"))
        if h1 and h1.lower() != "system overview":
            return h1
    pkg = safe_read(source / "package.json", source)
    if pkg:
        try:
            return json.loads(pkg).get("name") or source.resolve().name
        except json.JSONDecodeError:
            pass
    return source.resolve().name
