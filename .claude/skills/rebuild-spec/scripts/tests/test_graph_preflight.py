"""Tests for scripts/graph_preflight.py — deterministic graphify preflight (default-ON).

The Knowledge Graph is ON by default. The script no-ops only when disabled via config
(graphify.enabled=false) or env (GRAPHIFY_DISABLE=1 / REBUILD_NO_GRAPH=1). Every run
exits 0; when enabled but graphify is unavailable it degrades to "vanilla".
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "graph_preflight.py"

# The "enabled but graphify unavailable -> degrade" tests only make sense when graphify
# is actually absent. If it IS installed (e.g. CI's kit venv), running them would do real
# work (graphify update .) with side effects on the runner — so skip them there.
_GRAPHIFY_PRESENT = importlib.util.find_spec("graphify") is not None
_needs_no_graphify = pytest.mark.skipif(
    _GRAPHIFY_PRESENT, reason="degrade-path test requires graphify to be absent"
)


def _run(cwd, env_extra=None, args=None):
    env = dict(os.environ)
    # Isolate HOME so a real ~/.claude/.tkm.json can't influence the default-on assertions.
    home = Path(cwd) / "_home"
    home.mkdir(exist_ok=True)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(args or [])],
        capture_output=True, text=True, timeout=60, cwd=str(cwd), env=env,
    )


def _write_cfg(cwd, enabled):
    d = Path(cwd) / ".claude"
    d.mkdir(parents=True, exist_ok=True)
    (d / ".tkm.json").write_text(json.dumps({"graphify": {"enabled": enabled}}), encoding="utf-8")


def _write_cfg_takumi(cwd, enabled):
    """Write graphify.enabled to .claude/.takumi.json — the file the tkm CLI writes."""
    d = Path(cwd) / ".claude"
    d.mkdir(parents=True, exist_ok=True)
    (d / ".takumi.json").write_text(json.dumps({"graphify": {"enabled": enabled}}), encoding="utf-8")


def test_env_graphify_disable_noop(tmp_path):
    """GRAPHIFY_DISABLE=1 -> disabled: exits 0, builds NO graph, no .gitignore."""
    r = _run(tmp_path, {"GRAPHIFY_DISABLE": "1"})
    assert r.returncode == 0, r.stderr
    assert "disabled" in r.stdout.lower()
    assert not (tmp_path / "graphify-out").exists()
    assert not (tmp_path / ".gitignore").exists()


def test_env_rebuild_no_graph_noop(tmp_path):
    """REBUILD_NO_GRAPH=1 -> disabled (hard opt-out), builds NO graph."""
    r = _run(tmp_path, {"REBUILD_NO_GRAPH": "1"})
    assert r.returncode == 0, r.stderr
    assert "disabled" in r.stdout.lower()
    assert not (tmp_path / "graphify-out").exists()


def test_config_disable_noop(tmp_path):
    """Config graphify.enabled=false -> disabled with the config reason; no build/.gitignore."""
    _write_cfg(tmp_path, False)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "disabled" in r.stdout.lower()
    assert "graphify.enabled" in r.stdout
    assert not (tmp_path / "graphify-out").exists()
    assert not (tmp_path / ".gitignore").exists()


def test_config_disable_via_takumi_json(tmp_path):
    """graphify.enabled=false in .claude/.takumi.json (what `tkm graphify off` writes)
    also disables — the KG-scoped bridge to the CLI's config file."""
    _write_cfg_takumi(tmp_path, False)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "disabled" in r.stdout.lower()
    assert not (tmp_path / "graphify-out").exists()


def test_env_opt_out_does_not_touch_gitignore(tmp_path):
    """A disabled run must not create/modify .gitignore."""
    _run(tmp_path, {"GRAPHIFY_DISABLE": "1"})
    assert not (tmp_path / ".gitignore").exists()


@_needs_no_graphify
def test_default_on_degrades_when_unavailable(tmp_path):
    """No env/config -> ON by default. graphify absent + offline install -> degrade, exit 0.
    Must NOT be gated off (no 'disabled' status)."""
    r = _run(tmp_path, {"PIP_NO_INDEX": "1"})
    assert r.returncode == 0, r.stderr
    assert "disabled" not in r.stdout.lower()
    assert "vanilla" in r.stdout.lower()


@_needs_no_graphify
def test_config_enabled_true_degrades_when_unavailable(tmp_path):
    """Explicit graphify.enabled=true behaves like the default (enabled)."""
    _write_cfg(tmp_path, True)
    r = _run(tmp_path, {"PIP_NO_INDEX": "1"})
    assert r.returncode == 0, r.stderr
    assert "disabled" not in r.stdout.lower()
