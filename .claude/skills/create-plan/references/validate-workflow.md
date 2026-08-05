# Validate Workflow

Sit the user down with the hard questions — test the assumptions, lock in the decisions, and drag any lurking problems into the open before a line of code gets written.

## Plan Resolution

1. `$ARGUMENTS` given → use that path
2. Otherwise read the `## Plan Context` section → use the active plan path
3. Still nothing → ask the user for a path, or to run `/tkm:create-plan --level high` first

## Configuration

Pull the validation settings from the `## Plan Context` section:
- `mode` - drives the auto/prompt/off behavior
- `questions` - a range like `3-8` (min-max)

## Workflow

### Step 1: Read Plan Files
- `plan.md` - the overview and the phases list
- `phase-*.md` - every phase file
- Hunt for decision points, assumptions, risks, and trade-offs

### Step 2: Extract Question Topics
Load: `references/validate-question-framework.md`

### Step 3: Verification Pass
Before the interview opens, check the plan's claims against the codebase — don't take the prose's
word for it. Load: `references/verification-roles.md`.

**Guard:** if `plan.md` already carries a `## Red Team Review` section with verification evidence
attached, skip straight to Step 4 and only chase down any `[UNVERIFIED]` tags still open.

1. For the claims each phase leans on, run whichever role from `verification-roles.md` fits —
   Citation Checker for paths/symbols, Consumer Auditor for interface changes, Behavior Path Tracer
   for behavioral claims. Sample a handful per phase; widen the sample if a phase leans on a lot of
   external references.
2. Tag each sampled claim `GROUNDED — file:line` | `UNSUPPORTED — no match` | `INCONCLUSIVE`.
3. Every `UNSUPPORTED` claim becomes an interview question in Step 4 — bring a glob-suggested
   alternative along and mark it "(Recommended)". Never quietly rewrite the plan yourself; every
   correction goes through the interview so the user signs off on it.
4. Scan the plan for any `[UNVERIFIED]` tag the planner left behind and try to resolve it now.
5. Append the results to `## Validation Log`:
   ```
   ### Verification Results
   - Claims checked: N
   - Verified: N | Failed: N | Unverified: N
   - Failures: [list with file:line evidence]
   ```

### Step 4: Generate Questions
Turn each topic you found into a concrete question carrying 2-4 options.
Tag the one you'd recommend with a "(Recommended)" suffix.

### Step 5: Interview User
Run the `AskUserQuestion` tool.
- Take the question count from the `## Plan Context` validation settings
- Bundle related questions together (4 to a tool call, no more)
- Aim at the assumptions, the risks, the trade-offs, the architecture

**If `--grill` is active:** ignore the steps above. Load `../../../rules/grill-loop-protocol.md`
and run the grill loop instead — one question at a time, adaptive, no `questions=` count and no
4-per-call batching. Sink = the `## Validation Log` (see Step 6). The interview stays on the main
thread even when `--parallel` fanned research out to sub-agents.

### Step 6: Document Answers
Open or extend a `## Validation Log` section inside `plan.md`.
Load: `references/validate-question-framework.md` for the recording format.
Under `--grill`, append each decision to the log **the moment it crystallizes** (one entry per
answer, as it arrives) rather than waiting for the whole interview to finish.

### Step 7: Propagate Changes to Phases
Push the validation decisions out to whichever phase files they touch.
Drop in a marker: `<!-- Updated: Validation Session N - {change} -->`

### Step 8: Cross-Phase Claim Reconciliation
See `references/verification-roles.md` — the "Cross-Phase Claim Reconciliation" procedure.

Propagation fixes the phases a decision explicitly touched. This sweep catches the rest — re-read
`plan.md` and every `phase-*.md`, build the delta list from what this session just decided, and
hunt down any stale term, reversed assumption, or duplicate embedded draft the propagation left
behind elsewhere. Append the sweep's output to the current `## Validation Log`. If a contradiction
survives the sweep, list it as unresolved and don't recommend cooking yet.

## Output
- How many questions you asked
- The key decisions now locked in
- What the phase propagation changed
- Whole-plan consistency sweep results
- Your call: proceed or revise

## Next Steps (MANDATORY)
Remind the user, absolute path filled in:
> **Best Practice:** Run `/clear` before building so you start on a clean slate.
> Then run:
> ```
> /tkm:takumi --auto {ABSOLUTE_PATH_TO_PLAN_DIR}/plan.md
> ```
> **Why `--auto`?** The plan's already been validated, so the review gates can come off.
> **Why the absolute path?** A `/clear` wipes what the last session knew.
> A clean slate lets Claude give all its attention to building, free of planning-context noise.

## Important Notes
- Only raise the questions that hinge on a real decision
- A simple plan can land under the minimum question count — that's fine
- Lead with the questions that could swing the implementation hardest
- Don't recommend cooking while an `UNSUPPORTED` verification result or an open `[UNVERIFIED]` tag is
  still sitting unresolved, and don't recommend it while the consistency sweep still lists an
  open contradiction
