#!/usr/bin/env python3
"""clio-api: minimal helper for S3 operations in the clio-generate skill.

Subcommands:
  put       PUT a file to a presigned S3 URL (from clio_get_assets_upload_url or clio_get_artifacts_upload_url MCP tools)
  download  Download a file from a presigned URL (from clio_get_assets_download_url MCP tool)

The list/finalize operations are handled by MCP tools directly (no REST API calls needed).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ensure_deps import ensure_deps
ensure_deps(probe="requests")

import requests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MIME_MAP = {
    'md': 'text/markdown', 'markdown': 'text/markdown',
    'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'pdf': 'application/pdf',
}


def _mime_type(path: Path) -> str:
    return _MIME_MAP.get(path.suffix.lower().lstrip('.'), 'application/octet-stream')


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_put(url: str, file_path: str, content_type: str | None) -> None:
    """PUT a file to a presigned S3 URL from clio_get_assets_upload_url or clio_get_artifacts_upload_url."""
    p = Path(file_path)
    if not p.exists():
        sys.exit(f'File not found: {file_path}')

    mime = content_type or _mime_type(p)
    data = p.read_bytes()
    r = requests.put(url, headers={'Content-Type': mime}, data=data, timeout=120)
    r.raise_for_status()
    print(f'PUT {p.name} → S3 ({r.status_code})')


def cmd_download(url: str, output: str) -> None:
    """Download a file from a presigned S3 URL from clio_get_assets_download_url."""
    r = requests.get(url, timeout=120)
    r.raise_for_status()

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    print(f'Downloaded → {out}')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description='Clio S3 upload/download helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest='cmd', required=True)

    # put — S3 PUT to presigned URL
    p_put = sub.add_parser('put', help='PUT a file to a presigned S3 URL')
    p_put.add_argument('--url', required=True, help='Presigned S3 upload_url from MCP tool')
    p_put.add_argument('--file', required=True, help='Local file path to upload')
    p_put.add_argument('--content-type', default=None, help='MIME type (auto-detected if omitted)')

    # download
    p_dl = sub.add_parser('download', help='Download a file from a presigned URL')
    p_dl.add_argument('--url', required=True, help='Presigned S3 download_url from clio_get_assets_download_url')
    p_dl.add_argument('--output', required=True, help='Local output path')

    args = ap.parse_args()

    if args.cmd == 'put':
        cmd_put(args.url, args.file, args.content_type)
    elif args.cmd == 'download':
        cmd_download(args.url, args.output)


if __name__ == '__main__':
    main()
