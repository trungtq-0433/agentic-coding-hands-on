"""Integration tests for renumber_artifact_ids.py and rewrite_slice_plan_keys (F13).

Covers all 16 rows of the Success Criteria matrix in phase-01-renumber-core.md:
  gap compaction, chain collision, slug tail, mermaid fence rewrite,
  non-mermaid fence skipped+WARN, per-spec token coexist, citation untouched,
  idempotency, sibling apply + absent-sibling skip, report-only, atomic write,
  stale map ignored, sentinel collision exit 2, per-artifact map path,
  DISC sep, overflow detected.
"""
from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _id_schemes_lib import apply_map, rewrite_text, segment_text  # noqa: E402
from renumber_artifact_ids import rewrite_slice_plan_keys, run  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_plan(tmp_path: Path, artifact: str, content: str) -> tuple[Path, Path]:
    """Create a minimal plan directory with one artifact file. Returns (plan_dir, artifact_path)."""
    plan_dir = tmp_path / "plan"
    art_dir = plan_dir / "artifacts"
    art_dir.mkdir(parents=True)
    art_path = art_dir / f"{artifact}.md"
    art_path.write_text(content, encoding="utf-8")
    return plan_dir, art_path


def invoke(
    artifact: str,
    plan_dir: Path,
    project_root: Path | None = None,
    map_out: Path | None = None,
    report_only: bool = False,
) -> int:
    if project_root is None:
        project_root = plan_dir.parent
    if map_out is None:
        map_out = plan_dir / "artifacts" / f"renumber-map-{artifact}.json"
    return run(
        artifact=artifact,
        plan_dir=plan_dir,
        project_root=project_root,
        map_out=map_out,
        report_only=report_only,
    )


# ---------------------------------------------------------------------------
# 1. Gap compaction
# ---------------------------------------------------------------------------

class TestGapCompaction:
    def test_us_gap_compaction(self, tmp_path):
        content = "US001 first\nUS005 second\nUS013 third\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        assert "US001" in result
        assert "US002" in result
        assert "US003" in result
        # Original gap codes gone
        assert "US005" not in result
        assert "US013" not in result


# ---------------------------------------------------------------------------
# 2. Chain collision prevention
# ---------------------------------------------------------------------------

class TestChainCollision:
    def test_no_clobber(self, tmp_path):
        # US001, US002, US003 exist; US005 also present.
        # After compaction: US001→US001, US002→US002, US003→US003, US005→US004.
        # Old scenario for collision: if US003 were mapping to US002 at same time
        # US005 maps to US003 — two-phase prevents clobber.
        content = "US002 then US005 then US003\n"
        # Doc order: US002, US005, US003 → map: US002→US001, US005→US002, US003→US003
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        # Exactly one US001, one US002, one US003 — no duplication
        assert result.count("US001") == 1
        assert result.count("US002") == 1
        assert result.count("US003") == 1
        assert "US004" not in result
        assert "US005" not in result

    def test_apply_map_chain_collision(self):
        # Direct unit test of two-phase sentinel logic
        # US003 → US002; US005 → US003 (classic chain scenario)
        mapping = {"US003": "US002", "US005": "US003"}
        text = "US003 and US005"
        result = apply_map(text, mapping, "US", "")
        assert result == "US002 and US003"
        # No duplication of US002
        assert result.count("US002") == 1
        assert result.count("US003") == 1


# ---------------------------------------------------------------------------
# 3. Slug tail preserved
# ---------------------------------------------------------------------------

class TestSlugTailPreserved:
    def test_slug_tail_intact(self, tmp_path):
        content = "See US005_Login for details\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        assert "US001_Login" in result
        assert "US005_Login" not in result

    def test_apply_map_preserves_slug(self):
        mapping = {"US005": "US001"}
        result = apply_map("US005_Login here", mapping, "US", "")
        assert result == "US001_Login here"


# ---------------------------------------------------------------------------
# 4. Mermaid fence rewritten
# ---------------------------------------------------------------------------

