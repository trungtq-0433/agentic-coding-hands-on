---
name: input-mode-resolution
description: Turning whatever the user typed — a PR number, a commit hash, --pending, or nothing at all — into a concrete diff the review pipeline can chew on
---

# Input Mode Resolution

Resolve `/code-review` arguments into a diff for the review pipeline.

## Auto-Detection Rules

Walk the arguments left to right; the first pattern that matches takes it.

| Pattern | Mode | Example |
|---------|------|---------|
| `#\d+` | PR | `#123`, `#45` |
| GitHub PR URL | PR | `https://github.com/org/repo/pull/123` |
| `[0-9a-f]{7,40}` | Commit | `abc1234`, full SHA |
| `--pending` | Pending | explicit flag |
| `codebase` | Codebase | existing mode |
| *(none + context)* | Default | recent changes |
| *(none + no context)* | Prompt | ask user via `AskUserQuestion` |

## Resolution Commands

### PR Mode

```bash
# Extract PR number from argument
PR_NUM=$(echo "$ARG" | grep -oE '[0-9]+$')

# Fetch PR metadata
gh pr view "$PR_NUM" --json title,body,files,additions,deletions,baseRefName,headRefName

# Get the diff
gh pr diff "$PR_NUM"

# Get changed file list
gh pr diff "$PR_NUM" --name-only
```

**Context passed to reviewers:**
- PR title and description (intent)
- Base branch (what it merges into)
- Full diff
- Changed file list for scout

### Commit Mode

```bash
# Validate commit exists
git cat-file -t "$COMMIT_HASH"

# Get commit metadata
git log -1 --format="%H%n%s%n%b" "$COMMIT_HASH"

# Get the diff
git show "$COMMIT_HASH" --stat
git show "$COMMIT_HASH" -- # full diff

# Changed files
git show "$COMMIT_HASH" --name-only --format=""
```

**Context passed to reviewers:**
- Commit message (intent)
- Parent commit (what it changed from)
- Full diff
- Changed file list for scout

### Pending Mode

```bash
# Staged changes
git diff --cached

# Unstaged changes
git diff

# Combined (staged + unstaged vs HEAD)
git diff HEAD

# Changed files
git diff HEAD --name-only

# Status overview
git status --short
```

**Context passed to reviewers:**
- No commit message exists yet — ask the user for a one-line intent
- The combined diff (staged + unstaged)
- Changed file list for scout

### Default Mode

Lean on whatever changes are already sitting in the conversation. If none are in sight, drop to Prompt mode.

### Prompt Mode

When no arguments and no recent context, use `AskUserQuestion`:
- Header: "Review Target"
- Question: "What would you like to review?"
- Options: Pending changes, Enter PR number, Enter commit hash, Full codebase scan, Parallel codebase audit

For PR/commit options, follow up with second `AskUserQuestion` to get the number/hash.

### Codebase Mode

The codebase modes skip diff resolution entirely and sweep the whole tree instead.
- `codebase` → hand off to `references/codebase-scan-workflow.md`
- `codebase parallel` → hand off to `references/parallel-review-workflow.md`

Both workflows include adversarial review (always-on).

## Pipeline Handoff

With the diff resolved, feed it into the review pipeline:

```
Resolved diff
  ├─ Changed files → Edge case scout
  ├─ Full diff → Stage 1 (Spec compliance, if plan exists)
  ├─ Full diff → Stage 2 (Code quality review)
  └─ Full diff + findings → Stage 3 (Adversarial review)
```

## Error Handling

| Error | Action |
|-------|--------|
| PR not found | `gh pr view` fails → report "PR #N not found in this repo" |
| Commit not found | `git cat-file` fails → report "Commit not found — is it pushed?" |
| No pending changes | `git diff HEAD` empty → report "No pending changes to review" |
| Ambiguous input | Reads as either PR or commit → lean PR (the common case), and flag the assumption |
