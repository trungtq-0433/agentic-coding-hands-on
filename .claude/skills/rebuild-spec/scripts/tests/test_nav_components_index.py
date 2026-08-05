# layout-exempt: rebuild-spec test — all docs/components paths here are this skill's own managed targets under test
"""Tests for _nav_components_index.py (renderers) and _nav_components_io.py (wiring).

Covers:
  - Role-rank ordering: gateway < backend < frontend < fullstack
  - Reused-last: reused components sort after fresh peers of same role, marked (reused)
  - Presence pruning: system/README.md only lists files that exist on disk
  - 2-zone tail preservation for both renderers
  - All three locales carry the same components_index keys
  - Auto-detect wiring: build_navigation.run() generates components/README.md when
    docs/components/ holds >= 1 component with a .rebuild-state.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_components_index import (  # noqa: E402
    _SYSTEM_READING_ORDER,
    _role_rank,
    _sort_components,
    build_component_system_readme,
    build_components_index_readme,
)
from _nav_components_io import load_component_meta, write_components_index  # noqa: E402
from _nav_lib import GEN_END, GEN_START  # noqa: E402
from _nav_strings import get_strings  # noqa: E402
from build_navigation import run  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_components_tree(base: Path, components: list[dict]) -> Path:
    """Create a docs/components/ tree with .rebuild-state.json per component.

    Each entry in components: {name, role, reused, primary_lang, system_files}
    system_files is a list of filenames to create in <name>/system/.
    """
    docs = base / "docs"
    comps_root = docs / "components"
    comps_root.mkdir(parents=True)
    for comp in components:
        comp_dir = comps_root / comp["name"]
        comp_dir.mkdir(parents=True)
        state = {
            "role": comp.get("role", ""),
            "reused": comp.get("reused", False),
            "primary_lang": comp.get("primary_lang", "en"),
        }
        (comp_dir / ".rebuild-state.json").write_text(json.dumps(state))
        sys_files = comp.get("system_files", [])
        if sys_files:
            sys_dir = comp_dir / "system"
            sys_dir.mkdir(parents=True)
            for fname in sys_files:
                (sys_dir / fname).write_text(f"# {fname}\n")
    return docs


# ---------------------------------------------------------------------------
# Role-rank ordering
# ---------------------------------------------------------------------------

class TestRoleRank:
    def test_gateway_rank_lowest(self):
        assert _role_rank("gateway", False) < _role_rank("backend", False)

    def test_api_gateway_same_as_gateway(self):
        assert _role_rank("api-gateway", False) == _role_rank("gateway", False)

    def test_backend_before_frontend(self):
        assert _role_rank("backend", False) < _role_rank("frontend", False)

    def test_frontend_before_fullstack(self):
        assert _role_rank("frontend", False) < _role_rank("fullstack", False)

    def test_reused_sorts_after_fresh_same_role(self):
        assert _role_rank("backend", True) > _role_rank("backend", False)

    def test_reused_backend_may_sort_after_fresh_frontend(self):
        # reused backend rank = 1 + 10 = 11; frontend rank = 2 → reused backend after frontend
        assert _role_rank("backend", True) > _role_rank("frontend", False)

    def test_unknown_role_defaults_to_backend(self):
        assert _role_rank("unknown-service", False) == _role_rank("backend", False)


class TestSortComponents:
    def test_gateway_first(self):
        meta = [
            {"name": "svc-b", "role": "backend", "reused": False},
            {"name": "gw", "role": "gateway", "reused": False},
            {"name": "fe", "role": "frontend", "reused": False},
        ]
        sorted_ = _sort_components(meta)
        assert sorted_[0]["name"] == "gw"

    def test_reused_last_within_same_role(self):
        meta = [
            {"name": "auth-reused", "role": "backend", "reused": True},
            {"name": "orders", "role": "backend", "reused": False},
        ]
        sorted_ = _sort_components(meta)
        assert sorted_[0]["name"] == "orders"
        assert sorted_[1]["name"] == "auth-reused"

    def test_full_order_gateway_backend_frontend_fullstack_reused(self):
        meta = [
            {"name": "fe", "role": "frontend", "reused": False},
            {"name": "auth", "role": "backend", "reused": True},
            {"name": "gw", "role": "gateway", "reused": False},
            {"name": "svc", "role": "backend", "reused": False},
            {"name": "app", "role": "fullstack", "reused": False},
        ]
        sorted_ = _sort_components(meta)
        names = [c["name"] for c in sorted_]
        assert names.index("gw") < names.index("svc")
        assert names.index("svc") < names.index("fe")
        assert names.index("fe") < names.index("app")
        assert names.index("app") < names.index("auth")

    def test_name_tiebreak(self):
        meta = [
            {"name": "z-svc", "role": "backend", "reused": False},
            {"name": "a-svc", "role": "backend", "reused": False},
        ]
        sorted_ = _sort_components(meta)
        assert sorted_[0]["name"] == "a-svc"


# ---------------------------------------------------------------------------
# build_components_index_readme — renderer 1
# ---------------------------------------------------------------------------

class TestBuildComponentsIndexReadme:
    def test_two_zone_structure(self, tmp_path):
        meta = [{"name": "api-gw", "role": "gateway", "reused": False}]
        content = build_components_index_readme(str(tmp_path), meta, "en", "2026-01-01T00:00:00Z")
        assert GEN_START in content
        assert GEN_END in content

    def test_module_table_rendered(self, tmp_path):
        meta = [
            {"name": "api-gw", "role": "gateway", "reused": False},
            {"name": "user-svc", "role": "backend", "reused": False},
        ]
        content = build_components_index_readme(str(tmp_path), meta, "en", "2026-01-01T00:00:00Z")
        assert "api-gw" in content
        assert "user-svc" in content

    def test_reused_marked(self, tmp_path):
        meta = [{"name": "auth-lib", "role": "backend", "reused": True}]
        content = build_components_index_readme(str(tmp_path), meta, "en", "2026-01-01T00:00:00Z")
        reused_marker = get_strings("en")["components_index"]["reused_marker"]
        assert reused_marker in content

    def test_gateway_listed_before_backend(self, tmp_path):
        meta = [
            {"name": "user-svc", "role": "backend", "reused": False},
            {"name": "api-gw", "role": "gateway", "reused": False},
        ]
        content = build_components_index_readme(str(tmp_path), meta, "en", "2026-01-01T00:00:00Z")
        assert content.index("api-gw") < content.index("user-svc")

    def test_link_path_format(self, tmp_path):
        meta = [{"name": "orders", "role": "backend", "reused": False}]
        content = build_components_index_readme(str(tmp_path), meta, "en", "2026-01-01T00:00:00Z")
        # Index lives AT docs/components/README.md → link is relative to it,
        # NOT prefixed with components/ (that would 404 at components/components/...).
        assert "(orders/README.md)" in content
        assert "components/orders/README.md" not in content

    def test_user_tail_preserved(self, tmp_path):
        meta = [{"name": "gw", "role": "gateway", "reused": False}]
        first = build_components_index_readme(str(tmp_path), meta, "en", "2026-01-01T00:00:00Z")
        existing = first + "\n## My Notes\n\nKeep this!\n"
        second = build_components_index_readme(str(tmp_path), meta, "en", "2026-06-01T00:00:00Z",
                                               existing_content=existing)
        assert "Keep this!" in second
        assert GEN_START in second
        assert GEN_END in second

    def test_vi_locale_title(self, tmp_path):
        meta = [{"name": "gw", "role": "gateway", "reused": False}]
        content = build_components_index_readme(str(tmp_path), meta, "vi", "2026-01-01T00:00:00Z")
        assert get_strings("vi")["components_index"]["title"] in content

    def test_ja_locale_title(self, tmp_path):
        meta = [{"name": "gw", "role": "gateway", "reused": False}]
        content = build_components_index_readme(str(tmp_path), meta, "ja", "2026-01-01T00:00:00Z")
        assert get_strings("ja")["components_index"]["title"] in content


# ---------------------------------------------------------------------------
# build_component_system_readme — renderer 2
# ---------------------------------------------------------------------------

class TestBuildComponentSystemReadme:
    def test_two_zone_structure(self, tmp_path):
        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        content = build_component_system_readme(str(sys_dir), "en", "2026-01-01T00:00:00Z")
        assert GEN_START in content
        assert GEN_END in content

    def test_presence_pruning_only_existing_files(self, tmp_path):
        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        (sys_dir / "overview.md").write_text("# overview\n")
        # architecture.md NOT created
        content = build_component_system_readme(str(sys_dir), "en", "2026-01-01T00:00:00Z")
        assert "overview.md" in content
        assert "architecture.md" not in content

    def test_reading_order_overview_before_architecture(self, tmp_path):
        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        (sys_dir / "overview.md").write_text("# o\n")
        (sys_dir / "architecture.md").write_text("# a\n")
        (sys_dir / "business-rules.md").write_text("# br\n")
        content = build_component_system_readme(str(sys_dir), "en", "2026-01-01T00:00:00Z")
        assert content.index("overview.md") < content.index("architecture.md")
        assert content.index("architecture.md") < content.index("business-rules.md")

    def test_all_system_reading_order_files(self, tmp_path):
        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        for fname in _SYSTEM_READING_ORDER:
            (sys_dir / fname).write_text(f"# {fname}\n")
        content = build_component_system_readme(str(sys_dir), "en", "2026-01-01T00:00:00Z")
        for fname in _SYSTEM_READING_ORDER:
            assert fname in content

    def test_empty_system_dir_no_crash(self, tmp_path):
        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        content = build_component_system_readme(str(sys_dir), "en", "2026-01-01T00:00:00Z")
        assert "no system documentation" in content

    def test_user_tail_preserved(self, tmp_path):
        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        (sys_dir / "overview.md").write_text("# o\n")
        first = build_component_system_readme(str(sys_dir), "en", "2026-01-01T00:00:00Z")
        existing = first + "\n## Notes\n\nKeep this!\n"
        second = build_component_system_readme(str(sys_dir), "en", "2026-06-01T00:00:00Z",
                                               existing_content=existing)
        assert "Keep this!" in second


# ---------------------------------------------------------------------------
# Locale key parity — all three locales must carry the same components_index keys
# ---------------------------------------------------------------------------

class TestLocaleKeyParity:
    def test_all_locales_have_components_index(self):
        for lang in ("en", "vi", "ja"):
            s = get_strings(lang)
            assert "components_index" in s, f"{lang} missing components_index block"

    def test_all_locales_have_same_components_index_keys(self):
        en_keys = set(get_strings("en")["components_index"].keys())
        for lang in ("vi", "ja"):
            lang_keys = set(get_strings(lang)["components_index"].keys())
            assert lang_keys == en_keys, (
                f"{lang} components_index keys differ from en: "
                f"missing={en_keys - lang_keys}, extra={lang_keys - en_keys}"
            )

    def test_all_locales_have_same_role_label_keys(self):
        en_role_keys = set(get_strings("en")["components_index"]["role_labels"].keys())
        for lang in ("vi", "ja"):
            lang_role_keys = set(get_strings(lang)["components_index"]["role_labels"].keys())
            assert lang_role_keys == en_role_keys, (
                f"{lang} role_labels keys differ from en"
            )


# ---------------------------------------------------------------------------
# I/O wiring — load_component_meta + write_components_index
# ---------------------------------------------------------------------------

class TestLoadComponentMeta:
    def test_reads_state_files(self, tmp_path):
        docs = _make_components_tree(tmp_path, [
            {"name": "gw", "role": "gateway", "reused": False},
            {"name": "svc", "role": "backend", "reused": True},
        ])
        meta = load_component_meta(str(docs / "components"))
        names = {c["name"] for c in meta}
        assert names == {"gw", "svc"}

    def test_skips_dirs_without_state(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        (comps / "no-state").mkdir()  # no .rebuild-state.json
        meta = load_component_meta(str(comps))
        assert meta == []

    def test_reused_flag_parsed(self, tmp_path):
        docs = _make_components_tree(tmp_path, [
            {"name": "lib", "role": "backend", "reused": True},
        ])
        meta = load_component_meta(str(docs / "components"))
        assert meta[0]["reused"] is True

    def test_corrupt_state_skipped_gracefully(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        bad = comps / "bad-svc"
        bad.mkdir()
        (bad / ".rebuild-state.json").write_text("not json {{{{")
        meta = load_component_meta(str(comps))
        # corrupt JSON → state treated as {} → entry still added with empty role
        assert len(meta) == 1
        assert meta[0]["role"] == ""


class TestWriteComponentsIndex:
    def test_writes_components_readme(self, tmp_path):
        docs = _make_components_tree(tmp_path, [
            {"name": "gw", "role": "gateway", "reused": False, "system_files": []},
        ])
        write_components_index(str(docs), "en", "2026-01-01T00:00:00Z")
        assert (docs / "components" / "README.md").is_file()

    def test_writes_system_readme_when_dir_exists(self, tmp_path):
        docs = _make_components_tree(tmp_path, [
            {"name": "svc", "role": "backend", "reused": False,
             "system_files": ["overview.md"]},
        ])
        write_components_index(str(docs), "en", "2026-01-01T00:00:00Z")
        sys_readme = docs / "components" / "svc" / "system" / "README.md"
        assert sys_readme.is_file()
        content = sys_readme.read_text()
        assert "overview.md" in content

    def test_no_components_no_readme(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "components").mkdir(parents=True)
        write_components_index(str(docs), "en", "2026-01-01T00:00:00Z")
        assert not (docs / "components" / "README.md").is_file()


# ---------------------------------------------------------------------------
# Integration — build_navigation.run() auto-detect
# ---------------------------------------------------------------------------

class TestRunAutoDetect:
    def test_run_auto_generates_components_index(self, tmp_path):
        """run() auto-detects docs/components/ and writes components/README.md."""
        docs = _make_components_tree(tmp_path, [
            {"name": "gw", "role": "gateway", "reused": False, "system_files": []},
            {"name": "svc", "role": "backend", "reused": False, "system_files": []},
        ])
        run(str(docs), pass_complete=False)
        assert (docs / "components" / "README.md").is_file()

    def test_run_components_index_flag(self, tmp_path):
        """--components-index flag triggers generation even without auto-detect."""
        docs = _make_components_tree(tmp_path, [
            {"name": "svc", "role": "backend", "reused": False, "system_files": []},
        ])
        run(str(docs), pass_complete=False, components_index=True)
        assert (docs / "components" / "README.md").is_file()

    def test_run_no_components_dir_no_crash(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# Overview\n")
        result = run(str(docs), pass_complete=False)
        assert result == 0
        assert not (docs / "components" / "README.md").exists()

    def test_components_index_reading_order_in_output(self, tmp_path):
        """components/README.md lists gateway before backend."""
        docs = _make_components_tree(tmp_path, [
            {"name": "user-svc", "role": "backend", "reused": False, "system_files": []},
            {"name": "api-gw", "role": "gateway", "reused": False, "system_files": []},
        ])
        run(str(docs), pass_complete=False)
        content = (docs / "components" / "README.md").read_text()
        assert content.index("api-gw") < content.index("user-svc")
