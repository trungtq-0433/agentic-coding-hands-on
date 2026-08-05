"""Tests for propose-improvements Step 7 apply-verdicts script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "apply_verdicts.py"

from apply_verdicts_lib import (  # noqa: E402
    demote_h2_to_h4,
    load_verdicts,
    parse_value_effort,
    recompute_rollup_heading,
    sort_items_within_aspect,
    split_combined,
    split_rollups,
    strip_dedup_marker,
    title_to_slug,
    validate_revised_body,
)


# ---------------------------------------------------------------------------
# Library tests
# ---------------------------------------------------------------------------

def test_strip_dedup_marker_trailing() -> None:
    assert strip_dedup_marker("body\n<!-- dedup: applied (n=3) -->\n") == "body"
    assert strip_dedup_marker("body\n<!-- dedup: pending -->") == "body"
    assert strip_dedup_marker("body\n") == "body\n"


def test_split_combined_both_tracks() -> None:
    text = """# Improvement Proposal

intro

## Technical

#### A

## Business

#### B
"""
    header, tech, biz = split_combined(text)
    assert "intro" in header
    assert tech.startswith("## Technical")
    assert biz.startswith("## Business")


def test_split_combined_only_business() -> None:
    text = "# Improvement Proposal\n\n## Business\n\n#### B\n"
    header, tech, biz = split_combined(text)
    assert tech is None
    assert biz.startswith("## Business")


def test_split_combined_blocked_neither_track() -> None:
    text = "# Improvement Proposal\n\nNo tracks.\n"
    header, tech, biz = split_combined(text)
    assert tech is None and biz is None


def test_title_to_slug_untitled() -> None:
    assert title_to_slug("---") == "untitled"
    assert title_to_slug("Hello World") == "hello-world"


def test_validate_revised_body_ok() -> None:
    body = """## Refactor auth module

- **Value:** high
- **Need:** explain
- **Benefits:** named outcome
- **Proposed solution:** do X
- **Engineering effort hint:** medium
"""
    assert validate_revised_body(body) is True


def test_validate_revised_body_rejects_category_bullet() -> None:
    body = """## X

- **Category:** foo
- **Value:** high
- **Need:** explain
- **Benefits:** outcome
- **Proposed solution:** do X
- **Engineering effort hint:** medium
"""
    assert validate_revised_body(body) is False


def test_validate_revised_body_rejects_subheading() -> None:
    body = """## X

### Subsection

- **Value:** high
- **Need:** explain
- **Benefits:** outcome
- **Proposed solution:** do X
- **Engineering effort hint:** medium
"""
    assert validate_revised_body(body) is False


def test_validate_revised_body_rejects_missing_bullet() -> None:
    body = """## X

- **Value:** high
- **Need:** explain
- **Benefits:** outcome
- **Engineering effort hint:** medium
"""
    assert validate_revised_body(body) is False


def test_demote_h2_to_h4_basic() -> None:
    body = "## Title\n\n- **Value:** high\n"
    out = demote_h2_to_h4(body)
    assert out.startswith("#### Title")


def test_parse_value_effort() -> None:
    block = """#### Item

- **Value:** high
- **Need:** ...
- **Engineering effort hint:** low
"""
    v, e = parse_value_effort(block)
    assert v == "high"
    assert e == "low"


def test_sort_items_value_desc_effort_asc() -> None:
    items = [
        "#### A\n- **Value:** low\n- **Engineering effort hint:** low\n",
        "#### B\n- **Value:** high\n- **Engineering effort hint:** medium\n",
        "#### C\n- **Value:** high\n- **Engineering effort hint:** low\n",
    ]
    out, warns = sort_items_within_aspect(items)
    assert out[0].startswith("#### C")  # high+low
    assert out[1].startswith("#### B")  # high+medium
    assert out[2].startswith("#### A")  # low+low
    assert warns == []


def test_sort_items_fallback_warns_on_missing_bullets() -> None:
    items = ["#### Bad\n- **Value:** high\n"]
    out, warns = sort_items_within_aspect(items)
    assert len(warns) == 1
    assert "sort-fallback" in warns[0]


def test_recompute_rollup_heading_count_and_effort_range() -> None:
    items = [
        "#### A\n- **Value:** high\n- **Engineering effort hint:** low\n",
        "#### B\n- **Value:** medium\n- **Engineering effort hint:** high\n",
    ]
    out = recompute_rollup_heading("### MyAspect · 5 items · max=low · effort=medium", items)
    assert out == "### MyAspect · 2 items · max=high · effort=low-high"


def test_recompute_rollup_heading_singular_item() -> None:
    items = ["#### A\n- **Value:** high\n- **Engineering effort hint:** low\n"]
    out = recompute_rollup_heading("### Foo · 7 items · max=low · effort=medium", items)
    assert out == "### Foo · 1 item · max=high · effort=low"


def test_split_rollups_basic() -> None:
    track = """## Technical

