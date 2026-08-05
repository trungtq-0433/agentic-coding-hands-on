#!/usr/bin/env python3
"""Collect items from a Kensan watchlist into one normalized JSON file.

Structured feeds are collected here; `social` rows are emitted under
`_pending_social` for the agent to fill via WebSearch/WebFetch. Failures never
abort the run — they are recorded under `_warnings`.

Usage:
  collect_feeds.py --presets <dir> [--overrides ~/.claude/kensan/watchlist.local.md]
                   [--since 3] [--only <topic>] --out items.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # make kensan_lib importable
from kensan_lib import collectors, normalize, watchlist  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect Kensan watchlist items.")
    ap.add_argument("--presets", required=True, help="presets directory")
    ap.add_argument("--overrides", default="", help="user watchlist.local.md (optional)")
    ap.add_argument("--since", type=int, default=3, help="lookback window in days")
    ap.add_argument("--only", default="", help="restrict to a single topic")
    ap.add_argument("--out", required=True, help="output JSON path")
    args = ap.parse_args(argv)

    overrides = os.path.expanduser(args.overrides) if args.overrides else None
    rows, muted = watchlist.effective_watchlist(args.presets, overrides, args.only or None)

    items, pending_social, warnings = [], [], []
    by_id = {}  # de-dupe identical urls within a single run
    sources_run = 0
    for row in rows:
        if row["id"] in muted:
            continue
        weight = watchlist.source_weight(row)
        if row.get("type") == "social":
            pending_social.append({
                "id": row["id"], "name": row.get("name", row["id"]),
                "handle": row.get("handle", ""), "topic": row.get("topic", ""),
                "weight": weight, "since": args.since,
            })
            continue
        sources_run += 1
        got, warn = collectors.collect_source(row, args.since)
        if warn:
            warnings.append(warn)
        for it in got:
            if it["id"] and it["id"] not in by_id:
                it["weight"] = weight  # source priority carried onto every item
                by_id[it["id"]] = it
                items.append(it)

    out = {
        "items": items,
        "_pending_social": pending_social,
        "_warnings": warnings,
        "_provenance": normalize.build_provenance(items),
        "_meta": {
            "since_days": args.since,
            "sources_run": sources_run,
            "social_pending": len(pending_social),
            "collected": len(items),
        },
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    m = out["_meta"]
    print(f"collected {m['collected']} items from {m['sources_run']} sources "
          f"| {m['social_pending']} social pending | {len(warnings)} warnings -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
