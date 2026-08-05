"""Tests for validate_design_intent_density.py (Wave D.2 gate, F11c).

Coverage: mode-agnostic citation-density scan — uncited-asserted paragraph flagged,
cited paragraph (ADR/business-rules.md/architecture.md/file:line) passes, [INFERRED]-tagged
paragraph passes, disclaimer banner is skipped regardless of run mode (no --re-mode flag
exists on this validator — it is NOT the re-output-contract.md RE-mode check), fenced code and
headings/tables never trigger a finding, missing-file warning, CLI exit codes + summary merge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_design_intent_density import validate, main  # noqa: E402

DISCLAIMER = (
    "<!-- disclaimer:start -->\n"
    "EXPERIMENTAL — this document is heavily [INFERRED] and unvalidated. Treat every "
    "claim below as inference unless it carries an explicit ADR or code citation before "
    "you rely on any of it for a real decision about this system's architecture.\n"
    "<!-- disclaimer:end -->\n"
)

UNCITED_PARAGRAPH = (
    "This system uses an event-driven architecture because the team wanted loose "
    "coupling between services and needed to scale independently over time as traffic "
    "grew across many different regions worldwide."
)

ADR_CITED_PARAGRAPH = (
    "Per ADR-003, the team chose a soft-delete pattern to preserve audit history across "
    "all entities in the system for compliance purposes going forward into the future."
)

DOC_CITED_PARAGRAPH = (
    "As documented in business-rules.md, the invariant that orders cannot be cancelled "
    "after shipment reflects a deliberate trade-off between customer flexibility and "
    "fulfillment cost that the team accepted early in the project's life."
)

FILE_LINE_CITED_PARAGRAPH = (
    "The queue consumer retries failed jobs with exponential backoff, as seen in "
    "app/jobs/consumer.rb:42, to avoid overwhelming downstream services during traffic "
    "spikes that occur during seasonal peaks."
)

INFERRED_PARAGRAPH = (
    "[INFERRED] The repeated soft-delete column across six different models suggests a "
    "deliberate audit-history preservation strategy, though no ADR or comment confirms "
    "this reasoning anywhere in the codebase that was inspected during this pass."
)

SHORT_PARAGRAPH = "No distinctive pattern detected here."


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _doc(*paragraphs: str) -> str:
    body = "\n\n".join(paragraphs)
    return f"# Design Intent\n\n{DISCLAIMER}\n## Architecture Choices\n\n{body}\n"


class TestValidate:
    def test_uncited_asserted_paragraph_is_flagged(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(UNCITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "DesignIntent.uncited_assertion" for i in result["issues"])

    def test_adr_cited_paragraph_passes(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(ADR_CITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS"
        assert result["summary"]["critical"] == 0

    def test_doc_cited_paragraph_passes(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(DOC_CITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS"

    def test_file_line_cited_paragraph_passes(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(FILE_LINE_CITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS"

    def test_inferred_tagged_paragraph_passes(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(INFERRED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS"

    def test_disclaimer_banner_never_flagged(self, tmp_path):
        # The banner itself has zero citations by design (F11a) — must never be flagged,
        # even standing alone with no other paragraphs.
        content = f"# Design Intent\n\n{DISCLAIMER}\n"
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", content)
        result = validate(di_path)
        assert result["status"] == "PASS"
        assert result["summary"]["critical"] == 0

    def test_short_paragraph_excluded_from_gate(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(SHORT_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS"

    def test_fenced_code_never_flagged(self, tmp_path):
        content = (
            f"# Design Intent\n\n{DISCLAIMER}\n"
            "```\n" + UNCITED_PARAGRAPH + "\n```\n"
        )
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", content)
        result = validate(di_path)
        assert result["status"] == "PASS"

    def test_table_rows_never_flagged(self, tmp_path):
        content = (
            f"# Design Intent\n\n{DISCLAIMER}\n"
            "| Choice | Rationale |\n|---|---|\n"
            "| Event-driven | " + UNCITED_PARAGRAPH + " |\n"
        )
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", content)
        result = validate(di_path)
        assert result["status"] == "PASS"

    def test_mode_agnostic_no_re_mode_flag_exists(self, tmp_path):
        """F11c: this validator has NO --re-mode gate — it always runs. Confirmed by
        the absence of a --re-mode CLI argument (distinct from validate_source_citations.py)."""
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(UNCITED_PARAGRAPH))
        rc = main(["--design-intent-file", str(di_path), "--project-root", str(tmp_path)])
        assert rc == 1  # fired without any mode flag being passed at all

    def test_missing_file_warns_not_crits(self, tmp_path):
        di_path = tmp_path / "plans/p1/artifacts/design-intent.md"
        result = validate(di_path)
        assert result["summary"]["critical"] == 0
        assert any(i["rule_id"] == "DesignIntent.file_missing" for i in result["issues"])

    def test_multiple_uncited_paragraphs_all_flagged(self, tmp_path):
        di_path = _write(
            tmp_path, "plans/p1/artifacts/design-intent.md",
            _doc(UNCITED_PARAGRAPH, ADR_CITED_PARAGRAPH, UNCITED_PARAGRAPH + " Second one.")
        )
        result = validate(di_path)
        assert result["status"] == "FAIL"
        assert result["summary"]["critical"] == 2


UNFILLED_PLACEHOLDER_PARAGRAPH = (
    "{Explain the architectural rationale behind this choice in 2-3 sentences, citing an "
    "ADR, business-rules.md, architecture.md, or a file:line, or tag the sentence "
    "[INFERRED] if no such source exists in the codebase being documented right now.}"
)

MIXED_REAL_PLUS_PLACEHOLDER_PARAGRAPH = (
    "Per ADR-003, the team chose a soft-delete pattern. "
    "{Add more detail here about the specific trade-offs considered during the review "
    "before this decision was finalized by the team.}"
)


class TestPlaceholderStripping:
    """Minor regression (PR #176 phase-01): unfilled `{...}` scaffold guidance text must
    never be flagged as an uncited assertion (parity with derive_confidence_report's
    PLACEHOLDER_RE)."""

    def test_unfilled_placeholder_paragraph_not_flagged(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md",
                         _doc(UNFILLED_PLACEHOLDER_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS", result["issues"]

    def test_real_sentence_plus_trailing_placeholder_still_passes_via_its_own_citation(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md",
                         _doc(MIXED_REAL_PLUS_PLACEHOLDER_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS", result["issues"]

    def test_uncited_real_prose_still_flagged_after_placeholder_strip(self, tmp_path):
        # Guard against over-stripping: a genuinely uncited paragraph with no braces at
        # all must still be caught.
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(UNCITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "FAIL"


DELPHI_FILE_LINE_CITED_PARAGRAPH = (
    "The nightly batch job locks the ledger table before posting entries, as seen in "
    "unit1.pas:42, to avoid concurrent writers corrupting the balance during the close "
    "process that runs every night after business hours end."
)

ORACLE_SQL_FILE_LINE_CITED_PARAGRAPH = (
    "The trigger recalculates the running total on insert, as implemented in "
    "schema.sql:10, so downstream reports never see a stale balance during the batch "
    "window that follows the nightly close."
)


class TestI6LegacyStackExtensions:
    """I6: `_FILE_LINE_RE` must accept Delphi/Oracle legacy-stack citations
    (pas/dpr/dfm/sql/pks/pkb/pls) so legit citations there aren't read as uncited."""

    def test_delphi_pas_citation_passes(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md",
                         _doc(DELPHI_FILE_LINE_CITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS", result["issues"]

    def test_oracle_sql_citation_passes(self, tmp_path):
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md",
                         _doc(ORACLE_SQL_FILE_LINE_CITED_PARAGRAPH))
        result = validate(di_path)
        assert result["status"] == "PASS", result["issues"]

    @pytest.mark.parametrize("ext", ["dpr", "dfm", "pks", "pkb", "pls"])
    def test_remaining_legacy_extensions_pass(self, tmp_path, ext):
        paragraph = (
            f"The startup sequence wires the main form's dependencies, as seen in "
            f"main.{ext}:7, before control is handed back to the runtime event loop "
            "that drives the rest of the application for its whole lifetime."
        )
        di_path = _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(paragraph))
        result = validate(di_path)
        assert result["status"] == "PASS", result["issues"]


class TestMain:
    def test_cli_pass_exit_zero(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(ADR_CITED_PARAGRAPH))
        rc = main([
            "--plan-dir", str(tmp_path / "plans" / "p1"),
            "--project-root", str(tmp_path),
        ])
        assert rc == 0

    def test_cli_fail_exit_one(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(UNCITED_PARAGRAPH))
        rc = main([
            "--plan-dir", str(tmp_path / "plans" / "p1"),
            "--project-root", str(tmp_path),
        ])
        assert rc == 1

    def test_cli_summary_out_written(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/design-intent.md", _doc(ADR_CITED_PARAGRAPH))
        summary_out = tmp_path / "plans" / "p1" / "artifacts" / "validation" / "design-intent-validation-summary.json"
        rc = main([
            "--plan-dir", str(tmp_path / "plans" / "p1"),
            "--project-root", str(tmp_path),
            "--summary-out", str(summary_out),
        ])
        assert rc == 0
        data = json.loads(summary_out.read_text(encoding="utf-8"))
        assert data["validators"]["design_intent_density"]["status"] == "PASS"

    def test_cli_non_directory_plan_dir_errors(self, tmp_path):
        rc = main(["--plan-dir", str(tmp_path / "nope"), "--project-root", str(tmp_path)])
        assert rc == 2

    def test_cli_requires_plan_dir_or_file(self):
        with pytest.raises(SystemExit):
            main([])
