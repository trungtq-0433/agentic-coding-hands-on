"""Tests for derive_confidence_report.py — A1 deterministic confidence-report sidecar.

Covers: citation/marker extraction (per-section, fence-skipping), confidence_derived math,
disclaimer/legend rendering, best-effort behavior (never fails the pass), and the F15
regression guard that the companion never enters FEATURE_FILES / the promotion gate.
"""
from __future__ import annotations

import re

import pytest

from derive_confidence_report import (
    LIMITATION_NOTES,
    compute_stats,
    derive,
    extract_claims,
    main,
    render_companion,
)

FIXTURE_ARTIFACT = """# F001_Sample

## Cross-Cutting Logic

- **BR-001**: Users must verify email before login. **Source:** `app/models/user.rb:10-14`
- **BR-002**: [UNVERIFIED] Session timeout defaults to 30 minutes — needs runtime confirmation.

## Polymorphic Behavior

- **DISC-001**: [NEEDS_DOMAIN_CONFIRMATION] — legacy flag; unknown whether bug or intentional.

```
**Source:** `should/be/skipped.rb:1`
[INFERRED] fenced content must never be counted
```
"""

NO_CLAIMS_ARTIFACT = "# F002_Empty\n\n## Overview\n\nNothing here carries a citation or marker.\n"


def _frontmatter_int(content: str, key: str) -> int:
    m = re.search(rf"^{key}:\s*(\d+)\s*$", content, re.MULTILINE)
    assert m, f"{key} not found in frontmatter:\n{content[:300]}"
    return int(m.group(1))


def _frontmatter_raw(content: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+?)\s*$", content, re.MULTILINE)
    assert m, f"{key} not found in frontmatter:\n{content[:300]}"
    return m.group(1)


