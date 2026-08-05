#!/usr/bin/env python3
"""List the kensan briefing/deep-dive reports inside a time window, so the rollup
mode reads only what it needs. Reports are named `YYMMDD-<slug>-(briefing|deepdive).md`.
Stdlib only; no network.

Usage:
  rollup_index.py --dir ~/.claude/kensan/briefings --since 7
  rollup_index.py --dir ~/.claude/kensan/briefings --from 260601 --to 260623
"""

import argparse
import glob
import json
import os
import re
from datetime import datetime, timedelta, timezone

_NAME = re.compile(r"^(\d{6})-(.+?)-(briefing|deepdive)\.md$")


def _parse_yymmdd(s):
    try:
        return datetime.strptime("20" + s, "%Y%m%d").date()
    except ValueError:
        return None


def _title(path):
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Index kensan reports in a window.")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--since", type=int, default=None, help="lookback in days")
    ap.add_argument("--from", dest="from_", default=None, help="YYMMDD")
    ap.add_argument("--to", default=None, help="YYMMDD")
    args = ap.parse_args(argv)

    today = datetime.now(timezone.utc).date()
    if args.from_ or args.to:
        start = _parse_yymmdd(args.from_) if args.from_ else today - timedelta(days=3650)
        end = _parse_yymmdd(args.to) if args.to else today
        if args.from_ and start is None:
            ap.error("--from must be YYMMDD (e.g. 260601)")
        if args.to and end is None:
            ap.error("--to must be YYMMDD (e.g. 260623)")
    else:
        end = today
        start = today - timedelta(days=max(1, args.since if args.since is not None else 7))

    items = []
    for path in sorted(glob.glob(os.path.join(os.path.expanduser(args.dir), "*.md"))):
        m = _NAME.match(os.path.basename(path))
        if not m:
            continue
        d = _parse_yymmdd(m.group(1))
        if d is None or d < start or d > end:
            continue
        items.append({"path": path, "date": d.isoformat(), "kind": m.group(3),
                      "slug": m.group(2), "title": _title(path)})

    items.sort(key=lambda x: x["date"])
    out = {"from": start.isoformat(), "to": end.isoformat(),
           "count": len(items), "briefings": sum(1 for i in items if i["kind"] == "briefing"),
           "deepdives": sum(1 for i in items if i["kind"] == "deepdive"), "items": items}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
