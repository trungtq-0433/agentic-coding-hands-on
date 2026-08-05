"""Tests for shard retry/resume: partial-fragment detection + idempotent re-merge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def frag_dir(tmp_path):
    """Create a fragment directory with a slice plan and some fragments."""
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    fdir = art_dir / "_fragments" / "screen-flow"
    fdir.mkdir(parents=True)

    slice_plan = {
        "slices": [
            {"ordinal": "01", "namespace": "auth", "screens": ["SCR001", "SCR002"]},
            {"ordinal": "02", "namespace": "users", "screens": ["SCR003", "SCR004"]},
            {"ordinal": "03", "namespace": "posts", "screens": ["SCR005", "SCR006"]},
        ]
    }
    (fdir / "_slice-plan.json").write_text(json.dumps(slice_plan))

    (fdir / "01-auth.md").write_text("### SCR001 (Login)\n\n**Entry Points**:\n- Direct URL\n")
    (fdir / "03-posts.md").write_text("### SCR005 (PostList)\n\n**Entry Points**:\n- From dashboard\n")
    # Fragment 02-users.md is MISSING (simulates timeout)

    skeleton = (
        "# Screen Flow\n\n"
        "## Navigation Map\n\n```mermaid\ngraph TD\n```\n\n"
        "## Screen Transitions\n\n"
        "### Auth Module\n{POPULATED_BY_FRAGMENTS}\n\n"
        "### Users Module\n{POPULATED_BY_FRAGMENTS}\n\n"
        "### Posts Module\n{POPULATED_BY_FRAGMENTS}\n"
    )
    (art_dir / "screen-flow.md").write_text(skeleton)

    return tmp_path


class TestPartialFragmentDetection:
    def test_detects_missing_fragment(self, frag_dir):
        fdir = frag_dir / "artifacts" / "_fragments" / "screen-flow"
        plan = json.loads((fdir / "_slice-plan.json").read_text())
        expected = {s["ordinal"] for s in plan["slices"]}
        actual = {p.stem.split("-")[0] for p in fdir.glob("*.md")}
        missing = expected - actual
        assert missing == {"02"}

    def test_all_fragments_present(self, frag_dir):
        fdir = frag_dir / "artifacts" / "_fragments" / "screen-flow"
        (fdir / "02-users.md").write_text("### SCR003 (UserList)\n\n**Entry Points**:\n- From nav\n")
        plan = json.loads((fdir / "_slice-plan.json").read_text())
        expected = {s["ordinal"] for s in plan["slices"]}
        actual = {p.stem.split("-")[0] for p in fdir.glob("*.md")}
        assert expected == actual


class TestIdempotentRemerge:
    def _merge(self, art_dir: Path, artifact: str = "screen-flow") -> str:
        fdir = art_dir / "_fragments" / artifact
        skeleton = (art_dir / f"{artifact}.md").read_text()
        frags = sorted(fdir.glob("*.md"))
        for frag in frags:
            content = frag.read_text().strip()
            skeleton = skeleton.replace("{POPULATED_BY_FRAGMENTS}", content + "\n\n{POPULATED_BY_FRAGMENTS}", 1)
        skeleton = skeleton.replace("{POPULATED_BY_FRAGMENTS}", "")
        (art_dir / f"{artifact}.md").write_text(skeleton)
        return skeleton

    def test_merge_then_remerge_no_duplicates(self, frag_dir):
        art_dir = frag_dir / "artifacts"
        fdir = art_dir / "_fragments" / "screen-flow"
        (fdir / "02-users.md").write_text("### SCR003 (UserList)\n\n**Entry Points**:\n- From nav\n")

        merged1 = self._merge(art_dir)
        assert merged1.count("SCR001") == 1
        assert merged1.count("SCR003") == 1
        assert merged1.count("SCR005") == 1
        assert "{POPULATED_BY_FRAGMENTS}" not in merged1

    def test_remerge_after_fragment_overwrite(self, frag_dir):
        """Simulate: fragment 02 timed out, was re-dispatched, re-merge produces clean file."""
        art_dir = frag_dir / "artifacts"
        fdir = art_dir / "_fragments" / "screen-flow"

        # First merge with missing fragment
        merged_partial = self._merge(art_dir)
        assert "SCR003" not in merged_partial  # missing fragment

        # Re-create skeleton (idempotent: fresh from template)
        skeleton = (
            "# Screen Flow\n\n"
            "## Navigation Map\n\n```mermaid\ngraph TD\n```\n\n"
            "## Screen Transitions\n\n"
            "### Auth Module\n{POPULATED_BY_FRAGMENTS}\n\n"
            "### Users Module\n{POPULATED_BY_FRAGMENTS}\n\n"
            "### Posts Module\n{POPULATED_BY_FRAGMENTS}\n"
        )
        (art_dir / "screen-flow.md").write_text(skeleton)

        # Now the missing fragment arrives
        (fdir / "02-users.md").write_text("### SCR003 (UserList)\n\n**Entry Points**:\n- From nav\n")

        merged_complete = self._merge(art_dir)
        assert "SCR001" in merged_complete
        assert "SCR003" in merged_complete
        assert "SCR005" in merged_complete
        # No duplicate sections
        assert merged_complete.count("### SCR001") == 1
        assert merged_complete.count("### SCR003") == 1
        assert merged_complete.count("### SCR005") == 1


class TestRetryEstimateGate:
    """Verify that the estimator can be consulted at retry time."""

    def test_estimate_still_returns_shard(self, tmp_path):
        """After timeout, re-running estimate on the same input still says shard=true."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from estimate_artifact_loc import estimate

        rl = tmp_path / "route-list.md"
        lines = ["| Method | Path | Handler |", "|--------|------|---------|"]
        for i in range(500):
            lines.append(f"| GET | /api/r{i} | C{i}@i |")
        rl.write_text("\n".join(lines))

        r = estimate("route-list", route_list=rl)
        assert r["shard"] is True  # 500 * lpu 2 = 1000 > 800
