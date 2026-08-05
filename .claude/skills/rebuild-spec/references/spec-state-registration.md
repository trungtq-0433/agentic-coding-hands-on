<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows|screens paths — all references here are output targets or internal definitions -->
# Spec State Registration Recipe

**Owner:** rebuild-spec (state schema authority)
**Consumed by:** takumi Stage 1.5 orchestrator — link only, never inline.

This recipe is the authoritative checklist for registering a takumi-authored spec into all
rebuild-spec state files. Follow every step in order.

This recipe runs at **PROMOTE time** (implementation start), NOT at author time. Authoring writes a
draft to the plan dir only (see `claude/skills/rebuild-spec/references/spec-stage-procedure.md`). When
`/tkm:takumi <plan>` begins forging, the orchestrator runs § Promote below, which executes Step 0
then Steps 1–9 in order.

---

## Promote — copy plan-dir draft into docs/ (run at implement start)

**Trigger:** implement-start, BEFORE Forge (Stage 3) / TaskList — whichever run actually begins
forging. Two equivalent entry points (the recipe is discipline-agnostic):
- `code` discipline → Stage 0 step 8 (after blueprint load at Stage 0 step 4; the blueprint already exists).
- forging disciplines (interactive/auto/parallel/no-test/fast) → the **Stage 3 Promote Gate** (after
  blueprint approval at Rest Point 2). This is the common case: author + forge in ONE session.
Runs only when `plan.md` frontmatter has `spec_draft:` pointing at a plan-dir draft (idempotent — once
repointed to `spec:`, a later pass skips). Never re-litigated for `spec_waived:` / `work_type: deliverable`.

**Shape detection (SINGLE vs SYSTEM).** Inspect the `spec_draft:` target:
- contains a `feature-list.md` (i.e. `spec_draft:` is the `plans/<plan_dir>/spec/` dir) → **SYSTEM** →
  run **§ Promote — SYSTEM** below (loops this single-feature recipe over every feature folder).
- otherwise (`spec_draft:` is a single `spec/<slug>/` folder) → **SINGLE** → run P0–P5 as written here.

**P0. Run-type detection.** Read the draft's `technical-spec.md` frontmatter:
- `fcode:` ABSENT → **NEW feature** → run Step 0 (allocate + reserve + dup-check).
- `fcode: F###` PRESENT → **EXISTING-feature update** → SKIP Step 0 allocation; reuse that `F###`;
  verify it still exists in `docs/_canonical-fcodes.json` (if missing, treat as NEW and allocate).

**P1. Write rollback sentinel BEFORE any copy/registration:**
```json
// docs/.spec-promote-pending.json
{"fcode":"F###","run_type":"new","plan_dir":"plans/260615-0859-...","slug":"F###_Slug","from":"plans/<plan_dir>/spec/<slug>/","screens":["SCR###_Name"],"ts":"<ISO-8601 UTC>"}
```
- `run_type` (`new`|`existing`) is set from the P0 detection — it makes a later REVERT deterministic
  (only `new` runs remove the reservation/feature-list rows). Write it now, while run-type is known.
- `screens` lists any `SCR###` dirs this promote will copy/overwrite in `docs/screens/` (empty if none)
  — REVERT restores exactly these.
- For NEW features the `fcode` is the one just reserved in Step 0 — write the sentinel AFTER Step 0's
  reservation so the code is known, but BEFORE the docs copy.

**P2. Copy draft → docs.**
- NEW: copy `plans/<plan_dir>/spec/<slug>/` → `docs/features/F###_Slug/` (rename slug to `F###_Slug`).
  Allocate `SCR###` for any plan-local screen draft and copy → `docs/screens/SCR###_Name/spec.md`.
- EXISTING: overwrite `docs/features/F###_Slug/` from the plan-dir draft (the old shipped spec is
  replaced here — this is the first and only moment it changes).

**P3. Register.** Run Steps 1–9 below in full (NEW) or the EXISTING-feature subset (Steps 2–4, 8, 9 —
the entry already exists, so update in place rather than append; no contiguity append). For EXISTING
updates that changed a screen body, re-run Step 6 (screen-sha placeholder) so the sha matches the new
content; skip Step 6 if no screen body changed.

