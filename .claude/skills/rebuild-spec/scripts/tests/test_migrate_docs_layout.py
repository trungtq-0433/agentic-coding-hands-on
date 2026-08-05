# layout-exempt: migration tests — all docs/components paths here are this skill's own managed targets
"""Tests for migrate_docs_layout.py — the single-lang → per-lang docs flip."""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import migrate_docs_layout as M  # noqa: E402


def _make_root_repo(tmp_path: Path, *, with_jp=False, state_translations=None) -> Path:
    """Create an en-primary repo at docs/ root (pre-flip shape)."""
    docs = tmp_path / "docs"
    # Create all language layers from LANGUAGE_LAYERS (now includes 'components' as of Phase 02)
    for layer in M.LANGUAGE_LAYERS:
        d = docs / layer
        d.mkdir(parents=True)
        (d / "x.md").write_text(f"# {layer}\n", encoding="utf-8")
    # Container-level files that must NOT move
    (docs / "decisions").mkdir()
    (docs / "decisions" / "adr-1.md").write_text("# ADR\n", encoding="utf-8")
    (docs / "_source-to-fcode.json").write_text('{"index":{}}', encoding="utf-8")
    state = {"primary_lang": "en", "translations": state_translations or {}}
    (docs / ".rebuild-state.json").write_text(json.dumps(state), encoding="utf-8")
    if with_jp:
        jp = docs / "jp"
        (jp / "system").mkdir(parents=True)
        (jp / "system" / "x.md").write_text("# jp\n", encoding="utf-8")
    return docs


def _run(argv):
    return M.main(argv)


