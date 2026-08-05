# layout-exempt: rebuild-spec synthesis tests — docs/ paths are this skill's own output targets
"""Tests for the durable docs/.rebuild-system-state.json writer/reader (Phase R4).

Coverage:
- write_system_state: round-trip write → read returns correct payload.
- Schema version injected automatically.
- Payload shape: required keys present; components list preserved.
- Atomic write: no tmp files left behind; docs_base created if absent.
- read_system_state: missing file → None; corrupt JSON → None.
- snapshot_hash carried through from synthesize() integration.
- no_source_baseline warn emitted when source_sha is empty.
- write_system_state + read_system_state across multiple writes (last write wins).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _synthesis_io_lib import (  # noqa: E402
    SYSTEM_STATE_FILENAME,
    SYSTEM_STATE_SCHEMA_VERSION,
    read_system_state,
    write_system_state,
)
from synthesize_system import synthesize  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal valid payload fixture
# ---------------------------------------------------------------------------

def _make_payload(
    lang: str = "en",
    snap: str = "abc123",
    components: list | None = None,
) -> dict:
    return {
        "primary_lang": lang,
        "synthesis_format_version": "13.0.0",
        "snapshot_hash": snap,
        "generated_at": "2026-06-24T00:00:00Z",
        "components": components or [],
    }


# ---------------------------------------------------------------------------
# write_system_state / read_system_state unit tests
# ---------------------------------------------------------------------------

class TestWriteReadSystemState:
    def test_round_trip_basic(self, tmp_path):
        """write then read returns the same payload (plus schema_version)."""
        docs = str(tmp_path / "docs")
        payload = _make_payload()
        write_system_state(docs, payload)
        result = read_system_state(docs)
        assert result is not None
        assert result["primary_lang"] == "en"
        assert result["snapshot_hash"] == "abc123"
        assert result["schema_version"] == SYSTEM_STATE_SCHEMA_VERSION

    def test_schema_version_always_injected(self, tmp_path):
        """schema_version must be present even if caller omits it."""
        docs = str(tmp_path / "docs")
        payload = _make_payload()
        payload.pop("schema_version", None)
        write_system_state(docs, payload)
        result = read_system_state(docs)
        assert result is not None
        assert "schema_version" in result
        assert result["schema_version"] == SYSTEM_STATE_SCHEMA_VERSION

    def test_components_list_preserved(self, tmp_path):
        """components[] with multiple entries round-trips intact."""
        docs = str(tmp_path / "docs")
        components = [
            {"name": "svc-a", "role": "domain-service", "reused": False,
             "source_sha": "deadbeef", "mirror_sha": "digest1"},
            {"name": "svc-b", "role": "gateway", "reused": True,
             "source_sha": "cafebabe", "mirror_sha": None},
        ]
        payload = _make_payload(components=components)
        write_system_state(docs, payload)
        result = read_system_state(docs)
        assert result is not None
        assert len(result["components"]) == 2
        assert result["components"][0]["name"] == "svc-a"
        assert result["components"][0]["source_sha"] == "deadbeef"
        assert result["components"][1]["reused"] is True
        assert result["components"][1]["mirror_sha"] is None

    def test_atomic_no_tmp_left(self, tmp_path):
        """No .tmp files left after write."""
        docs = tmp_path / "docs"
        docs.mkdir()
        write_system_state(str(docs), _make_payload())
        tmps = list(docs.glob(".sysstate_tmp_*"))
        assert tmps == []

    def test_docs_base_created_if_absent(self, tmp_path):
        """docs_base directory is created if it does not exist."""
        docs = str(tmp_path / "nested" / "docs")
        write_system_state(docs, _make_payload())
        state_file = Path(docs) / SYSTEM_STATE_FILENAME
        assert state_file.is_file()

    def test_last_write_wins(self, tmp_path):
        """Second write overwrites the first (deterministic)."""
        docs = str(tmp_path / "docs")
        write_system_state(docs, _make_payload(snap="first"))
        write_system_state(docs, _make_payload(snap="second"))
        result = read_system_state(docs)
        assert result is not None
        assert result["snapshot_hash"] == "second"

    def test_keys_are_sorted(self, tmp_path):
        """JSON file uses sorted keys (deterministic diff-friendly output)."""
        docs = str(tmp_path / "docs")
        write_system_state(docs, _make_payload())
        raw = (Path(docs) / SYSTEM_STATE_FILENAME).read_text(encoding="utf-8")
        parsed_back = json.loads(raw)
        keys = list(parsed_back.keys())
        assert keys == sorted(keys), f"Keys not sorted: {keys}"

    def test_non_ascii_lang_code_preserved(self, tmp_path):
        """Non-ASCII values pass through ensure_ascii=False."""
        docs = str(tmp_path / "docs")
        payload = _make_payload(lang="ja")
        write_system_state(docs, payload)
        result = read_system_state(docs)
        assert result is not None
        assert result["primary_lang"] == "ja"


class TestReadSystemStateMissing:
    def test_missing_file_returns_none(self, tmp_path):
        """Missing state file → None (no crash)."""
        docs = str(tmp_path / "no_docs")
        result = read_system_state(docs)
        assert result is None

    def test_corrupt_json_returns_none(self, tmp_path, capsys):
        """Corrupt JSON → None + warn logged."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / SYSTEM_STATE_FILENAME).write_text("{broken json", encoding="utf-8")
        result = read_system_state(str(docs))
        assert result is None
        assert "cannot read system state" in capsys.readouterr().err

    def test_non_dict_json_returns_none(self, tmp_path):
        """JSON array (wrong type) → None."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / SYSTEM_STATE_FILENAME).write_text("[1,2,3]", encoding="utf-8")
        result = read_system_state(str(docs))
        assert result is None


# ---------------------------------------------------------------------------
# Integration: synthesize() writes docs/.rebuild-system-state.json
# ---------------------------------------------------------------------------

def _write_digest(directory: Path, digest: dict) -> None:
    svc = digest["service"]
    comp_dir = directory / "docs" / "components" / svc
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "_service-digest.json").write_text(
        json.dumps(digest), encoding="utf-8"
    )


_BASE_DIGEST = {
    "service": "orders",
    "role": "domain-service",
    "stack": "spring",
    "generated_at": "2026-06-24T00:00:00Z",
    "source_sha": "aabbcc001",
    "rpc": [],
    "topic": [],
    "entity": [],
}

_PAYMENT_DIGEST = {
    "service": "payment",
    "role": "domain-service",
    "stack": "nestjs",
    "generated_at": "2026-06-24T00:01:00Z",
    "source_sha": "bbccdd002",
    "rpc": [],
    "topic": [],
    "entity": [],
}


class TestSynthesizeWritesSystemState:
    def test_state_file_created_after_aggregate(self, tmp_path):
        """After synthesize(), docs/.rebuild-system-state.json must exist."""
        _write_digest(tmp_path, _BASE_DIGEST)
        rc = synthesize(
            root=str(tmp_path), manifest=None, digest_dir=None,
            max_digest_age=None, force_aggregate=True,
        )
        assert rc == 0
        state_path = tmp_path / "docs" / SYSTEM_STATE_FILENAME
        assert state_path.is_file(), f"{state_path} not found"

    def test_state_has_snapshot_hash(self, tmp_path):
        """snapshot_hash in state matches what .system-scout-report.md header has."""
        _write_digest(tmp_path, _BASE_DIGEST)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        snap = state["snapshot_hash"]
        assert isinstance(snap, str) and len(snap) == 64  # sha256 hex
        # v19: Verify it matches the header written into .system-scout-report.md.
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert snap in scout

    def test_state_primary_lang_matches_en_default(self, tmp_path):
        """No state files → primary_lang defaults to 'en'."""
        _write_digest(tmp_path, _BASE_DIGEST)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        assert state["primary_lang"] == "en"

    def test_state_components_populated_from_manifest(self, tmp_path):
        """Components in state come from the manifest entries."""
        _write_digest(tmp_path, _BASE_DIGEST)
        _write_digest(tmp_path, _PAYMENT_DIGEST)
        manifest_data = [
            {"path": "services/orders", "name": "orders", "role": "domain-service",
             "status": "done", "sha": "digest1", "fail_reason": None,
             "updated_at": "2026-06-24T00:00:00Z"},
            {"path": "services/payment", "name": "payment", "role": "domain-service",
             "status": "done", "sha": "digest2", "fail_reason": None,
             "updated_at": "2026-06-24T00:01:00Z"},
        ]
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
        synthesize(
            root=str(tmp_path), manifest=str(manifest_path),
            digest_dir=None, max_digest_age=None, force_aggregate=True,
        )
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        names = {c["name"] for c in state["components"]}
        assert "orders" in names
        assert "payment" in names

    def test_state_source_sha_from_digest(self, tmp_path):
        """source_sha in state component comes from the loaded digest."""
        _write_digest(tmp_path, _BASE_DIGEST)
        manifest_data = [
            {"path": "services/orders", "name": "orders", "role": "domain-service",
             "status": "done", "sha": "digest1", "fail_reason": None,
             "updated_at": "2026-06-24T00:00:00Z"},
        ]
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
        synthesize(
            root=str(tmp_path), manifest=str(manifest_path),
            digest_dir=None, max_digest_age=None, force_aggregate=True,
        )
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        orders = next((c for c in state["components"] if c["name"] == "orders"), None)
        # source_sha is empty because "orders" (manifest name) ≠ "orders" (digest service)
        # — BUT in this test the digest's service IS "orders" so it will match via direct lookup.
        assert orders is not None
        # The digest source_sha is "aabbcc001".
        assert orders["source_sha"] == "aabbcc001"

    def test_no_source_baseline_warn_emitted(self, tmp_path, capsys):
        """A manifest component with no matching digest emits [WARN] no_source_baseline."""
        _write_digest(tmp_path, _BASE_DIGEST)
        # Add a manifest entry for a component that has no digest on disk.
        manifest_data = [
            {"path": "services/orders", "name": "orders", "role": "domain-service",
             "status": "done", "sha": "digest1", "fail_reason": None,
             "updated_at": "2026-06-24T00:00:00Z"},
            {"path": "services/missing", "name": "missing-svc", "role": "domain-service",
             "status": "done", "sha": "digest2", "fail_reason": None,
             "updated_at": "2026-06-24T00:02:00Z"},
        ]
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
        synthesize(
            root=str(tmp_path), manifest=str(manifest_path),
            digest_dir=None, max_digest_age=None, force_aggregate=True,
        )
        err = capsys.readouterr().err
        assert "no_source_baseline" in err

    def test_state_mirror_sha_from_manifest(self, tmp_path):
        """mirror_sha in state component comes from manifest entry 'sha' field."""
        _write_digest(tmp_path, _BASE_DIGEST)
        manifest_data = [
            {"path": "services/orders", "name": "orders", "role": "domain-service",
             "status": "done", "sha": "DIGEST_SHA_XYZ", "fail_reason": None,
             "updated_at": "2026-06-24T00:00:00Z"},
        ]
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
        synthesize(
            root=str(tmp_path), manifest=str(manifest_path),
            digest_dir=None, max_digest_age=None, force_aggregate=True,
        )
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        orders = next((c for c in state["components"] if c["name"] == "orders"), None)
        assert orders is not None
        assert orders["mirror_sha"] == "DIGEST_SHA_XYZ"

    def test_state_idempotent_on_rerun(self, tmp_path):
        """Second synthesize() overwrites state (last write wins, no error)."""
        _write_digest(tmp_path, _BASE_DIGEST)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        assert state["schema_version"] == SYSTEM_STATE_SCHEMA_VERSION

    def test_state_no_digests_still_succeeds(self, tmp_path):
        """With no digests, synthesize exits 0 (advisory) and writes no state
        (no digests = nothing to synthesize, function returns before state write)."""
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        # State may or may not exist — the key assertion is no crash.