intro prose

### Aspect Architecture · 2 items · max=high · effort=low-medium
<!-- aspect-id: architecture -->

#### Item A

- **Value:** high

#### Item B

- **Value:** medium

### Aspect Security · 1 item · max=high · effort=low
<!-- aspect-id: security -->

#### Item C

- **Value:** high
"""
    header, rollups = split_rollups(track)
    assert "intro prose" in header
    assert len(rollups) == 2
    assert len(rollups[0].items) == 2
    assert rollups[0].aspect_comment == "<!-- aspect-id: architecture -->"
    assert len(rollups[1].items) == 1


def test_load_verdicts_parses_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "item-01-foo.md"
    f.write_text("""---
item_index: 1
item_slug: foo
track: technical
decision: KEEP
---

# Reason
all good
""")
    verdicts, warns = load_verdicts(tmp_path)
    assert 1 in verdicts
    assert verdicts[1].decision == "KEEP"
    assert warns == []


def test_load_verdicts_extracts_revised_body(tmp_path: Path) -> None:
    f = tmp_path / "item-02-bar.md"
    f.write_text("""---
item_index: 2
item_slug: bar
track: business
decision: REVISE
---

# Audits

- ...

# Reason
revise it

# Revised item

## Bar Improved

- **Value:** high
- **Need:** more
- **Benefits:** clear
- **Proposed solution:** do
- **Engineering effort hint:** low
""")
    verdicts, warns = load_verdicts(tmp_path)
    assert 2 in verdicts
    assert verdicts[2].revised_body is not None
    assert "**Engineering effort hint:** low" in verdicts[2].revised_body


def test_load_verdicts_handles_malformed(tmp_path: Path) -> None:
    f = tmp_path / "item-03-baz.md"
    f.write_text("no frontmatter here")
    verdicts, warns = load_verdicts(tmp_path)
    assert 3 not in verdicts
    assert any("malformed" in w for w in warns)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, check=False, cwd=str(cwd),
    )


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    plans = tmp_path / "plans"
    plans.mkdir()
    validation = plans / "validation"
    validation.mkdir()
    output = plans / "improvement-proposal.md"
    return plans / "combined-initial.md", validation, output


COMBINED_TWO_ITEMS = """# Improvement Proposal — example

> some banner

## Technical

### Architecture · 2 items · max=high · effort=low-medium
<!-- aspect-id: architecture -->

#### Refactor auth module

- **Value:** high
- **Need:** auth is messy
- **Benefits:** safer
- **Proposed solution:** rewrite
- **Engineering effort hint:** medium

#### Add caching layer

