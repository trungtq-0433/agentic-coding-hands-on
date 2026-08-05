# Orchestration Protocol

## Workflow Tool (Opt-In Only)

**Never use the `Workflow` tool unless the user explicitly requests it with the word "workflow".** Orchestrate with the `Task` tool instead.

## Delegation Context (MANDATORY)

Every time you spawn a subagent through the Task tool, the prompt **ALWAYS** carries three things:

1. **Work Context Path**: the git root of the PRIMARY files being touched
2. **Reports Path**: `{work_context}/plans/reports/` for that project
3. **Plans Path**: `{work_context}/plans/` for that project

**Example:**
```
Task prompt: "Fix parser bug.
Work context: /path/to/project-b
Reports: /path/to/project-b/plans/reports/
Plans: /path/to/project-b/plans/"
```

**Rule:** When your CWD and the work context differ (you are editing files in another project), point at the **work context paths**, not the CWD paths.

---

#### Sequential Chaining
Chain subagents when one step depends on another or needs an earlier step's output:
- **Planning → Implementation → Simplification → Testing → Review**: the shape for feature development (tests run against the simplified code).
- **Research → Design → Code → Documentation**: the shape for a brand-new system component.
- Each agent finishes fully before the next one starts.
- Carry the context and outputs forward through the chain.

#### Parallel Execution
Fire off several subagents at once when the tasks don't touch each other:
- **Code + Tests + Docs**: separate, non-conflicting pieces.
- **Multiple Feature Branches**: different agents on isolated features.
- **Cross-platform Development**: iOS and Android handled separately.
- **Careful Coordination**: keep them off the same files and shared resources.
- **Merge Strategy**: settle the integration points before the parallel work begins.

---

## Subagent Status Protocol

When a subagent wraps up, it MUST report exactly one of these statuses:

| Status | Meaning | Controller Action |
|--------|---------|-------------------|
| **DONE** | Task completed successfully | Proceed to next step (review, next task) |
| **DONE_WITH_CONCERNS** | Completed but flagged doubts | Read concerns → address if correctness/scope issue → proceed if observational |
| **BLOCKED** | Cannot complete task | Assess blocker → provide context / break task / escalate to user |
| **NEEDS_CONTEXT** | Missing information to proceed | Provide missing context → re-dispatch |

### Handling Rules

- **Never** let BLOCKED or NEEDS_CONTEXT slide — something has to change before you retry.
- **Never** re-run the same approach after BLOCKED — escalate the response: more context → simpler task → more capable model → escalate to user.
- **DONE_WITH_CONCERNS** about file growth or tech debt → log it for later, keep moving now.
- **DONE_WITH_CONCERNS** about correctness → settle it before review.
- A subagent that fails the same task 3+ times → escalate to the user; don't keep retrying blind.

### Reporting Format

Subagents should close their response with:

```
**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
**Summary:** [1-2 sentence summary]
**Concerns/Blockers:** [if applicable]
```

---

## Context Isolation Principle

**A subagent gets only the context it needs — never the whole session history.**

### Rules

1. **Craft prompts explicitly** — spell out the task, the file paths that matter, and the acceptance criteria. Not "here's what we discussed."
2. **No session history** — the subagent starts fresh. Summarize the decisions that matter; don't replay the conversation.
3. **Scope file references** — name the specific files to read or change. Not "look at the codebase."
4. **Include plan context** — working from a plan, pass the one relevant phase, not the whole plan.
5. **Preserve controller context** — coordination stays in the main agent; keep that detail out of subagent prompts.

### Prompt Template

```
Task: [specific task description]
Files to modify: [list]
Files to read for context: [list]
Acceptance criteria: [list]
Constraints: [any relevant constraints]
Plan reference: [phase file path if applicable]

Work context: [project path]
Reports: [reports path]
```

### Anti-Patterns

| Bad | Good |
|-----|------|
| "Continue from where we left off" | "Implement X feature per spec in phase-02.md" |
| "Fix the issues we discussed" | "Fix null check in auth.ts:45, root cause: missing validation" |
| "Look at the codebase and figure out" | "Read src/api/routes.ts and add POST /users endpoint" |
| Passing 50+ lines of conversation | 5-line task summary with file paths |

---

## Agent Teams (Optional)

For multi-session parallel collaboration inside a Claude Code agent team, follow `team-coordination-rules.md` (file ownership, communication, task claiming). It sits outside the default orchestration flow.
