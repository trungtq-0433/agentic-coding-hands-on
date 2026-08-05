"""Tests for propose-improvements Step 5c phase-d-prep splitter.

phase-d-prep now only splits combined-initial.md into one per-item payload
(carrying just the proposal item's markdown) + a manifest. The validator
self-verifies against the repo, so there is no evidence / stack-context /
use-context machinery left to test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "phase_d_prep.py"

from phase_d_prep_lib import (  # noqa: E402
    parse_items,
    rewrite_h4_to_h2,
    title_to_slug,
    validate_filename_slug,
)


# ---------------------------------------------------------------------------
# Library-level tests
# ---------------------------------------------------------------------------

def test_title_to_slug_basic() -> None:
    assert title_to_slug("Hello World") == "hello-world"
    assert title_to_slug("  Mixed CASE — punct!  ") == "mixed-case-punct"


def test_title_to_slug_untitled_fallback() -> None:
    assert title_to_slug("アプリ改善") == "untitled"
    assert title_to_slug("---") == "untitled"


def test_validate_filename_slug() -> None:
    assert validate_filename_slug("auth-mfa")
    assert not validate_filename_slug("-leading-dash")
    assert not validate_filename_slug("")


def test_parse_items_basic_two_tracks() -> None:
    combined = """\
# Improvement Proposal

## Technical

### Architecture · group-1
<!-- aspect-id: architecture -->

#### Refactor auth module

- Value: high
- Need: ...

#### Add caching layer

- Value: medium

## Business

### UX · group-1
<!-- aspect-id: ux-gaps -->

#### Improve signup
- Value: high
"""
    items = parse_items(combined)
    assert [it.title for it in items] == [
        "Refactor auth module", "Add caching layer", "Improve signup",
    ]
    assert [it.track for it in items] == ["technical", "technical", "business"]
    assert [it.index for it in items] == [1, 2, 3]


def test_parse_items_ignores_h4_inside_fence() -> None:
    combined = """\
## Technical

### Group
<!-- aspect-id: x -->

#### Real item

```
#### Fake item inside fence
```

#### Real item 2
"""
    items = parse_items(combined)
    assert [it.title for it in items] == ["Real item", "Real item 2"]


def test_parse_items_ignores_h4_outside_track_section() -> None:
    combined = """\
# Heading

#### Orphan item before any track

## Technical

### Group
<!-- aspect-id: x -->

#### Real item
"""
    items = parse_items(combined)
    assert [it.title for it in items] == ["Real item"]


def test_rewrite_h4_to_h2() -> None:
    body = "#### Refactor auth\n\n- Value: high\n"
    out = rewrite_h4_to_h2(body)
    assert out.startswith("## Refactor auth")
    assert out.count("####") == 0


# ---------------------------------------------------------------------------
# CLI-level tests
# ---------------------------------------------------------------------------

def _build_combined(tmp_path: Path, body: str) -> Path:
    """Wrap body with required trailing dedup-applied marker."""
    combined = tmp_path / "combined-initial.md"
    if not body.endswith("\n"):
        body += "\n"
    combined.write_text(body + "<!-- dedup: applied (n=0) -->\n")
    return combined


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False,
    )


def test_cli_blocks_when_dedup_marker_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()
    combined = plans / "combined-initial.md"
    combined.write_text("## Technical\n#### Item\n")  # no marker

    res = _run([
        "--combined-path", str(combined),
        "--payloads-dir", str(plans / "payloads"),
        "--manifest-path", str(plans / "payloads" / "_manifest.json"),
        "--validation-dir", str(plans / "validation"),
    ])
    assert res.returncode == 2
    assert "BLOCKED" in res.stdout
    assert "step-5b" in res.stdout


def test_cli_writes_payload_and_manifest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()

    combined = _build_combined(plans, """\
## Technical

### Architecture · group
<!-- aspect-id: architecture -->

#### Refactor auth module

