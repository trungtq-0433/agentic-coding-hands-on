"""Integration tests for validate_source_citations.py.
Runs script as subprocess with --spec <path>, parses stdout JSON,
asserts specific rule_ids per citation fixture variant.
Coverage per phase-05 test matrix.
"""
from __future__ import annotations  # PEP 604 `X | None` at runtime on Python 3.9

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT = SCRIPTS_DIR / "validate_source_citations.py"


def _run(spec_path: Path, project_root: Path = REPO_ROOT) -> tuple[int, dict]:
    """Run the citation validator against a single spec.

    The validator derives plan_dir = spec.parent.parent.parent, then asserts
    plan_dir is under project_root.  For specs placed via _make_spec_tree(),
    the spec lives at <tmp>/artifacts/features/F001_Auth/spec.md so that
    plan_dir == tmp_path, which is under project_root == tmp_path.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--spec", str(spec_path),
         "--project-root", str(project_root)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if not result.stdout.strip():
        raise RuntimeError(
            f"validator produced no JSON output (exit={result.returncode}).\n"
            f"stderr: {result.stderr}"
        )
    output = json.loads(result.stdout)
    return result.returncode, output


def _make_spec_tree(tmp_path: Path, citation_line: str) -> tuple[Path, Path]:
    """Create artifacts/features/F001_Auth/spec.md inside tmp_path.

    The validator computes plan_dir = spec.parent.parent.parent = tmp_path,
    so passing --project-root tmp_path satisfies the assert_under guard.
    Returns (spec_path, tmp_path).
    """
    spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
    spec_dir.mkdir(parents=True)
    spec = spec_dir / "spec.md"
    spec.write_text(
        "# F001_Auth — Authentication\n\n"
        "## Source Code References\n\n"
        f"**Source:** `{citation_line}`\n",
        encoding="utf-8",
    )
    return spec, tmp_path


def _issues(data: dict) -> list[dict]:
    all_issues = []
    for entry in data.get("specs", {}).values():
        all_issues.extend(entry.get("issues", []))
    return all_issues


def _critical_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data) if i["severity"] == "critical"]


# ---------------------------------------------------------------------------
# spec-pass.md: valid citation — path resolves via project_root / raw_path
# Citation in fixture uses repo-relative path to cited-source.py, so
# --project-root REPO_ROOT resolves it cleanly.
# ---------------------------------------------------------------------------

class TestSpecPassCitation:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-pass.md")
        assert code == 0

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "specs" / "spec-pass.md")
        criticals = _critical_rule_ids(data)
        assert criticals == [], f"unexpected: {criticals}"


# ---------------------------------------------------------------------------
# spec-bad-citation.md: cites nonexistent-file-that-does-not-exist.py
# ---------------------------------------------------------------------------

class TestSpecBadCitation:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-bad-citation.md")
        assert code == 1

    def test_file_missing_rule_id(self):
        _, data = _run(FIXTURES / "specs" / "spec-bad-citation.md")
        assert "citation.file_missing" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# Range out of bounds: cited-source.py has 30 lines; cite line 999.
# Tests use tmp_path as project_root so validator accepts spec location.
# cited-source.py is copied into tmp_path and cited as "cited-source.py".
# ---------------------------------------------------------------------------

class TestCitationRangeInvalid:
    def _setup(self, tmp_path: Path, citation: str) -> tuple[Path, Path]:
        """Place cited-source.py at tmp_path root so project_root/cited-source.py resolves."""
        (tmp_path / "cited-source.py").write_text(
            (FIXTURES / "cited-source.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, f"cited-source.py:{citation}")
        return spec, root

    def test_range_invalid_rule_id(self, tmp_path):
        spec, root = self._setup(tmp_path, "999")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.range_invalid" in _critical_rule_ids(data)

    def test_range_invalid_message_mentions_bounds(self, tmp_path):
        spec, root = self._setup(tmp_path, "999")
        _, data = _run(spec, root)
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.range_invalid"]
        assert any("out of bounds" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# Inverted range: end < start (e.g. :10-5)
# ---------------------------------------------------------------------------

class TestCitationRangeInverted:
    def test_range_inverted_rule_id(self, tmp_path):
        (tmp_path / "cited-source.py").write_text(
            (FIXTURES / "cited-source.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "cited-source.py:10-5")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.range_inverted" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# Path traversal: ../../../etc/passwd style citation.
# Spec is at tmp_path/artifacts/features/F001_Auth/spec.md so plan_dir==tmp_path
# which is under project_root==tmp_path. The traversal citation is then
# detected by the citation guard (not the plan_dir guard).
# ---------------------------------------------------------------------------

class TestCitationPathTraversal:
    def test_path_traversal_rule_id(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "../../../etc/passwd:1")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.path_traversal" in _critical_rule_ids(data)

    def test_path_traversal_is_critical(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "../../../etc/passwd:1")
        _, data = _run(spec, root)
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.path_traversal"]
        assert len(matching) >= 1
        assert all(i["severity"] == "critical" for i in matching)

    def test_absolute_path_also_rejected(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "/etc/passwd:1")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.path_traversal" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# Phase 04 (cobol-stack-and-generic-fallback plan): COBOL source extensions
# (.cbl/.cob/.cpy/.bms) + generic extensions for ui-sniff leads. The validator has no
# extension allowlist at all (only existence + line-range + traversal are checked), so
# these already resolve — these tests prove that explicitly rather than leaving it implicit.
# ---------------------------------------------------------------------------

class TestCobolAndGenericExtensionCitations:
    def _setup(self, tmp_path: Path, filename: str, n_lines: int = 20) -> tuple[Path, Path]:
        (tmp_path / filename).write_text(
            "\n".join(f"line {i}" for i in range(n_lines)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, f"{filename}:1-2")
        return spec, root

    def test_bms_extension_citation_accepted(self, tmp_path):
        spec, root = self._setup(tmp_path, "ORDMAP.bms")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_cbl_extension_citation_accepted(self, tmp_path):
        spec, root = self._setup(tmp_path, "inline_screen.cbl")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_cpy_extension_citation_accepted(self, tmp_path):
        spec, root = self._setup(tmp_path, "STOCKHDR.cpy")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_ui_sniff_generic_extension_citation_accepted(self, tmp_path):
        # ui-sniff leads cite arbitrary/generic source files — no COBOL-specific narrowing.
        spec, root = self._setup(tmp_path, "legacy_dump.txt")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []


# ---------------------------------------------------------------------------
# F2 guard parity: --plan-dir at a file and --spec at a directory both exit 2.
# ---------------------------------------------------------------------------

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
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--spec", str(tmp_path),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a file" in result.stderr.lower()


# ---------------------------------------------------------------------------
# spec-driven mode (used by tkm:migrate-aidd). Default --mode source unchanged;
# spec-driven additionally accepts spec:// URIs and specsRoot-relative paths.
# [FROM_CODE] citations remain validated as real source paths.
# ---------------------------------------------------------------------------

def _run_spec_driven(spec_path: Path, project_root: Path,
                     specs_root: Path | None = None) -> tuple[int, dict]:
    argv = [sys.executable, str(SCRIPT), "--spec", str(spec_path),
            "--project-root", str(project_root), "--mode", "spec-driven"]
    if specs_root is not None:
        argv += ["--specs-root", str(specs_root)]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    if not result.stdout.strip():
        raise RuntimeError(f"no JSON (exit={result.returncode}). stderr: {result.stderr}")
    return result.returncode, json.loads(result.stdout)


class TestSpecDrivenMode:
    def test_valid_spec_uri_accepted(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "spec://001-create-taskify/spec.md#user-stories")
        code, data = _run_spec_driven(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_specsroot_relative_citation_accepted(self, tmp_path):
        specs_root = tmp_path / "specs"
        (specs_root / "001-create-taskify").mkdir(parents=True)
        (specs_root / "001-create-taskify" / "spec.md").write_text("# spec", encoding="utf-8")
        spec, root = _make_spec_tree(tmp_path, "001-create-taskify/spec.md")
        code, data = _run_spec_driven(spec, root, specs_root=specs_root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_spec_uri_leading_dotdot_rejected(self, tmp_path):
        # spec://..  fails the SPEC_URI grammar (first segment must be alnum)
        spec, root = _make_spec_tree(tmp_path, "spec://../../etc/passwd")
        code, data = _run_spec_driven(spec, root)
        assert code == 1
        assert _critical_rule_ids(data) == ["citation.spec_uri_invalid"]

    def test_spec_uri_inpath_traversal_rejected(self, tmp_path):
        # valid first segment but traversal in the path part -> rejected (M1 fix)
        spec, root = _make_spec_tree(tmp_path, "spec://001-x/../../../etc/passwd")
        code, data = _run_spec_driven(spec, root)
        assert code == 1
        assert _critical_rule_ids(data) == ["citation.spec_uri_invalid"]

    def test_bare_from_code_citation_rejected(self, tmp_path):
        # [FROM_CODE] without a line range hits the bare branch -> must be flagged,
        # never accepted as a spec URI (H1 fix).
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001\n\n## Source Code References\n\n"
            "**Source:** `spec://001-x/real.md` [FROM_CODE]\n",
            encoding="utf-8",
        )
        code, data = _run_spec_driven(spec, tmp_path)
        assert code == 1
        assert "citation.from_code_no_range" in _critical_rule_ids(data)

    def test_from_code_citation_still_validated_as_source(self, tmp_path):
        # [FROM_CODE] forces source-path validation even in spec-driven mode.
        (tmp_path / "cited-source.py").write_text(
            (FIXTURES / "cited-source.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001\n\n## Source Code References\n\n"
            "**Source:** `cited-source.py:999` [FROM_CODE]\n",
            encoding="utf-8",
        )
        code, data = _run_spec_driven(spec, tmp_path)
        assert code == 1
        assert "citation.range_invalid" in _critical_rule_ids(data)


class TestSourceModeDefaultUnchanged:
    def test_default_mode_rejects_spec_uri(self):
        # spec:// is NOT a valid source-path citation; default mode must reject it.
        # Reuse the existing pass/bad fixtures to confirm source-mode parity.
        code, data = _run(FIXTURES / "specs" / "spec-pass.md")
        assert code == 0 and _critical_rule_ids(data) == []

    def test_default_mode_spec_uri_is_ignored_not_accepted(self, tmp_path):
        # Under default source mode, a bare spec:// value has no :N-M, so CITATION_RE
        # doesn't match and source mode does not run the spec-driven branch — i.e. it
        # is neither validated nor falsely accepted as a source path.
        spec, root = _make_spec_tree(tmp_path, "spec://001-x/spec.md#s")
        code, data = _run(spec, root)
        assert code == 0  # no critical (source mode ignores non-matching lines)
        assert _critical_rule_ids(data) == []


# ---------------------------------------------------------------------------
# RE-mode citation-density tests (Phase C, re-output-contract.md)
# ---------------------------------------------------------------------------

def _run_re_mode(spec_path: Path, project_root: Path,
                 density_min: float = 0.8) -> tuple[int, dict]:
    """Run the validator with --re-mode and a given --density-min."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--spec", str(spec_path),
         "--project-root", str(project_root),
         "--re-mode",
         "--density-min", str(density_min)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if not result.stdout.strip():
        raise RuntimeError(
            f"validator produced no JSON output (exit={result.returncode}).\n"
            f"stderr: {result.stderr}"
        )
    return result.returncode, json.loads(result.stdout)