**P4. Flip status.** Set `status: draft → implemented` in the promoted `technical-spec.md`. Add
`fcode: F###` if it was absent (NEW). Preserve all other content.

**P5. Repoint `plan.md`, then leave the sentinel in place.** Replace `spec_draft: <from>` with
`spec: docs/features/F###_Slug/` (also done by takumi `workflow-steps.md` Stage 0 step 8). Leave
`docs/.spec-promote-pending.json` in place — it is deleted by takumi Stage 6 on clean delivery, or
repaired by a future Stage 0 promote-sentinel check (REVERT/KEEP).

**Draft retention:** the `plans/<plan_dir>/spec/<slug>/` draft is NOT deleted after promote — it stays
as plan-local history. Promote does not re-copy it on a second run (Stage 0 step 8 skips once `spec:`
is set), so retaining it is safe.

---

## Promote — SYSTEM (multi-feature)

When `spec_draft:` contains a `feature-list.md`, the draft is N features (folders) + the feature-list.
This section LOOPS the single-feature recipe above; only the deltas below differ. Authoring guarantees
provisional codes `F001..FNNN` and no `fcode:` on NEW features (existing features carry their real
`fcode:`).

**Step order is load-bearing for crash-safety:** S1 → S2 (reserve+verify) → **S3 (sentinel)** →
S4 (remap) → S5 (loop) → S6. The sentinel is written BEFORE the remap and BEFORE any copy so that a
crash at any later point is recoverable; reservation rows (S2) are the ONLY state written before the
sentinel, and S2 self-cleans on its own failure.

**S1. Per-feature run-type.** For each feature folder, read its `technical-spec.md` frontmatter:
`fcode:` ABSENT → **new**; `fcode: F###` PRESENT (and still in `docs/_canonical-fcodes.json`) →
**existing** (reuse + overwrite). Record the run-type per feature; the draft MAY mix the two.

**S2. Batch reservation (NEW subset only).** Count the NEW features (`#new`). **If `#new == 0`
(all-existing batch), SKIP this step entirely.** Otherwise run Step 0 ONCE to allocate a **contiguous
block** `[max+1 .. max+#new]` (max = highest across `_canonical-fcodes.json` + `feature-list.md`).
Write all `#new` reservation rows, then **re-read and verify every row in the block counts == 1**. On
collision → **remove the rows you just appended this session, then HARD-ABORT** the whole promote
(no sentinel yet, nothing copied). Also allocate `SCR###` codes for every plan-local screen draft
across ALL features in the same pass (max from `screen-list.md`), giving each feature its own
provisional→real `SCR###` map. EXISTING features reuse their code (no allocation). Build the
**provisional→real F### map** `Fk(draft) → Fxx(real)` ordered by feature-list row order (existing
features map to their own code).

**S3. Write sentinel v2 (BEFORE the remap and any copy).** One sentinel for the whole batch — write it
NOW, immediately after S2's verify passes, so the reservation rows are never orphaned:
```json
// docs/.spec-promote-pending.json  (v2 — SYSTEM)
{"run_type":"system","plan_dir":"plans/260615-...","ts":"<ISO-8601 UTC>",
 "features":[{"fcode":"F013","run_type":"new","slug":"F013_Storefront","from":"plans/<plan_dir>/spec/storefront/","screens":["SCR007_Catalog"]},
             {"fcode":"F002","run_type":"existing","slug":"F002_Auth","from":"plans/<plan_dir>/spec/auth/","screens":[]}]}
```
Backward-compat: a sentinel WITHOUT `features[]` is a legacy SINGLE sentinel — the original
single-feature P0–P5 / rollback branches handle it unchanged.

**S4. Apply the remap (promote owns it).** Using the F### + per-feature `SCR###` maps, rewrite EVERY
surface that stores a code:
- feature folder name `<slug>` → `F###_Slug`
- `technical-spec.md` `fcode:`
- inline occurrences of provisional codes in the body of `technical-spec.md`, `business-context.md`,
  `screens.md`, `edge-cases.md` (4-file set) and any `phase-XX-*.md` body prose
