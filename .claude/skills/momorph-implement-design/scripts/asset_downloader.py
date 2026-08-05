"""Parallel media-asset downloader for `get_media_files` output (uses urllib).

Main input: JSON map from `get_media_files`. Supports:
- `{nodeId: url}` (simple)
- `{nodeId: {url|downloadUrl|href|link|src: ..., name?: ...}}` (with name)

Optional: `--names FILE` points at a JSON `{nodeId: name}` (e.g. from get_overview /
list_media_nodes). With names → file is named after the node name → 2 nodes sharing
the same name (same mm_media_*) → 1 physical file → DEDUP, downloaded once.

Output:
- Asset files inside --out (deduplicated)
- `assets.md` mapping `nodeId → file path` (multiple nodeIds may point to the same file)

Usage:
  python3 asset_downloader.py media_files.json --out data/assets
  python3 asset_downloader.py media_files.json --names data/node_names.json \\
    --out data/assets --plan-only --manifest data/assets.md
"""

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from typing import Any


SAFE = re.compile(r"[^A-Za-z0-9._-]+")
EXT_RE = re.compile(r"\.(png|jpe?g|svg|webp|gif)$", re.IGNORECASE)
MM_PREFIX_RE = re.compile(r"^mm[_-]?media[_-]?", re.IGNORECASE)


def filename_from_url(url: str) -> str:
    """Extract a filename from a presigned S3 URL."""
    try:
        path = urllib.parse.urlparse(url).path
        name = urllib.parse.unquote(os.path.basename(path))
        name = SAFE.sub("_", name).strip("_")
        return name
    except Exception:
        return ""


def ext_from_url(url: str) -> str:
    """Infer extension from URL path. Default `.bin`."""
    name = filename_from_url(url)
    m = EXT_RE.search(name) if name else None
    if not m:
        return ".bin"
    ext = m.group(1).lower()
    return "." + ("jpg" if ext == "jpeg" else ext)


def slug_from_name(name: str) -> str:
    """Sanitize the node name into a slug. Strip the `mm_media_` prefix."""
    if not name:
        return ""
    base = MM_PREFIX_RE.sub("", name)
    base = SAFE.sub("_", base).strip("_")
    return base


def safe_filename(node_id: str, url: str, name: str = "") -> str:
    """Priority: node name (after stripping mm_media_) → URL filename → nodeId."""
    slug = slug_from_name(name)
    if slug:
        return slug + ext_from_url(url)
    url_name = filename_from_url(url)
    if url_name and EXT_RE.search(url_name):
        return url_name
    base = SAFE.sub("_", node_id).strip("_") or "asset"
    return base + ext_from_url(url)


def normalize_pairs(data: Any, names: dict) -> list:
    """Return list[(nodeId, url, name)]. Merges name from the value dict or the names map."""
    pairs = []
    if not isinstance(data, dict):
        return pairs
    for nid, val in data.items():
        url = ""
        inline_name = ""
        if isinstance(val, str) and val.startswith("http"):
            url = val
        elif isinstance(val, dict):
            for k in ("url", "downloadUrl", "href", "link", "src"):
                v = val.get(k)
                if isinstance(v, str) and v.startswith("http"):
                    url = v
                    break
            inline_name = val.get("name") or val.get("nodeName") or ""
        if not url:
            continue
        name = inline_name or names.get(str(nid), "")
        pairs.append((str(nid), url, name))
    return pairs


def assign_filenames(pairs: list, out_dir: str) -> list:
    """Pre-compute filenames. Same filename = same dest (DEDUP).
    Two nodes sharing the same name → one physical file.
    """
    name_to_dest: dict = {}
    assigned = []
    for nid, url, name in pairs:
        fname = safe_filename(nid, url, name)
        if fname in name_to_dest:
            dest = name_to_dest[fname]
        else:
            dest = os.path.join(out_dir, fname)
            name_to_dest[fname] = dest
        assigned.append((nid, url, fname, dest))
    return assigned


def unique_downloads(assigned: list) -> list:
    """Drop duplicate destinations — download each dest once. Keep the first URL seen."""
    seen = set()
    unique = []
    for nid, url, fname, dest in assigned:
        if dest in seen:
            continue
        seen.add(dest)
        unique.append((nid, url, fname, dest))
    return unique


