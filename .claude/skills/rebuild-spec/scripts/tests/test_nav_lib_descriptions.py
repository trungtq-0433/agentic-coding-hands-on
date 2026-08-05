"""Drift-guard: every READING_ORDER non-glob path basename must be keyed in
_ARTIFACT_DESCRIPTIONS, and known missing filenames must return real descriptions
(not echo fallbacks).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_lib import _ARTIFACT_DESCRIPTIONS, file_description  # noqa: E402
from _nav_strings import READING_ORDER  # noqa: E402


def _non_glob_basenames() -> list[str]:
    """Extract the filename (basename) for every non-glob READING_ORDER entry."""
    basenames = []
    for layer in READING_ORDER:
        for entry in layer["entries"]:
            if "path" in entry:
                basenames.append(os.path.basename(entry["path"]))
    return basenames


class TestArtifactDescriptionsDriftGuard:
    def test_all_reading_order_basenames_keyed(self):
        """Every non-glob READING_ORDER path basename must have a key in
        _ARTIFACT_DESCRIPTIONS (drift-guard — no echo fallback allowed)."""
        basenames = _non_glob_basenames()
        missing = [b for b in basenames if b not in _ARTIFACT_DESCRIPTIONS]
        assert not missing, (
            f"Missing from _ARTIFACT_DESCRIPTIONS: {missing}. "
            "Add the basename keys with real prose to _nav_lib._ARTIFACT_DESCRIPTIONS."
        )

    def test_file_description_no_echo_for_known_artifacts(self):
        """file_description() must not return the bare stem for any READING_ORDER basename."""
        for basename in _non_glob_basenames():
            desc = file_description(basename)
            # The echo fallback would be e.g. "overview" for "overview.md"
            stem = basename.replace("-", " ").replace(".md", "")
            assert desc != stem, (
                f"file_description({basename!r}) returned echo fallback {stem!r}. "
                "Add a real description to _ARTIFACT_DESCRIPTIONS."
            )

    def test_overview_md_real_description(self):
        desc = file_description("overview.md")
        assert desc != "overview"
        assert len(desc) > 10  # real prose, not a one-word echo

    def test_architecture_md_real_description(self):
        desc = file_description("architecture.md")
        assert desc != "architecture"
        assert len(desc) > 10

    def test_business_rules_md_real_description(self):
        desc = file_description("business-rules.md")
        assert desc != "business rules"
        assert len(desc) > 10

    def test_entities_md_real_description(self):
        desc = file_description("entities.md")
        assert desc != "entities"
        assert len(desc) > 10

    def test_permissions_matrix_md_real_description(self):
        desc = file_description("permissions-matrix.md")
        assert desc != "permissions matrix"
        assert len(desc) > 10
