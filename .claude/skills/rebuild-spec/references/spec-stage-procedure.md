<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Spec Stage Procedure

**Shared procedure — invoked by takumi Stage 1.5 and tkm-plan's spec gate. Callers add their own discipline/mode-specific rules.**

**Owner:** rebuild-spec (spec-layer authority)
**Consumed by:** takumi Stage 1.5 orchestrator; tkm-plan spec gate (choice a — "Author spec first").

This file is the authoritative orchestration sequence for authoring a feature spec. Follow every step
in order. Callers (takumi Stage 1.5, tkm-plan) link here rather than duplicating this content.

**Caller requirements (every caller MUST provide):**
1. **Pre-run sentinel check** — before invoking this procedure, check `docs/.spec-promote-pending.json`;
   if present, a prior promote crashed mid-flight — prompt repair first (takumi: Stage 0 promote-sentinel
   check; tkm-plan: step 1d pre-check).
2. **Mode mapping for gaps & approval** — takumi disciplines apply as written below. tkm-plan
   callers in ALL modes (`--fast`, `--hard`, `--parallel`, `--two`, or no flag) are treated as
   interactive: ask ALL gaps, present the approval gate. tkm-plan's `--fast` is a research-depth
   flag, NOT takumi `--auto` — the F13 silent-default rule and the "skip if auto" rest-point
   exception apply ONLY to takumi `--auto`.
3. **Discipline (auto vs interactive)** — pass whether the caller is takumi `--auto`. Step 0.5
   (language resolution) only ever resolves silently for takumi `--auto`; every other caller —
   including ALL tkm-plan modes — asks the language gate when it has to.

---

### Pre-Step — Resolve spec language (orchestrator, runs ONCE, BEFORE Step 0)

