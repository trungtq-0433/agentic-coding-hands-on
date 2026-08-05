#!/usr/bin/env python3
"""Build the SKELETON llms.txt (llmstxt.org standard) for a project — the mechanical, deterministic part.

This is NOT the final output. The script only does the repeatable work:
  - discover files via the docs-first ladder (T1 rebuild-spec → T2 docs/README → T3 OpenAPI),
  - build the section frame + links carrying deterministic baseline descriptions,
  - optionally build the full inlined body (--full),
  - print a manifest JSON for the LLM layer to read next.

Output is written to STAGING files (`.llms.txt.work`, `.llms-full.txt.work`) — never straight to the
final `llms.txt`. The SKILL.md LLM step enriches + validates the staging file, then writes the final
artifact. So a crashed/aborted run never clobbers a previously good llms.txt with a `<TODO>` skeleton.
Pure stdlib. Discovery/parsing split into discovery.py / md_parse.py.

Usage:
  python3 build-llms-skeleton.py --source <repo> [--lang vi|ja|en] [--output <dir>]
                                 [--base-url <url>] [--full] [--name <product>] [--manifest -]
"""
import argparse
import json
import os
import sys
from pathlib import Path, PurePosixPath

from discovery import SECTION_ORDER, actual_lang, openapi_specs, product_name, read_text, resolve_tier

STAGE_SKELETON = ".llms.txt.work"
STAGE_FULL = ".llms-full.txt.work"


