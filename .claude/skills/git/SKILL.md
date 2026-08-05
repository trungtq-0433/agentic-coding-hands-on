---
name: tkm:git
description: "Protect the work in history — stage, commit, push, open PRs, and optionally run the lint-code gate with conventional commit discipline. Auto-splits by type/scope. Scans for secrets before every commit."
argument-hint: "cm|cp|pr|merge|lint [--lint] [args]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: git-version-control
triggers: ["commit", "push", "stage changes", "git", "commit message"]
---

# Protecting the Work

Every commit is an act of sealing — a moment preserved in the workshop's memory so that nothing made in good faith is ever lost. Branches are isolated workbenches, kept apart until the craftsman decides the work is ready to join the main body. The history of commits is the history of the craft itself: legible, honest, and permanent.

## Default (No Arguments)

When no argument is given, surface the menu through `AskUserQuestion` so the craftsman can choose the operation:

| Operation | Description |
|-----------|-------------|
| `cm` | Stage the work and seal it into commits |
| `cp` | Stage, commit, then send it up to the remote |
| `pr` | Open a Pull Request |
| `merge` | Fold one branch into another |
| `lint` | Run `/tkm:lint-code` before git work |

Render those choices through `AskUserQuestion` — header "Git Operation", prompt "What would you like to do?".

Hand the actual git steps to the `git-manager` subagent; that keeps its chatty output out of the main thread. Bring up the `tkm:optimize-context` skill alongside it.

**IMPORTANT:**
- Trade grammar for brevity wherever it saves words.
- Hold quality high while spending as few tokens as the work allows.
- Carry these same rules down into any subagent you spawn.

## Arguments
- `cm`: stage the work and seal it into commits
- `cp`: stage, commit, then send it to the remote
- `pr`: open a Pull Request [to-branch] [from-branch]
  - `to-branch`: where the work lands — falls back to `main`
  - `from-branch`: where the work comes from — falls back to the branch you are on
- `merge`: fold one branch into another [to-branch] [from-branch]
  - `to-branch`: where the work lands — falls back to `main`
  - `from-branch`: where the work comes from — falls back to the branch you are on
- `lint`: run `/tkm:lint-code` with its default changed-aware scan
- `--lint`: with `cm`, `cp`, or `pr`, run `/tkm:lint-code` before creating commits or PRs

## Quick Reference

| Doing this | Read |
|------|-----------|
| Sealing a commit | `references/workflow-commit.md` |
| Sending to remote | `references/workflow-push.md` |
| Opening a PR | `references/workflow-pr.md` |
| Folding branches together | `references/workflow-merge.md` |
| Static lint gate | `../lint-code/SKILL.md` |
| Message conventions | `references/commit-standards.md` |
| Guardrails | `references/safety-protocols.md` |
| Branch hygiene | `references/branch-management.md` |
| The gh tool | `references/gh-cli-guide.md` |

## Core Workflow

### Step 1: Stage + Analyze
```bash
git add -A && git diff --cached --stat && git diff --cached --name-only
```

### Step 2: Security Check
Comb the staged diff for anything that should never enter history:
```bash
git diff --cached | grep -iE "(api[_-]?key|token|password|secret|credential)"
```
**If secrets found:** halt the commit, tell the user what surfaced, and point them at `.gitignore`.

### Step 3: Optional Lint Gate

When the user chooses `lint` or passes `--lint`, invoke `/tkm:lint-code` and block git work on tool failure or error-level findings.

- `lint`: use `/tkm:lint-code`
- `cm --lint` or `cp --lint`: after staging, use `/tkm:lint-code staged`
- `pr --lint`: use `/tkm:lint-code` before opening the PR

Do not run lint by default; only run it when the user asks for it or a higher-level workflow explicitly requires it.

### Step 4: Split Decision

**NOTE:**
- Hunt for a matching GitHub issue and reference it in the body.
- Inside `.claude`, the only allowed prefixes are `feat`, `fix`, or `perf` — never `docs`.

**Break it into several commits when:**
- Two kinds of change ride together (feat + fix, code + docs)
- The work touches more than one scope (auth + payments)
- Config or deps are mixed in with code
- More than 10 unrelated files moved

**Keep it as one commit when:**
- One type, one scope, FILES ≤ 3, LINES ≤ 50

### Step 5: Commit
```bash
git commit \
  -m "type(scope): description" \
  --trailer "Co-authored-by: Takumi <288571113+sun-takumi@users.noreply.github.com>"
```

## Output Format
```
✓ staged: N files (+X/-Y lines)
✓ security: passed
✓ lint: passed/skipped
✓ commit: HASH type(scope): description
✓ co-author: Takumi <288571113+sun-takumi@users.noreply.github.com>
✓ pushed: yes/no
```

## Error Handling

| Error | Action |
|-------|--------|
| Secrets detected | Refuse the commit and name the offending files |
| Lint failed | Block commit/PR and summarize `/tkm:lint-code` findings |
| No changes | Bow out quietly |
| Push rejected | Steer the user toward `git pull --rebase` |
| Merge conflicts | Hand it back for manual resolution |

## References

- `references/workflow-commit.md` - committing, and how to decide on splitting
- `references/workflow-push.md` - pushing, with the errors you will hit
- `references/workflow-pr.md` - opening a PR off the remote diff
- `references/workflow-merge.md` - folding one branch into another
- `../lint-code/SKILL.md` - SunLint gate used by `lint` and `--lint`
- `references/commit-standards.md` - the conventional-commit grammar
- `references/safety-protocols.md` - catching secrets, guarding branches
- `references/branch-management.md` - naming, lifecycle, and strategies
- `references/gh-cli-guide.md` - the gh command reference
