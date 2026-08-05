---
name: feedback-docs-vs-plans-boundary
description: Rule for deciding whether a phase-file/clarifications.md detail belongs in docs/ or stays in plans/
metadata:
  type: feedback
---

When a completed phase's plan file (`plans/{plan}/phase-XX-*.md`) or `clarifications.md` contains
operational detail, judge by **who opens the file and when**, not by "more docs = safer":

- **Moves to `docs/` (event-ops runbook, README):** anything an operator needs *during* a live
  event/incident, when they will only open `docs/`, never `plans/`. Example: phase-02 added an
  RPC-based "grant more Secret Box mid-event" procedure with ready-to-run SQL — this went into
  `docs/runbook-su-kien.md` verbatim (verified the RPC signature and grant SQL against
  `supabase/migrations/0004_secret_box_tables.sql` first).
- **Stays in `plans/clarifications.md` / phase file:** constraints aimed at *whoever writes the next
  phase's code* (e.g. "`select('*')` on `profiles` now 42501s, list columns explicitly" — a
  column-level-grant fallout from an anonymity leak fix). These are already the authoritative sink
  per the MoMorph clarification protocol, future implementer subagents get them as direct context,
  and the schema is still evolving (phase-04 adds more RPCs) — duplicating into `docs/` mid-plan
  risks two sources of truth drifting apart. Verdict given: "không cần" (not needed), explicitly.
- **Existing annotations that are technically correct but under-specify a new risk**: strengthen
  in place rather than adding a new file. Example: `supabase:reset` was already labeled "xoá sạch
  dữ liệu" (wipes data) — true, but once `seed.sql` became a real 289-line demo dataset (50 depts,
  30 kudos, etc.), the real risk is that reset **silently repopulates with fake-but-realistic
  data** rather than leaving the DB empty. Added one paragraph to the existing section instead of
  a new doc — YAGNI, the existing section was the right home.

**Why:** the user's instructions for this task were explicit — "đừng đẻ tài liệu chỉ để có tài liệu"
(don't create docs just to have docs) and "verdict rõ ràng: cập nhật mấy file, hay không cần gì" — a
three-way review is expected to conclude "no action" on at least one item when the existing sink is
already correct for its audience, not to pad every finding into a doc change.

**How to apply:** for future Sun Kudos phases (phase-03 onward), keep asking "does the event-day
operator need this in `docs/`, or does only the next implementer need it via `clarifications.md`?"
before proposing any docs change. See [[project-sun-kudos-docs-layout]].
