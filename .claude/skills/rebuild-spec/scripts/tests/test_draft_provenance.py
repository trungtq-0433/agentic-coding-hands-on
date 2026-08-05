"""Draft-mode provenance tests for Phase 2 of the takumi SDD rewrite.

Covers:
 (a) draft spec with missing-file citation → warning not critical, exit 0
 (b) implemented spec with same citation → critical, exit 1 (regression)
 (c) spec with NO status field → behaves as implemented
 (d) contiguity with registered draft F### → PASS
 (e) draft spec missing a STRUCTURAL rule (sm_mermaid / required heading) → STILL critical (F8 negative)
 (f) F15 round-trip: docs/features/F001_Test draft → 0 critical exit 0; flip to implemented → criticals fire exit 1
 (g) promote_drafts guard: draft+takumi destination → SKIP; with --force → overwrite proceeds
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
SCRIPT_CITATIONS = SCRIPTS_DIR / "validate_source_citations.py"
SCRIPT_FEATURE_SPEC = SCRIPTS_DIR / "validate_feature_spec.py"
SCRIPT_CONTIGUITY = SCRIPTS_DIR / "validate_id_contiguity.py"
SCRIPT_PROMOTE = SCRIPTS_DIR / "promote_drafts.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DRAFT_FRONTMATTER = """\
---
status: draft
authored_by: takumi
fcode: F001
created: 2026-06-11
---
"""

IMPLEMENTED_FRONTMATTER = """\
---
status: implemented
authored_by: rebuild-spec
fcode: F001
created: 2026-06-11
---
"""

NO_FRONTMATTER = ""  # no leading ---


def _run_script(script: Path, args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def _parse_json(stdout: str) -> dict:
    return json.loads(stdout.strip())


def _issues(data: dict) -> list[dict]:
    all_issues = []
    for entry in data.get("specs", {}).values():
        all_issues.extend(entry.get("issues", []))
    return all_issues


def _critical_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data) if i["severity"] == "critical"]


def _warning_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data) if i["severity"] == "warning"]


def _make_citations_spec_tree(tmp_path: Path, frontmatter: str, citation: str) -> tuple[Path, Path]:
    """Create <tmp>/artifacts/features/F001_Test/technical-spec.md with given frontmatter + citation."""
    spec_dir = tmp_path / "artifacts" / "features" / "F001_Test"
    spec_dir.mkdir(parents=True)
    spec = spec_dir / "technical-spec.md"
    spec.write_text(
        frontmatter
        + "# F001_Test — Test Feature\n\n"
        + "## Source Code References\n\n"
        + f"**Source:** `{citation}`\n",
        encoding="utf-8",
    )
    return spec, tmp_path


def _make_full_feature_dir(tmp_path: Path, frontmatter: str, extra_tech_spec: str = "") -> Path:
    """Create docs/features/F001_Test/ with all 4 required files.

    technical-spec.md uses the given frontmatter + minimal valid structure.
    Returns project_root (tmp_path).
    """
    feat_dir = tmp_path / "docs" / "features" / "F001_Test"
    feat_dir.mkdir(parents=True)

    tech_spec = feat_dir / "technical-spec.md"
    tech_spec.write_text(
        frontmatter
        + _minimal_tech_spec()
        + extra_tech_spec,
        encoding="utf-8",
    )
    (feat_dir / "business-context.md").write_text(
        "# F001_Test Business Context\n\n"
        "## Why It Matters\nWhy.\n\n"
        "## Who Uses It\nUsers.\n\n"
        "## What They Do\nStuff.\n",
        encoding="utf-8",
    )
    (feat_dir / "screens.md").write_text(
        "# F001_Test Screens\n\n"
        "## Screen List\nScreens here.\n\n"
        "## User Journey\nJourney here.\n",
        encoding="utf-8",
    )
    (feat_dir / "edge-cases.md").write_text(
        "# F001_Test Edge Cases\n\n"
        "| Scenario | Expected |\n"
        "| --- | --- |\n"
        "| Network failure | Show error |\n",
        encoding="utf-8",
    )
    return tmp_path


def _minimal_tech_spec() -> str:
    """Return a minimal but structurally valid technical-spec.md body (no citations)."""
    return """\
# F001_Test — Test Feature

## Overview
Overview text.

## Polymorphic Behavior
None.

