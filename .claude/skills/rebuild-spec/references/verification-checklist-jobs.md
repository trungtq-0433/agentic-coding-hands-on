<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Verification Checklist: JobList (`--jobs` pass, J.3)

See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope:** Loaded ONLY by the `--jobs` pass reviewer (J.3). Do NOT load in the default (core)
W7a run.

## JobList

**Cross-refs:** `docs/generated/behavior-logic.md` (BL### source-of-record, filtered to
`scheduled-job`/`queue-worker`/`custom-command`), `references/bl-source-patterns.md` (per-stack
detection convention, incl. systemd-timer)

**Deterministic checks (J.2 `validate_job_list.py` — pre-J.3):** citation presence per JOB###
section, JOB### regex + file-global uniqueness, `**BL Ref**` presence + resolves to a real BL###
in `behavior-logic.md`, `.job-list.completed` marker, secrets gate (`assert_no_secrets()` —
CRITICAL, hard gate). Rule IDs passing J.2 are marked `[deterministic-pass]` — skip in semantic
review. Dedup vs `behavior-logic.md` is NOT a deterministic check — it stays a semantic review
responsibility, see JOB-S4 below.

**Semantic review rules (JOB-S1..JOB-S6):**
- [ ] **JOB-S1 Citation accuracy (spot-check):** for >=2 JOB### sections, Read the cited
  `**Source**` `file:line` and verify the code actually contains the schedule/handler/invocation
  logic described. Cited line is a comment or unrelated code → critical.
- [ ] **JOB-S2 Gate respected — type filter:** every JOB### section's `**BL Ref**` resolves to a
  `behavior-logic.md` entry whose `**Type**` is `scheduled-job`, `queue-worker`, or
  `custom-command`. A JOB### expanding a `mail`/`event-listener`/other non-job BL### type →
  critical (gate violation).
- [ ] **JOB-S3 No fabricated schedule/retry:** `## Schedule / Trigger` and
  `## Failure / Retry Behavior` content must be traceable to source, OR explicitly
  `N/A — not found in source.`. An invented cron expression or retry count with no citation →
  critical.
- [ ] **JOB-S4 DRY — no BL### re-listing:** `## Purpose` may summarize, but MUST NOT be a
  verbatim copy of the BL### entry's `### Description`. `## Data Touched` MUST NOT re-list the
  BL### entry's `### Related Data Models` bullet-for-bullet with no additional detail — if
  identical, it should have cited the BL### entry via `**BL Ref**` instead of duplicating.
- [ ] **JOB-S5 No secret leakage (spot-check beyond the deterministic gate):** for any job whose
  source touches a `.env`/`application.yml`/systemd `Environment=` line, confirm the researcher
  described the config surface without echoing a literal secret value. The deterministic
  `assert_no_secrets()` gate catches known patterns; this rule catches novel leak shapes (e.g. an
  inline API key pasted into `## Purpose` prose) that a regex pattern wouldn't match.
- [ ] **JOB-S6 systemd-timer pairing:** for any job sourced from a systemd unit, confirm BOTH the
  `.timer` (schedule) and `.service` (`ExecStart=`) files were consulted — a citation to only one
  half of the pair (e.g. `.timer` alone, no `ExecStart=` command) is incomplete evidence for
  `## Purpose`/`## Schedule / Trigger` and should be flagged.

**Critical edge cases:**
- JOB### section without a `**Source**` citation → critical (contract violation)
- JOB### code not matching `^JOB\d{3}_[A-Za-z0-9]+$` → critical
- Duplicate JOB### code (file-global — never resets per type) → critical
- `**BL Ref**` missing, or citing a BL### that does not exist in `behavior-logic.md` → critical
- A detected secret literal anywhere in `job-list.md` → critical (hard gate, `validate_job_list.py`)
- `.job-list.completed` marker absent after J.1 → warning

**Advisory (non-defect):** `confidence-report_job-list.md` beside the promoted job-list.md is an
optional, best-effort sidecar (`scripts/derive_confidence_report.py`, v25.2.0). Its absence is
NOT a defect — do NOT flag a missing companion as a review finding. See
`references/confidence-report-contract.md`.

## Failure Trap Assertions (JobList-specific)

- **Trap — type-filter violation:** a JOB### section whose BL Ref points to a non-job BL### type
  (e.g. `mail`, `middleware`) fabricates a job that the gate should have excluded → critical.
- **Trap — DRY violation masquerading as detail:** a `## Data Touched` list that is a verbatim
  copy of the BL### entry's own related-data-models bullets with zero job-specific annotation
  (no read/write direction, no table-level detail) is duplicated content, not expanded detail.
