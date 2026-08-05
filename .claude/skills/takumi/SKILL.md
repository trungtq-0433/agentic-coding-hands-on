---
name: tkm:takumi
description: "Reach for this before any implementation — one skill that carries a feature from first study to sealed commit: research → plan → implement → test → review → commit. The whole craft cycle, start to finish, under one roof."
argument-hint: "[task|plan-path] [--interactive|--fast|--parallel|--auto|--no-test]"
metadata:
  author: takumi-agent-kit
  version: "5.5.0"
module: implementation
triggers: ["implement", "build feature", "add X to app", "develop", "create functionality", "end-to-end"]
---

# Takumi (匠) — The Craftsman's Implementation

The master craftsman does not measure success by speed.
Every piece that leaves the workshop is examined, tested, and refined.
No feature ships without a blueprint. No blueprint earns approval without review.

**Principles:** YAGNI, KISS, DRY | Token efficiency | Concise stage reports

## Usage

```
/tkm:takumi <natural language task OR plan path>
```

If no discipline is specified, the craftsman defaults to **interactive** — full control, full craft.

**Working disciplines:**
- `--interactive`: Full pipeline with rest points for your review (**default**)
- `--fast`: Scout the material, draft, forge — no deep research
- `--parallel`: Many hands, many pieces — multi-agent execution
- `--no-test`: Forge without tempering — use only when conditions warrant
- `--auto`: Continuous craft — the master trusts his own hands

**Examples:**
```
/tkm:takumi "Add user authentication to the app" --fast
/tkm:takumi path/to/plan.md --auto
```

## Workshop Law

A craftsman measures twice, cuts once.
No chisel touches wood before its blueprint is drawn.
No blueprint earns its seal before passing through the master's review.

This is not procedure imposed from outside — it is the discipline that separates craft from labor.
The only exception: when the one who commissioned the work explicitly grants it.

*Note:* `--fast` discipline skips deep research, but the blueprint step remains sacred.
User override: if the user explicitly says "just code it" or "skip planning", honor their instruction.

## The Craftsman's Creed

*"Simple pieces hide the hardest grain."*
— Every task that feels trivial conceals unexamined assumptions. The blueprint costs thirty seconds. Rework costs hours.

*"Knowing the way is not walking it clean."*
— Confidence in the solution does not replace committing it to paper. Write it down.

*"The fastest path runs through the blueprint."*
— Draft → forge → deliver beats forge → break → restart, every time.

*"Speed is earned through discipline, not shortcuts."*
— A master works fast because they have walked every step before. A novice rushes and circles back.

*"Once" is how every exception begins.*
— There are no isolated skips. The standard holds or it does not.

## Reading the Material

The craftsman reads intent from what is brought to the workshop:

| Presented Material | Detected Discipline | Working Pattern |
|-------------------|--------------------|-----------------|
| Path to `plan.md` or `phase-*.md` | code | Execute the existing blueprint |
| Contains "fast", "quick" | fast | Scout → draft → forge |
| Contains "trust me", "auto" | auto | Continuous, no rest points |
| 3+ distinct features OR "parallel" | parallel | Multi-agent execution |
| Contains "no test", "skip test" | no-test | Skip tempering step |
| (default) | interactive | Full pipeline with rest points |

See `references/intent-detection.md` for the detection logic.

### Work-Type

Before discipline routing takes effect on Stage 1.5 — before any `F###` reservation claim — the craftsman classifies the work:

| Work Type | Meaning | Routing |
|-----------|---------|---------|
| `feature` | Product or system behavior (code that ships, screens, APIs, persistence) | Stage 1.5 runs normally |
| `deliverable` | One-off artifact handed to the user (excel/report/slide/doc, ad-hoc analysis, uncommitted script) | Skip Stage 1.5 entirely — no `F###`, no reservation |
| `ambiguous` | No clear cue on either side | `AskUserQuestion` BLOCKING in all disciplines incl. `--auto` |

Classify BEFORE discipline. Classify BEFORE any reservation. Classification cues live in `references/intent-detection.md` → "Work-Type Detection".

### SDD Mode (Spec-Driven Development Toggle)