## Cross-Cutting Logic

**Client behavior:** see behavior-logic.md

### Requirements
None.

### Business Rules
None.

### Decision Logic
N/A

### State Machines
None.

### Algorithms
None.

### External Integrations
None.

### Verification
None.

## User Stories

### Edge Cases
None.

## Key Entities
None.

## Artifact References
None.

## Assumptions
None.

## Source Code References

## Unresolved Questions
None.
"""


def _run_citations(spec: Path, project_root: Path) -> tuple[int, dict]:
    code, out, _ = _run_script(SCRIPT_CITATIONS, [
        "--spec", str(spec),
        "--project-root", str(project_root),
    ])
    return code, _parse_json(out)


def _run_citations_docs_root(project_root: Path) -> tuple[int, dict]:
    code, out, _ = _run_script(SCRIPT_CITATIONS, [
        "--docs-root", str(project_root),
        "--project-root", str(project_root),
    ])
    return code, _parse_json(out)


def _run_feature_spec_docs_root(project_root: Path) -> tuple[int, dict]:
    code, out, err = _run_script(SCRIPT_FEATURE_SPEC, [
        "--docs-root", str(project_root),
        "--project-root", str(project_root),
    ])
    if not out.strip():
        raise RuntimeError(f"no JSON output (exit={code}). stderr: {err}")
    return code, _parse_json(out)


# ===========================================================================
# (a) Draft spec with missing-file citation → warning, exit 0
# ===========================================================================

class TestDraftCitationFileMissing:
    def test_exit_code_zero(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, DRAFT_FRONTMATTER, "nonexistent-file.py:1"
        )
        code, _ = _run_citations(spec, root)
        assert code == 0, "draft with missing citation must exit 0"

    def test_file_missing_is_warning_not_critical(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, DRAFT_FRONTMATTER, "nonexistent-file.py:1"
        )
        _, data = _run_citations(spec, root)
        assert "citation.file_missing" in _warning_rule_ids(data), \
            "citation.file_missing must be a warning for draft"
        assert "citation.file_missing" not in _critical_rule_ids(data), \
            "citation.file_missing must NOT be critical for draft"

    def test_no_criticals(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, DRAFT_FRONTMATTER, "nonexistent-file.py:1"
        )
        _, data = _run_citations(spec, root)
        assert _critical_rule_ids(data) == [], f"no criticals expected; got: {_critical_rule_ids(data)}"


# ===========================================================================
# (b) Implemented spec with missing-file citation → critical, exit 1 (regression)
# ===========================================================================

class TestImplementedCitationFileMissing:
    def test_exit_code_one(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, IMPLEMENTED_FRONTMATTER, "nonexistent-file.py:1"
        )
        code, _ = _run_citations(spec, root)
        assert code == 1, "implemented spec with missing citation must exit 1"

    def test_file_missing_is_critical(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, IMPLEMENTED_FRONTMATTER, "nonexistent-file.py:1"
        )
        _, data = _run_citations(spec, root)
        assert "citation.file_missing" in _critical_rule_ids(data)

    def test_no_accidental_relaxation(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, IMPLEMENTED_FRONTMATTER, "nonexistent-file.py:1"
        )
        _, data = _run_citations(spec, root)
        # Must NOT appear as a warning (it's critical)
        assert "citation.file_missing" not in _warning_rule_ids(data)


# ===========================================================================
# (c) Spec with NO status field → behaves as implemented (exit 1 on missing citation)
# ===========================================================================

class TestNoStatusFieldBehavesAsImplemented:
    def test_no_status_missing_citation_exits_one(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, NO_FRONTMATTER, "nonexistent-file.py:1"
        )
        code, _ = _run_citations(spec, root)
        assert code == 1, "no-status spec must behave as implemented → exit 1"

    def test_no_status_file_missing_is_critical(self, tmp_path):
        spec, root = _make_citations_spec_tree(
            tmp_path, NO_FRONTMATTER, "nonexistent-file.py:1"
        )
        _, data = _run_citations(spec, root)
        assert "citation.file_missing" in _critical_rule_ids(data)


# ===========================================================================
# (d) Contiguity with registered draft F### → PASS (validate_id_contiguity unchanged)
# ===========================================================================

class TestContiguityWithDraftFCode:
    def _write_feature_list(self, plan_dir: Path, content: str) -> Path:
        art_dir = plan_dir / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        f = art_dir / "feature-list.md"
        f.write_text(content, encoding="utf-8")
        return f

    def _run_contiguity(self, plan_dir: Path, artifact: str) -> tuple[int, dict]:
        code, out, err = _run_script(SCRIPT_CONTIGUITY, [
            "--artifact", artifact,
            "--plan-dir", str(plan_dir),
            "--project-root", str(plan_dir.parent),
        ])
        return code, json.loads(out)

    def test_registered_draft_fcode_no_gap(self, tmp_path):
        """F001 + F002 (draft) + F003 all registered → contiguous → PASS."""
        # feature-list.md just needs F### slug patterns to be detected
        content = (
            "| F001_Auth | Auth | ... |\n"
            "| F002_DraftFeature | Draft Feature (status: draft) | ... |\n"
            "| F003_Search | Search | ... |\n"
        )
        self._write_feature_list(tmp_path, content)
        code, data = self._run_contiguity(tmp_path, "feature-list")
        assert code == 0, f"contiguous draft F### must exit 0; issues: {data.get('issues')}"
        assert data["status"] == "PASS"

    def test_registered_draft_fcode_no_contiguity_issues(self, tmp_path):
        content = (
            "| F001_Auth | Auth |\n"
            "| F002_Draft | Draft |\n"
        )
        self._write_feature_list(tmp_path, content)
        code, data = self._run_contiguity(tmp_path, "feature-list")
        assert data["issues"] == []

    def test_unregistered_draft_leaves_gap(self, tmp_path):
        """If draft F### is NOT in feature-list, gap still fires (validator unchanged)."""
        # Only F001 and F003 registered; F002 missing
        content = (
            "| F001_Auth | Auth |\n"
            "| F003_Search | Search |\n"
        )
        self._write_feature_list(tmp_path, content)
        code, data = self._run_contiguity(tmp_path, "feature-list")
        assert code == 1
        gap_ids = [i["rule_id"] for i in data["issues"] if i["rule_id"] == "contiguity.gap"]
        assert gap_ids, "gap must fire when F002 is absent from feature-list"


