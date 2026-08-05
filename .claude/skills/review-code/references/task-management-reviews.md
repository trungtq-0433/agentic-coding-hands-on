# Review Task Management Patterns

Drive the review pipeline through Claude Native Tasks (TaskCreate, TaskUpdate, TaskList) so each stage stays visible.

## When to Create Tasks

| Review Scope | Tasks? | Rationale |
|--------------|--------|-----------|
| Single-file fix | No | Scout, review, done — the bookkeeping isn't worth it |
| Multi-file feature (3+ files) | Yes | Worth tracking the scout → review → fix → verify chain |
| Parallel reviewers (2+ scopes) | Yes | Keeps the independent reviews in step |
| Review cycle with Critical fixes | Yes | The fix → re-verify dependency needs ordering |

**3-Task Rule:** If the pipeline has fewer than 3 meaningful steps, don't bother creating tasks.

## Review Pipeline as Tasks

```
TaskCreate: "Scout edge cases"         → pending
TaskCreate: "Review implementation"    → pending, blockedBy: [scout]
TaskCreate: "Adversarial review"       → pending, blockedBy: [review]
TaskCreate: "Fix critical issues"      → pending, blockedBy: [adversarial]
TaskCreate: "Verify fixes pass"        → pending, blockedBy: [fix]
```

Dependency chain auto-unblocks: scout → review → adversarial → fix → verify.

## Task Schemas

### Scout Task

```
TaskCreate(
  subject: "Scout edge cases for {feature}",
  activeForm: "Scouting edge cases",
  description: "Identify affected files, data flows, boundary conditions. Changed: {files}",
  metadata: { reviewStage: "scout", feature: "{feature}",
              changedFiles: "src/auth.ts,src/middleware.ts",
              priority: "P2", effort: "3m" }
)
```

### Review Task

```
TaskCreate(
  subject: "Review {feature} implementation",
  activeForm: "Reviewing {feature}",
  description: "Code-reviewer subagent reviews {BASE_SHA}..{HEAD_SHA}. Plan: {plan_ref}",
  metadata: { reviewStage: "review", feature: "{feature}",
              baseSha: "{BASE_SHA}", headSha: "{HEAD_SHA}",
              priority: "P1", effort: "10m" },
  addBlockedBy: ["{scout-task-id}"]
)
```

### Adversarial Task

```
TaskCreate(
  subject: "Adversarial review for {feature}",
  activeForm: "Red-teaming {feature}",
  description: "Spawn adversarial reviewer to break the code. See references/adversarial-review.md",
  metadata: { reviewStage: "adversarial", feature: "{feature}",
              priority: "P1", effort: "10m" },
  addBlockedBy: ["{review-task-id}"]
)
```

### Fix Task (created after adversarial finds issues)

```
TaskCreate(
  subject: "Fix {severity} issues from review",
  activeForm: "Fixing {severity} review issues",
  description: "Address: {issue_list}",
  metadata: { reviewStage: "fix", severity: "critical",
              issueCount: 3, priority: "P1", effort: "15m" },
  addBlockedBy: ["{review-task-id}"]
)
```

### Verify Task

```
TaskCreate(
  subject: "Verify fixes pass tests and build",
  activeForm: "Verifying fixes",
  description: "Run test suite, build, confirm 0 failures. Evidence before claims.",
  metadata: { reviewStage: "verify", priority: "P1", effort: "5m" },
  addBlockedBy: ["{fix-task-id}"]
)
```

## Parallel Review Coordination

When the change spans independent scopes (say, backend and frontend moved separately):

```
// Create scoped review tasks — no blockedBy between them
TaskCreate(subject: "Review backend auth changes",
  metadata: { reviewStage: "review", scope: "src/api/,src/middleware/",
              agentIndex: 1, totalAgents: 2, priority: "P1" })

TaskCreate(subject: "Review frontend auth UI",
  metadata: { reviewStage: "review", scope: "src/components/auth/",
              agentIndex: 2, totalAgents: 2, priority: "P1" })

// Both run simultaneously via separate reviewer subagents
// Fix task blocks on BOTH completing:
TaskCreate(subject: "Fix all review issues",
  addBlockedBy: ["{backend-review-id}", "{frontend-review-id}"])
```

## Task Lifecycle

```
Scout:       pending → in_progress → completed (scout report is back)
Review:      pending → in_progress → completed (reviewer findings are in)
Adversarial: pending → in_progress → completed (red-team findings adjudicated)
Fix:         pending → in_progress → completed (every Critical/Important resolved)
Verify:      pending → in_progress → completed (tests green, build clean)
```

### Handling Re-Reviews

When a fix breaks something new → open a fresh review cycle:

```
TaskCreate(subject: "Re-review after fixes",
  addBlockedBy: ["{fix-task-id}"],
  metadata: { reviewStage: "review", cycle: 2, priority: "P1" })
```

Cap it at 3 cycles. Still red after the third → hand it to the user.

## Integration with Planning Tasks

Review tasks live **apart from** the takumi/planning phase tasks.

**When takumi kicks off a review:**
1. Takumi finishes an implementation phase → spins up the review pipeline tasks
2. The pipeline runs its course (scout → review → adversarial → fix → verify)
3. Every review task closes → takumi stamps the phase as reviewed
4. Takumi moves on to the next phase

Review tasks point at the phase without blocking it outright — the orchestrator owns the handoff.

## Quality Check

After pipeline registration: `Registered [N] review tasks (scout → review → adversarial → fix → verify chain)`

## Error Handling

If `TaskCreate` errors: log a warning and run the review sequentially, untracked. The pipeline behaves the same — the tasks buy visibility, not capability.