SDD mode governs whether the spec-first stage (Stage 1.5) runs. It is a **project-level** decision,
not a per-run flag — one choice, shared by everyone working in the repo.

The state lives in config key `takumi.sddMode`, resolved from project-scope `.claude/.tkm.json`
(falls back to global `~/.claude/.tkm.json`, then the built-in default). Three values:

| `takumi.sddMode` | Meaning | Effect on the pipeline |
|------------------|---------|------------------------|
| `ask` (default — unset) | No decision recorded yet | **First-run gate:** prompt the user, then persist their choice |
| `on` | Spec-Driven Development enabled | Stage 1.5 runs per the discipline table (current behavior) |
| `off` | Spec stage disabled project-wide | Stage 1.5 is skipped; Pre-flight spec box = `N/A — SDD mode disabled (takumi.sddMode: off)` |

The current value is injected each session into `## Plan Context` as `- SDD mode: <value>` (and as
`$TKM_SDD_MODE`). The **SDD Mode Gate** runs at Stage 0 (after the sentinel check) — see
`references/workflow-steps.md` → Stage 0. On first run (`ask`) the gate shows an `AskUserQuestion`
box and saves the answer to `.claude/.tkm.json` so the whole project shares one decision.
`off` only skips the spec stage — Study, Blueprint, Forge, Temper, Inspect, and Deliver are unaffected.

### Documentation lifecycle (SDD on)