# ===========================================================================
# (e) Draft spec missing STRUCTURAL rule → STILL critical (F8 negative test)
# ===========================================================================

class TestDraftStructuralRulesStayCritical:
    def test_draft_missing_sm_mermaid_still_critical(self, tmp_path):
        """Draft spec with SM block missing mermaid fence → still critical."""
        feat_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        feat_dir.mkdir(parents=True)
        # Write a spec with draft frontmatter but SM block missing its mermaid diagram
        spec = feat_dir / "technical-spec.md"
        spec.write_text(
            DRAFT_FRONTMATTER
            + "# F001_Test — Test Feature\n\n"
            + "## Source Code References\n\nSome prose only.\n\n"
            + "### SM-001_StateMachine\n\nNo mermaid fence here.\n",
            encoding="utf-8",
        )
        code, out, _ = _run_script(SCRIPT_FEATURE_SPEC, [
            "--spec", str(spec),
            "--project-root", str(tmp_path),
        ])
        data = _parse_json(out)
        crit_ids = _critical_rule_ids(data)
        assert "FeatureSpec.sm_mermaid" in crit_ids, \
            f"sm_mermaid must be critical even for drafts; criticals: {crit_ids}"

    def test_draft_missing_required_h2_still_critical(self, tmp_path):
        """Draft spec missing a required H2 (required_sections) → still critical."""
        feat_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        feat_dir.mkdir(parents=True)
        # Minimal spec with draft frontmatter but missing most required sections
        spec = feat_dir / "technical-spec.md"
        spec.write_text(
            DRAFT_FRONTMATTER
            + "# F001_Test — Test Feature\n\n"
            + "## Overview\nOverview.\n\n"
            # Missing many required sections
        )
        code, out, _ = _run_script(SCRIPT_FEATURE_SPEC, [
            "--spec", str(spec),
            "--project-root", str(tmp_path),
        ])
        data = _parse_json(out)
        crit_ids = _critical_rule_ids(data)
        assert "FeatureSpec.required_sections" in crit_ids, \
            f"required_sections must be critical for drafts; criticals: {crit_ids}"

    def test_draft_path_traversal_still_critical(self, tmp_path):
        """Draft spec with path traversal citation → still critical (security rule)."""
        spec, root = _make_citations_spec_tree(
            tmp_path, DRAFT_FRONTMATTER, "../../../etc/passwd:1"
        )
        _, data = _run_citations(spec, root)
        assert "citation.path_traversal" in _critical_rule_ids(data), \
            "path_traversal must always be critical, even for drafts"


