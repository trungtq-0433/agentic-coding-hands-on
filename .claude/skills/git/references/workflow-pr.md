# Pull Request Workflow

Run this through the `git-manager` subagent.

## Variables
- TO_BRANCH: where it lands — `main` unless told otherwise
- FROM_BRANCH: where it comes from — the current branch unless told otherwise

## CRITICAL: Use REMOTE diff
A PR is built from what lives on the remote. A local diff drags in changes you have not pushed yet.

## Tool 1: Sync + Analyze

**IMPORTANT: fold `main` (or whatever the default branch is) into your branch before anything else.**

```bash
git fetch origin && \
git push -u origin HEAD 2>/dev/null || true && \
BASE=${BASE_BRANCH:-main} && \
HEAD=$(git rev-parse --abbrev-ref HEAD) && \
echo "=== PR: $HEAD → $BASE ===" && \
echo "=== COMMITS ===" && \
git log origin/$BASE...origin/$HEAD --oneline && \
echo "=== FILES ===" && \
git diff origin/$BASE...origin/$HEAD --stat
```

**If "Branch not on remote":** push it up, then try again.

## Tool 2: Generate Content
**Title:** conventional-commit shape, under 72 chars, no version numbers
**Body:** a few summary bullets plus a test-plan checklist

## Tool 3: Create PR
```bash
gh pr create --base $BASE --head $HEAD --title "..." --body "$(cat <<'EOF'
## Summary
- Bullet points

## Test plan
- [ ] Test item
EOF
)"
```

## Steer clear of (these compare locally)
- ❌ `git diff main...HEAD`
- ❌ `git diff --cached`
- ❌ `git status`

## Error Handling

| Error | Action |
|-------|--------|
| Branch not on remote | `git push -u origin HEAD`, then try again |
| Empty diff | Say so — there is nothing to open a PR for |
| Push rejected | `git pull --rebase`, settle it, push |
| No upstream | `git push -u origin HEAD` |
