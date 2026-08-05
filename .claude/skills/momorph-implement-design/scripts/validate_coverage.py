"""Validate coverage between assets.md and source code.

Scan the code dir → find comment markers `mm:{nodeId}` (universal across stacks) →
ensure every nodeId in assets.md appears at least once.

Recognized markers (comment-only, no runtime leak):
- `// mm:1:1`              (line comment — TS/JS/Vue/Svelte/Dart/Swift/Kotlin)
- `{/* mm:1:1 */}`         (JSX/TSX inline block)
- `/* mm:1:1 */`           (JS/CSS block)
- `<!-- mm:1:1 -->`        (HTML/Vue template)

Usage:
  python3 validate_coverage.py --assets data/assets.md --code src/components/screens/{slug}

Exit code: 0 if every asset is covered, 2 if any asset is missing.
"""

import argparse
import os
import re
import sys
from typing import Set

# 4 capture groups; whichever matches → take the nodeId from that group
MM_ID_RE = re.compile(
    r'//\s*mm:([\w:;.-]+)'                          # // mm:1:1
    r'|\{/\*\s*mm:([\w:;.-]+)'                      # {/* mm:1:1 */} (JSX) — open only, ID stops at non-id chars
    r'|/\*\s*mm:([\w:;.-]+)'                        # /* mm:1:1 */
    r'|<!--\s*mm:([\w:;.-]+)'                       # <!-- mm:1:1 -->
)
ASSET_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.MULTILINE)
CODE_EXTS = (".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte", ".dart", ".swift",
             ".kt", ".html", ".htm")


def collect_code_ids(code_dir: str) -> Set[str]:
    ids = set()
    for root, _, files in os.walk(code_dir):
        for fn in files:
            if not fn.endswith(CODE_EXTS):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for m in MM_ID_RE.finditer(f.read()):
                        ids.add(next(g for g in m.groups() if g))
            except OSError:
                pass
    return ids


def collect_asset_ids(assets_md: str) -> Set[str]:
    if not os.path.isfile(assets_md):
        return set()
    with open(assets_md, "r", encoding="utf-8") as f:
        content = f.read()
    ids = set()
    for m in ASSET_ROW_RE.finditer(content):
        nid = m.group(1).strip()
        if nid.lower() == "node id":  # skip header row
            continue
        ids.add(nid)
    return ids


def main():
    ap = argparse.ArgumentParser(description="Check assets.md coverage in code.")
    ap.add_argument("--assets", required=True, help="data/assets.md")
    ap.add_argument("--code", required=True, help="Component code directory")
    args = ap.parse_args()

    code_ids = collect_code_ids(args.code)
    asset_ids = collect_asset_ids(args.assets)
    missing = sorted(asset_ids - code_ids)

    print(f"Code marker IDs:     {len(code_ids)}")
    print(f"Assets to cover:     {len(asset_ids)}")

    if missing:
        print(f"\n❌ {len(missing)} assets not yet used in code:")
        for nid in missing[:30]:
            print(f"   - {nid}")
        if len(missing) > 30:
            print(f"   ... and {len(missing) - 30} more assets")
    else:
        print(f"\n✅ Every asset in assets.md appears in code.")

    sys.exit(2 if missing else 0)


if __name__ == "__main__":
    main()
