"""Tests for _components_manifest_lib.py (Phase D).

Coverage targets (from phase-05 success criteria):
- emit_manifest: components[] → run-plan JSON with correct shape and defaults
- collision check: two entries deriving the same component_name → error BEFORE write
- next_pending: returns first pending; skips done/failed
- mark_done / mark_failed: atomic updates; sha required on done
- resume simulation: mark entries 1-6 done, next_pending returns entry 7 of 20
- one failed entry does not affect done entries
- path-canonicalize: entry with '..' → rejected on load
- sha required + verify helper
- concurrent writers: two sequential atomic round-trips leave manifest consistent
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _components_manifest_lib as mlib  # noqa: E402


# ---------------------------------------------------------------------------
# Phase 03 — shared-layer sidecar (manifest stays a JSON array; shared goes in a sidecar)
# ---------------------------------------------------------------------------

class TestSharedSidecar:
    def test_sidecar_path_derivation(self):
        assert mlib.shared_sidecar_path("/r/.rebuild-components.json") == \
            "/r/.rebuild-components-shared.json"
        assert mlib.shared_sidecar_path("/r/custom.json") == "/r/custom-shared.json"

    def test_shared_sidecar_roundtrip(self, tmp_path):
        root = str(tmp_path)
        shared = [
            {"path": "PG/Common", "kind": "source", "label": "Common"},
            {"path": "DB", "kind": "db", "label": "DB"},
        ]
        sidecar = str(tmp_path / ".rebuild-components-shared.json")
        mlib.emit_shared_sidecar(sidecar, shared, root)
        loaded = mlib.load_shared_sidecar(sidecar, root)
        assert loaded == shared

    def test_missing_sidecar_is_empty(self, tmp_path):
        assert mlib.load_shared_sidecar(str(tmp_path / "nope.json")) == []

    def test_manifest_still_array(self, tmp_path):
        # The component manifest format is untouched — emit + load round-trips as a list.
        manifest = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest, _make_components(3), str(tmp_path))
        with open(manifest, encoding="utf-8") as fh:
            assert isinstance(json.load(fh), list)

    def test_sidecar_rejects_path_traversal(self, tmp_path):
        with pytest.raises(ValueError):
            mlib.emit_shared_sidecar(
                str(tmp_path / "s.json"),
                [{"path": "../escape", "kind": "db", "label": "escape"}],
                str(tmp_path),
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_components(n: int, prefix: str = "services/svc") -> list[dict]:
    return [
        {
            "path": f"{prefix}-{i:02d}",
            "profile": "spring",
            "role": "domain-service",
            "size_est": 100,
            "timeout_hint": 3600,
            "max_loc": 10000,
        }
        for i in range(1, n + 1)
    ]


def _write_dummy_digest(dir_: Path, content: str = '{"service":"x"}') -> Path:
    p = dir_ / "_service-digest.json"
    p.write_text(content, encoding="utf-8")
    return p


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# emit_manifest
# ---------------------------------------------------------------------------

class TestEmitManifest:
    def test_basic_shape(self, tmp_path):
        comps = _make_components(3)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))

        entries = json.loads(Path(manifest_path).read_text())
        assert len(entries) == 3
        for entry in entries:
            assert entry["status"] == "pending"
            assert entry["sha"] is None
            assert "name" in entry
            assert "timeout_hint" in entry

    def test_name_derived_from_path(self, tmp_path):
        comps = [{"path": "services/payments/api", "profile": "spring", "role": "svc"}]
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        entries = json.loads(Path(manifest_path).read_text())
        assert entries[0]["name"] == "services-payments-api"

    def test_collision_check_raises_before_write(self, tmp_path):
        """Two paths deriving the same component_name → ValueError, no file written."""
        manifest_path = str(tmp_path / ".rebuild-components.json")
        comps = [
            {"path": "services/payments/api", "profile": "spring", "role": "svc"},
            {"path": "services/payments/api", "profile": "nestjs", "role": "svc"},
        ]
        with pytest.raises(ValueError, match="collision"):
            mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        assert not Path(manifest_path).exists()

    def test_collision_different_basename_same_slug(self, tmp_path):
        """services/foo-bar and services/foo/bar both → services-foo-bar collision."""
        manifest_path = str(tmp_path / ".rebuild-components.json")
        comps = [
            {"path": "services/foo-bar", "profile": "go", "role": "svc"},
            {"path": "services/foo/bar", "profile": "go", "role": "svc"},
        ]
        # Both produce "services-foo-bar" — collision
        with pytest.raises(ValueError, match="collision"):
            mlib.emit_manifest(manifest_path, comps, str(tmp_path))

    def test_writes_atomically(self, tmp_path):
        """File must exist and be valid JSON after emit (tmp→replace)."""
        comps = _make_components(2)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        # No .tmp files left
        tmp_files = list(tmp_path.glob("*.json.tmp"))
        assert tmp_files == []
        # Valid JSON
        data = json.loads(Path(manifest_path).read_text())
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------

class TestLoadManifest:
    def test_load_valid(self, tmp_path):
        comps = _make_components(2)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        entries = mlib.load_manifest(manifest_path, str(tmp_path))
        assert len(entries) == 2

    def test_path_traversal_rejected(self, tmp_path):
        """Entry path with '..' must be rejected on load."""
        evil = [
            {
                "path": "../etc/passwd",
                "name": "evil",
                "profile": "spring",
                "role": "svc",
                "status": "pending",
                "sha": None,
                "fail_reason": None,
                "size_est": 0,
                "timeout_hint": 3600,
                "max_loc": 0,
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]
        manifest_path = str(tmp_path / ".rebuild-components.json")
        Path(manifest_path).write_text(json.dumps(evil), encoding="utf-8")
        with pytest.raises(ValueError):
            mlib.load_manifest(manifest_path, str(tmp_path))

    def test_done_without_sha_rejected(self, tmp_path):
        """status=done with null sha must be rejected on load."""
        entry = {
            "path": "services/svc-01",
            "name": "services-svc-01",
            "profile": "spring",
            "role": "svc",
            "status": "done",
            "sha": None,
            "fail_reason": None,
            "size_est": 0,
            "timeout_hint": 3600,
            "max_loc": 0,
            "updated_at": "2026-01-01T00:00:00Z",
        }
        manifest_path = str(tmp_path / ".rebuild-components.json")
        Path(manifest_path).write_text(json.dumps([entry]), encoding="utf-8")
        with pytest.raises(ValueError, match="sha"):
            mlib.load_manifest(manifest_path, str(tmp_path))


# ---------------------------------------------------------------------------
# next_pending
# ---------------------------------------------------------------------------

class TestNextPending:
    def test_returns_first_pending(self, tmp_path):
        comps = _make_components(3)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        entries = mlib.load_manifest(manifest_path)
        entry = mlib.next_pending(entries)
        assert entry is not None
        assert entry["status"] == "pending"
        assert entry["path"] == comps[0]["path"]

    def test_returns_none_when_all_done(self, tmp_path):
        comps = _make_components(2)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        digest_file = _write_dummy_digest(tmp_path)
        sha = _sha256('{"service":"x"}')
        for comp in comps:
            mlib.mark_done(manifest_path, comp["path"], sha)
        entries = mlib.load_manifest(manifest_path)
        assert mlib.next_pending(entries) is None

    def test_resume_at_entry_7_of_20(self, tmp_path):
        """Simulate kill at entry 7: mark 1-6 done → next_pending returns entry 7."""
        comps = _make_components(20)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))

        sha = _sha256("dummy")
        for comp in comps[:6]:
            mlib.mark_done(manifest_path, comp["path"], sha)

        entries = mlib.load_manifest(manifest_path)
        nxt = mlib.next_pending(entries)
        assert nxt is not None
        assert nxt["path"] == comps[6]["path"]   # 0-indexed: 7th entry

    def test_failed_entry_does_not_block_others(self, tmp_path):
        """One failed entry → remaining done entries stay done; pending entries accessible."""
        comps = _make_components(5)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))

        sha = _sha256("dummy")
        # Mark entries 0 and 2 done, entry 1 failed
        mlib.mark_done(manifest_path, comps[0]["path"], sha)
        mlib.mark_failed(manifest_path, comps[1]["path"], "timeout")
        mlib.mark_done(manifest_path, comps[2]["path"], sha)

        entries = mlib.load_manifest(manifest_path)
        done = [e for e in entries if e["status"] == "done"]
        failed = [e for e in entries if e["status"] == "failed"]
        pending = [e for e in entries if e["status"] == "pending"]

        assert len(done) == 2
        assert len(failed) == 1
        assert len(pending) == 2
        assert failed[0]["fail_reason"] == "timeout"


# ---------------------------------------------------------------------------
# mark_done / mark_failed
# ---------------------------------------------------------------------------

class TestMarkDone:
    def test_mark_done_sets_sha(self, tmp_path):
        comps = _make_components(1)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        sha = _sha256("some content")
        mlib.mark_done(manifest_path, comps[0]["path"], sha)
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["status"] == "done"
        assert entries[0]["sha"] == sha

    def test_mark_done_requires_sha(self, tmp_path):
        comps = _make_components(1)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        with pytest.raises(ValueError, match="sha"):
            mlib.mark_done(manifest_path, comps[0]["path"], "")

    def test_mark_failed_sets_reason(self, tmp_path):
        comps = _make_components(1)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        mlib.mark_failed(manifest_path, comps[0]["path"], "session_terminated")
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["status"] == "failed"
        assert entries[0]["fail_reason"] == "session_terminated"
        assert entries[0]["sha"] is None


# ---------------------------------------------------------------------------
# verify_sha
# ---------------------------------------------------------------------------

class TestVerifySha:
    def test_verify_sha_match(self, tmp_path):
        comps = _make_components(1)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))

        content = '{"service":"orders"}'
        digest_file = tmp_path / "_service-digest.json"
        digest_file.write_text(content, encoding="utf-8")
        sha = mlib._sha256_file(str(digest_file))
        mlib.mark_done(manifest_path, comps[0]["path"], sha)

        assert mlib.verify_sha(manifest_path, comps[0]["path"], str(digest_file)) is True

    def test_verify_sha_mismatch(self, tmp_path):
        comps = _make_components(1)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))

        content = '{"service":"orders"}'
        digest_file = tmp_path / "_service-digest.json"
        digest_file.write_text(content, encoding="utf-8")
        # Store wrong sha
        mlib.mark_done(manifest_path, comps[0]["path"], "wrongsha")

        assert mlib.verify_sha(manifest_path, comps[0]["path"], str(digest_file)) is False

    def test_verify_sha_pending_returns_false(self, tmp_path):
        comps = _make_components(1)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))
        digest_file = _write_dummy_digest(tmp_path)
        assert mlib.verify_sha(manifest_path, comps[0]["path"], str(digest_file)) is False


# ---------------------------------------------------------------------------
# Concurrent writers simulation (sequential atomic round-trips)
# ---------------------------------------------------------------------------

class TestConcurrentWriters:
    def test_two_sequential_atomic_writes_consistent(self, tmp_path):
        """Simulate two concurrent writers via sequential atomic round-trips.

        Both mark different entries done. Final manifest must show both done
        and no corruption — proves the lock+replace cycle is safe.
        """
        comps = _make_components(3)
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, comps, str(tmp_path))

        sha = _sha256("content")

        # Writer 1 marks entry 0 done
        mlib.mark_done(manifest_path, comps[0]["path"], sha)
        # Writer 2 marks entry 1 done (simulates interleaved access)
        mlib.mark_done(manifest_path, comps[1]["path"], sha)

        # Must be valid JSON with both entries done
        entries = json.loads(Path(manifest_path).read_text())
        statuses = {e["path"]: e["status"] for e in entries}
        assert statuses[comps[0]["path"]] == "done"
        assert statuses[comps[1]["path"]] == "done"
        assert statuses[comps[2]["path"]] == "pending"
        # No orphaned tmp files
        assert list(tmp_path.glob("*.json.tmp")) == []


# ---------------------------------------------------------------------------
# Phase 05 — reused status in manifest
# ---------------------------------------------------------------------------

class TestReusedManifestStatus:
    """emit_manifest threads reused fields; load_manifest accepts status=reused without sha."""

    def _make_reused_comp(self, path: str = "employee") -> dict:
        return {
            "path": path,
            "profile": None,
            "role": "service",
            "group": None,
            "status": "reused",
            "docs_path": f"{path}/docs",
            "source_sha": "abc123def456abc123def456abc123def456abc1",
            "is_git_root": False,
        }

    def test_emit_manifest_includes_reused_fields(self, tmp_path):
        comp = self._make_reused_comp()
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, [comp], str(tmp_path))
        entries = json.loads(Path(manifest_path).read_text())
        assert len(entries) == 1
        e = entries[0]
        assert e["status"] == "reused"
        assert e["docs_path"] == "employee/docs"
        assert e["source_sha"] == "abc123def456abc123def456abc123def456abc1"
        assert e["is_git_root"] is False

    def test_emit_manifest_reused_sha_null(self, tmp_path):
        """sha field stays null for reused (no digest produced yet)."""
        comp = self._make_reused_comp()
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, [comp], str(tmp_path))
        entries = json.loads(Path(manifest_path).read_text())
        assert entries[0]["sha"] is None

    def test_load_manifest_accepts_reused_without_sha(self, tmp_path):
        """status=reused with sha=null must NOT raise on load."""
        comp = self._make_reused_comp()
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, [comp], str(tmp_path))
        # Should not raise
        entries = mlib.load_manifest(manifest_path, str(tmp_path))
        assert len(entries) == 1
        assert entries[0]["status"] == "reused"

    def test_load_manifest_done_still_requires_sha(self, tmp_path):
        """Regression: status=done still requires sha even when reused entries exist."""
        reused = self._make_reused_comp("employee")
        normal = {
            "path": "gateway", "profile": "web-js-ts", "role": "backend",
            "group": None, "size_est": 0, "timeout_hint": 3600, "max_loc": 0,
        }
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, [reused, normal], str(tmp_path))
        # Force gateway to done without sha
        entries = json.loads(Path(manifest_path).read_text())
        for e in entries:
            if e["path"] == "gateway":
                e["status"] = "done"
                e["sha"] = None
        Path(manifest_path).write_text(json.dumps(entries), encoding="utf-8")
        with pytest.raises(ValueError, match="sha"):
            mlib.load_manifest(manifest_path, str(tmp_path))

    def test_mixed_manifest_pending_and_reused(self, tmp_path):
        """next_pending skips reused entries (only returns pending)."""
        reused = self._make_reused_comp("employee")
        normal = {
            "path": "gateway", "profile": "web-js-ts", "role": "backend",
            "group": None, "size_est": 0, "timeout_hint": 3600, "max_loc": 0,
        }
        manifest_path = str(tmp_path / ".rebuild-components.json")
        mlib.emit_manifest(manifest_path, [reused, normal], str(tmp_path))
        entries = mlib.load_manifest(manifest_path, str(tmp_path))
        nxt = mlib.next_pending(entries)
        assert nxt is not None
        assert nxt["path"] == "gateway"
        assert nxt["status"] == "pending"
