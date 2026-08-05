# GitHub CLI Guide

## Authentication
```bash
gh auth login        # sign in, step by step
gh auth status       # see where auth stands
gh auth logout       # sign out
```

## Pull Requests

### Create PR
```bash
# Basic
gh pr create --base main --head feature-branch --title "feat: add login" --body "Summary"

# body via HEREDOC
gh pr create --base main --title "feat(auth): add OAuth" --body "$(cat <<'EOF'
## Summary
- Wired in the OAuth2 provider
- Token refresh now handled

## Test plan
- [ ] Unit suite green
- [ ] Logged in by hand
EOF
)"

# Draft mode
gh pr create --draft --title "WIP: new feature"

# Assign reviewers
gh pr create --reviewer @user1,@user2

# Add labels
gh pr create --label "bug,priority:high"
```

### View/Review PR
```bash
gh pr list                    # every open PR
gh pr view 123                # look at one PR
gh pr view 123 --web          # the same, in a browser
gh pr checkout 123            # pull a PR down to work on
gh pr diff 123                # what the PR changes
gh pr status                  # your PRs and review requests
```

### Merge PR
```bash
gh pr merge 123               # a plain merge commit
gh pr merge 123 --squash      # fold every commit into one
gh pr merge 123 --rebase      # replay commits onto the base
gh pr merge 123 --auto        # let it merge once checks go green
gh pr merge 123 --delete-branch  # tidy up the branch afterward
```

### PR Comments
```bash
gh pr comment 123 --body "LGTM!"
gh api repos/{owner}/{repo}/pulls/123/comments  # read them all
```

## Issues

```bash
gh issue list                 # every issue
gh issue view 42              # look at one issue
gh issue create --title "Bug" --body "Description"
gh issue develop 42 -c        # spin a branch off an issue
```

## Repository

```bash
gh repo view                  # details on this repo
gh repo clone owner/repo      # clone it
gh browse                     # open the repo in a browser
gh browse path/to/file:42     # jump straight to a file and line
```

## Workflow Runs

```bash
gh run list                   # recent workflow runs
gh run view <run-id>          # details on one run
gh run watch                  # follow a run as it goes
gh run rerun <run-id>         # send a failed run through again
```

## JSON Output (scripting)

```bash
gh pr list --json number,title,author
gh pr view 123 --json commits,reviews
gh issue list --json number,title --jq '.[].title'
```

## Common Patterns

### Create PR with auto-merge
```bash
gh pr create --fill && gh pr merge --auto --squash
```

### Close stale PRs
```bash
gh pr list --state open --json number -q '.[].number' | xargs -I {} gh pr close {}
```