- **Value:** medium
- **Need:** slow
- **Benefits:** faster
- **Proposed solution:** redis
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
"""


def _write_combined(path: Path, text: str = COMBINED_TWO_ITEMS) -> None:
    path.write_text(text)


def test_cli_blocks_when_combined_missing(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    # combined not written
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 2
    assert "BLOCKED" in res.stdout


def test_cli_all_keep_no_verdicts(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    # validation_dir is empty -> all items default to KEEP
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    text = output.read_text()
    assert "#### Refactor auth module" in text
    assert "#### Add caching layer" in text
    # Banner mentions 2 unvalidated items.
    assert "2 items shipped without complete validation" in text


def test_cli_keep_with_verdict(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    (validation / "item-01-refactor-auth-module.md").write_text(
        "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: KEEP\n---\n"
    )
    (validation / "item-02-add-caching-layer.md").write_text(
        "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: KEEP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0
    text = output.read_text()
    # Both items present, no banner.
    assert "#### Refactor auth module" in text
    assert "#### Add caching layer" in text
    assert "without complete validation" not in text


def test_cli_drop_removes_item_and_recomputes_rollup(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    (validation / "item-01-refactor-auth-module.md").write_text(
        "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: DROP\n---\n"
    )
    (validation / "item-02-add-caching-layer.md").write_text(
        "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: KEEP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0
    text = output.read_text()
    assert "#### Refactor auth module" not in text
    assert "#### Add caching layer" in text
    # Rollup recomputed to 1 item.
    assert "### Architecture · 1 item ·" in text
    assert "drop: item-01" in res.stdout


def test_cli_drop_all_removes_rollup(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    for idx, slug in ((1, "refactor-auth-module"), (2, "add-caching-layer")):
        (validation / f"item-{idx:02d}-{slug}.md").write_text(
            f"---\nitem_index: {idx}\nitem_slug: {slug}\ntrack: technical\ndecision: DROP\n---\n"
        )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0
    text = output.read_text()
    assert "### Architecture" not in text
    assert "<!-- aspect-id: architecture -->" not in text


def test_cli_slug_mismatch_keeps_original(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    # Wrong slug → stale verdict → KEEP fallback.
    (validation / "item-01-something-else.md").write_text(
        "---\nitem_index: 1\nitem_slug: something-else\ntrack: technical\ndecision: DROP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0
    text = output.read_text()
    assert "#### Refactor auth module" in text  # stayed
    assert "verdict slug mismatch" in res.stdout


def test_cli_evidence_degraded_banner(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    (validation / "item-01-refactor-auth-module.md").write_text(
        "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: KEEP\n---\n"
    )
    (validation / "item-02-add-caching-layer.md").write_text(
        "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: KEEP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
        "--evidence-degraded-warns",
        'warn: item-01 "Refactor auth module" evidence-degraded — aspect-id=foo missing',
    ], cwd=tmp_path)
    assert res.returncode == 0
    text = output.read_text()
    assert "1 item shipped without complete validation" in text


def test_cli_idempotency_skip(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    output.write_text("PRE-EXISTING")
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0
    assert "skip: step-7" in res.stdout
    assert output.read_text() == "PRE-EXISTING"


def test_cli_orphan_verdict_warns(tmp_path: Path) -> None:
    combined, validation, output = _setup(tmp_path)
    _write_combined(combined)
    (validation / "item-99-ghost-item.md").write_text(
        "---\nitem_index: 99\nitem_slug: ghost-item\ntrack: technical\ndecision: DROP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0
    assert "orphan verdict at item_index=99" in res.stdout


# Regression: items whose first 200 chars are identical (same title + same
# Value/Need/Benefits/Proposed-solution prose; only Effort differs at the end)
# previously collided on a content-based block_key and silently swapped decisions.
COMBINED_TWIN_PREFIX = """# Improvement Proposal — twin-prefix regression

## Technical

### Architecture · 2 items · max=high · effort=low-high
<!-- aspect-id: architecture -->

#### Add SSO Support

- **Value:** high
- **Need:** Enables enterprise SSO via SAML and OIDC, unlocking large-account deals that block on identity federation. Most prospects above 200 seats require this exact integration before signing.
- **Benefits:** Removes blocker for enterprise sales pipeline.
- **Proposed solution:** Wire SAML + OIDC into existing auth.
- **Engineering effort hint:** medium

#### Add SSO Support

- **Value:** high
- **Need:** Enables enterprise SSO via SAML and OIDC, unlocking large-account deals that block on identity federation. Most prospects above 200 seats require this exact integration before signing.
- **Benefits:** Removes blocker for enterprise sales pipeline.
- **Proposed solution:** Wire SAML + OIDC into existing auth.
- **Engineering effort hint:** large

<!-- dedup: applied (n=0) -->
"""


def test_cli_twin_prefix_items_get_distinct_decisions(tmp_path: Path) -> None:
    """Regression for content-key collision: item-01 DROP must not bleed into item-02."""
    combined, validation, output = _setup(tmp_path)
    combined.write_text(COMBINED_TWIN_PREFIX)
    (validation / "item-01-add-sso-support.md").write_text(
        "---\nitem_index: 1\nitem_slug: add-sso-support\ntrack: technical\ndecision: DROP\n---\n"
    )
    (validation / "item-02-add-sso-support.md").write_text(
        "---\nitem_index: 2\nitem_slug: add-sso-support\ntrack: technical\ndecision: KEEP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    text = output.read_text()
    # item-01 must be dropped, item-02 must remain.
    assert text.count("#### Add SSO Support") == 1
    assert "**Engineering effort hint:** large" in text  # the kept (item-02) effort line survives
    assert "**Engineering effort hint:** medium" not in text  # the dropped (item-01) is gone
    assert "drop: item-01" in res.stdout


def test_cli_title_with_trigger_phrase_does_not_inflate_banner(tmp_path: Path) -> None:
    """Regression for substring-search false-positive on 'validation directory missing'."""
    combined, validation, output = _setup(tmp_path)
    # Build a combined with an item whose TITLE contains the trigger substring.
    combined.write_text("""# Improvement Proposal — trigger-phrase regression

