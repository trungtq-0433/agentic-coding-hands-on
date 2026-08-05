"""Self-contained bootstrap for the officecli binary (qa-slides.py's visual QA).

Why this exists
----------------
qa-slides.py's screenshot QA step needs the `officecli` binary
(https://github.com/iOfficeAI/OfficeCLI). Most environments — including the
Claude Desktop sandbox — won't have it pre-installed, and running
`officecli install` isn't appropriate here: it modifies PATH / global agent
configs, and the sandbox's skill dir is read-only anyway.

This module downloads the plain binary straight from GitHub Releases into a
writable cache dir on first use, verifies it against the release's published
SHA256SUMS, and reuses the cached copy afterward. No PATH changes, nothing
global, easy to remove (rm -rf ~/.cache/clio-generate/bin).

If the platform is unsupported or the download/verification fails for any
reason (no network, GitHub unreachable, checksum mismatch), `ensure_officecli()`
returns None and the caller degrades exactly as if officecli were absent.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

_LATEST_BASE = 'https://github.com/iOfficeAI/OfficeCLI/releases/latest/download'
_DOWNLOAD_TIMEOUT_SECONDS = 180
_CHECKSUM_TIMEOUT_SECONDS = 30
_CHUNK_BYTES = 1024 * 1024

# (platform.system(), platform.machine()) -> release asset name.
# musl/alpine Linux isn't covered (rare for this skill's use case) — falls
# through to None and ensure_officecli() reports unavailable, same as today.
_ASSET_BY_PLATFORM = {
    ('Linux', 'x86_64'): 'officecli-linux-x64',
    ('Linux', 'aarch64'): 'officecli-linux-arm64',
    ('Darwin', 'x86_64'): 'officecli-mac-x64',
    ('Darwin', 'arm64'): 'officecli-mac-arm64',
    ('Windows', 'AMD64'): 'officecli-win-x64.exe',
    ('Windows', 'ARM64'): 'officecli-win-arm64.exe',
}


def _cache_dir() -> Path:
    candidates = [
        os.environ.get('CLIO_BIN_DIR'),
        Path.home() / '.cache' / 'clio-generate' / 'bin',
        Path(tempfile.gettempdir()) / 'clio_bin',
    ]
    for cand in candidates:
        if not cand:
            continue
        path = Path(cand)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            continue
    return Path(tempfile.mkdtemp(prefix='clio_bin_'))


def _asset_name() -> str | None:
    return _ASSET_BY_PLATFORM.get((platform.system(), platform.machine()))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(_CHUNK_BYTES), b''):
            h.update(chunk)
    return h.hexdigest()


def _expected_checksum(asset: str) -> str | None:
    """Look up *asset*'s sha256 in the latest release's SHA256SUMS. None on any failure."""
    try:
        with urllib.request.urlopen(f'{_LATEST_BASE}/SHA256SUMS', timeout=_CHECKSUM_TIMEOUT_SECONDS) as resp:
            sums = resp.read().decode('utf-8', errors='replace')
    except (urllib.error.URLError, OSError, TimeoutError):
        return None
    for line in sums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == asset:
            return parts[0]
    return None


def ensure_officecli() -> str | None:
    """Return a usable officecli binary path, downloading + verifying it if needed.

    Never raises — returns None when officecli can't be made available
    (unsupported platform, no network, or checksum mismatch).
    """
    on_path = shutil.which('officecli')
    if on_path:
        return on_path

    asset = _asset_name()
    if not asset:
        return None

    cache_dir = _cache_dir()
    cached = cache_dir / asset
    if cached.exists() and os.access(cached, os.X_OK):
        return str(cached)

    expected = _expected_checksum(asset)
    if not expected:
        return None  # no network / GitHub unreachable / asset not in SHA256SUMS

    print(f'[qa-slides] officecli not found — downloading {asset} for visual QA '
          f'(one-time, cached at {cache_dir})...', file=sys.stderr)

    # PID-scoped tmp name: concurrent qa-slides.py runs must not write the same
    # file, which would corrupt both downloads and could otherwise race the
    # final os.replace() below.
    tmp_path = cache_dir / f'{asset}.{os.getpid()}.part'
    try:
        with urllib.request.urlopen(f'{_LATEST_BASE}/{asset}', timeout=_DOWNLOAD_TIMEOUT_SECONDS) as resp, \
                tmp_path.open('wb') as f:
            while True:
                chunk = resp.read(_CHUNK_BYTES)
                if not chunk:
                    break
                f.write(chunk)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        tmp_path.unlink(missing_ok=True)
        print(f'[qa-slides] officecli download failed: {e}', file=sys.stderr)
        return None

    if _sha256(tmp_path) != expected:
        tmp_path.unlink(missing_ok=True)
        print('[qa-slides] officecli download failed checksum verification, discarding', file=sys.stderr)
        return None

    tmp_path.chmod(tmp_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    # os.replace (not Path.rename): atomic overwrite on both POSIX and Windows.
    # Path.rename raises FileExistsError on Windows if `cached` already exists
    # (e.g. a concurrent run finished first) — os.replace never does.
    os.replace(tmp_path, cached)
    return str(cached)
