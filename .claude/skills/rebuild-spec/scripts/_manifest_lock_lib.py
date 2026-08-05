"""File-locking helpers for manifest atomic read-modify-write (Phase D, RT2-F5).

POSIX: fcntl.flock exclusive lock on the manifest file handle.
Windows / fallback: .lock sentinel file with spin-wait (max 30 s).

Stdlib only. Imported exclusively by _components_manifest_lib.
"""
from __future__ import annotations

import os
import sys

if sys.platform != "win32":
    import fcntl

    def lock_file(fh) -> None:  # type: ignore[return]
        """Acquire exclusive lock on open file handle (POSIX)."""
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)

    def unlock_file(fh) -> None:
        """Release exclusive lock on open file handle (POSIX)."""
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

else:
    import time

    def lock_file(fh) -> None:
        """Sentinel-file spin-lock for non-POSIX platforms."""
        sentinel = fh.name + ".lock"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                fd = os.open(sentinel, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return
            except FileExistsError:
                time.sleep(0.05)
        raise TimeoutError(f"Could not acquire manifest lock: {sentinel}")

    def unlock_file(fh) -> None:
        """Release sentinel-file lock."""
        sentinel = fh.name + ".lock"
        try:
            os.unlink(sentinel)
        except FileNotFoundError:
            pass