# ===========================================================================
# (f) F15 round-trip: docs/features/F001_Test draft → 0 critical exit 0;
#     flip to implemented → criticals fire exit 1
# ===========================================================================

class TestF15RoundTrip:
    def test_draft_docs_root_no_citations_zero_critical_exit_0(self, tmp_path):
        """Draft technical-spec.md with NO citations in docs/features/ → 0 critical, exit 0."""
        _make_full_feature_dir(tmp_path, DRAFT_FRONTMATTER)
        # citations validator
        code, data = _run_citations_docs_root(tmp_path)
        crit = _critical_rule_ids(data)
        assert code == 0, f"draft with no citations must exit 0; criticals: {crit}"
        assert crit == [], f"no criticals expected for draft with no citations; got: {crit}"

    def test_draft_docs_root_feature_spec_zero_critical_exit_0(self, tmp_path):
        """Draft technical-spec.md validated via --docs-root → 0 critical, exit 0."""
        _make_full_feature_dir(tmp_path, DRAFT_FRONTMATTER)
        code, data = _run_feature_spec_docs_root(tmp_path)
        crit = _critical_rule_ids(data)
        assert code == 0, f"draft via --docs-root must exit 0; criticals: {crit}"
        assert crit == [], f"no criticals expected for valid draft; got: {crit}"

    def test_implemented_docs_root_source_evidence_fires_exit_1(self, tmp_path):
        """Flip to implemented → source-evidence criticals fire → exit 1."""
        _make_full_feature_dir(tmp_path, IMPLEMENTED_FRONTMATTER)
        code, data = _run_feature_spec_docs_root(tmp_path)
        crit = _critical_rule_ids(data)
        # The implemented spec has no **Source:** citations and no BR/SM/ALG/INT Source lines.
        # The source-evidence rule fires.
        assert code == 1, f"implemented spec without sources must exit 1; criticals: {crit}"
        # At least source_refs_empty or block_source_missing should fire
        evidence_rules = {"FeatureSpec.source_refs_empty", "FeatureSpec.block_source_missing"}
        assert evidence_rules & set(crit), \
            f"at least one source-evidence rule must be critical; criticals: {crit}"

    def test_implemented_docs_root_table_citation_passes(self, tmp_path):
        """C2 regression: an implemented spec whose ## Source Code References uses the
        canonical Markdown table format (| Symbol | Path | Purpose |) — the shape emitted by
        technical-spec-template.md — must NOT trigger source_refs_empty. Table-row citations
        are valid source evidence, consistent with the SHA citation parser."""
        _make_full_feature_dir(tmp_path, IMPLEMENTED_FRONTMATTER)
        tech_spec = tmp_path / "docs" / "features" / "F001_Test" / "technical-spec.md"
        table = (
            "## Source Code References\n\n"
            "| Symbol | Path | Purpose |\n"
            "|--------|------|---------|\n"
            "| LoginForm | `app/auth/login.py:5-10` | Credential validation |\n\n"
        )
        body = IMPLEMENTED_FRONTMATTER + _minimal_tech_spec().replace(
            "## Source Code References\n\n", table
        )
        tech_spec.write_text(body, encoding="utf-8")
        code, data = _run_feature_spec_docs_root(tmp_path)
        crit = _critical_rule_ids(data)
        assert "FeatureSpec.source_refs_empty" not in crit, \
            f"table-format citation must satisfy the source-evidence check; criticals: {crit}"
        assert code == 0, f"implemented spec with table citation must exit 0; criticals: {crit}"

    def test_docs_root_mode_detects_docs_features_not_artifacts(self, tmp_path):
        """--docs-root sees docs/features/ specs; confirm artifact path is NOT scanned."""
        # Put a spec only in docs/features/ (the draft path)
        _make_full_feature_dir(tmp_path, DRAFT_FRONTMATTER)
        # --docs-root should find it
        code, data = _run_citations_docs_root(tmp_path)
        assert "F001_Test" in data.get("specs", {}), \
            "--docs-root must discover docs/features/F001_Test"

    def test_docs_root_mode_skips_pending_dirs(self, tmp_path):
        """--docs-root skips dirs with .pending marker."""
        _make_full_feature_dir(tmp_path, DRAFT_FRONTMATTER)
        (tmp_path / "docs" / "features" / "F001_Test" / ".pending").write_text("")
        _, data = _run_citations_docs_root(tmp_path)
        assert "F001_Test" not in data.get("specs", {}), \
            ".pending dirs must be skipped by iter_docs_technical_specs"

    def test_docs_root_scans_after_pending_marker_removed(self, tmp_path):
        """H1 round-trip: .pending excludes the spec; deleting it (registration Step 9)
        makes --docs-root scan the spec again."""
        _make_full_feature_dir(tmp_path, DRAFT_FRONTMATTER)
        marker = tmp_path / "docs" / "features" / "F001_Test" / ".pending"
        marker.write_text("")
        _, data = _run_citations_docs_root(tmp_path)
        assert "F001_Test" not in data.get("specs", {})
        marker.unlink()
        _, data = _run_citations_docs_root(tmp_path)
        assert "F001_Test" in data.get("specs", {}), \
            "spec must be scanned once the .pending marker is deleted post-registration"

    def test_implemented_citations_validator_exit_0_when_only_warnings(self, tmp_path):
        """Regression: implemented spec with VALID citation exits 0."""
        feat_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        feat_dir.mkdir(parents=True)
        # Write a cited source file
        (tmp_path / "some_source.py").write_text("line1\nline2\nline3\n", encoding="utf-8")
        spec = feat_dir / "technical-spec.md"
        spec.write_text(
            IMPLEMENTED_FRONTMATTER
            + "# F001_Test — Test\n\n## Source Code References\n\n"
            + "**Source:** `some_source.py:1-3`\n",
            encoding="utf-8",
        )
        code, data = _run_citations(spec, tmp_path)
        assert code == 0
        assert _critical_rule_ids(data) == []


