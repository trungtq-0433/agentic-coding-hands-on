"""Tests for build_navigation.py — Phase C navigation layer."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_lib import (  # noqa: E402
    GEN_END as _GEN_END,
    GEN_START as _GEN_START,
)
from _nav_index import build_index_readme as _build_index_readme  # noqa: E402
from _nav_strings import (  # noqa: E402
    READING_ORDER as _READING_ORDER,
    ROLES as _ROLES,
    get_strings as _get_strings,
)
from _layout_lib import LAYERED_PATH_MAP as _LAYERED_PATH_MAP  # noqa: E402
from _path_lib import _resolve_guarded  # noqa: E402
from build_navigation import _build_readme_content, run, _write_index_readme  # noqa: E402
from _nav_index import (  # noqa: E402
    is_bare_docs_root as _is_bare_docs_root,
    read_primary_lang_from_state as _read_primary_lang_from_state,
    resolve_root_readme_removal as _resolve_root_readme_removal,
)


# ---------------------------------------------------------------------------
# Index-README fixture + helpers
# ---------------------------------------------------------------------------

def _make_layered_docs_tree(base: Path, *, with_api_contracts: bool = True,
                            with_flows: bool = True) -> Path:
    """Create a realistic layered docs tree (system/ + generated/ + features/)."""
    docs = base / "docs"
    (docs / "system").mkdir(parents=True)
    (docs / "generated").mkdir(parents=True)
    for rel in (
        "system/overview.md", "system/architecture.md", "system/glossary.md",
        "system/business-rules.md",
        "generated/entities.md", "generated/feature-list.md",
        "generated/user-stories.md", "generated/screen-list.md",
        "generated/screen-flow.md", "generated/route-list.md",
        "generated/api-map.md", "generated/behavior-logic.md",
        "generated/permissions-matrix.md",
    ):
        (docs / rel).write_text(f"# {rel}\n")
    if with_api_contracts:
        (docs / "generated" / "api-contracts.md").write_text("# api-contracts\n")
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# spec\n")
    if with_flows:
        (docs / "flows").mkdir(parents=True)
        (docs / "flows" / "checkout.md").write_text("# checkout flow\n")
    return docs


def _index_rows(content: str):
    """Extract ordered (number, link_target) tuples from index table rows."""
    rows = []
    for line in content.splitlines():
        m = re.match(r"^\| (\d+) \| \[[^\]]+\]\(([^)]+)\) \|", line)
        if m:
            rows.append((int(m.group(1)), m.group(2)))
    return rows


# ---------------------------------------------------------------------------
# Top-level reading-order index README (v13.1.0)
# ---------------------------------------------------------------------------

class TestIndexReadme:
    def test_run_writes_root_readme(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        readme = docs / "README.md"
        assert readme.is_file()
        assert _get_strings("en")["title"] in readme.read_text()

    def test_four_layers_in_order(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        headings = re.findall(r"^## (\d)\.", (docs / "README.md").read_text(), re.M)
        assert headings == ["1", "2", "3", "4"]

    def test_layer1_internal_order(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        rows = _index_rows(content)
        # overview(1) < architecture(2) < glossary(3)
        assert [n for n, _ in rows[:3]] == [1, 2, 3]
        assert rows[0][1] == "system/overview.md"
        assert rows[1][1] == "system/architecture.md"
        assert rows[2][1] == "system/glossary.md"

    def test_link_targets_relative(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        targets = {t for _, t in _index_rows(content)}
        assert "generated/entities.md" in targets
        assert "features/" in targets  # glob entry links to dir

    def test_subdir_readmes_dont_reference_root_readme(self, tmp_path):
        """Subdir READMEs list their own files, never the root README."""
        docs = _make_layered_docs_tree(tmp_path)
        run(str(docs), pass_complete=False)
        # Subdir README should not reference parent README
        system_readme = docs / "system" / "README.md"
        if system_readme.exists():
            assert "../README.md" not in system_readme.read_text()


class TestIndexPruning:
    def test_absent_single_artifact_omitted_with_footnote(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path, with_api_contracts=False)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        targets = {t for _, t in _index_rows(content)}
        assert "generated/api-contracts.md" not in targets
        assert _get_strings("en")["footnote"] in content

    def test_all_present_no_footnote(self, tmp_path):
        # every conditional artifact present → no omission → no footnote
        docs = _make_layered_docs_tree(tmp_path, with_api_contracts=True, with_flows=True)
        (docs / "screens" / "SCR001_Home").mkdir(parents=True)
        (docs / "screens" / "SCR001_Home" / "spec.md").write_text("# s\n")
        (docs / "generated" / "job-list.md").write_text("# job-list\n")
        (docs / "system" / "design-intent.md").write_text("# design-intent\n")
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert _get_strings("en")["footnote"] not in content

    def test_glob_flows_absent_omits_row(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path, with_flows=False)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        targets = {t for _, t in _index_rows(content)}
        assert "flows/" not in targets

    def test_glob_flows_present_links_to_dir(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path, with_flows=True)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        rows = dict((t, n) for n, t in _index_rows(content))
        assert rows.get("flows/") == 15


class TestPerLangIndex:
    def test_vi_labels(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        run(str(docs), pass_complete=True, lang="vi")
        content = (docs / "README.md").read_text()
        assert _get_strings("vi")["title"] in content
        assert _get_strings("vi")["quick_path_label"] in content

    def test_skeleton_identity_en_vs_vi(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        en = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        vi = _build_index_readme(str(docs), "vi", "2026-01-01T00:00:00Z")
        # numbers + link targets byte-identical; only prose differs
        assert _index_rows(en) == _index_rows(vi)
        assert en != vi  # prose actually differs

    def test_principles_heading_localized(self, tmp_path):
        # prose headings (not just bullets) must render in the target language
        docs = _make_layered_docs_tree(tmp_path)
        en = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        vi = _build_index_readme(str(docs), "vi", "2026-01-01T00:00:00Z")
        assert f"### {_get_strings('en')['principles_label']}" in en
        assert f"### {_get_strings('vi')['principles_label']}" in vi
        assert "### Principles" not in vi  # no English leak in the vi doc

    def test_unknown_lang_falls_back_to_en(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        content = _build_index_readme(str(docs), "fr", "2026-01-01T00:00:00Z")
        assert _get_strings("en")["title"] in content

    def test_jp_alias_resolves_to_ja(self):
        assert _get_strings("jp") == _get_strings("ja")


class TestIndexRichContent:
    def test_roles_section_rendered(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert f"## {_get_strings('en')['roles_heading']}" in content
        # one bullet per role whose path has at least one present artifact
        for r in _ROLES:
            assert _get_strings("en")["role_labels"][r["key"]] in content

    def test_layer_intros_rendered(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        for n in (1, 2, 3, 4):
            assert _get_strings("en")["layer_intros"][n] in content

    def test_role_paths_language_independent(self, tmp_path):
        # the number sequences in role lines must be byte-identical across langs;
        # only the role label (prose) differs.
        docs = _make_layered_docs_tree(tmp_path)
        en = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        vi = _build_index_readme(str(docs), "vi", "2026-01-01T00:00:00Z")

        def seqs(text):
            return re.findall(r":\*\*\s*([\d →]+)$", text, re.M)
        assert seqs(en) == seqs(vi)
        assert seqs(en)  # non-empty

    def test_role_drops_absent_number(self, tmp_path):
        # reviewer path is [2, 13, 14, 11]; drop api-contracts (#11) → 11 gone
        docs = _make_layered_docs_tree(tmp_path, with_api_contracts=False)
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        reviewer = _get_strings("en")["role_labels"]["reviewer"]
        line = next(ln for ln in content.splitlines() if reviewer in ln)
        assert "11" not in line
        assert "13" in line and "14" in line

    def test_quick_path_label_localized(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        content = _build_index_readme(str(docs), "vi", "2026-01-01T00:00:00Z")
        assert _get_strings("vi")["quick_path_label"] in content
        # the numbers come from QUICK_PATH, not prose
        assert "1 → 2 → 4 → 5" in content

    def test_quick_path_prunes_absent(self, tmp_path):
        # QUICK_PATH is [1,2,4,5]; #4 = generated/entities.md — remove it → 4 dropped
        docs = _make_layered_docs_tree(tmp_path)
        (docs / "generated" / "entities.md").unlink()
        content = _build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        label = _get_strings("en")["quick_path_label"]
        qline = next(ln for ln in content.splitlines() if label in ln)
        assert "4" not in qline and "1 → 2 → 5" in qline


class TestIndexTwoZone:
    def test_user_tail_preserved(self, tmp_path):
        docs = _make_layered_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        readme = docs / "README.md"
        readme.write_text(readme.read_text() + "\n## My Notes\n\nKeep this!\n")
        run(str(docs), pass_complete=True)
        regenerated = readme.read_text()
        assert "Keep this!" in regenerated
        assert _GEN_START in regenerated
        assert _GEN_END in regenerated


class TestReadingOrderConsistency:
    def test_non_glob_paths_subset_of_layered_map(self):
        values = set(_LAYERED_PATH_MAP.values())
        for layer in _READING_ORDER:
            for entry in layer["entries"]:
                if "path" in entry:
                    assert entry["path"] in values, (
                        f"READING_ORDER path {entry['path']!r} drifted from "
                        f"LAYERED_PATH_MAP values"
                    )

    def test_numbers_are_contiguous_1_to_19(self):
        nums = [e["num"] for layer in _READING_ORDER for e in layer["entries"]]
        assert nums == list(range(1, 20))

    def test_artifact_keys_have_descriptions_all_langs(self):
        keys = {e["key"] for layer in _READING_ORDER for e in layer["entries"]}
        for lang in ("en", "vi", "ja"):
            descs = _get_strings(lang)["artifact_descriptions"]
            missing = keys - set(descs)
            assert not missing, f"{lang} missing descriptions for {missing}"

    def test_role_labels_parity_all_langs(self):
        # every ROLES key must have a label in each locale, else KeyError at render
        role_keys = {r["key"] for r in _ROLES}
        for lang in ("en", "vi", "ja"):
            labels = _get_strings(lang)["role_labels"]
            missing = role_keys - set(labels)
            assert not missing, f"{lang} missing role_labels for {missing}"

    def test_layer_intros_cover_all_layers_all_langs(self):
        layers = {layer["layer"] for layer in _READING_ORDER}
        for lang in ("en", "vi", "ja"):
            intros = _get_strings(lang)["layer_intros"]
            assert layers <= set(intros), f"{lang} missing layer_intros"


# ---------------------------------------------------------------------------
# _path_lib._resolve_guarded unit tests (RT-F14)
# ---------------------------------------------------------------------------

class TestResolveGuarded:
    def test_same_dir_ok(self, tmp_path):
        target = tmp_path / "sub" / "file.md"
        target.parent.mkdir()
        target.touch()
        result = _resolve_guarded(str(target), str(tmp_path))
        assert result == str(target.resolve())

    def test_base_itself_ok(self, tmp_path):
        result = _resolve_guarded(str(tmp_path), str(tmp_path))
        assert result == str(tmp_path.resolve())

    def test_path_escaping_base_raises(self, tmp_path):
        outside = tmp_path.parent / "other"
        with pytest.raises(ValueError, match="Path traversal"):
            _resolve_guarded(str(outside), str(tmp_path))

    def test_traversal_via_dotdot_raises(self, tmp_path):
        (tmp_path / "sub").mkdir()
        evil = str(tmp_path / "sub" / ".." / ".." / "etc" / "passwd")
        with pytest.raises(ValueError, match="Path traversal"):
            _resolve_guarded(evil, str(tmp_path))


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_docs_tree(base: Path) -> Path:
    """Create a minimal docs tree for navigation tests."""
    docs = base / "docs"
    # features subdir
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# F001\n\nSome spec content.\n")
    (feat / "screens.md").write_text("# Screens\n")
    # system subdir
    sys_dir = docs / "system"
    sys_dir.mkdir(parents=True)
    (sys_dir / "data-model.md").write_text("# Data Model\n")
    (sys_dir / "route-list.md").write_text("# Routes\n")
    # root-level artifact
    (docs / "feature-list.md").write_text("# Feature List\n")
    return docs


# ---------------------------------------------------------------------------
# README 2-zone tests (RT-F14)
# ---------------------------------------------------------------------------

class TestReadmeGeneration:
    def test_generated_block_present(self, tmp_path):
        docs = _make_docs_tree(tmp_path)
        subdir = docs / "system"
        content = _build_readme_content(subdir, str(docs), "2026-01-01T00:00:00Z")
        assert _GEN_START in content
        assert _GEN_END in content

    def test_files_listed(self, tmp_path):
        docs = _make_docs_tree(tmp_path)
        subdir = docs / "system"
        content = _build_readme_content(subdir, str(docs), "2026-01-01T00:00:00Z")
        assert "data-model.md" in content
        assert "route-list.md" in content

    def test_user_content_preserved_across_runs(self, tmp_path):
        docs = _make_docs_tree(tmp_path)
        subdir = docs / "system"
        readme = subdir / "README.md"

        # First run: no existing content
        content1 = _build_readme_content(subdir, str(docs), "2026-01-01T00:00:00Z")
        readme.write_text(content1)

        # User adds content below the end marker
        user_note = "\n## My Notes\n\nKeep this!\n"
        readme.write_text(content1 + user_note)

        # Second run: regenerate — user note must survive
        existing = readme.read_text()
        content2 = _build_readme_content(subdir, str(docs), "2026-06-01T00:00:00Z", existing)
        assert "Keep this!" in content2
        assert _GEN_START in content2
        assert _GEN_END in content2

    def test_empty_dir_handled_gracefully(self, tmp_path):
        docs = tmp_path / "docs"
        empty_dir = docs / "empty"
        empty_dir.mkdir(parents=True)
        content = _build_readme_content(empty_dir, str(docs), "2026-01-01T00:00:00Z")
        assert _GEN_START in content
        assert "no markdown files" in content


# ---------------------------------------------------------------------------
# run() integration tests (RT-F12 freshness + RT-F14 write-safety)
# ---------------------------------------------------------------------------

class TestRunIntegration:
    def test_no_document_map_written_when_complete(self, tmp_path):
        """Phase 04: build_navigation no longer writes DOCUMENT-MAP (removed)."""
        docs = _make_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        # Neither completed nor draft DOCUMENT-MAP should be written
        assert not (docs / "DOCUMENT-MAP.md").is_file()
        assert not (docs / "DOCUMENT-MAP.draft.md").is_file()

    def test_no_document_map_written_when_incomplete(self, tmp_path):
        """Phase 04: build_navigation no longer writes DOCUMENT-MAP (removed)."""
        docs = _make_docs_tree(tmp_path)
        run(str(docs), pass_complete=False)
        # Neither completed nor draft DOCUMENT-MAP should be written
        assert not (docs / "DOCUMENT-MAP.md").is_file()
        assert not (docs / "DOCUMENT-MAP.draft.md").is_file()

    def test_existing_document_map_purged(self, tmp_path):
        """run() actively purges stale DOCUMENT-MAP files (purge_document_maps sweep)."""
        docs = _make_docs_tree(tmp_path)
        real_map = docs / "DOCUMENT-MAP.md"
        real_map.write_text("# Existing map\n")
        run(str(docs), pass_complete=False)
        # Existing DOCUMENT-MAP.md must have been deleted by purge_document_maps.
        assert not real_map.exists()
        # And no draft should be written
        assert not (docs / "DOCUMENT-MAP.draft.md").is_file()

    def test_each_subdir_gets_readme(self, tmp_path):
        docs = _make_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        # system/ has direct .md files → README generated
        assert (docs / "system" / "README.md").is_file(), "Missing README for system"
        # A5: features/ has NO direct .md (only F### subdirs) → now gets a FEATURE INDEX
        # (previously suppressed; flipped in Phase A5). The index lists each F### subdir.
        feat_readme = docs / "features" / "README.md"
        assert feat_readme.is_file(), "features/ index README should be generated (A5)"
        assert "F001_Login" in feat_readme.read_text(), "features index must list F001_Login"

    def test_features_index_suppressed_when_no_feature_subdirs(self, tmp_path):
        """A5 scoped suppression: features/ with 0 F### subdirs AND 0 direct .md → no index."""
        docs = tmp_path / "docs"
        (docs / "features" / "notes").mkdir(parents=True)  # non-F### subdir, no .md
        (docs / "system").mkdir(parents=True)
        (docs / "system" / "overview.md").write_text("# o\n")
        run(str(docs), pass_complete=True)
        assert not (docs / "features" / "README.md").is_file(), (
            "features/ with no F### subdir must stay suppressed"
        )

    def test_pass_complete_flag_accepted_noop(self, tmp_path):
        """Phase 04: --pass-complete flag is accepted (vestigial, no-op)."""
        docs = _make_docs_tree(tmp_path)
        # Should exit 0 without error despite pass_complete=True
        result = run(str(docs), pass_complete=True)
        assert result == 0
        # But no DOCUMENT-MAP is written (removed in Phase 04)
        assert not (docs / "DOCUMENT-MAP.md").is_file()

    def test_pass_incomplete_no_document_map(self, tmp_path):
        """Phase 04: incomplete pass no longer writes draft DOCUMENT-MAP."""
        docs = _make_docs_tree(tmp_path)
        result = run(str(docs), pass_complete=False)
        assert result == 0
        # No DOCUMENT-MAP or DOCUMENT-MAP.draft written
        assert not (docs / "DOCUMENT-MAP.md").is_file()
        assert not (docs / "DOCUMENT-MAP.draft.md").is_file()

    def test_nonexistent_docs_root_exits_cleanly(self, tmp_path):
        # Should return 0 (advisory) not crash
        result = run(str(tmp_path / "nonexistent"), pass_complete=True)
        assert result == 0

    def test_nested_feature_dirs_generate_readme(self, tmp_path):
        docs = _make_docs_tree(tmp_path)
        # Add a direct .md file to features/ so it passes the non-empty guard
        (docs / "features" / "feature-index.md").write_text("# Feature Index\n")
        run(str(docs), pass_complete=True)
        # features/ now has a direct .md → README generated
        assert (docs / "features" / "README.md").is_file()

    def test_empty_subdir_readme_suppressed(self, tmp_path):
        """Subdirs with zero direct .md artifact files must not receive a README (P02)."""
        docs = tmp_path / "docs"
        empty_dir = docs / "empty"
        empty_dir.mkdir(parents=True)
        # populated dir alongside so run() has something to process
        populated = docs / "system"
        populated.mkdir(parents=True)
        (populated / "overview.md").write_text("# Overview\n")
        run(str(docs), pass_complete=False)
        assert not (empty_dir / "README.md").is_file(), (
            "Empty subdir must not receive a README"
        )
        assert (populated / "README.md").is_file(), (
            "Populated subdir must still receive a README"
        )

    def test_subdir_readme_includes_blurb(self, tmp_path):
        """Non-empty known subdirs must have a blurb line in their README (P02)."""
        docs = tmp_path / "docs"
        sys_dir = docs / "system"
        sys_dir.mkdir(parents=True)
        (sys_dir / "overview.md").write_text("# Overview\n")
        run(str(docs), pass_complete=False)
        content = (sys_dir / "README.md").read_text()
        # Blurb for "system" must appear
        from _nav_lib import subdir_blurb
        assert subdir_blurb("system") in content

    def test_unknown_subdir_has_no_blurb(self, tmp_path):
        """Unknown subdir names fall back to empty blurb — no crash, no blurb line."""
        from _nav_lib import subdir_blurb, GEN_START
        docs = tmp_path / "docs"
        custom_dir = docs / "custom-reports"
        custom_dir.mkdir(parents=True)
        (custom_dir / "report.md").write_text("# Report\n")
        from build_navigation import _build_readme_content
        content = _build_readme_content(custom_dir, str(docs), "2026-01-01T00:00:00Z")
        assert subdir_blurb("custom-reports") == ""
        # Title line still present, no blurb noise
        assert "# custom-reports" in content
        assert GEN_START in content