Every draft this run produces (the `feature-list.md` from Step 0a AND every feature's 4-file set) is
written in ONE prose language — `spec_lang`. Resolve it before any researcher is spawned, so the
directive can ride in every spawn prompt. This runs once per run, NOT per feature.

```js
const state = existsNonEmpty("docs/.rebuild-state.json")
  ? JSON.parse(readFile("docs/.rebuild-state.json"))
  : {}

let spec_lang
if (state.primary_lang) {
  // Docs/specs already exist → follow their language. If multiple language mirrors exist
  // (docs/<lang>/…), primary_lang IS the default — secondaries are translations of it.
  spec_lang = state.primary_lang
} else if (caller_is_takumi_auto) {
  // Greenfield + non-interactive: default silently, never block --auto.
  spec_lang = "en"
} else {
  // Greenfield + interactive (ALL tkm-plan modes + takumi interactive/parallel/no-test):
  // ASK. AskUserQuestion "Which language for the spec prose?" → en / vi / jp / Other.
  spec_lang = <user's answer>
}
spec_lang = spec_lang.trim().toLowerCase()   // normalize (en, vi, jp, …)
```

**Resolution rules:**

| Condition | `spec_lang` | How |
|-----------|-------------|-----|
| `docs/.rebuild-state.json` has `primary_lang` | that value | Existing docs win — no prompt (covers single AND multi-language: primary is the default) |
| Greenfield + takumi `--auto` | `en` | Silent default — `--auto` is never blocked |
| Greenfield + any interactive caller (all tkm-plan modes, takumi interactive/parallel/no-test) | user's pick | `AskUserQuestion`: en / vi / jp / Other |

`spec_lang` is then (a) injected as the **Language directive** into every researcher spawn
(see `claude/skills/takumi/references/subagent-patterns.md ## Spec Stage`), and (b) recorded as `lang: <spec_lang>` in each draft's
`technical-spec.md` frontmatter (per `spec-authoring-contract.md` § Draft Frontmatter Schema). Authoring
NEVER writes `docs/` — for greenfield, promote reads that `lang:` to bootstrap `primary_lang`
(`spec-state-registration.md` Step 1), so the choice sticks for every later feature.

---

### Step 0 — Scope assessment & decomposition (orchestrator, before slug resolution)

A task is either ONE feature or a SYSTEM (many features). The orchestrator determines which by running
two sub-checks in strict order before any spec is authored or slug resolved. Over-decomposition is
recoverable at Rest Point 1.5a; under-decomposition (collapsing a SYSTEM into one feature) is not —
when in doubt, decompose.

**`--fast` is the only exception** to this entire step: it always stays SINGLE, never decomposes, and
skips to Step 1 immediately (after emitting the artifact below). Do NOT apply the smell-flag or
enumeration to a `--fast` run.

**Control flow:**

```
(B) Smell-flag check — runs FIRST on raw task title + description (CLOSED lists; ports Wave4.5 Check 1 conjunction rule to feature granularity)
      ├─ ALWAYS-fire match → force SYSTEM → jump to Step 0a   (skip enumeration; log warning)
      ├─ NEVER-fire match  → (A) enumerate intents
      └─ neither           → (A) enumerate intents
            (A) Enumerate intents
                        ├─ count ≥ 2 → SYSTEM → Step 0a
                        ├─ count = 1 → SINGLE → Step 1
                        └─ --fast    → SINGLE → Step 1   (documented exception above; skip to here)

→ EMIT  plans/<plan_dir>/spec/.intent-enum.json  (see artifact spec below)
```

#### (B) Smell-flag check — CLOSED conjunction lists

Scan the raw task title and description for a conjunction pattern (` & `, ` + `, ` và `, ` and `)
joining two terms. Match against the CLOSED lists below. If neither list matches, fall through to
enumeration — do NOT force-fire on a gray-zone phrase.

**NEVER-fire list** (CRUD verb pairs on ONE entity — these remain SINGLE; still subject to enumeration):

| Pattern examples | Why stays SINGLE |
|------------------|-----------------|
| "create and edit product" | Same entity, CRUD pair |
| "view and manage settings" | Same entity, CRUD pair |
| "add and remove members" | Same entity, CRUD pair |
| "list and filter orders" | Same entity, read-only pair |
| "edit and delete comment" | Same entity, CRUD pair |

**ALWAYS-fire list** (distinct system layers or business domains — force SYSTEM; log warning):

| Pattern examples | Why forced SYSTEM |
|-----------------|-------------------|
| "login and reporting" | Auth surface + analytics surface |
| "checkout and inventory" | Commerce flow + stock management |
| "auth and product management" | Auth layer + catalog domain |
| "login + quản lý hàng hóa" | Auth layer + inventory domain |
| "dashboard and billing" | Analytics surface + financial domain |

**Gray zone (neither list matches):** fall through to enumeration — never force-fire on ambiguity.

**`--auto` interaction:** a forced SYSTEM stalls `--auto` at Rest Point 1.5a (the one gate that does
not yield to `--auto`). This is deliberate human-in-the-loop: the system cannot confirm a forced
decomposition silently.

#### (A) Enumerate intents — mandatory before SINGLE/SYSTEM is chosen

List every distinct user-facing intent present in the task. Define intent as an
`(actor, action-domain, outcome)` triple that maps to its own screen-group or API boundary.

**Rule:** count ≥ 2 → SYSTEM (default). count = 1 confirmed → SINGLE. Ambiguous count → SYSTEM
(default; over-decomposition is recoverable, under-decomposition is not). Example: "storefront +
admin panel + API" yields three intents → SYSTEM.

Once the mode is determined:

- **SINGLE** → skip to Step 1 (N = 1, no feature-list).
- **SYSTEM** → run Step 0a + 0b + Rest Point 1.5a, then fan out Steps 1–2.5 over every confirmed feature.

This scope evaluation is mandatory in ALL disciplines including `--auto` (scope defines the whole
pipeline, like work-type classification).

#### Chokepoint artifact — `.intent-enum.json`

After deciding SINGLE or SYSTEM (including `--fast`), emit:

```json
// plans/<plan_dir>/spec/.intent-enum.json
{
  "mode": "single|system",
  "intents": ["<intent-1>", "<intent-2>", "..."],
  "justification": "<required when mode=single but enumeration found >1 intent, e.g. --fast forced SINGLE; omit or leave empty string when single is straightforward>"
}
```

`justification` is REQUIRED when `mode=single` but the enumeration listed more than one intent
(e.g. a `--fast` run that skipped decomposition). State this clearly: `scaffold_spec.py` reads this
file as the chokepoint input that gates file creation — prose enumeration in the orchestrator context
alone is insufficient.

### Step 0a — Decompose into a feature-list draft (SYSTEM only)

**[RT-5] Stale-sentinel check (MANDATE — runs at entry, before spawning anything):**

```bash
if [ -f "plans/<plan_dir>/.rp-1.5a-pending" ]; then
  echo "NOTIFY: A prior Rest Point 1.5a gate was left unconfirmed (sentinel present)."
  echo "A previous run decomposed features but the human confirmation step was never completed."
  echo "Re-entering Rest Point 1.5a gate now — do NOT silently proceed."
  # Re-enter the gate: skip re-decomposing (feature-list.md already exists), go directly to Step 0b → Rest Point 1.5a.
fi
```

If the sentinel is found: notify the user that a prior 1.5a was left incomplete, then jump directly to Step 0b (re-run the quality gate on the existing `feature-list.md`) and re-present the AskUserQuestion gate. Do NOT silently proceed past it. Do NOT silently fail or delete it.

Spawn the decomposition researcher (see `claude/skills/takumi/references/subagent-patterns.md ## Feature Decomposition`). It writes
**one** file:
- `plans/<plan_dir>/spec/feature-list.md` — the rebuild-spec feature-list FORMAT
  (`templates/feature-list-template.md`: the `Code | Name | Type | Language | Workspace | Priority`
  table + per-`F###` "Feature Details"). Greenfield deltas governed by `spec-authoring-contract.md`
  § Greenfield Feature-List: codes are **PROVISIONAL** `F001..FNNN` (real allocation/renumber at
  promote), and the cross-reference sections (Related Screens/User Stories/APIs/Data Models/BL/
  Permissions) are filled from intent where derivable, else `TBD (draft)` — **NEVER fabricated**.

### Step 0b — Feature-list quality gate (SYSTEM only)

Spawn the quality-gate reviewer (see `claude/skills/takumi/references/subagent-patterns.md ## Feature-List Quality Gate`). It runs the
**greenfield subset** of the rebuild-spec W5.6 checks → `plans/<plan_dir>/spec/feature-list-review.md`
(YAML frontmatter `passed: bool, issues: int, warnings: int`):
- **Kept:** Check 4 F-code uniqueness (needs only the feature-list itself), Check 5 Single-Intent
  (critical), Check 6 Clear Flow / input→process→output (warning), Check 7 Vague-naming (warning),
  Check 8 Scope-overlap >50% (warning), Check 9 Grouping-coherence (critical).
- **Skipped (greenfield):** Checks 1–3 only (US###/SCR### cross-artifact coverage + orphan) — no
  `user-stories.md` / `screen-list.md` exists yet, so they cannot be evaluated (not failed). Check 4 is
  NOT skipped despite being in Group A.

On a critical fail: the orchestrator **re-spawns** the decompose researcher, quoting the reviewer's
exact merge/split directives in the new prompt, then re-gates. Cap at 3 cycles; escalate to the user if
still failing.

### [Rest Point 1.5a] After Decomposition — confirm the feature set (SYSTEM only; BLOCKING in ALL disciplines incl. `--auto`)

**This is the ONE rest point that does NOT yield to `--auto`.** The sentinel + `scaffold_spec.py` chokepoint enforce it physically — `--auto` cannot bypass it.

**Sentinel write (BEFORE AskUserQuestion):** after Step 0b passes, write the sentinel:

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) features=$(grep -c '^| F' plans/<plan_dir>/spec/feature-list.md 2>/dev/null || echo '?')" \
  > plans/<plan_dir>/.rp-1.5a-pending
```

The sentinel path is `plans/<plan_dir>/.rp-1.5a-pending` — one level above `spec/` so it exists even if Step 0a failed before creating `spec/`. It is a one-line file: ISO timestamp + feature count. `plans/` is gitignored — never committed. Presence means: "human confirm has NOT happened."

**Defense-in-depth note:** the sentinel here provides two independent enforcement layers:
1. `scaffold_spec.py` SYSTEM chokepoint (machine): reads this sentinel and **refuses to create any files** (exit 2) while it is present AND intents < 2. A model that skips the AskUserQuestion cannot scaffold. This is the primary machine-checked gate (implemented in a separate phase).
2. The Step 2 fan-out guard below (inline `test -f`): blocks researcher spawn while sentinel is present.
A no-guard Python script for this check is NOT warranted (one file-presence test) — KISS/YAGNI.

**MUST call `AskUserQuestion` (required tool call)** — present the feature-list (codes, names, one-line intents, priority) + the Step 0b gate verdict. Options:

- **"Approve — proceed with this feature set"** (Recommended) → delete the sentinel (`rm plans/<plan_dir>/.rp-1.5a-pending`), then run the scaffolder (sentinel now ABSENT → proceeds), then fan out Steps 1–2.5 per feature.

  **Scaffolder invocation (SYSTEM, APPROVED branch only — runs once after sentinel delete, before fan-out):**

  ```bash
  .claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/scaffold_spec.py \
    --plan-dir plans/<plan_dir> \
    --mode system \
    --lang <spec_lang> \
    --feature-names "Feature A Name,Feature B Name,Feature C Name"
  ```

  Pass every confirmed feature's name (from `feature-list.md`) as a comma-separated list to
  `--feature-names`. The scaffolder derives kebab slugs, creates all feature dirs + 4-file sets,
  and writes a `feature-list.md` stub (the decomposition researcher's richer `feature-list.md` is
  already present — the scaffolder writes only its frontmatter stub; the researcher's file is
  preserved if already present; use `--force` only when explicitly re-scaffolding). `<spec_lang>` is
  the value resolved in the Pre-Step. On exit ≠ 0, stop and surface the error — do NOT fan out
  researchers against a missing tree.
- **"Adjust — merge / split / rename / re-priority"** → sentinel REMAINS (proof the gate is still open) → re-spawn decompose researcher with user's feedback → re-run Step 0b → re-present this gate.
- **"Abort — stop here"** → delete `plans/<plan_dir>/spec/` (feature-list + any sub-folders) AND delete sentinel (`rm plans/<plan_dir>/.rp-1.5a-pending`). Zero orphaned state — both the spec tree and the sentinel are removed.

The user is the final authority on the feature set — this gate is **NOT** skipped in `--auto`.

---

### Step 1 — Resolve draft slug + target dir (orchestrator, before spawn)

**Fan-out note:** for a SYSTEM, this resolves **one `<slug>` per confirmed feature** from Step 0a
(slug = the feature's name, no `F###` prefix on the folder), and Steps 2–2.5 repeat for each. For a
SINGLE feature, N = 1 and there is no `feature-list.md`.

NO `F###` allocation here. The `F###` is allocated at PROMOTE time (implement start) — see
`claude/skills/rebuild-spec/references/spec-state-registration.md` § Promote.

- **NEW feature:** derive a human slug from the task (kebab or CamelCase, no `F###` prefix).
  Draft target = `plans/<plan_dir>/spec/<slug>/`.
- **EXISTING feature (already `status: implemented` in `docs/features/F###_Slug/`):** reuse that
  feature's existing `F###` as the draft's recorded `fcode` (READ it; do NOT allocate). Draft
  target = `plans/<plan_dir>/spec/<slug>/` where `<slug>` = the existing `F###_Slug`.
- The draft frontmatter `fcode:` line is OMITTED for NEW features (unknown until promote) and set to
  the existing code for EXISTING-feature updates (see `spec-authoring-contract.md`).

### Step 1.5 — Scaffold spec file tree (orchestrator, SINGLE path — before researcher spawn)

**Run the scaffolder BEFORE spawning the researcher.** The scaffolder creates the 4-file set with
correct frontmatter + H2 skeleton; the researcher then FILLs the pre-scaffolded files. This is the
SINGLE path (N=1); the SYSTEM path runs the scaffolder inside the RP1.5a APPROVED branch (see above).

```bash
.claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/scaffold_spec.py \
  --plan-dir plans/<plan_dir> \
  --mode single \
  --lang <spec_lang> \
  --slug <slug> \
  [--fcode F### ]   # ONLY when revising an EXISTING implemented feature — omit for NEW features
```

`<spec_lang>` is the value resolved in the Pre-Step. The scaffolder reads
`plans/<plan_dir>/spec/.intent-enum.json` as its chokepoint input (exit 2 if missing or inconsistent)
and emits a JSON array of created paths to stdout. On exit ≠ 0, stop and surface the error — do NOT
spawn a researcher against a missing or partially-created file tree.

### Step 2 — Spawn spec researcher

**[RT-5] Fan-out guard (INLINE — runs before ANY researcher is spawned):**

```bash
if [ -f "plans/<plan_dir>/.rp-1.5a-pending" ]; then
  echo "HARD-STOP: Rest Point 1.5a has not been confirmed."
  echo "The feature set was not approved by a human — researcher fan-out is BLOCKED."
  echo "To bypass this gate manually (skips human confirmation): rm plans/<plan_dir>/.rp-1.5a-pending"
  echo "WARNING: running that command bypasses the Rest Point 1.5a gate entirely."
  exit 1
fi
```

This guard mirrors the `scaffold_spec.py` SYSTEM chokepoint. A separate Python guard script is NOT added — this is a one-file-presence test (KISS/YAGNI); the machine enforcement is `scaffold_spec.py`.

**SYSTEM fan-out:** spawn one researcher **per confirmed feature** in bounded waves
(`REBUILD_FS_BATCH_SIZE`, default 5: one researcher per feature dispatched in chained waves of ≤5 —
every spawn of wave i+1 waits for ALL of wave i; >20 features = sequential batch tasks — mirrors
rebuild-spec FS.1; never more than 5 researchers runnable at once). Each researcher receives its feature's row from `feature-list.md` (intent +
provisional `F###` + related codes) as primary context, plus the shared Study reports, **plus the
`spec_lang` Language directive resolved in the Pre-Step**, and FILLs its pre-scaffolded
`plans/<plan_dir>/spec/<slug>/` 4-file set. For a SINGLE feature this is one spawn (N = 1).

