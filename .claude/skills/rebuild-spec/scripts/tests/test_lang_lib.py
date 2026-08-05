"""Tests for _lang_lib.py — language resolution helpers."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _lang_lib import (
    detect_layout_mode,
    looks_unusual,
    normalize_lang,
    resolve_docs_root,
)


class TestNormalizeLang:
    def test_none_returns_en(self):
        assert normalize_lang(None) == "en"

    def test_empty_returns_en(self):
        assert normalize_lang("") == "en"

    def test_whitespace_returns_en(self):
        assert normalize_lang("   ") == "en"

    def test_uppercase_lowered(self):
        assert normalize_lang("VI") == "vi"

    def test_mixed_case(self):
        assert normalize_lang("Pt-BR") == "pt-br"

    def test_jp_aliased_to_ja(self):
        # [D1] post-alias reality: jp resolves to canonical ISO ja
        assert normalize_lang("jp") == "ja"

    def test_strips_whitespace(self):
        assert normalize_lang("  vi  ") == "vi"

    def test_en_passthrough(self):
        assert normalize_lang("en") == "en"


class TestNormalizeLangAliases:
    def test_jp_to_ja(self):
        assert normalize_lang("jp") == "ja"

    def test_japan_to_ja(self):
        assert normalize_lang("japan") == "ja"

    def test_cn_to_zh(self):
        assert normalize_lang("cn") == "zh"

    def test_kr_to_ko(self):
        assert normalize_lang("kr") == "ko"

    def test_vn_to_vi(self):
        assert normalize_lang("vn") == "vi"

    def test_uppercase_alias(self):
        assert normalize_lang("JP") == "ja"

    def test_valid_iso_passthrough(self):
        # Already-valid codes are never rewritten.
        assert normalize_lang("ja") == "ja"
        assert normalize_lang("vi") == "vi"
        assert normalize_lang("en") == "en"

    def test_region_tag_passthrough(self):
        assert normalize_lang("zh-cn") == "zh-cn"
        assert normalize_lang("pt-br") == "pt-br"

    def test_alias_preserves_region_suffix(self):
        # Only the primary subtag is aliased; the region suffix survives.
        assert normalize_lang("jp-x") == "ja-x"


class TestResolveDocsRoot:
    def test_en_returns_docs(self):
        assert resolve_docs_root("en") == "docs"

    def test_vi_returns_docs_vi(self):
        assert resolve_docs_root("vi") == "docs/vi"

    def test_uppercase_normalized(self):
        assert resolve_docs_root("VI") == "docs/vi"

    def test_pt_br(self):
        assert resolve_docs_root("pt-br") == "docs/pt-br"

    def test_none_defaults_en(self):
        assert resolve_docs_root(None) == "docs"

    def test_empty_defaults_en(self):
        assert resolve_docs_root("") == "docs"


class TestNormalizeLangPathTraversal:
    def test_slash_rejected(self):
        with pytest.raises(ValueError, match="unsafe path characters"):
            normalize_lang("../etc")

    def test_backslash_rejected(self):
        with pytest.raises(ValueError, match="unsafe path characters"):
            normalize_lang("ja\\..\\etc")

    def test_dot_dot_rejected(self):
        with pytest.raises(ValueError, match="unsafe path characters"):
            normalize_lang("..")

    def test_absolute_path_rejected(self):
        with pytest.raises(ValueError, match="unsafe path characters"):
            normalize_lang("/abs")

    def test_hidden_traversal_rejected(self):
        with pytest.raises(ValueError, match="unsafe path characters"):
            normalize_lang("ja/../../")


class TestLooksUnusual:
    def test_standard_two_letter(self):
        assert looks_unusual("en") is False
        assert looks_unusual("vi") is False
        assert looks_unusual("jp") is False

    def test_three_letter(self):
        assert looks_unusual("vie") is False

    def test_with_region(self):
        assert looks_unusual("pt-br") is False
        assert looks_unusual("zh-hans") is False

    def test_single_char_unusual(self):
        assert looks_unusual("x") is True

    def test_numbers_only(self):
        assert looks_unusual("123") is True

    def test_special_chars(self):
        assert looks_unusual("en_US") is True

    def test_none_normalized_to_en(self):
        assert looks_unusual(None) is False

    def test_path_traversal_is_unusual(self):
        assert looks_unusual("../etc") is True
        assert looks_unusual("/abs") is True


class TestResolveDocsRootModeAware:
    # Back-compat single-arg form (legacy callers) — unchanged behavior.
    def test_backcompat_en_root(self):
        assert resolve_docs_root("en") == "docs"

    def test_backcompat_nonen_subdir(self):
        assert resolve_docs_root("vi") == "docs/vi"

    # en-primary single-lang → root (the only "docs" case).
    def test_en_primary_single_root(self):
        assert resolve_docs_root("en", "en", multilang=False) == "docs"

    # en-primary per-lang → docs/en (primary itself moves under docs/en).
    def test_en_primary_per_lang(self):
        assert resolve_docs_root("en", "en", multilang=True) == "docs/en"
        assert resolve_docs_root("vi", "en", multilang=True) == "docs/vi"

    # non-en primary single-lang → already docs/<primary> (current behavior, C2).
    def test_vi_primary_single(self):
        assert resolve_docs_root("vi", "vi", multilang=False) == "docs/vi"

    # non-en primary per-lang.
    def test_vi_primary_per_lang(self):
        assert resolve_docs_root("vi", "vi", multilang=True) == "docs/vi"
        assert resolve_docs_root("en", "vi", multilang=True) == "docs/en"

    # alias is applied inside the resolver.
    def test_alias_in_resolver(self):
        assert resolve_docs_root("jp", "en", multilang=True) == "docs/ja"


class TestDetectLayoutMode:
    def test_no_state_single(self):
        assert detect_layout_mode("en", state=None) == "single"

    def test_empty_translations_single(self):
        assert detect_layout_mode("en", state={"translations": {}}) == "single"

    def test_secondary_registered_per_lang(self):
        assert detect_layout_mode("en", state={"translations": {"vi": {}}}) == "per-lang"

    def test_primary_only_translation_is_single(self):
        # A translations entry equal to the primary is not a secondary.
        assert detect_layout_mode("en", state={"translations": {"en": {}}}) == "single"

    def test_alias_key_counts_as_primary(self):
        # primary=ja, a "jp" key normalizes to ja → not a secondary.
        assert detect_layout_mode("ja", state={"translations": {"jp": {}}}) == "single"

    def test_sentinel_signals_per_lang(self, tmp_path):
        primary_dir = tmp_path / "en"
        primary_dir.mkdir()
        (primary_dir / ".layout-migrated").write_text("", encoding="utf-8")
        assert detect_layout_mode("en", docs_base=str(tmp_path), state={}) == "per-lang"

    def test_bare_dir_without_sentinel_is_single(self, tmp_path):
        # Bare docs/<primary>/ directory existence is NOT a per-lang signal (C2).
        (tmp_path / "vi").mkdir()
        assert detect_layout_mode("vi", docs_base=str(tmp_path), state={}) == "single"
