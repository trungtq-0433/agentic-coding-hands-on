# Git Safety Protocols

## Secret Detection Patterns

### Scan Command
```bash
git diff --cached | grep -iE "(AKIA|api[_-]?key|token|password|secret|credential|private[_-]?key|mongodb://|postgres://|mysql://|redis://|-----BEGIN)"
```

### Patterns to Detect

| Category | Pattern | Example |
|----------|---------|---------|
| API keys | `api[_-]?key`, `apiKey` | `API_KEY=abc123` |
| AWS | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| Tokens | `token`, `auth_token`, `jwt` | `AUTH_TOKEN=xyz` |
| Passwords | `password`, `passwd`, `pwd` | `DB_PASSWORD=secret` |
| Private keys | `-----BEGIN PRIVATE KEY-----` | a `.pem` file |
| DB URLs | `mongodb://`, `postgres://`, `mysql://` | a connection string |
| OAuth | `client_secret`, `oauth_token` | `CLIENT_SECRET=abc` |

### Files to Warn About
- `.env`, `.env.*` (but `.env.example` is fine)
- `*.key`, `*.pem`, `*.p12`
- `credentials.json`, `secrets.json`
- `config/private.*`

### Action on Detection
1. **Stop the commit on the spot**
2. Pull up the lines that matched: `git diff --cached | grep -B2 -A2 <pattern>`
3. Point the way out: gitignore it, or move it into an environment variable
4. Offer to back it out: `git reset HEAD <file>`

## Branch Protection

### Never Force Push To
- `main`, `master`, `production`, `prod`, `release/*`

### Pre-Merge Checks
```bash
# Check for conflicts before merge
git merge --no-commit --no-ff origin/{branch} && git merge --abort
```

### Remote-First Operations
Lean on `origin/{branch}` whenever you compare:
- ✅ `git diff origin/main...origin/feature`
- ❌ `git diff main...HEAD` — this drags in whatever you have not committed

## Error Recovery

### Undo Last Commit (unpushed)
```bash
git reset --soft HEAD~1  # leave the work staged
git reset HEAD~1         # leave the work unstaged
```

### Abort Merge
```bash
git merge --abort
```

### Discard Local Changes
```bash
git checkout -- <file>   # just the one file
git reset --hard HEAD    # everything, no undo (DANGER)
```

**Anything that destroys work waits for the user's go-ahead.**
