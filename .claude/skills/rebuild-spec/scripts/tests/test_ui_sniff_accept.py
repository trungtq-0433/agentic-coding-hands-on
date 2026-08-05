"""Tests for `_ui_sniff_accept_lib.py` (Phase 09, Track D — Tier-2 accept-path).

`sys.path` already has scripts/ on it (see conftest.py). Covers:
  (a) accepted Tier-2 leads -> valid sparse ScreenRec-shaped digest, every entry
      `unverified: True`, cited.
  (b) session profile override -> `screen_source: "ui-sniff"` + both
      `artifact_map` screen actions flipped to `"produce"`.
  (c) [RT-F5, critical] no file under `references/stack-profiles/` is ever
      touched by any code path in this lib.
  (d) end-to-end: the sparse digest -> a hand-rendered `screen-list.md` ->
      `validate_screen_list.py` PASSES on it — proves "no new validator code
      needed" holds for real, not just in theory.
"""
from __future__ import annotations

import builtins
import hashlib
import json
from pathlib import Path

import _ui_sniff_accept_lib as accept_lib
import _stack_profile_lib as profile_lib
import validate_screen_list

PROFILES_DIR = profile_lib.PROFILES_DIR

_SIGNALS = [
    {
        "family": "stdin_read",
        "token": "ACCEPT",
        "citation": "src/menu.cbl:12: ACCEPT WS-CHOICE FROM CONSOLE",
        "structural": False,
    },
    {
        "family": "menu_loop",
        "token": "menu-loop",
        "citation": "src/menu.cbl:20: PERFORM UNTIL WS-CHOICE = '9'",
        "structural": True,
    },
    {
        "family": "vb6_inputbox",
        "token": ".frm",
        "citation": "src/Login.frm:0: <VB6 form file marker>",
        "structural": False,
    },
]


# ---------------------------------------------------------------------------
# (a) sparse digest builder
# ---------------------------------------------------------------------------

class TestSparseDigestBuilder:
    def test_every_entry_matches_screenrec_shape_and_unverified(self):
        recs = accept_lib.build_sparse_screen_recs(_SIGNALS, summary="3 signal(s), tier=2")
        assert len(recs) == len(_SIGNALS)
        expected_keys = {"screen", "kind", "reachable", "entry_citation", "flow_edges", "unverified", "raw"}
        for rec in recs:
            assert set(rec.keys()) == expected_keys
            assert rec["unverified"] is True
            assert rec["kind"] == "ui-sniff"
            assert rec["flow_edges"] == []
            assert rec["entry_citation"]  # cited, non-empty

    def test_structural_signal_is_reachable_non_structural_is_not(self):
        recs = accept_lib.build_sparse_screen_recs(_SIGNALS)
        by_family = {r["raw"]["family"]: r for r in recs}
        assert by_family["menu_loop"]["reachable"] is True
        assert by_family["stdin_read"]["reachable"] is False
        assert by_family["vb6_inputbox"]["reachable"] is False

    def test_screen_names_are_unique_and_markdown_safe(self):
        recs = accept_lib.build_sparse_screen_recs(_SIGNALS)
        names = [r["screen"] for r in recs]
        assert len(names) == len(set(names))
        for name in names:
            assert "|" not in name and "`" not in name and "\n" not in name

    def test_entry_citation_is_sanitized_backtick_cannot_break_out_of_delimiter(self):
        """Regression (Wave 5 review, Critical security finding): SKILL.md's Tier-2
        AskUserQuestion prose wraps `entry_citation` in a single backtick span for its
        fix-10 prompt-injection defense. An unsanitized backtick in the untrusted source
        excerpt would let it break out of that delimiter -- entry_citation must get the
        same Markdown-hostile-char strip `screen` already gets, not be the one unsanitized
        field in this ScreenRec."""
        malicious_signals = [{
            "family": "shell_dialog", "token": "dialog",
            "citation": "menu.sh:12: dialog --msgbox `rm -rf /` | cat /etc/passwd 0 0",
            "structural": True,
        }]
        recs = accept_lib.build_sparse_screen_recs(malicious_signals)
        assert "`" not in recs[0]["entry_citation"]
        assert "|" not in recs[0]["entry_citation"]

    def test_no_signals_yields_empty_digest_not_a_crash(self, tmp_path):
        path = accept_lib.write_ui_sniff_digest(tmp_path / "plan", [])
        digest = json.loads(path.read_text(encoding="utf-8"))
        assert digest["screens"] == []
        assert "no_accepted_signals" in digest["warnings"]

    def test_write_ui_sniff_digest_writes_expected_shard_filename(self, tmp_path):
        plan_dir = tmp_path / "plan"
        path = accept_lib.write_ui_sniff_digest(plan_dir, _SIGNALS, summary="3 signal(s), tier=2")
        assert path.name == "_digest_extract_ui_sniff.json"
        assert path.parent == plan_dir / "artifacts"
        digest = json.loads(path.read_text(encoding="utf-8"))
        assert digest["extractor"] == "extract_ui_sniff"
        assert len(digest["screens"]) == len(_SIGNALS)
        assert all(s["raw"]["summary"] == "3 signal(s), tier=2" for s in digest["screens"])


