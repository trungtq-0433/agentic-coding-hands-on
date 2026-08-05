# Jobs Researcher Contract (Wave J.1 — rebuild-spec v26.1.0)

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other read.
Do NOT re-derive information already present there.

## Synthesis Sources (read ALL before drafting any job)

Read these upstream artifacts from `docs/` (already promoted by the core pass — NOT
`plans/<active>/artifacts/`):

- `docs/system/business-rules.md` — `behavior-logic.md` is mirrored here in plain language;
  read `behavior-logic.md` (see below) for the machine-readable BL### entries.
- `docs/generated/behavior-logic.md` — PRIMARY source. Filter to BL### entries whose
  `**Type**` is `scheduled-job`, `queue-worker`, or `custom-command`. Every qualifying entry
  becomes exactly one JOB### section — this is a re-projection, not a re-detection.
- `docs/generated/entities.md` — entity/table names for the `## Data Touched` field.
- `references/bl-source-patterns.md` — per-stack detection convention reference (includes the
  systemd-timer row); use it to understand WHERE a given BL### entry's source lives, never to
  re-classify a BL### into a different type than `behavior-logic.md` already assigned it.

## Read-Only Static Scan Contract (STRICT — F7)

This is a **read-only, static-analysis-only** research task. You are AUTHORIZED to read source
code directly via Grep/Read (job handler bodies, schedule config, systemd unit files) to fill in
Purpose / Schedule / Data Touched / Failure-Retry detail beyond what `behavior-logic.md` already
states.

You are **NEVER** authorized to:
- Execute the target project's build or task tooling to enumerate jobs (`rake -T`, `crontab -l`,
  `systemctl list-timers`, `bundle exec sidekiq`, or any shell-out to the target app/runtime).
- Run any command that boots, imports, or evaluates target-project code.
- Connect to a queue broker, database, or scheduler service to "check" a job's real-world state.

This mirrors `references/structural-extractor-contract.md` § "never execute": a scan that shells
out to or boots untrusted repo code is a security risk, not a research convenience. Everything
needed to document a job is discoverable by reading text (source files, config files, systemd
unit files) — never by running it.

## Gate/Filter (STRICT — hard-omit)

- Only `behavior-logic.md` entries with `**Type**` ∈ `{scheduled-job, queue-worker,
  custom-command}` qualify.
- Only entries with a REAL job-invocation site (a concrete `**Source File**` +
  `**Source Symbol**`, not a stub/abstract base) qualify — `behavior-logic.md`'s own Cardinality
  Contract already enforces this upstream; do not re-relax it here.
- Below threshold (wrong type, or the BL### entry itself is a stub) → **zero output** for that
  entry. No partial job section, no thin placeholder.

## JOB### Code Grammar (slug-sanitized — F7)

Format: `JOB###_NameSlug` — 3-digit zero-padded, **file-global** (never resets per type or per
directory; F13 — this is a single artifact, not a per-dir namespace).

Regex: `^JOB\d{3}_[A-Za-z0-9]+$`

- Sequential assignment in order of discovery (JOB001, JOB002, ...).
- Slug derivation mirrors the F###/BL### convention (`_slug_lib.py::derive_slug`'s algorithm —
  split the job name on non-alphanumeric boundaries, capitalize each token, concatenate, cap at
  36 chars): strip everything but `[A-Za-z0-9]`, CamelCase the remaining tokens. Never emit a
  space, `/`, `:`, `;`, shell metacharacter, or any character outside `[A-Za-z0-9_]` — the
  resulting slug becomes a markdown heading anchor and MUST be injection-safe.
- MUST NOT contain shell metacharacters (enforced by regex).

## Citation Rule (anti-hallucination)

Every JOB### section MUST carry a `**Source**` field with a `` `file:line` `` citation (the
concrete handler/command/unit-file location — may differ from the BL### entry's own
`**Source File**`/`**Source Symbol**` fields if this job adds detail the BL entry didn't cite,
e.g. a `config/schedule.rb` line for the cron expression vs. the job class file itself).

- If a claim (schedule, retry policy, data touched) cannot be source-cited → do NOT assert it.
  Omit the field's content and write `N/A — not found in source.` rather than inventing one.
- An unsourced `**Source**` field (missing or empty) = **CRITICAL** contract violation
  (`validate_job_list.py` gates this).
- NEVER echo a literal secret/credential value into any field, even if one appears adjacent to
  the job's config (e.g. an `EnvironmentFile=` line in a systemd unit). Describe the config
  surface ("reads DB credentials from `EnvironmentFile=`"), never the value.
  `scripts/_credential_scrub_lib.py::assert_no_secrets()` is a hard CRITICAL gate on the
  promoted output — a leaked value fails the pass, it does not just get a warning.

## DRY Boundary (JOB### vs BL###)

- `BL###` = the canonical inventory entry (`behavior-logic.md`) — one per background-logic unit,
  file-global, owned by the core pass.
- `JOB###` = the operational-detail expansion of a BL### that is a job-shaped type — owned by
  this standalone pass.
- Every JOB### section's `**BL Ref**` field MUST cite exactly one `BL###` code.
- Do NOT re-list the BL### entry's `**Description**`/`**Related Modules**` verbatim — add ONLY
  the job-specific operational fields (`## Schedule / Trigger`, `## Data Touched`,
  `## Failure / Retry Behavior`) that `behavior-logic.md` does not already carry in structured
  form. Verbatim duplication is a DRY violation (`validate_job_list.py` flags it).

## Systemd-Timer Detection (new surface — the one genuinely new BL-source pattern)

`references/bl-source-patterns.md` now carries a `systemd-timer` row (added for this pass).
Timer units may live outside the app repo's own language surface (`/etc/systemd/system/*.timer`
+ paired `*.service`, or an in-repo `deploy/systemd/` directory). If `behavior-logic.md` already
carries a `[SIGNAL_INFERRED]` entry that turns out to be a systemd timer, use the paired
`.service`/`.timer` unit file pair as the `**Source**` citation (the `.timer` for the schedule,
the `.service`'s `ExecStart=` for the invoked binary/command).

## Output

Single file: `plans/<active>/artifacts/job-list.md`. Template: `templates/job-list-template.md`.

Zero qualifying `behavior-logic.md` entries → still emit the file with the header/preamble intact
and `## Job Index` containing only `_(no scheduled-job/queue-worker/custom-command entries
detected)_` — never omit the file.

### Confidence Companion (advisory sidecar)

`confidence-report_job-list.md` is NOT part of the researcher's output above. It is emitted
automatically by `scripts/derive_confidence_report.py` (deterministic, not authored by the
researcher) after promotion — a citation-coverage sidecar, never gated, never asserted. See
`references/confidence-report-contract.md`.

## Completion Marker

After the file is fully written (including the zero-qualifying-entries case), write:

```
plans/<active>/artifacts/.job-list.completed
```

Non-zero output: zero-byte file. Zero output: file content = `no_jobs_inferred`.

## See Also

- `references/bl-source-patterns.md` — per-stack detection convention (incl. systemd-timer row)
- `references/structural-extractor-contract.md` § "never execute" — the read-only contract this
  file mirrors
- `templates/job-list-template.md` — output template
- `scripts/_credential_scrub_lib.py` — secrets-scrub coverage (extended to `.service`/`.timer`)
