# layout-exempt: rebuild-spec single-component reading-why tests
"""Tests for the single-component reading_why clauses (Phase A1).

reading_why carries a causal "why read this here" clause per READING_ORDER
layer-1-3 entry key. Keyed directly on the entry key (no parallel map). The
renderer appends it to the "what it answers" cell as " — <clause>", presence-
pruned identically to the artifact row it annotates. Layer-4 entries
(flows/features/screens) carry NO clause here (A2/A3 prose covers them).

Mirrors the aggregate_why parity tests (test_nav_aggregate_render.py:507-560).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_strings_en import STRINGS as STRINGS_EN  # noqa: E402
from _nav_strings_vi import STRINGS as STRINGS_VI  # noqa: E402
from _nav_strings_ja import STRINGS as STRINGS_JA  # noqa: E402
from _nav_strings import READING_ORDER  # noqa: E402
from _nav_index import build_index_readme  # noqa: E402

# The set of keys reading_why must cover: every layer-1-3 READING_ORDER entry key.
LAYER123_KEYS = {
    e["key"]
    for layer in READING_ORDER
    if layer["layer"] in (1, 2, 3)
    for e in layer["entries"]
}
# Layer-4 keys must NOT appear in reading_why (A2/A3 own them).
LAYER4_KEYS = {
    e["key"]
    for layer in READING_ORDER
    if layer["layer"] == 4
    for e in layer["entries"]
}

_LOCALES = {"en": STRINGS_EN, "vi": STRINGS_VI, "ja": STRINGS_JA}


class TestReadingWhyParity:
    """reading_why covers exactly the layer-1-3 keys, in every locale (skeleton identity)."""

    def test_every_layer123_key_present(self):
        """Each layer-1-3 READING_ORDER key has a reading_why entry in every locale."""
        for lang, strings in _LOCALES.items():
            rw = strings.get("reading_why", {})
            assert rw, f"{lang}: reading_why block missing or empty"
            for key in LAYER123_KEYS:
                assert key in rw, f"{lang}: reading_why[{key!r}] missing"

    def test_no_extra_keys(self):
        """reading_why carries no keys beyond the layer-1-3 set (no drift, no layer-4 leak)."""
        for lang, strings in _LOCALES.items():
            rw = strings.get("reading_why", {})
            for key in rw:
                assert key in LAYER123_KEYS, (
                    f"{lang}: reading_why[{key!r}] is not a layer-1-3 key"
                )

    def test_no_layer4_keys(self):
        """Layer-4 keys (flows/features/screens) never appear in reading_why."""
        for lang, strings in _LOCALES.items():
            rw = strings.get("reading_why", {})
            for key in LAYER4_KEYS:
                assert key not in rw, (
                    f"{lang}: reading_why[{key!r}] is a layer-4 key — must be absent"
                )

    def test_all_values_non_empty_str(self):
        """Every reading_why value is a non-empty string."""
        for lang, strings in _LOCALES.items():
            for key, clause in strings.get("reading_why", {}).items():
                assert isinstance(clause, str) and clause.strip(), (
                    f"{lang}: reading_why[{key!r}] is not a non-empty string"
                )

    def test_all_locales_same_key_set(self):
        """All three locales carry the identical reading_why key set (skeleton identity)."""
        key_sets = {lang: set(s.get("reading_why", {})) for lang, s in _LOCALES.items()}
        assert key_sets["en"] == key_sets["vi"] == key_sets["ja"], (
            f"reading_why key set drift across locales: {key_sets}"
        )

    def test_en_clauses_are_causal(self):
        """EN clauses reference causal connectors (read after / read first / before)."""
        causal_markers = {"read after", "read first", "read last", "before"}
        for key, clause in STRINGS_EN["reading_why"].items():
            lower = clause.lower()
            assert any(m in lower for m in causal_markers), (
                f"EN reading_why[{key!r}] lacks a causal connector: {clause!r}"
            )


class TestReadingWhyRender:
    """The single-component index appends each present layer-1-3 clause; prunes absent."""

    def _make_full_tree(self, base: Path) -> Path:
        """A docs tree carrying every layer-1-3 artifact + a layer-4 feature."""
        docs = base / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "generated").mkdir(parents=True)
        for rel in (
            "system/overview.md", "system/architecture.md", "system/glossary.md",
            "system/business-rules.md",
            "generated/entities.md", "generated/feature-list.md",
            "generated/user-stories.md", "generated/screen-list.md",
            "generated/screen-flow.md", "generated/route-list.md",
            "generated/api-map.md", "generated/api-contracts.md",
            "generated/behavior-logic.md", "generated/permissions-matrix.md",
        ):
            (docs / rel).write_text(f"# {rel}\n")
        return docs

    def test_present_artifact_carries_its_clause(self, tmp_path):
        """A known layer-1-3 clause substring appears in the rendered index."""
        docs = self._make_full_tree(tmp_path)
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        # overview clause + a deeper clause must both be rendered.
        assert "establishes the product's purpose" in out
        assert "which role may perform each action" in out
        # The clause is appended to the answer cell with " — ".
        assert "— Read after" in out or "— Read first" in out

    def test_absent_artifact_clause_pruned(self, tmp_path):
        """When an artifact is absent, its row AND its clause are pruned."""
        docs = self._make_full_tree(tmp_path)
        (docs / "generated" / "permissions-matrix.md").unlink()
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "which role may perform each action" not in out
        # A still-present clause remains.
        assert "establishes the product's purpose" in out


class TestFeatureTraversalParity:
    """feature_traversal is a non-empty, equal-length list across all 3 locales (A2)."""

    def test_present_and_is_list(self):
        for lang, strings in _LOCALES.items():
            ft = strings.get("feature_traversal")
            assert isinstance(ft, list) and ft, f"{lang}: feature_traversal missing/empty/not-list"

    def test_all_lines_non_empty_str(self):
        for lang, strings in _LOCALES.items():
            for i, ln in enumerate(strings["feature_traversal"]):
                assert isinstance(ln, str) and ln.strip(), f"{lang}: feature_traversal[{i}] empty"

    def test_equal_line_count_skeleton_identity(self):
        """Equal len() across locales — the skeleton parity guarantee."""
        counts = {lang: len(s["feature_traversal"]) for lang, s in _LOCALES.items()}
        assert counts["en"] == counts["vi"] == counts["ja"], f"line-count drift: {counts}"

    def test_old_feature_reading_note_dropped(self):
        """feature_reading_note was superseded by feature_traversal — must be gone."""
        for lang, strings in _LOCALES.items():
            assert "feature_reading_note" not in strings, (
                f"{lang}: stale feature_reading_note key still present"
            )

    def test_en_describes_scr_jump(self):
        """EN traversal block documents the screen-name → SCR### lookup + screen-flow."""
        joined = " ".join(STRINGS_EN["feature_traversal"])
        assert "SCR###" in joined
        assert "screen-flow.md" in joined


