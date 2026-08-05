"""Integration tests for validate_feature_spec.py.
Runs script as subprocess with --spec <path>, parses stdout JSON,
asserts specific rule_ids present/absent per fixture.
Coverage per phase-05 test matrix.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT = SCRIPTS_DIR / "validate_feature_spec.py"


def _run(spec_path: Path) -> tuple[int, dict]:
    """Run the spec validator against a single spec and return (exit_code, json)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--spec", str(spec_path),
         "--project-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


def _issues(data: dict) -> list[dict]:
    """Flatten all issues across all spec entries."""
    all_issues = []
    for entry in data.get("specs", {}).values():
        all_issues.extend(entry.get("issues", []))
    return all_issues


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data)]


def _critical_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data) if i["severity"] == "critical"]


# ---------------------------------------------------------------------------
# spec-pass.md: well-formed spec — no critical issues expected
# ---------------------------------------------------------------------------

class TestSpecPass:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-pass.md")
        assert code == 0

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "specs" / "spec-pass.md")
        criticals = _critical_rule_ids(data)
        assert criticals == [], f"unexpected critical issues: {criticals}"

    def test_output_has_specs_key(self):
        _, data = _run(FIXTURES / "specs" / "spec-pass.md")
        assert "specs" in data


# ---------------------------------------------------------------------------
# spec-missing-h2.md: ## Business Workflow omitted
# ---------------------------------------------------------------------------

class TestSpecMissingH2:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-missing-h2.md")
        assert code == 1

    def test_required_sections_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-h2.md")
        assert "FeatureSpec.required_sections" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-h2.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.required_sections"]
        assert all(i["severity"] == "critical" for i in matching)


# ---------------------------------------------------------------------------
# spec-deprecated-heading.md: top-level ## Requirements present
# ---------------------------------------------------------------------------

class TestSpecDeprecatedHeading:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-deprecated-heading.md")
        assert code == 1

    def test_deprecated_headings_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-deprecated-heading.md")
        assert "FeatureSpec.deprecated_headings" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-deprecated-heading.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.deprecated_headings"]
        assert all(i["severity"] == "critical" for i in matching)


# ---------------------------------------------------------------------------
# spec-placeholder.md: contains {ROUTE_PATH} literal
# ---------------------------------------------------------------------------

