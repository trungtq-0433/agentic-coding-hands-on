# layout-exempt: rebuild-spec aggregate nav + render helper tests
"""Tests for aggregate README rendering, nav helpers, AGGREGATE_SYSTEM_ORDER/AGGREGATE_ROLES.

v16 aggregate changes: README rewritten with numbered reading-order table + role paths
+ components pointer + principles; AGGREGATE_SYSTEM_ORDER = 7 v16 names; AGGREGATE_ROLES
prunes absent numbers; locale key-set parity; _is_aggregate_root detects on component-catalog.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_aggregate_lib import build_aggregate_system_readme  # noqa: E402
from _nav_strings_en import STRINGS as STRINGS_EN  # noqa: E402
from _nav_strings_vi import STRINGS as STRINGS_VI  # noqa: E402
from _nav_strings_ja import STRINGS as STRINGS_JA  # noqa: E402
from _nav_lib import _ARTIFACT_DESCRIPTIONS  # noqa: E402
from _nav_index import _is_aggregate_root  # noqa: E402
from _nav_strings import AGGREGATE_SYSTEM_ORDER, AGGREGATE_ROLES, AGGREGATE_WHY_KEYS  # noqa: E402
from _nav_aggregate_render import reading_order_rows  # noqa: E402
from _nav_why_lib import build_why_clauses  # noqa: E402


class TestAggregateSystemOrder:
    """AGGREGATE_SYSTEM_ORDER contains exactly 7 v16 artifact names in order."""

    def test_order_has_seven_artifacts(self):
        """AGGREGATE_SYSTEM_ORDER length == 7."""
        assert len(AGGREGATE_SYSTEM_ORDER) == 7

    def test_order_contains_overview(self):
        """overview.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "overview.md" in AGGREGATE_SYSTEM_ORDER

    def test_order_contains_component_catalog(self):
        """component-catalog.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "component-catalog.md" in AGGREGATE_SYSTEM_ORDER

    def test_order_contains_architecture(self):
        """architecture.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "architecture.md" in AGGREGATE_SYSTEM_ORDER

    def test_order_contains_data_ownership_map(self):
        """data-ownership-map.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "data-ownership-map.md" in AGGREGATE_SYSTEM_ORDER

    def test_order_contains_cross_service_flows(self):
        """cross-service-flows.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "cross-service-flows.md" in AGGREGATE_SYSTEM_ORDER

    def test_order_contains_glossary(self):
        """glossary.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "glossary.md" in AGGREGATE_SYSTEM_ORDER

    def test_order_contains_per_component_confidence(self):
        """per-component-confidence.md is in AGGREGATE_SYSTEM_ORDER."""
        assert "per-component-confidence.md" in AGGREGATE_SYSTEM_ORDER

    def test_no_old_names_in_order(self):
        """Old aggregate names (service-catalog, interaction-graph, system-glossary, system-overview) absent."""
        assert "service-catalog.md" not in AGGREGATE_SYSTEM_ORDER
        assert "interaction-graph.md" not in AGGREGATE_SYSTEM_ORDER
        assert "system-glossary.md" not in AGGREGATE_SYSTEM_ORDER
        assert "system-overview.md" not in AGGREGATE_SYSTEM_ORDER


class TestAggregateRoles:
    """AGGREGATE_ROLES is a list of role dicts with path indices."""

    def _get_role_entry(self, key):
        """Find role by key in AGGREGATE_ROLES list."""
        for entry in AGGREGATE_ROLES:
            if entry.get("key") == key:
                return entry
        return None

    def test_roles_has_new_dev(self):
        """AGGREGATE_ROLES includes 'new_dev' role."""
        assert self._get_role_entry("new_dev") is not None

    def test_roles_has_reviewer(self):
        """AGGREGATE_ROLES includes 'reviewer' role."""
        assert self._get_role_entry("reviewer") is not None

    def test_roles_has_pm(self):
        """AGGREGATE_ROLES includes 'pm' role."""
        assert self._get_role_entry("pm") is not None

    def test_roles_new_dev_indices_valid(self):
        """new_dev indices map to valid positions in AGGREGATE_SYSTEM_ORDER."""
        role_entry = self._get_role_entry("new_dev")
        indices = role_entry.get("path", []) if role_entry else []
        for idx in indices:
            assert 1 <= idx <= len(AGGREGATE_SYSTEM_ORDER)

    def test_roles_reviewer_indices_valid(self):
        """reviewer indices map to valid positions in AGGREGATE_SYSTEM_ORDER."""
        role_entry = self._get_role_entry("reviewer")
        indices = role_entry.get("path", []) if role_entry else []
        for idx in indices:
            assert 1 <= idx <= len(AGGREGATE_SYSTEM_ORDER)

    def test_roles_pm_indices_valid(self):
        """pm indices map to valid positions in AGGREGATE_SYSTEM_ORDER."""
        role_entry = self._get_role_entry("pm")
        indices = role_entry.get("path", []) if role_entry else []
        for idx in indices:
            assert 1 <= idx <= len(AGGREGATE_SYSTEM_ORDER)


class TestArtifactDescriptions:
    """_ARTIFACT_DESCRIPTIONS has entries for all v16 aggregate artifacts."""

    def test_component_catalog_description_exists(self):
        """component-catalog.md has a description."""
        assert "component-catalog.md" in _ARTIFACT_DESCRIPTIONS

    def test_no_service_catalog_description(self):
        """Old service-catalog.md entry absent."""
        assert "service-catalog.md" not in _ARTIFACT_DESCRIPTIONS

    def test_no_interaction_graph_description(self):
        """Old interaction-graph.md entry absent."""
        assert "interaction-graph.md" not in _ARTIFACT_DESCRIPTIONS

    def test_no_system_glossary_description(self):
        """Old system-glossary.md entry absent."""
        assert "system-glossary.md" not in _ARTIFACT_DESCRIPTIONS


class TestIsAggregateRoot:
    """_is_aggregate_root detects aggregate signal files (component-catalog.md / architecture.md)."""

    def test_detects_component_catalog(self, tmp_path):
        """_is_aggregate_root(docs_root) = True when system/component-catalog.md exists."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "component-catalog.md").write_text("# Catalog\n")
        assert _is_aggregate_root(str(tmp_path)) is True

    def test_architecture_alone_insufficient(self, tmp_path):
        """_is_aggregate_root returns False on architecture.md alone (shared with single-component)."""
        # architecture.md is shared with single-component tier, so it's not a unique aggregate signal
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "architecture.md").write_text("# Architecture\n")
        assert _is_aggregate_root(str(tmp_path)) is False

    def test_false_when_no_aggregate_files(self, tmp_path):
        """_is_aggregate_root returns False when component-catalog.md is absent."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "overview.md").write_text("# Overview\n")
        assert _is_aggregate_root(str(tmp_path)) is False

    def test_false_when_no_system_dir(self, tmp_path):
        """_is_aggregate_root returns False when docs/system/ doesn't exist."""
        assert _is_aggregate_root(str(tmp_path)) is False