class TestFeatureTraversalRender:
    """The traversal block renders only when a features/*/ entry is present."""

    def test_block_rendered_when_feature_present(self, tmp_path):
        docs = tmp_path / "docs"
        feat = docs / "features" / "F001_Login"
        feat.mkdir(parents=True)
        (feat / "spec.md").write_text("# F001\n")
        (docs / "system").mkdir()
        (docs / "system" / "overview.md").write_text("# o\n")
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "How to read a feature" in out
        assert "SCR###" in out

    def test_block_absent_when_no_features(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# o\n")
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "How to read a feature" not in out


class TestRelationshipMapParity:
    """relationship_map + heading present in all 3 locales, equal length (A3)."""

    def test_present_and_is_list(self):
        for lang, strings in _LOCALES.items():
            rm = strings.get("relationship_map")
            assert isinstance(rm, list) and rm, f"{lang}: relationship_map missing/empty"
            assert strings.get("relationship_map_heading"), f"{lang}: heading missing"

    def test_all_lines_non_empty_str(self):
        for lang, strings in _LOCALES.items():
            for i, ln in enumerate(strings["relationship_map"]):
                assert isinstance(ln, str) and ln.strip(), f"{lang}: relationship_map[{i}] empty"

    def test_equal_line_count(self):
        counts = {lang: len(s["relationship_map"]) for lang, s in _LOCALES.items()}
        assert counts["en"] == counts["vi"] == counts["ja"], f"line-count drift: {counts}"

    def test_en_names_all_id_systems(self):
        joined = " ".join(STRINGS_EN["relationship_map"])
        for tok in ("F###", "SCR###", "US###", "route", "screen-flow.md"):
            assert tok in joined, f"relationship_map omits {tok!r}"


class TestRelationshipMapRender:
    """The legend renders only when feature-list or screen-list is present."""

    def test_rendered_when_inventory_present(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "generated" / "feature-list.md").write_text("# f\n")
        (docs / "generated" / "screen-list.md").write_text("# s\n")
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "How the ID systems relate" in out

    def test_absent_when_no_inventory(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# o\n")
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "How the ID systems relate" not in out


class TestRoleNotesParity:
    """role_notes present in all 3 locales with the same key set (A6)."""

    def test_present_with_new_dev(self):
        for lang, strings in _LOCALES.items():
            rn = strings.get("role_notes", {})
            assert "new_dev" in rn and rn["new_dev"].strip(), f"{lang}: role_notes[new_dev] missing"

    def test_same_key_set(self):
        sets = {lang: set(s.get("role_notes", {})) for lang, s in _LOCALES.items()}
        assert sets["en"] == sets["vi"] == sets["ja"], f"role_notes key drift: {sets}"


class TestRoleNoteRender:
    """The new_dev role note renders only when the features entry (16) is present."""

    def test_note_rendered_with_features(self, tmp_path):
        docs = tmp_path / "docs"
        # new_dev path = [1,2,4,5,7,16]; need overview(1) + a present feature(16).
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# o\n")
        feat = docs / "features" / "F001_Login"
        feat.mkdir(parents=True)
        (feat / "spec.md").write_text("# f\n")
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "pick one feature and read it end-to-end" in out

    def test_note_pruned_without_features(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# o\n")  # no features/ → 16 pruned
        out = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert "pick one feature and read it end-to-end" not in out