- `feature-list.md` codes
- every `phase-XX-*.md` frontmatter `feature: F###` (provisional → real; comma-separated lists
  element-wise)

Then verify: `grep -rnE 'F[0-9]{3}' plans/<plan_dir>/spec/ plans/<plan_dir>/phase-*.md` (plan dir
ONLY — never the repo) and confirm no provisional code from the `Fk(draft)` range survives.

**S5. Loop P2–P4 per feature** (copy → register Steps 1–9 → flip status), using each feature's real
code + its `SCR###` map from S2. **Run Step 8 (`feature-list.md` + `id_contiguity` commit) exactly
ONCE, after the loop** — append all N rows, merge the draft `feature-list.md` Feature Details into
`docs/generated/feature-list.md`, then run the contiguity check on the merged file. (Because Step 8 is
deferred, NO `feature-list.md` rows exist mid-loop — relevant to rollback below.)

**S6. P5 repoint (list form).** Replace `spec_draft: plans/<plan_dir>/spec/` with a YAML list under
`spec:` — one entry per promoted feature (new + existing):
```yaml
spec:
  - docs/features/F013_Storefront/
  - docs/features/F002_Auth/
```
Tooling reading `spec:` MUST accept both a scalar (SINGLE) and a list (SYSTEM). Leave the sentinel for
Stage 6 cleanup.

---

## Promote — SYSTEM-DOC (single-file architecture/permissions)

For forward-drafted system narratives (`docs/system/architecture.md` / `permissions.md` — see
`spec-authoring-contract.md` § Forward-Authored System Docs). These are **SINGLE files, NOT 4-file
feature dirs** — so the feature § Promote recipe does NOT apply: **no F### allocation, no Step 0
reservation, no `_canonical-fcodes.json` entry, no screen sha, no `feature-list.md` row.** Runs
ALONGSIDE the feature promote at the same implement-start point (Stage 3 Promote Gate / Stage 0 step 8).

**Trigger:** the plan dir has one or more `spec/system/*.md` drafts (recorded in `plan.md`).

**Steps (lightweight, per draft):**
- **D1. Sentinel branch.** Record the system docs in the promote sentinel so a crash is recoverable —
  add a `system_docs` array to whichever sentinel this run writes (SINGLE or SYSTEM):
  `"system_docs":["docs/system/architecture.md","docs/system/permissions.md"]` (only the ones promoted).
  **INVARIANT (MED-3):** `system_docs` is always an *addendum* to a feature sentinel that already carries
  an `fcode`/`run_type` — it MUST NOT be written as a standalone sentinel. Forward-draft only fires for
  `work_type: feature` + `sddMode: on`, which always co-promotes ≥1 feature, so a feature sentinel always
  exists to attach to. This guarantees the Stage 0 SINGLE recovery branch always has an `fcode` to act on
  and never executes `git checkout docs/features/<undefined>`. A future change that forward-drafts system
  docs on a waived/deliverable path would break this invariant — if you add such a path, first make the
  Stage 0 SINGLE branch tolerate an absent `fcode` (skip the feature-dir checkout, revert only `system_docs`).
- **D2. Copy.** `plans/<plan_dir>/spec/system/<name>.md` → `docs/system/<name>.md` (atomic copy).
- **D3. Flip status.** Set `status: draft → implemented` in the promoted file.
- **D4. Leave the sentinel** for Stage 6 cleanup (deleted alongside the feature sentinel).

**Idempotent guard:** if `docs/system/<name>.md` is already promoted this run (sentinel already lists it,
or no `spec/system/*` draft remains) → skip. **No repoint needed** — system docs are not referenced by a
`spec:`/`spec_draft:` frontmatter key (those track the feature set), so nothing in `plan.md` changes.

Reconcile: when the post-forge Core pass next runs (takumi Step 6.a-pre gen gate — auto if Core was
absent, else via re-baseline advisory / manual `/tkm:rebuild-spec`) it regenerates `docs/system/*` from
the as-built code. The forward draft is intentionally reconcilable; design rationale lives in ADRs.

---

## Step 0 — Reservation Claim (F6 — run at PROMOTE, NEW features only)

