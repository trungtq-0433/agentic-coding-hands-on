#!/usr/bin/env python3
"""CLI for the Kensan cross-day dedup ledger.

Classification / upsert / prune logic lives in `kensan_lib/ledger.py`; this is a
thin command wrapper. Stdlib only.

Subcommands:
  classify     --index L --items items.json [--threshold 0.82]
  upsert       --index L --items classified.json --briefing ID [--today YYYY-MM-DD]
  prune        --index L --older-than 90 [--today YYYY-MM-DD]
  canonicalize URL
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kensan_lib import ledger, normalize  # noqa: E402


def _today(arg=None):
    return arg or datetime.now(timezone.utc).date().isoformat()


def _load_items(path):
    """Accept either collect output ({items:[...]}) or classify output
    ({new,update,merge}), so a scored classify result pipes straight to upsert."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        if "items" in data:
            return data["items"]
        if any(k in data for k in ("new", "update", "merge")):
            return data.get("new", []) + data.get("update", []) + data.get("merge", [])
    return data


def _build_parser():
    ap = argparse.ArgumentParser(description="Kensan dedup ledger.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("classify")
    c.add_argument("--index", required=True)
    c.add_argument("--items", required=True)
    c.add_argument("--threshold", type=float, default=0.82)

    u = sub.add_parser("upsert")
    u.add_argument("--index", required=True)
    u.add_argument("--items", required=True)
    u.add_argument("--briefing", default="")
    u.add_argument("--today", default=None)

    p = sub.add_parser("prune")
    p.add_argument("--index", required=True)
    p.add_argument("--older-than", type=int, default=90)
    p.add_argument("--today", default=None)

    cn = sub.add_parser("canonicalize")
    cn.add_argument("url")
    return ap


def main(argv=None):
    args = _build_parser().parse_args(argv)

    if args.cmd == "canonicalize":
        print(normalize.canonicalize_url(args.url))
        return 0

    records = ledger.load_ledger(args.index)

    if args.cmd == "classify":
        result = ledger.classify(_load_items(args.items), records, args.threshold)
        result["_summary"] = {"new": len(result["new"]), "update": len(result["update"]),
                              "merge": len(result["merge"]), "skip": result["skip_count"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "upsert":
        records = ledger.upsert(_load_items(args.items), records, args.briefing, _today(args.today))
        ledger.save_ledger(args.index, records)
        print(f"ledger now {len(records)} items -> {args.index}")
        return 0

    if args.cmd == "prune":
        before = len(records)
        records = ledger.prune(records, args.older_than, _today(args.today))
        ledger.save_ledger(args.index, records)
        print(f"pruned {before - len(records)} of {before} records")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