class TestFlip:
    def test_clean_flip_moves_layers(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        assert _run(["--docs-base", str(docs)]) == 0
        # v20: MOVED_LAYERS (system, generated, flows, features, screens) move
        for layer in M.MOVED_LAYERS:
            assert (docs / "en" / layer / "x.md").is_file()
            assert not (docs / layer).exists()
        # v20: components stays at the root (SOURCE of truth — not moved)
        assert (docs / "components" / "x.md").is_file()
        assert not (docs / "en" / "components").exists()
        assert (docs / "en" / M.LAYOUT_SENTINEL).is_file()

    def test_container_files_not_moved(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        _run(["--docs-base", str(docs)])
        assert (docs / "decisions" / "adr-1.md").is_file()
        assert (docs / ".rebuild-state.json").is_file()
        assert not (docs / "en" / "decisions").exists()
        assert not (docs / "en" / ".rebuild-state.json").exists()

    def test_reverse_index_invalidated(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        _run(["--docs-base", str(docs)])
        assert not (docs / "_source-to-fcode.json").exists()

    def test_idempotent_second_run_noop(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        assert _run(["--docs-base", str(docs)]) == 0
        # second run: sentinel present → no-op, tree unchanged
        assert _run(["--docs-base", str(docs)]) == 0
        assert (docs / "en" / "system" / "x.md").is_file()

    def test_non_en_primary_is_noop(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        assert _run(["--docs-base", str(docs), "--primary", "vi"]) == 0
        # nothing moved — still at root, no docs/vi created
        assert (docs / "system" / "x.md").is_file()
        assert not (docs / "vi").exists()

    def test_resume_after_partial_move(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        # Simulate a crashed flip: 'system' already moved, sentinel absent
        (docs / "en").mkdir()
        (docs / "en" / "system").mkdir()
        (docs / "system" / "x.md").rename(docs / "en" / "system" / "x.md")
        (docs / "system").rmdir()
        assert not (docs / "en" / M.LAYOUT_SENTINEL).exists()
        # Re-run resumes the rest (MOVED_LAYERS only — not components)
        assert _run(["--docs-base", str(docs)]) == 0
        for layer in M.MOVED_LAYERS:
            assert (docs / "en" / layer / "x.md").is_file()
        # v20: components stays at root
        assert (docs / "components" / "x.md").is_file()
        assert (docs / "en" / M.LAYOUT_SENTINEL).is_file()


class TestAliasRename:
    def test_jp_to_ja_during_flip(self, tmp_path):
        docs = _make_root_repo(tmp_path, with_jp=True,
                               state_translations={"jp": {"passes_translated": ["core"]}})
        assert _run(["--docs-base", str(docs)]) == 0
        assert (docs / "ja" / "system" / "x.md").is_file()
        assert not (docs / "jp").exists()
        state = json.loads((docs / ".rebuild-state.json").read_text())
        assert "ja" in state["translations"]
        assert "jp" not in state["translations"]

    def test_standalone_rename(self, tmp_path):
        docs = _make_root_repo(tmp_path, with_jp=True,
                               state_translations={"jp": {"passes_translated": ["core"]}})
        assert _run(["--docs-base", str(docs), "--rename-alias", "jp:ja"]) == 0
        assert (docs / "ja").is_dir()
        assert not (docs / "jp").exists()

    def test_standalone_rename_invalidates_reverse_index(self, tmp_path):
        # [M2] standalone rename must also bust the reverse-index, like the flip path.
        docs = _make_root_repo(tmp_path, with_jp=True)
        assert (docs / "_source-to-fcode.json").is_file()
        assert _run(["--docs-base", str(docs), "--rename-alias", "jp:ja"]) == 0
        assert not (docs / "_source-to-fcode.json").exists()

    def test_rename_alias_rejects_traversal(self, tmp_path):
        # [H2] an unsafe alias arm must be rejected, not resolved outside docs/.
        docs = _make_root_repo(tmp_path)
        outside = tmp_path / "evil"
        outside.mkdir()
        (outside / "x").write_text("secret\n", encoding="utf-8")
        rc = _run(["--docs-base", str(docs), "--rename-alias", "../evil:ja"])
        assert rc == 2
        assert outside.is_dir()  # untouched — not renamed into docs/

    def test_both_exist_aborts_without_force(self, tmp_path):
        docs = _make_root_repo(tmp_path, with_jp=True)
        (docs / "ja" / "system").mkdir(parents=True)
        (docs / "ja" / "system" / "y.md").write_text("# ja\n", encoding="utf-8")
        # flip should abort on coexistence
        assert _run(["--docs-base", str(docs)]) == 1
        # both dirs still present (no clobber)
        assert (docs / "jp").is_dir()
        assert (docs / "ja").is_dir()

    def test_both_exist_force_merges(self, tmp_path):
        docs = _make_root_repo(tmp_path, with_jp=True)
        (docs / "ja" / "system").mkdir(parents=True)
        (docs / "ja" / "system" / "y.md").write_text("# ja\n", encoding="utf-8")
        assert _run(["--docs-base", str(docs), "--rename-alias", "jp:ja",
                     "--force-rename-alias"]) == 0
        assert (docs / "ja" / "system" / "x.md").is_file()  # merged in
        assert (docs / "ja" / "system" / "y.md").is_file()  # preserved
        assert not (docs / "jp").exists()


class TestRollback:
    def test_rollback_restores_root(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        # partial flip without sentinel
        (docs / "en").mkdir()
        for layer in M.LANGUAGE_LAYERS:
            (docs / layer).rename(docs / "en" / layer)
        assert not (docs / "en" / M.LAYOUT_SENTINEL).exists()
        assert _run(["--docs-base", str(docs), "--rollback"]) == 0
        for layer in M.LANGUAGE_LAYERS:
            assert (docs / layer / "x.md").is_file()
        assert not (docs / "en").exists()

    def test_rollback_refuses_completed_flip(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        _run(["--docs-base", str(docs)])  # full flip → sentinel written
        assert _run(["--docs-base", str(docs), "--rollback"]) == 1
        # tree untouched
        assert (docs / "en" / "system" / "x.md").is_file()


class TestConcurrencyLock:
    def test_parallel_flips_no_double_move(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        results = []

        def worker():
            results.append(_run(["--docs-base", str(docs)]))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert all(r == 0 for r in results)
        # exactly one complete tree, sentinel present, no leftover MOVED_LAYERS at root
        for layer in M.MOVED_LAYERS:
            assert (docs / "en" / layer / "x.md").is_file()
            assert not (docs / layer).exists()
        # v20: components stays at root (not moved by flip)
        assert (docs / "components" / "x.md").is_file()
        assert not (docs / "en" / "components").exists()
        assert (docs / "en" / M.LAYOUT_SENTINEL).is_file()


class TestRelocateToPrimary:
    """Direct unit tests for relocate_to_primary (non-en flat → docs/<primary>/)."""

    def test_relocates_flat_layers(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        rc, moved = M.relocate_to_primary(docs, "vi")
        assert rc == 0
        # v20: only MOVED_LAYERS are relocated (components stays at root)
        assert set(moved) == set(M.MOVED_LAYERS)
        assert (docs / "vi" / "system" / "x.md").is_file()
        assert not (docs / "system").exists()
        # v20: components stays at root (SOURCE of truth — not relocated)
        assert (docs / "components" / "x.md").is_file()
        assert not (docs / "vi" / "components").exists()
        assert (docs / "vi" / M.LAYOUT_SENTINEL).is_file()
        # Container-level files stay at the root (never moved).
        assert (docs / "decisions" / "adr-1.md").is_file()
        assert (docs / "_source-to-fcode.json").is_file()

    def test_idempotent_with_sentinel(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        M.relocate_to_primary(docs, "vi")
        # Second call sees the sentinel → no-op, no moved layers.
        rc, moved = M.relocate_to_primary(docs, "vi")
        assert rc == 0
        assert moved == []
        assert (docs / "vi" / "system" / "x.md").is_file()

    def test_partial_resume_skips_existing_dst(self, tmp_path, capsys):
        """A layer already at docs/<primary>/ is skipped (resume-safe), not clobbered."""
        docs = _make_root_repo(tmp_path)
        # Pre-place one layer at the target as if a prior run partially moved it.
        (docs / "vi" / "system").mkdir(parents=True)
        (docs / "vi" / "system" / "pre.md").write_text("pre", encoding="utf-8")
        rc, moved = M.relocate_to_primary(docs, "vi")
        assert rc == 0
        assert "system" not in moved          # skipped — already present at dst
        assert "generated" in moved
        assert (docs / "vi" / "system" / "pre.md").read_text() == "pre"

    def test_unsafe_primary_raises(self, tmp_path):
        docs = _make_root_repo(tmp_path)
        with __import__("pytest").raises(ValueError):
            M.relocate_to_primary(docs, "../evil")


class TestComponentsLayer:
    """v20: components is in LANGUAGE_LAYERS (alias) but NOT in MOVED_LAYERS.
    flip/relocate do NOT move components — it stays at docs/components/ (SOURCE of truth).
    """

    def test_components_in_language_layers(self):
        """LANGUAGE_LAYERS still includes components for backward-compat (rollback, etc.)."""
        assert "components" in M.LANGUAGE_LAYERS

    def test_components_not_in_moved_layers(self):
        """v20: MOVED_LAYERS does NOT include components — flip/relocate leave it at root."""
        assert "components" not in M.MOVED_LAYERS

    def test_flip_does_not_move_components(self, tmp_path):
        """Flip moves MOVED_LAYERS but leaves docs/components/ at root (v20)."""
        docs = _make_root_repo(tmp_path)
        (docs / "components" / "auth-service").mkdir(parents=True)
        (docs / "components" / "auth-service" / "spec.md").write_text("# auth\n", encoding="utf-8")

        assert _run(["--docs-base", str(docs)]) == 0
        # components stays at root (not moved by flip in v20)
        assert (docs / "components" / "auth-service" / "spec.md").is_file()
        assert not (docs / "en" / "components" / "auth-service").exists()

    def test_relocate_does_not_move_components(self, tmp_path):
        """relocate_to_primary does NOT move docs/components in v20."""
        docs = _make_root_repo(tmp_path)
        rc, moved = M.relocate_to_primary(docs, "vi")
        assert rc == 0
        assert "components" not in moved
        # components stays at root
        assert (docs / "components" / "x.md").is_file()
        assert not (docs / "vi" / "components").exists()

    def test_rollback_can_restore_v15_era_components(self, tmp_path):
        """Rollback can restore docs/<lang>/components → docs/components for v15-era partial flips."""
        docs = _make_root_repo(tmp_path)
        # Simulate a v15-era partial flip: all LANGUAGE_LAYERS (incl. components) were moved
        (docs / "en").mkdir(parents=True, exist_ok=True)
        for layer in M.LANGUAGE_LAYERS:
            if (docs / layer).exists():
                (docs / layer).rename(docs / "en" / layer)
        # Sentinel NOT present (partial flip — never completed)
        assert not (docs / "en" / M.LAYOUT_SENTINEL).exists()

        assert M.rollback(docs, "en") == 0
        # rollback iterates LANGUAGE_LAYERS so it restores components too
        assert (docs / "components" / "x.md").is_file()
        assert not (docs / "en").exists()


class TestPurgeDocumentMaps:
    """Test Phase 06: purge_document_maps (matrix row 8)."""

    def test_purge_document_maps_count(self, tmp_path):
        """purge_document_maps deletes both DOCUMENT-MAP filenames; returns count."""
        docs = _make_root_repo(tmp_path)
        # Add DOCUMENT-MAP files at various tiers
        (docs / "DOCUMENT-MAP.md").write_text("# map\n")
        (docs / "system" / "DOCUMENT-MAP.md").write_text("# system map\n")
        (docs / "generated" / "DOCUMENT-MAP.draft.md").write_text("# draft\n")

        count = M.purge_document_maps(str(docs))
        assert count == 3
        assert not (docs / "DOCUMENT-MAP.md").exists()
        assert not (docs / "system" / "DOCUMENT-MAP.md").exists()
        assert not (docs / "generated" / "DOCUMENT-MAP.draft.md").exists()

    def test_purge_document_maps_idempotent(self, tmp_path):
        """Second run of purge_document_maps returns 0 (already gone)."""
        docs = _make_root_repo(tmp_path)
        (docs / "DOCUMENT-MAP.md").write_text("# map\n")

        count1 = M.purge_document_maps(str(docs))
        assert count1 == 1
        count2 = M.purge_document_maps(str(docs))
        assert count2 == 0

    def test_purge_document_maps_no_glob_overkill(self, tmp_path):
        """purge_document_maps exact-match only; doesn't delete DOCUMENT-MAP-* variants."""
        docs = _make_root_repo(tmp_path)
        (docs / "DOCUMENT-MAP.md").write_text("# standard\n")
        (docs / "DOCUMENT-MAP-backup.md").write_text("# backup\n")
        (docs / "DOCUMENT-MAP.draft.md").write_text("# draft\n")

        count = M.purge_document_maps(str(docs))
        # Should delete .md and .draft.md, not -backup
        assert count == 2
        assert (docs / "DOCUMENT-MAP-backup.md").is_file()
        assert not (docs / "DOCUMENT-MAP.md").exists()
        assert not (docs / "DOCUMENT-MAP.draft.md").exists()


class TestConvergeComponentsToSource:
    """v20: _converge_components_to_source moves docs/<primary>/components BACK to docs/components.

    This is a one-time legacy cleanup for trees migrated under v15 that have
    docs/<primary>/components/ as their only copy. v20 requires docs/components/ as the
    lang-agnostic SOURCE of truth. _catchup_components is deprecated (now a no-op).
    """

    def test_converge_moves_legacy_to_source(self, tmp_path):
        """_converge_components_to_source moves docs/<lang>/components/ → docs/components/."""
        docs = tmp_path / "docs"
        # Simulate v15 tree: components was moved to docs/vi/components/ by a prior relocate
        (docs / "vi" / "components" / "auth-svc").mkdir(parents=True)
        (docs / "vi" / "components" / "auth-svc" / "spec.md").write_text("# auth\n")

        result = M._converge_components_to_source(docs, "vi")
        assert result is True
        assert (docs / "components" / "auth-svc" / "spec.md").is_file()
        assert not (docs / "vi" / "components").exists()

    def test_converge_noop_when_source_exists(self, tmp_path):
        """No-op when docs/components/ already present at root (canonical source position)."""
        docs = tmp_path / "docs"
        (docs / "components" / "auth").mkdir(parents=True)
        (docs / "components" / "auth" / "spec.md").write_text("# auth\n")
        # Also simulate the v15-style location
        (docs / "vi" / "components" / "payment").mkdir(parents=True)
        (docs / "vi" / "components" / "payment" / "spec.md").write_text("# payment\n")

        result = M._converge_components_to_source(docs, "vi")
        # No-op: source already canonical
        assert result is False
        # Original source untouched
        assert (docs / "components" / "auth" / "spec.md").is_file()

    def test_converge_noop_when_no_legacy(self, tmp_path):
        """No-op when docs/<primary>/components/ does not exist."""
        docs = tmp_path / "docs"
        docs.mkdir(parents=True, exist_ok=True)

        result = M._converge_components_to_source(docs, "vi")
        assert result is False

    def test_converge_idempotent(self, tmp_path):
        """Second call is a no-op (source already at docs/components/)."""
        docs = tmp_path / "docs"
        (docs / "vi" / "components" / "auth").mkdir(parents=True)
        (docs / "vi" / "components" / "auth" / "spec.md").write_text("# auth\n")

        M._converge_components_to_source(docs, "vi")
        # Second call: docs/components/ now exists → no-op
        result = M._converge_components_to_source(docs, "vi")
        assert result is False
        assert (docs / "components" / "auth" / "spec.md").is_file()

    def test_converge_archive_dirs_survive(self, tmp_path):
        """Archive dirs (.review-archive, .flows-archive) survive the converge move."""
        docs = tmp_path / "docs"
        comp_auth = docs / "vi" / "components" / "auth"
        comp_auth.mkdir(parents=True)
        (comp_auth / ".review-archive").mkdir()
        (comp_auth / ".review-archive" / "old.md").write_text("# old\n")
        (comp_auth / ".flows-archive").mkdir()
        (comp_auth / ".flows-archive" / "flow.md").write_text("# flow\n")

        M._converge_components_to_source(docs, "vi")
        final = docs / "components" / "auth"
        assert (final / ".review-archive" / "old.md").is_file()
        assert (final / ".flows-archive" / "flow.md").is_file()

    def test_catchup_components_deprecated_noop(self, tmp_path):
        """_catchup_components (v15) is a no-op in v20 — kept for import compatibility."""
        docs = tmp_path / "docs"
        (docs / "components" / "svc").mkdir(parents=True)
        (docs / "components" / "svc" / "spec.md").write_text("# svc\n")
        # _catchup_components used to move docs/components/ → docs/<lang>/components/
        # In v20, it is a no-op (returns False, moves nothing)
        result = M._catchup_components(docs, "en")
        assert result is False
        # Nothing moved
        assert (docs / "components" / "svc" / "spec.md").is_file()
        assert not (docs / "en" / "components").exists()


# ============================================================
# P07: migrate_components_to_lang (v23 root → lang direction)
# ============================================================

import sys as _sys  # noqa: E402
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _component_migrate_lib as CM  # noqa: E402
from _lang_lib import COMPONENTS_V23_SENTINEL  # noqa: E402


def _make_v22_non_en_repo(tmp_path: Path, primary: str = "vi",
                           identical: bool = True) -> Path:
    """Build an old v20/v22 layout: root docs/components/ + docs/<primary>/components/ both present.

    identical=True  → both trees are byte-identical (the common v22 case — derived view is a copy).
    identical=False → lang tree has an EXTRA file that differs from the root tree.
    """
    docs = tmp_path / "docs"
    # Root source (old location)
    (docs / "components" / "auth-svc" / "sub").mkdir(parents=True)
    (docs / "components" / "auth-svc" / "spec.md").write_text("# auth spec\n", encoding="utf-8")
    (docs / "components" / "auth-svc" / "sub" / "detail.md").write_text("detail\n", encoding="utf-8")
    # Lang-namespaced derived view (same content)
    (docs / primary / "components" / "auth-svc" / "sub").mkdir(parents=True)
    (docs / primary / "components" / "auth-svc" / "spec.md").write_text(
        "# auth spec\n", encoding="utf-8"
    )
    (docs / primary / "components" / "auth-svc" / "sub" / "detail.md").write_text(
        "detail\n", encoding="utf-8"
    )
    if not identical:
        # Introduce a divergence: extra file in lang tree only
        (docs / primary / "components" / "auth-svc" / "extra.md").write_text(
            "# extra (differs)\n", encoding="utf-8"
        )
    return docs


def _make_v22_only_root(tmp_path: Path, primary: str = "vi") -> Path:
    """v22 repo with root docs/components/ but NO docs/<primary>/components/ yet."""
    docs = tmp_path / "docs"
    (docs / "components" / "svc" / "sub").mkdir(parents=True)
    (docs / "components" / "svc" / "spec.md").write_text("# svc\n", encoding="utf-8")
    return docs


class TestMigrateComponentsToLang:
    """P07: v23 one-time migration root docs/components/ → docs/<primary>/components/."""

    # (a) non-en old-layout repo with byte-identical trees → lang tree wins, root pruned
    def test_non_en_identical_dup_pruned(self, tmp_path):
        docs = _make_v22_non_en_repo(tmp_path, primary="vi", identical=True)
        result = CM.migrate_components_to_lang(docs, "vi")
        assert result is True
        # Root source gone
        assert not (docs / "components").exists()
        # Lang tree preserved with all files
        assert (docs / "vi" / "components" / "auth-svc" / "spec.md").is_file()
        assert (docs / "vi" / "components" / "auth-svc" / "sub" / "detail.md").is_file()
        # Sentinel written
        assert (docs / "vi" / COMPONENTS_V23_SENTINEL).is_file()

    # (b) en repo → no-op (en source legitimately lives at docs/components/)
    def test_en_primary_noop(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "components" / "svc").mkdir(parents=True)
        (docs / "components" / "svc" / "spec.md").write_text("# svc\n", encoding="utf-8")
        result = CM.migrate_components_to_lang(docs, "en")
        assert result is False
        # Root components untouched
        assert (docs / "components" / "svc" / "spec.md").is_file()
        # No sentinel written for en
        assert not (docs / "en" / COMPONENTS_V23_SENTINEL).exists()

    # (c) idempotent second run
    def test_idempotent_second_run(self, tmp_path):
        docs = _make_v22_non_en_repo(tmp_path, primary="vi", identical=True)
        result1 = CM.migrate_components_to_lang(docs, "vi")
        assert result1 is True
        # Second run: sentinel present → no-op
        result2 = CM.migrate_components_to_lang(docs, "vi")
        assert result2 is False
        # Tree unchanged from first run
        assert not (docs / "components").exists()
        assert (docs / "vi" / "components" / "auth-svc" / "spec.md").is_file()

    # (d) atomic/crash-safety: only root dir present (no lang dir yet) → simple rename
    def test_only_root_present_simple_rename(self, tmp_path):
        """When only docs/components/ exists (no lang duplicate), a simple atomic rename."""
        docs = _make_v22_only_root(tmp_path, primary="vi")
        assert not (docs / "vi" / "components").exists()
        result = CM.migrate_components_to_lang(docs, "vi")
        assert result is True
        assert not (docs / "components").exists()
        assert (docs / "vi" / "components" / "svc" / "spec.md").is_file()
        assert (docs / "vi" / COMPONENTS_V23_SENTINEL).is_file()

    # (e) byte-identical trees converge cleanly (duplicate test emphasis: content preserved)
    def test_identical_trees_content_preserved(self, tmp_path):
        docs = _make_v22_non_en_repo(tmp_path, primary="ja", identical=True)
        CM.migrate_components_to_lang(docs, "ja")
        spec = (docs / "ja" / "components" / "auth-svc" / "spec.md").read_text(encoding="utf-8")
        detail = (docs / "ja" / "components" / "auth-svc" / "sub" / "detail.md").read_text(
            encoding="utf-8"
        )
        assert spec == "# auth spec\n"
        assert detail == "detail\n"

    # (f) differing trees → lang-tree wins + WARN, no data loss (root kept)
    def test_differing_trees_kept_and_warned(self, tmp_path, capsys):
        docs = _make_v22_non_en_repo(tmp_path, primary="vi", identical=False)
        result = CM.migrate_components_to_lang(docs, "vi")
        assert result is False
        # Both trees still present (no deletion)
        assert (docs / "components" / "auth-svc" / "spec.md").is_file()
        assert (docs / "vi" / "components" / "auth-svc" / "spec.md").is_file()
        # extra.md (the divergence) still present in lang tree
        assert (docs / "vi" / "components" / "auth-svc" / "extra.md").is_file()
        # No sentinel (migration was NOT completed)
        assert not (docs / "vi" / COMPONENTS_V23_SENTINEL).exists()
        # WARN was emitted
        captured = capsys.readouterr()
        assert "[WARN]" in captured.err
        assert "differing" in captured.err.lower() or "differ" in captured.err.lower()

    # (g) generated root README pruned, hand-written one kept
    def test_generated_root_readme_pruned(self, tmp_path, monkeypatch):
        """A generated-only root docs/README.md is deleted after migration."""
        docs = _make_v22_only_root(tmp_path, primary="vi")
        # Write a README that looks generated (contains GEN_END marker and no user tail)
        from _nav_lib import GEN_END
        generated_readme = f"<!-- generated nav zone -->\n{GEN_END}\n"
        (docs / "README.md").write_text(generated_readme, encoding="utf-8")
        CM.migrate_components_to_lang(docs, "vi")
        assert not (docs / "README.md").exists()

    def test_handwritten_root_readme_kept(self, tmp_path):
        """A hand-written root docs/README.md (no GEN markers) is never deleted."""
        docs = _make_v22_only_root(tmp_path, primary="vi")
        (docs / "README.md").write_text("# My project\nHuman wrote this.\n", encoding="utf-8")
        CM.migrate_components_to_lang(docs, "vi")
        assert (docs / "README.md").is_file()
        assert "Human wrote this" in (docs / "README.md").read_text(encoding="utf-8")

    # Lock/concurrent safety: two threads race — exactly one performs the migration
    def test_concurrent_runs_safe(self, tmp_path):
        """Concurrent calls under the lock produce exactly one successful migration."""
        import threading
        docs = _make_v22_non_en_repo(tmp_path, primary="vi", identical=True)
        results: list[bool] = []

        def worker():
            results.append(CM.migrate_components_to_lang(docs, "vi"))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Exactly one True (actual migration); the rest no-op (sentinel)
        assert sum(1 for r in results if r) == 1
        assert not (docs / "components").exists()
        assert (docs / "vi" / "components" / "auth-svc" / "spec.md").is_file()
        assert (docs / "vi" / COMPONENTS_V23_SENTINEL).is_file()

    # no-op when docs/components/ absent (clean v23 repo)
    def test_no_root_components_no_op(self, tmp_path):
        """No-op + sentinel written when docs/components/ does not exist at all."""
        docs = tmp_path / "docs"
        (docs / "vi" / "components" / "svc").mkdir(parents=True)
        (docs / "vi" / "components" / "svc" / "spec.md").write_text("# svc\n", encoding="utf-8")
        result = CM.migrate_components_to_lang(docs, "vi")
        assert result is False
        # Lang tree untouched
        assert (docs / "vi" / "components" / "svc" / "spec.md").is_file()
        # Sentinel still written (fast-path mark)
        assert (docs / "vi" / COMPONENTS_V23_SENTINEL).is_file()
