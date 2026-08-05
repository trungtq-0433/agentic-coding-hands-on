# Merge Workflow

Run this through the `git-manager` subagent.

## Variables
- TO_BRANCH: where it lands — `main` unless told otherwise
- FROM_BRANCH: where it comes from — the current branch unless told otherwise

## Step 1: Sync with Remote

**IMPORTANT: fold `main` (or whatever the default branch is) into your branch before anything else.**

```bash
git fetch origin
git checkout {TO_BRANCH}
git pull origin {TO_BRANCH}
```

## Step 2: Merge from REMOTE
```bash
git merge origin/{FROM_BRANCH} --no-ff -m "merge: {FROM_BRANCH} into {TO_BRANCH}"
```

**Why `origin/{FROM_BRANCH}`:** it folds in only what was committed and pushed, leaving local work-in-progress out of the merge.

## Step 3: Resolve Conflicts
When conflicts show up:
1. Work through them by hand
2. `git add . && git commit`
3. If something needs a decision, kick it back to the main agent

## Step 4: Push
```bash
git push origin {TO_BRANCH}
```

## Pre-Merge Checklist
- Pull down the latest: `git fetch origin`
- Confirm FROM_BRANCH is up on the remote
- Dry-run for conflicts: `git merge --no-commit --no-ff origin/{FROM_BRANCH}`, then abort it

## Error Handling

| Error | Action |
|-------|--------|
| Merge conflicts | Settle them by hand, then commit |
| Branch not found | Check the name, make sure it was pushed |
| Push rejected | `git pull --rebase`, then try again |
