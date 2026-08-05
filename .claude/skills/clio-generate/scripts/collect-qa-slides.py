#!/usr/bin/env python3
"""collect-qa-slides: decide which PPTX slides need visual QA.

Combines two signals:
  1. Slides gen-slide.py already auto-routed (passed via --auto-slides) --
     generic layouts filled from unrecognized `## heading` sections.
  2. Slides OfficeCLI's `view issues` flags as having real overflow / off-slide
     / overlapping shapes -- catches bespoke-template slides (table splits,
     row-fitting, in-place truncation) that auto-routing never looks at, and
     that qa-slides.py previously skipped entirely.

Signal 2 is ranked by issue count and capped (--max-extra, default 5): a
freshly-rendered deck routinely carries many *already-handled* overflow
issues (truncate-in-place + appendix slide, see renderer.py's
_queue_overflow_extra) that don't need a human look. Surfacing all of them
would blow up the QA step's token cost for no benefit, so only the noisiest
slides beyond what's already queued get added, and the count of anything
dropped by the cap is reported (never silently truncated).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ensure_officecli import ensure_officecli

_ISSUES_TIMEOUT_SECONDS = 60
_SLIDE_PATH_RE = re.compile(r'/slide\[(\d+)\]')


def _issue_slide_counts(officecli: str, pptx: Path) -> Counter:
    try:
        result = subprocess.run(
            [officecli, 'view', str(pptx), 'issues', '--json'],
            capture_output=True, text=True, timeout=_ISSUES_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return Counter()

    if result.returncode != 0:
        return Counter()

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return Counter()

    issues = (payload.get('data') or {}).get('issues') or []
    counts = Counter()
    for issue in issues:
        m = _SLIDE_PATH_RE.search(issue.get('path') or '')
        if m:
            counts[int(m.group(1))] += 1
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description='Pick slides for visual QA: auto-routed + OfficeCLI issue hotspots')
    ap.add_argument('--input', required=True, help='Path to the rendered .pptx')
    ap.add_argument('--auto-slides', default='',
                     help='Comma-separated 1-indexed slide numbers already known to need QA (e.g. from '
                          '"Inserted extra slide ... at index N" log lines, N+1)')
    ap.add_argument('--max-extra', type=int, default=5,
                     help='Cap on additional slides pulled in from the issues scan (default 5)')
    args = ap.parse_args()

    auto_slides = sorted({int(s.strip()) for s in args.auto_slides.split(',') if s.strip()})

    officecli = ensure_officecli()
    if not officecli:
        print(json.dumps({'available': False, 'slides': ','.join(map(str, auto_slides))}))
        return

    pptx = Path(args.input)
    if not pptx.exists():
        sys.exit(f'Input not found: {pptx}')

    counts = _issue_slide_counts(officecli, pptx)
    candidates = [n for n in counts if n not in auto_slides]
    candidates.sort(key=lambda n: counts[n], reverse=True)

    extra = sorted(candidates[:args.max_extra])
    dropped = candidates[args.max_extra:]

    all_slides = sorted(set(auto_slides) | set(extra))
    print(json.dumps({
        'available': True,
        'slides': ','.join(map(str, all_slides)),
        'auto_slides': auto_slides,
        'issue_flagged_extra': extra,
        'issue_flagged_dropped': dropped,
        'issue_counts': {str(n): counts[n] for n in sorted(counts)},
    }, indent=2))


if __name__ == '__main__':
    main()
