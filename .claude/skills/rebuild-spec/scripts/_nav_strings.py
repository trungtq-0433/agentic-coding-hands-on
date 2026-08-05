"""Reading-order STRUCTURE for the top-level docs/README.md index.

Structure only (numbers, on-disk paths/globs, role reading-paths) + the
get_strings accessor. Translatable PROSE lives in the per-language locale
modules _nav_strings_<lang> (one file per language). Keeping numbers/links/role
paths here single-sourced is what makes skeleton identity across en/vi/ja
automatic — only prose differs.

READING_ORDER is keyed by ON-DISK relative paths/globs (the renderer walks real
files). Every non-glob path must be a value in _layout_lib.LAYERED_PATH_MAP
(asserted by a test; update both when adding an artifact — see
docs-canonical-mapping.md). Single-file entries use "path"; drill-downs use
"glob" + "link" (the target dir).
"""
from __future__ import annotations

from _lang_lib import normalize_lang
from _nav_strings_en import STRINGS as _EN
from _nav_strings_ja import STRINGS as _JA
from _nav_strings_vi import STRINGS as _VI

READING_ORDER = [
    {"layer": 1, "entries": [
        {"num": 1, "path": "system/overview.md", "key": "system_overview"},
        {"num": 2, "path": "system/architecture.md", "key": "architecture"},
        {"num": 3, "path": "system/glossary.md", "key": "glossary", "conditional": True},
    ]},
    {"layer": 2, "entries": [
        {"num": 4, "path": "generated/entities.md", "key": "entities"},
        {"num": 5, "path": "generated/feature-list.md", "key": "feature_list"},
        {"num": 6, "path": "generated/user-stories.md", "key": "user_stories"},
    ]},
    {"layer": 3, "entries": [
        {"num": 7, "path": "generated/screen-list.md", "key": "screen_list"},
        {"num": 8, "path": "generated/screen-flow.md", "key": "screen_flow"},
        {"num": 9, "path": "generated/route-list.md", "key": "route_list"},
        {"num": 10, "path": "generated/api-map.md", "key": "api_map"},
        {"num": 11, "path": "generated/api-contracts.md", "key": "api_contracts", "conditional": True},
        {"num": 12, "path": "generated/behavior-logic.md", "key": "behavior_logic"},
        {"num": 13, "path": "system/business-rules.md", "key": "business_rules"},
        {"num": 14, "path": "generated/permissions-matrix.md", "key": "permissions_matrix"},
    ]},
    {"layer": 4, "entries": [
        {"num": 15, "glob": "flows/*.md", "link": "flows/", "key": "flows", "conditional": True},
        {"num": 16, "glob": "features/*/", "link": "features/", "key": "features",
         "conditional": True, "feature_note": True},
        {"num": 17, "glob": "screens/*/spec.md", "link": "screens/", "key": "screens",
         "conditional": True},
        {"num": 18, "path": "generated/job-list.md", "key": "job_list", "conditional": True},
        {"num": 19, "path": "system/design-intent.md", "key": "design_intent", "conditional": True},
    ]},
]

# Minimum fast-read sequence — lang-independent numbers (the label is translated
# per-locale via quick_path_label). Pruned at render time like ROLES, so it never
# points at an artifact that is absent on disk.
QUICK_PATH = [1, 2, 4, 5]

# Role reading-paths — lang-independent number sequences (labels are translated
# per-locale via role_labels[key]). A number absent on disk is dropped from the
# path by the renderer, so a role line never points at a missing artifact.
ROLES = [
    {"key": "new_dev", "path": [1, 2, 4, 5, 7, 16]},
    {"key": "reviewer", "path": [2, 13, 14, 11]},
    {"key": "pm", "path": [1, 5, 6]},
]

# Aggregate reading order for docs/<lang>/system/ in system-of-systems layouts (v16 parity names).
# Ordered: overview first, then catalog/architecture/ownership/flows/glossary/confidence.
# Presence-pruned by the renderer, so absent files are silently dropped.
AGGREGATE_SYSTEM_ORDER = [
    "overview.md",
    "component-catalog.md",
    "architecture.md",
    "data-ownership-map.md",
    "cross-service-flows.md",
    "glossary.md",
    "per-component-confidence.md",
]

# Maps each AGGREGATE_SYSTEM_ORDER filename to a stable key used to look up the
# causal why-read-here clause in strings.aggregate_why[why_key].  Parallel to
# AGGREGATE_SYSTEM_ORDER so the presence-prune logic in the renderer is untouched.
# A test asserts every AGGREGATE_SYSTEM_ORDER entry appears as a key here.
AGGREGATE_WHY_KEYS: dict[str, str] = {
    "overview.md":                "overview",
    "component-catalog.md":       "component_catalog",
    "architecture.md":            "architecture",
    "data-ownership-map.md":      "data_ownership_map",
    "cross-service-flows.md":     "cross_service_flows",
    "glossary.md":                "glossary",
    "per-component-confidence.md":"per_component_confidence",
}

# Role reading-paths for the aggregate tier — lang-independent number sequences.
# Positions map to AGGREGATE_SYSTEM_ORDER (1-indexed).
# Labels reuse existing role_labels keys (new_dev / reviewer / pm).
# A number absent on disk is dropped from the path at render time.
AGGREGATE_ROLES = [
    {"key": "new_dev",  "path": [1, 2, 3, 4]},
    {"key": "reviewer", "path": [3, 4, 5, 7]},
    {"key": "pm",       "path": [1, 5, 6]},
]

LANG_STRINGS = {"en": _EN, "vi": _VI, "ja": _JA}  # keyed by canonical code (jp→ja)


def get_strings(lang: str | None) -> dict:
    """Return the locale strings block, falling back to 'en'.

    The code is normalized (jp→ja, path-traversal hardened) before lookup, so an
    unlisted language (e.g. 'fr') renders with English labels rather than raising.
    """
    try:
        key = normalize_lang(lang)
    except ValueError:
        key = "en"
    return LANG_STRINGS.get(key, LANG_STRINGS["en"])
