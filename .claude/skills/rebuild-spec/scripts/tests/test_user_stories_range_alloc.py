"""Tests for US### range pre-allocation in estimate_artifact_loc.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
from estimate_artifact_loc import emit_us_ranges  # noqa: E402


class TestDisjointRanges:
    def test_two_actors_disjoint(self):
        ranges = emit_us_ranges(["admin", "guest"], {"admin": 10, "guest": 5})
        assert ranges[0]["actor"] == "admin"
        assert ranges[1]["actor"] == "guest"
        assert ranges[0]["end"] < ranges[1]["start"]

    def test_three_actors_contiguous_between(self):
        ranges = emit_us_ranges(["a", "b", "c"], {"a": 10, "b": 10, "c": 10})
        for i in range(len(ranges) - 1):
            assert ranges[i]["end"] + 1 == ranges[i + 1]["start"]

    def test_no_collision(self):
        ranges = emit_us_ranges(["x", "y", "z"], {"x": 20, "y": 20, "z": 20})
        all_nums = set()
        for r in ranges:
            for n in range(r["start"], r["end"] + 1):
                assert n not in all_nums, f"US{n:03d} collision"
                all_nums.add(n)


class TestHeadroom:
    def test_20_percent_headroom(self):
        ranges = emit_us_ranges(["actor"], {"actor": 10})
        r = ranges[0]
        assert r["start"] == 1
        assert r["end"] == 12  # 10 * 1.2 = 12
        assert r["estimated_count"] == 10

    def test_headroom_tail_gaps_safe(self):
        """Unused tail of a range leaves a US### gap — safe (no density gate)."""
        ranges = emit_us_ranges(["a", "b"], {"a": 10, "b": 5})
        assert ranges[0]["end"] - ranges[0]["start"] + 1 == 12  # padded
        assert ranges[1]["start"] == 13


class TestEdgeCases:
    def test_empty_actors(self):
        assert emit_us_ranges([]) == []

    def test_single_actor(self):
        ranges = emit_us_ranges(["solo"], {"solo": 3})
        assert len(ranges) == 1
        assert ranges[0]["start"] == 1

    def test_default_estimate(self):
        """Actor not in us_per_actor dict gets default 5."""
        ranges = emit_us_ranges(["unknown_actor"])
        assert ranges[0]["estimated_count"] == 5
        assert ranges[0]["end"] == 6  # ceil(5 * 1.2) = 6

    def test_sorted_by_actor_name(self):
        ranges = emit_us_ranges(["zebra", "alpha", "middle"])
        actors = [r["actor"] for r in ranges]
        assert actors == ["alpha", "middle", "zebra"]

    def test_minimum_range_size(self):
        """Even with 0 estimated US, range has at least 1 slot."""
        ranges = emit_us_ranges(["tiny"], {"tiny": 0})
        assert ranges[0]["start"] == 1
        assert ranges[0]["end"] >= 1

    def test_small_count_headroom_with_ceil(self):
        """math.ceil guarantees headroom even for small counts (3 → 4 slots)."""
        ranges = emit_us_ranges(["actor"], {"actor": 3})
        r = ranges[0]
        assert r["end"] - r["start"] + 1 == 4  # ceil(3 * 1.2) = 4
        assert r["end"] >= r["start"] + r["estimated_count"]  # room for at least 1 extra