def atomic_write(path: Path, text: str) -> None:
    """Write via a per-process temp file + os.replace so an interrupted write never leaves a
    truncated file and concurrent writers don't clobber each other's temp."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def promote(out: Path, want_full: bool) -> None:
    """Publish enriched staging files to their final artifacts atomically, both-or-report.
    Called by the SKILL.md step 6 ONLY after the staging file passed the validation gate — so a
    good llms.txt is never overwritten by an unfinished skeleton, and --full never deletes staging
    without producing llms-full.txt."""
    pairs = [(out / STAGE_SKELETON, out / "llms.txt")]
    if want_full:
        pairs.append((out / STAGE_FULL, out / "llms-full.txt"))
    missing = [str(s) for s, _ in pairs if not s.is_file()]
    if missing:
        print(f"Error: staging file(s) missing, refusing to promote: {missing}", file=sys.stderr)
        sys.exit(1)
    for stage, final in pairs:          # each os.replace is atomic; do skeleton first, then full
        os.replace(stage, final)
    print("promoted: " + ", ".join(str(f) for _, f in pairs))


def build_url(rel: str, base_url: str) -> str:
    """Link target: repo-relative path, or an absolute web URL when --base-url is set
    (web routes usually drop the doc extension)."""
    if not base_url:
        return rel
    path = PurePosixPath(rel)
    if path.suffix in (".md", ".mdx"):
        path = path.with_suffix("")
    return f"{base_url.rstrip('/')}/{path}"


def inline_body(content: str) -> str:
    """Prepare a doc for inlining under `### {title}`: drop YAML frontmatter and the leading H1,
    then demote every remaining heading by two levels (fence-aware) so the inlined outline nests
    correctly instead of colliding with the wrapper headings."""
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":                      # strip top frontmatter block
        close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if close is not None:
            lines = lines[close + 1:]
    out, in_fence, h1_dropped = [], False, False
    for line in lines:
        st = line.lstrip()
        if st.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        m = None if in_fence else _heading_len(st)
        if m:
            if m == 1 and not h1_dropped:                        # the leading H1 becomes the ### title
                h1_dropped = True
                continue
            out.append("#" * min(m + 2, 6) + st[m:])
            continue
        out.append(line)
    return "\n".join(out).strip()


def _heading_len(stripped: str) -> int:
    """Number of leading '#' if the line is an ATX heading (`# ` … `###### `), else 0."""
    n = len(stripped) - len(stripped.lstrip("#"))
    return n if 1 <= n <= 6 and stripped[n:n + 1] == " " else 0


def _grouped(files):
    groups = {}
    for f in files:
        groups.setdefault(f["section"], []).append(f)
    return groups


def build_skeleton(name: str, files, base_url: str) -> str:
    """The llms.txt frame: H1 + blockquote placeholder + sections with links carrying a
    deterministic baseline description (`<TODO desc>` only where extraction found nothing)."""
    groups = _grouped(files)
    lines = [f"# {name}", "", "> <TODO: one or two sentences — what the product is, who it's for, its core value>", ""]
    for sec in SECTION_ORDER:
        if sec not in groups:
            continue
        lines += [f"## {sec}", ""]
        for f in groups[sec]:
            lines.append(f"- [{f['title']}]({build_url(f['rel'], base_url)}): {f.get('desc') or '<TODO desc>'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_full(name: str, files) -> str:
    """llms-full.txt: H1 + blockquote placeholder + each doc's content inlined by section."""
    groups = _grouped(files)
    lines = [f"# {name}", "", "> <TODO: one or two sentences — what the product is, who it's for, its core value>", ""]
    for sec in SECTION_ORDER:
        if sec not in groups:
            continue
        lines += [f"## {sec}", ""]
        for f in groups[sec]:
            lines += [f"### {f['title']}", "", inline_body(read_text(Path(f["abs"]))), ""]
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Build the llms.txt skeleton + manifest (deterministic)")
    ap.add_argument("--source", default=".", help="Project repo (default: cwd)")
    ap.add_argument("--lang", default="", help="Docs language (vi|ja|en) → docs/<lang> if present")
    ap.add_argument("--output", default=".", help="Directory for the final + staging files (default: cwd)")
    ap.add_argument("--base-url", default="", help="Absolute base URL for links (web-hosted llms.txt)")
    ap.add_argument("--full", action="store_true", help="Also stage llms-full.txt with inlined content")
    ap.add_argument("--name", default="", help="Override the auto-detected product name")
    ap.add_argument("--manifest", default="-", help="Manifest JSON path, '-' = stdout")
    ap.add_argument("--promote", action="store_true",
                    help="Atomically publish validated staging files to final artifacts (run after enrichment)")
    args = ap.parse_args()

    if args.promote:  # step 6: publish staging -> final, no discovery needed
        promote(Path(args.output).resolve(), args.full)
        return

    source = Path(args.source).resolve()
    if not source.is_dir():
        print(f"Error: '{source}' is not a directory", file=sys.stderr)
        sys.exit(1)

    tier, root, files = resolve_tier(source, args.lang)
    name = args.name or product_name(source, args.lang)
    used_lang = actual_lang(source, args.lang)
    out = Path(args.output).resolve()
    manifest = {
        "tier": tier,
        "requested_lang": args.lang or "default",
        "actual_lang": used_lang,
        "lang_fallback": bool(args.lang) and used_lang == "default",
        "product_name": name,
        "base_url": args.base_url or None,
        "openapi_count": len(openapi_specs(source)),
        "docs_root": str(root),
        "final_path": str(out / "llms.txt"),
        "files": files,
    }
    if manifest["lang_fallback"]:
        manifest["warning"] = (f"Requested --lang {args.lang} but docs/{args.lang} is absent; "
                               f"content came from the default docs root. Report actual_lang, not the request.")

    if tier == 4:
        manifest["note"] = "T1-T3 empty. Needs --deep (LLM agents) or return the rebuild-spec advisory."
    else:
        out.mkdir(parents=True, exist_ok=True)
        atomic_write(out / STAGE_SKELETON, build_skeleton(name, files, args.base_url))
        manifest["skeleton_path"] = str(out / STAGE_SKELETON)
        if args.full:
            atomic_write(out / STAGE_FULL, build_full(name, files))
            manifest["full_staging_path"] = str(out / STAGE_FULL)
            manifest["final_full_path"] = str(out / "llms-full.txt")

    payload = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.manifest == "-":
        print(payload)
    else:
        Path(args.manifest).write_text(payload, encoding="utf-8")
        print(f"manifest -> {args.manifest}")


if __name__ == "__main__":
    main()
