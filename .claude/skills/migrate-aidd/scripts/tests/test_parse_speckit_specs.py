"""Subprocess tests for parse_speckit_specs.py."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "parse_speckit_specs.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SPECS_DIR = FIXTURES_DIR / "specs"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


class TestParseSpeckitSpecs:
    def test_exit_zero_with_specs_root(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr

    def test_status_done_in_stdout(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        assert "Status: DONE" in result.stdout

    def test_spec_summary_created(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        assert (plan_dir / "artifacts" / "spec-summary.md").is_file()

    def test_speckit_index_created(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        assert (plan_dir / "artifacts" / "_speckit-index.json").is_file()

    def test_index_has_two_features(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        assert len(index["features"]) == 2

    def test_index_has_detected_stack(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        assert "detectedStack" in index
        assert isinstance(index["detectedStack"], str)
        assert len(index["detectedStack"]) > 0

    def test_index_feature_slugs(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        slugs = {f["slug"] for f in index["features"]}
        assert "create-taskify" in slugs
        assert "add-auth" in slugs

    def test_index_feature_has_artifact_flags(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        feat = next(f for f in index["features"] if f["nnn"] == "001")
        for key in ("has_spec", "has_plan", "has_tasks", "has_data_model", "has_contracts"):
            assert key in feat

    def test_spec_summary_has_detected_language(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)],
            cwd=tmp_path,
        )
        content = (plan_dir / "artifacts" / "spec-summary.md").read_text()
        assert "## Detected Language" in content

    def test_via_detection_json(self, tmp_path):
        """Accept --detection-json path instead of --specs-root."""
        import json as _json
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        det_json = tmp_path / "sdd-detection.json"
        det_json.write_text(_json.dumps({"isSDD": True, "specsRoot": str(SPECS_DIR), "signals": []}))
        result = _run(
            ["--plan-dir", str(plan_dir), "--detection-json", str(det_json)],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert (plan_dir / "artifacts" / "_speckit-index.json").is_file()

    def test_blocked_without_specs_root_or_detection_json(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            ["--plan-dir", str(plan_dir)],
            cwd=tmp_path,
        )
        assert result.returncode == 2
        assert "BLOCKED" in result.stdout

    def test_blocked_on_nonexistent_specs_root(self, tmp_path):
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        result = _run(
            ["--plan-dir", str(plan_dir), "--specs-root", str(tmp_path / "no-such-dir")],
            cwd=tmp_path,
        )
        assert result.returncode == 2
        assert "BLOCKED" in result.stdout

    # --- P04: contracts_src in _speckit-index.json ---

    def test_index_feature_has_contracts_src_field(self, tmp_path):
        """P04: every feature record has a contracts_src field in the index."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        for feat in index["features"]:
            assert "contracts_src" in feat

    def test_index_contracts_src_none_when_absent(self, tmp_path):
        """P04: contracts_src is null when feature has no contracts/ dir (001)."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        feat = next(f for f in index["features"] if f["nnn"] == "001")
        assert feat["contracts_src"] is None

    def test_index_contracts_src_path_when_present(self, tmp_path):
        """P04: contracts_src records the absolute path to contracts/ dir (002)."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        feat = next(f for f in index["features"] if f["nnn"] == "002")
        assert feat["contracts_src"] is not None
        contracts_path = Path(feat["contracts_src"])
        assert contracts_path.is_dir()
        assert (contracts_path / "openapi.yaml").is_file()

    def test_spec_summary_contains_contracts_src_for_002(self, tmp_path):
        """P04: spec-summary.md surfaces contracts_src line for features that have it."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        content = (plan_dir / "artifacts" / "spec-summary.md").read_text()
        assert "contracts_src" in content

    # --- P05: research fields in _speckit-index.json ---

    def test_index_feature_has_research_fields(self, tmp_path):
        """P05: every feature record has has_research, research_src, research_sections."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        for feat in index["features"]:
            assert "has_research" in feat
            assert "research_src" in feat
            assert "research_sections" in feat

    def test_index_has_research_false_for_001(self, tmp_path):
        """P05: 001 has no research.md → has_research=false, research_src=null."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        feat = next(f for f in index["features"] if f["nnn"] == "001")
        assert feat["has_research"] is False
        assert feat["research_src"] is None
        assert feat["research_sections"] == []

    def test_index_has_research_true_for_002(self, tmp_path):
        """P05: 002 has research.md → has_research=true with sections list."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        index = json.loads((plan_dir / "artifacts" / "_speckit-index.json").read_text())
        feat = next(f for f in index["features"] if f["nnn"] == "002")
        assert feat["has_research"] is True
        assert feat["research_src"] is not None
        assert Path(feat["research_src"]).is_file()
        assert "Authentication Strategy" in feat["research_sections"]
        assert "PKCE Flow" in feat["research_sections"]

    def test_spec_summary_contains_research_src_for_002(self, tmp_path):
        """P05: spec-summary.md surfaces research_src for features that have it."""
        plan_dir = tmp_path / "plan"
        plan_dir.mkdir()
        _run(["--plan-dir", str(plan_dir), "--specs-root", str(SPECS_DIR)], cwd=tmp_path)
        content = (plan_dir / "artifacts" / "spec-summary.md").read_text()
        assert "research_src" in content