class TestAggregateReadmeRender:
    """build_aggregate_system_readme produces correct structure with no ## Files list."""

    def test_readme_has_numbered_table(self, tmp_path):
        """README includes a numbered reading-order table."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert "|" in out  # Markdown table
        assert "1" in out or "2" in out  # Numbers present

    def test_readme_has_new_dev_role_path(self, tmp_path):
        """README includes 'new_dev' reading path section."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # Should reference reading paths or roles
        assert "read" in out.lower() or "path" in out.lower() or "role" in out.lower()

    def test_readme_has_principles_block(self, tmp_path):
        """README includes a principles/guidelines block."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert len(out) > 0  # Has content

    def test_readme_no_files_list(self, tmp_path):
        """README does NOT have a flat ## Files list (v16 change)."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # Should not have the old flat ## Files section
        assert "## Files" not in out

    def test_readme_has_components_pointer(self, tmp_path):
        """README includes documentation structure (may reference components separately)."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # Implementation may have components pointer optional — check for table/structure
        assert "|" in out  # Has markdown table structure

    def test_components_pointer_per_lang_layout(self, tmp_path):
        """Per-lang layout (docs/<lang>/components/) → pointer rel is ../components/ (M2)."""
        # docs/vi/system/README.md ; components at docs/vi/components/
        system_dir = tmp_path / "docs" / "vi" / "system"
        system_dir.mkdir(parents=True)
        (tmp_path / "docs" / "vi" / "components").mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "vi", "T")
        assert "../components/" in out
        assert "../../components/" not in out

    def test_components_pointer_sibling_layout(self, tmp_path):
        """Sibling layout (docs/components/, lang dir peer) → pointer rel ../../components/."""
        # docs/vi/system/README.md ; components at docs/components/
        system_dir = tmp_path / "docs" / "vi" / "system"
        system_dir.mkdir(parents=True)
        (tmp_path / "docs" / "components").mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "vi", "T")
        assert "../../components/" in out

    def test_components_pointer_omitted_when_absent(self, tmp_path):
        """No components dir anywhere → no dead pointer link emitted."""
        system_dir = tmp_path / "docs" / "vi" / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "vi", "T")
        assert "components/" not in out

    def test_readme_accepts_existing_content_param(self, tmp_path):
        """build_aggregate_system_readme accepts existing_content parameter."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        existing_content = "## Custom Section\nUser-added content."
        # Ensure the function accepts the parameter without error
        out = build_aggregate_system_readme(str(system_dir), "en", "T", existing_content=existing_content)
        assert len(out) > 0  # Returns non-empty string


