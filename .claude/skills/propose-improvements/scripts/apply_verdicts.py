#!/usr/bin/env python3
"""Improvement-proposal Step 7 CLI — apply per-item KEEP/REVISE/DROP verdicts.

Authoritative implementation of `claude/skills/propose-improvements/references/apply-validations.md`.
Replaces the previous `researcher` subagent invocation. The orchestrator calls
this script via Bash; stdout is captured into its log buffer verbatim. After
exit 0, the orchestrator marks step-7 task completed.

Stdout contract:
  - All `warn:` / `drop:` / `revise:` log lines from verdict collection and
    per-item passes, then orphan-verdict `warn:` lines.
  - One `done: step-7 -> <abs path>` OR `skip: step-7 (artifact exists at <path>)`.
  - Exactly one trailer: `Status: DONE` | `Status: DONE_WITH_CONCERNS - <reason>`
    | `Status: BLOCKED - <reason>`.

Exit code: 0 for DONE / DONE_WITH_CONCERNS / skip. Non-zero only for BLOCKED.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_verdicts_lib import (  # noqa: E402
    demote_h2_to_h4,
    load_verdicts,
    recompute_rollup_heading,
    sanitize_title_for_log,
    sort_items_within_aspect,
    split_combined,
    split_rollups,
    strip_dedup_marker,
    title_to_slug,
    validate_revised_body,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Apply Phase-D verdicts to produce improvement-proposal.md (Step 7).",
        allow_abbrev=False,
    )
    p.add_argument("--combined-path", type=Path, required=True)
    p.add_argument("--validation-dir", type=Path, required=True)
    p.add_argument("--output-path", type=Path, required=True)
    p.add_argument(
        "--evidence-degraded-warns", type=str, default="",
        help="Newline-joined warns from step-5c manifest's evidence_degraded_warns array.",
    )
    return p.parse_args(argv)


def _print_status(status: str, reason: str = "") -> None:
    if reason:
        print(f"Status: {status} — {reason}")
    else:
        print(f"Status: {status}")


def _atomic_write(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _path_safe(path: Path, cwd: Path) -> bool:
    s = str(path)
    if "\x00" in s:
        return False
    try:
        path.resolve().relative_to(cwd.resolve())
    except ValueError:
        return False
    return True


def _apply_to_track(
    track: str,
    track_body: str,
    start_index: int,
    verdicts: dict,
    log_warns: list[str],
    log_drops: list[str],
    log_revises: list[str],
    consumed: set[int],
) -> tuple[str, int, int]:
    """Apply verdicts to one track body. Returns (output_body, next_index, unvalidated_for_this_track).

    Single-walk design: iterate `split_rollups` output (rollups → items) and assign
    sequential indices in document order. The earlier dual-walker design
    (parse_track_items + split_rollups paired positionally) silently misrouted
    verdicts when a `#### H4` existed outside any `### H3` rollup, because such
    pre-rollup items appear in `parse_track_items` but get absorbed into
    `track_header` by `split_rollups`, shifting the alignment.
    """
    if not track_body:
        return "", start_index, 0
    track_header, rollups = split_rollups(track_body)

    unvalidated_local = 0
    next_index = start_index
    out_chunks: list[str] = [track_header]

    for ru in rollups:
        surviving: list[str] = []
        for blk in ru.items:
            it_index = next_index
            next_index += 1
            consumed.add(it_index)

            # Extract title from the leading `#### <title>` line of this block.
            first_line = blk.splitlines()[0] if blk else ""
            it_title = first_line.lstrip(" #").strip()
            log_title = sanitize_title_for_log(it_title)

            verdict = verdicts.get(it_index)
            if verdict is None:
                log_warns.append(
                    f"warn: missing verdict for item-{it_index:02d} \"{log_title}\" — kept as-is"
                )
                surviving.append(blk)
                unvalidated_local += 1
                continue
            current_slug = title_to_slug(it_title)
            if verdict.item_slug and current_slug != verdict.item_slug:
                log_warns.append(
                    f"warn: verdict slug mismatch at item-{it_index:02d} "
                    f"(expected={current_slug}, got={verdict.item_slug}) — "
                    f"kept original (stale verdict — delete validation/ after regenerating combined-initial.md)"
                )
                surviving.append(blk)
                unvalidated_local += 1
                continue
            if verdict.decision == "DROP":
                log_drops.append(
                    f"drop: item-{it_index:02d} \"{log_title}\" — validator verdict"
                )
                continue
            if verdict.decision == "KEEP":
                surviving.append(blk)
                continue
            # REVISE
            body = verdict.revised_body
            if body is None or not body.strip():
                log_warns.append(
                    f"warn: revise-without-body for item-{it_index:02d} \"{log_title}\" — kept original"
                )
                surviving.append(blk)
                unvalidated_local += 1
                continue
            if not validate_revised_body(body):
                log_warns.append(
                    f"warn: revise-malformed for item-{it_index:02d} \"{log_title}\" — kept original"
                )
                surviving.append(blk)
                unvalidated_local += 1
                continue
            log_revises.append(
                f"revise: item-{it_index:02d} \"{log_title}\" — applied validator revision"
            )
            surviving.append(demote_h2_to_h4(body))

        if not surviving:
            continue  # drop the entire rollup + aspect-id comment.
        new_heading = recompute_rollup_heading(ru.rollup_heading or "", surviving)
        sorted_items, sort_warns = sort_items_within_aspect(surviving)
        log_warns.extend(sort_warns)
        parts = [new_heading]
        if ru.aspect_comment:
            parts.append(ru.aspect_comment)
        parts.append("")
        for blk in sorted_items:
            parts.append(blk.rstrip())
            parts.append("")
        out_chunks.append("\n".join(parts).rstrip())

    return "\n\n".join(out_chunks), next_index, unvalidated_local


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    cwd = Path.cwd().resolve()

    # Path-safety.
    if not _path_safe(args.combined_path, cwd):
        _print_status("BLOCKED", f"unsafe combined path: {args.combined_path}")
        return 2
    if not _path_safe(args.validation_dir, cwd):
        _print_status("BLOCKED", f"unsafe validation_dir: {args.validation_dir}")
        return 2
    plans_root = (cwd / "plans").resolve()
    try:
        args.output_path.resolve().relative_to(plans_root)
    except ValueError:
        _print_status("BLOCKED", f"output path outside plans/: {args.output_path}")
        return 2

    # Idempotency.
    if args.output_path.exists() and args.output_path.stat().st_size > 0:
        print(f"skip: step-7 (artifact exists at {args.output_path})")
        _print_status("DONE")
        return 0

    if not args.combined_path.is_file():
        _print_status("BLOCKED", f"combined missing at {args.combined_path}")
        return 2
    combined_raw = args.combined_path.read_text(encoding="utf-8")
    if not combined_raw.strip():
        _print_status("BLOCKED", "combined file missing/empty")
        return 2

    combined_text = strip_dedup_marker(combined_raw)
    header, tech_body, biz_body = split_combined(combined_text)
    if tech_body is None and biz_body is None:
        _print_status("BLOCKED", "combined proposal missing both '## Technical' and '## Business' sections")
        return 2

    verdicts, verdict_warns = load_verdicts(args.validation_dir)
    log_warns: list[str] = list(verdict_warns)
    log_drops: list[str] = []
    log_revises: list[str] = []
    validation_dir_missing = not args.validation_dir.is_dir()
    if validation_dir_missing:
        log_warns.append(
            f"warn: validation directory missing at {args.validation_dir} — defaulting all items to KEEP"
        )

    consumed: set[int] = set()
    unvalidated_total = 0
    next_index = 1
    output_tech, next_index, ut = _apply_to_track(
        "technical", tech_body or "", next_index, verdicts,
        log_warns, log_drops, log_revises, consumed,
    )
    unvalidated_total += ut
    output_biz, next_index, ub = _apply_to_track(
        "business", biz_body or "", next_index, verdicts,
        log_warns, log_drops, log_revises, consumed,
    )
    unvalidated_total += ub

    # Orphan verdicts.
    for idx, v in sorted(verdicts.items()):
        if idx not in consumed:
            log_warns.append(
                f"warn: orphan verdict at item_index={idx} "
                f"(slug={v.item_slug}, decision={v.decision.lower()}) — no matching item"
            )

    # Count evidence-degraded items.
    evidence_degraded_count = 0
    if args.evidence_degraded_warns:
        for line in args.evidence_degraded_warns.splitlines():
            if re.match(r'^warn: item-(\d+) ".*" evidence-degraded ', line):
                evidence_degraded_count += 1

    unvalidated_total += evidence_degraded_count
    if validation_dir_missing:
        # Per spec — count = total items consumed.
        unvalidated_total = len(consumed)

    # Assemble output.
    parts: list[str] = []
    if header.strip():
        parts.append(header.rstrip())
    if unvalidated_total > 0:
        plural = "item" if unvalidated_total == 1 else "items"
        parts.append(
            f"> ⚠️ **{unvalidated_total} {plural} shipped without complete validation.** "
            f"Review the orchestrator log (`warn:` lines) before sharing this proposal."
        )
    if output_tech.strip():
        parts.append(output_tech.rstrip())
    if output_biz.strip():
        parts.append(output_biz.rstrip())
    final = "\n\n".join(parts).rstrip() + "\n"

    try:
        _atomic_write(args.output_path, final)
    except OSError as exc:
        _print_status("BLOCKED", f"write failed: {exc}")
        return 2

    # Emit logs in spec order.
    for w in log_warns:
        print(w)
    for d in log_drops:
        print(d)
    for r in log_revises:
        print(r)
    print(f"done: step-7 → {args.output_path.resolve()}")
    if log_warns or log_drops or log_revises:
        reasons: list[str] = []
        if log_warns:
            reasons.append(f"{len(log_warns)} warn(s)")
        if log_drops:
            reasons.append(f"{len(log_drops)} drop(s)")
        if log_revises:
            reasons.append(f"{len(log_revises)} revise(s)")
        _print_status("DONE_WITH_CONCERNS", "; ".join(reasons))
    else:
        _print_status("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