<!-- layout-exempt: docs lifecycle overview — docs/system paths are takumi's own forward-draft targets -->
Three mechanisms keep `docs/` faithful — they interlock; full detail in `references/workflow-steps.md`
and `_shared/docs-canonical-mapping.md` (don't restate, just know the shape):
- **Forward-draft (Stage 1.5):** when a task touches architecture or auth, the spec stage also drafts
  `docs/system/architecture.md` / `permissions.md` (promoted at implement-start, reconciled post-forge).
- **Gen gate (Step 6.a-pre):** after Inspect, bootstrap the absent code-derived layer (Core/Flow) via
  `rebuild-spec` on the final code; interactive asks, `--auto` bootstraps silently / re-baseline is advisory.
- **Guardrailed prose (doc-writer, every delivery):** keeps prose docs fresh per-task within section
  guardrails (`doc_lock: user` opts a file out). The gen-gate re-baseline is the drift escape hatch.

## Seven Stages (Authoritative Flow)

```mermaid
flowchart TD
    A[Read the Material] --> B{Blueprint exists?}
    B -->|Yes| F[Load Blueprint]
    B -->|No| C{Discipline?}
    C -->|fast| D[Scout → Draft]
    C -->|interactive/auto| E[Study → Review]
    E --> S[Spec — author/update]
    S --> MM{MoMorph detected?}
    MM -->|Yes| PA["Spawn N background UI agents (1 per screen)"]
    MM -->|No| F
    PA --> PB["Clarify → Draft → Forge backend (non-blocking)"]
    PB --> INT["Integrate UI + backend as agents complete"]
    INT --> I
    D --> Sf[Spec — minimal]
    Sf --> F
    F --> G[Rest Point]
    G -->|approved| PR[Promote spec draft → docs/features/ if spec_draft present]  %% layout-exempt: flowchart — docs/features/ is takumi's promote target
    PR --> H[Forge the Piece]
    G -->|rejected| E
    H --> I[Rest Point]
    I -->|approved| J{--no-test?}
    J -->|No| K[Temper the Edge]
    J -->|Yes| L[Deliver the Work]
    K --> L
    L --> M[Record + Session]
```

**The diagram is the source of truth for the flow.** Where the prose and the diagram disagree, the diagram wins.

**Skipping or shortening Study does NOT skip Spec.** Study reads what exists; Spec writes what will
exist — they never share a fate. An empty repo empties Study, not Spec: greenfield is precisely when
the spec is CREATED from zero. Spec is skipped ONLY in `code` discipline (blueprint already exists)
or when the user explicitly waives it; `fast` still writes the minimal spec. The full Stage 1.5
procedure lives in `references/workflow-steps.md` — read it BEFORE acting; the SKILL.md summary alone
is not enough to run the stage.

## Stage Overview

```
[Read Material] → [Study?] → [Spec?] → [Review] → [Blueprint] → [Review] → [Forge] → [Review] → [Temper?] → [Review] → [Deliver]
```

**Interactive (default):** Pauses at each rest point for your approval before advancing.
**Auto discipline:** Advances through all stages without pause — the master trusts the process.
Two exceptions are still BLOCKING even in `--auto` because they define pipeline scope: the first-run
SDD Mode Gate (`takumi.sddMode: ask`) and an `ambiguous` work-type classification.
**Claude Tasks:** Use `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList` during the forge stage. **Fallback:** CLI-only tools, unavailable in VSCode extension. If they error, use `TodoWrite` instead.

| Discipline | Study | Spec | Tempering | Rest Points | Progression |
|------------|-------|------|-----------|-------------|-------------|
| interactive | ✓ | ✓ | ✓ | **Approval at each stage** | One stage at a time |
| auto | ✓ | ✓ | ✓ | Auto if score≥9.5 | All stages, no pauses |
| fast | ✗ | minimal | ✓ | **Approval at each stage** | One stage at a time |
| parallel | Optional | ✓ | ✓ | **Approval at each stage** | Concurrent groups |
| no-test | ✓ | ✓ | ✗ | **Approval at each stage** | One stage at a time |
| code | ✗ | ✗ | ✓ | **Approval at each stage** | Per blueprint |

The **Spec** column applies only when `takumi.sddMode` is `on` (or `ask` resolved to on). When
`sddMode: off`, the Spec stage is skipped in every discipline regardless of the ✓ above — see
"SDD Mode" and the SDD Mode Gate (`## Stage 0 Pre-flight Gates` → `references/stage0-preflight-gates.md`).

## Stage Output Format

```
⚒ Stage [N]: [Brief status] — [Key metrics]
```

## Workshop Rest Points (Non-Auto Disciplines)

The craftsman pauses here for your eye before advancing (skipped with `--auto`):
- **After Study:** Review findings before drafting the blueprint
- **After Spec:** Review spec gaps before blueprinting (interactive/parallel/no-test only)
- **After Blueprint:** Approve the plan before the forge begins
- **After Forge:** Inspect the work before tempering
- **After Tempering:** 100% pass + approval before delivery

**Always enforced across all disciplines:**
- **Blueprint Pre-flight (MANDATORY — emit BEFORE spawning `planner` in interactive/auto/parallel/no-test):**
  ```
  ⚒ Blueprint Pre-flight
  - [x] Spec drafted — spec_draft: plans/<plan_dir>/spec/<slug>/   (fast: minimal spec draft | code: N/A — blueprint exists | user waived: quote their words | deliverable: N/A — non-feature deliverable (work-type: deliverable) | SDD off: N/A — SDD mode disabled (takumi.sddMode: off))
  - [x] Spec language resolved — spec_lang: <en|vi|jp> (asked | inherited primary_lang | auto-en | N/A — no spec stage)
  - [x] System-doc forward-draft — drafted: plans/<plan_dir>/spec/system/<name>.md  (N/A — task touches neither architecture nor auth | N/A — SDD off / no spec stage)
  - [x] Gaps clarified — [N] resolved, [M] logged under Unresolved Questions
  ```
  If the spec box cannot honestly read `[x]`, do NOT spawn the planner — return to Stage 1.5 and run it.
  (`SDD off` is a legitimate `[x]` state: when `takumi.sddMode: off`, no spec is expected.)
  The spec-language box makes a skipped Language Gate visible: a greenfield interactive run must read
  `(asked)`, never a silent `auto-en` — see the Language Gate (`## Stage 0 Pre-flight Gates` → `references/stage0-preflight-gates.md`). `N/A — no spec stage`
  applies only when the spec box is itself N/A (code / deliverable / SDD off).
  The System-doc forward-draft box makes a skipped Step 2b visible: when the task TOUCHES architecture
  (new service/layer/integration/data-store) or auth (RBAC/policy/guard/middleware/roles) — detected via
  the existing Trigger Mapping (`references/subagent-patterns.md` → `## Documentation`) — Stage 1.5 MUST
  forward-draft the matching `docs/system/*` narrative and this box names the draft path; only a task  <!-- layout-exempt: forward-draft description — docs/system/ is takumi's own forward-draft target -->
  touching neither (or SDD off / no spec stage) may read `N/A`. See `workflow-steps.md` → Stage 1.5
  "Forward-draft system docs". The orchestrator runs that same Trigger Mapping grep over the planned
  surface — no new detection table.
  A Pre-flight that was not printed to the user did not happen. The planner's prompt MUST carry the
  `spec_draft` path shown here.
- **Tempering:** 100% pass required (unless no-test discipline)
- **Master's Inspection:** Approval OR auto-approve (score≥9.5, 0 critical)
- **Delivery (MANDATORY — never skip, never reorder):**
  The commit question is not the seal of the work — the Delivery Manifest is. Steps 0–4 run BEFORE the commit prompt, always.
  0. **Gen gate (Step 6.a-pre)** — runs FIRST (after Inspect, before the subagents). When `work_type: feature` AND `sddMode: on` AND code was forged this session: evaluate the `docs/.rebuild-state.json` cursor — if Core/Flow is **absent**, bootstrap the code-derived doc layer via `rebuild-spec` (interactive asks `[Core][Flow][Skip]`; `--auto` runs Core→Flow silently). Otherwise emit the skip line `⚒ Step 6.a-pre: gen gate skipped — <reason>`. **Either way you MUST emit one line** — running it or skipping it. Full logic: `references/workflow-steps.md` → Step 6.a-pre.
  1. `project-manager` subagent → sync all completed stages back to `phase-XX-*.md` and `plan.md`
  2. `doc-writer` subagent → review `./docs` AND (when present) the layered spec layer (`docs/system/`, `docs/generated/`, `docs/features/`, `docs/flows/`) for impact. <!-- layout-exempt: doc-writer step — layered spec layer refs are mode-aware per pointer below --> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). **ALWAYS spawn this subagent.** "No update needed" is `doc-writer`'s verdict to return, not Takumi's verdict to assume. Detection + impact map built in `workflow-steps.md` Stage 6.
  3. `TaskUpdate` → mark Claude Tasks complete after sync-back
  4. **Run the evidence gate (hard stage)** → the work must prove itself before it is sealed: `node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir <abs {plan}/evidence> --stage hard`. Exit 2 = BLOCKED — show the reasons and loop back to fix; do NOT reach the commit prompt over unproven work. Detail + the 3 artifacts: `workflow-steps.md` → "Evidence Gate".
  5. **Emit the Delivery Manifest (below)**, then ask if the work should be committed via `git-manager`
  6. Run `/tkm:write-journal` to record the session

  **Delivery Manifest — emit verbatim to the user before the commit prompt:**
  ```
  ⚒ Delivery Manifest
  - [x] gen-gate (6.a-pre) — <ran Core|Flow|Both: <N> core artifacts @ <sha7> | skipped: <reason>>
  - [x] system-doc forward-draft — <promoted: docs/system/<name>.md | N/A — task touched neither architecture nor auth | N/A — SDD off>  <!-- layout-exempt: delivery manifest template — docs/system/ is takumi's own forward-draft target -->
  - [x] project-manager — plan.md & phases reconciled
  - [x] orchestrator — spec promoted at implement-start + sentinel cleaned, shas refreshed (or N/A — deliverable/SDD-off; or ⚠ NOT promoted — see Step 6.b advisory if `spec_draft:` still in plan.md)
  - [x] doc-writer — docs/ + spec layer reviewed (verdict: <updated N files | no changes needed>)
  - [x] TaskUpdate — all tasks closed (or N/A in VSCode)
  - [x] evidence-gate — SEALED (hard stage; 3 artifacts verified, exit 0)
  - [ ] git-manager — awaiting your seal
  - [ ] /tkm:write-journal — pending
  ```
  - The gen-gate, system-doc, project-manager, orchestrator, doc-writer, TaskUpdate, and evidence-gate boxes must read `[x]` before any commit prompt. If any is `[ ]`, complete it NOW. The gen-gate box reads `[x]` whether it ran a pass OR skipped with a stated reason — what it must never be is **absent** (a missing box is the silent skip this gate exists to prevent). When it RAN, the box carries **evidence derived from `docs/.rebuild-state.json`** (`<N> core artifacts @ <sha7>`, the advanced cursor) — never a self-asserted "ran" with no sha; a hand-rolled doc subset is a SKIP, not a run (see Delivery Anti-Rationalization). The evidence-gate box reads `[x]` only on a real exit-0 from the gate CLI — never hand-checked. (The orchestrator box's sentinel/sha cleanup is the orchestrator's own Step 6.b work — `doc-writer` cannot read `plan.md` to do it.)
  - A Manifest that was not printed to the user did not happen. Silent self-checks do not pass this gate.