# ---------------------------------------------------------------------------
# Write-safety via run() — path outside docs_root must not be written
# ---------------------------------------------------------------------------

class TestWriteSafetyViaPathLib:
    def test_resolve_guarded_rejects_escape(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        outside = str(tmp_path / "outside.md")
        with pytest.raises(ValueError, match="Path traversal"):
            _resolve_guarded(outside, str(docs))

    def test_resolve_guarded_accepts_subpath(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        inside = docs / "sub" / "file.md"
        inside.parent.mkdir()
        inside.touch()
        result = _resolve_guarded(str(inside), str(docs))
        assert result.startswith(str(docs.resolve()))


# ---------------------------------------------------------------------------
# Directive 3 — per-lang root README pointer (v15.0.0)
# ---------------------------------------------------------------------------
class TestRootPointer:
    def test_is_bare_docs_root(self, tmp_path):
        assert _is_bare_docs_root("/abs/docs", "vi") is True
        assert _is_bare_docs_root("/abs/docs/vi", "vi") is False
        assert _is_bare_docs_root("/abs/docs/en", "en") is False

    def test_read_primary_lang_from_state(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / ".rebuild-state.json").write_text('{"primary_lang": "vi"}', encoding="utf-8")
        assert _read_primary_lang_from_state(str(docs)) == "vi"

    def test_read_primary_lang_fallback_en(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        assert _read_primary_lang_from_state(str(docs)) == "en"  # no state file

    def test_removal_generated_only_deletes(self):
        # Purely generated root README (GEN markers, no user tail) → delete.
        existing = f"# Documentation\n\n{_GEN_START}\nold index\n{_GEN_END}\n"
        action, body = _resolve_root_readme_removal(existing)
        assert action == "delete" and body is None

    def test_removal_empty_deletes(self):
        action, body = _resolve_root_readme_removal("")
        assert action == "delete" and body is None

    def test_removal_preserves_user_tail(self):
        existing = (f"# Documentation\n\n{_GEN_START}\nold\n{_GEN_END}\n"
                    "## My notes\nkeep me\n")
        action, body = _resolve_root_readme_removal(existing)
        assert action == "preserve"
        assert "## My notes" in body and "keep me" in body
        assert "old" not in body  # generated zone dropped

    def test_removal_handwritten_no_markers_skipped_with_warn(self, capsys):
        existing = "# Hand-written index\nimportant content\n"  # no GEN markers
        action, body = _resolve_root_readme_removal(existing)
        assert action == "skip" and body is None
        assert "root_readme_no_markers" in capsys.readouterr().err

    def test_run_per_lang_bare_root_removes_generated_readme(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        # per-lang signal: a secondary translation registered in state
        (docs / ".rebuild-state.json").write_text(
            '{"primary_lang": "vi", "translations": {"en": {}}}', encoding="utf-8")
        # a pre-existing generated root README should be removed
        (docs / "README.md").write_text(
            f"# Documentation\n\n{_GEN_START}\nstale\n{_GEN_END}\n", encoding="utf-8")
        _write_index_readme(str(docs), None, "2026-01-01T00:00:00Z")
        assert not (docs / "README.md").exists()  # deleted, no root README in per-lang

    def test_run_single_lang_bare_root_writes_full_index(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        # single-lang: no translations → NOT a pointer
        (docs / ".rebuild-state.json").write_text('{"primary_lang": "en"}', encoding="utf-8")
        _write_index_readme(str(docs), None, "2026-01-01T00:00:00Z")
        body = (docs / "README.md").read_text(encoding="utf-8")
        assert "[`en/`](en/README.md)" not in body  # full index, not a pointer