def download_one(node_id: str, url: str, fname: str, dest: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "momorph-ui/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        return {"ok": True, "dest": dest, "url": url}
    except Exception as e:
        return {"ok": False, "dest": dest, "url": url, "error": str(e)[:200]}


def write_manifest(path: str, assigned: list, results: list = None,
                   code_prefix: str = "") -> None:
    """Write assets.md. If results are provided → include a Status column. Dedup is
    reflected by multiple nodeIds pointing to the same file path.

    `code_prefix`: if set → manifest path = `{code_prefix}/{filename}` (import-ready,
    e.g. `/assets/momorph/home/logo.png` for Next.js public). If unset → relative
    to the manifest directory.
    """
    base = os.path.dirname(os.path.abspath(path))
    dest_status: dict = {}
    if results is not None:
        for r in results:
            dest_status[r.get("dest")] = r

    intro = ("Mapping `nodeId → asset file path`. Multiple nodeIds may point to "
             "the same file (dedup by node name). The path is a PLAN — the file "
             "may still be downloading in the background.")
    if code_prefix:
        intro += f" Paths are **import-ready** (prefix `{code_prefix}`)."
    lines = ["# Asset Manifest", "", intro, ""]
    has_status = results is not None
    if has_status:
        lines += ["| Node ID | File path | Filename | Status |",
                  "|---------|-----------|----------|--------|"]
    else:
        lines += ["| Node ID | File path | Filename |",
                  "|---------|-----------|----------|"]
    prefix = code_prefix.rstrip("/") if code_prefix else ""
    for nid, _url, fname, dest in sorted(assigned, key=lambda x: x[0]):
        rel = (f"{prefix}/{fname}" if prefix
               else os.path.relpath(os.path.abspath(dest), base))
        if has_status:
            r = dest_status.get(dest)
            if r and r.get("ok"):
                st = "✓"
            elif r:
                st = f"✗ {r.get('error', 'failed')[:60]}"
            else:
                st = "…"
            lines.append(f"| `{nid}` | `{rel}` | `{fname}` | {st} |")
        else:
            lines.append(f"| `{nid}` | `{rel}` | `{fname}` |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def load_names(path: str) -> dict:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}
    except Exception as e:
        print(f"Warn: cannot read --names {path}: {e}", file=sys.stderr)
    return {}


def main():
    ap = argparse.ArgumentParser(
        description="Parallel media-asset downloader, dedup by node name.")
    ap.add_argument("input", help="JSON file from get_media_files")
    ap.add_argument("--out", required=True, help="Destination directory for files")
    ap.add_argument("--workers", type=int, default=8,
                    help="Parallel workers (default 8)")
    ap.add_argument("--manifest", help="Path of assets.md (default: <out>/../assets.md)")
    ap.add_argument("--names", help="JSON `{nodeId: name}` for name-based dedup")
    ap.add_argument("--code-path-prefix",
                    help="Prefix for manifest paths (e.g. /assets/momorph/home). "
                         "When set → manifest = '<prefix>/<filename>' (import-ready). "
                         "When unset → relative to manifest directory.")
    ap.add_argument("--plan-only", action="store_true",
                    help="Generate manifest only, DO NOT download files.")
    args = ap.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    names = load_names(args.names)
    pairs = normalize_pairs(data, names)
    if not pairs:
        print("No nodeId→url pairs found in input.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    assigned = assign_filenames(pairs, args.out)
    manifest_path = args.manifest or os.path.join(
        os.path.dirname(os.path.abspath(args.out)), "assets.md")

    write_manifest(manifest_path, assigned, code_prefix=args.code_path_prefix or "")
    n_unique = len({dest for _, _, _, dest in assigned})
    print(f"Manifest (planned) → {manifest_path}  ({len(assigned)} nodes → "
          f"{n_unique} unique files)", file=sys.stderr)

    if args.plan_only:
        return

    unique = unique_downloads(assigned)
    results = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(download_one, nid, url, fname, dest)
                   for nid, url, fname, dest in unique]
        for fut in cf.as_completed(futures):
            results.append(fut.result())

    ok = [r for r in results if r.get("ok")]
    fail = [r for r in results if not r.get("ok")]
    print(f"Downloaded {len(ok)}/{len(results)} unique → {args.out}", file=sys.stderr)
    if fail:
        print(f"Failed: {len(fail)}", file=sys.stderr)
        for r in fail[:10]:
            print(f"  - {r}", file=sys.stderr)

    write_manifest(manifest_path, assigned, results,
                   code_prefix=args.code_path_prefix or "")
    sys.exit(0 if not fail else 2)


if __name__ == "__main__":
    main()