**Purpose:** prevent two parallel sessions from allocating the same F### (read-modify-write race).

**SYSTEM batch:** when invoked from § Promote — SYSTEM S2, allocate a **contiguous block** of `#new`
codes `[max+1 .. max+#new]` in one pass — write ALL `#new` reservation rows, then re-read and require
every row in the block to count == 1 (step 5 applied to each). Steps 1–6 below are otherwise identical
(one code → a block).

1. Read the maximum allocated F### across BOTH sources; take the higher value:
   - `docs/_canonical-fcodes.json` → `features` array sorted ascending → last entry's `fcode`
   - `docs/generated/feature-list.md` → highest `F###` code in the Feature Hierarchy table

2. **Greenfield (F11):** if NEITHER file exists (or both are absent/empty), default max to `0`
   → allocate `F001`. Create the missing files with minimal valid skeletons in Step 2 below.

3. Allocate `max_f + 1` → new `F###` (zero-padded to 3 digits: `F001`, `F042`, `F100`).
   Repeat for screens using `docs/generated/screen-list.md` → highest `## SCR###` heading
   (default to `SCR001` if absent).

4. **Write the reservation claim** into `docs/_canonical-fcodes.json` immediately:
   - If the file exists: append a skeleton entry `{"fcode": "F###", "name": "RESERVED", "slug": "F###_Reserved", "priority": "P1", "type": "mixed", "related": {"screens":[],"user_stories":[],"routes":[],"models":[],"bl":[],"perms":[]}}` to the `features` array.
   - If the file does not exist: create it with the skeleton structure (see Step 3 for full format).

5. **Re-read `docs/_canonical-fcodes.json`** immediately and count occurrences of the claimed
   `F###`. If count > 1 → a parallel session already claimed the same ID → **HARD-ABORT**.
   Do NOT copy the draft. Report: "ID collision on F### — another session claimed it first.
   Retry with the next available ID." Stop.

6. If count == 1 → the claim is unique. Proceed to copy the draft (Promote P2).

---

## Promote-Failure Rollback (crash/abort during § Promote)

If § Promote fails after P1 (sentinel written) but before P5 success, branch on the sentinel's
`run_type` field (deterministic — no need to infer):

**`run_type: new`:**
- `git checkout HEAD -- docs/features/F###_*` (removes the just-copied tree). For a NEW feature this
  path did not exist before, so `git checkout` removes it cleanly.