# ---------------------------------------------------------------------------
# (b) session profile override
# ---------------------------------------------------------------------------

class TestProfileOverride:
    def _generic_source(self) -> dict:
        with open(PROFILES_DIR / "generic-source.json", encoding="utf-8") as f:
            return json.load(f)

    def test_override_sets_screen_source_ui_sniff_and_flips_artifact_map(self):
        base = self._generic_source()
        assert base["screen_source"] == "none"  # sanity: base really skips screens
        overridden = accept_lib.override_profile_for_ui_sniff(base)

        assert overridden["screen_source"] == "ui-sniff"
        assert overridden["artifact_map"]["screen-list"]["action"] == "produce"
        assert overridden["artifact_map"]["screen-flow"]["action"] == "produce"

    def test_override_does_not_mutate_input_profile(self):
        base = self._generic_source()
        before = json.dumps(base, sort_keys=True)
        accept_lib.override_profile_for_ui_sniff(base)
        after = json.dumps(base, sort_keys=True)
        assert before == after  # input untouched — pure transform

    def test_override_handles_missing_artifact_map_entries(self):
        base = {"id": "x", "artifact_map": {}, "screen_source": "none"}
        overridden = accept_lib.override_profile_for_ui_sniff(base)
        assert overridden["artifact_map"]["screen-list"] == {"class": "web", "action": "produce"}
        assert overridden["artifact_map"]["screen-flow"] == {"class": "web", "action": "produce"}

    def test_write_profile_override_sidecar_lands_in_plan_dir_only(self, tmp_path):
        plan_dir = tmp_path / "plan"
        overridden = accept_lib.override_profile_for_ui_sniff(self._generic_source())
        path = accept_lib.write_profile_override_sidecar(plan_dir, overridden)

        assert path == plan_dir / ".ui-sniff-profile-override.json"
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["screen_source"] == "ui-sniff"


# ---------------------------------------------------------------------------
# (c) [RT-F5, critical] kit profile files are NEVER touched
# ---------------------------------------------------------------------------