- Value: high
- Need: foo
""")

    res = _run([
        "--combined-path", str(combined),
        "--payloads-dir", str(plans / "payloads"),
        "--manifest-path", str(plans / "payloads" / "_manifest.json"),
        "--validation-dir", str(plans / "validation"),
    ])
    assert res.returncode == 0, res.stdout + res.stderr
    assert "done: step-5c" in res.stdout
    assert "Status: DONE" in res.stdout

    manifest = json.loads((plans / "payloads" / "_manifest.json").read_text())
    assert manifest["schema_version"] == 1
    assert len(manifest["items"]) == 1
    assert manifest["items"][0]["item_slug"] == "refactor-auth-module"
    assert manifest["items"][0]["track"] == "technical"
    assert "use_context" not in manifest
    assert "evidence_degraded_warns" not in manifest

    payload_path = plans / "payloads" / "item-01-refactor-auth-module.json"
    payload = json.loads(payload_path.read_text())
    # The slimmed payload carries ONLY the proposal item — nothing else.
    assert list(payload.keys()) == ["schema_version", "item_markdown"]
    assert payload["item_markdown"].startswith("## Refactor auth module")


def test_cli_idempotency_skips_on_matching_sha(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()

    combined = _build_combined(plans, """\
## Technical

### Architecture · group
<!-- aspect-id: architecture -->

#### Refactor auth module
- Value: high
""")

    args = [
        "--combined-path", str(combined),
        "--payloads-dir", str(plans / "payloads"),
        "--manifest-path", str(plans / "payloads" / "_manifest.json"),
        "--validation-dir", str(plans / "validation"),
    ]
    assert _run(args).returncode == 0
    second = _run(args)
    assert "skip: step-5c" in second.stdout


def test_cli_stale_manifest_rebuilds(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()

    combined = _build_combined(plans, """\
## Technical

### Architecture · group
<!-- aspect-id: architecture -->

#### Item A
- Value: high
""")

    args_common = [
        "--payloads-dir", str(plans / "payloads"),
        "--manifest-path", str(plans / "payloads" / "_manifest.json"),
        "--validation-dir", str(plans / "validation"),
    ]
    assert _run(["--combined-path", str(combined)] + args_common).returncode == 0

    # Mutate combined → expect rebuild with the new item count.
    _build_combined(plans, """\
## Technical

### Architecture · group
<!-- aspect-id: architecture -->

#### Item A
- Value: high

#### Item B (new)
- Value: medium
""")
    res = _run(["--combined-path", str(combined)] + args_common)
    assert res.returncode == 0
    manifest = json.loads((plans / "payloads" / "_manifest.json").read_text())
    assert len(manifest["items"]) == 2


def test_cli_zero_items(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()
    combined = _build_combined(plans, "## Technical\n\nNo items here.\n")

    res = _run([
        "--combined-path", str(combined),
        "--payloads-dir", str(plans / "payloads"),
        "--manifest-path", str(plans / "payloads" / "_manifest.json"),
        "--validation-dir", str(plans / "validation"),
    ])
    assert res.returncode == 0
    assert "(no items)" in res.stdout
    manifest = json.loads((plans / "payloads" / "_manifest.json").read_text())
    assert manifest["items"] == []


def test_cli_single_track_business_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()

    combined = _build_combined(plans, """\
## Business

### UX-gaps · group
<!-- aspect-id: ux-gaps -->

#### Improve signup
- Value: high
""")

    res = _run([
        "--combined-path", str(combined),
        "--payloads-dir", str(plans / "payloads"),
        "--manifest-path", str(plans / "payloads" / "_manifest.json"),
        "--validation-dir", str(plans / "validation"),
    ])
    assert res.returncode == 0, res.stdout + res.stderr
    manifest = json.loads((plans / "payloads" / "_manifest.json").read_text())
    assert len(manifest["items"]) == 1
    assert manifest["items"][0]["track"] == "business"
