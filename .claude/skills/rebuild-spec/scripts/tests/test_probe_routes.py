"""Tests for probe_routes.py — Tier-1 CLI route probe.

Coverage:
- Rails text output → manifest rows with stack label
- Laravel JSON output → manifest rows with stack label
- Missing binary → tier1_failed (graceful)
- subprocess.TimeoutExpired → tier1_failed (graceful)
- Non-zero return code → tier1_failed
- Embedded-only (no bootable lockfile) → skipped
- Multi-stack merge (rails + laravel) → combined manifest
- Exit semantics: main() always returns 0
- LISTERS map contains no install commands
- Output byte cap: runaway child killed before OOM (A5)
- Manifest route cap: 5000 limit + truncated flag (A6)
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import probe_routes  # noqa: E402
from probe_routes import (  # noqa: E402
    classify_bootable,
    main,
    probe,
    LISTERS,
    PROBE_TIMEOUT_S,
)
from _probe_routes_lib import (  # noqa: E402
    parse_json_output as _parse_json_output,
    parse_text_output as _parse_text_output,
    MAX_MANIFEST_ROUTES,
    write_manifest,
)


# ---------------------------------------------------------------------------
# FakePopen helper — simulates subprocess.Popen for tests that patch Popen
# ---------------------------------------------------------------------------

class _FakePopen:
    """Minimal Popen mock: stdout returns given bytes, proc exits with given code."""

    def __init__(self, stdout_bytes: bytes, returncode: int = 0, raise_on_popen: Exception | None = None):
        self._raise = raise_on_popen
        self.returncode = returncode
        self.stdout = io.BytesIO(stdout_bytes)
        self.stderr = io.BytesIO(b"")

    def kill(self) -> None:
        pass

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode


def _make_fake_popen(stdout_text: str, returncode: int = 0):
    """Return a Popen constructor that yields a _FakePopen with given output."""
    encoded = stdout_text.encode("utf-8")

    def _popen(cmd, **kwargs):
        return _FakePopen(encoded, returncode=returncode)

    return _popen


def _make_fake_popen_multi(dispatch: dict):
    """Return a Popen constructor that dispatches on cmd content."""
    def _popen(cmd, **kwargs):
        for key, (stdout_text, rc) in dispatch.items():
            if key in cmd:
                return _FakePopen(stdout_text.encode("utf-8"), returncode=rc)
        return _FakePopen(b"", returncode=0)

    return _popen


class _RaisingPopen:
    """Popen that raises an exception during construction (FileNotFoundError/OSError)."""

    def __init__(self, exc: Exception):
        raise exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rails_project(tmp_path: Path) -> Path:
    """Create a minimal Rails project structure."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "Gemfile.lock").write_text("GEM\n  specs:\n", encoding="utf-8")
    (tmp_path / "bin").mkdir(exist_ok=True)
    (tmp_path / "bin" / "rails").write_text("#!/usr/bin/env ruby\n", encoding="utf-8")
    return tmp_path


