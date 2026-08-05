"""E2E (Phase 06): Ishindenshin-shape repo → detect → manifest → sidecar → auto-switch chain.

Mirrors the real shape (multi-executable Delphi + shared Common + sibling DB tree) and asserts the
whole detection→manifest→shared-sidecar→auto-switch chain end to end through the actual CLI — not
just the unit pieces. No live Ishindenshin regen (per plan scope); a tmp fixture stands in.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "detect_stack_profile.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import _components_manifest_lib as mlib  # noqa: E402


def _ishindenshin_fixture(root: Path) -> list[str]:
    """PG/<MOD>/*.dpr executables + shared PG/Common (no .dpr) + sibling DB/{TABLE,SP}/<MOD>."""
    modules = ["POS", "RSV", "INV"]
    for m in modules:
        d = root / "PG" / m
        d.mkdir(parents=True)
        (d / f"{m}main61.dpr").write_text("program X; begin end.")
        (d / f"{m}unit.pas").write_text("unit U; interface implementation end.")
    common = root / "PG" / "Common"
    common.mkdir(parents=True)
    (common / "DBACC.pas").write_text("unit DBACC; interface implementation end.")
    for m in modules:
        t = root / "DB" / "TABLE" / m
        t.mkdir(parents=True)
        (t / f"M_{m}_HEAD.sql").write_text("create table x (id number);")
        sp = root / "DB" / "SP" / m
        sp.mkdir(parents=True)
        (sp / f"P_{m}.pks").write_text("create or replace package x is end;")
        (sp / f"P_{m}.pkb").write_text("create or replace package body x is end;")
    return modules


def _run(root: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)] + (extra or []),
        capture_output=True, text=True, timeout=60, cwd=str(root),
    )


def test_e2e_detection_chain(tmp_path):
    modules = _ishindenshin_fixture(tmp_path)
    out = json.loads(_run(tmp_path).stdout)

    # profile + component_profile
    assert out["recommended_profile"] in ("delphi-vcl", "oracle-plsql")  # hits may tip either way
    assert out["component_profile"] == "delphi-vcl"

    # find_components = the N PG modules only — no Common, no DB.
    paths = {c["path"] for c in out["components"]}
    assert paths == {f"PG/{m}" for m in modules}

    # shared[] = Common (source) + DB (db)
    shared = {s["label"]: s["kind"] for s in out["shared"]}
    assert shared == {"Common": "source", "DB": "db"}

    # auto_switch fires
    assert out["auto_switch"] is True


def test_e2e_mono_flips_autoswitch(tmp_path):
    _ishindenshin_fixture(tmp_path)
    out = json.loads(_run(tmp_path, ["--mono"]).stdout)
    assert out["auto_switch"] is False


def test_e2e_emit_manifest_and_sidecar(tmp_path):
    _ishindenshin_fixture(tmp_path)
    manifest = tmp_path / ".rebuild-components.json"
    r = _run(tmp_path, ["--emit-manifest", "--manifest", str(manifest)])
    assert r.returncode == 0, r.stderr
    status = json.loads(r.stdout)
    assert status["status"] == "manifest_emitted"
    assert status["components"] == 3
    assert status["shared"] == 2

    # Component manifest is a JSON ARRAY (consumers untouched).
    entries = mlib.load_manifest(str(manifest), str(tmp_path))
    assert isinstance(entries, list)
    assert {e["path"] for e in entries} == {"PG/POS", "PG/RSV", "PG/INV"}

    # Shared sidecar written alongside, kinds routed correctly.
    sidecar = Path(mlib.shared_sidecar_path(str(manifest)))
    assert sidecar.exists()
    shared = mlib.load_shared_sidecar(str(sidecar), str(tmp_path))
    by_label = {s["label"]: s["kind"] for s in shared}
    assert by_label == {"Common": "source", "DB": "db"}
