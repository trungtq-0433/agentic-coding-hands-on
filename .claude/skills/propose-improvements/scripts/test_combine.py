"""Tests for propose-improvements Step 5a combine library + CLI.

Run with:
    .claude/skills/.venv/bin/python3 -m pytest claude/skills/propose-improvements/scripts/test_combine.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from combine_lib import (  # noqa: E402
    build_combined,
    demote_headings,
    parse_use_context_marker,
    prepare_track_body,
    strip_h1_and_use_context,
    validate_paths,
)

SCRIPT = THIS_DIR / "combine_proposals.py"
PY = Path(sys.executable)


def _proposal(track_h1: str, use_ctx: str, body: str) -> str:
    return f"# {track_h1}\n**Use context:** {use_ctx}\n\n{body}"


# ---------------------------------------------------------------------------
# strip_h1_and_use_context
# ---------------------------------------------------------------------------

def test_strip_atx_h1_plus_use_context():
    src = "# Title\n**Use context:** internal\n\n## Body\nfoo"
    assert strip_h1_and_use_context(src) == "## Body\nfoo"


def test_strip_setext_h1():
    src = "Title\n=====\n**Use context:** hybrid\n\n## Body"
    assert strip_h1_and_use_context(src) == "## Body"


def test_strip_skips_when_no_h1():
    src = "Not a heading\nMore lines"
    assert strip_h1_and_use_context(src) == src


def test_strip_html_comments_passthrough_elsewhere():
    src = "# Title\n**Use context:** internal\n\n<!-- preserved -->\n## Body"
    out = strip_h1_and_use_context(src)
    assert "<!-- preserved -->" in out


def test_strip_handles_h1_only_no_use_context():
    src = "# Title\n\n## Body"
    out = strip_h1_and_use_context(src)
    assert out == "## Body"


# ---------------------------------------------------------------------------
# parse_use_context_marker
# ---------------------------------------------------------------------------

def test_parse_use_context_basic():
    assert parse_use_context_marker("# T\n**Use context:** internal\n## X") == "internal"


def test_parse_use_context_case_insensitive():
    assert parse_use_context_marker("# T\n**USE CONTEXT:** Hybrid\n## X") == "hybrid"


def test_parse_use_context_invalid_value_returns_none():
    assert parse_use_context_marker("# T\n**Use context:** bogus\n") is None


def test_parse_use_context_stops_at_first_h2():
    # Marker after ## should be ignored (out of header region).
    src = "# T\n## Body\n**Use context:** internal\n"
    assert parse_use_context_marker(src) is None


# ---------------------------------------------------------------------------
# demote_headings - order + fence handling
# ---------------------------------------------------------------------------

def test_demote_order_strict():
    # `## Foo\n### Bar` -> `### Foo\n#### Bar`, NOT `### Foo\n##### Bar`.
    src = "## Foo\n### Bar"
    assert demote_headings(src) == "### Foo\n#### Bar"


def test_demote_skips_fenced_code():
    src = "## Real\n```\n## In code\n### Also code\n```\n### After\n"
    out = demote_headings(src)
    # Real H2 demoted, H3 demoted, fenced lines untouched.
    assert "### Real" in out
    assert "## In code" in out
    assert "### Also code" in out
    assert "#### After" in out


def test_demote_skips_tilde_fence_with_run_length():
    # Opening ~~~~~ requires closing ~~~~~ (or more), shorter ~~~ does NOT close.
    src = "~~~~~\n## Inside\n~~~\nstill inside\n~~~~~\n## After\n"
    out = demote_headings(src)
    assert "## Inside" in out
    assert "### After" in out


def test_demote_handles_indented_heading():
    # 0-3 leading spaces still counts as heading.
    src = "   ## Indented\n   ### Item"
    out = demote_headings(src)
    assert "   ### Indented" in out
    assert "   #### Item" in out


def test_demote_ignores_h4_and_deeper():
    # `#### Foo` should NOT be matched by H3-pass (4 hashes not 3).
    src = "## A\n### B\n#### C\n##### D\n"
    out = demote_headings(src)
    assert "### A" in out
    assert "#### B" in out
    assert "#### C" in out  # untouched
    assert "##### D" in out  # untouched


# ---------------------------------------------------------------------------
# build_combined
# ---------------------------------------------------------------------------

def test_build_with_both_tracks():
    out = build_combined(
        project_name="proj",
        iso_date="2026-05-18",
        use_context="internal",
        tech_body="### Aspect\n#### Item",
        biz_body="### B-Aspect",
    )
    assert "# Improvement Proposal — proj" in out
    assert "Use context: **internal**" in out
    assert "## Technical" in out
    assert "## Business" in out
    assert out.rstrip().endswith("<!-- dedup: pending -->")


def test_build_omits_business_when_absent():
    out = build_combined(
        project_name="proj",
        iso_date="2026-05-18",
        use_context="hybrid",
        tech_body="### A",
        biz_body=None,
    )
    assert "## Technical" in out
    assert "## Business" not in out
    assert "<!-- dedup: pending -->" in out


def test_build_omits_technical_when_absent():
    out = build_combined(
        project_name="proj",
        iso_date="2026-05-18",
        use_context="customer-facing",
        tech_body=None,
        biz_body="### B",
    )
    assert "## Business" in out
    assert "## Technical" not in out


def test_build_omits_use_context_badge_when_none():
    out = build_combined(
        project_name="proj",
        iso_date="2026-05-18",
        use_context=None,
        tech_body="### A",
        biz_body=None,
    )
    assert "Use context" not in out


def test_build_rejects_both_missing():
    with pytest.raises(ValueError):
        build_combined(project_name="p", iso_date="d", use_context=None, tech_body=None, biz_body=None)


# ---------------------------------------------------------------------------
# validate_paths
# ---------------------------------------------------------------------------

def test_validate_paths_accepts_inside_plans(tmp_path, monkeypatch):
    plans = tmp_path / "plans"
    plans.mkdir()
    monkeypatch.chdir(tmp_path)
    out = plans / "improvement-proposal" / "combined-initial.md"
    inp = tmp_path / "proposal.md"
    inp.touch()
    validate_paths(plans_root=plans, output_path=out, input_paths=[inp])  # no raise


def test_validate_paths_rejects_traversal(tmp_path, monkeypatch):
    plans = tmp_path / "plans"
    plans.mkdir()
    monkeypatch.chdir(tmp_path)
    bad_out = tmp_path / "etc" / "passwd"
    with pytest.raises(ValueError):
        validate_paths(plans_root=plans, output_path=bad_out, input_paths=[])


def test_validate_paths_rejects_null_byte(tmp_path, monkeypatch):
    plans = tmp_path / "plans"
    plans.mkdir()
    monkeypatch.chdir(tmp_path)
    bad = Path(str(plans / "combined-initial.md") + "\x00")
    with pytest.raises(ValueError):
        validate_paths(plans_root=plans, output_path=bad, input_paths=[])


# ---------------------------------------------------------------------------
# prepare_track_body integration
# ---------------------------------------------------------------------------

def test_prepare_track_body_strips_then_demotes():
    src = _proposal("Technical Proposal", "internal", "## Aspect\n### Item\n#### Detail")
    out = prepare_track_body(src)
    assert "Technical Proposal" not in out
    assert "Use context" not in out
    assert "### Aspect" in out
    assert "#### Item" in out
    assert "#### Detail" in out  # H4 untouched


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def _run_cli(tmp_path: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PY), str(SCRIPT), *extra],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def _setup_workspace(tmp_path: Path, *, tech: str | None = None, biz: str | None = None,
                     use_ctx_json: str | None = None) -> dict[str, Path]:
    plans = tmp_path / "plans" / "improvement-proposal"
    plans.mkdir(parents=True)
    tech_path = plans / "technical" / "03-technical-proposal.md"
    biz_path = plans / "business" / "04-business-proposal.md"
    if tech is not None:
        tech_path.parent.mkdir(parents=True, exist_ok=True)
        tech_path.write_text(tech, encoding="utf-8")
    if biz is not None:
        biz_path.parent.mkdir(parents=True, exist_ok=True)
        biz_path.write_text(biz, encoding="utf-8")
    if use_ctx_json is not None:
        (plans / "use-context.json").write_text(use_ctx_json, encoding="utf-8")
    return {
        "tech": tech_path,
        "biz": biz_path,
        "use_ctx_json": plans / "use-context.json",
        "out": plans / "combined-initial.md",
    }


def test_cli_both_tracks_happy_path(tmp_path):
    paths = _setup_workspace(
        tmp_path,
        tech=_proposal("Technical Proposal — p", "internal", "## Reliability\n### Add retries"),
        biz=_proposal("Business Proposal — p", "internal", "## Revenue\n### Upsell add-ons"),
        use_ctx_json=json.dumps({"useContext": "internal"}),
    )
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--business-path", str(paths["biz"].relative_to(tmp_path)),
        "--use-context-json", str(paths["use_ctx_json"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "done: step-5a →" in result.stdout
    assert "Status: DONE" in result.stdout
    body = paths["out"].read_text(encoding="utf-8")
    assert "## Technical" in body
    assert "## Business" in body
    assert "### Reliability" in body  # H2 demoted
    assert "#### Add retries" in body  # H3 demoted
    assert body.rstrip().endswith("<!-- dedup: pending -->")


def test_cli_use_context_divergence_emits_warn(tmp_path):
    paths = _setup_workspace(
        tmp_path,
        tech=_proposal("T", "internal", "## A\n### x"),
        biz=_proposal("B", "hybrid", "## A\n### y"),
    )
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--business-path", str(paths["biz"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode == 0
    assert "warn: step-5a use-context divergence" in result.stdout
    assert "Status: DONE_WITH_CONCERNS" in result.stdout


def test_cli_technical_only(tmp_path):
    paths = _setup_workspace(
        tmp_path,
        tech=_proposal("T", "internal", "## A\n### x"),
    )
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    body = paths["out"].read_text(encoding="utf-8")
    assert "## Technical" in body
    assert "## Business" not in body
    assert "<!-- dedup: pending -->" in body


def test_cli_business_only(tmp_path):
    paths = _setup_workspace(
        tmp_path,
        biz=_proposal("B", "internal", "## A\n### x"),
    )
    result = _run_cli(
        tmp_path,
        "--business-path", str(paths["biz"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    body = paths["out"].read_text(encoding="utf-8")
    assert "## Business" in body
    assert "## Technical" not in body


def test_cli_neither_track_blocks(tmp_path):
    _setup_workspace(tmp_path)
    result = _run_cli(
        tmp_path,
        "--output", "plans/improvement-proposal/combined-initial.md",
        "--project-name", "p",
    )
    assert result.returncode != 0
    assert "Status: BLOCKED" in result.stdout


def test_cli_both_provided_but_empty_blocks(tmp_path):
    paths = _setup_workspace(tmp_path, tech="", biz="   \n\n")
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--business-path", str(paths["biz"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode != 0
    assert "Status: BLOCKED" in result.stdout
    assert "missing/empty" in result.stdout


def test_cli_idempotent_on_existing_output(tmp_path):
    paths = _setup_workspace(
        tmp_path,
        tech=_proposal("T", "internal", "## A\n### x"),
    )
    paths["out"].parent.mkdir(parents=True, exist_ok=True)
    paths["out"].write_text("pre-existing content\n", encoding="utf-8")
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode == 0
    assert "skip: step-5a" in result.stdout
    assert "Status: DONE" in result.stdout
    # Content untouched.
    assert paths["out"].read_text(encoding="utf-8") == "pre-existing content\n"


def test_cli_rejects_traversal(tmp_path):
    paths = _setup_workspace(
        tmp_path,
        tech=_proposal("T", "internal", "## A\n### x"),
    )
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--output", "plans/../etc/passwd",
        "--project-name", "p",
    )
    assert result.returncode != 0
    assert "Status: BLOCKED" in result.stdout
    assert "path-safety" in result.stdout


def test_cli_writes_atomically(tmp_path):
    """Output dir contains only the final file - no `.tmp` leftovers."""
    paths = _setup_workspace(
        tmp_path,
        tech=_proposal("T", "internal", "## A\n### x"),
    )
    result = _run_cli(
        tmp_path,
        "--technical-path", str(paths["tech"].relative_to(tmp_path)),
        "--output", str(paths["out"].relative_to(tmp_path)),
        "--project-name", "p",
    )
    assert result.returncode == 0
    leftovers = [p.name for p in paths["out"].parent.iterdir() if ".tmp" in p.name]
    assert leftovers == [], f"tempfile leaked: {leftovers}"
