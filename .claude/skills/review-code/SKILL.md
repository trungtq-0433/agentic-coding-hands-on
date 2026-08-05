---
name: tkm:review-code
description: "Adversarial code review before merging — surfaces security holes, false assumptions, and failure modes across pending changes, PRs, commits, or full codebase scan. Red-team analysis prevents issues from shipping."
argument-hint: "[#PR | COMMIT | --pending | codebase [parallel]] [--level low|medium|high|max] [--codex-companion]"
metadata:
  author: takumi-agent-kit
  version: "2.1.0"
module: testing-code-quality
triggers: ["review code", "code review", "check my PR", "before merging", "is this safe"]
---

# The Master's Inspection

A master craftsman does not admire finished work — they interrogate it.
Every joint is pressed. Every surface is checked against the light.
The piece must hold not just under ideal conditions, but under every force that will ever touch it.

This skill is that interrogation: structured, adversarial, evidence-based.
Praise is not inspection. Discomfort is the point.

## What to Inspect

Auto-detect from arguments. If ambiguous or no arguments, prompt via `AskUserQuestion`.

| Input | Mode | What Gets Reviewed |
|-------|------|--------------------|
| `#123` or PR URL | **PR** | Full PR diff fetched via `gh pr diff` |
| `abc1234` (7+ hex chars) | **Commit** | Single commit diff via `git show` |
| `--pending` | **Pending** | Staged + unstaged changes via `git diff` |
| *(no args, recent changes)* | **Default** | Recent changes in context |
| `codebase` | **Codebase** | Full codebase scan |
| `codebase parallel` | **Codebase+** | Parallel multi-reviewer audit |

**Resolution details:** `references/input-mode-resolution.md`

### When Called Without Arguments

If invoked WITHOUT arguments and no recent changes in context, use `AskUserQuestion` with header "Review Target", question "What would you like to review?":

| Option | Description |
|--------|-------------|
| Pending changes | Review staged/unstaged git diff |
| Enter PR number | Fetch and review a specific PR |
| Enter commit hash | Review a specific commit |
| Full codebase scan | Deep codebase analysis |
| Parallel codebase audit | Multi-reviewer codebase scan |

## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | Stage 1 spec | Stage 2 quality | Stage 3 adversarial |
|-------|-------------|----------------|---------------------|
| `low` | Skip | Quick pass | No |
| `medium` *(default)* | Yes | Standard | Scope gate applies |
| `high` | Yes | Deep | Forced |
| `max` | Yes | Deep | Parallel multi-reviewer |

> `--level max` is equivalent to `codebase parallel` + full 3-stage pipeline.
> `--level high` overrides the Stage 3 scope gate (skips the `≤2 files, ≤30 lines` exemption).
> At `--level low`, Stage 1 spec compliance is skipped *unless* the review runs from a plan (plan context forces spec compliance back on); the quick pass is Stage 2 quality — this is review-code's "quick-pass equivalent" per `_shared/processing-levels.md`.

## The Inspection Law

**YAGNI**, **KISS**, **DRY** always. Technical correctness over social comfort.
Honest findings, not comfortable ones. Straight to the point. Concise.

Verify before claiming. Ask before assuming. Evidence before conclusions.

## Inspection Disciplines

| Discipline | When | Reference |
|----------|------|-----------|
| **Spec compliance** | After implementing from plan/spec, BEFORE quality review | `references/spec-compliance-review.md` |
| **Adversarial review** | Always-on Stage 3 — actively tries to break the code | `references/adversarial-review.md` |
| Receiving feedback | Unclear feedback, external reviewers, needs prioritization | `references/code-review-reception.md` |
| Requesting review | After tasks, before merge, stuck on problem | `references/requesting-code-review.md` |
| Verification gates | Before any completion claim, commit, PR | `references/verification-before-completion.md` |
| Static lint evidence | Pending/full reviews where SunLint output can sharpen findings | `/tkm:lint-code` |
| Edge case scouting | After implementation, before review | `references/edge-case-scouting.md` |
| **Checklist review** | Pre-landing, `/tkm:ship-feature` pipeline, security audit | `references/checklist-workflow.md` |
| **Task-managed reviews** | Multi-file features (3+ files), parallel reviewers, fix cycles | `references/task-management-reviews.md` |

