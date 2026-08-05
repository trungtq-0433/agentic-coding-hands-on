#!/usr/bin/env python3
"""Gather topic-scoped community discussion into one normalized JSON file.

Mines Hacker News comments and GitHub issues for a topic. Reddit + X are NOT here
(agent-native via WebSearch — see references/discussion-mining.md). Failures never
abort — they land in `_warnings`.

Usage:
  collect_discussions.py --topic "agent memory" [--since 30]
                         [--sources hn-comments,github-issues] --out disc.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # make kensan_lib importable
from kensan_lib import discussions, normalize  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect topic-scoped community discussion.")
    ap.add_argument("--topic", required=True, help="topic / search query")
    ap.add_argument("--since", type=int, default=30, help="lookback window in days")
    ap.add_argument("--sources", default=",".join(discussions.SOURCES),
                    help="comma-separated subset of: " + ",".join(discussions.SOURCES))
    ap.add_argument("--out", required=True, help="output JSON path")
    args = ap.parse_args(argv)

    wanted = [s.strip() for s in args.sources.split(",") if s.strip()]
    items, warnings, by_id = [], [], {}
    sources_run = 0
    for source in wanted:
        sources_run += 1
        got, warn = discussions.collect_discussion_source(source, args.topic, args.since)
        if warn:
            warnings.append(warn)
        for it in got:
            if it["id"] and it["id"] not in by_id:
                by_id[it["id"]] = it
                items.append(it)

    out = {
        "items": items,
        "_warnings": warnings,
        "_provenance": normalize.build_provenance(items),
        "_meta": {"topic": args.topic, "since_days": args.since,
                  "sources_run": sources_run, "collected": len(items)},
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    by_platform = {}
    for it in items:
        by_platform[it["platform"]] = by_platform.get(it["platform"], 0) + 1
    print(f"collected {len(items)} discussion items for '{args.topic}' "
          f"{by_platform} | {len(warnings)} warnings -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
