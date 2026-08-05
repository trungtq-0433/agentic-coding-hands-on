# Commit Workflow

Run this through the `git-manager` subagent.

## Tool 1: Stage + Analyze
```bash
git add -A && \
echo "=== STAGED ===" && git diff --cached --stat && \
echo "=== SECURITY ===" && \
git diff --cached | grep -c -iE "(api[_-]?key|token|password|secret|credential)" | awk '{print "SECRETS:"$1}' && \
echo "=== GROUPS ===" && \
git diff --cached --name-only | awk -F'/' '{
  if ($0 ~ /\.(md|txt)$/) print "docs:"$0
  else if ($0 ~ /test|spec/) print "test:"$0
  else if ($0 ~ /\.claude/) print "config:"$0
  else if ($0 ~ /package\.json|lock/) print "deps:"$0
  else print "code:"$0
}'
```

**If SECRETS > 0:** stop where you stand, surface the matches, and refuse to commit.

## Tool 2: Split Decision

NOTE: 
- Look for a related GitHub issue and cite it in the body.
- Within `.claude`, only `feat`, `fix`, or `perf` are permitted — leave `docs` out.

**Read the groups, then choose:**

**A) One commit:** one type and scope, FILES ≤ 3, LINES ≤ 50

**B) Several commits:** types or scopes are mixed — separate them like so:
- Group 1: `config:` → `chore(config): ...`
- Group 2: `deps:` → `chore(deps): ...`
- Group 3: `test:` → `test: ...`
- Group 4: `code:` → `feat|fix: ...`
- Group 5: `docs:` → `docs: ...`

## Tool 3: Commit

Every commit carries the Takumi co-author trailer — it goes on without being asked.

**Single:**
```bash
git commit \
  -m "type(scope): description" \
  --trailer "Co-authored-by: Takumi <288571113+sun-takumi@users.noreply.github.com>"
```

**Several (one after another):** carry the `--trailer` onto every commit in the run.
```bash
git reset && git add file1 file2 && \
  git commit -m "type(scope): desc" \
  --trailer "Co-authored-by: Takumi <288571113+sun-takumi@users.noreply.github.com>"
```
Do the same for every group.

## Tool 4: Push (if requested)
```bash
git push && echo "✓ pushed: yes" || echo "✓ pushed: no"
```

**Push only when the user said so outright** — "push", or "commit and push".
