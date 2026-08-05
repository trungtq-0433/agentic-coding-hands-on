# Push Workflow

Run this through the `git-manager` subagent.

## Pre-Push Checklist
1. Nothing left uncommitted
2. Diff combed for secrets (see `safety-protocols.md`)
3. Branch tracked on the remote

## Tool 1: Verify State
```bash
git status && \
git log origin/$(git rev-parse --abbrev-ref HEAD)..HEAD --oneline 2>/dev/null || echo "NO_UPSTREAM"
```

**If work is still uncommitted:** flag it and tell the user to commit before pushing.
**If NO_UPSTREAM:** reach for `git push -u origin HEAD`.

## Tool 2: Push
```bash
git push origin HEAD
```

**On success:** name the commit hashes that went up.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `rejected - non-fast-forward` | The remote moved ahead of you | `git pull --rebase`, settle the conflicts, push once more |
| `no upstream branch` | The branch has no tracking ref | `git push -u origin HEAD` |
| `Authentication failed` | Credentials are bad | Look at `gh auth status` or your SSH keys |
| `Repository not found` | The remote URL is off | Confirm it with `git remote -v` |
| `Permission denied` | You lack write rights | Review the repo's permissions |

## Force Push (DANGER)

**A force push must never touch main, master, or production.**

Only when the user asks for it by name, and only on a feature branch:
```bash
git push -f origin HEAD
```

**Warn the user:** a force push rewrites history, and a teammate's work can vanish with it.

## Output Format
```
✓ pushed: N commits to origin/{branch}
  - abc123 feat(auth): add login
  - def456 fix(api): resolve timeout
```