## Spec Anti-Rationalization (Stage 1.5 Specific)

The task looks small. The repo looks empty. The temptation is to jump straight to the blueprint.
Resist — this is where the spec-first discipline most often fails.

<!-- layout-exempt: anti-pattern table — docs/ paths are takumi's own forward-draft and promote targets -->
| The Whisper | The Master's Answer |
|-------------|---------------------|
| "The repo is empty — there is nothing to spec." | Greenfield is when the spec is CREATED, not skipped. Stage 1.5 writes the draft to `plans/<plan_dir>/spec/` from zero; promote moves it to `docs/features/` at implement-start. |
| "Study had nothing to do, so Spec falls with it." | Study reads what exists. Spec writes what will exist. They never share a fate. |
| "The task is simple — a spec is overhead." | Simple pieces hide the hardest grain. The spec costs minutes; an unspecified feature costs rework. |
| "Token efficiency — trim the pipeline." | Trim prose, not gates. The Blueprint Pre-flight must still print `[x] Spec drafted`. |
| "I'll author the spec after planning." | The spec draft is the plan's INPUT (`spec_draft`). After is too late — the planner would re-derive requirements. |
| "Every task needs a spec — safer to always author one." | A spec describes the SYSTEM. A deliverable is not the system. Forcing `F###` onto throwaway artifacts pollutes feature-list permanently (contiguity never forgets). Classify first. |
| "The repo is empty, so default the spec to English." | Greenfield interactive MUST run the Language Gate and ASK (en/vi/jp). Only takumi `--auto` may default to `en`; an existing `primary_lang` is inherited. Silently writing `lang: en` on an interactive run is a skipped gate, not a default. |
| "The contract told me everything about the spec." | The contract (`spec-authoring-contract.md`) only points to the procedure — it does NOT contain the Language Gate or the step logic. You MUST read `spec-stage-procedure.md` § Pre-Step before authoring; the SKILL.md summary alone is not enough to run the stage. |
| "This touches auth/architecture, but I'll let the post-forge Core pass write the system docs." | Step 2b forward-draft and the Step 6.a-pre gen gate back EACH OTHER up — skip the forward-draft and the only safety net is a gen-gate that may itself be skipped (re-baseline advisory on an existing baseline). Draft `docs/system/*` NOW; the Pre-flight System-doc box must read the draft path, not `N/A`, when the Trigger Mapping fires. |

