"""Engine 3 — deterministic granularity-outlier statistic.

The one non-LLM sub-signal Engine 3 owns: flag a feature whose size is a statistical outlier
versus the set (far coarser or finer than its peers). Uses the MEDIAN + MAD (median absolute
deviation) modified z-score — robust to the few genuinely-large features that would wreck a
mean/stdev test. The anchor is the stat itself, never taste; the finding is advisory WARN wording
("granularity outlier — review"), never definitive.

Stdlib only.
"""
from __future__ import annotations


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def find_outliers(feature_metrics: dict[str, float], threshold: float = 3.5) -> dict:
    """Detect granularity outliers via the MAD modified z-score.

    `feature_metrics`: {feature_id: metric_value} (e.g. interaction-count or cited-symbol span).
    Returns:
        {
          "median": <float>, "mad": <float>, "threshold": <float>,
          "outliers": [ {feature, value, z_score, direction: "coarse"|"fine", anchor} ],
        }
    A set with < 3 features, or MAD == 0 (all equal), yields no outliers (too little signal).
    """
    values = list(feature_metrics.values())
    med = _median(values)
    if len(values) < 3:
        return {"median": med, "mad": 0.0, "threshold": threshold, "outliers": []}

    mad = _median([abs(v - med) for v in values])
    # MAD is 0 when > half the values equal the median (a common shape: many same-size features
    # + a few outliers). Fall back to the mean absolute deviation, which still has spread. Only a
    # genuinely uniform set (every value identical) yields no scale → no outliers.
    if mad == 0:
        mean_ad = sum(abs(v - med) for v in values) / len(values)
        if mean_ad == 0:
            return {"median": med, "mad": 0.0, "threshold": threshold, "outliers": []}
        scale, const = mean_ad, 1.253314
    else:
        scale, const = mad, 1.0 / 0.6745

    outliers: list[dict] = []
    for feat, v in sorted(feature_metrics.items()):
        z = (v - med) / (const * scale)
        if abs(z) > threshold:
            outliers.append({
                "feature": feat,
                "value": v,
                "z_score": round(z, 2),
                "direction": "coarse" if z > 0 else "fine",
                "anchor": f"granularity outlier: value {v} vs set median {med} "
                          f"(modified z-score {round(z, 2)}, scale {round(scale, 3)}, threshold {threshold})",
            })
    return {"median": med, "mad": mad, "scale": scale, "threshold": threshold, "outliers": outliers}