class TestMermaidFenceRewrite:
    def test_scr_in_mermaid_rewritten(self, tmp_path):
        content = textwrap.dedent("""\
            Some prose SCR003 text.
            ```mermaid
            graph TD
                A[SCR003_Dashboard] --> B[SCR007_Settings]
            ```
            End prose.
        """)
        plan_dir, art_path = make_plan(tmp_path, "screen-list", content)
        rc = invoke("screen-list", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        # SCR003 → SCR001 (first seen), SCR007 → SCR002
        assert "SCR001" in result
        assert "SCR002" in result
        assert "SCR003" not in result
        assert "SCR007" not in result
        # Still inside a mermaid fence block
        assert "```mermaid" in result

    def test_segment_text_mermaid_kind(self):
        text = "prose\n```mermaid\nnode\n```\nmore\n"
        parts = list(segment_text(text))
        kinds = [k for k, _ in parts]
        assert "mermaid" in kinds


# ---------------------------------------------------------------------------
# 5. Non-mermaid fence skipped + WARN
# ---------------------------------------------------------------------------

class TestNonMermaidFenceSkipped:
    def test_python_fence_byte_identical(self, tmp_path):
        content = textwrap.dedent("""\
            Prose US001 text.
            ```python
            # Implements US005
            def foo():
                pass
            ```
            End US003.
        """)
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        # Inside python fence must be untouched
        assert "# Implements US005" in result

    def test_stale_id_in_code_fence_emits_warn(self, tmp_path, capsys):
        content = textwrap.dedent("""\
            Prose US005 text.
            ```python
            # Implements US005
            ```
        """)
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        captured = capsys.readouterr()
        assert "[WARN]" in captured.err
        assert "US005" in captured.err
        assert "skipped code fence" in captured.err

    def test_rewrite_text_skips_non_mermaid(self):
        text = "```python\nUS005\n```\n"
        mapping = {"US005": "US001"}
        result = rewrite_text(text, mapping, "US", "", Path("test.md"))
        assert result == text  # byte-identical


# ---------------------------------------------------------------------------
# 6. Per-spec token coexistence (FR-/SC-/DEC- survive US renumber)
# ---------------------------------------------------------------------------

class TestPerSpecTokenCoexist:
    def test_fr_sc_dec_untouched(self, tmp_path):
        content = "FR-001 SC-002 DEC-003 US005 end\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        assert "FR-001" in result
        assert "SC-002" in result
        assert "DEC-003" in result
        assert "US001" in result   # US005 compacted to US001
        assert "US005" not in result


# ---------------------------------------------------------------------------
# 7. Citation untouched
# ---------------------------------------------------------------------------

class TestCitationUntouched:
    def test_source_citation_byte_identical(self, tmp_path):
        citation = "**Source:** a/b.ts:42-61"
        content = f"US005 story\n{citation}\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        assert citation in result


# ---------------------------------------------------------------------------
# 8. Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_rerun_no_change(self, tmp_path):
        content = "US001 first\nUS002 second\nUS003 third\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        # First run — already contiguous, should be no-op
        rc1 = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc1 == 0
        mtime_after_first = art_path.stat().st_mtime
        content_after_first = art_path.read_text(encoding="utf-8")

        # Second run
        rc2 = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc2 == 0
        assert art_path.read_text(encoding="utf-8") == content_after_first

    def test_rerun_after_gap_compaction(self, tmp_path):
        content = "US001\nUS005\nUS013\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        after_first = art_path.read_text(encoding="utf-8")

        invoke("user-stories", plan_dir, project_root=tmp_path)
        after_second = art_path.read_text(encoding="utf-8")
        assert after_first == after_second


# ---------------------------------------------------------------------------
# 9. Sibling apply + absent sibling skip
# ---------------------------------------------------------------------------

class TestSiblingApply:
    def test_present_sibling_gets_map_applied(self, tmp_path):
        # SCR renumber: screen-flow.md exists → should be updated
        content = "SCR003 screen\nSCR007 another\n"
        plan_dir, art_path = make_plan(tmp_path, "screen-list", content)

        sibling_path = plan_dir / "artifacts" / "screen-flow.md"
        sibling_path.write_text("node SCR003_Dashboard\nnode SCR007_Settings\n", encoding="utf-8")

        rc = invoke("screen-list", plan_dir, project_root=tmp_path)
        assert rc == 0
        sib_result = sibling_path.read_text(encoding="utf-8")
        assert "SCR001" in sib_result
        assert "SCR002" in sib_result
        assert "SCR003" not in sib_result
        assert "SCR007" not in sib_result

    def test_absent_sibling_skipped_no_error(self, tmp_path):
        content = "SCR003 screen\n"
        plan_dir, art_path = make_plan(tmp_path, "screen-list", content)
        # user-stories.md is a sibling for SCR but we don't create it
        rc = invoke("screen-list", plan_dir, project_root=tmp_path)
        assert rc == 0


# ---------------------------------------------------------------------------
# 10. Report-only
# ---------------------------------------------------------------------------

class TestReportOnly:
    def test_report_only_no_md_written(self, tmp_path):
        content = "US001\nUS005\nUS013\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        original = art_path.read_text(encoding="utf-8")

        rc = invoke("user-stories", plan_dir, project_root=tmp_path, report_only=True)
        assert rc == 0
        assert art_path.read_text(encoding="utf-8") == original

    def test_report_only_no_map_file_written(self, tmp_path):
        content = "US001\nUS005\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        map_out = plan_dir / "artifacts" / "renumber-map-user-stories.json"

        rc = invoke("user-stories", plan_dir, project_root=tmp_path, report_only=True)
        assert rc == 0
        assert not map_out.exists()


# ---------------------------------------------------------------------------
# 11. Atomic write
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    def test_tmp_file_does_not_persist(self, tmp_path):
        content = "US001\nUS005\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        # No .tmp file should linger
        for f in (plan_dir / "artifacts").iterdir():
            assert not f.name.endswith(".tmp"), f"Orphaned .tmp: {f}"

    def test_original_preserved_if_no_change(self, tmp_path):
        content = "US001\nUS002\nUS003\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        assert art_path.read_text(encoding="utf-8") == content


# ---------------------------------------------------------------------------
# 12. Stale map ignored
# ---------------------------------------------------------------------------

class TestStaleMapIgnored:
    def test_stale_map_overwritten_at_start(self, tmp_path):
        content = "US001\nUS005\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        map_out = plan_dir / "artifacts" / "renumber-map-user-stories.json"

        # Write a stale map that has wrong/stale data
        map_out.write_text(json.dumps({"US": {"US999": "US001"}}), encoding="utf-8")

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0

        # Map file must have been overwritten with current run's data
        new_map = json.loads(map_out.read_text(encoding="utf-8"))
        assert "US999" not in str(new_map)

    def test_stale_map_not_applied_to_sibling(self, tmp_path):
        # The sibling must only get the IN-MEMORY map, not a stale file map
        content = "SCR003\n"
        plan_dir, art_path = make_plan(tmp_path, "screen-list", content)

        sibling = plan_dir / "artifacts" / "screen-flow.md"
        sibling.write_text("SCR003 node\n", encoding="utf-8")

        stale_map = plan_dir / "artifacts" / "renumber-map-screen-list.json"
        stale_map.write_text(json.dumps({"SCR": {"SCR099": "SCR001"}}), encoding="utf-8")

        invoke("screen-list", plan_dir, project_root=tmp_path)
        sib_result = sibling.read_text(encoding="utf-8")

        # SCR003 → SCR001 from in-memory map (stale SCR099 must NOT appear)
        assert "SCR001" in sib_result
        assert "SCR099" not in sib_result


# ---------------------------------------------------------------------------
# 13. Sentinel collision → exit 2, no file written
# ---------------------------------------------------------------------------

class TestSentinelCollision:
    def test_sentinel_in_content_aborts(self, tmp_path):
        # Text containing the sentinel base must trigger exit 2
        content = "US005 text \x00RN0\x00 more\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        original = art_path.read_text(encoding="utf-8")

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 2
        # File must NOT have been modified
        assert art_path.read_text(encoding="utf-8") == original

    def test_sentinel_in_content_no_partial_write(self, tmp_path):
        content = "US005\x00RN\x00extra\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        # No .tmp orphan
        for f in (plan_dir / "artifacts").iterdir():
            assert not f.name.endswith(".tmp")


# ---------------------------------------------------------------------------
# 14. Per-artifact map path (F6)
# ---------------------------------------------------------------------------

class TestPerArtifactMapPath:
    def test_map_file_named_per_artifact(self, tmp_path):
        content = "US001\nUS005\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0

        expected_map = plan_dir / "artifacts" / "renumber-map-user-stories.json"
        assert expected_map.exists(), "Per-artifact map file must exist"

        # Generic name must NOT be created
        generic = plan_dir / "artifacts" / "renumber-map.json"
        assert not generic.exists(), "Shared renumber-map.json must NOT be created"

    def test_different_artifact_different_map(self, tmp_path):
        content_us = "US001\nUS005\n"
        content_fl = "F001\nF007\n"
        plan_dir = tmp_path / "plan"
        art_dir = plan_dir / "artifacts"
        art_dir.mkdir(parents=True)
        (art_dir / "user-stories.md").write_text(content_us, encoding="utf-8")
        (art_dir / "feature-list.md").write_text(content_fl, encoding="utf-8")

        invoke("user-stories", plan_dir, project_root=tmp_path)
        invoke("feature-list", plan_dir, project_root=tmp_path)

        assert (art_dir / "renumber-map-user-stories.json").exists()
        assert (art_dir / "renumber-map-feature-list.json").exists()


# ---------------------------------------------------------------------------
# 15. DISC separator
# ---------------------------------------------------------------------------

class TestDiscSep:
    def test_disc_gap_compaction(self, tmp_path):
        # DISC is in ARTIFACT_OWNS only if we add it; test via direct run() with
        # a synthetic artifact. Since DISC is NOT in ARTIFACT_OWNS, we test the
        # underlying lib directly here (integration of segment + apply_map).
        # Per spec, DISC renumber through the same path as others if added to owns.
        # We test the sep="-" logic via apply_map directly:
        mapping = {"DISC-003": "DISC-002"}
        text = "DISC-001 here, DISC-003 there"
        result = apply_map(text, mapping, "DISC", "-")
        assert result == "DISC-001 here, DISC-002 there"

    def test_disc_token_re_requires_hyphen(self):
        from _id_schemes_lib import token_re
        pat = token_re("DISC", "-")
        assert pat.search("DISC-001") is not None
        assert pat.search("DISC001") is None


# ---------------------------------------------------------------------------
# 16. Overflow detection
# ---------------------------------------------------------------------------

class TestOverflowDetection:
    def test_overflow_token_emits_warn(self, tmp_path, capsys):
        content = "US1000 overflow\nUS001 normal\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0

        captured = capsys.readouterr()
        assert "[WARN]" in captured.err
        assert "US1000" in captured.err
        assert "overflow" in captured.err

    def test_overflow_token_left_untouched(self, tmp_path):
        content = "US1000 overflow\nUS001 normal\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        result = art_path.read_text(encoding="utf-8")
        assert "US1000" in result  # not renumbered

    def test_find_overflow_tokens_direct(self):
        from _id_schemes_lib import find_overflow_tokens
        tokens = find_overflow_tokens("US1000 in text", "US", "")
        assert "US1000" in tokens

    def test_three_digit_not_overflow(self, tmp_path):
        import contextlib
        import io
        content = "US001 normal\nUS999 also normal\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        assert "overflow" not in buf.getvalue()


# ---------------------------------------------------------------------------
# 17. Slice-plan key rewrite (F13)
# ---------------------------------------------------------------------------

class TestSlicePlanKeyRewrite:
    """Tests for rewrite_slice_plan_keys (F13): old F### keys → new keys, values untouched."""

    def _make_slice_plan(self, tmp_path: Path, data: dict) -> Path:
        """Write a _slice-plan.json under _fragments/feature-list/ and return the path."""
        frag_dir = tmp_path / "_fragments" / "feature-list"
        frag_dir.mkdir(parents=True, exist_ok=True)
        sp = frag_dir / "_slice-plan.json"
        sp.write_text(json.dumps(data), encoding="utf-8")
        return sp

    def test_keys_rewritten_with_map(self, tmp_path):
        """Old F### keys are rewritten to new codes using the provided map."""
        sp = self._make_slice_plan(tmp_path, {
            "F005": {"members": ["US001", "SCR002"]},
            "F013": {"members": ["US004", "SCR007"]},
        })
        full_map = {"F": {"F005": "F001", "F013": "F002"}}
        rewrite_slice_plan_keys(sp, full_map, tmp_path)
        result = json.loads(sp.read_text(encoding="utf-8"))
        assert "F001" in result
        assert "F002" in result
        assert "F005" not in result
        assert "F013" not in result

    def test_values_untouched(self, tmp_path):
        """Values (US###/SCR### references) are NOT modified by slice-plan key rewrite."""
        sp = self._make_slice_plan(tmp_path, {
            "F005": {"members": ["US001", "SCR002", "F005_self_ref"]},
        })
        full_map = {"F": {"F005": "F001"}}
        rewrite_slice_plan_keys(sp, full_map, tmp_path)
        result = json.loads(sp.read_text(encoding="utf-8"))
        # Key was rewritten
        assert "F001" in result
        # Value is untouched
        assert result["F001"]["members"] == ["US001", "SCR002", "F005_self_ref"]

    def test_absent_file_is_noop(self, tmp_path):
        """When _slice-plan.json does not exist, no error is raised and nothing is written."""
        absent = tmp_path / "_fragments" / "feature-list" / "_slice-plan.json"
        assert not absent.exists()
        full_map = {"F": {"F005": "F001"}}
        rewrite_slice_plan_keys(absent, full_map, tmp_path)  # must not raise
        assert not absent.exists()

    def test_already_contiguous_noop(self, tmp_path):
        """If no key appears in the map, the file is left byte-identical (no write)."""
        original = {"F001": {"members": ["US001"]}, "F002": {"members": ["US002"]}}
        sp = self._make_slice_plan(tmp_path, original)
        mtime_before = sp.stat().st_mtime
        full_map = {"F": {}}  # empty map → nothing to rewrite
        rewrite_slice_plan_keys(sp, full_map, tmp_path)
        # File should not be touched (mtime unchanged or content identical)
        assert json.loads(sp.read_text(encoding="utf-8")) == original

    def test_empty_map_no_change(self, tmp_path):
        """An empty full_map results in no key rewrites."""
        data = {"F007": {"members": []}}
        sp = self._make_slice_plan(tmp_path, data)
        rewrite_slice_plan_keys(sp, {}, tmp_path)
        assert json.loads(sp.read_text(encoding="utf-8")) == data

    def test_integration_feature_list_run_rewrites_slice_plan(self, tmp_path):
        """End-to-end: invoking run() on feature-list rewrites _slice-plan.json keys."""
        # Create feature-list artifact with non-contiguous F codes
        content = "### F005: AuthFeature\nsome content\n\n### F013: DashboardFeature\nmore content\n"
        plan_dir, art_path = make_plan(tmp_path, "feature-list", content)

        # Create the _fragments/feature-list/_slice-plan.json with old F### keys
        frag_dir = plan_dir / "_fragments" / "feature-list"
        frag_dir.mkdir(parents=True, exist_ok=True)
        slice_plan_path = frag_dir / "_slice-plan.json"
        slice_plan_path.write_text(json.dumps({
            "F005": {"members": ["US001"]},
            "F013": {"members": ["US002"]},
        }), encoding="utf-8")

        rc = invoke("feature-list", plan_dir, project_root=tmp_path)
        assert rc == 0

        # Artifact codes should be compacted
        result_text = art_path.read_text(encoding="utf-8")
        assert "F001" in result_text
        assert "F002" in result_text
        assert "F005" not in result_text
        assert "F013" not in result_text

        # Slice-plan keys should also be rewritten
        sp_result = json.loads(slice_plan_path.read_text(encoding="utf-8"))
        assert "F001" in sp_result
        assert "F002" in sp_result
        assert "F005" not in sp_result
        assert "F013" not in sp_result


# ---------------------------------------------------------------------------
# Phase-04 edge-case regression tests
# ---------------------------------------------------------------------------

class TestDenseChainCollision:
    """Dense US001..US020 range with holes — final IDs exactly US001..N, no dups."""

    def test_dense_downshift_no_duplicates(self, tmp_path):
        """20 US codes with several interior holes → compact to US001..N with no duplicates."""
        # Build 20 codes with holes at odd positions above 10
        codes = [f"US{i:03d}" for i in [1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37]]
        content = " ".join(codes) + "\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")

        n = len(codes)  # 20 unique codes → should compact to US001..US020
        # Every compacted code must appear exactly once
        for i in range(1, n + 1):
            code = f"US{i:03d}"
            assert result.count(code) == 1, f"Expected exactly 1 occurrence of {code}, got {result.count(code)}"

        # No original large code should remain
        for original in codes:
            if int(original[2:]) > n:
                assert original not in result, f"Old code {original} should be gone"

    def test_dense_downshift_result_contiguous(self, tmp_path):
        """After dense downshift the codes form a gapless 001..N sequence."""
        codes = [f"US{i:03d}" for i in range(1, 21)]  # US001..US020, already contiguous
        # Remove every 3rd entry to create gaps
        sparse = [c for idx, c in enumerate(codes) if (idx + 1) % 3 != 0]  # 13 remain
        content = " ".join(sparse) + "\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")

        n = len(sparse)
        # Exactly US001..US<n> present, nothing beyond
        for i in range(1, n + 1):
            assert f"US{i:03d}" in result
        assert f"US{n + 1:03d}" not in result


