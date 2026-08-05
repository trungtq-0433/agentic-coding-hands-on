"""Cross-day dedup ledger logic (stdlib only).

The ledger is `seen-items.jsonl` — one JSON record per known item. These helpers
classify collected items NEW / SKIP / UPDATE / MERGE against it and write back,
so repeated runs report only what genuinely changed. The CLI lives in
`scripts/index_store.py`.
"""

import json
import os
import re
from datetime import datetime


def load_ledger(path):
    """Read the JSONL ledger into {id: record}; tolerant of blank/corrupt lines."""
    records = {}
    if not path or not os.path.exists(path):
        return records
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                records[rec["id"]] = rec
            except (json.JSONDecodeError, KeyError):
                continue
    return records


def save_ledger(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records.values():
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _shingles(title):
    words = re.sub(r"[^\w\s]", " ", (title or "").lower()).split()
    return set(words)


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _find_near_duplicate(item, records, threshold):
    """Return an existing record whose title is a near-duplicate, else None."""
    target = _shingles(item.get("title", ""))
    best_rec, best = None, 0.0
    for rec in records.values():
        score = _jaccard(target, _shingles(rec.get("title", "")))
        if score > best:
            best_rec, best = rec, score
    return best_rec if best >= threshold else None


def _known_hashes(rec):
    """All content hashes ever seen for a record (back-compat with old ledgers)."""
    hashes = set(rec.get("seen_hashes") or [])
    if rec.get("content_hash"):
        hashes.add(rec["content_hash"])
    return hashes


def classify(items, records, threshold):
    """Split items into new / update / skip / merge against the ledger.

    Lookup includes each record's aliases, so a once-merged item resolves to its
    canonical record on later runs and SKIPs instead of re-merging every time.
    """
    by_id = {}
    for rec in records.values():
        by_id[rec["id"]] = rec
        for alias in rec.get("aliases", []):
            by_id.setdefault(alias, rec)

    new, update, merge, skip = [], [], [], 0
    for it in items:
        rec = by_id.get(it["id"])
        is_alias = rec is not None and rec["id"] != it["id"]
        if rec is None:
            rec = _find_near_duplicate(it, records, threshold)
            is_alias = rec is not None
        if rec is None:
            new.append(it)
            continue
        if it.get("content_hash") in _known_hashes(rec):
            skip += 1
            continue
        it["_first_seen"] = rec.get("first_seen", "")
        it["_prev_seen"] = rec.get("times_seen", 1)
        if is_alias:
            it["_alias_of"] = rec["id"]
            merge.append(it)
        else:
            update.append(it)
    return {"new": new, "update": update, "merge": merge,
            "skip_count": skip, "ledger_size": len(records)}


def upsert(items, records, briefing_id, today):
    """Write classified items back into the ledger (records aliases + seen hashes)."""
    for it in items:
        rid = it.get("_alias_of") or it["id"]
        rec = records.get(rid)
        if rec is None:
            rec = {"id": it["id"], "url": it.get("url", ""), "title": it.get("title", ""),
                   "topic": it.get("topic", it.get("source_id", "")), "first_seen": today,
                   "times_seen": 0, "briefings": [], "aliases": [], "seen_hashes": []}
            records[rec["id"]] = rec
        rec["last_updated"] = today
        rec["times_seen"] = rec.get("times_seen", 0) + 1
        new_hash = it.get("content_hash", "")
        rec["content_hash"] = new_hash or rec.get("content_hash", "")
        seen = rec.setdefault("seen_hashes", [])
        if new_hash and new_hash not in seen:
            seen.append(new_hash)  # every variant seen → future identical runs SKIP
        if "score" in it:
            rec["score"] = it["score"]
        rec["status"] = it.get("status", "stable")
        if briefing_id and briefing_id not in rec.setdefault("briefings", []):
            rec["briefings"].append(briefing_id)
        if it.get("_alias_of") and it["id"] != rid:
            if it["id"] not in rec.setdefault("aliases", []):
                rec["aliases"].append(it["id"])
    return records


def prune(records, older_than_days, today):
    """Drop records not seen within N days (unparseable dates are kept)."""
    cutoff = datetime.fromisoformat(today).toordinal() - int(older_than_days)
    kept = {}
    for rid, rec in records.items():
        last = rec.get("last_updated") or rec.get("first_seen")
        try:
            if datetime.fromisoformat(last).toordinal() >= cutoff:
                kept[rid] = rec
        except (ValueError, TypeError):
            kept[rid] = rec
    return kept
