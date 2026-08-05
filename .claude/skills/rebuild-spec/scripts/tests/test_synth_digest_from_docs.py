"""Tests for synth_digest_from_docs.py + _reused_digest_parse_lib.py (Phase 07).

Coverage:
- route-list → inbound rpc entries
- entities.md → entity[] entries
- architecture.md → rpc outbound + topic entries
- missing sections → empty arrays + SIGNAL_INFERRED markers
- full digest: schema-valid (passes _check_caps + source_sha/generated_at required)
- generated_at and source_sha come from args, not wall-clock (determinism)
- multi-lang docs root: IDs still extracted from vi/jp docs
- path guard: rejects .. / symlink escape
- cap overflow: raises on violation
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import synth_digest_from_docs as sdd
import _reused_digest_parse_lib as parse_lib
from _system_synthesis_lib import _check_caps


# ---------------------------------------------------------------------------
# Sample doc content
# ---------------------------------------------------------------------------

ROUTE_LIST_EN = """\
# Route List

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | /api/employees | EmployeeController.list | List employees |
| POST | /api/employees | EmployeeController.create | Create employee |
| GET | /api/employees/:id | EmployeeController.get | Get by ID |
"""

ENTITIES_EN = """\
# Entities

## Employee

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| name | string | Name |

## Department

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| name | string | Dept name |
"""

ARCH_EN = """\
# Architecture

## Service Interactions

| From | To | Method | Description |
|------|----|--------|-------------|
| employee-frontend | employee-backend | GET /api/employees | Fetch list |

## Events

| Topic | Role | Event |
|-------|------|-------|
| employee.created | producer | EmployeeCreated |
| employee.updated | producer | EmployeeUpdated |
"""

ROUTE_LIST_VI = """\
# Danh Sách Route

| Phương thức | Đường dẫn | Bộ xử lý | Mô tả |
|-------------|-----------|----------|-------|
| GET | /api/nhan-vien | NhanVienController.list | Danh sách |
| POST | /api/nhan-vien | NhanVienController.create | Tạo mới |
"""

ENTITIES_JP = """\
# エンティティ

## Jugyoin

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | uuid | 主キー |
| namae | string | 名前 |
"""


def _make_docs(root: Path, lang: str = "en") -> Path:
    """Create a minimal docs/ tree under root for the given language."""
    lang_dir = root / lang
    (lang_dir / "generated").mkdir(parents=True)
    (lang_dir / "system").mkdir(parents=True)
    (lang_dir / "generated" / "route-list.md").write_text(ROUTE_LIST_EN, encoding="utf-8")
    (lang_dir / "generated" / "entities.md").write_text(ENTITIES_EN, encoding="utf-8")
    (lang_dir / "system" / "architecture.md").write_text(ARCH_EN, encoding="utf-8")
    return lang_dir


def _make_flat_docs(root: Path) -> Path:
    """Create a flat docs/ (no lang subdir, primary_lang=en)."""
    (root / "generated").mkdir(parents=True)
    (root / "system").mkdir(parents=True)
    (root / "generated" / "route-list.md").write_text(ROUTE_LIST_EN, encoding="utf-8")
    (root / "generated" / "entities.md").write_text(ENTITIES_EN, encoding="utf-8")
    (root / "system" / "architecture.md").write_text(ARCH_EN, encoding="utf-8")
    return root


def _write_state(docs_root: Path, primary_lang: str = "en") -> None:
    (docs_root / ".rebuild-state.json").write_text(
        json.dumps({"schema_version": "21.0.0", "primary_lang": primary_lang}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

class TestParseRouteList:
    def test_extracts_inbound_rpc(self):
        rpcs, signal = parse_lib.parse_route_list(ROUTE_LIST_EN)
        assert signal == ""
        names = {r["name"] for r in rpcs}
        assert "GET /api/employees" in names
        assert "POST /api/employees" in names

    def test_all_directions_inbound(self):
        rpcs, _ = parse_lib.parse_route_list(ROUTE_LIST_EN)
        assert all(r["direction"] == "inbound" for r in rpcs)

    def test_empty_text_gives_signal(self):
        rpcs, signal = parse_lib.parse_route_list("")
        assert rpcs == []
        assert signal == parse_lib.SIGNAL_INFERRED

    def test_no_table_gives_signal(self):
        rpcs, signal = parse_lib.parse_route_list("# Just a heading\n\nSome prose.")
        assert rpcs == []
        assert signal == parse_lib.SIGNAL_INFERRED

    def test_vi_route_list(self):
        rpcs, signal = parse_lib.parse_route_list(ROUTE_LIST_VI)
        assert signal == ""
        names = {r["name"] for r in rpcs}
        assert "GET /api/nhan-vien" in names

    def test_ignores_non_http_method_columns(self):
        text = """\