## Delivery Anti-Rationalization (Stage 6 Specific)

The forge is hot. The inspection passed. The temptation is to seal the work with one final question. Resist — that is where the discipline most often fails.

| The Whisper | The Master's Answer |
|-------------|---------------------|
| "Tests pass, review approved — just commit." | The commit is not the seal. The Manifest is. The Manifest comes first. |
| "This change touches no docs — skip `doc-writer`." | You are not the docs authority. `doc-writer` is. Spawn it. It returns its verdict in seconds. |
| "The plan is already in sync — skip `project-manager`." | Stale checkboxes from earlier stages are the most common drift. Spawn it. |
| "The user said 'commit' — they want the commit." | A commit instruction is not a license to skip Delivery. Deliver first, then commit. |
| "rebuild-spec returned 'promoted 0 files' / errored — I'll hand-author the system + generated docs to fill the gap." | A hand-rolled doc subset is a SKIP of the gen gate, not a run — it never advances `docs/.rebuild-state.json`, so the cursor postcondition fails and the layer stays un-bootstrapped. ONLY `/tkm:rebuild-spec` satisfies the gate. A non-zero exit (incl. the `promoted 0` block) means STOP and fix the pipeline, never substitute your own files. |
| "I'll record the docs/journal in a follow-up session." | There is no follow-up session for this piece. It is sealed now or it is not sealed. |