- For each `SCR###` in the sentinel's `screens`: `git checkout HEAD -- docs/screens/SCR###_*`.
- Remove the `F###` reservation row from `docs/_canonical-fcodes.json` and the `feature-list.md` row.
- If `plan.md` was already repointed (`spec:` present, `spec_draft:` gone), restore it: replace `spec:`
  with `spec_draft: <from>` (the sentinel's `from` value).
- Delete `docs/.spec-promote-pending.json`. The plan-dir draft is untouched — re-run is safe.

**`run_type: existing`:**
- `git checkout HEAD -- docs/features/F###_Slug/` (restores the shipped spec).
- For each `SCR###` in the sentinel's `screens`: `git checkout HEAD -- docs/screens/SCR###_*`
  (restores the previously shipped screen spec).
- `docs/_canonical-fcodes.json` untouched (no new row).
- If `plan.md` was already repointed, restore `spec_draft: <from>` as above.
- Delete the sentinel.

**`run_type: system`** (sentinel v2 with a `features[]` array — full-batch atomic revert):
- Iterate every entry in `features[]` and apply its OWN per-entry branch: `run_type: new` → the
  `new` steps above (git checkout the dir + screens, remove its `_canonical-fcodes.json` reservation
  row, and remove its `feature-list.md` row **if present**); `run_type: existing` → the `existing`
  steps above (git checkout the dir + screens; no row removal).
- **`feature-list.md` rows removal is conditional:** SYSTEM Step 8 is deferred to AFTER the whole loop
  (S5), so a mid-loop crash leaves NO `feature-list.md` rows — the removal is then a no-op. Only a
  crash during/after Step 8 will have rows to remove. "Remove if present" — never error on absent.
- `git checkout` / row-removal for a feature not yet reached by the loop is a clean no-op (it never
  touched `docs/`); its reservation row (written in S2) is still removed.
- After all entries are reverted, restore `plan.md`: if it was repointed to the `spec:` list, replace
  it with `spec_draft: plans/<plan_dir>/spec/` (the draft dir is untouched — re-run is safe).
- Delete the sentinel.

**`system_docs` branch (any sentinel that carries a `system_docs` array — from § Promote — SYSTEM-DOC):**
- For each path in `system_docs`: `git checkout HEAD -- <path>` (e.g. `docs/system/architecture.md`).
  A NEW system doc that did not exist before is removed cleanly; an updated one is restored to shipped.
- No reservation row / feature-list row / `_canonical-fcodes.json` entry to remove (system docs write
  none). No `plan.md` repoint to undo (system docs are not tracked by `spec:`/`spec_draft:`).
- This branch runs ALONGSIDE whichever `run_type` branch applies (the same sentinel carries both the
  feature data and the `system_docs` array); the sentinel is deleted once after both are reverted.

---

## Fast-Discipline Subset

`--fast` authors only `technical-spec.md` (minimal delta) to the plan dir; promote copies that single
file and runs the REDUCED registration subset below. The other 3 feature files do not exist yet.

| Step | Fast mode |
|------|-----------|
| 0 (reservation claim) | RUN |
| 1 (greenfield skeletons) | RUN if files absent |
| 2 (`_canonical-fcodes.json` real entry) | RUN |
| 3 (`_source-to-fcode.json`) | RUN |
| 4 (`.rebuild-state.json` cursor) | RUN |
| 5–6 (screen-list section + `screen_spec_shas`) | SKIP — fast never introduces new screens |
| 7 (4-file existence check) | SKIP — partial set is the sanctioned fast-mode state |
| 8 (`feature-list.md`) | RUN |
| 9 (duplicate check) | RUN the duplicate check, but KEEP the `.pending` marker |

Keeping `.pending` reuses the existing partial-write semantics (`canonical-fcode-schema.md`
folder lifecycle): validators skip the dir, and the later full `/tkm:rebuild-spec --features F###`
run removes the marker when it completes the 4-file set.

---

## Step 1 — Greenfield Skeleton Creation (F11)

If any of the following files are absent, create them with the minimal valid skeleton below
before writing real data. Reading a non-existent file is not an error in greenfield.

**`docs/_canonical-fcodes.json`** (if not yet created in Step 0):
```json
{
  "generated_at": "<ISO-8601 UTC now>",
  "plan": "<active-plan-slug>",
  "features": []
}
```

**`docs/_source-to-fcode.json`**:
```json
{
  "generated_at": "<ISO-8601 UTC now>",
  "index": {}
}
```

**`docs/.rebuild-state.json`**:
```json
{
  "primary_lang": "<draft lang: — fallback en>",
  "last_rebuild_sha": "",
  "last_feature_spec_run_sha": "",
  "fcode_index_sha": "",
  "doc_shas": {},
  "screen_spec_shas": {}
}
```

**`primary_lang` seed (greenfield first-promote ONLY):** If `docs/.rebuild-state.json` already
exists, SKIP this skeleton creation entirely — `primary_lang` is owned by the first run and is NEVER
re-seeded from a draft. Only when the file is absent: set `primary_lang` from the promoted draft's
`technical-spec.md` frontmatter `lang:` value (read it; missing → `en`). This is what makes a
greenfield non-English language choice stick for every later feature. A draft whose `lang:` disagrees
with an established `primary_lang` is a mismatch the orchestrator surfaces (warn + ask the user — see
`spec-authoring-contract.md` § Draft Frontmatter Schema), not silently re-seeds.

**`docs/generated/feature-list.md`**: create with minimal heading structure:
```markdown
# Feature List

## Feature Hierarchy

| # | Feature | Priority | Type | Status |
|---|---------|----------|------|--------|

## Feature Details
```

**`docs/generated/screen-list.md`**: create with minimal heading structure:
```markdown
# Screen List
```

---

## Step 2 — Update `docs/_canonical-fcodes.json`

Replace the reservation skeleton entry written in Step 0 with the real entry:

```json
{
  "fcode": "F042",
  "name": "Feature Name",
  "slug": "F042_FeatureName",
  "priority": "P1",
  "type": "ui|background|mixed",
  "related": {
    "screens": ["SCR042_ScreenName"],
    "user_stories": [],
    "routes": [],
    "models": [],
    "bl": [],
    "perms": []
  }
}
```

Rules:
- `slug` MUST match `^F\d{3}_[A-Za-z0-9]+$` (CamelCase from name, max 36 chars total).
- Keep the `features` array sorted by `fcode` ascending.
- Slug collision = HARD abort (rename before write).
- After writing, create the slug folder marker:
  `docs/features/F042_FeatureName/.pending` (zero-byte sentinel)

---

## Step 3 — Update `docs/_source-to-fcode.json`

For a greenfield feature with no source files yet, merge an empty index entry:

```json
{
  "generated_at": "<ISO-8601 UTC now>",
  "index": {}
}
```

An empty `{}` index is valid (RT-C5). If specific source files are already known (spec-first TDD),
add stub entries:
```json
{
  "index": {
    "app/models/Foo.php": ["F042"]
  }
}
```

**Merge rule:** append to existing `index` keys — never clobber existing entries.

After writing, recompute `fcode_index_sha`:
```
fcode_index_sha = sha256(canonical_json(index_object, sort_keys=True, separators=(",",":")))
```
Write the new `fcode_index_sha` into `docs/.rebuild-state.json`.

---

## Step 4 — Update `docs/.rebuild-state.json` (cursor + sha fields)

Write the following fields (merge — do NOT overwrite unrelated keys):

```json
{
  "last_feature_spec_run_sha": "<git rev-parse HEAD>",
  "fcode_index_sha": "<recomputed in Step 3>"
}
```

- `last_feature_spec_run_sha` is the diff base the `--feature-specs` planner reads.
  Setting it to HEAD means the next incremental run diffs from this point.
- Do NOT advance `last_rebuild_sha` (owned by the core pass only).
- Do NOT touch `doc_shas` keys (owned by the core pass only).

---

## Step 5 — Add SCR### section to `docs/generated/screen-list.md` (new screens only)

If Promote P2 allocated a new `SCR###` (from a plan-local screen draft), append an H2 section at the end:

```markdown
## SCR042_ScreenName

**Feature:** F042 — Feature Name
**Route:** /path/to/screen
**Description:** One-line description.
**States:** loading, empty, error, success
```

The body content (everything between `## SCR042_ScreenName` and the next `## SCR` heading)
is what the planner hashes. Write accurate content — the placeholder sha in Step 6 depends on it.

---

## Step 6 — Write Placeholder `screen_spec_shas` (F4 crash-recovery placeholder)

**This step prevents a pre-Stage-6 crash from marking the screen as unprocessed.**

Compute the section-body hash using the SAME algorithm the incremental planner uses:

```python
# Replicate _hash_screen_sections / _parse_screen_sections semantics
# from rebuild-spec/scripts/incremental_planner.py (match those functions, not pinned line numbers)

# 1. Read docs/generated/screen-list.md
# 2. For each ## SCR### heading, collect all lines until the next ## SCR heading
#    (the heading line itself is NOT included in the body)
# 3. body = "".join(body_lines)   ← keepends=True when reading
# 4. sha = hashlib.sha256(body.encode("utf-8")).hexdigest()

screen_spec_shas["SCR042"] = hashlib.sha256(section_body.encode("utf-8")).hexdigest()
```

Write into `docs/.rebuild-state.json`:
```json
{
  "screen_spec_shas": {
    "SCR042": "<sha256-hex of SCR042 section body in screen-list.md>"
  }
}
```

**CRITICAL:** This is the hash of the SCR### section BODY in `docs/generated/screen-list.md`,
NOT `sha256(spec.md content)`. Using the wrong source will cause the next incremental
`--screen-specs` run to mismatch and overwrite the authored spec.

**Merge rule:** append to existing `screen_spec_shas` — never clobber other SCR### entries.

Stage 6 (delivery) refreshes this value after the final spec edit. This is a correct-at-registration
placeholder, not a final value.

---

## Step 7 — Create Feature Spec Files

*(Fast discipline: SKIP this step — see § Fast-Discipline Subset.)*

Promote P2 copied these from the plan dir. Confirm they exist before proceeding:

```
docs/features/F042_FeatureName/
  technical-spec.md       ← status: draft, authored_by: takumi, fcode: F042
  business-context.md
  screens.md
  edge-cases.md
```

And for new screens:
```
docs/screens/SCR042_ScreenName/
  spec.md                 ← status: draft, authored_by: takumi, fcode: F042
```

If any file is missing, STOP and return BLOCKED — the researcher output is incomplete.

---

## Step 8 — Update `docs/generated/feature-list.md` (LAST — contiguity commit point)

**Write this file LAST.** The contiguity validator reads it to determine allocated F### range.
Writing it last means a crash mid-registration leaves no orphaned contiguity gap.

Add the feature to BOTH sections:

**Feature Hierarchy table** (append row, keep sorted by `#`):
```markdown
| 42 | F042 | Feature Name | P1 | mixed | draft |
```

**Feature Details section** (append subsection):
```markdown
### F042 — Feature Name

**Priority:** P1 | **Type:** mixed | **Status:** draft | **Slug:** F042_FeatureName

Brief one-line description from spec.

**Related:** screens: SCR042 | routes: — | models: —
```

---

## Step 9 — Post-Registration Duplicate Check (F6)

After all files are written, verify uniqueness across ALL state files:

1. `docs/_canonical-fcodes.json → features[].fcode` — assert F### appears exactly once.
2. `docs/generated/feature-list.md` — assert F### appears exactly once in hierarchy table.
3. `docs/.rebuild-state.json → screen_spec_shas` — assert SCR### appears at most once.
4. `docs/generated/screen-list.md` — assert `## SCR###` heading appears at most once.

If any duplicate is found → HARD-ABORT with a detailed conflict report.
Do NOT proceed to Stage 2.

When the duplicate check passes, DELETE the `docs/features/F###_*/.pending` marker (created in
Step 2). Validators (`iter_docs_technical_specs`) skip `.pending` dirs — leaving the marker in
place would permanently exclude the registered spec from every `--docs-root` validator run.
**Exception — fast discipline:** KEEP the marker; the partial set must stay excluded until the
full `/tkm:rebuild-spec --features F###` run completes it (see § Fast-Discipline Subset).

---

## State-File Write Ordering (Summary)

```
Step 0  _canonical-fcodes.json (reservation claim)     ← FIRST
Step 2  _canonical-fcodes.json (real entry)
Step 3  _source-to-fcode.json
Step 4  .rebuild-state.json (cursor + fcode_index_sha)
Step 5  screen-list.md (new SCR### section)
Step 6  .rebuild-state.json (screen_spec_shas placeholder)
Step 7  docs/features/ + docs/screens/ (copied from plan dir by Promote P2)
Step 8  feature-list.md                                 ← LAST (contiguity commit point)
Step 9  post-registration duplicate check, then delete .pending marker
```

**Merge rule (all files):** state-file writes are append/merge operations.
Never clobber existing `index`, `doc_shas`, `screen_spec_shas`, or `features` keys.

---

## Stage 6 Refresh (after delivery)

At Stage 6 delivery, the **orchestrator** (takumi `workflow-steps.md` Step 6.b — NOT `doc-writer`,
which is forbidden from reading `plan.md`) refreshes `screen_spec_shas`:
- Re-read `docs/generated/screen-list.md` for the SCR### section body.
- Recompute using the same section-hash algorithm as Step 6 above.
- Write the refreshed value into `docs/.rebuild-state.json → screen_spec_shas`.
- Remove `docs/.spec-promote-pending.json` sentinel (clean-promote cleanup; clears the `system_docs`
  branch too if present).

This ensures the sha reflects the final state of `screen-list.md` after all Stage 3–5 edits. The full
procedure (incl. the `spec_draft:`-still-present safety advisory) lives in `workflow-steps.md` Step 6.b.
