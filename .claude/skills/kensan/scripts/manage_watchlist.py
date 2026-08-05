#!/usr/bin/env python3
"""Inspect + edit the per-user kensan watchlist (`~/.claude/kensan/watchlist.local.md`).

Drives the interactive `/tkm:kensan manage` mode: `list` reports the effective
state for display; the mutators apply one change and rewrite the override file.
Shipped presets are never touched. Stdlib only.

Usage:
  manage_watchlist.py list      --presets DIR [--overrides PATH]
  manage_watchlist.py set-preset --overrides PATH --stem STEM --state on|off
  manage_watchlist.py mute|unmute|remove --overrides PATH --id ID
  manage_watchlist.py add|update --overrides PATH --id ID [--name N --type T --handle H --topic TP --weight W]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kensan_lib import overrides_io, watchlist  # noqa: E402

KNOWN_TYPES = {"rss", "arxiv", "github-releases", "github-trending", "github-user",
               "hn", "hf-papers", "goodailist", "bluesky", "youtube", "twitter", "social"}


def _state(rid, preset, data):
    if rid in data["remove"]:
        return "removed"
    if preset in data["disable_preset"]:
        return "disabled"
    overridden = rid in {r.get("id") for r in data["add"]}
    muted = rid in data["mute"]
    if overridden and muted:
        return "overridden+muted"
    if overridden:
        return "overridden"
    if muted:
        return "muted"
    return "enabled"


def cmd_list(args):
    presets = watchlist.load_presets(args.presets)
    data = overrides_io.load(args.overrides) if args.overrides else \
        {"add": [], "remove": [], "mute": [], "disable_preset": []}
    preset_ids = {r["id"] for r in presets}
    sources = [{
        "preset": r.get("_preset", ""), "id": r["id"], "name": r.get("name", r["id"]),
        "type": r.get("type", ""), "topic": r.get("topic", ""),
        "weight": watchlist.source_weight(r), "state": _state(r["id"], r.get("_preset"), data),
    } for r in presets]
    for r in data["add"]:  # user-added sources (not shadowing a preset)
        if r.get("id") not in preset_ids:
            sources.append({"preset": "custom", "id": r.get("id"), "name": r.get("name", r.get("id")),
                            "type": r.get("type", ""), "topic": r.get("topic", "custom"),
                            "weight": watchlist.source_weight(r), "state": "added"})
    stems = sorted({r.get("_preset", "") for r in presets})
    out = {
        "presets": [{"stem": s, "disabled": s in data["disable_preset"],
                     "count": sum(1 for x in sources if x["preset"] == s)} for s in stems],
        "sources": sources,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _row_from_args(args):
    row = {"id": args.id}
    for f in ("name", "type", "handle", "topic", "weight"):
        v = getattr(args, f, None)
        if v is not None:
            row[f] = v
    return row


def cmd_mutate(args):
    data = overrides_io.load(args.overrides)
    if args.cmd in ("add", "update"):
        if getattr(args, "type", None) and args.type not in KNOWN_TYPES:
            print(f"error: unknown type '{args.type}' (known: {', '.join(sorted(KNOWN_TYPES))})", file=sys.stderr)
            return 2
        if args.cmd == "update":  # merge onto any existing add row
            merged = dict(next((r for r in data["add"] if r.get("id") == args.id), {}))
            merged.update(_row_from_args(args))
            overrides_io.add_or_update(data, merged)
        else:
            overrides_io.add_or_update(data, _row_from_args(args))
    elif args.cmd == "remove":
        overrides_io.remove_id(data, args.id)
    elif args.cmd == "mute":
        overrides_io.toggle(data, "mute", args.id, True)
    elif args.cmd == "unmute":
        overrides_io.toggle(data, "mute", args.id, False)
    elif args.cmd == "set-preset":
        overrides_io.toggle(data, "disable_preset", args.stem, args.state == "off")
    overrides_io.dump(args.overrides, data)
    print(f"ok: {args.cmd} -> {os.path.expanduser(args.overrides)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Manage the kensan watchlist overrides.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--presets", required=True)
    p.add_argument("--overrides", default="")
    for name in ("add", "update"):
        m = sub.add_parser(name)
        m.add_argument("--overrides", required=True)
        m.add_argument("--id", required=True)
        for f in ("name", "type", "handle", "topic", "weight"):
            m.add_argument("--" + f, default=None)
    for name in ("mute", "unmute", "remove"):
        m = sub.add_parser(name)
        m.add_argument("--overrides", required=True)
        m.add_argument("--id", required=True)
    sp = sub.add_parser("set-preset")
    sp.add_argument("--overrides", required=True)
    sp.add_argument("--stem", required=True)
    sp.add_argument("--state", required=True, choices=["on", "off"])
    args = ap.parse_args(argv)
    return cmd_list(args) if args.cmd == "list" else cmd_mutate(args)


if __name__ == "__main__":
    raise SystemExit(main())