## Workshop Delegation (Mandatory Subagents)

| Stage | Subagent | Requirement |
|-------|----------|-------------|
| Study | `researcher` | Optional in fast/code |
| Spec | `researcher` (spec-authoring contract) | Optional in fast/code |
| Scout | `tkm:scan-codebase` | Optional in code |
| Blueprint | `planner` | Optional in code |
| UI Craft | `ui-ux-designer` | If frontend work |
| **MoMorph UI** | **`implementer` (background, 1 per screen)** | **If MoMorph detected — spawn N agents for N screens BEFORE drafting** |
| Tempering | `tester`, `debugger` | **MUST** spawn |
| Inspection | `reviewer` | **MUST** spawn |
| Delivery | `project-manager`, `doc-writer`, `git-manager` | **MUST** spawn all 3 |

**Critical enforcement:**
- Stages 4, 5, 6 **MUST** use Task tool to spawn subagents
- DO NOT perform tempering, inspection, or delivery yourself — delegate
- If workflow ends with 0 Task tool calls, the work is INCOMPLETE
- Pattern: `Task(subagent_type="[type]", prompt="[task]", description="[brief]")`

## Stage 0 Pre-flight Gates

Three gates run at the head of Stage 0, in order, before any spec/blueprint work. The full
procedures (sentinel rollback shapes, the `.tkm.json` persistence bash, the `spec_lang` resolution
table) live in **`references/stage0-preflight-gates.md`** — read it when executing Stage 0; the
common `off` / no-sentinel paths never need to load it.

1. **Promote Sentinel Check** — if `docs/.spec-promote-pending.json` exists, a prior promote crashed
   mid-flight. **Do NOT proceed** — prompt REVERT/KEEP/Abort (SINGLE vs SYSTEM-v2 shapes) per the
   reference, then resolve before any new run.
2. **SDD Mode Gate** — resolve `takumi.sddMode` (injected `## Plan Context` `- SDD mode:` line /
   `$TKM_SDD_MODE` / `loadConfig()`). `on` → Stage 1.5 runs; `off` → skip Stage 1.5 project-wide
   (spec box `N/A — SDD mode disabled (takumi.sddMode: off)`); `ask` (first run) → **BLOCKING
   `AskUserQuestion` in all disciplines incl. `--auto`**, persist the answer to `.claude/.tkm.json`.
3. **Language Gate** — only when the spec stage will run (`on`, work-type ≠ deliverable, discipline ≠
   code): resolve `spec_lang`. Existing `primary_lang` is inherited; greenfield `--auto` defaults `en`
   silently; **greenfield interactive is BLOCKING** (ask en/vi/jp/Other — never silent `auto-en`).
   When the SDD gate is also prompting this run, ask BOTH in one `AskUserQuestion` call.

`code` discipline skips gates 2 and 3 (SDD Mode + Language — the blueprint already encodes those decisions); the Promote Sentinel Check (gate 1) still runs on every discipline, since a crashed prior promote is discipline-independent.

## References

- `references/intent-detection.md` — Material reading rules and discipline routing
- `references/stage0-preflight-gates.md` — Stage 0 gate procedures (Promote Sentinel, SDD Mode Gate, Language Gate)
- `references/workflow-steps.md` — Detailed stage definitions for all disciplines
- `references/review-cycle.md` — Interactive and auto inspection processes
- `references/subagent-patterns.md` — Workshop delegation patterns
- Canonical docs mapping: `claude/skills/_shared/docs-canonical-mapping.md` — surgical-edit rule, escalation heuristic, version policy
- Spec-authoring contract: `claude/skills/rebuild-spec/references/spec-authoring-contract.md` — contract file injected into the Stage 1.5 researcher prompt
- Spec stage procedure: `claude/skills/rebuild-spec/references/spec-stage-procedure.md` — authoritative Stage 1.5 steps incl. the **Pre-Step Language Gate** (`spec_lang` resolution)