```
Task(subagent_type="researcher", prompt="[see claude/skills/takumi/references/subagent-patterns.md ## Spec Stage]",
     description="Fill pre-scaffolded spec draft (<slug>)")
```

The researcher FILLs the pre-scaffolded files (files already exist with correct frontmatter + H2
skeleton; do NOT recreate frontmatter or reorder H2) — writing content into the plan-local tree NEVER
`docs/` during authoring:
- `plans/<plan_dir>/spec/<slug>/technical-spec.md`, `business-context.md`, `screens.md`,
  `edge-cases.md` — fill each file's sections; frontmatter and H2 structure are already correct
- `plans/<plan_dir>/spec/<slug>/screens/SCR-<name>/spec.md` — create only if a new screen is
  introduced (plan-local, no `SCR###` — that is allocated at promote)

**Existing-feature runs:** the draft is authored into the plan dir tied to the existing `F###`.
The shipped `docs/features/F###_Slug/` spec is NEVER touched during authoring — it stays
`status: implemented` until promote at implement-start overwrites it.

The researcher MUST return a `## Gaps for Clarification` block in the strict schema
(see `claude/skills/rebuild-spec/references/spec-authoring-contract.md`).

**Rejected/failed spawn cleanup:** if the researcher spawn is rejected/dies, delete any partial
`plans/<plan_dir>/spec/<slug>/` tree created this run. NO `_canonical-fcodes.json` or `docs/`
cleanup is needed — nothing was allocated or written there.