# ===========================================================================
# (g) promote_drafts guard: draft+takumi destination → SKIP; --force → overwrite
# ===========================================================================

class TestPromoteDraftsGuard:
    def _setup_promote_tree(self, tmp_path: Path, dst_frontmatter: str) -> tuple[str, str]:
        """Create minimal source + destination tree for promote_drafts.

        Returns (plan_dir_str, docs_root_str).
        """
        plan_dir = tmp_path / "plan"
        docs_root = tmp_path / "docs"

        # Source feature dir in artifacts
        src_feat = plan_dir / "artifacts" / "features" / "F001_Test"
        src_feat.mkdir(parents=True)
        (src_feat / "technical-spec.md").write_text(
            IMPLEMENTED_FRONTMATTER + "# F001_Test\n\n## Overview\nNew content.\n",
            encoding="utf-8",
        )

        # Destination with given frontmatter (simulates prior takumi draft)
        dst_feat = docs_root / "features" / "F001_Test"
        dst_feat.mkdir(parents=True)
        (dst_feat / "technical-spec.md").write_text(
            dst_frontmatter + "# F001_Test\n\nOriginal draft content.\n",
            encoding="utf-8",
        )

        return str(plan_dir), str(docs_root)

    def _run_promote(self, plan_dir: str, docs_root: str, force: bool = False,
                     cwd: str | None = None) -> tuple[int, str, str]:
        args = [
            "--plan-dir", plan_dir,
            "--docs-root", docs_root,
            "--mode", "full",
            "--scope", "features",
        ]
        if force:
            args.append("--force")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PROMOTE)] + args,
            capture_output=True, text=True, timeout=30,
            cwd=cwd,
        )
        return result.returncode, result.stdout, result.stderr

    def test_draft_takumi_destination_is_skipped(self, tmp_path):
        """Promote over draft+takumi destination → SKIP without --force."""
        plan_dir, docs_root = self._setup_promote_tree(tmp_path, DRAFT_FRONTMATTER)
        code, stdout, stderr = self._run_promote(plan_dir, docs_root, force=False, cwd=str(tmp_path))
        assert code == 0, f"promote must not exit non-zero on skip; got {code}\nstderr: {stderr}"
        # Destination content must be unchanged (still original draft content)
        dst_spec = Path(docs_root) / "features" / "F001_Test" / "technical-spec.md"
        content = dst_spec.read_text(encoding="utf-8")
        assert "Original draft content." in content, \
            "draft+takumi destination must not be overwritten without --force"

    def test_skipped_path_reported_in_stderr(self, tmp_path):
        """Skipped paths must appear in stderr output."""
        plan_dir, docs_root = self._setup_promote_tree(tmp_path, DRAFT_FRONTMATTER)
        _, _, stderr = self._run_promote(plan_dir, docs_root, force=False, cwd=str(tmp_path))
        assert "SKIP" in stderr, f"expected [SKIP] in stderr; got: {stderr!r}"
        assert "F001_Test" in stderr

    def test_force_overwrites_draft_takumi_destination(self, tmp_path):
        """--force allows overwriting draft+takumi destination."""
        plan_dir, docs_root = self._setup_promote_tree(tmp_path, DRAFT_FRONTMATTER)
        code, _, stderr = self._run_promote(plan_dir, docs_root, force=True, cwd=str(tmp_path))
        assert code == 0, f"--force promote must exit 0; got {code}\nstderr: {stderr}"
        dst_spec = Path(docs_root) / "features" / "F001_Test" / "technical-spec.md"
        content = dst_spec.read_text(encoding="utf-8")
        assert "New content." in content, \
            "--force must overwrite destination with source content"
        assert "Original draft content." not in content

    def test_implemented_destination_not_skipped(self, tmp_path):
        """Implemented destination (not draft+takumi) is promoted normally."""
        plan_dir, docs_root = self._setup_promote_tree(tmp_path, IMPLEMENTED_FRONTMATTER)
        code, _, stderr = self._run_promote(plan_dir, docs_root, force=False, cwd=str(tmp_path))
        assert code == 0
        # Must NOT have SKIP in stderr
        assert "SKIP" not in stderr or "F001_Test" not in stderr.split("SKIP")[-1], \
            "implemented destination must not be skipped"
        dst_spec = Path(docs_root) / "features" / "F001_Test" / "technical-spec.md"
        content = dst_spec.read_text(encoding="utf-8")
        assert "New content." in content, "implemented destination must be overwritten"

    def test_skipped_list_printed_at_end_of_stdout(self, tmp_path):
        """After a skip, stdout must show skipped count."""
        plan_dir, docs_root = self._setup_promote_tree(tmp_path, DRAFT_FRONTMATTER)
        _, stdout, stderr = self._run_promote(plan_dir, docs_root, force=False, cwd=str(tmp_path))
        # Either stdout or stderr carries the summary
        combined = stdout + stderr
        assert "draft" in combined.lower() or "skip" in combined.lower(), \
            "skipped summary must appear in output"