class TestMermaidScrRenameSibling:
    """SCR renamed in screen-list AND screen-flow mermaid simultaneously consistent."""

    def test_scr_rename_in_both_docs_consistent(self, tmp_path):
        """After renumber, SCR codes in screen-list body AND screen-flow mermaid match."""
        screen_list_content = textwrap.dedent("""\
            ## SCR005_Login
            Some description.
            ## SCR012_Dashboard
            Another description.
        """)
        screen_flow_content = textwrap.dedent("""\
            ```mermaid
            graph TD
                A[SCR005_Login] --> B[SCR012_Dashboard]
                B --> A
            ```
        """)
        plan_dir, art_path = make_plan(tmp_path, "screen-list", screen_list_content)
        sibling_path = plan_dir / "artifacts" / "screen-flow.md"
        sibling_path.write_text(screen_flow_content, encoding="utf-8")

        rc = invoke("screen-list", plan_dir, project_root=tmp_path)
        assert rc == 0

        sl_result = art_path.read_text(encoding="utf-8")
        sf_result = sibling_path.read_text(encoding="utf-8")

        # Both docs must use the same renamed codes; original codes gone
        assert "SCR005" not in sl_result
        assert "SCR012" not in sl_result
        assert "SCR005" not in sf_result
        assert "SCR012" not in sf_result

        # Compacted codes present in both
        assert "SCR001" in sl_result
        assert "SCR002" in sl_result
        assert "SCR001" in sf_result
        assert "SCR002" in sf_result

    def test_scr_rename_sibling_mermaid_fence_rewritten(self, tmp_path):
        """Mermaid fence in sibling screen-flow.md is rewritten (not skipped)."""
        screen_list_content = "## SCR003_SettingsPage\n"
        screen_flow_content = textwrap.dedent("""\
            Some prose SCR003 text.
            ```mermaid
            stateDiagram-v2
                SCR003_SettingsPage --> SCR003_SettingsPage : reload
            ```
        """)
        plan_dir, art_path = make_plan(tmp_path, "screen-list", screen_list_content)
        sibling_path = plan_dir / "artifacts" / "screen-flow.md"
        sibling_path.write_text(screen_flow_content, encoding="utf-8")

        rc = invoke("screen-list", plan_dir, project_root=tmp_path)
        assert rc == 0

        sf_result = sibling_path.read_text(encoding="utf-8")
        assert "SCR001" in sf_result
        assert "SCR003" not in sf_result
        assert "```mermaid" in sf_result  # fence preserved