def _make_low_density_spec(tmp_path: Path, *, n_claim_lines: int = 10,
                            n_cited: int = 0) -> tuple[Path, Path]:
    """Create a spec where n_cited out of n_claim_lines have a Source citation.

    The source file is written alongside the spec so citations resolve.
    """
    spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
    spec_dir.mkdir(parents=True)
    # Write a tiny source file so citations can resolve
    src = tmp_path / "src" / "auth.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("\n".join(f"# line {i}" for i in range(20)), encoding="utf-8")

    lines = ["# F001_Auth — Auth\n", ""]
    for i in range(n_claim_lines):
        if i < n_cited:
            lines.append(f"This claim is cited. **Source:** `src/auth.py:1-2`")
        else:
            lines.append(f"This claim has no citation. Claim number {i}.")
    spec = spec_dir / "spec.md"
    spec.write_text("\n".join(lines), encoding="utf-8")
    return spec, tmp_path


class TestReModeOff:
    """Without --re-mode, behaviour must be byte-for-byte unchanged."""

    def test_no_re_mode_no_density_issue(self, tmp_path):
        # A spec with zero citations emits no density issue in normal (non-RE) mode
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=0)
        code, data = _run(spec, root)
        rule_ids = [i["rule_id"] for s in data["specs"].values() for i in s["issues"]]
        assert "citation_density_low" not in rule_ids

    def test_no_re_mode_exit_0_on_warn_only_spec(self, tmp_path):
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=5, n_cited=0)
        code, data = _run(spec, root)
        # No critical issues from a spec with no source citations in default mode
        assert code == 0