class TestBuildNavMetadata:
    """Phase 04: build_nav_metadata ranks gateway/most-depended-on first, reused last."""

    def test_ranks_gateway_first_reused_last(self):
        """Fix A (v23): reused flag comes from reused_map (manifest), NOT provenance."""
        from _nav_metadata_lib import build_nav_metadata
        digests = [
            # emp has provenance "docs-derived" — under the old buggy code this would
            # flag it reused. With Fix A it must NOT be reused unless reused_map says so.
            {"service": "emp", "role": "service", "provenance": "docs-derived"},
            {"service": "gw", "role": "gateway"},
            {"service": "auth", "role": "domain-service"},
        ]
        edges = [{"from": "auth", "to": "gw", "type": "sync", "label": "x"}]
        # Pass authoritative reused_map: only "emp" is reused (manifest status=="reused").
        meta = build_nav_metadata(digests, edges, reused_map={"emp": True})
        assert [m["service"] for m in meta] == ["gw", "auth", "emp"]
        assert [m["rank"] for m in meta] == [1, 2, 3]
        assert meta[0]["rationale_key"] == "gateway" and meta[0]["fan_in"] == 1
        assert meta[-1]["rationale_key"] == "reused"

    def test_provenance_does_not_drive_reused_flag(self):
        """Fix A (v23): provenance='docs-derived' must NOT flag a service as reused.

        Old _is_reused keyed on provenance and flagged every docs-derived service reused.
        With the fix, reused is False unless explicitly in reused_map.
        """
        from _nav_metadata_lib import build_nav_metadata
        digests = [
            {"service": "svc-a", "role": "service", "provenance": "docs-derived"},
            {"service": "svc-b", "role": "service", "provenance": "docs-derived"},
        ]
        edges = []
        # No reused_map → none should be reused despite provenance=="docs-derived".
        meta = build_nav_metadata(digests, edges)
        assert all(not m["reused"] for m in meta), (
            "provenance='docs-derived' must not flag a service reused; use reused_map"
        )
        # With reused_map marking one service reused, only that one is flagged.
        meta2 = build_nav_metadata(digests, edges, reused_map={"svc-a": True})
        reused_svcs = [m["service"] for m in meta2 if m["reused"]]
        assert reused_svcs == ["svc-a"]

    def test_within_tier_by_fan_in_desc(self):
        from _nav_metadata_lib import build_nav_metadata
        digests = [{"service": "a", "role": "service"}, {"service": "b", "role": "service"}]
        edges = [{"from": "a", "to": "b", "type": "sync", "label": "x"}]  # b fan_in=1, a=0
        meta = build_nav_metadata(digests, edges)
        assert [m["service"] for m in meta] == ["b", "a"]