### Step 2b — Forward-draft system docs (architecture/auth — opt-in)

If the task TOUCHES architecture (new service/layer/integration/data-store) or auth
(RBAC/policy/guard/middleware/roles) — detected via the Trigger Mapping in
`claude/skills/takumi/references/subagent-patterns.md ## Documentation` (reuse it; do not invent a
second pattern) — ALSO author the relevant `docs/system/*` narrative draft(s) to
`plans/<plan_dir>/spec/system/<name>.md` (`architecture.md` and/or `permissions.md`). The same
`spec_lang` directive applies (`lang: <spec_lang>` in frontmatter). Format + hard rules are owned by
`spec-authoring-contract.md` § Forward-Authored System Docs (single-file frontmatter, NEVER fabricate
`PERM###`/codes, rationale → ADR, NEVER write `docs/generated/*`) — follow it, don't restate here.
A task touching neither → skip (no system draft). Record the draft path(s) in `plan.md` so promote
(§ Promote — SYSTEM-DOC) finds them. **Skip entirely in `--fast` discipline** — system-doc
forward-drafting needs intent-level research that `fast` deliberately omits.

### Step 2.5 — Verify draft content (orchestrator, BEFORE gap clarification — MANDATORY)

**The scaffolder now owns structure.** File presence, YAML frontmatter shape, and H2 skeleton order
are guaranteed by `scaffold_spec.py` (exit 2 if those invariants cannot be established). This lint
step guards only CONTENT mutations a researcher may introduce — do NOT re-check what the scaffolder
already enforces.