## Graph Context

When `graphify-out/graph.json` exists (Knowledge Graph is on by default), load `../_shared/graphify-code-graph.md` before edge
scouting or codebase review. Use `graphify affected`, `path`, and `explain` to pick context files
and likely impact paths. The diff remains the review boundary: graph output can expand context, but
do not report issues outside ADDED/MODIFIED code unless the change makes that existing code newly
exploitable.

## How to Route the Work

```
SITUATION?
│
├─ Input mode? → Resolve diff (references/input-mode-resolution.md)
│   ├─ #PR / URL → fetch PR diff
│   ├─ commit hash → git show
│   ├─ --pending → git diff (staged + unstaged)
│   ├─ codebase → full scan (references/codebase-scan-workflow.md)
│   ├─ codebase parallel → parallel audit (references/parallel-review-workflow.md)
│   └─ default → recent changes in context
│
├─ Received feedback → STOP if unclear, verify if external, implement if human partner
├─ Completed work from plan/spec:
│   ├─ Stage 1: Spec compliance review (references/spec-compliance-review.md)
│   │   └─ PASS? → Stage 2 │ FAIL? → Fix → Re-review Stage 1
│   ├─ Stage 2: Code quality review (reviewer subagent)
│   │   └─ Scout edge cases → Review standards, performance
│   └─ Stage 3: Adversarial review (references/adversarial-review.md) [ALWAYS-ON]
│       └─ Red-team the code → Adjudicate → Accept/Reject findings
├─ Completed work (no plan) → Scout → Code quality → Adversarial review
├─ Pre-landing / ship → Load checklists → Two-pass review → Adversarial review
├─ Multi-file feature (3+ files) → Create review pipeline tasks (scout→review→adversarial→fix→verify)
└─ About to claim status → RUN verification command FIRST
```

### Three-Stage Inspection Protocol

**Stage 1 — Spec Compliance** (load `references/spec-compliance-review.md`)
- Does code match what was requested?
- Any missing requirements? Any unjustified extras?
- MUST pass before Stage 2

**Stage 2 — Code Quality** (reviewer subagent)
- Only runs AFTER spec compliance passes
- Standards, security, performance, edge cases
- Use `/tkm:lint-code` output when available, or run it for pending/full reviews when static analysis would add evidence. SunLint supports the review; it does not replace reasoning review.

**Stage 3 — Adversarial Review** (load `references/adversarial-review.md`)
- Runs AFTER Stage 2 passes, subject to scope gate (skip if <=2 files, <=30 lines, no security files)
- Spawn adversarial reviewer with context anchoring (runtime, framework, context files)
- Find: security holes, false assumptions, resource exhaustion, race conditions, supply chain, observability gaps
- Output: Accept (must fix) / Reject (false positive) / Defer (GitHub issue) verdicts per finding
- Critical findings block merge; re-reviews use fix-diff-only optimization
- When feeding an evidence-gated flow, adjudicated findings become `inspection-verdict.json`'s `findings[]` -- every Accept finding needs a real `file:line` location or the evidence gate blocks (`_shared/references/evidence-artifacts.md`, `agents/reviewer.md` Evidence Verdict Contract)

## When Feedback Arrives

**Pattern:** READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT
No performative agreement. Verify before implementing. Push back when wrong.

**Full protocol:** `references/code-review-reception.md`

## Commissioning an Inspection

**When:** After each task, major features, before merge

**Process:**
1. **Scout edge cases first** (see below)
2. Get SHAs: `BASE_SHA=$(git rev-parse HEAD~1)` and `HEAD_SHA=$(git rev-parse HEAD)`
3. Dispatch reviewer subagent with: WHAT, PLAN, BASE_SHA, HEAD_SHA, DESCRIPTION
4. Fix Critical immediately, Important before proceeding

**Full protocol:** `references/requesting-code-review.md`

## Scouting the Edges

**When:** After implementation, before commissioning a reviewer

