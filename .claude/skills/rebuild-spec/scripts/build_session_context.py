#!/usr/bin/env python3
"""Write plans/<active>/artifacts/_session-context.md — shared context for all W1-W9 subagents.

Exit codes: 0 = success, 2 = arg/IO error.
Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
import tempfile


def _resolve_guarded(path: str, base: str) -> str:
    """Resolve path and verify it stays under base. Raises ValueError if not."""
    resolved = os.path.realpath(os.path.abspath(path))
    base_resolved = os.path.realpath(os.path.abspath(base))
    if os.path.commonpath([resolved, base_resolved]) != base_resolved:
        raise ValueError(f"Path traversal detected: {path!r} escapes {base!r}")
    return resolved


def _extract_detected_stack(content: str, profile_id: str | None = None) -> str | None:
    """Return the scout's '## Detected Language' value.

    RT-F2: when a profile is explicitly selected (`profile_id` set) but the scout report has
    no recognizable Detected Language, return None so the caller can ABORT — never silently
    fall back to "JS/TS" on a non-JS stack. With no profile selected, the legacy "JS/TS"
    fallback is preserved (backward-compatible).
    """
    m = re.search(r"^## Detected Language\s*\n\s*(\S[^\n]*)", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None if profile_id else "JS/TS"


def _atomic_write(path: str, content: str) -> None:
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".sc_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _patch_feature_count(existing: str, count: int) -> str:
    return re.sub(r"(?m)^(- feature_count: ).*$", rf"\g<1>{count}", existing)


def _graphify_enabled() -> bool:
    """ON by default. Off via env (GRAPHIFY_DISABLE / REBUILD_NO_GRAPH) or config
    graphify.enabled=false. Reads local .takumi.json (tkm CLI) → local .tkm.json →
    global .takumi.json → global .tkm.json; first that defines it wins."""
    import json
    if os.environ.get("REBUILD_NO_GRAPH") == "1" or os.environ.get("GRAPHIFY_DISABLE") == "1":
        return False
    for p in (os.path.join(os.getcwd(), ".claude", ".takumi.json"),
              os.path.join(os.getcwd(), ".claude", ".tkm.json"),
              os.path.expanduser("~/.claude/.takumi.json"),
              os.path.expanduser("~/.claude/.tkm.json")):
        try:
            with open(p, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            continue
        g = cfg.get("graphify") if isinstance(cfg, dict) else None
        if isinstance(g, dict) and "enabled" in g:
            return g["enabled"] is not False
    return True


def build(args: argparse.Namespace) -> None:
    cwd = os.getcwd()

    # [GRAPHIFY-INTEGRATION] graphify-first discovery directive — emitted when graphify is
    # enabled (default) AND a knowledge graph (graphify-out/graph.json) exists in the project.
    # Suppressed when graphify is disabled (config graphify.enabled=false or env opt-out).
    # graph_preflight.py puts `graphify` on PATH, so the short bare command is used here.
    graphify_directive = ""
    if _graphify_enabled() and os.path.exists(os.path.join(cwd, "graphify-out", "graph.json")):
        graphify_directive = (
            "\n## Knowledge Graph (graphify) — PRIMARY code-discovery tool\n"
            "A prebuilt graph exists at `graphify-out/`. To understand SOURCE CODE (definitions, "
            "call sites, relationships, impact) you MUST query it FIRST via the Bash tool, instead "
            "of grepping or reading source files one by one:\n"
            "- `graphify query \"<question>\"` — scoped subgraph (routes, models, auth...)\n"
            "- `graphify explain \"<Symbol>\"` — a symbol plus its neighbors\n"
            "- `graphify path \"<A>\" \"<B>\"` — how two concepts relate\n"
            "- `graphify affected \"<Symbol>\"` — reverse impact (what a change touches)\n"
            "Also read `graphify-out/GRAPH_REPORT.md` for the architecture overview and god-nodes.\n"
            "Read a source file ONLY to confirm a detail the graph lacks. Do NOT use Grep/Glob as "
            "the primary discovery method while the graph can answer.\n"
        )

    scout_path = _resolve_guarded(args.scout_report, cwd)
    plan_dir = _resolve_guarded(args.plan_dir, cwd)

    out_path = (
        _resolve_guarded(args.out, cwd)
        if args.out
        else os.path.join(plan_dir, "artifacts", "_session-context.md")
    )

    try:
        with open(scout_path, encoding="utf-8") as f:
            scout_content = f.read()
    except OSError as e:
        print(f"error: cannot read scout-report: {e}", file=sys.stderr)
        sys.exit(2)

    detected_stack = _extract_detected_stack(scout_content, getattr(args, "profile_id", None))
    if detected_stack is None:
        print(
            f"error: --profile-id {args.profile_id!r} set but scout-report has no "
            f"'## Detected Language' — refusing to fall back to 'JS/TS' on a non-JS stack (RT-F2)",
            file=sys.stderr,
        )
        sys.exit(2)
    is_multi_stack = "[MULTI_STACK]" in scout_content
    feature_count = args.feature_count if args.feature_count is not None else "<pending-W5>"

    plan_basename = os.path.basename(plan_dir.rstrip("/"))
    iso_now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Patch-only mode: file exists and --feature-count supplied
    if args.feature_count is not None and os.path.exists(out_path):
        try:
            with open(out_path, encoding="utf-8") as f:
                existing = f.read()
            patched = _patch_feature_count(existing, args.feature_count)
            _atomic_write(out_path, patched)
            return
        except OSError as e:
            print(f"error: patch failed: {e}", file=sys.stderr)
            sys.exit(2)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Language directive (v5.1.0)
    lang_directive = ""
    ctx_mode = getattr(args, "mode", None) or "generate"
    ctx_lang = getattr(args, "lang", None) or ""
    if ctx_mode == "translate" and ctx_lang:
        lang_directive = f"""