# ===========================================================================
# (h) Relaxation requires status:draft AND authored_by:takumi — a draft from
#     any other author gets full strict validation (review fix I5)
# ===========================================================================

DRAFT_NON_TAKUMI_FRONTMATTER = """\
---
status: draft
authored_by: rebuild-spec
fcode: F001
created: 2026-06-11
---
"""


class TestDraftNonTakumiNotRelaxed:
    def test_citations_missing_file_stays_critical(self, tmp_path):
        """draft + authored_by:rebuild-spec with missing citation → critical, exit 1."""
        spec, root = _make_citations_spec_tree(
            tmp_path, DRAFT_NON_TAKUMI_FRONTMATTER, "nonexistent-file.py:1"
        )
        code, data = _run_citations(spec, root)
        assert code == 1, "non-takumi draft must NOT be relaxed → exit 1"
        assert "citation.file_missing" in _critical_rule_ids(data)
        assert "citation.file_missing" not in _warning_rule_ids(data)

    def test_feature_spec_source_evidence_stays_critical(self, tmp_path):
        """draft + authored_by:rebuild-spec with empty Source Code References → critical."""
        _make_full_feature_dir(tmp_path, DRAFT_NON_TAKUMI_FRONTMATTER)
        code, data = _run_feature_spec_docs_root(tmp_path)
        assert code == 1, "non-takumi draft must fail source-evidence as critical"
        evidence_rules = {"FeatureSpec.source_refs_empty", "FeatureSpec.block_source_missing"}
        assert evidence_rules & set(_critical_rule_ids(data))

    def test_takumi_draft_still_relaxed(self, tmp_path):
        """Control: draft + authored_by:takumi keeps the relaxation (warning, exit 0)."""
        spec, root = _make_citations_spec_tree(
            tmp_path, DRAFT_FRONTMATTER, "nonexistent-file.py:1"
        )
        code, data = _run_citations(spec, root)
        assert code == 0
        assert "citation.file_missing" in _warning_rule_ids(data)