class TestEmptyArtifact:
    """Artifact with zero codes → gate PASS, renumber is no-op, no file writes."""

    def test_zero_codes_exit_zero(self, tmp_path):
        """An artifact with no IDs at all → renumber returns 0."""
        content = "# Header\nSome prose with no codes.\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0

    def test_zero_codes_content_unchanged(self, tmp_path):
        """No codes → file content identical after renumber (no writes)."""
        content = "# Header\nSome prose with no codes.\n"
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        invoke("user-stories", plan_dir, project_root=tmp_path)
        assert art_path.read_text(encoding="utf-8") == content

    def test_empty_string_artifact_exit_zero(self, tmp_path):
        """Completely empty artifact → renumber returns 0."""
        plan_dir, art_path = make_plan(tmp_path, "user-stories", "")
        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0


class TestFcodeOrdering:
    """Feature-list renumber produces artifact file with new codes so W5 post-step
    (canonical-fcode derivation) operates on the compacted F### codes, not the originals."""

    def test_feature_list_artifact_has_new_codes_after_renumber(self, tmp_path):
        """After invoking run() on feature-list, only compacted F### codes remain in the file."""
        content = textwrap.dedent("""\
            ## Feature Hierarchy
            | F### | Name |
            |------|------|
            | F005 | Auth |
            | F013 | Dashboard |

            ### F005: Auth
            Auth details.

            ### F013: Dashboard
            Dashboard details.
        """)
        plan_dir, art_path = make_plan(tmp_path, "feature-list", content)
        rc = invoke("feature-list", plan_dir, project_root=tmp_path)
        assert rc == 0

        result = art_path.read_text(encoding="utf-8")
        # After renumber, downstream W5 reads F001 and F002 (not F005/F013)
        assert "F001" in result
        assert "F002" in result
        assert "F005" not in result
        assert "F013" not in result

    def test_feature_list_new_codes_used_for_canonical_fcode_derivation(self, tmp_path):
        """The post-renumber artifact only exposes new F### codes — any parser building
        _canonical-fcodes.json from the file will see the compacted codes."""
        content = "### F007: AlphaFeature\n### F021: BetaFeature\n### F099: GammaFeature\n"
        plan_dir, art_path = make_plan(tmp_path, "feature-list", content)
        rc = invoke("feature-list", plan_dir, project_root=tmp_path)
        assert rc == 0

        result = art_path.read_text(encoding="utf-8")
        # Compacted to F001, F002, F003
        for expected in ["F001", "F002", "F003"]:
            assert expected in result, f"Expected {expected} in renumbered feature-list"
        for old in ["F007", "F021", "F099"]:
            assert old not in result, f"Old code {old} should be gone after renumber"


