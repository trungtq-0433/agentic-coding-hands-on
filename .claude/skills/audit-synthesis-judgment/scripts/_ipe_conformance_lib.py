"""Engine 2 — IPE Step-3/Step-4 conformance rule engine (deterministic, WARN-only).

Audits whether the promoted `user-stories.md` APPLIED the (already-fixed) IPE protocol — it does
NOT re-derive the partition. Every finding cites the violated clause. Findings are WARN or
UNVERIFIABLE; NONE is ever a FAIL, and none ever touches Engine-1's phantom/orphan counts.

Checks:
  - **Anti-CRUD (Step-4)** — stack-agnostic. US title must contain exactly ONE action verb; reject
    CRUD-lump names ("Manage X", "User CRUD") and compound verbs ("Create/Edit"). → NAMING.
  - **Merge/split (Step-3)** — route-view / dfm-form only. Per screen, compare the mapped US count
    against the minimum justified by the Interaction Inventory under condition (b): same endpoint
    (route-view) / same handler proc (dfm-form), with destructive interactions ALWAYS separate.
      M == 0, N > 0            → MISSING_US   (screen has interactions, no US — IPE_ZERO)
      0 < M < min_justified    → OVER_MERGE   (merged across an endpoint/destructive boundary — 86-vs-354)
      M > N                    → UNDER_SPLIT  (more US than interactions)
      min_justified ≤ M ≤ N    → conformant   (no finding)
  - Ambiguity (blank Endpoint on a non-destructive row, absent Inventory/Map, unsupported
    screen_source) → UNVERIFIABLE, never a guessed WARN.

Stdlib only.
"""
from __future__ import annotations

import re

from _ipe_parse_lib import ParsedUserStories

# Screen sources whose Step-3 condition (b) is specified upstream (user-stories-ipe-protocol.md).
_MERGE_SUPPORTED = {"route-view", "dfm-form"}

_BLANK_ENDPOINT = {"", "n/a", "na", "none", "-", "—"}
_DESTRUCTIVE = "destructive-action"

# Anti-CRUD (Step-4) — the template's own Bad list.
_CRUD_LUMP_RE = re.compile(r"\b(manage|management|administer|administration|crud|handle|maintain)\b", re.I)
_COMPOUND_VERB_RE = re.compile(r"\b\w+\s*/\s*\w+\b|\b\w+\s+(?:and|&)\s+\w+\b")

_CLAUSE_STEP3_B = "IPE Step-3 condition (b): same endpoint (route-view) / same event-handler proc (dfm-form)"
_CLAUSE_STEP3_DESTRUCTIVE = "IPE Step-1: destructive actions are ALWAYS a separate US"
_CLAUSE_STEP4 = "IPE Step-4: US title MUST contain exactly ONE action verb (anti-CRUD)"
_CLAUSE_STEP5 = "IPE Step-5: a screen with N interactions expects ≥N US unless a Step-3 merge applies"


def _finding(kind, severity, verdict, evidence, clause, **extra):
    f = {"engine": "boundary", "kind": kind, "severity": severity, "verdict": verdict,
         "evidence": evidence, "clause": clause, "anchor": clause}
    f.update(extra)
    return f


def check_anti_crud(parsed: ParsedUserStories) -> list[dict]:
    findings: list[dict] = []
    for code, title in sorted(parsed.us_titles.items()):
        lump = _CRUD_LUMP_RE.search(title)
        compound = _COMPOUND_VERB_RE.search(title)
        if lump:
            findings.append(_finding(
                "NAMING", "low", "WARN",
                f"{code} title '{title}' uses a CRUD-lump term '{lump.group(0)}' (not a single action verb)",
                _CLAUSE_STEP4, us=code))
        elif compound:
            findings.append(_finding(
                "NAMING", "low", "WARN",
                f"{code} title '{title}' contains a compound verb '{compound.group(0)}' — split into separate US",
                _CLAUSE_STEP4, us=code))
    return findings


def check_merge_split(parsed: ParsedUserStories, screen_source: str) -> list[dict]:
    findings: list[dict] = []

    if not parsed.has_inventory or not parsed.has_screen_map:
        findings.append(_finding(
            "UNVERIFIABLE", "low", "UNVERIFIABLE",
            "user-stories.md lacks an Interaction Inventory and/or Screen→US Map — "
            "merge/split conformance cannot be judged (older corpus)",
            _CLAUSE_STEP5))
        return findings

    if screen_source not in _MERGE_SUPPORTED:
        findings.append(_finding(
            "UNVERIFIABLE", "low", "UNVERIFIABLE",
            f"screen_source '{screen_source}' has no upstream Step-3 condition (b) — "
            f"merge/split UNVERIFIABLE (anti-CRUD still runs)",
            _CLAUSE_STEP3_B))
        return findings

    # Group interactions by screen.
    by_screen: dict[str, list] = {}
    for it in parsed.interactions:
        by_screen.setdefault(it.screen, []).append(it)

    for screen, us_codes in sorted(parsed.screen_to_us.items()):
        interactions = by_screen.get(screen, [])
        n = len(interactions)
        m = len(us_codes)
        if n == 0:
            continue  # a mapped screen with no inventory rows — nothing to compare against

        destructive = [it for it in interactions if it.itype == _DESTRUCTIVE]
        non_destructive = [it for it in interactions if it.itype != _DESTRUCTIVE]

        # Ambiguity: a non-destructive row with a blank endpoint can't be grouped → UNVERIFIABLE.
        if any(it.endpoint.strip().lower() in _BLANK_ENDPOINT for it in non_destructive):
            findings.append(_finding(
                "UNVERIFIABLE", "low", "UNVERIFIABLE",
                f"screen {screen}: a non-destructive interaction has a blank Endpoint — "
                f"cannot apply Step-3 condition (b); UNVERIFIABLE (not a guessed OVER_MERGE)",
                _CLAUSE_STEP3_B, screen=screen))
            continue

        distinct_endpoints = {it.endpoint.strip().lower() for it in non_destructive}
        min_justified = len(distinct_endpoints) + len(destructive)

        if m == 0:
            findings.append(_finding(
                "MISSING_US", "medium", "WARN",
                f"screen {screen} has {n} interaction(s) but 0 US mapped (IPE_ZERO)",
                _CLAUSE_STEP5, screen=screen))
        elif m < min_justified:
            findings.append(_finding(
                "OVER_MERGE", "medium", "WARN",
                f"screen {screen}: {n} interactions across {len(distinct_endpoints)} endpoint-group(s) "
                f"+ {len(destructive)} destructive → minimum justified US = {min_justified}, "
                f"but only {m} US mapped — merge crossed an endpoint/destructive boundary",
                _CLAUSE_STEP3_B if len(distinct_endpoints) > m else _CLAUSE_STEP3_DESTRUCTIVE,
                screen=screen, mapped_us=m, min_justified=min_justified, interactions=n))
        elif m > n:
            findings.append(_finding(
                "UNDER_SPLIT", "low", "WARN",
                f"screen {screen}: {m} US mapped for only {n} interaction(s) — "
                f"identical interactions may have been over-split",
                _CLAUSE_STEP3_B, screen=screen, mapped_us=m, interactions=n))
        # else conformant
    return findings


def run_checks(parsed: ParsedUserStories, screen_source: str) -> list[dict]:
    return check_anti_crud(parsed) + check_merge_split(parsed, screen_source)
