# Team Coordination Rules

> These rules apply only when you are operating as a teammate inside an Agent Team.
> Standard sessions and subagent workflows are untouched by them.

Rules for agents working as teammates within an Agent Team.

## File Ownership (CRITICAL)

- Every teammate MUST hold distinct files — no two editing the same one.
- Spell out ownership with glob patterns in the task description: `File ownership: src/api/*, src/models/*`.
- The lead untangles ownership clashes by reshaping tasks or taking the shared files itself.
- The tester owns test files only — it may read implementation files but never edit them.
- Catch an ownership violation → STOP and tell the lead at once.

## Git Safety

- Favor git worktrees for implementation teams — one dev per worktree, and the conflicts disappear.
- Never force-push from a teammate session.
- Commit often, with messages that say what changed.
- Pull before you push so merge conflicts surface early.
- Inside a worktree, commit and push to the worktree branch — not main, not dev.

## Communication Protocol

- `SendMessage(type: "message")` for peer DMs — always name the recipient.
- `SendMessage(type: "broadcast")` ONLY for a critical blocker that hits the whole team.
- Mark a task done with `TaskUpdate` BEFORE you send the completion message to the lead.
- Put the actionable finding in the message — not just "I'm done".
- Never send structured JSON status messages — plain text only.

## TKM Stack Conventions

### Report Output
- Drop reports into `{TKM_REPORTS_PATH}` (injected by the hook; falls back to `plans/reports/`).
- Name them `{type}-{date}-{slug}.md`, where type is your role (researcher, reviewer, debugger).
- Trade grammar for concision. Put any unresolved questions at the end.

### Commit Messages
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- No AI references in commit messages.
- Keep each commit on the actual code change.

### Docs Sync (Implementation Teams Only)
- Once implementation tasks land, the lead MUST weigh the docs impact.
- Say it outright: `Docs impact: [none|minor|major]`.
- If there is impact: update the `docs/` directory or flag it in the completion message.

## Task Claiming

- Take the lowest-ID unblocked task first — the earlier tasks set up the context for the later ones.
- Re-check `TaskList` after each task you finish, in case work has just unblocked.
- Flip the task to `in_progress` before you start.
- If everything is blocked, tell the lead and offer to help clear the way.

## Plan Approval Flow

When `plan_mode_required` is set:
1. Research and plan your approach (read-only — no file edits).
2. Send the plan via `ExitPlanMode` — this fires an approval request to the lead.
3. Wait for the lead's `plan_approval_response`.
4. Rejected → revise on the feedback and resubmit.
5. Approved → start implementing.

## Conflict Resolution

- Two teammates need the same file → escalate to the lead at once.
- A teammate's plan rejected twice → the lead takes the task over.
- Reviewers' findings conflict → the lead synthesizes and records the disagreement.
- Blocked by another teammate's unfinished work → message them directly first; escalate to the lead if they go quiet.

## Shutdown Protocol

- Approve shutdown requests unless you are mid-critical-operation.
- Always mark the current task completed before you approve a shutdown.
- Rejecting a shutdown → say why, briefly.
- Pull `requestId` from the shutdown request JSON and pass it to `shutdown_response`.

## Idle State (Normal Behavior)

- Going idle after sending a message is NORMAL — not a failure.
- Idle means waiting for input, not disconnected.
- Sending a message to an idle teammate wakes them.
- Don't read an idle notification as "done" — check the task status instead.

## Discovery

- Read the team config at `~/.claude/teams/{team-name}/config.json` to find your teammates.
- Always call teammates by NAME, never by agent ID.
- Names are what `recipient` in SendMessage and task `owner` in TaskUpdate expect.