# ---------------------------------------------------------------------------
# FIX C1: process-flows multi-file renumber
# ---------------------------------------------------------------------------

class TestProcessFlowsMultiFile:
    """process-flows resolves to artifacts/flows/*.md (multi-file, sorted order)."""

    def _make_flows(self, tmp_path: Path, files: dict[str, str]) -> Path:
        """Create a plan dir with artifacts/flows/<name>.md files. Returns plan_dir."""
        plan_dir = tmp_path / "plan"
        flows_dir = plan_dir / "artifacts" / "flows"
        flows_dir.mkdir(parents=True)
        for name, content in files.items():
            (flows_dir / name).write_text(content, encoding="utf-8")
        return plan_dir

    def test_renumber_compacts_across_two_files(self, tmp_path):
        """FLOW### gap across two files → both files rewritten with compact map."""
        plan_dir = self._make_flows(tmp_path, {
            "a.md": "FLOW001 first state\nFLOW003 second state\n",
            "b.md": "FLOW005 third state\n",
        })
        rc = invoke("process-flows", plan_dir, project_root=tmp_path)
        assert rc == 0

        a_text = (plan_dir / "artifacts" / "flows" / "a.md").read_text(encoding="utf-8")
        b_text = (plan_dir / "artifacts" / "flows" / "b.md").read_text(encoding="utf-8")

        # a.md: FLOW001→FLOW001 (no change), FLOW003→FLOW002
        assert "FLOW001" in a_text
        assert "FLOW002" in a_text
        assert "FLOW003" not in a_text

        # b.md: FLOW005→FLOW003
        assert "FLOW003" in b_text
        assert "FLOW005" not in b_text

    def test_renumber_cross_file_map_consistent(self, tmp_path):
        """All three compacted codes are FLOW001, FLOW002, FLOW003 — no gaps."""
        plan_dir = self._make_flows(tmp_path, {
            "a.md": "FLOW001 first\nFLOW003 second\n",
            "b.md": "FLOW005 third\n",
        })
        invoke("process-flows", plan_dir, project_root=tmp_path)

        a_text = (plan_dir / "artifacts" / "flows" / "a.md").read_text(encoding="utf-8")
        b_text = (plan_dir / "artifacts" / "flows" / "b.md").read_text(encoding="utf-8")

        combined = a_text + b_text
        assert "FLOW001" in combined
        assert "FLOW002" in combined
        assert "FLOW003" in combined
        # Nothing beyond FLOW003
        assert "FLOW004" not in combined
        assert "FLOW005" not in combined

    def test_empty_flows_dir_noop_exit_zero(self, tmp_path):
        """Empty artifacts/flows/ → no-op, exit 0."""
        plan_dir = tmp_path / "plan"
        flows_dir = plan_dir / "artifacts" / "flows"
        flows_dir.mkdir(parents=True)

        rc = invoke("process-flows", plan_dir, project_root=tmp_path)
        assert rc == 0

    def test_missing_flows_dir_noop_exit_zero(self, tmp_path):
        """Missing artifacts/flows/ → no-op, exit 0 (no FLOW files to process)."""
        plan_dir = tmp_path / "plan"
        (plan_dir / "artifacts").mkdir(parents=True)

        rc = invoke("process-flows", plan_dir, project_root=tmp_path)
        assert rc == 0

    def test_single_flow_file_compacted(self, tmp_path):
        """Single flows/*.md with a gap → compacted."""
        plan_dir = self._make_flows(tmp_path, {
            "entity.md": "FLOW003 only flow\n",
        })
        rc = invoke("process-flows", plan_dir, project_root=tmp_path)
        assert rc == 0

        text = (plan_dir / "artifacts" / "flows" / "entity.md").read_text(encoding="utf-8")
        assert "FLOW001" in text
        assert "FLOW003" not in text

    def test_already_contiguous_flows_is_noop(self, tmp_path):
        """Already-contiguous FLOW codes across files → no writes needed."""
        plan_dir = self._make_flows(tmp_path, {
            "a.md": "FLOW001 first\n",
            "b.md": "FLOW002 second\n",
        })
        a_path = plan_dir / "artifacts" / "flows" / "a.md"
        b_path = plan_dir / "artifacts" / "flows" / "b.md"
        original_a = a_path.read_text(encoding="utf-8")
        original_b = b_path.read_text(encoding="utf-8")

        rc = invoke("process-flows", plan_dir, project_root=tmp_path)
        assert rc == 0
        assert a_path.read_text(encoding="utf-8") == original_a
        assert b_path.read_text(encoding="utf-8") == original_b