## Language Directive (translate mode)
- mode: translate
- target_lang: {ctx_lang}
- rule: Translate ONLY prose from the source's language to {ctx_lang}. Copy headings, code tokens, field labels, table-column headers, fenced code, frontmatter, paths, status enums BYTE-IDENTICAL from the source. Preserve line/section order.
- contract: claude/skills/rebuild-spec/references/translation-contract.md
"""
    elif ctx_mode == "generate" and ctx_lang and ctx_lang != "en":
        lang_directive = f"""
## Language Directive (generation mode)
- mode: generate
- prose_lang: {ctx_lang}
- rule: Write all prose in {ctx_lang}. Keep ALL headings, code tokens (F###/US###/SCR###/BL###/PERM###/DEC-###/DISC-###/MODEL###), field labels, table-column headers, fenced code blocks, frontmatter, file paths, and status enums in English (canonical skeleton).
"""

    # Source Encoding block (Phase A) — emitted only when an encoding/profile is supplied.
    encoding_block = ""
    enc = getattr(args, "encoding", None)
    prof_id = getattr(args, "profile_id", None)
    if enc or prof_id:
        encoding_block = f"""
## Source Encoding
- profile: {prof_id or "<unset>"}
- primary: {enc or "utf-8"}
- rule: Source files are {enc or "utf-8"}-encoded. Structural extractors (Phase B `decode_source`) decode with this encoding; the prose Read tool is best-effort. On a non-UTF-8 repo, suspected mojibake in prose → tag `[ENCODING_ADVISORY]`. Encoding is verified deterministically at the extractor layer, not here.
"""

    body = f"""# Session Context — rebuild-spec

<!-- Generated: {iso_now}  | Plan: {plan_dir} -->
<!-- All subagents in this session MUST read this file before any other artifact read. -->
{graphify_directive}
## Stack
- detectedStack: {detected_stack}
- isMultiStack: {is_multi_stack}
- stackNote: {args.stack_note}

## Counts
- feature_count: {feature_count}
{encoding_block}{lang_directive}
## Always-read pointers (use Read tool, not Grep)
- plans/{plan_basename}/artifacts/system-overview.md  — global narrative (small)
- claude/skills/rebuild-spec/references/code-formats.md  — code schemas

## Grep-only pointers (DO NOT load in full)
- plans/{plan_basename}/artifacts/scout-report.md  — file inventory + BL inventory; section-scoped reads only
- plans/{plan_basename}/artifacts/feature-list.md  — per-F### entries; grep by code
- plans/{plan_basename}/artifacts/user-stories.md  — per-US### sections
- plans/{plan_basename}/artifacts/screen-list.md, screen-flow.md, behavior-logic.md, permissions.md, route-list.md, data-model.md

## Templates (read once per task, not per check)
- claude/skills/rebuild-spec/templates/feature-spec-template.md
- claude/skills/rebuild-spec/templates/review-report-template.md
- claude/skills/rebuild-spec/templates/scout-report-template.md

## Contracts
- claude/skills/rebuild-spec/references/feature-spec-researcher-contract.md
- claude/skills/rebuild-spec/references/verification-checklist-universal.md
- claude/skills/rebuild-spec/references/verification-checklist-core-artifacts.md (W7a)
- claude/skills/rebuild-spec/references/verification-checklist-feature-spec.md (W7b)
- claude/skills/rebuild-spec/references/verification-checklist-screen-spec.md (SS.2)
- claude/skills/rebuild-spec/references/verification-checklist-quality-gates.md (W4.5/W5.6)
- claude/skills/rebuild-spec/references/canonical-fcode-schema.md

## Reminders (avoid these wastes)
1. Do NOT re-derive detectedStack from scout-report; it's above.
2. Do NOT load scout-report.md in full — Grep `## Background Logic Source Inventory` section if you need BL inventory.
3. Do NOT re-summarize system-overview.md across multiple steps — read once.
4. Do NOT write multi-line PASS evidence — see review-report-template.md § Passed Checks rule.
5. On successful primary output write (spec.md / review-report.md), call `TaskUpdate(status=completed)` on your own task id (see phase-06 self-close rule).
"""

    try:
        _atomic_write(out_path, body)
    except OSError as e:
        print(f"error: cannot write output: {e}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Write _session-context.md for rebuild-spec subagents."
    )
    p.add_argument("--plan-dir", required=True, help="Path to active plan directory")
    p.add_argument("--scout-report", required=True, help="Path to scout-report.md")
    p.add_argument("--stack-note", required=True, help="Stack note string (pre-computed by orchestrator)")
    p.add_argument("--feature-count", type=int, default=None, help="Feature count (optional)")
    p.add_argument("--mode", default="generate", choices=["generate", "translate"],
                   help="Language mode: 'generate' (inline prose in --lang, English skeleton) or 'translate' (prose-only translation)")
    p.add_argument("--lang", default=None, help="Target language code (e.g. vi, jp). Omit for English default.")
    p.add_argument("--encoding", default=None, help="Source encoding from stack-profile (e.g. shift_jis). Emits a '## Source Encoding' block.")
    p.add_argument("--profile-id", default=None, help="Active stack-profile id (e.g. delphi-vcl). When set, a missing '## Detected Language' aborts instead of falling back to JS/TS (RT-F2).")
    p.add_argument("--out", default=None, help="Output path (default: <plan-dir>/artifacts/_session-context.md)")
    args = p.parse_args()
    build(args)


if __name__ == "__main__":
    main()