**For a SYSTEM, run this check once PER feature folder.** On any failure, re-spawn that feature's
researcher with the specific defect quoted (or fix a trivial token/heading slip inline) — a malformed
draft must not reach the rest point.

```bash
d="plans/<plan_dir>/spec/<slug>"

# Belt-and-suspenders: the scaffolder guarantees these; keep as a backstop for hand-authored drafts.
grep -qE '^fcode:' "$d/technical-spec.md" && echo "WARN  fcode present — allowed ONLY for EXISTING-feature updates" || echo "OK  no fcode (new feature)"
ls "$d"/spec.md 2>/dev/null && echo "FAIL  stray single spec.md at feature root (that is the screen shape)" || echo "OK  no stray spec.md"

# --- FORMAT LINT (guards researcher CONTENT mutations — not duplicates of scaffolder structure) ---
# 1. Code tokens that MUST be no-hyphen (US/BL/PERM/MODEL/REG/F) used WITH a hyphen → bug.
#    SCR is DELIBERATELY excluded: draft screen codes are `SCR-<name>` (slug, no number), so an
#    error-page screen legitimately named SCR-404/SCR-500 would false-match SCR-<digits>.
grep -rEn '\b(US|BL|PERM|MODEL|REG|F)-[0-9]{2,3}' "$d" \
  && echo "FAIL  hyphenated no-hyphen token (e.g. US-001 → must be US001 — see code-formats.md)" \
  || echo "OK  no-hyphen tokens clean"
# 2. screens.md canonical heading — researcher may overwrite with wrong heading.
grep -qE '^## Screen List$' "$d/screens.md" && echo "OK  screens.md '## Screen List'" \
  || echo "FAIL  screens.md missing '## Screen List' (found 'Screen Route Table' or other?)"
# 3. technical-spec.md required headings present + deprecated absent — researcher may remove/add.
grep -qE '^## Artifact References$' "$d/technical-spec.md" && echo "OK  Artifact References present" \
  || echo "FAIL  technical-spec.md missing '## Artifact References' (validator-critical at promote)"
grep -qE '^## (Functional Requirements|Requirements|Business Rules|Success Criteria)$' "$d/technical-spec.md" \
  && echo "FAIL  deprecated standalone H2 in technical-spec.md (FRs go under US / Cross-Cutting Logic)" \
  || echo "OK  no deprecated standalone H2"
# 4. screen specs (if any) use canonical headings, not ad-hoc ones.
if ls "$d"/screens/*/spec.md >/dev/null 2>&1; then
  grep -rlE '^## (Layout & Component Tree|Form Fields|User-Visible Copy|Constraints)$' "$d"/screens/*/spec.md \
    && echo "FAIL  screen spec uses ad-hoc headings — follow screen-spec-template.md (## Screen Layout / ## UI States / ## Validation & Error Feedback)" \
    || echo "OK  screen-spec headings canonical"
fi
```