# Data

| Name | Value |
|------|-------|
| foo | bar |
"""
        rpcs, signal = parse_lib.parse_route_list(text)
        assert rpcs == []


class TestParseEntities:
    def test_extracts_entity_names(self):
        entities, signal = parse_lib.parse_entities(ENTITIES_EN)
        assert signal == ""
        names = {e["name"] for e in entities}
        assert "Employee" in names
        assert "Department" in names

    def test_extracts_id_field(self):
        entities, _ = parse_lib.parse_entities(ENTITIES_EN)
        emp = next(e for e in entities if e["name"] == "Employee")
        assert emp["id_field"] == "id"
        assert emp["id_type"] == "uuid"

    def test_default_visibility_internal(self):
        entities, _ = parse_lib.parse_entities(ENTITIES_EN)
        for e in entities:
            assert e["visibility"] == "internal"

    def test_empty_text_gives_signal(self):
        entities, signal = parse_lib.parse_entities("")
        assert entities == []
        assert signal == parse_lib.SIGNAL_INFERRED

    def test_jp_entities(self):
        entities, signal = parse_lib.parse_entities(ENTITIES_JP)
        assert signal == ""
        names = {e["name"] for e in entities}
        assert "Jugyoin" in names

    def test_skips_doc_section_headings(self):
        """Section headings are not emitted as entities; MODEL-prefix is canonicalized (Phase 01)."""
        text = (
            "## Entity Relationship Diagram\n\n"
            "## Summary\n\n"
            "## MODEL004 — Candidate\n\n"
            "## Staff\n\n"
        )
        entities, signal = parse_lib.parse_entities(text)
        names = {e["name"] for e in entities}
        assert names == {"Candidate", "Staff"}
        assert "Summary" not in names


class TestParseArchitecture:
    def test_extracts_outbound_rpc(self):
        rpcs, topics, signal = parse_lib.parse_architecture(ARCH_EN)
        # Should have outbound rpc from interaction table
        assert any(r["direction"] == "outbound" for r in rpcs)

    def test_extracts_topics(self):
        rpcs, topics, signal = parse_lib.parse_architecture(ARCH_EN)
        names = {t["name"] for t in topics}
        assert "employee.created" in names
        assert "employee.updated" in names

    def test_topic_roles(self):
        rpcs, topics, _ = parse_lib.parse_architecture(ARCH_EN)
        for t in topics:
            assert t["role"] in ("producer", "consumer")

    def test_empty_arch_gives_signal(self):
        rpcs, topics, signal = parse_lib.parse_architecture("")
        assert rpcs == []
        assert topics == []
        assert signal == parse_lib.SIGNAL_INFERRED


# ---------------------------------------------------------------------------
# build_digest unit tests
# ---------------------------------------------------------------------------

class TestBuildDigest:
    def test_schema_fields_present(self, tmp_path):
        docs = tmp_path / "docs"
        _make_flat_docs(docs)
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc123", generated_at="2026-06-24T12:00:00Z",
        )
        for field in ("service", "role", "generated_at", "source_sha", "rpc", "topic", "entity"):
            assert field in digest, f"Missing field: {field}"

    def test_generated_at_from_arg_not_wallclock(self, tmp_path):
        docs = tmp_path / "docs"
        _make_flat_docs(docs)
        fixed_ts = "2026-01-01T00:00:00Z"
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="sha1", generated_at=fixed_ts,
        )
        assert digest["generated_at"] == fixed_ts

    def test_source_sha_from_arg(self, tmp_path):
        docs = tmp_path / "docs"
        _make_flat_docs(docs)
        sha = "deadbeef" * 8
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha=sha, generated_at="2026-06-24T12:00:00Z",
        )
        assert digest["source_sha"] == sha

    def test_passes_check_caps(self, tmp_path):
        docs = tmp_path / "docs"
        _make_flat_docs(docs)
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc123", generated_at="2026-06-24T12:00:00Z",
        )
        # Should not raise
        _check_caps(digest, "test")

    def test_missing_route_list_gives_signal(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "generated").mkdir()
        (docs / "system").mkdir()
        # No route-list.md
        (docs / "generated" / "entities.md").write_text(ENTITIES_EN)
        (docs / "system" / "architecture.md").write_text(ARCH_EN)
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc", generated_at="2026-06-24T12:00:00Z",
        )
        assert "_signals" in digest
        assert any("rpc" in s and "SIGNAL_INFERRED" in s for s in digest["_signals"])

    def test_all_missing_gives_signals(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc", generated_at="2026-06-24T12:00:00Z",
        )
        signals = digest.get("_signals", [])
        assert len(signals) >= 3  # rpc, entity, arch all signalled

    def test_lang_mapped_vi_docs(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_state(docs, primary_lang="vi")
        vi_dir = docs / "vi"
        (vi_dir / "generated").mkdir(parents=True)
        (vi_dir / "system").mkdir(parents=True)
        (vi_dir / "generated" / "route-list.md").write_text(ROUTE_LIST_VI, encoding="utf-8")
        (vi_dir / "generated" / "entities.md").write_text(ENTITIES_EN, encoding="utf-8")
        (vi_dir / "system" / "architecture.md").write_text(ARCH_EN, encoding="utf-8")
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc", generated_at="2026-06-24T12:00:00Z",
        )
        rpc_names = {r["name"] for r in digest["rpc"] if r["direction"] == "inbound"}
        assert "GET /api/nhan-vien" in rpc_names

    def test_lang_mapped_jp_docs(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_state(docs, primary_lang="jp")
        jp_dir = docs / "jp"
        (jp_dir / "generated").mkdir(parents=True)
        (jp_dir / "system").mkdir(parents=True)
        (jp_dir / "generated" / "route-list.md").write_text(
            "# ルート\n\n| メソッド | パス | ハンドラ |\n|---------|------|------|\n| GET | /api/jugyoin | X |\n",
            encoding="utf-8"
        )
        (jp_dir / "generated" / "entities.md").write_text(ENTITIES_JP, encoding="utf-8")
        (jp_dir / "system" / "architecture.md").write_text(ARCH_EN, encoding="utf-8")
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc", generated_at="2026-06-24T12:00:00Z",
        )
        rpc_names = {r["name"] for r in digest["rpc"] if r["direction"] == "inbound"}
        assert "GET /api/jugyoin" in rpc_names

    def test_fixture_docs_valid(self, tmp_path):
        """The committed fixture employee/docs/en/ parses to a valid digest."""
        import shutil
        fixture_docs = FIXTURES_DIR / "monorepo_reused" / "employee" / "docs"
        dest_docs = tmp_path / "docs"
        shutil.copytree(str(fixture_docs), str(dest_docs))
        digest = sdd.build_digest(
            docs_root=str(dest_docs), name="employee", role="service",
            source_sha="abc123def456abc123def456abc123def456abc1",
            generated_at="2026-06-24T12:00:00Z",
            primary_lang="en",
        )
        _check_caps(digest, "fixture_test")
        assert digest["service"] == "employee"
        assert len(digest["rpc"]) > 0 or "_signals" in digest  # at minimum signals present

    def test_lang_mapped_ja_fallback(self, tmp_path):
        """When primary_lang='jp' but only ja/ exists, resolve_lang_root falls back to ja/."""
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_state(docs, primary_lang="jp")
        # Create ja/ instead of jp/
        ja_dir = docs / "ja"
        (ja_dir / "generated").mkdir(parents=True)
        (ja_dir / "system").mkdir(parents=True)
        (ja_dir / "generated" / "route-list.md").write_text(
            "# ルート\n\n| メソッド | パス |\n|---------|------|\n| GET | /api/x |\n",
            encoding="utf-8"
        )
        (ja_dir / "generated" / "entities.md").write_text(ENTITIES_JP, encoding="utf-8")
        (ja_dir / "system" / "architecture.md").write_text(ARCH_EN, encoding="utf-8")
        digest = sdd.build_digest(
            docs_root=str(docs), name="employee", role="service",
            source_sha="abc", generated_at="2026-06-24T12:00:00Z",
            primary_lang="jp",  # Request jp, but it doesn't exist
        )
        # Should still parse ja/ and extract entities
        assert len(digest.get("entity", [])) > 0, "Should have parsed from ja/ fallback"


# ---------------------------------------------------------------------------
# self_check
# ---------------------------------------------------------------------------

class TestSelfCheck:
    def test_cap_overflow_raises(self):
        digest = {
            "service": "x",
            "role": "service",
            "generated_at": "2026-06-24T12:00:00Z",
            "source_sha": "abc",
            "rpc": [{"name": "a" * 257, "direction": "inbound"}],
            "topic": [],
            "entity": [],
        }
        with pytest.raises(ValueError, match="exceeds"):
            sdd.self_check(digest, "test")

    def test_empty_source_sha_raises(self):
        digest = {
            "service": "x", "role": "service",
            "generated_at": "2026-06-24T12:00:00Z", "source_sha": "",
            "rpc": [], "topic": [], "entity": [],
        }
        with pytest.raises(ValueError, match="source_sha"):
            sdd.self_check(digest, "test")

    def test_empty_generated_at_raises(self):
        digest = {
            "service": "x", "role": "service",
            "generated_at": "", "source_sha": "abc",
            "rpc": [], "topic": [], "entity": [],
        }
        with pytest.raises(ValueError, match="generated_at"):
            sdd.self_check(digest, "test")


# ---------------------------------------------------------------------------
# write_digest / path guard
# ---------------------------------------------------------------------------

class TestWriteDigest:
    def _minimal_digest(self) -> dict:
        return {
            "service": "emp", "role": "service",
            "generated_at": "2026-06-24T12:00:00Z", "source_sha": "abc123",
            "rpc": [], "topic": [], "entity": [],
        }

    def test_writes_valid_json(self, tmp_path):
        out = str(tmp_path / "comps" / "emp" / "_service-digest.json")
        sdd.write_digest(out, self._minimal_digest())
        data = json.loads(Path(out).read_text())
        assert data["service"] == "emp"

    def test_no_tmp_files_left(self, tmp_path):
        out = str(tmp_path / "_service-digest.json")
        sdd.write_digest(out, self._minimal_digest())
        assert list(tmp_path.glob("*.json")) == [Path(out)]

    def test_path_guard_rejects_traversal(self, tmp_path):
        out = str(tmp_path / ".." / "_service-digest.json")
        with pytest.raises(ValueError, match="traversal"):
            sdd.write_digest(out, self._minimal_digest(), project_root=str(tmp_path))


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCLI:
    def _run(self, tmp_path: Path, extra: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "synth_digest_from_docs.py")] + extra,
            capture_output=True, text=True, timeout=30, cwd=str(tmp_path),
        )

    def test_cli_produces_valid_digest(self, tmp_path):
        import shutil
        fixture_docs = FIXTURES_DIR / "monorepo_reused" / "employee" / "docs"
        dest_docs = tmp_path / "docs"
        shutil.copytree(str(fixture_docs), str(dest_docs))
        out = str(tmp_path / "_service-digest.json")
        r = self._run(tmp_path, [
            "--docs-root", str(dest_docs),
            "--name", "employee",
            "--role", "service",
            "--source-sha", "abc123def456abc123def456abc123def456abc1",
            "--generated-at", "2026-06-24T12:00:00Z",
            "--out", out,
            "--primary-lang", "en",
        ])
        assert r.returncode == 0, r.stderr
        result = json.loads(r.stdout)
        assert result["status"] == "ok"
        digest = json.loads(Path(out).read_text())
        assert digest["service"] == "employee"
        assert digest["generated_at"] == "2026-06-24T12:00:00Z"
        assert digest["source_sha"] == "abc123def456abc123def456abc123def456abc1"

    def test_cli_deterministic(self, tmp_path):
        """Two runs with same args produce identical output."""
        import shutil
        fixture_docs = FIXTURES_DIR / "monorepo_reused" / "employee" / "docs"
        dest_docs = tmp_path / "docs"
        shutil.copytree(str(fixture_docs), str(dest_docs))
        out1 = str(tmp_path / "d1.json")
        out2 = str(tmp_path / "d2.json")
        args = [
            "--docs-root", str(dest_docs), "--name", "employee",
            "--role", "service", "--source-sha", "abc123",
            "--generated-at", "2026-06-24T12:00:00Z",
        ]
        self._run(tmp_path, args + ["--out", out1])
        self._run(tmp_path, args + ["--out", out2])
        assert Path(out1).read_text() == Path(out2).read_text()

    def test_cli_missing_docs_root_exits_1(self, tmp_path):
        r = self._run(tmp_path, [
            "--docs-root", str(tmp_path / "nonexistent"),
            "--name", "emp", "--role", "service",
            "--source-sha", "abc", "--generated-at", "2026-06-24T12:00:00Z",
            "--out", str(tmp_path / "out.json"),
        ])
        assert r.returncode == 1
