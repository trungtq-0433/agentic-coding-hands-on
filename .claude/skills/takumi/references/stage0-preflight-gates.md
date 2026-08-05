<!-- layout-exempt: takumi references — all docs/system|features|generated|flows paths are takumi's own forward-draft targets, promote targets, or spec-layer detection references -->
# Stage 0 Pre-flight Gates

The three pre-flight gates that run at the head of Stage 0 (`workflow-steps.md` → Stage 0),
before any spec/blueprint work. `SKILL.md` carries only the summary — this file is the authoritative
procedure. Load it when actually executing Stage 0; the `off` / no-sentinel common paths never need it.

Order: **Promote Sentinel Check** → **SDD Mode Gate** → **Language Gate**.

## Stage 0 Pre-flight: Promote Sentinel Check

Before starting any new run, check for a prior promote crash:

```bash
[ -f docs/.spec-promote-pending.json ] && echo "SENTINEL_PRESENT"
```

If the sentinel exists, a prior run started promoting a plan-dir draft into `docs/` (copy + register +
`status: implemented`) but crashed before Stage 6 cleaned it. **Do NOT proceed.** Read the sentinel and
prompt the user — REVERT follows the matching branch of § Promote-Failure Rollback in
`spec-state-registration.md`.

**SINGLE sentinel** (`{fcode, run_type, plan_dir, slug, from, screens, ts}` — no `features[]`):

> "A prior promote left `docs/.spec-promote-pending.json` (fcode: `<fcode>`, run_type: `<run_type>`, plan: `<plan_dir>`, started: `<ts>`).
> Choose:
> 1. REVERT — `git checkout HEAD -- docs/features/<fcode>_*` + the listed `screens`; if `run_type: new`
>    also remove its `_canonical-fcodes.json` reservation row + feature-list row; if `plan.md` was
>    repointed, restore `spec_draft: <from>`; delete the sentinel.
> 2. KEEP — leave docs as-is (promote was effectively complete); delete the sentinel.
> 3. Abort — stop this run entirely."

**SYSTEM sentinel v2** (`run_type: system` with a `features[]` array): a multi-feature promote crashed
mid-batch. Prompt the same way but over the SET — list each `features[]` entry (`fcode`, its
per-entry `run_type`):

> "A prior SYSTEM promote left `docs/.spec-promote-pending.json` (plan: `<plan_dir>`, started: `<ts>`, N features: `<F### list>`).
> Choose:
> 1. REVERT — run § Promote-Failure Rollback `run_type: system` (revert every `features[]` entry by its
>    own per-entry `run_type`, restore `plan.md` to `spec_draft: plans/<plan_dir>/spec/`, delete the sentinel).
> 2. KEEP — leave docs as-is (batch was effectively complete); delete the sentinel.
> 3. Abort — stop this run entirely."

Only proceed with the new run after the sentinel is resolved.

## Stage 0 Pre-flight: SDD Mode Gate

After the sentinel check, resolve `takumi.sddMode`. Read it from the injected `## Plan Context`
line (`- SDD mode: <value>`), or `$TKM_SDD_MODE`, or — if neither is present — run:

```bash
node -e "process.stdout.write(require('./.claude/hooks/lib/tkm-config-utils.cjs').loadConfig().takumi?.sddMode || 'ask')"
```

**If `on`** → proceed normally; Stage 1.5 runs per the discipline table.

**If `off`** → the spec stage is disabled project-wide. Skip Stage 1.5 entirely (no `F###`, no
reservation, no spec researcher). The Blueprint Pre-flight spec box reads
`N/A — SDD mode disabled (takumi.sddMode: off)`. Everything else runs unchanged.

**If `ask` (first run — no decision recorded)** → emit an `AskUserQuestion` box. This is **BLOCKING
in all disciplines including `--auto`** (like work-type classification, it defines pipeline scope):

> **Enable Spec-Driven Development (SDD) mode for this project?**
> - **On — author specs first (Recommended):** every feature gets a spec draft (in the plan dir) before planning, promoted to `docs/features/` at implement-start. Best for shared/long-lived codebases.
> - **Off — skip the spec stage:** go straight from study to blueprint. Lighter; no spec layer.

If the **Language Gate** (below) would also prompt this run (greenfield interactive, no `primary_lang`),
ask it as a SECOND question in this SAME `AskUserQuestion` call — both are one-time scope decisions.

After the user answers, **persist the choice to project-scope `.claude/.tkm.json`** so the whole
team shares one decision (it overrides the global default). Procedure — read the file (or treat as
`{}` if absent), set `takumi.sddMode` to `"on"`/`"off"`, write it back with 2-space indent,
preserving every other key (only when the existing file is valid JSON — a corrupt file is reported
and replaced rather than silently merged):

```bash
node -e "const fs=require('fs'),p='.claude/.tkm.json';let c={};if(fs.existsSync(p)){try{c=JSON.parse(fs.readFileSync(p,'utf8'))}catch{process.stderr.write('warn: .tkm.json is not valid JSON — writing a fresh file\n')}}c.takumi={...(c.takumi||{}),sddMode:process.argv[1]};fs.writeFileSync(p,JSON.stringify(c,null,2)+'\n')" on
```
(replace `on` with `off` per the answer). If the warning fires, tell the user their previous
`.tkm.json` was unreadable and ask them to re-add any custom keys. Then confirm and advise:
"⚒ SDD mode saved to `.claude/.tkm.json` — commit it to share this decision with your team."
Continue the run using the chosen value (no re-prompt for the rest of the session).

The gate never writes `ask` back — once answered the value is always `on` or `off`, so the box
appears only on the first run per project.

## Stage 0 Pre-flight: Language Gate

After the SDD Mode Gate, if the spec stage will run this session (`sddMode` resolved to `on`,
work-type ≠ `deliverable`, discipline ≠ `code`), resolve the spec prose language `spec_lang`
**before** authoring any spec or spawning the Stage 1.5 researcher. Like the SDD gate, this is a
**scope-defining gate** — for a greenfield interactive run it is **BLOCKING** (the choice cannot be
silently defaulted). It is invisible only because its full logic lives in
`references/spec-stage-procedure.md` § Pre-Step (authoritative) — this inline summary exists so the
gate is never skipped by reading the contract alone.

Resolution (mirrors `spec-stage-procedure.md` § Pre-Step — read it for the exact algorithm):

| Condition | `spec_lang` | Prompt? |
|-----------|-------------|---------|
| `docs/.rebuild-state.json` has `primary_lang` | that value (existing docs win) | No — inherited |
| Greenfield + takumi `--auto` | `en` | No — silent default (never block `--auto`) |
| Greenfield + any interactive caller (interactive/parallel/no-test, all tkm-plan modes) | user's pick | **Yes — BLOCKING** `AskUserQuestion`: en / vi / jp / Other |

The resolved value rides into every researcher spawn as the **Language directive** and is recorded as
`lang: <spec_lang>` in each draft's `technical-spec.md` frontmatter; at promote it bootstraps
`primary_lang`, so the choice sticks for every later feature.

**Combine with the SDD gate (one prompt).** When the SDD Mode Gate is *also* prompting this run
(first run, `sddMode: ask`) AND the language gate would prompt, ask BOTH in a single
`AskUserQuestion` call (two questions) — both are one-time scope decisions, so combining saves a
round-trip. They remain independent gates: the language gate still fires on its own on later runs
(SDD already `on`) whenever the repo is still greenfield (no `primary_lang` yet).