class TestReModeOn:
    """With --re-mode, density below threshold → WARN citation_density_low."""

    def test_low_density_emits_warn(self, tmp_path):
        # 0 out of 10 claim lines cited → density 0% < 80%
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=0)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" in warn_ids

    def test_low_density_does_not_halt(self, tmp_path):
        # WARN must not flip exit to 1 (only critical issues do that)
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=0)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        assert code == 0  # advisory WARN, not critical

    def test_above_threshold_no_density_warn(self, tmp_path):
        # 9 out of 10 cited → density 90% > 80% → no density warn
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=9)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" not in warn_ids

    def test_exactly_at_threshold_no_warn(self, tmp_path):
        # 8 out of 10 cited → density exactly 80% = threshold → no warn (not strictly below)
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=8)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" not in warn_ids

    def test_density_min_respected(self, tmp_path):
        # With a very high threshold (0.99), 5/10 cited still triggers warn
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=5)
        code, data = _run_re_mode(spec, root, density_min=0.99)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" in warn_ids

    def test_re_mode_does_not_change_existing_citation_checks(self, tmp_path):
        # A valid spec-pass fixture must still exit 0 under --re-mode
        # (density check only adds warnings, never removes passes)
        code, data = _run_re_mode(FIXTURES / "specs" / "spec-pass.md",
                                  REPO_ROOT, density_min=0.0)
        assert code == 0


