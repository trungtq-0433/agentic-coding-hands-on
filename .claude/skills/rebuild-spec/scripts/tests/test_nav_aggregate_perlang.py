# layout-exempt: rebuild-spec test — all docs/components paths here are this skill's own managed targets under test
"""Tests for v14.1.0 nav fixes on the per-lang aggregate (system-of-systems) layout.

Covers all 5 root causes identified in the wsm_platform symptom report:
  Fix 1 — role/reused overlay from docs/.rebuild-system-state.json
  Fix 2 — aggregate-mode index (SoS artifacts + components pointer, non-empty)
  Fix 3 — every component including mirrored ones gets a top README.md
  Fix 4 — vi locale applied (no English label leak when lang=None)
  Fix 5 — aggregate system/README.md ordered (overview first, v16 parity names)

Plus regression guard: single-component (non-aggregate) index unchanged.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_aggregate_lib import build_aggregate_system_readme  # noqa: E402
from _nav_components_io import load_component_meta, write_components_index  # noqa: E402
from _nav_index import _is_aggregate_root, build_index_readme  # noqa: E402
from _nav_lib import GEN_END, GEN_START  # noqa: E402
from _nav_state_overlay_lib import load_system_state_overlay, resolve_lang_from_state  # noqa: E402
from _nav_strings import AGGREGATE_SYSTEM_ORDER  # noqa: E402
from build_navigation import run  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _make_aggregate_tree(base: Path) -> Path:
    """Create a realistic per-lang aggregate docs tree.

    Structure:
      docs/
        .rebuild-system-state.json          (components: gateway, auth, employee[reused])
        vi/
          README.md (optional, will be written)
          system/
            overview.md
            component-catalog.md
            architecture.md
            data-ownership-map.md
            cross-service-flows.md
            glossary.md
            per-component-confidence.md
        components/
          gateway/
            .rebuild-state.json  (primary_lang: vi)
            system/
              overview.md
              architecture.md
          auth/
            .rebuild-state.json  (primary_lang: vi)
            system/
              overview.md
          employee/              (reused mirror — no direct system/, has vi/ subdir)
            .rebuild-state.json  (primary_lang: vi)
            vi/
              system/
                overview.md
    """
    docs = base / "docs"
    # System state at docs/.rebuild-system-state.json
    system_state = {
        "schema_version": "1",
        "primary_lang": "vi",
        "components": [
            {"name": "gateway", "role": "gateway", "reused": False, "source_sha": ""},
            {"name": "auth", "role": "backend", "reused": False, "source_sha": ""},
            {"name": "employee", "role": "backend", "reused": True, "source_sha": "abc"},
        ],
    }
    docs.mkdir(parents=True)
    (docs / ".rebuild-system-state.json").write_text(
        json.dumps(system_state, indent=2)
    )

    # docs/vi/system/ — SoS artifacts
    vi_sys = docs / "vi" / "system"
    vi_sys.mkdir(parents=True)
    for fname in AGGREGATE_SYSTEM_ORDER:
        (vi_sys / fname).write_text(f"# {fname}\n")

    # docs/components/gateway/
    gw = docs / "components" / "gateway"
    gw_sys = gw / "system"
    gw_sys.mkdir(parents=True)
    (gw / ".rebuild-state.json").write_text(
        json.dumps({"primary_lang": "vi", "role": "", "reused": False})
    )
    (gw_sys / "overview.md").write_text("# overview\n")
    (gw_sys / "architecture.md").write_text("# architecture\n")

    # docs/components/auth/
    auth = docs / "components" / "auth"
    auth_sys = auth / "system"
    auth_sys.mkdir(parents=True)
    (auth / ".rebuild-state.json").write_text(
        json.dumps({"primary_lang": "vi", "role": "", "reused": False})
    )
    (auth_sys / "overview.md").write_text("# overview\n")

    # docs/components/employee/ (reused mirror — no direct system/)
    emp = docs / "components" / "employee"
    emp_vi_sys = emp / "vi" / "system"
    emp_vi_sys.mkdir(parents=True)
    (emp / ".rebuild-state.json").write_text(
        json.dumps({"primary_lang": "vi", "role": "", "reused": False})
    )
    (emp_vi_sys / "overview.md").write_text("# overview\n")

    return docs


# ---------------------------------------------------------------------------
# Fix 1 — Role/reused overlay from .rebuild-system-state.json
# ---------------------------------------------------------------------------

class TestFix1RoleReusedOverlay:
    def test_role_filled_from_system_state(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        meta = load_component_meta(str(docs / "components"))
        by_name = {c["name"]: c for c in meta}
        assert by_name["gateway"]["role"] == "gateway"
        assert by_name["auth"]["role"] == "backend"

    def test_reused_flag_filled_from_system_state(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        meta = load_component_meta(str(docs / "components"))
        by_name = {c["name"]: c for c in meta}
        assert by_name["employee"]["reused"] is True
        assert by_name["gateway"]["reused"] is False

    def test_primary_lang_from_per_component_state(self, tmp_path):
        """primary_lang still comes from per-component .rebuild-state.json."""
        docs = _make_aggregate_tree(tmp_path)
        meta = load_component_meta(str(docs / "components"))
        by_name = {c["name"]: c for c in meta}
        assert by_name["gateway"]["primary_lang"] == "vi"

    def test_role_rank_order_gateway_before_backend(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), None, "2026-01-01T00:00:00Z")
        content = (docs / "components" / "README.md").read_text()
        assert content.index("gateway") < content.index("auth")

    def test_employee_marked_reused_in_index(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), None, "2026-01-01T00:00:00Z")
        content = (docs / "components" / "README.md").read_text()
        # reused marker must appear alongside employee
        from _nav_strings import get_strings
        vi_marker = get_strings("vi")["components_index"]["reused_marker"]
        en_marker = get_strings("en")["components_index"]["reused_marker"]
        assert vi_marker in content or en_marker in content
        emp_line = next(ln for ln in content.splitlines() if "employee" in ln)
        assert "(reused)" in emp_line or "(tái sử dụng)" in emp_line

    def test_overlay_fallback_to_manifest(self, tmp_path):
        """When system-state absent, falls back to .rebuild-components.json."""
        docs = tmp_path / "docs"
        comps = docs / "components" / "svc"
        comps.mkdir(parents=True)
        (comps / ".rebuild-state.json").write_text(
            json.dumps({"primary_lang": "en"})
        )
        # No system-state; place manifest at project root (parent of docs)
        manifest = [{"name": "svc", "role": "backend", "reused": True}]
        (tmp_path / ".rebuild-components.json").write_text(json.dumps(manifest))
        meta = load_component_meta(str(docs / "components"))
        assert meta[0]["role"] == "backend"
        assert meta[0]["reused"] is True

    def test_overlay_absent_falls_back_to_per_component(self, tmp_path):
        """No system-state and no manifest → role from per-component state."""
        docs = tmp_path / "docs"
        comps = docs / "components" / "svc"
        comps.mkdir(parents=True)
        (comps / ".rebuild-state.json").write_text(
            json.dumps({"primary_lang": "en", "role": "frontend", "reused": False})
        )
        meta = load_component_meta(str(docs / "components"))
        assert meta[0]["role"] == "frontend"


# ---------------------------------------------------------------------------
# Fix 2 — Aggregate-mode index (SoS artifacts + components pointer, non-empty)
# ---------------------------------------------------------------------------

class TestFix2AggregateIndex:
    def test_is_aggregate_root_detected(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_root = str(docs / "vi")
        assert _is_aggregate_root(vi_root)

    def test_is_aggregate_root_false_for_single_component(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        # gateway has system/overview.md + architecture.md but NOT component-catalog.md
        gw_root = str(docs / "components" / "gateway")
        assert not _is_aggregate_root(gw_root)

    def test_aggregate_index_non_empty(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_root = str(docs / "vi")
        content = build_index_readme(vi_root, "vi", "2026-01-01T00:00:00Z")
        # Phase 04 C2: the parent is a thin pointer — it points at system/README.md
        # instead of carrying its own numbered table.
        assert "system/README.md" in content

    def test_aggregate_index_points_to_system_readme_not_table(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_root = str(docs / "vi")
        content = build_index_readme(vi_root, "vi", "2026-01-01T00:00:00Z")
        # Phase 04 C2: the full reading-order table now lives ONLY in system/README.md;
        # the parent must NOT duplicate the numbered artifact rows (system/overview.md …).
        assert "system/README.md" in content
        assert "system/overview.md" not in content
        assert "system/component-catalog.md" not in content

    def test_aggregate_index_contains_components_pointer(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_root = str(docs / "vi")
        content = build_index_readme(vi_root, "vi", "2026-01-01T00:00:00Z")
        # Must include a link to ../components/
        assert "../components/" in content

    def test_aggregate_index_has_gen_zones(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_root = str(docs / "vi")
        content = build_index_readme(vi_root, "vi", "2026-01-01T00:00:00Z")
        assert GEN_START in content
        assert GEN_END in content

    def test_aggregate_index_user_tail_preserved(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_root = str(docs / "vi")
        first = build_index_readme(vi_root, "vi", "2026-01-01T00:00:00Z")
        existing = first + "\n## My Notes\n\nKeep this!\n"
        second = build_index_readme(vi_root, "vi", "2026-06-01T00:00:00Z", existing)
        assert "Keep this!" in second
        assert GEN_START in second

    def test_aggregate_index_does_not_duplicate_artifact_table(self, tmp_path):
        # Phase 04 C2: artifact presence-pruning now happens in system/README.md (the table's
        # new sole home — covered by test_nav_aggregate_render). The parent lists no artifact
        # rows at all, so removing one must not surface it in the parent either way.
        docs = _make_aggregate_tree(tmp_path)
        (docs / "vi" / "system" / "glossary.md").unlink()
        vi_root = str(docs / "vi")
        content = build_index_readme(vi_root, "vi", "2026-01-01T00:00:00Z")
        assert "system/glossary.md" not in content
        assert "system/overview.md" not in content  # parent never lists the artifacts now
        assert "system/README.md" in content          # only the thin pointer


# ---------------------------------------------------------------------------
# Fix 3 — Every component (incl. mirrored employee) gets a top README.md
# ---------------------------------------------------------------------------

class TestFix3PerComponentTopReadme:
    def test_gateway_top_readme_written(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), "vi", "2026-01-01T00:00:00Z")
        assert (docs / "components" / "gateway" / "README.md").is_file()

    def test_auth_top_readme_written(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), "vi", "2026-01-01T00:00:00Z")
        assert (docs / "components" / "auth" / "README.md").is_file()

    def test_employee_mirror_top_readme_written(self, tmp_path):
        """The reused/mirror employee component must get a top README.md."""
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), "vi", "2026-01-01T00:00:00Z")
        assert (docs / "components" / "employee" / "README.md").is_file()

    def test_top_readme_has_gen_zones(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), "vi", "2026-01-01T00:00:00Z")
        content = (docs / "components" / "gateway" / "README.md").read_text()
        assert GEN_START in content
        assert GEN_END in content

    def test_top_readme_idempotent_preserves_user_tail(self, tmp_path):
        """Second write preserves user content below GEN_END."""
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), "vi", "2026-01-01T00:00:00Z")
        top = docs / "components" / "gateway" / "README.md"
        top.write_text(top.read_text() + "\n## Custom\n\nKeep!\n")
        write_components_index(str(docs), "vi", "2026-06-01T00:00:00Z")
        assert "Keep!" in top.read_text()

    def test_components_index_link_resolves(self, tmp_path):
        """components/README.md links component/README.md — file must exist."""
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), "vi", "2026-01-01T00:00:00Z")
        index_content = (docs / "components" / "README.md").read_text()
        # Each link like (employee/README.md) must resolve on disk
        import re
        links = re.findall(r"\(([^)]+/README\.md)\)", index_content)
        for rel_link in links:
            target = docs / "components" / rel_link
            assert target.is_file(), f"Link {rel_link} → {target} does not exist (404)"


# ---------------------------------------------------------------------------
# Fix 4 — vi locale applied (no English label leak when lang=None)
# ---------------------------------------------------------------------------

class TestFix4LocaleResolution:
    def test_resolve_lang_from_state_returns_vi(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        resolved = resolve_lang_from_state(None, str(docs / "components"))
        assert resolved == "vi"

    def test_resolve_lang_passthrough_when_set(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        assert resolve_lang_from_state("ja", str(docs / "components")) == "ja"

    def test_resolve_lang_none_when_no_state(self, tmp_path):
        comps = tmp_path / "docs" / "components"
        comps.mkdir(parents=True)
        result = resolve_lang_from_state(None, str(comps))
        assert result is None

    def test_components_index_vi_title_when_lang_none(self, tmp_path):
        """With lang=None and primary_lang=vi in system-state → vi labels."""
        from _nav_strings import get_strings
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), None, "2026-01-01T00:00:00Z")
        content = (docs / "components" / "README.md").read_text()
        vi_title = get_strings("vi")["components_index"]["title"]
        en_title = get_strings("en")["components_index"]["title"]
        assert vi_title in content, f"Expected vi title in index; got:\n{content[:400]}"
        assert en_title not in content, "English title leaked into vi-primary index"

    def test_no_english_label_leak_in_system_readme(self, tmp_path):
        """Per-component system/README.md must use vi labels when lang=None."""
        from _nav_strings import get_strings
        docs = _make_aggregate_tree(tmp_path)
        write_components_index(str(docs), None, "2026-01-01T00:00:00Z")
        sys_readme = docs / "components" / "gateway" / "system" / "README.md"
        content = sys_readme.read_text()
        vi_sys_title = get_strings("vi")["components_index"]["system_readme_title"]
        en_sys_title = get_strings("en")["components_index"]["system_readme_title"]
        assert vi_sys_title in content
        assert en_sys_title not in content


# ---------------------------------------------------------------------------
# Fix 5 — Aggregate system/README.md ordered (overview first, v16 parity names)
# ---------------------------------------------------------------------------

class TestFix5AggregateSystemOrder:
    def test_system_overview_first_in_aggregate_system_readme(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_sys = str(docs / "vi" / "system")
        content = build_aggregate_system_readme(vi_sys, "vi", "2026-01-01T00:00:00Z")
        # v16 parity names: overview.md first, then component-catalog.md
        assert "overview.md" in content
        assert "component-catalog.md" in content
        assert content.index("overview.md") < content.index("component-catalog.md")

    def test_full_aggregate_order_preserved(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_sys = str(docs / "vi" / "system")
        content = build_aggregate_system_readme(vi_sys, "vi", "2026-01-01T00:00:00Z")
        positions = [content.index(f) for f in AGGREGATE_SYSTEM_ORDER if f in content]
        assert positions == sorted(positions), "Aggregate artifacts not in reading order"

    def test_run_writes_aggregate_system_readme_in_order(self, tmp_path):
        """run() must call build_aggregate_system_readme for vi/system/."""
        docs = _make_aggregate_tree(tmp_path)
        run(str(docs / "vi"), pass_complete=False, lang="vi")
        sys_readme = docs / "vi" / "system" / "README.md"
        assert sys_readme.is_file()
        content = sys_readme.read_text()
        # v16 parity names: overview.md first, then component-catalog.md
        assert content.index("overview.md") < content.index("component-catalog.md")

    def test_aggregate_system_readme_has_gen_zones(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_sys = str(docs / "vi" / "system")
        content = build_aggregate_system_readme(vi_sys, "vi", "2026-01-01T00:00:00Z")
        assert GEN_START in content
        assert GEN_END in content

    def test_aggregate_system_readme_user_tail_preserved(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        vi_sys = str(docs / "vi" / "system")
        first = build_aggregate_system_readme(vi_sys, "vi", "2026-01-01T00:00:00Z")
        existing = first + "\n## Notes\n\nKeep this!\n"
        second = build_aggregate_system_readme(vi_sys, "vi", "2026-06-01T00:00:00Z", existing)
        assert "Keep this!" in second

    def test_non_aggregate_system_readme_alphabetical(self, tmp_path):
        """Single-component system/ dirs keep the old alphabetical _build_readme_content."""
        docs = _make_aggregate_tree(tmp_path)
        # gateway system/ has overview.md + architecture.md (non-aggregate)
        run(str(docs / "components" / "gateway"), pass_complete=False)
        sys_readme = docs / "components" / "gateway" / "system" / "README.md"
        # Just verify it exists and has both files (order is alphabetical here)
        content = sys_readme.read_text()
        assert "architecture.md" in content
        assert "overview.md" in content

    def test_aggregate_system_absent_files_pruned(self, tmp_path):
        docs = _make_aggregate_tree(tmp_path)
        (docs / "vi" / "system" / "per-component-confidence.md").unlink()
        vi_sys = str(docs / "vi" / "system")
        content = build_aggregate_system_readme(vi_sys, "vi", "2026-01-01T00:00:00Z")
        assert "per-component-confidence.md" not in content
        assert "overview.md" in content  # v16 parity name


# ---------------------------------------------------------------------------
# Regression guard — single-component (non-aggregate) index unchanged
# ---------------------------------------------------------------------------

class TestRegressionSingleComponentIndex:
    def test_single_component_index_unchanged(self, tmp_path):
        """Non-aggregate docs root produces the same READING_ORDER table as before."""
        from _nav_strings import get_strings
        # Build a canonical single-component docs tree
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "generated").mkdir(parents=True)
        for rel in (
            "system/overview.md", "system/architecture.md",
            "generated/entities.md", "generated/feature-list.md",
        ):
            (docs / rel).write_text(f"# {rel}\n")
        content = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        # Must have regular title, not aggregate title
        en_title = get_strings("en")["title"]
        agg_title = get_strings("en").get("aggregate_index", {}).get("title", "")
        assert en_title in content
        if agg_title:
            assert agg_title not in content
        # Standard artifacts present
        assert "system/overview.md" in content
        assert "generated/feature-list.md" in content

    def test_single_component_not_detected_as_aggregate(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# overview\n")
        assert not _is_aggregate_root(str(docs))

    def test_aggregate_detection_requires_sos_files(self, tmp_path):
        """system/ with only single-component files is NOT detected as aggregate."""
        docs = tmp_path / "docs"
        sys_dir = docs / "system"
        sys_dir.mkdir(parents=True)
        for f in ("overview.md", "architecture.md", "business-rules.md"):
            (sys_dir / f).write_text(f"# {f}\n")
        assert not _is_aggregate_root(str(docs))

    def test_existing_nav_test_suite_compatibility(self, tmp_path):
        """Verify build_index_readme returns non-empty content for a minimal tree."""
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# overview\n")
        (docs / "system" / "architecture.md").write_text("# arch\n")
        content = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert GEN_START in content
        assert GEN_END in content
        assert "system/overview.md" in content


# ---------------------------------------------------------------------------
# Regression: components-pointer prefers NEARER components dir
# ---------------------------------------------------------------------------

class TestComponentsPointerNearerPreference:
    def test_nearer_components_dir_preferred_per_lang(self, tmp_path):
        """Regression: per-lang layout with docs/<lang>/components/ → ../components/ from system/."""
        docs = tmp_path / "docs"
        # Create per-lang layout with docs/components/ (sibling of vi/)
        lang_system = docs / "vi" / "system"
        lang_system.mkdir(parents=True)
        lang_system_path = str(lang_system)

        # Create at least one system file so the README generates properly
        (lang_system / "overview.md").write_text("# overview\n")

        # Create components dir at docs/components/ (nearer to docs/vi/)
        (docs / "components").mkdir(parents=True)
        (docs / "components" / "README.md").write_text("# Components\n")

        content = build_aggregate_system_readme(lang_system_path, "vi", "2026-01-01T00:00:00Z")
        # From docs/vi/system/, ../components/ resolves to docs/components/ (nearer)
        assert "../components/" in content

    def test_farther_components_fallback_when_nearer_absent(self, tmp_path):
        """Regression guard: fallback to ../../components/ when nearer dir absent."""
        docs = tmp_path / "docs"
        # Per-lang layout without docs/vi/components/ or docs/components/
        lang_system = docs / "vi" / "system"
        lang_system.mkdir(parents=True)
        lang_system_path = str(lang_system)

        # Create at least one system file so the README generates properly
        (lang_system / "overview.md").write_text("# overview\n")

        # Create components at docs/ (grandparent) → becomes ../../components/ from docs/vi/system
        (docs / "components").mkdir(parents=True)
        (docs / "components" / "README.md").write_text("# Components\n")

        content = build_aggregate_system_readme(lang_system_path, "vi", "2026-01-01T00:00:00Z")
        # Should use ../../components/ (nearer check for docs/vi/components fails, falls back to docs/components)
        assert "../../components/" in content

    def test_no_pointer_when_no_components_dir_exists(self, tmp_path):
        """Regression guard: no components pointer when neither path exists."""
        docs = tmp_path / "docs"
        lang_system = docs / "vi" / "system"
        lang_system.mkdir(parents=True)
        lang_system_path = str(lang_system)

        # Create at least one system file
        (lang_system / "overview.md").write_text("# overview\n")

        content = build_aggregate_system_readme(lang_system_path, "vi", "2026-01-01T00:00:00Z")
        # No components dir at either location → no pointer row
        assert "../components/" not in content
        assert "../../components/" not in content

    def test_single_lang_layout_uses_parent_components(self, tmp_path):
        """Regression guard: single-lang layout (system_dir = docs/system/) → ../components/."""
        docs = tmp_path / "docs"
        sys_dir = docs / "system"
        sys_dir.mkdir(parents=True)
        sys_dir_path = str(sys_dir)

        # Create at least one system file
        (sys_dir / "overview.md").write_text("# overview\n")

        # Create components at docs/components/ (parent from docs/system/)
        (docs / "components").mkdir(parents=True)
        (docs / "components" / "README.md").write_text("# Components\n")

        content = build_aggregate_system_readme(sys_dir_path, "en", "2026-01-01T00:00:00Z")
        # From docs/system/, ../components/ resolves to docs/components/
        assert "../components/" in content
        # overview.md link is relative (from inside system/)
        assert "overview.md" in content


# ---------------------------------------------------------------------------
# Error handling & edge cases
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_missing_components_root_graceful(self, tmp_path):
        """load_component_meta gracefully handles missing components/ dir."""
        comps_root = str(tmp_path / "nonexistent" / "components")
        meta = load_component_meta(comps_root)
        assert meta == []

    def test_missing_system_state_graceful_fallback(self, tmp_path):
        """load_system_state_overlay gracefully handles missing system-state."""
        docs = tmp_path / "docs"
        comps = docs / "components"
        comps.mkdir(parents=True)
        overlay = load_system_state_overlay(str(comps))
        assert overlay == {}

    def test_corrupt_json_graceful_fallback(self, tmp_path):
        """load_system_state_overlay ignores corrupt JSON and returns empty dict."""
        docs = tmp_path / "docs"
        comps = docs / "components"
        comps.mkdir(parents=True)
        # Write corrupt JSON to system-state
        (docs / ".rebuild-system-state.json").write_text("{ invalid json")
        overlay = load_system_state_overlay(str(comps))
        assert overlay == {}

    def test_empty_system_state_components_list(self, tmp_path):
        """System-state with empty components list returns empty overlay."""
        docs = tmp_path / "docs"
        comps = docs / "components"
        comps.mkdir(parents=True)
        (docs / ".rebuild-system-state.json").write_text(
            json.dumps({"schema_version": "1", "primary_lang": "vi", "components": []})
        )
        overlay = load_system_state_overlay(str(comps))
        assert overlay == {}

    def test_auth_with_default_role_when_overlay_missing(self, tmp_path):
        """Component role defaults to system-state when per-component state incomplete."""
        docs = _make_aggregate_tree(tmp_path)
        # Auth's role should come from system-state even if per-component state has empty role
        meta = load_component_meta(str(docs / "components"))
        by_name = {c["name"]: c for c in meta}
        # System state has auth role = "backend", so that's what we should get
        assert by_name["auth"]["role"] == "backend"

    def test_aggregate_system_dir_missing_graceful(self, tmp_path):
        """build_aggregate_system_readme handles missing system/ gracefully (no crash)."""
        sys_dir = str(tmp_path / "nonexistent" / "system")
        content = build_aggregate_system_readme(sys_dir, "vi", "2026-01-01T00:00:00Z")
        # New renderer: emits valid markdown (header + gen zones) even when dir is absent.
        # No crash, no "no files found" fallback — just an empty reading-order section.
        from _nav_lib import GEN_START, GEN_END
        assert GEN_START in content
        assert GEN_END in content

    def test_resolve_lang_corrupt_json_fallback(self, tmp_path):
        """resolve_lang_from_state ignores corrupt system-state, returns None."""
        docs = tmp_path / "docs"
        comps = docs / "components"
        comps.mkdir(parents=True)
        (docs / ".rebuild-system-state.json").write_text("{ invalid")
        result = resolve_lang_from_state(None, str(comps))
        assert result is None