class TestExtractClaims:
    def test_counts_citation_and_markers_exhaustively(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        assert len(claims) == 3

    def test_citation_row_status_and_evidence(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        cited = [c for c in claims if c["status"] == "○"]
        assert len(cited) == 1
        assert cited[0]["evidence"] == "app/models/user.rb:10-14"
        assert cited[0]["section"] == "Cross-Cutting Logic"

    def test_marker_rows_status_and_sections(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        marked = [c for c in claims if c["status"] == "△"]
        assert len(marked) == 2
        sections = {c["section"] for c in marked}
        assert sections == {"Cross-Cutting Logic", "Polymorphic Behavior"}
        assert all(c["evidence"] == "—" for c in marked)

    def test_fenced_code_block_never_counted(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        assert not any("skipped.rb" in c["evidence"] for c in claims)
        assert not any("fenced content" in c["claim"] for c in claims)

    def test_no_claims_when_none_present(self):
        assert extract_claims(NO_CLAIMS_ARTIFACT) == []


class TestComputeStats:
    def test_math_matches_with_evidence_over_total(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        total, with_evidence, confidence_derived = compute_stats(claims)
        assert total == 3
        assert with_evidence == 1
        assert confidence_derived == round(with_evidence / total, 4)

    def test_zero_claims_confidence_is_null_not_zero(self):
        total, with_evidence, confidence_derived = compute_stats([])
        assert (total, with_evidence, confidence_derived) == (0, 0, None)


class TestRenderCompanion:
    def test_disclaimer_and_boundary_present(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        total, with_evidence, cd = compute_stats(claims)
        content = render_companion("technical-spec.md", claims, total, with_evidence, cd)
        assert "NOT a correctness verification" in content
        assert "audit-doc-parity" in content

    def test_legend_and_table_header_present(self):
        content = render_companion("technical-spec.md", [], 0, 0, None)
        assert "○" in content and "△" in content
        assert "| Claim | Section | Evidence (file:line) | Status ○/△ |" in content

    def test_no_reviewer_checklist_section(self):
        # F15 — the companion must never grow a standalone reviewer-checklist section.
        content = render_companion("technical-spec.md", [], 0, 0, None)
        assert "reviewer checklist" not in content.lower()

    def test_zero_claims_risk_flag(self):
        content = render_companion("technical-spec.md", [], 0, 0, None)
        assert "No detectable claims" in content
        assert "confidence_derived: null" in content


class TestDerive:
    def test_writes_companion_with_correct_frontmatter_math(self, tmp_path):
        artifact = tmp_path / "technical-spec.md"
        artifact.write_text(FIXTURE_ARTIFACT, encoding="utf-8")
        out_path = derive(artifact, project_root=tmp_path)
        assert out_path == tmp_path / "confidence-report_technical-spec.md"
        content = out_path.read_text(encoding="utf-8")
        total = _frontmatter_int(content, "claims_total")
        with_evidence = _frontmatter_int(content, "claims_with_evidence")
        cd = float(_frontmatter_raw(content, "confidence_derived"))
        assert total == 3
        assert with_evidence == 1
        assert cd == round(with_evidence / total, 4)
        assert _frontmatter_raw(content, "source_artifact") == "technical-spec.md"

    def test_zero_claims_artifact_gets_null_confidence(self, tmp_path):
        artifact = tmp_path / "business-context.md"
        artifact.write_text(NO_CLAIMS_ARTIFACT, encoding="utf-8")
        out_path = derive(artifact, project_root=tmp_path)
        content = out_path.read_text(encoding="utf-8")
        assert _frontmatter_raw(content, "confidence_derived") == "null"


class TestMainBestEffort:
    def test_missing_artifact_returns_0_never_fails(self, tmp_path, capsys):
        rc = main(["--artifact", str(tmp_path / "does-not-exist.md")])
        assert rc == 0
        assert "[WARN]" in capsys.readouterr().err

    def test_success_path_returns_0_and_writes_companion(self, tmp_path):
        artifact = tmp_path / "technical-spec.md"
        artifact.write_text(FIXTURE_ARTIFACT, encoding="utf-8")
        rc = main(["--artifact", str(artifact), "--project-root", str(tmp_path)])
        assert rc == 0
        assert (tmp_path / "confidence-report_technical-spec.md").is_file()

    def test_write_failure_is_swallowed_never_raises(self, tmp_path, monkeypatch, capsys):
        artifact = tmp_path / "technical-spec.md"
        artifact.write_text(FIXTURE_ARTIFACT, encoding="utf-8")

        def _boom(*_args, **_kwargs):
            raise OSError("disk full (simulated)")

        monkeypatch.setattr("derive_confidence_report.derive", _boom)
        rc = main(["--artifact", str(artifact)])
        assert rc == 0
        assert "[WARN]" in capsys.readouterr().err


class TestFlowsAndGlossaryCompanions:
    """phase-02 (A1 remaining passes) — flows/glossary reuse the same generic derive()
    (per-artifact-stem naming), no pass-specific script branch needed."""

    def test_flows_slug_companion_naming(self, tmp_path):
        artifact = tmp_path / "EvaluationCycle.md"
        artifact.write_text(FIXTURE_ARTIFACT, encoding="utf-8")
        out_path = derive(artifact, project_root=tmp_path)
        assert out_path == tmp_path / "confidence-report_EvaluationCycle.md"
        content = out_path.read_text(encoding="utf-8")
        assert _frontmatter_raw(content, "source_artifact") == "EvaluationCycle.md"

    def test_glossary_companion_naming_and_math(self, tmp_path):
        artifact = tmp_path / "glossary.md"
        artifact.write_text(FIXTURE_ARTIFACT, encoding="utf-8")
        out_path = derive(artifact, project_root=tmp_path)
        assert out_path == tmp_path / "confidence-report_glossary.md"
        content = out_path.read_text(encoding="utf-8")
        assert _frontmatter_int(content, "claims_total") == 3
        assert _frontmatter_int(content, "claims_with_evidence") == 1


class TestLimitationNote:
    """--limitation-note synthesis (in-v1, Validation Session 1) — mandatory header caveat
    for system-synthesis/aggregate companions."""

    def test_synthesis_note_injected_after_disclaimer(self):
        claims = extract_claims(FIXTURE_ARTIFACT)
        total, with_evidence, cd = compute_stats(claims)
        content = render_companion(
            "overview.md", claims, total, with_evidence, cd, limitation_note="synthesis"
        )
        assert "Synthesis artifact" in content
        assert "do not compare against per-feature scores" in content
        # Header caveat must appear AFTER the standard disclaimer, before the Claims table.
        disclaimer_idx = content.index("NOT a correctness verification")
        note_idx = content.index("Synthesis artifact")
        table_idx = content.index("## Claims ↔ Evidence")
        assert disclaimer_idx < note_idx < table_idx

    def test_no_note_by_default(self):
        content = render_companion("technical-spec.md", [], 0, 0, None)
        assert "Synthesis artifact" not in content

    def test_unknown_note_key_ignored_silently(self):
        # Best-effort: an unrecognized key must never raise or corrupt the header.
        content = render_companion("overview.md", [], 0, 0, None, limitation_note="bogus")
        assert "Synthesis artifact" not in content

    def test_derive_passes_note_through(self, tmp_path):
        artifact = tmp_path / "overview.md"
        artifact.write_text(NO_CLAIMS_ARTIFACT, encoding="utf-8")
        out_path = derive(artifact, project_root=tmp_path, limitation_note="synthesis")
        content = out_path.read_text(encoding="utf-8")
        assert "Synthesis artifact" in content

    def test_cli_flag_injects_note(self, tmp_path):
        artifact = tmp_path / "overview.md"
        artifact.write_text(NO_CLAIMS_ARTIFACT, encoding="utf-8")
        rc = main([
            "--artifact", str(artifact), "--project-root", str(tmp_path),
            "--limitation-note", "synthesis",
        ])
        assert rc == 0
        content = (tmp_path / "confidence-report_overview.md").read_text(encoding="utf-8")
        assert "Synthesis artifact" in content

    def test_cli_rejects_unknown_choice(self, tmp_path):
        artifact = tmp_path / "overview.md"
        artifact.write_text(NO_CLAIMS_ARTIFACT, encoding="utf-8")
        with pytest.raises(SystemExit):
            main(["--artifact", str(artifact), "--limitation-note", "bogus"])

    def test_registry_has_exactly_synthesis_key(self):
        # Guard against silent scope creep — v1 ships exactly one limitation-note kind.
        assert set(LIMITATION_NOTES) == {"synthesis"}


class TestRegressionNeverGated:
    """F15 regression guard — the companion must never enter FEATURE_FILES or affect the
    promotion gate. Executed as a permanent test, not a one-time check."""

    def test_feature_files_tuple_unchanged_and_excludes_companion(self):
        from _slug_lib import FEATURE_FILES

        assert FEATURE_FILES == (
            "technical-spec.md", "business-context.md", "screens.md", "edge-cases.md",
        )
        assert not any("confidence-report" in f for f in FEATURE_FILES)

    def test_promotion_gate_missing_check_ignores_companion_file(self, tmp_path):
        from _slug_lib import FEATURE_FILES

        folder = tmp_path / "F001_Sample"
        folder.mkdir()
        for fname in FEATURE_FILES:
            (folder / fname).write_text("placeholder\n", encoding="utf-8")
        # A companion sidecar sitting alongside the 4 mandatory files must not be required,
        # and must not make the gate's missing-file check regress.
        (folder / "confidence-report_technical-spec.md").write_text("placeholder\n", encoding="utf-8")
        missing = [f for f in FEATURE_FILES if not (folder / f).is_file()]
        assert missing == []


DESIGN_INTENT_DISCLAIMER_ARTIFACT = """# Design Intent

**Status**: EXPERIMENTAL — report-only (see disclaimer below)

<!-- disclaimer:start -->
> **⚠ EXPERIMENTAL — read before trusting anything below.**
>
> This document infers "why the system was built this way".
>
> - Every claim below either cites its source (`ADR-###`, `business-rules.md`,
>   `architecture.md`, or a `file:line`) or is tagged **`[INFERRED]`** with a one-line reason.
> - Graduation from EXPERIMENTAL to default-promote requires `[INFERRED]` reasoning.
<!-- disclaimer:end -->

## Architecture Choices

- **DEC-001**: Soft-delete pattern chosen. **Source:** `app/models/order.rb:5`
"""


class TestDisclaimerBannerSkipped:
    """Minor regression (PR #176 phase-01): the design-intent disclaimer banner's own
    `[INFERRED]` marker tokens must never inflate claims_total (was +2 spurious triangles)."""

    def test_disclaimer_marker_tokens_excluded_from_claims(self):
        claims = extract_claims(DESIGN_INTENT_DISCLAIMER_ARTIFACT)
        # Only the real Source-cited DEC-001 claim should be counted — both [INFERRED]
        # tokens inside the disclaimer span must be gone.
        assert len(claims) == 1
        assert claims[0]["status"] == "○"
        assert claims[0]["evidence"] == "app/models/order.rb:5"

    def test_disclaimer_stripped_stats_not_inflated(self):
        claims = extract_claims(DESIGN_INTENT_DISCLAIMER_ARTIFACT)
        total, with_evidence, confidence_derived = compute_stats(claims)
        assert total == 1
        assert with_evidence == 1
        assert confidence_derived == 1.0

    def test_content_outside_disclaimer_still_scanned(self):
        claims = extract_claims(DESIGN_INTENT_DISCLAIMER_ARTIFACT)
        assert any(c["section"] == "Architecture Choices" for c in claims)


class TestTildeFenceSupport:
    """Minor regression: the shared iterator adds ~~~ fence support (the prior local
    loop only recognized ``` )."""

    def test_tilde_fenced_content_never_counted(self):
        text = (
            "# F001\n\n## Notes\n\n"
            "~~~\n**Source:** `should/be/skipped.rb:1`\n[INFERRED] also skipped\n~~~\n"
        )
        assert extract_claims(text) == []

    def test_content_after_tilde_fence_still_scanned(self):
        text = (
            "# F001\n\n## Notes\n\n~~~\nfenced\n~~~\n\n"
            "Real claim. **Source:** `real/file.rb:9`\n"
        )
        claims = extract_claims(text)
        assert len(claims) == 1
        assert claims[0]["evidence"] == "real/file.rb:9"


class TestPlaceholderBlindness:
    """v26.0.0 rework regression: `{...}` template-placeholder spans are instructions,
    not claims — a literal marker token inside one must never inflate claims_total
    (reviewer-reproduced on a fresh scaffold draft: 2 fake △ from B4 guidance text)."""

    def test_marker_inside_placeholder_span_not_counted(self):
        text = (
            "# F002\n\n## DB Impact per Event\n\n"
            "{One row per endpoint. Source cites `file:line` or `[INFERRED]`.}\n\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|---|---|---|---|---|---|\n"
            "| {METHOD /path} | `{t}` | {c} | {INSERT\\|UPDATE\\|DELETE} | {how} | "
            "`{path.ext:line — or an INFERRED tag if not citable}` |\n"
        )
        assert extract_claims(text) == []
        total, with_evidence, cd = compute_stats(extract_claims(text))
        assert (total, with_evidence, cd) == (0, 0, None)

    def test_real_marker_outside_placeholder_still_counted(self):
        text = (
            "# F002\n\n## DB Impact per Event\n\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|---|---|---|---|---|---|\n"
            "| POST /orders | `orders` | total | INSERT | sum of items | [INFERRED] |\n"
            "| POST /orders | `orders` | id | INSERT | sequence | **Source:** `app/o.rb:12` |\n"
        )
        claims = extract_claims(text)
        assert len(claims) == 2
        assert sorted(c["status"] for c in claims) == ["△", "○"]

    def test_citation_inside_placeholder_span_not_counted(self):
        text = "## X\n\n{example: **Source:** `a/b.rb:1`}\n"
        assert extract_claims(text) == []
