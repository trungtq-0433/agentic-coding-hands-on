# Takumi Workflow Patterns

> Standard multi-skill chains. Each pattern shows the optimal sequence for a task type.
> Skills in brackets are optional/conditional.

---

## Core Feature Development

**When:** "implement feature X", "build Y", "add Z to my app", "develop new functionality"

```
/tkm:scan-codebase → /tkm:create-plan → /tkm:takumi → /tkm:run-tests → /tkm:review-code → /tkm:ship → /tkm:write-journal
```

**Shortcut (fast mode):**
```
/tkm:takumi --fast  (handles scan + plan + implement + test internally)
```

**With architecture exploration first:**
```
/tkm:brainstorm → /tkm:research → /tkm:create-plan → /tkm:takumi → /tkm:run-tests → /tkm:ship
```

---

## Bug Fix

**When:** "bug", "broken", "error", "not working", "failing test", "exception"

**Quick fix (known bug):**
```
/tkm:fix-bug → /tkm:run-tests → /tkm:git
```

**Deep investigation (unknown root cause):**
```
/tkm:scan-codebase → /tkm:debug-code → /tkm:fix-bug → /tkm:run-tests → /tkm:review-code
```

**CI/CD failing:**
```
/tkm:fix-bug --auto  (autonomous mode, no human gates)
```

---

## Design — Replicate Existing Asset

**When:** Have mockup / screenshot / Figma / video / existing HTML, want to code it

```
/tkm:design-to-code → /tkm:review-code → /tkm:git
```

**With UX improvements:**
```
/tkm:design-ui  [design decisions first]
→ /tkm:design-to-code  [then implement]
→ /tkm:review-code → /tkm:git
```

---

## Design — From Scratch

**When:** No existing asset, need to decide what it should look like first

```
/tkm:design-ui → /tkm:design-to-code → /tkm:review-code → /tkm:git
```

---

## New Project Bootstrap

**When:** "start new project", "create app from scratch", "scaffold"

```
/tkm:brainstorm → /tkm:research → /tkm:bootstrap → /tkm:create-plan → /tkm:takumi
```

---

## Planning Only (No Implementation Yet)

**When:** "plan this before we start", "I want a blueprint", "design the architecture"

```
/tkm:research → /tkm:brainstorm → /tkm:create-plan
```

Then hand off: `/tkm:takumi plans/xxx/plan.md`

---

## Security Audit

**When:** "check for vulnerabilities", "security review", "OWASP audit", before major release

```
/tkm:scan-codebase → /tkm:audit-security → /tkm:fix-bug → /tkm:run-tests → /tkm:review-code
```

**With auto-fix:**
```
/tkm:audit-security --fix --iterations 3
```

---

## Static Quality And License Gates

**When:** "lint code", "SunLint", "static analysis", "license compliance", "audit licenses"

```
/tkm:lint-code → /tkm:audit-licenses → /tkm:run-tests → /tkm:review-code
```

**Before committing with git:**
```
/tkm:git cp --lint
```

---

## Code Review Before Merge

**When:** "review my PR", "check before merging", "code quality check"

```
/tkm:review-code
```

**With risk assessment:**
```
/tkm:predict-risks → /tkm:review-code
```

---

## Deploy to Production

**When:** Feature complete, ready to go live

```
/tkm:run-tests → /tkm:ship → /tkm:deploy-app
```

**Ship only (no separate deploy):**
```
/tkm:ship  (handles test + review + commit + push + PR)
```

---

## End of Session

**When:** Work session complete, want to record and wrap up

```
/tkm:write-journal
```

---

## Research & Decision

**When:** "which technology should I use", "evaluate options", "compare X vs Y"

```
/tkm:research → /tkm:brainstorm
```

Then: `/tkm:create-plan` if decision made

---

## Understand Existing Codebase

**When:** New to the codebase, before a major change, "what does this code do"

```
/tkm:scan-codebase → /tkm:rebuild-spec
```

**Quick orientation:**
```
/tkm:scan-codebase
```

---

## Infrastructure Setup

**When:** Need Docker, K8s, CI/CD, Cloudflare, AWS Terraform

**Cloud/containers:**
```
/tkm:create-plan → /tkm:devops → /tkm:run-tests → /tkm:ship
```

**AWS Terraform:**
```
/tkm:research → /tkm:infra → /tkm:review-code
```

---

## Parallel Feature Development (Team)

**When:** Large feature with independent components, or multiple features in parallel

```
/tkm:create-worktree  [for each developer/feature]
→ /tkm:run-tests → /tkm:review-code → /tkm:ship
```

---

## Document Translation

**When:** "translate this document/spreadsheet/book", "dịch file này", "localize this manual", "翻訳"

**Standalone (most common):**
```
/tkm:translate-file <file-path> --target <lang>
```

**Reverse-engineer foreign-language docs, then translate:**
```
/tkm:document-skills  [extract text from the file]
→ /tkm:translate-file <file-path> --target <lang>
```

---

## Decision Tree: Which Pattern?

```
Task involves...
├── Has visual asset (mockup, screenshot, Figma)?    → Design — Replicate
├── No asset, needs UI design decisions?             → Design — From Scratch
├── Something broken / failing?                      → Bug Fix
├── New feature to implement?                        → Core Feature Development
├── New project from zero?                           → New Project Bootstrap
├── Just need a plan, not code yet?                  → Planning Only
├── Security concerns?                               → Security Audit
├── Translate a document / spreadsheet / book?       → Document Translation
├── Ready to merge/ship?                             → Deploy to Production
├── End of day / session done?                       → End of Session
└── Unsure what to build?                           → Research & Decision
```
