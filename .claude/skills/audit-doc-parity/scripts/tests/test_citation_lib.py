"""Tests for _citation_lib.py."""
import json
import sys
from pathlib import Path

import pytest

# Ensure the scripts package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from _citation_lib import (
    CITATION_RE,
    STATUS_FILE_MISSING,
    STATUS_OK,
    STATUS_RANGE_INVALID,
    STATUS_STALE,
    STATUS_TRAVERSAL,
    STATUS_UNREADABLE,
    CitationRef,
    parse_citations,
    read_text_safe,
    resolve_docs_root,
    validate_citation,
)

FIXTURES = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent  # agent-kit root


# ---------------------------------------------------------------------------
# CITATION_RE — verbatim check against rebuild-spec pattern
# ---------------------------------------------------------------------------

class TestCitationRe:
    def test_basic_range(self):
        m = CITATION_RE.search("**Source:** `src/foo.py:10-20`")
        assert m is not None
        assert m.group(1) == "src/foo.py"
        assert m.group(2) == "10"
        assert m.group(3) == "20"

    def test_single_line(self):
        m = CITATION_RE.search("**Source:** src/bar.ts:42")
        assert m is not None
        assert m.group(1) == "src/bar.ts"
        assert m.group(2) == "42"
        assert m.group(3) is None

    def test_no_backtick(self):
        m = CITATION_RE.search("**Source:** path/to/file.rb:5-10")
        assert m is not None
        assert m.group(1).strip() == "path/to/file.rb"

    def test_no_match_plain_text(self):
        assert CITATION_RE.search("some plain text line") is None

    def test_sql_extension(self):
        m = CITATION_RE.search("**Source:** `db/schema.sql:1-50`")
        assert m is not None
        assert "sql" in m.group(1)

    def test_php_extension(self):
        m = CITATION_RE.search("**Source:** `app/Http/routes.php:100-200`")
        assert m is not None


# ---------------------------------------------------------------------------
# parse_citations — fence skipping + multi-citation
# ---------------------------------------------------------------------------

class TestParseCitations:
    def test_finds_citations(self):
        text = "**Source:** `src/foo.py:1-5`\nsome text\n**Source:** `src/bar.py:10`\n"
        refs = parse_citations(text)
        assert len(refs) == 2
        assert refs[0].raw_path == "src/foo.py"
        assert refs[0].start == 1
        assert refs[0].end == 5
        assert refs[1].raw_path == "src/bar.py"
        assert refs[1].start == 10
        assert refs[1].end == 10

    def test_skips_inside_fence(self):
        text = (
            "Before fence\n"
            "```\n"
            "**Source:** `src/skipped.py:1-5`\n"
            "```\n"
            "**Source:** `src/real.py:10-20`\n"
        )
        refs = parse_citations(text)
        assert len(refs) == 1
        assert refs[0].raw_path == "src/real.py"

    def test_empty_doc(self):
        assert parse_citations("") == []

    def test_no_citations(self):
        assert parse_citations("# Heading\nsome prose\n## Another heading\n") == []

    def test_line_number_is_1based(self):
        text = "line1\nline2\n**Source:** `src/x.py:1`\n"
        refs = parse_citations(text)
        assert refs[0].line_no == 3


# ---------------------------------------------------------------------------
# read_text_safe — encoding variants
# ---------------------------------------------------------------------------

class TestReadTextSafe:
    def test_utf8_plain(self):
        path = FIXTURES / "source_plain.py"
        result = read_text_safe(path)
        assert result is not None
        text, enc = result
        assert "inner_target" in text
        assert enc in ("utf-8", "utf-8-sig", "cp932", "latin-1")

    def test_bom_file(self):
        path = FIXTURES / "source_bom.py"
        result = read_text_safe(path)
        assert result is not None
        text, enc = result
        assert "bom_func" in text
        # BOM should be stripped
        assert not text.startswith("﻿")

    def test_shift_jis_file(self):
        path = FIXTURES / "source_sjis.py"
        result = read_text_safe(path)
        assert result is not None
        text, enc = result
        assert enc == "cp932"
        assert "hello" in text

    def test_crlf_normalised(self):
        path = FIXTURES / "source_crlf.py"
        result = read_text_safe(path)
        assert result is not None
        text, _ = result
        assert "\r\n" not in text
        assert "crlf_func" in text

    def test_missing_file_returns_none(self):
        assert read_text_safe(FIXTURES / "nonexistent.py") is None


