# layout-exempt: rebuild-spec test — all docs/components paths here are this skill's own managed targets under test
"""Tests for _path_lib: shared write-safety guard + Phase R --root resolution."""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import _path_lib as pl  # noqa: E402


class TestResolveGuarded:
    def test_inside_base_ok(self, tmp_path):
        target = tmp_path / "docs" / "x.md"
        target.parent.mkdir()
        target.write_text("x")
        assert pl._resolve_guarded(str(target), str(tmp_path)).endswith("x.md")

    def test_escape_raises(self, tmp_path):
        base = tmp_path / "docs"
        base.mkdir()
        with pytest.raises(ValueError):
            pl._resolve_guarded(str(tmp_path / ".." / "evil.md"), str(base))


class TestComponentName:
    def test_path_based_not_basename(self):
        assert pl.component_name("services/payments/api") == "services-payments-api"
        assert pl.component_name("billing/api") == "billing-api"

    def test_collision_avoided(self):
        # The bug RT2-F14 guards: two different paths, same basename — must NOT collide.
        assert pl.component_name("services/payments/api") != pl.component_name("billing/api")


class TestResolveComponentPaths:
    def test_single_repo_default_is_legacy_layout(self, tmp_path):
        """en-primary (default None) → docs/ root — byte-identical to v22 back-compat."""
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(str(tmp_path), plan, root_arg=None)
        assert cp.name == ""
        assert cp.docs_root == str((tmp_path / "docs"))
        assert cp.state_file == str((tmp_path / "docs" / ".rebuild-state.json"))
        assert cp.plan_dir == str(Path(plan).resolve()) or cp.plan_dir.endswith("active")

    def test_root_scopes_per_component(self, tmp_path):
        """en-primary (default) → docs/components/<name> — byte-identical to v22 back-compat."""
        (tmp_path / "services" / "payments" / "api").mkdir(parents=True)
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(str(tmp_path), plan, root_arg="services/payments/api")
        assert cp.name == "services-payments-api"
        assert cp.docs_root.endswith("docs/components/services-payments-api")
        assert cp.state_file.endswith("docs/components/services-payments-api/.rebuild-state.json")
        assert cp.plan_dir.endswith("components/services-payments-api")

    def test_two_components_do_not_share_state(self, tmp_path):
        (tmp_path / "services" / "payments" / "api").mkdir(parents=True)
        (tmp_path / "billing" / "api").mkdir(parents=True)
        plan = str(tmp_path / "plans" / "active")
        a = pl.resolve_component_paths(str(tmp_path), plan, "services/payments/api")
        b = pl.resolve_component_paths(str(tmp_path), plan, "billing/api")
        assert a.state_file != b.state_file
        assert a.docs_root != b.docs_root

    def test_root_escaping_project_raises(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        plan = str(proj / "plans" / "active")
        with pytest.raises(ValueError):
            pl.resolve_component_paths(str(proj), plan, root_arg="../outside")

    # --- v23 primary_lang tests ---

    def test_en_primary_explicit_unchanged(self, tmp_path):
        """primary_lang='en' → same docs/components/<name> as default — BYTE-IDENTICAL to v22."""
        (tmp_path / "services" / "api").mkdir(parents=True)
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(
            str(tmp_path), plan, root_arg="services/api", primary_lang="en"
        )
        assert cp.docs_root.endswith("docs/components/services-api")
        assert cp.state_file.endswith("docs/components/services-api/.rebuild-state.json")

    def test_en_primary_single_repo_unchanged(self, tmp_path):
        """primary_lang='en', no root_arg → docs/ root — BYTE-IDENTICAL to v22 back-compat."""
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(str(tmp_path), plan, root_arg=None, primary_lang="en")
        assert cp.docs_root == str(tmp_path / "docs")
        assert cp.state_file == str(tmp_path / "docs" / ".rebuild-state.json")

    def test_non_en_primary_namespaces_component(self, tmp_path):
        """primary_lang='vi', --root → docs/vi/components/<name> (v23 breaking change)."""
        (tmp_path / "services" / "api").mkdir(parents=True)
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(
            str(tmp_path), plan, root_arg="services/api", primary_lang="vi"
        )
        assert cp.docs_root.endswith("docs/vi/components/services-api"), (
            f"expected docs/vi/components/services-api, got {cp.docs_root}"
        )
        assert cp.state_file.endswith("docs/vi/components/services-api/.rebuild-state.json")
        assert cp.plan_dir.endswith("components/services-api")

    def test_non_en_primary_single_repo_namespaced(self, tmp_path):
        """primary_lang='vi', no root_arg → docs/vi/ root (non-en single-repo)."""
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(str(tmp_path), plan, root_arg=None, primary_lang="vi")
        assert cp.docs_root == str(tmp_path / "docs" / "vi")
        assert cp.state_file == str(tmp_path / "docs" / "vi" / ".rebuild-state.json")

    def test_non_en_primary_no_docs_components_source_created(self, tmp_path):
        """vi-primary: resolve NEVER returns docs/components/<name> (old en path)."""
        (tmp_path / "svc").mkdir()
        plan = str(tmp_path / "plans" / "active")
        cp = pl.resolve_component_paths(
            str(tmp_path), plan, root_arg="svc", primary_lang="vi"
        )
        assert "docs/components" not in cp.docs_root.replace("\\", "/"), (
            f"vi-primary must NOT use docs/components/, got {cp.docs_root}"
        )
        assert "docs/vi/components" in cp.docs_root.replace("\\", "/")