**Reject (return to researcher) if any line reads `FAIL`, or — for a NEW feature — the `fcode present`
WARN.** The fcode-WARN is kept as belt-and-suspenders: the scaffolder omits `fcode:` for new features,
but a researcher may re-add it. The FORMAT LINT block rejects hyphenated no-hyphen tokens (`US-001`),
a non-canonical `screens.md` heading, a missing `## Artifact References`, a deprecated standalone
`## Functional Requirements`, and ad-hoc screen-spec headings. The heading checks mirror
`validate_feature_spec.py`'s `REQUIRED_H2_*`/`DEPRECATED_H2` and WOULD hard-fail at promote —
catching them here saves a promote round-trip. The hyphenated-token check guards a convention the
script validator does NOT explicitly reject (it merely fails to recognize `US-001` as a `US\d{3}`
code, silently breaking downstream coverage) — so this lint is the PRIMARY guard for token format.
On any `FAIL`, re-spawn that feature's researcher quoting the exact defect (or fix a trivial
token/heading slip inline). Also confirm `plan.md` frontmatter records `spec_draft:`
(SINGLE: `plans/<plan_dir>/spec/<slug>/`; SYSTEM: `plans/<plan_dir>/spec/`) — add it if omitted.

**SYSTEM folder-count machine check (RT-14):**