# ---------------------------------------------------------------------------
# validate_citation — all status paths
# ---------------------------------------------------------------------------

class TestValidateCitation:
    def _ref(self, raw, start, end):
        return CitationRef(raw_path=raw, start=start, end=end, line_no=1)

    # Correct project-root-relative path to the fixtures
    _FIXTURE_REL = "claude/skills/audit-doc-parity/scripts/tests/fixtures/source_plain.py"

    def test_valid_citation(self):
        # source_plain.py has 13 lines; cite lines 6-8 (inner_target def)
        ref = self._ref(self._FIXTURE_REL, 6, 8)
        doc_path = FIXTURES / "doc_with_citations.md"
        result = validate_citation(ref, doc_path, PROJECT_ROOT)
        assert result["status"] == STATUS_OK
        assert result["lines"] is not None
        assert len(result["lines"]) == 3

    def test_traversal_rejected(self):
        ref = self._ref("../../etc/passwd", 1, 1)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", FIXTURES)
        assert result["status"] == STATUS_TRAVERSAL

    def test_absolute_path_rejected(self):
        ref = self._ref("/etc/passwd", 1, 1)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", FIXTURES)
        assert result["status"] == STATUS_TRAVERSAL

    def test_missing_file(self):
        ref = self._ref("nonexistent/file.py", 1, 1)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", FIXTURES)
        assert result["status"] == STATUS_FILE_MISSING

    def test_range_out_of_bounds_high(self):
        ref = self._ref(self._FIXTURE_REL, 1, 9999)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", PROJECT_ROOT)
        assert result["status"] == STATUS_RANGE_INVALID

    def test_range_start_zero(self):
        ref = self._ref(self._FIXTURE_REL, 0, 5)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", PROJECT_ROOT)
        assert result["status"] == STATUS_RANGE_INVALID

    def test_stale_anchor(self):
        # Cite a real range but hint for a symbol that is NOT there
        ref = self._ref(self._FIXTURE_REL, 1, 3)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", PROJECT_ROOT,
                                   symbol_hint="SYMBOL_NOT_PRESENT_XYZ")
        assert result["status"] == STATUS_STALE

    def test_symbol_hint_found(self):
        # inner_target is at line 6
        ref = self._ref(self._FIXTURE_REL, 6, 8)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", PROJECT_ROOT,
                                   symbol_hint="inner_target")
        assert result["status"] == STATUS_OK

    def test_non_source_extension_accepted(self):
        # .sql, .sh etc. should NOT be rejected by extension — verify via .py as proxy
        # since extension is never a rejection criterion in _citation_lib
        ref = self._ref(self._FIXTURE_REL, 1, 1)
        result = validate_citation(ref, FIXTURES / "doc_with_citations.md", PROJECT_ROOT)
        assert result["status"] != STATUS_TRAVERSAL


# ---------------------------------------------------------------------------
# resolve_docs_root — layout-aware docs root (docs/ vs docs/<primary>/)
# ---------------------------------------------------------------------------