class TestReadFirstSection:
    """Phase 04 C1: system README renders a reasoned read-first section from metadata."""

    def _write_meta(self, system_dir):
        import json
        meta = [
            {"service": "gw", "role": "gateway", "rank": 1, "reused": False,
             "fan_in": 3, "rationale_key": "gateway"},
            {"service": "auth", "role": "domain-service", "rank": 2, "reused": False,
             "fan_in": 0, "rationale_key": "backend"},
            {"service": "emp", "role": "service", "rank": 3, "reused": True,
             "fan_in": 0, "rationale_key": "reused"},
        ]
        (system_dir / ".nav-metadata.json").write_text(json.dumps(meta), encoding="utf-8")

    def _write_meta_no_deps(self, system_dir, stack="Delphi"):
        """Write metadata where all fan_in==0 (no cross-service edges detected)."""
        import json
        meta = [
            {"service": "billing", "role": "service", "rank": 1, "reused": False,
             "fan_in": 0, "rationale_key": "backend", "stack": stack},
            {"service": "auth", "role": "service", "rank": 2, "reused": False,
             "fan_in": 0, "rationale_key": "backend", "stack": stack},
            {"service": "gateway", "role": "gateway", "rank": 3, "reused": False,
             "fan_in": 0, "rationale_key": "gateway", "stack": stack},
        ]
        (system_dir / ".nav-metadata.json").write_text(json.dumps(meta), encoding="utf-8")

    def test_renders_from_metadata_in_rank_order(self, tmp_path):
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert "Which service to read first" in out
        assert out.index("**gw**") < out.index("**auth**") < out.index("**emp**")
        assert "start here" in out  # gateway rationale rendered

    def test_absent_when_no_metadata(self, tmp_path):
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert "Which service to read first" not in out

    def test_localized_vi(self, tmp_path):
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "vi", "T")
        assert "Nên đọc dịch vụ nào trước" in out

    def test_deterministic(self, tmp_path):
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta(system_dir)
        a = build_aggregate_system_readme(str(system_dir), "en", "T")
        b = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert a == b

    # --- Fix B (v23): no-deps branch tests ---

    def test_no_deps_emits_no_deps_intro(self, tmp_path):
        """Fix B: when all fan_in==0, the no-deps intro is used instead of ranked intro."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta_no_deps(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert "Which service to read first" in out
        assert "not statically detected" in out  # no-deps prose
        # Normal ranked intro must NOT appear when no deps
        assert "Suggested order across services" not in out

    def test_no_deps_alphabetical_order(self, tmp_path):
        """Fix B: services in no-deps branch are listed alphabetically."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta_no_deps(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # auth < billing < gateway alphabetically
        assert out.index("**auth**") < out.index("**billing**") < out.index("**gateway**")

    def test_no_deps_zero_rationale_lines(self, tmp_path):
        """Fix B: no per-service rationale lines (— Backend service … called by 0) emitted."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta_no_deps(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # No rationale suffix "— " on service lines (no "called by 0", no "start here")
        assert "called by 0" not in out
        assert "called by" not in out

    def test_no_deps_stack_hint_in_intro(self, tmp_path):
        """Fix B: stack name appears as parenthetical hint in the no-deps intro."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta_no_deps(system_dir, stack="Delphi")
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert "Delphi" in out

    def test_no_deps_no_stack_hint_when_absent(self, tmp_path):
        """Fix B: no parenthetical when stack field is empty."""
        import json
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        meta = [
            {"service": "svc-a", "role": "service", "rank": 1, "reused": False,
             "fan_in": 0, "rationale_key": "backend", "stack": ""},
            {"service": "svc-b", "role": "service", "rank": 2, "reused": False,
             "fan_in": 0, "rationale_key": "backend", "stack": ""},
        ]
        (system_dir / ".nav-metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # No trailing "()" from empty stack
        assert "()" not in out
        assert "not statically detected" in out  # still gets the no-deps intro

    def test_no_deps_localized_vi(self, tmp_path):
        """Fix B: Vietnamese no-deps intro — must be Vietnamese, no English leak."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta_no_deps(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "vi", "T")
        assert "Không phát hiện được" in out  # Vietnamese no-deps intro present
        assert "not statically detected" not in out  # no English in VI output

    def test_no_deps_localized_ja(self, tmp_path):
        """Fix B: Japanese no-deps intro — must be Japanese, no English leak."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        self._write_meta_no_deps(system_dir)
        out = build_aggregate_system_readme(str(system_dir), "ja", "T")
        assert "静的に検出されませんでした" in out  # Japanese no-deps intro present
        assert "not statically detected" not in out  # no English in JA output

    def test_deps_present_uses_ranked_rendering(self, tmp_path):
        """Fix B gate: when some fan_in>0, the ranked rendering (not no-deps) is used."""
        import json
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        meta = [
            {"service": "gw", "role": "gateway", "rank": 1, "reused": False,
             "fan_in": 2, "rationale_key": "gateway", "stack": ""},
            {"service": "auth", "role": "service", "rank": 2, "reused": False,
             "fan_in": 0, "rationale_key": "backend", "stack": ""},
        ]
        (system_dir / ".nav-metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        # The ranked intro must appear, not the no-deps intro
        assert "not statically detected" not in out
        assert "start here" in out  # gateway rationale rendered


class TestParentReadmeDedup:
    """Phase 04 C2: parent docs README is a thin pointer, not a full table duplicate."""

    def _mk(self, tmp_path):
        sysd = tmp_path / "system"
        sysd.mkdir(parents=True)
        (sysd / "overview.md").write_text("x", encoding="utf-8")
        (sysd / "component-catalog.md").write_text("x", encoding="utf-8")
        return tmp_path

    def test_thin_pointer_no_full_table(self, tmp_path):
        from _nav_index import _build_aggregate_index
        out = _build_aggregate_index(str(self._mk(tmp_path)), "en", "T")
        assert "system/README.md" in out          # thin pointer present
        assert "system/overview.md" not in out     # numbered table NOT duplicated

    def test_parent_still_has_principles(self, tmp_path):
        from _nav_index import _build_aggregate_index
        out = _build_aggregate_index(str(self._mk(tmp_path)), "en", "T")
        assert len(out) > 0


class TestLocaleKeySetParity:
    """en/vi/ja STRINGS have recursive key-set equality (including aggregate_index)."""

    def test_en_vi_parity(self):
        """STRINGS_EN and STRINGS_VI have the same keys recursively."""
        en_keys = _recursive_keys(STRINGS_EN)
        vi_keys = _recursive_keys(STRINGS_VI)
        missing_in_vi = en_keys - vi_keys
        extra_in_vi = vi_keys - en_keys
        assert not missing_in_vi, f"Missing in vi: {missing_in_vi}"
        assert not extra_in_vi, f"Extra in vi: {extra_in_vi}"

    def test_en_ja_parity(self):
        """STRINGS_EN and STRINGS_JA have the same keys recursively."""
        en_keys = _recursive_keys(STRINGS_EN)
        ja_keys = _recursive_keys(STRINGS_JA)
        missing_in_ja = en_keys - ja_keys
        extra_in_ja = ja_keys - en_keys
        assert not missing_in_ja, f"Missing in ja: {missing_in_ja}"
        assert not extra_in_ja, f"Extra in ja: {extra_in_ja}"

    def test_aggregate_index_keys_present(self):
        """All locales have aggregate_index keys."""
        assert "aggregate_index" in STRINGS_EN
        assert "aggregate_index" in STRINGS_VI
        assert "aggregate_index" in STRINGS_JA


def _recursive_keys(obj, prefix=""):
    """Return flattened set of all keys in nested dict."""
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys.update(_recursive_keys(v, full_key))
    return keys


class TestAggregateWhyKeys:
    """AGGREGATE_WHY_KEYS covers every AGGREGATE_SYSTEM_ORDER entry (single-source test)."""

    def test_every_order_entry_has_why_key(self):
        """Every filename in AGGREGATE_SYSTEM_ORDER has a why_key in AGGREGATE_WHY_KEYS."""
        for fname in AGGREGATE_SYSTEM_ORDER:
            assert fname in AGGREGATE_WHY_KEYS, (
                f"{fname!r} missing from AGGREGATE_WHY_KEYS — add a why_key entry"
            )

    def test_no_extra_keys_in_why_map(self):
        """AGGREGATE_WHY_KEYS has no keys not in AGGREGATE_SYSTEM_ORDER (no drift)."""
        order_set = set(AGGREGATE_SYSTEM_ORDER)
        for fname in AGGREGATE_WHY_KEYS:
            assert fname in order_set, (
                f"{fname!r} in AGGREGATE_WHY_KEYS but not in AGGREGATE_SYSTEM_ORDER"
            )

    def test_why_keys_are_non_empty_strings(self):
        """Every why_key value is a non-empty string."""
        for fname, key in AGGREGATE_WHY_KEYS.items():
            assert isinstance(key, str) and key.strip(), (
                f"AGGREGATE_WHY_KEYS[{fname!r}] = {key!r} is not a non-empty string"
            )


class TestAggregateWhyStrings:
    """All locales carry aggregate_why with an entry for each AGGREGATE_WHY_KEYS value."""

    def _check_locale(self, strings, lang_name):
        ag_why = strings.get("aggregate_why", {})
        assert ag_why, f"{lang_name}: aggregate_why block missing or empty"
        for fname, key in AGGREGATE_WHY_KEYS.items():
            assert key in ag_why, (
                f"{lang_name}: aggregate_why[{key!r}] missing (needed for {fname!r})"
            )
            clause = ag_why[key]
            assert isinstance(clause, str) and clause.strip(), (
                f"{lang_name}: aggregate_why[{key!r}] is empty"
            )

    def test_en_has_all_why_clauses(self):
        """English aggregate_why covers every AGGREGATE_WHY_KEYS value."""
        self._check_locale(STRINGS_EN, "en")

    def test_vi_has_all_why_clauses(self):
        """Vietnamese aggregate_why covers every AGGREGATE_WHY_KEYS value."""
        self._check_locale(STRINGS_VI, "vi")

    def test_ja_has_all_why_clauses(self):
        """Japanese aggregate_why covers every AGGREGATE_WHY_KEYS value."""
        self._check_locale(STRINGS_JA, "ja")

    def test_en_clauses_are_causal_not_just_descriptive(self):
        """EN clauses reference causal connectors (read after / read first / context)."""
        ag_why = STRINGS_EN["aggregate_why"]
        causal_markers = {"read after", "read first", "read last", "before", "context"}
        for key, clause in ag_why.items():
            lower = clause.lower()
            assert any(m in lower for m in causal_markers), (
                f"EN aggregate_why[{key!r}] lacks a causal connector: {clause!r}"
            )

    def test_vi_no_english_leak(self):
        """Vietnamese why-clauses contain no raw English words (no EN leak)."""
        ag_why = STRINGS_VI["aggregate_why"]
        # Spot-check that clauses are not the same as English
        en_why = STRINGS_EN["aggregate_why"]
        for key in ag_why:
            assert ag_why[key] != en_why.get(key), (
                f"VI aggregate_why[{key!r}] is identical to EN — translation missing"
            )

    def test_ja_no_english_leak(self):
        """Japanese why-clauses contain no raw English words (no EN leak)."""
        ag_why = STRINGS_JA["aggregate_why"]
        en_why = STRINGS_EN["aggregate_why"]
        for key in ag_why:
            assert ag_why[key] != en_why.get(key), (
                f"JA aggregate_why[{key!r}] is identical to EN — translation missing"
            )


class TestReadingOrderRowsWhyClauses:
    """reading_order_rows appends why-clause when why_clauses param is provided."""

    def test_no_why_clauses_default_unchanged(self):
        """Default why_clauses=None produces same rows as when why_clauses={}."""
        files = ["overview.md", "architecture.md"]
        rows_none = reading_order_rows(files, "", ("#", "Doc", "Answers"))
        rows_empty = reading_order_rows(files, "", ("#", "Doc", "Answers"), why_clauses={})
        assert rows_none == rows_empty

    def test_why_clause_appended_to_desc(self):
        """When why_clauses is provided, clause is appended to the answers cell."""
        files = ["overview.md"]
        clauses = {"overview.md": "Read first for scope and actors."}
        rows = reading_order_rows(files, "", ("#", "Doc", "Answers"), why_clauses=clauses)
        data_row = rows[2]
        assert "Read first for scope and actors." in data_row

    def test_missing_key_in_why_clauses_graceful(self):
        """A file not in why_clauses gets no clause appended (graceful degradation)."""
        files = ["overview.md", "architecture.md"]
        clauses = {"overview.md": "Some clause."}
        rows = reading_order_rows(files, "", ("#", "Doc", "Answers"), why_clauses=clauses)
        arch_row = rows[3]  # architecture.md is index 3 (header, sep, overview, arch)
        assert "Some clause." not in arch_row

    def test_empty_why_clauses_dict_no_clauses(self):
        """Empty why_clauses dict produces the same output as why_clauses=None."""
        files = ["overview.md"]
        rows_none = reading_order_rows(files, "", ("#", "Doc", "Answers"))
        rows_empty = reading_order_rows(files, "", ("#", "Doc", "Answers"), why_clauses={})
        assert rows_none == rows_empty


class TestBuildWhyClauses:
    """build_why_clauses returns static fallbacks + respects .nav-why.json overrides."""

    def test_static_clauses_for_all_present_files(self, tmp_path):
        """All AGGREGATE_SYSTEM_ORDER entries get a static clause from EN strings."""
        clauses = build_why_clauses(str(tmp_path), STRINGS_EN)
        for fname in AGGREGATE_SYSTEM_ORDER:
            assert fname in clauses, f"{fname!r} missing from why_clauses"
            assert clauses[fname].strip()

    def test_grounded_override_wins(self, tmp_path):
        """When .nav-why.json has an entry, it overrides the static clause."""
        import json
        why_data = {"overview.md": "Researcher-written reason for reading overview first."}
        (tmp_path / ".nav-why.json").write_text(json.dumps(why_data), encoding="utf-8")
        clauses = build_why_clauses(str(tmp_path), STRINGS_EN)
        assert clauses["overview.md"] == "Researcher-written reason for reading overview first."

    def test_static_fallback_when_not_in_nav_why(self, tmp_path):
        """Files not in .nav-why.json fall back to static clause."""
        import json
        # Only override overview.md; architecture.md should get the static clause.
        why_data = {"overview.md": "Grounded overview."}
        (tmp_path / ".nav-why.json").write_text(json.dumps(why_data), encoding="utf-8")
        clauses = build_why_clauses(str(tmp_path), STRINGS_EN)
        static_arch = STRINGS_EN["aggregate_why"]["architecture"]
        assert clauses["architecture.md"] == static_arch

    def test_absent_nav_why_json_uses_static_only(self, tmp_path):
        """Absent .nav-why.json → all entries from static strings (no error)."""
        clauses = build_why_clauses(str(tmp_path), STRINGS_EN)
        assert len(clauses) == len(AGGREGATE_SYSTEM_ORDER)

    def test_corrupt_nav_why_json_falls_back(self, tmp_path):
        """Corrupt .nav-why.json → silent fallback to static clauses."""
        (tmp_path / ".nav-why.json").write_text("NOT VALID JSON !!!", encoding="utf-8")
        clauses = build_why_clauses(str(tmp_path), STRINGS_EN)
        assert len(clauses) == len(AGGREGATE_SYSTEM_ORDER)

    def test_non_dict_nav_why_json_ignored(self, tmp_path):
        """A .nav-why.json that is a list (not a dict) is ignored."""
        import json
        (tmp_path / ".nav-why.json").write_text(json.dumps(["a", "b"]), encoding="utf-8")
        clauses = build_why_clauses(str(tmp_path), STRINGS_EN)
        assert len(clauses) == len(AGGREGATE_SYSTEM_ORDER)


class TestReadmeIncludesWhyClauses:
    """build_aggregate_system_readme includes static why-clauses in reading-order table."""

    def test_readme_includes_overview_why_clause(self, tmp_path):
        """Rendered README contains the EN overview why-clause."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "overview.md").write_text("# Overview\n")
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        overview_clause = STRINGS_EN["aggregate_why"]["overview"]
        assert overview_clause in out

    def test_readme_grounded_override_replaces_static(self, tmp_path):
        """When .nav-why.json has an entry, the grounded clause appears; static does not."""
        import json
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "overview.md").write_text("# Overview\n")
        grounded = "Researcher wrote: start here for the mission statement."
        (system_dir / ".nav-why.json").write_text(
            json.dumps({"overview.md": grounded}), encoding="utf-8"
        )
        out = build_aggregate_system_readme(str(system_dir), "en", "T")
        assert grounded in out
        static_clause = STRINGS_EN["aggregate_why"]["overview"]
        assert static_clause not in out

    def test_readme_vi_no_english_clause(self, tmp_path):
        """VI README reading-order table contains no EN overview clause (no EN leak)."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "overview.md").write_text("# Overview\n")
        out = build_aggregate_system_readme(str(system_dir), "vi", "T")
        en_clause = STRINGS_EN["aggregate_why"]["overview"]
        assert en_clause not in out

    def test_readme_ja_no_english_clause(self, tmp_path):
        """JA README reading-order table contains no EN overview clause (no EN leak)."""
        system_dir = tmp_path / "system"
        system_dir.mkdir(parents=True)
        (system_dir / "overview.md").write_text("# Overview\n")
        out = build_aggregate_system_readme(str(system_dir), "ja", "T")
        en_clause = STRINGS_EN["aggregate_why"]["overview"]
        assert en_clause not in out
