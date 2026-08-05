"""Tests for the `ui_sniff` wiring added to `detect_stack_profile.py` (Phase 08, Track D).

`sys.path` already has scripts/ on it (see conftest.py), so this file imports
`detect_stack_profile` and `_content_sniff_lib` directly for in-process tests that need to
monkeypatch the sniff call (assert it was/wasn't invoked) -- something a subprocess-based CLI
run (the convention in test_detect_stack_profile.py) can't do. The CLI-level no-match test
mirrors that file's existing `_run` helper for consistency.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import detect_stack_profile as dsp

SCRIPT = Path(dsp.__file__)


def _run(root: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)] + (extra or []),
        capture_output=True, text=True, timeout=60, cwd=str(root),
    )


def _delphi_tree(root: Path) -> None:
    (root / "src").mkdir()
    (root / "src" / "Main.dpr").write_text("program Main; begin end.")
    (root / "src" / "Unit1.pas").write_text("unit Unit1; interface implementation end.")
    (root / "src" / "Form1.dfm").write_text("object Form1: TForm1\nend")
    (root / "App.dproj").write_text("<Project></Project>")


class _SniffSpy:
    """Records every call to `_content_sniff_lib.sniff_ui` made through detect_stack_profile's
    `_safe_sniff` wrapper, so tests can assert both invocation AND non-invocation."""

    def __init__(self, result: dict | None = None, raise_exc: Exception | None = None):
        self.calls: list[tuple[str, int]] = []
        self._result = result if result is not None else {"tier": 1, "signals": [], "summary": "0 signal(s), tier=1"}
        self._raise = raise_exc

    def __call__(self, root: str, file_cap: int = 50_000, deadline_seconds: float = 30.0) -> dict:
        self.calls.append((root, file_cap))
        if self._raise is not None:
            raise self._raise
        return self._result


# --- No-match repo → tier + cited signals -----------------------------------

class TestNoMatchRepoSniff:
    def test_no_match_repo_surfaces_tier_and_signals(self, tmp_path):
        (tmp_path / "main.c").write_text(
            "#include <stdio.h>\n"
            "int main() {\n"
            "    char name[32];\n"
            "    scanf(\"%s\", name);\n"
            "    return 0;\n"
            "}\n"
        )
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["matched"] == []
        assert out["recommended_profile"] is None
        assert out["ui_sniff"]["tier"] >= 1
        assert out["ui_sniff"]["signals"], "expected at least one cited signal"
        citation = out["ui_sniff"]["signals"][0]["citation"]
        assert "main.c" in citation

    def test_schema_version_bumped(self, tmp_path):
        (tmp_path / "README.txt").write_text("hello")
        out = json.loads(_run(tmp_path).stdout)
        assert out["schema_version"] == "22.1.0"


# --- fully-matched repo → zero-cost, sniff_ui never invoked -----------------

class TestFullyMatchedRepoSkipsSniff:
    def test_matched_repo_ui_sniff_is_tier_zero_and_unscanned(self, tmp_path, monkeypatch):
        _delphi_tree(tmp_path)
        spy = _SniffSpy()
        monkeypatch.setattr(dsp._content_sniff_lib, "sniff_ui", spy)

        out = dsp.detect(str(tmp_path), file_cap=50_000, sample_cap=5)

        assert out["recommended_profile"] == "delphi-vcl"
        assert out["ui_sniff"] == {"tier": 0}
        assert spy.calls == [], "sniff_ui must not be invoked on a fully-matched repo (perf contract)"
        assert all(c.get("profile") is not None for c in out["components"]), (
            "fixture has no unrecognized component -- sanity check the fixture, not the wiring"
        )
        assert all("ui_sniff" not in c for c in out["components"])


# --- fix 12: masked profile:None component in an otherwise-matched monorepo -

class TestMaskedComponentSniff:
    def test_per_component_sniff_fires_when_root_already_matched(self, tmp_path, monkeypatch):
        # Root DOES match (web-js-ts via package.json) -- the root-level gate alone would
        # never fire. find_components is monkeypatched to also report one unrecognized,
        # non-reused component (`profile: None`), the masked case fix 12 exists to rescue.
        (tmp_path / "package.json").write_text('{"name":"root"}')
        (tmp_path / "services" / "unknown").mkdir(parents=True)

        synthetic_components = [
            {"path": ".", "profile": "web-js-ts", "role": "service", "group": None},
            {"path": "services/unknown", "profile": None, "role": "service", "group": None},
        ]
        monkeypatch.setattr(dsp, "find_components", lambda *a, **kw: list(synthetic_components))

        spy = _SniffSpy(result={"tier": 2, "signals": [{"family": "menu_loop"}], "summary": "1 signal(s), tier=2"})
        monkeypatch.setattr(dsp._content_sniff_lib, "sniff_ui", spy)

        out = dsp.detect(str(tmp_path), file_cap=50_000, sample_cap=5)

        assert out["matched"] != []                      # root DID match
        assert out["ui_sniff"] == {"tier": 0}             # top-level stays zero-cost
        unknown = next(c for c in out["components"] if c["path"] == "services/unknown")
        assert unknown["ui_sniff"]["tier"] == 2
        matched_component = next(c for c in out["components"] if c["path"] == ".")
        assert "ui_sniff" not in matched_component        # only the None-profile component was sniffed

        # Sniffed exactly the masked component's own path, not the whole root again.
        assert len(spy.calls) == 1
        sniffed_path = spy.calls[0][0]
        assert sniffed_path.endswith(str(Path("services") / "unknown"))

    def test_reused_component_is_not_sniffed(self, tmp_path, monkeypatch):
        (tmp_path / "package.json").write_text('{"name":"root"}')
        synthetic_components = [
            {"path": ".", "profile": "web-js-ts", "role": "service", "group": None},
            {
                "path": "services/legacy", "profile": None, "role": "service", "group": None,
                "status": "reused", "docs_path": "services/legacy/docs",
                "source_sha": "deadbeef", "is_git_root": False,
            },
        ]
        monkeypatch.setattr(dsp, "find_components", lambda *a, **kw: list(synthetic_components))
        spy = _SniffSpy()
        monkeypatch.setattr(dsp._content_sniff_lib, "sniff_ui", spy)

        out = dsp.detect(str(tmp_path), file_cap=50_000, sample_cap=5)

        assert spy.calls == [], "reused components are previously-documented, not unrecognized"
        legacy = next(c for c in out["components"] if c["path"] == "services/legacy")
        assert "ui_sniff" not in legacy


# --- sniff exception guard: detection stays advisory/exit-0 -----------------

class TestSniffExceptionGuard:
    def test_root_level_sniff_exception_is_guarded(self, tmp_path, monkeypatch):
        (tmp_path / "README.txt").write_text("nothing recognizable here")
        spy = _SniffSpy(raise_exc=RuntimeError("boom: unreadable file"))
        monkeypatch.setattr(dsp._content_sniff_lib, "sniff_ui", spy)

        out = dsp.detect(str(tmp_path), file_cap=50_000, sample_cap=5)  # must not raise

        assert out["ui_sniff"]["tier"] == 0
        assert out["ui_sniff"]["error"] == "boom: unreadable file"
        assert out["recommended_profile"] is None

    def test_cli_exits_zero_on_corrupt_or_missing_root(self, tmp_path):
        missing = tmp_path / "does-not-exist"
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(missing)],
            capture_output=True, text=True, timeout=60, cwd=str(tmp_path),
        )
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["ui_sniff"]["tier"] == 0