class TestSpecPlaceholder:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-placeholder.md")
        assert code == 1

    def test_no_placeholder_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder.md")
        assert "Universal.no_placeholder" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "Universal.no_placeholder"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_placeholder(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "Universal.no_placeholder"]
        assert any("ROUTE_PATH" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# spec-placeholder-evasion.md: placeholder wrapped in <!-- a --> {X} <!-- b -->
# Regression for stage-3 finding F1 (comment net-depth evasion).
# Old per-line net-depth logic suppressed this; new strip_html_comments detects.
# ---------------------------------------------------------------------------

class TestSpecPlaceholderEvasion:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-placeholder-evasion.md")
        assert code == 1

    def test_no_placeholder_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder-evasion.md")
        assert "Universal.no_placeholder" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# spec-sm-fence-far.md: SM-001 heading + 50+ lines of intro before mermaid fence.
# Regression for stage-3 finding S1 (legacy 50-line window false positive).
# ---------------------------------------------------------------------------

class TestSpecSmFenceFar:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-sm-fence-far.md")
        assert code == 0

    def test_sm_mermaid_not_flagged(self):
        _, data = _run(FIXTURES / "specs" / "spec-sm-fence-far.md")
        assert "FeatureSpec.sm_mermaid" not in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# spec-sm-no-fence.md: SM-001 heading but no mermaid fence anywhere.
# Regression: sm_mermaid must still fire when the fence is genuinely missing.
# ---------------------------------------------------------------------------

class TestSpecSmNoFence:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-sm-no-fence.md")
        assert code == 1

    def test_sm_mermaid_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-sm-no-fence.md")
        assert "FeatureSpec.sm_mermaid" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# spec-dec-missing-field.md: DEC block missing **subtype:** field → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecDecMissingField:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        assert code == 1

    def test_dec_blocks_well_formed_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        assert "FeatureSpec.dec_blocks_well_formed" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_subtype(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert any("**subtype:**" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# spec-dec-invalid-subtype.md: DEC block with invalid subtype value → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecDecInvalidSubtype:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-dec-invalid-subtype.md")
        assert code == 1

    def test_dec_blocks_well_formed_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-invalid-subtype.md")
        assert "FeatureSpec.dec_blocks_well_formed" in _critical_rule_ids(data)

    def test_message_mentions_invalid_subtype(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-invalid-subtype.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert any("invalid" in i["message"].lower() for i in matching)


# ---------------------------------------------------------------------------
# spec-dec-lazy-na.md: Decision Logic N/A but JSX ternary in spec body → WARNING
# ---------------------------------------------------------------------------

class TestSpecDecLazyNa:
    def test_exit_code_zero(self):
        # warnings do not cause non-zero exit
        code, _ = _run(FIXTURES / "specs" / "spec-dec-lazy-na.md")
        assert code == 0

    def test_dec_lazy_na_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-lazy-na.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.dec_lazy_na" in rule_ids

    def test_issue_is_warning(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-lazy-na.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_lazy_na"]
        assert all(i["severity"] == "warning" for i in matching)


# ---------------------------------------------------------------------------
# spec-missing-client-anchor.md: missing **Client behavior:** anchor → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecMissingClientAnchor:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-missing-client-anchor.md")
        assert code == 1

    def test_missing_client_behavior_anchor_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-client-anchor.md")
        assert "FeatureSpec.missing_client_behavior_anchor" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-client-anchor.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.missing_client_behavior_anchor"]
        assert all(i["severity"] == "critical" for i in matching)


# ---------------------------------------------------------------------------
# spec-linked-fr-missing.md: BR-001 missing **Linked FR:** → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecLinkedFrMissing:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        assert code == 1

    def test_linked_fr_missing_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        assert "FeatureSpec.linked_fr_missing" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.linked_fr_missing"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_br_code(self):
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.linked_fr_missing"]
        assert any("BR-001" in i["message"] for i in matching)

    def test_present_linked_fr_not_flagged(self):
        # BR-002 has **Linked FR:** → should NOT appear in linked_fr_missing issues
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.linked_fr_missing"]
        assert not any("BR-002" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# spec-disc-boolean-values.md: DISC subsection with only true/false → WARNING
# ---------------------------------------------------------------------------

class TestSpecDiscBooleanValues:
    def test_exit_code_zero(self):
        # warnings do not cause non-zero exit
        code, _ = _run(FIXTURES / "specs" / "spec-disc-boolean-values.md")
        assert code == 0

    def test_disc_boolean_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-disc-boolean-values.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" in rule_ids

    def test_issue_is_warning(self):
        _, data = _run(FIXTURES / "specs" / "spec-disc-boolean-values.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.disc_boolean"]
        assert all(i["severity"] == "warning" for i in matching)


# ---------------------------------------------------------------------------
# spec-disc-enum-values.md: DISC subsection with enum values → no disc_boolean warning
# ---------------------------------------------------------------------------

class TestSpecDiscEnumValues:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-disc-enum-values.md")
        assert code == 0

    def test_disc_boolean_not_flagged(self):
        _, data = _run(FIXTURES / "specs" / "spec-disc-enum-values.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" not in rule_ids


# ---------------------------------------------------------------------------
# spec-alg-file-schema-missing.md: ALG-001 matches file-exchange vocab but has
# no populated **File Schema** table → WARNING (does not flip exit code)
# ---------------------------------------------------------------------------

def test_alg_file_schema_missing_warns():
    code, data = _run(FIXTURES / "specs" / "spec-alg-file-schema-missing.md")
    assert code == 0  # warning severity — never flips PASS→FAIL / exit code
    rule_ids = [i["rule_id"] for i in _issues(data)]
    assert "FeatureSpec.alg_file_schema_missing" in rule_ids
    matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.alg_file_schema_missing"]
    assert all(i["severity"] == "warning" for i in matching)


# ---------------------------------------------------------------------------
# spec-alg-file-schema-present.md: ALG-001 has a populated **File Schema** table
# → no alg_file_schema_missing warning
# ---------------------------------------------------------------------------

def test_alg_file_schema_present_passes():
    code, data = _run(FIXTURES / "specs" / "spec-alg-file-schema-present.md")
    assert code == 0
    rule_ids = [i["rule_id"] for i in _issues(data)]
    assert "FeatureSpec.alg_file_schema_missing" not in rule_ids


# ---------------------------------------------------------------------------
# spec-alg-non-file-exchange.md: ALG block has no import/export vocabulary
# (includes an "important" substring guard) → no alg_file_schema_missing warning
# ---------------------------------------------------------------------------

def test_alg_non_file_exchange_no_warn():
    code, data = _run(FIXTURES / "specs" / "spec-alg-non-file-exchange.md")
    assert code == 0
    rule_ids = [i["rule_id"] for i in _issues(data)]
    assert "FeatureSpec.alg_file_schema_missing" not in rule_ids


# ---------------------------------------------------------------------------
# disc_boolean: header/separator normalization (H2 fix)
# Ensures lowercase "| value |" headers and "| --- | --- |" spaced separators
# are excluded from non_bool_table so the boolean detection still fires.
# ---------------------------------------------------------------------------

class TestDiscBooleanHeaderNormalization:
    def test_lowercase_value_header_triggers_disc_boolean(self):
        # spec-disc-bool-lowercase-header.md: boolean DISC with lowercase "| value |" header
        _, data = _run(FIXTURES / "specs" / "spec-disc-bool-lowercase-header.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" in rule_ids

    def test_spaced_separator_triggers_disc_boolean(self):
        # spec-disc-bool-spaced-sep.md: boolean DISC with "| --- | --- |" spaced separator
        _, data = _run(FIXTURES / "specs" / "spec-disc-bool-spaced-sep.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" in rule_ids

    def test_enum_values_with_spaced_separator_not_flagged(self):
        # spec-disc-enum-spaced-sep.md: enum DISC with spaced separator → no false positive
        _, data = _run(FIXTURES / "specs" / "spec-disc-enum-spaced-sep.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" not in rule_ids
# ---------------------------------------------------------------------------
# F2 guard parity: --plan-dir at a file and --spec at a directory both exit 2.
# ---------------------------------------------------------------------------

def _run_plan(plan_dir: Path) -> tuple[int, dict]:
    """Run spec validator with --plan-dir."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--plan-dir", str(plan_dir),
         "--project-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


# ---------------------------------------------------------------------------
# 4-file layout: business-context.md with forbidden token BR-001 → CRITICAL
# ---------------------------------------------------------------------------

class TestBusinessContextForbiddenToken:
    def test_exit_code_one(self):
        code, _ = _run_plan(FIXTURES / "plan-forbidden-bc")
        assert code == 1

    def test_bc_forbidden_token_rule_id_present(self):
        _, data = _run_plan(FIXTURES / "plan-forbidden-bc")
        assert "bc.forbidden_token" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run_plan(FIXTURES / "plan-forbidden-bc")
        matching = [i for i in _issues(data) if i["rule_id"] == "bc.forbidden_token"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_br_token(self):
        _, data = _run_plan(FIXTURES / "plan-forbidden-bc")
        matching = [i for i in _issues(data) if i["rule_id"] == "bc.forbidden_token"]
        assert any("BR-001" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# 4-file layout: --spec pointing at a feature dir runs all 4 checks
# ---------------------------------------------------------------------------

class TestSpecAsFeatureDir:
    def test_feature_dir_runs_all_checks(self):
        feature_dir = FIXTURES / "plan-forbidden-bc" / "artifacts" / "features" / "F001_Auth"
        code, data = _run(feature_dir)
        # bc.forbidden_token should be present (BR-001 in business-context.md)
        assert "bc.forbidden_token" in _critical_rule_ids(data)


class TestInputGuards:
    def test_plan_dir_is_file_exits_two(self, tmp_path):
        bogus = tmp_path / "not-a-dir.txt"
        bogus.write_text("x")
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--plan-dir", str(bogus),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a directory" in result.stderr.lower()

    def test_spec_is_directory_exits_two(self, tmp_path):
        # A dir whose plan_dir (parent.parent) lies outside project_root triggers exit 2.
        # Note: --spec <dir> is valid for 4-file feature dirs; the guard here is assert_under.
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--spec", str(tmp_path),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
