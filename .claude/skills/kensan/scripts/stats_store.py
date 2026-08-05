#!/usr/bin/env python3
"""Persist + aggregate per-run collection provenance (the "crawled from" data).

`write`   — turn a collect output's `_provenance` into a dated stats file
            `~/.claude/kensan/stats/YYMMDD-<watchlist>.json` (same scope+day overwrites; latest wins).
`aggregate` — merge every stats file in a window into one provenance summary for the rollup.
Stdlib only; no network.

Usage:
  stats_store.py write --collect collect.json --out stats.json [--watchlist NAME] [--date YYMMDD]
  stats_store.py aggregate --dir ~/.claude/kensan/stats [--since N | --from YYMMDD --to YYMMDD]
"""

import argparse
import glob
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone

_NAME = re.compile(r"^(\d{6})-(.+)\.json$")


def _yymmdd(s):
    try:
        return datetime.strptime("20" + s, "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def _atomic_write(path, obj):
    p = os.path.expanduser(path)
    d = os.path.dirname(p) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def cmd_write(args):
    with open(os.path.expanduser(args.collect), encoding="utf-8") as fh:
        data = json.load(fh)
    prov = data.get("_provenance", {"by_type": {}, "sources": []})
    today = datetime.now(timezone.utc).date().isoformat()
    stats = {
        "date": (_yymmdd(args.date).isoformat() if args.date and _yymmdd(args.date) else today),
        "watchlist": args.watchlist or (data.get("_meta", {}).get("topic") or "all"),
        "collected": data.get("_meta", {}).get("collected", len(data.get("items", []))),
        "by_type": prov.get("by_type", {}),
        "sources": prov.get("sources", []),
    }
    _atomic_write(args.out, stats)
    print(f"wrote stats: {stats['collected']} items, {len(stats['by_type'])} types -> {os.path.expanduser(args.out)}")
    return 0


def cmd_aggregate(args):
    today = datetime.now(timezone.utc).date()
    if args.from_ or args.to:
        start = _yymmdd(args.from_) or (today - timedelta(days=3650))
        end = _yymmdd(args.to) or today
    else:
        end = today
        start = today - timedelta(days=max(1, args.since if args.since is not None else 7))

    by_type, sources, runs = {}, {}, []
    for path in sorted(glob.glob(os.path.join(os.path.expanduser(args.dir), "*.json"))):
        m = _NAME.match(os.path.basename(path))
        d = _yymmdd(m.group(1)) if m else None
        if d is None or d < start or d > end:
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                s = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        runs.append({"date": s.get("date"), "watchlist": s.get("watchlist"), "collected": s.get("collected", 0)})
        for t, n in (s.get("by_type") or {}).items():
            by_type[t] = by_type.get(t, 0) + n
        for src in s.get("sources") or []:
            key = src.get("id")
            cur = sources.setdefault(key, {"id": key, "name": src.get("name", key),
                                           "type": src.get("type", ""), "count": 0})
            cur["count"] += src.get("count", 0)

    out = {"from": start.isoformat(), "to": end.isoformat(), "runs": len(runs),
           "total_items": sum(r["collected"] for r in runs),
           "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
           "sources": sorted(sources.values(), key=lambda x: -x["count"]), "run_list": runs}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="kensan collection provenance store.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--collect", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--watchlist", default="")
    w.add_argument("--date", default="")
    a = sub.add_parser("aggregate")
    a.add_argument("--dir", required=True)
    a.add_argument("--since", type=int, default=None)
    a.add_argument("--from", dest="from_", default=None)
    a.add_argument("--to", default=None)
    args = ap.parse_args(argv)
    # Hard-error on bad dates (consistent with rollup_index.py): a silently-wrong
    # window — or a stats filename that can never aggregate — is worse than failing.
    if args.cmd == "write" and args.date and _yymmdd(args.date) is None:
        ap.error("--date must be YYMMDD (e.g. 260623)")
    if args.cmd == "aggregate":
        if args.from_ and _yymmdd(args.from_) is None:
            ap.error("--from must be YYMMDD (e.g. 260601)")
        if args.to and _yymmdd(args.to) is None:
            ap.error("--to must be YYMMDD (e.g. 260623)")
    return cmd_write(args) if args.cmd == "write" else cmd_aggregate(args)


if __name__ == "__main__":
    raise SystemExit(main())
