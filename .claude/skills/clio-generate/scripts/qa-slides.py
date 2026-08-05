#!/usr/bin/env python3
"""qa-slides: screenshot specific PPTX slides via OfficeCLI for visual review.

Optional QA step for Step B (--gen slide): renders the slides that gen-slide.py
auto-routed (extra sections / --extra-slides entries) to PNG so the calling
agent can Read() them and check for text overflow or broken layout before
uploading to Clio.

Uses the `officecli` binary (https://github.com/iOfficeAI/OfficeCLI) — found
on PATH if already installed, otherwise downloaded on first use into a local
cache via ensure_officecli.py. If that isn't possible either (unsupported
platform, no network), this prints {"available": false} and exits 0 so the
skill falls back to the existing manual-review message.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ensure_officecli import ensure_officecli

_SCREENSHOT_TIMEOUT_SECONDS = 60


def _screenshot_one(officecli: str, pptx: Path, slide_no: int, out_dir: Path) -> dict:
    out_path = out_dir / f'slide-{slide_no}.png'
    try:
        result = subprocess.run(
            [officecli, 'view', str(pptx), 'screenshot',
             '-o', str(out_path), '--page', str(slide_no)],
            capture_output=True, text=True, timeout=_SCREENSHOT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {'slide': slide_no, 'ok': False, 'error': 'timed out'}

    if result.returncode != 0 or not out_path.exists():
        error = (result.stderr or result.stdout or 'unknown error').strip()[:300]
        return {'slide': slide_no, 'ok': False, 'error': error}
    return {'slide': slide_no, 'ok': True, 'path': str(out_path)}


def main() -> None:
    ap = argparse.ArgumentParser(description='Screenshot PPTX slides via OfficeCLI for visual QA')
    ap.add_argument('--input', required=True, help='Path to the rendered .pptx')
    ap.add_argument('--slides', required=True,
                     help='Comma-separated 1-indexed slide numbers to screenshot, e.g. "5,12,47"')
    ap.add_argument('--output-dir', required=True, help='Directory to write slide-N.png files into')
    args = ap.parse_args()

    officecli = ensure_officecli()
    if not officecli:
        print(json.dumps({'available': False}))
        return

    pptx = Path(args.input)
    if not pptx.exists():
        sys.exit(f'Input not found: {pptx}')

    try:
        slide_numbers = list(dict.fromkeys(int(s.strip()) for s in args.slides.split(',') if s.strip()))
    except ValueError:
        sys.exit(f'--slides must be comma-separated integers, got: {args.slides}')

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    screenshots = [_screenshot_one(officecli, pptx, n, out_dir) for n in slide_numbers]
    print(json.dumps({'available': True, 'screenshots': screenshots}, indent=2))


if __name__ == '__main__':
    main()