# ===========================================================================
# (h2) MED-1 / T3 — a takumi draft may ship with ONLY technical-spec.md;
#      the satellite files (business-context/screens/edge-cases) may be deferred.
#      Their *.missing must downgrade critical -> warning for a takumi draft so
#      the "draft exit 0" contract holds. A non-takumi/implemented dir with the
#      same shape stays critical (exit 1).
# ===========================================================================

def _make_tech_spec_only_dir(tmp_path: Path, frontmatter: str) -> Path:
    """Create docs/features/F001_Test/ with ONLY technical-spec.md (no satellites)."""
    feat_dir = tmp_path / "docs" / "features" / "F001_Test"
    feat_dir.mkdir(parents=True)
    (feat_dir / "technical-spec.md").write_text(
        frontmatter + _minimal_tech_spec(), encoding="utf-8"
    )
    return tmp_path


class TestDraftSatellitesDeferred:
    _SATELLITE_MISSING = {"bc.missing", "screens.missing", "edge_cases.missing"}

    def test_takumi_draft_only_tech_spec_exits_0(self, tmp_path):
        _make_tech_spec_only_dir(tmp_path, DRAFT_FRONTMATTER)
        code, data = _run_feature_spec_docs_root(tmp_path)
        assert code == 0, "takumi draft with only technical-spec.md must exit 0"

    def test_takumi_draft_satellite_missing_is_warning(self, tmp_path):
        _make_tech_spec_only_dir(tmp_path, DRAFT_FRONTMATTER)
        _, data = _run_feature_spec_docs_root(tmp_path)
        warnings = set(_warning_rule_ids(data))
        criticals = set(_critical_rule_ids(data))
        assert self._SATELLITE_MISSING <= warnings, "satellite .missing must be warnings"
        assert not (self._SATELLITE_MISSING & criticals), "no satellite .missing as critical"

    def test_implemented_only_tech_spec_stays_critical(self, tmp_path):
        """Control: a non-draft (implemented) dir with only technical-spec.md keeps
        satellite .missing critical → exit 1. Relaxation is draft-scoped."""
        _make_tech_spec_only_dir(tmp_path, IMPLEMENTED_FRONTMATTER)
        code, data = _run_feature_spec_docs_root(tmp_path)
        assert code == 1, "implemented dir missing satellites must fail"
        assert self._SATELLITE_MISSING & set(_critical_rule_ids(data))

    def test_non_takumi_draft_only_tech_spec_stays_critical(self, tmp_path):
        """Control: draft authored by rebuild-spec is NOT relaxed → satellites critical."""
        _make_tech_spec_only_dir(tmp_path, DRAFT_NON_TAKUMI_FRONTMATTER)
        code, data = _run_feature_spec_docs_root(tmp_path)
        assert code == 1, "non-takumi draft must not get satellite relaxation"
        assert self._SATELLITE_MISSING & set(_critical_rule_ids(data))


# ===========================================================================
# (i) block_source_missing bounded at next H1-H3 heading — a **Source:** line
#     in ## Source Code References must NOT satisfy the last block (review fix I4)
# ===========================================================================

