"""Unit tests for _layout_lib.py — LAYERED_PATH_MAP."""
from __future__ import annotations
import sys
from pathlib import Path

# conftest.py adds SCRIPTS_DIR to sys.path when pytest loads it, but a plain
# import of _layout_lib in direct runs also needs the path set.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _layout_lib import LAYERED_PATH_MAP  # noqa: E402


class TestLayeredPathMap:
    def test_system_overview_maps_to_system_dir(self):
        assert LAYERED_PATH_MAP["system-overview.md"] == "system/overview.md"

    def test_data_model_maps_to_entities(self):
        assert LAYERED_PATH_MAP["data-model.md"] == "generated/entities.md"

    def test_permissions_in_system(self):
        assert LAYERED_PATH_MAP["permissions.md"].startswith("system/")

    def test_route_list_in_generated(self):
        assert LAYERED_PATH_MAP["route-list.md"].startswith("generated/")

    def test_all_values_have_subdir(self):
        for fname, path in LAYERED_PATH_MAP.items():
            assert "/" in path, f"{fname!r} → {path!r} has no subdirectory"