# ---------------------------------------------------------------------------
# FIX A4: map built from fence content
# ---------------------------------------------------------------------------

class TestMapScopeExcludesFence:
    """A4: renumber map must be built from prose+mermaid only, not from code fences."""

    def test_id_only_in_closed_fence_not_in_map(self, tmp_path, capsys):
        """US005 appearing only inside a closed python fence → not in renumber map, file unchanged."""
        content = (
            "US001 prose entry\n"
            "```python\n"
            "# Implements US005\n"
            "```\n"
        )
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        original = art_path.read_text(encoding="utf-8")

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        # File unchanged: US005 was not in map, no rewrite happened
        assert art_path.read_text(encoding="utf-8") == original
        # Warn emitted about skipped fence ID
        captured = capsys.readouterr()
        assert "US005" in captured.err
        assert "fence" in captured.err.lower()

    def test_id_only_in_closed_fence_not_in_map_file(self, tmp_path):
        """Map JSON must not contain an entry for a fence-only ID."""
        content = (
            "US001 prose entry\n"
            "```python\n"
            "# Implements US005\n"
            "```\n"
        )
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        map_out = plan_dir / "artifacts" / "renumber-map-user-stories.json"

        invoke("user-stories", plan_dir, project_root=tmp_path)
        # US001 is contiguous alone; map should be empty (no renames needed)
        if map_out.exists():
            m = json.loads(map_out.read_text(encoding="utf-8"))
            # US005 must not appear in the emitted map at all
            assert "US005" not in str(m), f"Fence-only ID US005 must not be in map: {m}"

    def test_id_only_in_unclosed_fence_at_eof_not_in_map(self, tmp_path, capsys):
        """US003 in an unclosed fence at EOF → not in renumber map, warn emitted."""
        # Unclosed fence: no closing ``` before end of file
        content = (
            "US001 prose entry\n"
            "```python\n"
            "# US003 reference without closing fence\n"
        )
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)
        original = art_path.read_text(encoding="utf-8")

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        # File unchanged: US003 in unclosed fence not in scope
        assert art_path.read_text(encoding="utf-8") == original
        captured = capsys.readouterr()
        assert "US003" in captured.err

    def test_id_in_mermaid_fence_is_in_map_and_rewritten(self, tmp_path):
        """US003 appearing only in a mermaid fence → in map and rewritten (mermaid is prose-equivalent scope)."""
        content = (
            "```mermaid\n"
            "graph TD\n"
            "    A[US003_Login]\n"
            "```\n"
        )
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        # US003 → US001 (only code, compacted to 001)
        assert "US001" in result
        assert "US003" not in result

    def test_id_in_prose_takes_precedence_over_fence(self, tmp_path):
        """US003 in prose + US003 also in python fence → prose wins, ID in map and rewritten in prose."""
        content = (
            "US003 prose entry\n"
            "```python\n"
            "# US003 also in fence\n"
            "```\n"
        )
        plan_dir, art_path = make_plan(tmp_path, "user-stories", content)

        rc = invoke("user-stories", plan_dir, project_root=tmp_path)
        assert rc == 0
        result = art_path.read_text(encoding="utf-8")
        # Prose US003 → US001; fence US003 stays (code fence skipped by rewrite_text)
        assert "US001 prose entry" in result
        assert "# US003 also in fence" in result  # fence untouched