```bash
.claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/scaffold_spec.py \
  --plan-dir plans/<plan_dir> \
  --mode system \
  --lang <spec_lang> \
  --feature-names "placeholder" \
  --check-folder-count
```

Or equivalently, invoke the dedicated check flag directly:

```bash
.claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/scaffold_spec.py \
  --check-folder-count \
  --plan-dir plans/<plan_dir> \
  --mode system \
  --lang <spec_lang>
```

This command prints `OK folder-count=N matches feature-list rows=N` (exit 0) or
`MISMATCH folders=N feature-list rows=M` (exit 1) without creating any files. A mismatch means a
feature was dropped or duplicated in the fan-out — re-spawn the missing researcher(s) before the rest
point. The `--check-folder-count` flag skips all scaffold writes and only compares
`find plans/<plan_dir>/spec -mindepth 1 -maxdepth 1 -type d` count vs `feature-list.md` `| F###` row
count.

### Step 3 — Gap clarification (orchestrator runs AskUserQuestion)

Parse the strict-schema gap block returned by the researcher. **For a SYSTEM, aggregate every
feature's gap block, dedupe overlapping questions, and tag each with its `F###`** so the user sees one
consolidated clarification pass rather than N separate ones.

**F13 auto-mode rule:**
- Gaps with `category` ∈ `{auth, permissions, scope, external-integration}` are **BLOCKING** even
  in `--auto` — the orchestrator MUST call `AskUserQuestion`.
- All other categories: resolve silently using the `recommended` option and log under
  `## Unresolved Questions` in `technical-spec.md`. No question asked.

**Interactive/parallel/no-test:** Ask all gaps via `AskUserQuestion` regardless of category.

### [Rest Point 1.5b] After Spec — Approval Gate (interactive/parallel/no-test; skip if auto)

Present the spec location(s) and gap-resolution summary (SYSTEM: list every feature folder + the
`feature-list.md` path).
Use `AskUserQuestion` to ask: "Approve spec and proceed to planning?" / "Request spec revisions" / "Abort"

**If ABORTED here (NEW or EXISTING):**
- Delete the draft tree — SINGLE: `plans/<plan_dir>/spec/<slug>/`; SYSTEM: the whole
  `plans/<plan_dir>/spec/` (feature-list + every feature folder). Nothing in `docs/` was created or
  modified during authoring, so there is nothing to revert there. No reservation was claimed.
- The promote sentinel does not exist yet (promote happens at implement-start, not here).
- The abort leaves zero orphaned state.

**If APPROVED:** proceed to Step 4.

### Step 4 — (registration deferred to promote)

Authoring does NOT register the spec into rebuild-spec state files. Registration (`F###` allocation,
reservation claim, `_canonical-fcodes.json`, `feature-list.md`, screen shas) runs at PROMOTE time
when implementation begins — see
**`claude/skills/rebuild-spec/references/spec-state-registration.md`** § Promote. After approval, the
draft simply remains in the plan dir awaiting `/tkm:takumi <plan>`.

### Step 5 — Emit

SINGLE feature:
```
⚒ Spec drafted — plans/<plan_dir>/spec/<slug>/ (status: draft, not yet in docs/)
```
SYSTEM:
```
⚒ Specs drafted — N features in plans/<plan_dir>/spec/ (feature-list.md + N×4-file, status: draft, not yet in docs/)
```

Callers may prefix their own stage label (takumi: `⚒ Stage 1.5: …`; tkm-plan: `⚒ Spec Gate: …`).