class TestTrustBoundaryNeverWritesKitProfiles:
    def _snapshot(self) -> dict[str, str]:
        return {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(PROFILES_DIR.glob("*"))
            if p.is_file()
        }

    def test_full_accept_flow_leaves_stack_profiles_dir_byte_identical(self, tmp_path):
        before = self._snapshot()
        assert before, "sanity: stack-profiles dir must be non-empty for this test to mean anything"

        with open(PROFILES_DIR / "generic-source.json", encoding="utf-8") as f:
            base_profile = json.load(f)

        plan_dir = tmp_path / "plan"
        accept_lib.write_ui_sniff_digest(plan_dir, _SIGNALS, summary="tier=2")
        overridden = accept_lib.override_profile_for_ui_sniff(base_profile)
        accept_lib.write_profile_override_sidecar(plan_dir, overridden)

        after = self._snapshot()
        assert after == before

    def test_open_for_write_is_never_called_against_stack_profiles_dir(self, tmp_path, monkeypatch):
        """Regression guard: monkeypatch builtins.open to fail loudly if any code
        path in this lib ever opens a file under references/stack-profiles/ in a
        write-capable mode. Reads (loading generic-source.json here, in the test
        harness) are unaffected; only THIS module's calls are exercised below."""
        real_open = builtins.open
        write_modes = {"w", "a", "x", "w+", "a+", "x+", "r+"}

        def guarded_open(file, mode="r", *args, **kwargs):
            try:
                resolved = str(Path(file).resolve())
            except (TypeError, OSError):
                resolved = str(file)
            if str(PROFILES_DIR) in resolved and any(m in mode for m in write_modes):
                raise AssertionError(f"attempted write-mode open() under stack-profiles/: {file!r}")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", guarded_open)

        with real_open(PROFILES_DIR / "generic-source.json", encoding="utf-8") as f:
            base_profile = json.load(f)

        plan_dir = tmp_path / "plan"
        accept_lib.write_ui_sniff_digest(plan_dir, _SIGNALS)
        overridden = accept_lib.override_profile_for_ui_sniff(base_profile)
        accept_lib.write_profile_override_sidecar(plan_dir, overridden)
        # No AssertionError raised => no write-mode open() ever targeted stack-profiles/.


# ---------------------------------------------------------------------------
# (d) end-to-end: sparse digest -> hand-rendered screen-list.md -> validator PASS
# ---------------------------------------------------------------------------

def _render_screen_list_md(screens: list[dict]) -> str:
    """Minimal hand-rendered screen-list.md from a sparse ui-sniff digest —
    stands in for the LLM synthesis pass (Wave 2) without any new template
    code. Exercises the SAME structural rules validate_screen_list.py checks:
    one Screen Index, unique SCR codes, cited + [UNVERIFIED] rows."""
    lines = ["# Screen List", "", "## Screen Index", "", "| Code | Name | Type |", "|------|------|------|"]
    scr_codes = []
    for i, screen in enumerate(screens, start=1):
        code = f"SCR{i:03d}_{screen['screen'][:20]}"
        scr_codes.append(code)
        lines.append(f"| {code} | {screen['screen']} | ui-sniff-lead |")
    lines.append("")
    for code, screen in zip(scr_codes, screens):
        verified_tag = "" if screen["unverified"] else " [VERIFIED]"
        lines.append(f"## {code}: {screen['screen']}")
        lines.append("")
        lines.append("### Description")
        lines.append("")
        lines.append(
            f"[UNVERIFIED]{verified_tag} lead sniffed from `{screen['entry_citation']}` "
            f"(family: {screen['raw']['family']})."
        )
        lines.append("")
        lines.append("### Invocation")
        lines.append("")
        lines.append(f"- Reachability: {'static' if screen['reachable'] else '[UNVERIFIED]'} — `{screen['entry_citation']}`")
        lines.append("")
    return "\n".join(lines)


class TestEndToEndValidatorPass:
    def test_sparse_digest_renders_a_screen_list_that_passes_validator(self, tmp_path):
        recs = accept_lib.build_sparse_screen_recs(_SIGNALS, summary="3 signal(s), tier=2")
        assert all(r["unverified"] for r in recs)  # sanity: every row stays unverified

        md_text = _render_screen_list_md(recs)
        plan_dir = tmp_path / "plan"
        artifacts = plan_dir / "artifacts"
        artifacts.mkdir(parents=True)
        sl_path = artifacts / "screen-list.md"
        sl_path.write_text(md_text, encoding="utf-8")

        result = validate_screen_list.validate(plan_dir, tmp_path, screen_source="ui-sniff")

        assert result["status"] == "PASS", result["issues"]
        assert result["summary"]["critical"] == 0
