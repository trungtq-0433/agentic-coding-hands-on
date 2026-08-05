# Takumi Quick Reference

> One-page cheat sheet. Memorize the "By Task" table and the workflow chains.

---

## By Task

| I want to... | Primary skill | Shortcut / notes |
|--------------|--------------|-----------------|
| Implement a feature (full pipeline) | `/tkm:takumi` | Handles plan + code + test internally |
| Implement fast, skip deep research | `/tkm:takumi --fast` | — |
| Create a plan only (no code) | `/tkm:create-plan` | Then hand off: `takumi plan.md` |
| Explore options / get an advisor perspective | `/tkm:brainstorm` | Before deciding, not after. Default CTO; `--role ceo\|cfo\|coo\|cmo\|cpo` or `--bod` for a board |
| Research technology options | `/tkm:research` | Produces ranked recommendations |
| Start a new project from scratch | `/tkm:bootstrap` | After: `create-plan` → `takumi` |
| **Redesign HTML from screenshot/Figma** | `/tkm:design-to-code` | ⚠️ NOT brainstorm |
| Design UI from scratch (no asset) | `/tkm:design-ui` | Then: `design-to-code` |
| Build React/TS components | `/tkm:build-frontend` | — |
| Build Next.js app | `/tkm:build-frontend` | React/TS, incl. Next.js |
| Fix a bug / error | `/tkm:fix-bug` | Works for CI/CD too |
| Investigate root cause | `/tkm:debug-code` | Before `fix-bug` when unknown |
| Security audit | `/tkm:audit-security` | Add `--fix` for auto-repair |
| Run static lint / SunLint | `/tkm:lint-code` | Changed-aware by default; use `staged`, `full`, `security`, `architecture` |
| Audit dependency licenses | `/tkm:audit-licenses` | licenseal report + `licenseal.policy.toml` allow/deny policy |
| Build a backend API | `/tkm:build-backend` | REST, GraphQL, gRPC |
| Run tests | `/tkm:run-tests` | Coverage + build verification |
| Review code quality | `/tkm:review-code` | Before merging |
| Predict risks before a change | `/tkm:predict-risks` | 5 expert personas |
| Deploy to Vercel / Netlify / etc. | `/tkm:deploy-app` | Auto-detects platform |
| Ship feature branch (test + PR) | `/tkm:ship` | One command to PR URL |
| Set up Docker / CI/CD / K8s | `/tkm:devops` | — |
| AWS Terraform infrastructure | `/tkm:infra` | Mermaid-to-Terraform supported |
| **Estimate project effort from spec/doc** | `/tkm:estimate` | PDF/Excel/Word/URL/image → WBS + man-days |
| Estimate from Clio KG (Sun* internal) | `/tkm:estimate` | Auto-detects clio mode via `.estimate.yml` |
| Pre-estimation discovery Q&A | `/tkm:estimate discovery` | Clarifying questions before full estimate |
| WBS task breakdown | `/tkm:estimate task-breakdown` | Function list → per-task effort |
| Import historical estimate data | `/tkm:estimate import` | Build knowledge base from past projects |
| Calibrate estimation knowledge base | `/tkm:estimate calibrate` | Tune multipliers from historical data |
| Commit changes | `/tkm:git` | Conventional commits + secrets scan; add `--lint` to run `/tkm:lint-code` first |
| Create isolated worktree | `/tkm:create-worktree` | For parallel feature work |
| Understand the codebase | `/tkm:scan-codebase` | Parallel agents |
| Update documentation | `/tkm:manage-docs` | Syncs `./docs` |
| End-of-session journal | `/tkm:write-journal` | End of session |
| Search library docs | `/tkm:search-docs` | Via context7 |
| Create slides | `/tkm:generate-slide` | HTML or PPTX |
| Translate a document / spreadsheet / book | `/tkm:translate-file` | PDF/DOCX/XLSX/EPUB → any language |
| Read markdown in a browser reader | `/tkm:markdown-novel-viewer` | Book-like view for plans/specs/docs |
| Visual explanation / diagram | `/tkm:preview-output` | Self-contained HTML |
| Automate browser / Puppeteer | `/tkm:automate-browser` | Screenshots, scraping |
| Set explanation level | `/tkm:set-level` | 0=ELI5, 5=expert |
| Ask an expert | `/tkm:ask-expert` | Architectural consultation |
| Improve / extend an installed skill | `/tkm:kaizen` | Update-safe extensions, never edits SKILL.md |
| Compare two skill implementations | `/tkm:kaizen <skill> --compare <path>` | Report only, no changes |

---

## Processing Level (`--level`)

Depth-sensitive skills accept `--level low|medium|high|max` (default `medium`) to control effort, parallel agents, and validation passes:
`research`, `scan-codebase`, `brainstorm`, `review-code`, `audit-security`, `debug-code`, `predict-risks`, `propose-improvements`.
For `propose-improvements`, `--level high|max` enables the source-code security audit (step 4.1.09).

---

## Standard Workflow Chains

**Full Feature:**
```
scan-codebase → create-plan → takumi → run-tests → review-code → ship → write-journal
```

**Quick Feature (fast mode):**
```
takumi --fast → run-tests → git
```

**Bug Fix:**
```
fix-bug → run-tests → git
```

**Quality Gate:**
```
lint-code → audit-licenses → run-tests → review-code
```

**Deep Debug:**
```
scan-codebase → debug-code → fix-bug → run-tests → review-code
```

**Redesign from Asset:**
```
design-to-code → review-code → git
```

**Design from Scratch:**
```
design-ui → design-to-code → review-code → git
```

**New Project:**
```
brainstorm → research → bootstrap → create-plan → takumi
```

**Plan Then Implement:**
```
research → brainstorm → create-plan → takumi plans/xxx/plan.md
```

**Security Hardening:**
```
scan-codebase → audit-security --fix → run-tests → review-code
```

**Ship Feature:**
```
run-tests → ship → deploy-app
```

**Session Wrap-Up:**
```
write-journal
```

---

## Common Mistakes (Quick Version)

| ❌ Wrong | ✅ Right | Reason |
|---------|---------|--------|
| `brainstorm` to redesign HTML | `design-to-code` | brainstorm = decisions, not work |
| `create-plan` to implement | `takumi` | create-plan = blueprint only |
| `design-ui` to replicate Figma | `design-to-code` | design-ui = design choices, not replication |
| `research` to build something | `takumi` | research = evaluate options, not build |
| `scan-codebase` to fix a bug | `fix-bug` | fix-bug scans internally |
| `find-skill` to route in kit | `help` | find-skill = external registry |
| Edit a shipped SKILL.md to customize | `kaizen` | direct edits conflict with kit updates |

---

## `/tkm:help` Modes

```
/tkm:help "describe my task"   → Recommend the right skill + workflow
/tkm:help --list               → Full skill catalog by domain
/tkm:help --workflow           → All workflow chains
/tkm:help brainstorm           → Deep explanation of a specific skill
/tkm:help                      → Interactive — ask what you're trying to do
```