**Process:**
1. If `graphify-out/graph.json` exists (Knowledge Graph is on by default), load `../_shared/graphify-code-graph.md` and use `graphify affected/path/explain` to seed impact scope
2. Invoke `/tkm:scan-codebase` with edge-case-focused prompt, including graph-derived candidates
3. Scout analyzes: affected files, data flows, error paths, boundary conditions
4. Review scout findings for potential issues
5. Address critical gaps before code review

**Full protocol:** `references/edge-case-scouting.md`

## Inspection Pipeline (Task-Managed)

**When:** Multi-file features (3+ changed files), parallel reviewer scopes, review cycles with Critical fix iterations.

**Fallback:** Task tools (`TaskCreate`/`TaskUpdate`/`TaskGet`/`TaskList`) are CLI-only — unavailable in VSCode extension. If they error, use `TodoWrite` for tracking and run pipeline sequentially. Inspection quality is identical.

**Pipeline:** scout → review → adversarial → fix → verify (each a Task with dependency chain)

```
TaskCreate: "Scout edge cases"         → pending
TaskCreate: "Review implementation"    → pending, blockedBy: [scout]
TaskCreate: "Adversarial review"       → pending, blockedBy: [review]
TaskCreate: "Fix critical issues"      → pending, blockedBy: [adversarial]
TaskCreate: "Verify fixes pass"        → pending, blockedBy: [fix]
```

**Parallel reviews:** Spawn scoped reviewer subagents for independent file groups (e.g., backend + frontend). Fix task blocks on all reviewers completing.

**Re-review cycles:** If fixes introduce new issues, create cycle-2 review task. Limit 3 cycles, escalate to user after.

**Full protocol:** `references/task-management-reviews.md`

## Codex Companion (opt-in, `--codex-companion`)

When `--codex-companion` is passed, read `references/codex-companion.md` and follow it (a second model
cross-checks the diff before the Verification Gate). Otherwise skip — no extra cost when the flag is unused.

## The Verification Gate

**Iron Law:** NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE

**Cross-model dedupe (when Codex companion ran):** collapse findings that share `file:line` + symptom.
- Same finding from both models → mark **"confirmed by claude+codex"** (higher confidence).
- Reported by only one model → keep it, tag `⚠ single-model`; the gate still requires a real `file:line` (findings without one are dropped, regardless of source).

**Gate:** IDENTIFY command → RUN full → READ output → VERIFY confirms → THEN claim

**Requirements:**
- Tests pass: Output shows 0 failures
- Build succeeds: Exit 0
- Bug fixed: Original symptom passes
- Requirements met: Checklist verified

**Warning signs:** "should"/"probably"/"seems to", satisfaction before verification, trusting agent reports without running commands

**Full protocol:** `references/verification-before-completion.md`

## Where This Fits

- **Subagent-Driven:** Scout → Review → Adversarial → Verify before next task
- **Pull Requests:** Scout → Code quality → Adversarial → Merge
- **Task Pipeline:** Create review tasks with dependencies → auto-unblock through chain
- **Takumi Handoff:** Takumi completes phase → review pipeline tasks (incl. adversarial) → all complete → takumi proceeds
- **PR Review:** `/code-review #123` → fetch diff → full 3-stage review on PR changes
- **Commit Review:** `/code-review abc1234` → review specific commit with full pipeline

## Codebase Analysis Subcommands

| Subcommand | Reference | Purpose |
|------------|-----------|---------|
| `/tkm:review-code codebase` | `references/codebase-scan-workflow.md` | Scan & analyze the codebase |
| `/tkm:review-code codebase parallel` | `references/parallel-review-workflow.md` | Ultrathink edge cases, then parallel verify |

Shared graph rule: `../_shared/graphify-code-graph.md`.

## The Master's Standard

1. Know what you are inspecting before touching it — resolve input mode first
2. Technical truth over social ease
3. Scout the edges before calling in the inspector
4. Adversarial review on EVERY piece — no exceptions
5. Evidence first. Conclusions after.

Inspect. Probe. Break. Question. Verify. Then — and only then — sign off.
