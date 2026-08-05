# Quick Workflow

A compressed scout-diagnose-fix-verify loop for simple issues.

## Steps

### Step 1: Scout (Minimal)
Pin the affected file(s) and their immediate dependencies — and stop there.
- Read the error message → find the file path
- Check what the affected file imports/depends on directly
- Don't bother mapping the whole codebase

**Output:** `✓ Step 1: Scouted - [file], [N] direct deps`

### Step 2: Diagnose (Abbreviated)
Activate `tkm:debug-code` skill. Activate `tkm:think-sequential` to keep the analysis structured.

- Read the error message/logs
- **Capture pre-fix state:** Save the exact error output — this is your verification baseline
- Name the root cause (for simple issues it usually announces itself)
- Skip parallel hypothesis testing on the trivial cases

**Output:** `✓ Step 2: Diagnosed - Root cause: [brief description]`

### Step 3: Fix & Verify
Apply the fix straight away.
- Smallest change that works
- Stay inside the existing patterns

**Parallel Verification:**
Launch `Bash` agents in parallel:
```
Task("Bash", "Run typecheck", "Verify types")
Task("Bash", "Run lint", "Verify lint")
```

**Before/After comparison:** Re-run the EXACT command from the pre-fix capture. Diff the output.

See `references/parallel-exploration.md` for patterns.

**Output:** `✓ Step 3: Fixed - [N] files, verified (types/lint passed)`

### Step 4: Review + Prevent
Hand off to the `reviewer` subagent for a quick pass.

Prompt: "Quick review of fix for [issue]. Check: correctness, security, no regressions. Score X/10."

**Prevention (abbreviated for Quick):**
- Type errors/lint: the type system already plays the test → regression test optional
- Bug fixes: drop in at least 1 test over the fixed scenario
- Still demand the before/after comparison of verification output

**Review handling:** See `references/review-cycle.md`

**Output:** `✓ Step 4: Review [score]/10 - [prevention measures]`

### Step 5: Complete
Report the summary to the user.

**If autonomous mode:** Offer to commit via the `git-manager` subagent when the score clears 9.0
**If HITL mode:** Ask the user where to go next

**Output:** `✓ Step 5: Complete - [action]`

## Skills/Subagents Activated

| Step | Skills/Subagents |
|------|------------------|
| 1 | `tkm:scan-codebase` (minimal) or direct file read |
| 2 | `tkm:debug-code`, `tkm:think-sequential` |
| 3 | Parallel `Bash` for verification |
| 4 | `reviewer` subagent |
| 5 | `git-manager` subagent |

**Extra:** `tkm:optimize-context` when the code is AI/LLM territory

## Notes

- If the review fails → bail out to the Standard workflow
- Total steps: 5
- No planning phase here
- Pre-fix state capture stays mandatory — even on the quick fixes