## Technical

### Reliability · 1 item · max=medium · effort=low
<!-- aspect-id: reliability -->

#### Fix validation directory missing error in onboarding

- **Value:** medium
- **Need:** Users hit a 500 when validation dir is absent.
- **Benefits:** Smoother first-run experience.
- **Proposed solution:** Lazily create the dir.
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
""")
    # NO verdict file → missing-verdict warn (which contains the trigger phrase as part of the title).
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    text = output.read_text()
    # The validation dir IS present (empty but exists). Banner must say "1 item",
    # not be inflated by the substring-match false positive.
    assert "1 item shipped without complete validation" in text


def test_cli_pre_rollup_h4_does_not_misroute_verdicts(tmp_path: Path) -> None:
    """Regression for walker-divergence bug.

    A `#### H4` that lives in the track body BEFORE the first `### H3` rollup
    used to silently invert verdicts: the pre-rollup item's verdict would be
    applied to the first real rollup item, and the pre-rollup item itself
    (which lives in `track_header` after `split_rollups`) would be emitted
    verbatim regardless of its own verdict.

    Post-fix expectation: indices walk only inside rollups, so the pre-rollup
    item never receives an index. Its verdict (item_index=1) collides with the
    first real rollup item (also walked as index=1) and triggers a slug-mismatch
    warning instead of silently misrouting. The pre-rollup block is preserved
    verbatim (it's part of the unstructured track header). The real rollup
    item is KEPT because slug mismatch defaults to keep + warn.
    """
    combined, validation, output = _setup(tmp_path)
    combined.write_text(
        "# Combined\n\n"
        "## Technical\n\n"
        "#### Stray pre-rollup item\n\n"
        "- **Value:** high\n- **Need:** outside any rollup\n"
        "- **Benefits:** none\n- **Proposed solution:** none\n- **Engineering effort hint:** low\n\n"
        "### Architecture · 1 item · max=high · effort=medium\n"
        "<!-- aspect-id: architecture -->\n\n"
        "#### Real rollup item\n\n"
        "- **Value:** high\n- **Need:** real\n- **Benefits:** real\n"
        "- **Proposed solution:** real\n- **Engineering effort hint:** medium\n\n"
        "<!-- dedup: applied (n=0) -->\n"
    )
    # Two verdicts that target the items by their original (pre-fix) indices.
    (validation / "item-01-stray-pre-rollup-item.md").write_text(
        "---\nitem_index: 1\nitem_slug: stray-pre-rollup-item\ndecision: DROP\n---\n"
    )
    (validation / "item-02-real-rollup-item.md").write_text(
        "---\nitem_index: 2\nitem_slug: real-rollup-item\ndecision: KEEP\n---\n"
    )
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(validation),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    text = output.read_text()
    # Stray remains (it's part of track_header, emitted verbatim).
    assert "#### Stray pre-rollup item" in text
    # Real rollup item MUST survive — the pre-fix bug would drop it because the
    # stray's DROP verdict was misrouted onto it.
    assert "#### Real rollup item" in text
    assert "### Architecture" in text
    # Operator must see something is wrong: slug-mismatch + orphan warns.
    assert "verdict slug mismatch at item-01" in res.stdout
    assert "orphan verdict at item_index=2" in res.stdout


def test_cli_blocks_on_unsafe_validation_dir(tmp_path: Path) -> None:
    """Regression for missing _path_safe check on validation_dir."""
    combined, _validation, output = _setup(tmp_path)
    _write_combined(combined)
    # Point validation_dir outside CWD via an absolute path well outside the tmp_path.
    outside = Path("/tmp") / f"proposal-evil-{tmp_path.name}"
    outside.mkdir(exist_ok=True)
    res = _run([
        "--combined-path", str(combined),
        "--validation-dir", str(outside),
        "--output-path", str(output),
    ], cwd=tmp_path)
    assert res.returncode == 2
    assert "BLOCKED" in res.stdout
    assert "validation_dir" in res.stdout
