"""Atomic JSON merge helpers for `validation-summary.json`. Stdlib only.
Each validator owns one slot under `validators.{name}`.
"""
from __future__ import annotations
import datetime as _dt
import json
import os
from pathlib import Path

SCHEMA_VERSION = 1


def _now() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _seed(plan: str) -> dict:
    return {"schema_version": SCHEMA_VERSION, "generated_at": _now(), "plan": plan, "overall_status": "PASS",
            "totals": {"critical": 0, "warning": 0, "passed_specs": 0, "failed_specs": 0}, "validators": {}}


def load_summary(path: Path, plan_name: str) -> dict:
    """Load existing or seed fresh."""
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("schema_version", SCHEMA_VERSION); data.setdefault("validators", {})
            data.setdefault("totals", {"critical": 0, "warning": 0, "passed_specs": 0, "failed_specs": 0})
            data.setdefault("overall_status", "PASS"); data["plan"] = plan_name; return data
        except (json.JSONDecodeError, OSError):
            pass
    return _seed(plan_name)


def merge_validator_result(summary: dict, validator: str, result: dict) -> dict:
    """Insert/overwrite validator slot. Spec/citation merge per-fcode."""
    summary["generated_at"] = _now()
    if validator == "feature_existence":
        summary["validators"][validator] = {"status": result.get("status", "PASS"),
                                            "summary": result.get("summary", {"critical": 0, "warning": 0}),
                                            "issues": result.get("issues", [])}
        return summary
    specs = summary["validators"].setdefault("specs", {})
    for fcode, entry in result.get("specs", {}).items():
        cur = specs.setdefault(fcode, {"spec_path": "", "status": "PASS",
                                       "summary": {"critical": 0, "warning": 0}, "issues": []})
        cur["spec_path"] = entry.get("spec_path", cur["spec_path"])
        cur["issues"] = [i for i in cur["issues"] if i.get("validator") != validator] + entry.get("issues", [])
        c = sum(1 for i in cur["issues"] if i["severity"] == "critical")
        w = sum(1 for i in cur["issues"] if i["severity"] == "warning")
        cur["summary"] = {"critical": c, "warning": w}
        cur["status"] = "FAIL" if c else ("WARN" if w else "PASS")
    return summary


def recalculate_totals(summary: dict) -> None:
    """Sum across validators + count pass/fail specs."""
    c = w = p = f = 0; fe = summary["validators"].get("feature_existence")
    if fe: c += fe["summary"].get("critical", 0); w += fe["summary"].get("warning", 0)
    for spec in summary["validators"].get("specs", {}).values():
        c += spec["summary"].get("critical", 0); w += spec["summary"].get("warning", 0)
        f += 1 if spec["status"] == "FAIL" else 0; p += 0 if spec["status"] == "FAIL" else 1
    # Include top-level core-artifact validators (explicit allowlist avoids double-counting specs/feature_existence)
    for name in ("route_list", "screen_list", "id_contiguity"):
        slot = summary["validators"].get(name, {})
        slot_summary = slot.get("summary", {})
        c += slot_summary.get("critical", 0); w += slot_summary.get("warning", 0)
    summary["totals"] = {"critical": c, "warning": w, "passed_specs": p, "failed_specs": f}


def derive_overall_status(summary: dict) -> str:
    t = summary["totals"]
    return "FAIL" if t["critical"] or t["failed_specs"] else ("WARN" if t["warning"] else "PASS")


def atomic_write(path: Path, data: dict) -> None:
    """Write `.tmp` next to target, then atomic rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(str(tmp), str(path))