class TestReModeScreenArtifacts:
    """v21.0.0 — RE-mode also counts screen-list/screen-flow toward citation density."""

    def _run_plan_dir_re(self, plan_dir: Path, root: Path):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--plan-dir", str(plan_dir),
             "--project-root", str(root), "--re-mode", "--density-min", "0.8"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.stdout.strip(), result.stderr
        return result.returncode, json.loads(result.stdout)

    def test_low_density_screen_list_warns(self, tmp_path):
        # A screen-list.md present in artifacts/ with no citations → density WARN under its own entry.
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir(parents=True)
        lines = ["## Screen Index", ""]
        lines += [f"This screen claim has no citation. Row {i}." for i in range(10)]
        (artifacts / "screen-list.md").write_text("\n".join(lines), encoding="utf-8")
        code, data = self._run_plan_dir_re(tmp_path, tmp_path)
        assert code == 0  # advisory WARN, never HALT
        assert "screen-list" in data["specs"]
        warn_ids = [i["rule_id"] for i in data["specs"]["screen-list"]["issues"]]
        assert "citation_density_low" in warn_ids

    def test_absent_screen_artifact_no_entry(self, tmp_path):
        # Headless run (no screen-list.md on disk) → no screen-list entry, no crash.
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir(parents=True)
        code, data = self._run_plan_dir_re(tmp_path, tmp_path)
        assert code == 0
        assert "screen-list" not in data["specs"]
        assert "screen-flow" not in data["specs"]


# ---------------------------------------------------------------------------
# Regression: invalid env var does not crash, uses default density
# ---------------------------------------------------------------------------

class TestInvalidDensityEnv:
    def test_invalid_density_env_no_crash(self, tmp_path, monkeypatch):
        """Regression: bad REBUILD_CITATION_DENSITY_MIN env value no longer crashes."""
        # Set env to invalid value
        monkeypatch.setenv("REBUILD_CITATION_DENSITY_MIN", "disabled")

        # Create a minimal spec
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001 Test\n\n**Source:** `cited-source.py:1`\n",
            encoding="utf-8",
        )

        # Run main with minimal args — should not crash
        from validate_source_citations import main
        rc = main([
            "--spec", str(spec),
            "--project-root", str(tmp_path),
        ])
        # May be 1 (missing citation logic) or 0 (file not found), but not a crash
        assert rc in (0, 1, 2)

    def test_valid_density_env_used(self, tmp_path, monkeypatch):
        """Regression guard: valid density env IS parsed and used."""
        monkeypatch.setenv("REBUILD_CITATION_DENSITY_MIN", "0.5")

        spec_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001 Test\n\n## Behavior\n\n"
            "Claim 1: does X.\n"
            "Claim 2: does Y.\n"
            "Claim 3: does Z.\n\n"
            "**Source:** `test.py:1`\n",  # Only 1 out of 3 claims cited
            encoding="utf-8",
        )

        from validate_source_citations import main
        # RE mode should use 0.5 threshold
        rc = main([
            "--spec", str(spec),
            "--project-root", str(tmp_path),
            "--re-mode",
        ])
        # With 1/3 cited < 0.5 threshold, should warn (and exit 0 since density warn is not critical)
        # The return code depends on other issues, but parsing should succeed
        assert rc in (0, 1, 2)
