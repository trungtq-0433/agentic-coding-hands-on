"""Calibration engine: analyze historical data and propose KB adjustments."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from agentic_estimate.utils.historical_data_loader import (
    _load_calibration_config,
    load_all_entries,
)
from agentic_estimate.utils.knowledge_base_loader_yaml_config import (
    _get_project_root,
    _load_yaml,
)


@dataclass
class ParameterDiff:
    category: str
    key: str
    current: float
    proposed: float
    change_pct: float
    samples: int
    median: float
    iqr: tuple[float, float]
    confidence: str
    sources: list[str] = field(default_factory=list)


@dataclass
class CalibrationReport:
    generated_date: str
    total_accepted: int
    total_actuals: int
    diffs: list[ParameterDiff] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CalibrationEngine:
    def __init__(self, config_path: str | None = None):
        if config_path:
            with open(config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = _load_calibration_config()

        self.weights_cfg = self.config.get("weights", {})
        self.thresholds = self.config.get("thresholds", {})
        self.algorithm = self.config.get("algorithm", "weighted_median")
        self.blending = self.config.get("blending", {})

        self._kb_base_efforts = _load_yaml(
            "knowledge-base/base-efforts-man-days-per-task-type.yaml"
        )
        self._kb_role_splits = _load_yaml("knowledge-base/role-split-heuristics.yaml")

    def _compute_weight(self, entry: dict) -> float:
        entry_type = entry.get("type", "accepted")
        base = self.weights_cfg.get(entry_type, 1.0)
        decay = self.weights_cfg.get("recency_decay", 0.9)
        date_str = entry.get("project", {}).get("date", "")
        if date_str:
            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                years_old = (datetime.now() - entry_date).days / 365.25
                base *= decay**years_old
            except ValueError:
                pass
        return base

    def _collect_base_effort_samples(
        self, entries: list[dict]
    ) -> dict[str, list[tuple[float, float, str]]]:
        """Collect (value, weight, source) per task_type for base effort analysis."""
        samples: dict[str, list[tuple[float, float, str]]] = {}
        for entry in entries:
            w = self._compute_weight(entry)
            slug = entry.get("project", {}).get("name", "?")
            for task in entry.get("estimate", {}).get("tasks", []):
                tt = task.get("task_type", "")
                if not tt or tt == "unclassified":
                    continue
                total_md = task.get("total_md", 0)
                if total_md > 0:
                    samples.setdefault(tt, []).append((total_md, w, slug))
        return samples

    def _collect_role_split_samples(
        self, entries: list[dict]
    ) -> dict[str, dict[str, list[tuple[float, float, str]]]]:
        """Collect role split ratios per task_type."""
        samples: dict[str, dict[str, list[tuple[float, float, str]]]] = {}
        for entry in entries:
            w = self._compute_weight(entry)
            slug = entry.get("project", {}).get("name", "?")
            for task in entry.get("estimate", {}).get("tasks", []):
                tt = task.get("task_type", "")
                if not tt or tt == "unclassified":
                    continue
                effort = task.get("effort", {})
                total_md = task.get("total_md", 0)
                if total_md <= 0 or not effort:
                    continue
                for role, md in effort.items():
                    ratio = md / total_md
                    samples.setdefault(tt, {}).setdefault(role, []).append((ratio, w, slug))
        return samples

    def _collect_buffer_samples(self, entries: list[dict]) -> list[tuple[float, float, str]]:
        """Collect estimate accuracy ratios from Type A entries."""
        samples = []
        for entry in entries:
            if entry.get("type") != "actual":
                continue
            est_md = entry.get("estimate", {}).get("total_md", 0)
            act_md = entry.get("actual", {}).get("total_md", 0)
            if est_md > 0 and act_md > 0:
                w = self._compute_weight(entry)
                slug = entry.get("project", {}).get("name", "?")
                samples.append((act_md / est_md, w, slug))
        return samples

    @staticmethod
    def weighted_median(samples: list[tuple[float, float]]) -> float:
        if not samples:
            return 0.0
        sorted_s = sorted(samples, key=lambda x: x[0])
        total_w = sum(w for _, w in sorted_s)
        if total_w == 0:
            return sorted_s[len(sorted_s) // 2][0]
        cumulative = 0.0
        for value, weight in sorted_s:
            cumulative += weight
            if cumulative >= total_w / 2:
                return value
        return sorted_s[-1][0]

    @staticmethod
    def weighted_mean(samples: list[tuple[float, float]]) -> float:
        if not samples:
            return 0.0
        total_w = sum(w for _, w in samples)
        if total_w == 0:
            return sum(v for v, _ in samples) / len(samples)
        return sum(v * w for v, w in samples) / total_w

    @staticmethod
    def bayesian_blend(
        observed: float, kb_default: float, n_samples: int, prior_strength: int
    ) -> float:
        return (kb_default * prior_strength + observed * n_samples) / (prior_strength + n_samples)

    @staticmethod
    def compute_iqr(values: list[float]) -> tuple[float, float]:
        if len(values) < 2:
            return (values[0], values[0]) if values else (0.0, 0.0)
        s = sorted(values)
        n = len(s)
        q1 = s[n // 4]
        q3 = s[(3 * n) // 4]
        return (round(q1, 2), round(q3, 2))

    @staticmethod
    def confidence_level(n: int) -> str:
        if n < 5:
            return "low"
        if n <= 15:
            return "medium"
        return "high"

    def _aggregate(self, samples: list[tuple[float, float]]) -> float:
        if self.algorithm == "weighted_mean":
            return self.weighted_mean(samples)
        return self.weighted_median(samples)

    def analyze(self, entries: list[dict] | None = None) -> CalibrationReport:
        if entries is None:
            entries = load_all_entries()

        report = CalibrationReport(
            generated_date=datetime.now().strftime("%Y-%m-%d"),
            total_accepted=sum(1 for e in entries if e.get("type") == "accepted"),
            total_actuals=sum(1 for e in entries if e.get("type") == "actual"),
        )

        if not entries:
            report.warnings.append("No historical entries found.")
            return report

        min_samples = self.thresholds.get("min_samples", 2)
        sig_pct = self.thresholds.get("significance_pct", 10)
        prior_strength = self.blending.get("prior_strength", 5)

        # Base effort analysis
        base_samples = self._collect_base_effort_samples(entries)
        for task_type, type_samples in base_samples.items():
            if len(type_samples) < min_samples:
                report.warnings.append(
                    f"{task_type}: only {len(type_samples)} sample(s), skipped (min={min_samples})"
                )
                continue

            kb_default = self._get_kb_base_effort(task_type)
            if kb_default is None:
                continue

            vw = [(v, w) for v, w, _ in type_samples]
            observed = self._aggregate(vw)
            blended = self.bayesian_blend(observed, kb_default, len(type_samples), prior_strength)
            blended = round(blended, 2)

            change_pct = ((blended - kb_default) / kb_default * 100) if kb_default else 0

            if abs(change_pct) >= sig_pct:
                values = [v for v, _, _ in type_samples]
                sources = list({s for _, _, s in type_samples})
                report.diffs.append(
                    ParameterDiff(
                        category="base_efforts",
                        key=task_type,
                        current=kb_default,
                        proposed=blended,
                        change_pct=round(change_pct, 1),
                        samples=len(type_samples),
                        median=round(self.weighted_median(vw), 2),
                        iqr=self.compute_iqr(values),
                        confidence=self.confidence_level(len(type_samples)),
                        sources=sources,
                    )
                )
            else:
                report.unchanged.append(f"base_efforts.{task_type}")

        # Role split analysis
        role_samples = self._collect_role_split_samples(entries)
        for task_type, roles in role_samples.items():
            kb_splits = self._get_kb_role_splits(task_type)
            if not kb_splits:
                continue
            for role, r_samples in roles.items():
                if len(r_samples) < min_samples:
                    continue
                kb_val = kb_splits.get(role, 0)
                if kb_val == 0:
                    continue

                vw = [(v, w) for v, w, _ in r_samples]
                observed = self._aggregate(vw)
                blended = self.bayesian_blend(observed, kb_val, len(r_samples), prior_strength)
                blended = round(blended, 3)
                change_pct = ((blended - kb_val) / kb_val * 100) if kb_val else 0

                if abs(change_pct) >= sig_pct:
                    values = [v for v, _, _ in r_samples]
                    sources = list({s for _, _, s in r_samples})
                    report.diffs.append(
                        ParameterDiff(
                            category="role_splits",
                            key=f"{task_type}.{role}",
                            current=kb_val,
                            proposed=blended,
                            change_pct=round(change_pct, 1),
                            samples=len(r_samples),
                            median=round(self.weighted_median(vw), 3),
                            iqr=self.compute_iqr(values),
                            confidence=self.confidence_level(len(r_samples)),
                            sources=sources,
                        )
                    )
                else:
                    report.unchanged.append(f"role_splits.{task_type}.{role}")

        # Buffer analysis from actuals
        buffer_samples = self._collect_buffer_samples(entries)
        if len(buffer_samples) >= min_samples:
            kb_buffer = self._kb_base_efforts.get("buffer", {})
            default_buffer = kb_buffer.get("standard", 0.25) if kb_buffer else 0.25
            vw = [(v, w) for v, w, _ in buffer_samples]
            observed_ratio = self._aggregate(vw)
            implied_buffer = max(0, observed_ratio - 1.0)
            blended = self.bayesian_blend(
                implied_buffer, default_buffer, len(buffer_samples), prior_strength
            )
            blended = round(blended, 3)
            change_pct = (
                ((blended - default_buffer) / default_buffer * 100) if default_buffer else 0
            )

            if abs(change_pct) >= sig_pct:
                values = [v for v, _, _ in buffer_samples]
                sources = list({s for _, _, s in buffer_samples})
                report.diffs.append(
                    ParameterDiff(
                        category="buffer",
                        key="standard",
                        current=default_buffer,
                        proposed=blended,
                        change_pct=round(change_pct, 1),
                        samples=len(buffer_samples),
                        median=round(self.weighted_median(vw), 3),
                        iqr=self.compute_iqr(values),
                        confidence=self.confidence_level(len(buffer_samples)),
                        sources=sources,
                    )
                )
            else:
                report.unchanged.append("buffer.standard")
        elif buffer_samples:
            report.warnings.append(f"buffer: only {len(buffer_samples)} actual(s), skipped")

        return report

    def apply_changes(self, diffs: list[ParameterDiff]) -> list[str]:
        """Apply approved diffs to KB YAML files. Returns modified file paths."""
        root = _get_project_root()
        modified = []

        by_category: dict[str, list[ParameterDiff]] = {}
        for d in diffs:
            by_category.setdefault(d.category, []).append(d)

        if "base_efforts" in by_category:
            path = root / "knowledge-base/base-efforts-man-days-per-task-type.yaml"
            data = self._read_yaml_file(path)
            for d in by_category["base_efforts"]:
                self._set_nested(data, d.key, d.proposed)
            self._write_yaml_file(path, data)
            modified.append(str(path))

        if "role_splits" in by_category:
            path = root / "knowledge-base/role-split-heuristics.yaml"
            data = self._read_yaml_file(path)
            for d in by_category["role_splits"]:
                parts = d.key.split(".")
                task_type, role = parts[0], parts[1]
                if task_type in data and "split" in data[task_type]:
                    data[task_type]["split"][role] = d.proposed
            self._normalize_role_splits(data, by_category["role_splits"])
            self._write_yaml_file(path, data)
            modified.append(str(path))

        if "buffer" in by_category:
            path = root / "knowledge-base/base-efforts-man-days-per-task-type.yaml"
            data = self._read_yaml_file(path)
            if "buffer" not in data:
                data["buffer"] = {}
            for d in by_category["buffer"]:
                data["buffer"][d.key] = d.proposed
            self._write_yaml_file(path, data)
            if str(path) not in modified:
                modified.append(str(path))

        # Clear LRU cache so reloads pick up new values
        _load_yaml.cache_clear()

        return modified

    def _get_kb_base_effort(self, task_type: str) -> float | None:
        """Look up KB base effort for a task type (handles nested structure)."""
        for category, items in self._kb_base_efforts.items():
            if category == "buffer":
                continue
            if isinstance(items, dict) and task_type in items:
                return items[task_type]
            if category == task_type and not isinstance(items, dict):
                return items
        return None

    def _get_kb_role_splits(self, task_type: str) -> dict | None:
        entry = self._kb_role_splits.get(task_type)
        if entry and isinstance(entry, dict):
            return entry.get("split", {})
        return None

    @staticmethod
    def _normalize_role_splits(data: dict, diffs: list[ParameterDiff]):
        """After adjusting a role split, normalize all roles in that task_type to sum=1.0."""
        affected_types = {d.key.split(".")[0] for d in diffs}
        for tt in affected_types:
            if tt not in data or "split" not in data[tt]:
                continue
            split = data[tt]["split"]
            total = sum(split.values())
            if total > 0:
                for role in split:
                    split[role] = round(split[role] / total, 3)

    @staticmethod
    def _set_nested(data: dict, key: str, value: float):
        """Set a value in possibly-nested dict by dot-separated or flat key."""
        for category, items in data.items():
            if isinstance(items, dict) and key in items:
                data[category][key] = value
                return
        data[key] = value

    @staticmethod
    def _read_yaml_file(path: Path) -> dict:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @staticmethod
    def _write_yaml_file(path: Path, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
