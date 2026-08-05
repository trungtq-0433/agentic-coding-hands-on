#!/usr/bin/env python3
"""Engine 2 — protocol-conformance boundary check (WARN-only, deterministic).

Parses the promoted `user-stories.md` and audits whether it APPLIED the per-stack IPE Step-3
merge rule + Step-4 anti-CRUD rule. Catches the 86-vs-354 over/under-merge shape deterministically,
citing the exact violated clause. No fan-out, no subagents, no graph dependency, no re-synthesis.

Engine 2 emits WARN / UNVERIFIABLE only — NEVER FAIL, and its findings NEVER increment Engine-1's
orphan/phantom/redundancy counts (the no-cross-feed invariant).

Stdlib only. Exit 0 always (advisory emitter).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import read_text_safe, resolve_docs_root, resolve_project_root  # noqa: E402
import _ipe_parse_lib as ipe_parse  # noqa: E402
import _ipe_conformance_lib as ipe_conf  # noqa: E402


def _resolve_screen_source(stack: str | None, explicit: str | None) -> tuple[str, str]:
    if explicit:
        return (explicit, f"--screen-source {explicit}")
    if stack:
        prof = (Path(__file__).resolve().parent.parent.parent / "rebuild-spec"
                / "references" / "stack-profiles" / f"{stack}.json")
        if prof.is_file():
            try:
                data = json.loads(prof.read_text(encoding="utf-8"))
                ss = data.get("screen_source")
                if ss:
                    return (ss, f"stack-profile {stack}.json screen_source={ss}")
            except (json.JSONDecodeError, OSError):
                pass
    return ("route-view", "default (no --stack/--screen-source given; assuming route-view web)")


def run(project_root: Path, docs_root_override: str | None, us_path_override: str | None,
        stack: str | None, screen_source_override: str | None) -> dict:
    docs_root = (Path(docs_root_override).resolve() if docs_root_override
                 else resolve_docs_root(project_root))
    us_path = (Path(us_path_override).resolve() if us_path_override
               else docs_root / "generated" / "user-stories.md")

    screen_source, ss_reason = _resolve_screen_source(stack, screen_source_override)

    if not us_path.is_file():
        return {"engine": "boundary", "boundary_status": "OK",
                "screen_source": screen_source, "screen_source_reason": ss_reason,
                "user_stories_present": False,
                "note": f"user-stories.md not found at {us_path} — nothing to check",
                "findings": []}

    read = read_text_safe(us_path)
    if read is None:
        return {"engine": "boundary", "boundary_status": "FAILED",
                "screen_source": screen_source, "screen_source_reason": ss_reason,
                "user_stories_present": True,
                "note": f"user-stories.md at {us_path} could not be decoded",
                "findings": []}

    text, _enc = read
    parsed = ipe_parse.parse(text)
    findings = ipe_conf.run_checks(parsed, screen_source)

    return {
        "engine": "boundary",
        "boundary_status": "OK",
        "screen_source": screen_source,
        "screen_source_reason": ss_reason,
        "user_stories_present": True,
        "counts": {
            "interactions": len(parsed.interactions),
            "screens_mapped": len(parsed.screen_to_us),
            "user_stories": len(parsed.us_titles),
        },
        "findings": findings,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Engine 2 — IPE protocol-conformance boundary check (WARN-only)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--docs-root", default=None)
    p.add_argument("--user-stories", default=None, help="explicit path to user-stories.md")
    p.add_argument("--stack", default=None, help="stack-profile name (resolves screen_source)")
    p.add_argument("--screen-source", default=None,
                   choices=["route-view", "dfm-form", "cobol-screen", "none"],
                   help="override the per-stack Step-3 keying")
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    result = run(project_root, args.docs_root, args.user_stories, args.stack, args.screen_source)

    payload = json.dumps(result, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(out)
        print(f"[boundary_conformance] wrote → {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