def _make_laravel_project(tmp_path: Path) -> Path:
    """Create a minimal Laravel project structure."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "composer.lock").write_text('{"packages": []}', encoding="utf-8")
    (tmp_path / "artisan").write_text("<?php\n", encoding="utf-8")
    return tmp_path


def _make_phoenix_project(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "mix.lock").write_text("%{}\n", encoding="utf-8")
    return tmp_path


def _make_plan_dir(tmp_path: Path) -> Path:
    plan = tmp_path / "plans" / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    return plan


# ---------------------------------------------------------------------------
# LISTERS integrity: no install commands
# ---------------------------------------------------------------------------

class TestListersIntegrity:
    FORBIDDEN = ("install", "update", "upgrade", "require", "add")

    def test_no_install_commands_in_any_lister(self):
        for stack, defn in LISTERS.items():
            for token in defn.get("cmd", []):
                for bad in self.FORBIDDEN:
                    assert bad not in token.lower(), (
                        f"LISTERS[{stack!r}].cmd contains forbidden token {token!r}"
                    )

    def test_all_listers_have_cmd_list(self):
        for stack, defn in LISTERS.items():
            assert isinstance(defn.get("cmd"), list), f"LISTERS[{stack!r}].cmd must be a list"
            assert len(defn["cmd"]) > 0, f"LISTERS[{stack!r}].cmd must not be empty"

    def test_known_stacks_present(self):
        expected = {"rails", "laravel", "phoenix", "symfony", "django"}
        assert expected.issubset(set(LISTERS.keys()))


# ---------------------------------------------------------------------------
# classify_bootable
# ---------------------------------------------------------------------------

class TestClassifyBootable:
    def test_rails_lockfile_detected(self, tmp_path):
        (tmp_path / "Gemfile.lock").write_text("", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "rails" in result

    def test_laravel_lockfile_detected(self, tmp_path):
        (tmp_path / "composer.lock").write_text("{}", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "laravel" in result

    def test_phoenix_lockfile_detected(self, tmp_path):
        (tmp_path / "mix.lock").write_text("%{}", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "phoenix" in result

    def test_no_lockfile_returns_empty(self, tmp_path):
        result = classify_bootable(tmp_path)
        assert result == []

    def test_embedded_only_stack_never_in_result(self, tmp_path):
        """ColdFusion and other embedded shims have no lockfile entry — never bootable."""
        # Simulate a project with only a ColdFusion marker (no known lockfile)
        (tmp_path / "Application.cfc").write_text("", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert result == []

    def test_multi_lockfile_returns_all(self, tmp_path):
        (tmp_path / "Gemfile.lock").write_text("", encoding="utf-8")
        (tmp_path / "mix.lock").write_text("%{}", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "rails" in result
        assert "phoenix" in result

    # --- H2: Django requires manage.py AND a dep manifest ---

    def test_django_manage_py_alone_not_bootable(self, tmp_path):
        """H2: manage.py alone must NOT classify django as bootable — not a lockfile."""
        (tmp_path / "manage.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "django" not in result, (
            "manage.py alone should not trigger django bootable classification"
        )

    def test_django_manage_py_plus_requirements_txt_bootable(self, tmp_path):
        """H2: manage.py + requirements.txt → django is bootable."""
        (tmp_path / "manage.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
        (tmp_path / "requirements.txt").write_text("django>=4.0\n", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "django" in result

    def test_django_manage_py_plus_pyproject_toml_bootable(self, tmp_path):
        """H2: manage.py + pyproject.toml → django is bootable."""
        (tmp_path / "manage.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "django" in result

    def test_django_manage_py_plus_poetry_lock_bootable(self, tmp_path):
        """H2: manage.py + poetry.lock → django is bootable."""
        (tmp_path / "manage.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
        (tmp_path / "poetry.lock").write_text("# poetry\n", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "django" in result

    # --- M1: Symfony detected via composer.lock + bin/console ---

    def test_symfony_detected_when_bin_console_present(self, tmp_path):
        """M1: composer.lock + bin/console → symfony is bootable."""
        (tmp_path / "composer.lock").write_text("{}", encoding="utf-8")
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin" / "console").write_text("#!/usr/bin/env php\n", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "symfony" in result

    def test_symfony_not_detected_without_bin_console(self, tmp_path):
        """M1: composer.lock alone (no bin/console) → symfony NOT in result; laravel IS."""
        (tmp_path / "composer.lock").write_text("{}", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "symfony" not in result
        assert "laravel" in result

    def test_laravel_and_symfony_both_detected_when_both_entrypoints_present(self, tmp_path):
        """M1: composer.lock + artisan + bin/console → both laravel and symfony bootable."""
        (tmp_path / "composer.lock").write_text("{}", encoding="utf-8")
        (tmp_path / "artisan").write_text("<?php\n", encoding="utf-8")
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin" / "console").write_text("#!/usr/bin/env php\n", encoding="utf-8")
        result = classify_bootable(tmp_path)
        assert "laravel" in result
        assert "symfony" in result


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

class TestParsers:
    def test_parse_json_laravel_format(self):
        data = [
            {"method": "GET", "uri": "/api/users", "action": "UserController@index"},
            {"method": "POST", "uri": "/api/users", "action": "UserController@store"},
        ]
        routes = _parse_json_output(json.dumps(data), "laravel")
        assert len(routes) == 2
        assert routes[0]["method"] == "GET"
        assert routes[0]["path"] == "/api/users"
        assert routes[0]["handler"] == "UserController@index"
        assert routes[0]["stack"] == "laravel"

    def test_parse_json_empty_list(self):
        routes = _parse_json_output("[]", "laravel")
        assert routes == []

    def test_parse_json_invalid(self):
        routes = _parse_json_output("not json", "laravel")
        assert routes == []

    def test_parse_json_non_list(self):
        routes = _parse_json_output('{"routes": []}', "laravel")
        assert routes == []

    def test_parse_text_rails_format(self):
        raw = """\
                                   Prefix Verb   URI Pattern                 Controller#Action
                                     root GET    /                           home#index
                                    users GET    /users(.:format)            users#index
                                          POST   /users(.:format)            users#create