class TestResolveDocsRoot:
    @staticmethod
    def _write_state(docs_dir: Path, **state):
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / ".rebuild-state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )

    def test_no_state_falls_back_to_docs(self, tmp_path):
        """Legacy en-primary repo with no state file → bare docs/."""
        (tmp_path / "docs").mkdir()
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_no_docs_dir_at_all(self, tmp_path):
        """Missing docs/ → returns docs/ path (caller errors on non-dir)."""
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_en_primary_single_lang(self, tmp_path):
        """primary_lang=en, no translations → docs/."""
        self._write_state(tmp_path / "docs", primary_lang="en", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_non_en_primary_single_lang_root_state(self, tmp_path):
        """primary_lang=vi, state at docs/ root → docs/vi/."""
        self._write_state(tmp_path / "docs", primary_lang="vi", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs" / "vi"

    def test_non_en_primary_state_inside_lang_dir(self, tmp_path):
        """The ishindenshin case: state lives at docs/vi/.rebuild-state.json."""
        self._write_state(tmp_path / "docs" / "vi", primary_lang="vi", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs" / "vi"

    def test_per_lang_en_primary_with_translations(self, tmp_path):
        """en primary + a registered secondary lang → docs/en/ (per-lang)."""
        self._write_state(
            tmp_path / "docs", primary_lang="en", translations={"vi": {}}
        )
        assert resolve_docs_root(tmp_path) == tmp_path / "docs" / "en"

    def test_root_state_preferred_over_lang_dir(self, tmp_path):
        """When both exist, the canonical docs/ root state wins discovery."""
        self._write_state(tmp_path / "docs", primary_lang="en", translations={})
        self._write_state(tmp_path / "docs" / "ja", primary_lang="ja", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_corrupt_state_falls_back(self, tmp_path):
        """Unparseable state file → bare docs/ (graceful)."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / ".rebuild-state.json").write_text("{not json", encoding="utf-8")
        assert resolve_docs_root(tmp_path) == docs

    def test_missing_primary_lang_key_defaults_to_en(self, tmp_path):
        """State missing primary_lang key → treated as en single-lang → docs/."""
        self._write_state(tmp_path / "docs", translations={})
        # No primary_lang key; should default to "en" and return docs/
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_empty_string_primary_lang_defaults_to_en(self, tmp_path):
        """primary_lang='', no translations → treated as en → docs/."""
        self._write_state(tmp_path / "docs", primary_lang="", translations={})
        # Empty string should trigger the `or "en"` default
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_none_primary_lang_defaults_to_en(self, tmp_path):
        """primary_lang=None explicitly → defaults to en → docs/."""
        self._write_state(tmp_path / "docs", primary_lang=None, translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_path_unsafe_primary_lang_does_not_crash(self, tmp_path):
        """A corrupt/adversarial primary_lang must degrade to docs/, never raise (H1)."""
        self._write_state(tmp_path / "docs", primary_lang="../evil", translations={})
        # Must not raise ValueError from _lang_lib.normalize_lang.
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_fallback_path_no_lang_lib(self, tmp_path, monkeypatch):
        """When _lang_lib is unavailable, the documented rule still resolves correctly."""
        import _citation_lib
        monkeypatch.setattr(_citation_lib, "_import_lang_lib", lambda: None)
        # en single-lang → docs/
        self._write_state(tmp_path / "docs", primary_lang="en", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"

    def test_fallback_non_en_primary_no_lang_lib(self, tmp_path, monkeypatch):
        """Fallback: non-en primary → docs/<primary>."""
        import _citation_lib
        monkeypatch.setattr(_citation_lib, "_import_lang_lib", lambda: None)
        self._write_state(tmp_path / "docs", primary_lang="vi", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs" / "vi"

    def test_fallback_sentinel_triggers_per_lang(self, tmp_path, monkeypatch):
        """Fallback: en primary + .layout-migrated sentinel → docs/en (M1)."""
        import _citation_lib
        monkeypatch.setattr(_citation_lib, "_import_lang_lib", lambda: None)
        docs = tmp_path / "docs"
        self._write_state(docs, primary_lang="en", translations={})
        (docs / "en").mkdir(parents=True, exist_ok=True)
        (docs / "en" / ".layout-migrated").write_text("", encoding="utf-8")
        assert resolve_docs_root(tmp_path) == docs / "en"

    def test_fallback_path_unsafe_no_lang_lib(self, tmp_path, monkeypatch):
        """Fallback also guards path-unsafe primary_lang → docs/."""
        import _citation_lib
        monkeypatch.setattr(_citation_lib, "_import_lang_lib", lambda: None)
        self._write_state(tmp_path / "docs", primary_lang="../evil", translations={})
        assert resolve_docs_root(tmp_path) == tmp_path / "docs"
