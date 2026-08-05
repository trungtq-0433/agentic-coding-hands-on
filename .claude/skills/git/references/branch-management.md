# Branch Management

## Naming Convention

**Format:** `<type>/<descriptive-name>`

| Type | Purpose | Example |
|------|---------|---------|
| `feature/` | Something new | `feature/oauth-login` |
| `fix/` | Squashing a bug | `fix/db-timeout` |
| `refactor/` | Reshaping code | `refactor/api-cleanup` |
| `docs/` | Writing docs | `docs/api-reference` |
| `test/` | Shoring up tests | `test/integration-suite` |
| `chore/` | Housekeeping | `chore/deps-update` |
| `hotfix/` | Urgent prod repair | `hotfix/payment-crash` |

## Branch Lifecycle

### Create
```bash
git checkout main
git pull origin main
git checkout -b feature/new-feature
```

### During Development
```bash
# commit as you go
git add <files> && git commit -m "feat(scope): description"

# keep pace with main
git fetch origin
git rebase origin/main
```

### Before Merge
```bash
# send the final state up
git push origin feature/new-feature

# or, after a rebase — feature branches only
git push -f origin feature/new-feature
```

### After Merge
```bash
# clear the local copy
git branch -d feature/new-feature

# clear it on the remote
git push origin --delete feature/new-feature
```

## Branch Strategies

### Simple (small teams)
```
main (production)
  └─ feature/* (work in progress)
```

### Git Flow (releases)
```
main (production)
develop (staging)
  ├─ feature/*
  ├─ bugfix/*
  ├─ hotfix/*
  └─ release/*
```

### Trunk-Based (CI/CD)
```
main (ship-ready at all times)
  └─ short-lived feature branches
```

## Quick Commands

| Task | Command |
|------|---------|
| See every branch | `git branch -a` |
| Which branch am I on | `git rev-parse --abbrev-ref HEAD` |
| Move to a branch | `git checkout <branch>` |
| Make one and move to it | `git checkout -b <branch>` |
| Drop it locally | `git branch -d <branch>` |
| Drop it on the remote | `git push origin --delete <branch>` |
| Give it a new name | `git branch -m <old> <new>` |