"""
        routes = _parse_text_output(raw, "rails")
        # Should parse lines with recognized HTTP verbs
        methods = {r["method"] for r in routes}
        assert "GET" in methods or "POST" in methods

    def test_parse_text_attaches_stack_label(self):
        raw = "GET  /api/health  HealthController#check"
        routes = _parse_text_output(raw, "rails")
        assert all(r["stack"] == "rails" for r in routes)

    def test_parse_text_skips_blank_and_comment_lines(self):
        raw = "\n# comment\n\nGET /health HealthCheck\n"
        routes = _parse_text_output(raw, "rails")
        paths = [r["path"] for r in routes]
        assert "/health" in paths


# ---------------------------------------------------------------------------
# probe() integration (monkeypatched subprocess)
# ---------------------------------------------------------------------------

RAILS_TEXT_OUTPUT = """\
Prefix Verb   URI Pattern          Controller#Action
root   GET    /                    home#index
       POST   /sessions(.:format)  sessions#create
"""

LARAVEL_JSON_OUTPUT = json.dumps([
    {"method": "GET", "uri": "/api/users", "action": "App\\Http\\Controllers\\UserController@index"},
    {"method": "POST", "uri": "/api/users", "action": "App\\Http\\Controllers\\UserController@store"},
])


class TestProbeHappyPath:
    def test_rails_ok_writes_manifest(self, tmp_path, monkeypatch):
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        monkeypatch.setattr(probe_routes.subprocess, "Popen", _make_fake_popen(RAILS_TEXT_OUTPUT))
        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_ok"
        assert result["manifest_path"] is not None
        assert result["per_stack"]["rails"]["status"] == "tier1_ok"
        # Verify manifest file exists
        assert Path(result["manifest_path"]).exists()

    def test_manifest_json_has_stack_label(self, tmp_path, monkeypatch):
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        monkeypatch.setattr(probe_routes.subprocess, "Popen", _make_fake_popen(RAILS_TEXT_OUTPUT))
        result = probe(project, plan, ["rails"])

        routes = json.loads(Path(result["manifest_path"]).read_text())
        assert all(r["stack"] == "rails" for r in routes)

    def test_laravel_json_format(self, tmp_path, monkeypatch):
        project = _make_laravel_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        # Simulate php binary present (not available in CI)
        monkeypatch.setattr(probe_routes.shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(probe_routes.subprocess, "Popen", _make_fake_popen(LARAVEL_JSON_OUTPUT))
        result = probe(project, plan, ["laravel"])

        assert result["status"] == "tier1_ok"
        routes = json.loads(Path(result["manifest_path"]).read_text())
        assert len(routes) == 2
        assert all(r["stack"] == "laravel" for r in routes)

    def test_multi_stack_merge(self, tmp_path, monkeypatch):
        """Rails + Laravel both present → merged manifest with both stack labels."""
        project = tmp_path / "project"
        project.mkdir()
        _make_rails_project(project)
        # Add composer.lock for laravel too
        (project / "composer.lock").write_text("{}", encoding="utf-8")
        plan = _make_plan_dir(tmp_path)

        # Simulate php binary present (not available in CI/dev box)
        monkeypatch.setattr(probe_routes.shutil, "which", lambda name: f"/usr/bin/{name}")

        monkeypatch.setattr(
            probe_routes.subprocess,
            "Popen",
            _make_fake_popen_multi({
                "routes": (RAILS_TEXT_OUTPUT, 0),
                "route:list": (LARAVEL_JSON_OUTPUT, 0),
            }),
        )
        result = probe(project, plan, ["rails", "laravel"])

        assert result["status"] == "tier1_ok"
        routes = json.loads(Path(result["manifest_path"]).read_text())
        stacks_in_manifest = {r["stack"] for r in routes}
        assert "rails" in stacks_in_manifest
        assert "laravel" in stacks_in_manifest


class TestProbeFailurePaths:
    def test_missing_binary_returns_tier1_failed(self, tmp_path, monkeypatch):
        """Stack lockfile present but binary absent → tier1_failed, no crash."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "Gemfile.lock").write_text("", encoding="utf-8")
        # No bin/rails file, shutil.which returns None
        monkeypatch.setattr(probe_routes.shutil, "which", lambda _: None)
        plan = _make_plan_dir(tmp_path)

        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_failed"
        assert result["per_stack"]["rails"]["status"] == "tier1_failed"
        assert result["manifest_path"] is None

    def test_timeout_returns_tier1_failed(self, tmp_path, monkeypatch):
        """proc.wait(timeout=60) raises TimeoutExpired → tier1_failed, never crash, exit 0."""
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        class _TimeoutPopen(_FakePopen):
            def wait(self, timeout=None):
                raise subprocess.TimeoutExpired(["bin/rails", "routes"], PROBE_TIMEOUT_S)

        monkeypatch.setattr(
            probe_routes.subprocess, "Popen",
            lambda cmd, **kw: _TimeoutPopen(b"", returncode=0),
        )
        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_failed"
        assert result["per_stack"]["rails"]["status"] == "tier1_failed"
        assert result["manifest_path"] is None

    def test_nonzero_returncode_returns_tier1_failed(self, tmp_path, monkeypatch):
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        monkeypatch.setattr(probe_routes.subprocess, "Popen", _make_fake_popen("", returncode=1))
        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_failed"

    def test_unparseable_output_returns_tier1_failed(self, tmp_path, monkeypatch):
        """Lister returns exit 0 but output can't be parsed into routes."""
        project = _make_laravel_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        # Returns exit 0 but malformed JSON for laravel (json format)
        monkeypatch.setattr(probe_routes.subprocess, "Popen", _make_fake_popen("not-json-at-all"))
        result = probe(project, plan, ["laravel"])

        assert result["status"] == "tier1_failed"

    def test_oserror_returns_tier1_failed(self, tmp_path, monkeypatch):
        """OSError during Popen construction → tier1_failed, never crash."""
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        def _raising_popen(cmd, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(probe_routes.subprocess, "Popen", _raising_popen)
        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_failed"


class TestProbeSkippedPaths:
    def test_no_bootable_stacks_returns_skipped(self, tmp_path):
        """No lockfiles present → skipped status (not tier1_failed)."""
        project = tmp_path / "project"
        project.mkdir()
        plan = _make_plan_dir(tmp_path)

        result = probe(project, plan)

        assert result["status"] == "skipped"
        assert result["manifest_path"] is None
        assert result["stacks_probed"] == []

    def test_requested_stack_not_bootable_returns_skipped(self, tmp_path):
        """Explicit --stacks arg for stack without lockfile → skipped."""
        project = tmp_path / "project"
        project.mkdir()
        # No Gemfile.lock → rails not bootable
        plan = _make_plan_dir(tmp_path)

        result = probe(project, plan, ["rails"])

        assert result["status"] == "skipped"

    def test_embedded_only_project_returns_skipped(self, tmp_path):
        """Project with only ColdFusion marker → no bootable stacks → skipped."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "Application.cfc").write_text("", encoding="utf-8")
        plan = _make_plan_dir(tmp_path)

        result = probe(project, plan)

        assert result["status"] == "skipped"


# ---------------------------------------------------------------------------
# main() CLI — always exits 0
# ---------------------------------------------------------------------------

class TestMainCli:
    def test_main_always_exits_0_on_no_stacks(self, tmp_path, capsys):
        project = tmp_path / "empty"
        project.mkdir()
        plan = _make_plan_dir(tmp_path)

        rc = main([
            "--project-root", str(project),
            "--plan-dir", str(plan),
        ])

        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "skipped"

    def test_main_outputs_valid_json(self, tmp_path, capsys):
        project = tmp_path / "empty"
        project.mkdir()
        plan = _make_plan_dir(tmp_path)

        rc = main([
            "--project-root", str(project),
            "--plan-dir", str(plan),
            "--stacks", "rails",
        ])

        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "status" in parsed
        assert "manifest_path" in parsed
        assert "stacks_probed" in parsed
        assert "per_stack" in parsed

    def test_main_tier1_failed_still_exits_0(self, tmp_path, capsys, monkeypatch):
        """Even on tier1_failed, exit code is 0 (advisory)."""
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        class _TimeoutPopen(_FakePopen):
            def wait(self, timeout=None):
                raise subprocess.TimeoutExpired(["bin/rails", "routes"], 60)

        monkeypatch.setattr(
            probe_routes.subprocess, "Popen",
            lambda cmd, **kw: _TimeoutPopen(b"", returncode=0),
        )

        rc = main([
            "--project-root", str(project),
            "--plan-dir", str(plan),
            "--stacks", "rails",
        ])

        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "tier1_failed"

    def test_main_stacks_comma_split(self, tmp_path, capsys, monkeypatch):
        """--stacks 'rails,laravel' → probes both if lockfiles present."""
        project = tmp_path / "project"
        project.mkdir()
        _make_rails_project(project)
        (project / "composer.lock").write_text("{}", encoding="utf-8")
        plan = _make_plan_dir(tmp_path)

        monkeypatch.setattr(
            probe_routes.subprocess,
            "Popen",
            _make_fake_popen_multi({
                "routes": (RAILS_TEXT_OUTPUT, 0),
                "route:list": (LARAVEL_JSON_OUTPUT, 0),
            }),
        )

        rc = main([
            "--project-root", str(project),
            "--plan-dir", str(plan),
            "--stacks", "rails,laravel",
        ])

        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        # At least one stack probed
        assert len(out["stacks_probed"]) >= 1


# ---------------------------------------------------------------------------
# A5: output byte cap — runaway child killed before OOM
# ---------------------------------------------------------------------------

class TestOutputByteCap:
    """A5: Popen stdout capped at MAX_PROBE_OUTPUT_BYTES; kills process, returns tier1_failed."""

    def test_chatty_binary_returns_tier1_failed_quickly(self, tmp_path, monkeypatch):
        """A5: child emitting endless lines is killed by byte cap, not 60s wall-clock."""
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        # Produce just over MAX_PROBE_OUTPUT_BYTES in one large read call.
        # The real read loop uses 64 KB chunks — we emit one chunk well over the cap.
        import probe_routes as _pr
        cap = _pr.MAX_PROBE_OUTPUT_BYTES

        class _GiantPopen(_FakePopen):
            """stdout yields a block larger than cap in one read, then EOF."""
            def __init__(self):
                # Build a BytesIO with enough data to exceed cap in the first 64 KB read
                # by repeating a short line until we're over cap+64KB.
                line = b"GET /route/x Handler\n"
                count = (cap // len(line)) + 2
                self.returncode = 0
                self.stdout = io.BytesIO(line * count)
                self.stderr = io.BytesIO(b"")

            def kill(self):
                # mark killed so we can verify it was called
                self.returncode = -9

            def wait(self, timeout=None):
                return self.returncode

        instance = _GiantPopen()
        monkeypatch.setattr(probe_routes.subprocess, "Popen", lambda cmd, **kw: instance)
        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_failed"
        # kill() was called (returncode set to -9 by our mock)
        assert instance.returncode == -9

    def test_normal_output_under_cap_succeeds(self, tmp_path, monkeypatch):
        """A5: small output well under cap → tier1_ok as normal."""
        project = _make_rails_project(tmp_path / "project")
        plan = _make_plan_dir(tmp_path)

        monkeypatch.setattr(probe_routes.subprocess, "Popen", _make_fake_popen(RAILS_TEXT_OUTPUT))
        result = probe(project, plan, ["rails"])

        assert result["status"] == "tier1_ok"


# ---------------------------------------------------------------------------
# A6: manifest route cap — 5000 limit + truncated flag
# ---------------------------------------------------------------------------

class TestManifestRouteCap:
    """A6: write_manifest truncates at MAX_MANIFEST_ROUTES, sets truncated+total_routes."""

    def test_5001_routes_truncated_to_5000(self, tmp_path):
        """A6: 5001 fake routes → manifest has 5000 entries, truncated=true, total_routes=5001."""
        plan = _make_plan_dir(tmp_path)
        routes = [
            {"method": "GET", "path": f"/route/{i}", "handler": f"Handler{i}", "stack": "rails"}
            for i in range(5001)
        ]
        manifest_path = write_manifest(routes, plan)

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), "Truncated manifest must be a JSON object, not a list"
        assert data["truncated"] is True
        assert data["total_routes"] == 5001
        assert len(data["routes"]) == MAX_MANIFEST_ROUTES

    def test_5001_routes_txt_has_warning(self, tmp_path):
        """A6: .txt manifest must contain a warning line when truncated."""
        plan = _make_plan_dir(tmp_path)
        routes = [
            {"method": "GET", "path": f"/route/{i}", "handler": f"Handler{i}", "stack": "rails"}
            for i in range(5001)
        ]
        write_manifest(routes, plan)
        txt = (plan / "artifacts" / "route-manifest.txt").read_text(encoding="utf-8")
        assert "WARNING" in txt
        assert "truncated" in txt.lower()

    def test_5000_routes_not_truncated(self, tmp_path):
        """A6: exactly 5000 routes → not truncated, manifest is a plain list."""
        plan = _make_plan_dir(tmp_path)
        routes = [
            {"method": "GET", "path": f"/route/{i}", "handler": f"H{i}", "stack": "rails"}
            for i in range(5000)
        ]
        manifest_path = write_manifest(routes, plan)

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert isinstance(data, list), "Exactly-at-cap manifest must be a plain list"
        assert len(data) == 5000