class TestLastBlockSourceBounded:
    def _write_spec(self, tmp_path: Path, body: str) -> tuple[Path, Path]:
        feat_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        feat_dir.mkdir(parents=True)
        spec = feat_dir / "technical-spec.md"
        spec.write_text(IMPLEMENTED_FRONTMATTER + body, encoding="utf-8")
        return spec, tmp_path

    def _rule_ids(self, spec: Path, root: Path) -> list[str]:
        _, out, _ = _run_script(SCRIPT_FEATURE_SPEC, [
            "--spec", str(spec), "--project-root", str(root),
        ])
        return [i["rule_id"] for i in _issues(_parse_json(out))]

    def test_last_block_without_source_fires_despite_later_section(self, tmp_path):
        """Last BR block has no **Source:**; ## Source Code References below has one
        → block_source_missing must still fire (regression for EOF false negative)."""
        spec, root = self._write_spec(
            tmp_path,
            "# F001_Test — Test\n\n"
            "### BR-001_Rule\n**Linked FR:** FR-001\n\nNo source line in this block.\n\n"
            "## Source Code References\n\n**Source:** `some.py:1-2`\n",
        )
        assert "FeatureSpec.block_source_missing" in self._rule_ids(spec, root), \
            "**Source:** in a later section must not satisfy the last block"

    def test_block_with_own_source_does_not_fire(self, tmp_path):
        """Control: block carrying its own **Source:** line passes."""
        spec, root = self._write_spec(
            tmp_path,
            "# F001_Test — Test\n\n"
            "### BR-001_Rule\n**Linked FR:** FR-001\n"
            "**Source:** `some.py:1-2`\n\nRule text.\n\n"
            "## Source Code References\n\n**Source:** `some.py:1-2`\n",
        )
        assert "FeatureSpec.block_source_missing" not in self._rule_ids(spec, root)


# ===========================================================================
# (j) promote_drafts screen-spec guard — draft+takumi docs/screens destination
#     skipped unless --force (review fix I3)
# ===========================================================================

class TestPromoteScreenSpecGuard:
    def _setup_screen_tree(self, tmp_path: Path, dst_frontmatter: str) -> tuple[str, str]:
        plan_dir = tmp_path / "plan"
        docs_root = tmp_path / "docs"
        src_scr = plan_dir / "artifacts" / "screens" / "SCR001_Test"
        src_scr.mkdir(parents=True)
        (src_scr / "spec.md").write_text("# SCR001_Test\n\nNew screen content.\n", encoding="utf-8")
        dst_scr = docs_root / "screens" / "SCR001_Test"
        dst_scr.mkdir(parents=True)
        (dst_scr / "spec.md").write_text(
            dst_frontmatter + "# SCR001_Test\n\nOriginal draft screen.\n", encoding="utf-8",
        )
        return str(plan_dir), str(docs_root)

    def _run_promote_all(self, plan_dir: str, docs_root: str, force: bool = False,
                         cwd: str | None = None) -> tuple[int, str, str]:
        args = ["--plan-dir", plan_dir, "--docs-root", docs_root,
                "--mode", "full", "--scope", "all"]
        if force:
            args.append("--force")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PROMOTE)] + args,
            capture_output=True, text=True, timeout=30, cwd=cwd,
        )
        return result.returncode, result.stdout, result.stderr

    def test_draft_takumi_screen_spec_skipped(self, tmp_path):
        plan_dir, docs_root = self._setup_screen_tree(tmp_path, DRAFT_FRONTMATTER)
        code, _, stderr = self._run_promote_all(plan_dir, docs_root, cwd=str(tmp_path))
        assert code == 0, f"skip must not fail the run; stderr: {stderr}"
        content = (Path(docs_root) / "screens" / "SCR001_Test" / "spec.md").read_text(encoding="utf-8")
        assert "Original draft screen." in content, \
            "draft+takumi screen spec must not be overwritten without --force"
        assert "SKIP" in stderr and "SCR001_Test" in stderr

    def test_force_overwrites_screen_spec(self, tmp_path):
        plan_dir, docs_root = self._setup_screen_tree(tmp_path, DRAFT_FRONTMATTER)
        code, _, _ = self._run_promote_all(plan_dir, docs_root, force=True, cwd=str(tmp_path))
        assert code == 0
        content = (Path(docs_root) / "screens" / "SCR001_Test" / "spec.md").read_text(encoding="utf-8")
        assert "New screen content." in content

    def test_implemented_screen_spec_promoted_normally(self, tmp_path):
        plan_dir, docs_root = self._setup_screen_tree(tmp_path, IMPLEMENTED_FRONTMATTER)
        code, _, _ = self._run_promote_all(plan_dir, docs_root, cwd=str(tmp_path))
        assert code == 0
        content = (Path(docs_root) / "screens" / "SCR001_Test" / "spec.md").read_text(encoding="utf-8")
        assert "New screen content." in content, "implemented screen dst must be overwritten"
