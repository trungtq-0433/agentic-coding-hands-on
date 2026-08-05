---
name: tkm:audit-security
description: "Harden the work against attackers — STRIDE + OWASP security audit with optional auto-fix. Scans code for vulnerabilities, categorizes by severity, and iteratively fixes findings."
argument-hint: "<scope|full> [--fix] [--level low|medium|high|max]"
metadata:
  author: takumi-agent-kit
  attribution: "Security audit pattern adapted from autoresearch by Udit Goenka (MIT)"
  license: MIT
  version: "1.0.0"
module: bug-fixing-debugging
triggers: ["security", "vulnerabilities", "OWASP", "harden", "security audit", "scan for exploits"]
---

# Testing Every Joint

A craftsman who finishes a piece without stress-testing every joint has not finished the piece.
The joint that holds under light load will snap under real use. The surface that looks sealed will leak under pressure.
This skill presses every joint: STRIDE threat modeling against every entry point, OWASP patterns against every data boundary, severity-ranked so the worst cracks are fixed first.

With `--fix`: applies repairs iteratively using the `tkm:auto-research` guard pattern.

## When to Apply

Reach for an audit when the stakes change, not on a fixed calendar:

- A release or sizeable deployment is about to leave your hands
- You just wired in auth, payments, or anything that touches user data
- A recurring sweep falls due (monthly or quarterly)
- A compliance milestone looms — SOC 2, GDPR, PCI-DSS groundwork

## When NOT to Use

Skip it when there is nothing for an attacker to reach:

- Surface-level edits — styling, copy, layout tweaks
- Code paths that neither face a user nor handle data

---

## Modes

| Mode | Invocation | Behavior |
|------|-----------|----------|
| Audit only | `/tkm:audit-security <scope>` | Scan → categorize → report |
| Audit + Fix | `/tkm:audit-security <scope> --fix` | Scan → categorize → fix iteratively |
| Bounded fix | `/tkm:audit-security <scope> --fix --iterations N` | Limit fix iterations to N |

---

## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | STRIDE | OWASP | Deps | Secrets | Static tools | Auto-fix |
|-------|--------|-------|------|---------|-------------|---------|
| `low` | AI only | Yes | No | No | No | No |
| `medium` *(default)* | Full | Yes | Yes | Yes | No | No |
| `high` | Full | Yes | Yes | Yes | Yes | No |
| `max` | Full | Yes | Yes | Yes | Yes | Implied |

> `--level max` implies `--fix`. Explicit `--fix` overrides regardless of level.
> `--level low` is suitable for quick pre-commit spot checks, not production audits.

## Audit Methodology

### 1. Scope Resolution
Turn the glob — or the `full` keyword — into a concrete list of files, then read every one of them before reasoning about a single weakness.

### 2. STRIDE Analysis
Walk each threat category in turn, asking where this codebase gives ground:
- **S**poofing — identity/authentication weaknesses
- **T**ampering — input validation, integrity controls
- **R**epudiation — audit logging gaps
- **I**nformation Disclosure — data leakage, secret exposure
- **D**enial of Service — rate limits, resource exhaustion
- **E**levation of Privilege — broken access control, RBAC gaps

### 3. OWASP Top 10 Check
Pin each finding to an OWASP category (A01–A10). The per-category checks live in `references/stride-owasp-checklist.md`.

### 4. Dependency Audit
Pick the audit tool that matches the stack you detected and run it:
- Node.js: `npm audit`
- Python: `pip-audit`
- Go: `govulncheck`
- Ruby: `bundle audit`

If dependency manifests or lockfiles changed, also run `/tkm:audit-licenses` so license compatibility is checked before release. Watch for files such as `package.json`, lockfiles, `requirements*.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `mix.exs`, and `DESCRIPTION`.

### 4.1 Static Security Lint
At `--level high` or `--level max`, run:

```bash
/tkm:lint-code --security
```

Treat SunLint security errors as blocking security findings. Warning-only results should be included in the audit report unless project policy makes them blocking.

### 5. Secret Detection
Sweep the source for keys, passwords, tokens, and private keys left in plain sight, using the regex set in `references/stride-owasp-checklist.md` → Secret Patterns.

### 6. Finding Categorization
Stamp every finding with a severity (definitions are below).

---

## Output Format

```
## Security Audit Report

### Summary
- Files scanned: N
- Findings: X critical, Y high, Z medium, W low, V info

### Findings

| # | Severity | Category | File:Line | Description | Fix Recommendation |
|---|----------|----------|-----------|-------------|-------------------|
| 1 | Critical  | Injection | api/users.ts:45 | SQL string concatenation | Use parameterized queries |
| 2 | High      | Auth      | auth/login.ts:12 | No rate limiting | Add express-rate-limit |
```

---

## Fix Mode (--fix)

Pass `--fix` and the audit hands off into repair, one finding at a time:

1. Order the findings worst-first (Critical → High → Medium → Low)
2. For each finding:
   a. Make one surgical change — nothing wider than the finding
   b. Run the guard (tests or lint) and confirm nothing else broke
   c. Commit: `security(fix-N): <short description>`
   d. Move to the next finding
3. The moment the guard fails, stop and report it — do not push on
4. Regression safety comes from the `tkm:auto-research` guard pattern

> Tip: Use `--iterations N` to cap total fix iterations when scope is large.

---

## Severity Definitions

| Severity | Description | Fix Priority |
|----------|-------------|-------------|
| Critical | Exploitable now, data breach or RCE risk | Immediate — block release |
| High | Exploitable with moderate effort, significant impact | This sprint |
| Medium | Limited exploitability or impact | Next sprint |
| Low | Theoretical risk, defense-in-depth improvement | Backlog |
| Info | Best practice suggestion, no direct risk | Optional |

---

## Integration with Other Skills

- When the security persona in `tkm:predict-risks` raises a flag, follow it with this audit
- Hand Critical/High findings to `tkm:auto-research --fix` to drive remediation on their own
- Use `tkm:create-plan` to park Medium/Low findings as scheduled sprint work

---

## Example Invocations

```bash
# Audit API layer only
/tkm:audit-security src/api/**/*.ts

# Audit entire src/ and auto-fix, max 15 iterations
/tkm:audit-security src/ --fix --iterations 15

# Full codebase audit (no fix)
/tkm:audit-security full
```

---

See `references/stride-owasp-checklist.md` for the detailed per-category checklist and secret detection regex patterns.
