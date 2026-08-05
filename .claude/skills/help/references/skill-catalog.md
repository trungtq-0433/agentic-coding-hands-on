# Takumi Skill Catalog

> Complete catalog of all takumi-kit skills organized by domain.
> **Maintainers:** Update this file whenever a skill is added, renamed, or removed.

> **Processing level (`--level`):** these depth-sensitive skills accept `--level low|medium|high|max` to control how hard they work (depth, parallel agents, validation passes) — `research`, `scan-codebase`, `brainstorm`, `review-code`, `audit-security`, `debug-code`, `predict-risks`, `propose-improvements`. Default is `medium`. For `propose-improvements`, `--level high|max` enables the source-code security audit (step 4.1.09).

---

## Design & Frontend

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:design-to-code` | Replicate an existing design (mockup, screenshot, Figma, video, HTML) into polished frontend code with full aesthetic fidelity | "redesign this", "make it look like", "replicate UI", "from screenshot", "from Figma", "pixel-perfect", "convert design to code", "thiết kế lại" |
| `/tkm:design-ui` | Make UI/UX design DECISIONS — choose color palette, typography, style system, UX patterns for a new or existing interface | "design from scratch", "choose colors", "pick fonts", "design system", "what style should", "UX guidelines", "create UI from idea" |
| `/tkm:build-frontend` | Build React/TypeScript frontend components and pages with modern patterns (Suspense, TanStack, MUI v7, lazy loading) | "React component", "TypeScript frontend", "TanStack Router", "MUI", "useSuspenseQuery", "lazy loading" |

**Don't confuse:**
- `design-to-code` = TRANSLATE existing visual → code (input: asset)
- `design-ui` = DECIDE what the design should look like (input: requirements)
- `build-frontend` = BUILD components with React/TS patterns (input: specs)

---

## Implementation

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:takumi` | End-to-end feature implementation: research → plan → implement → test → review → commit. The full craftsman pipeline. | "implement", "build feature", "add X to app", "develop", "create functionality", "end-to-end" |
| `/tkm:create-plan` | Create a detailed implementation plan (blueprint) BEFORE writing code | "plan this", "create a plan", "design architecture", "blueprint", "before implementing", "plan only" |
| `/tkm:brainstorm` | Role-aware trade-off analysis BEFORE committing — surfaces alternatives, quantifies risks from a chosen advisor lens (default CTO; `--role ceo\|cto\|cfo\|coo\|cmo\|cpo`, or `--bod` for a C-level board). Technical AND non-technical decisions. | "should I use X or Y", "trade-offs", "architecture decision", "which approach", "help me think through", "before deciding", "CEO/CFO perspective", "board feedback", "course outline ideas", "marketing angle" |
| `/tkm:bootstrap` | Start a new project from scratch: research stack, scaffold structure, set up foundations | "new project", "start from scratch", "scaffold", "init project", "create new app" |
| `/tkm:research` | Multi-source technical research with ranked recommendations | "research", "evaluate", "compare libraries", "best practice for", "what technology", "investigate options" |

---

## Bug Fixing & Debugging

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:fix-bug` | Fix ANY bug, error, test failure, CI/CD issue, type error, lint error | "bug", "error", "broken", "not working", "failing", "crash", "exception", "CI failing", "fix this" |
| `/tkm:debug-code` | Root cause investigation — trace symptoms to source before touching code | "investigate", "why is X happening", "root cause", "strange behavior", "unexpected", "trace", "diagnose" |
| `/tkm:audit-security` | STRIDE + OWASP security scan with optional auto-fix | "security", "vulnerabilities", "OWASP", "harden", "security audit", "scan for exploits" |

---

## Backend & Database

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:build-backend` | Build Node.js/Python/Go APIs (NestJS, FastAPI, Django) — REST, GraphQL, gRPC, auth, microservices | "API", "backend", "REST endpoint", "GraphQL", "NestJS", "FastAPI", "Django", "auth backend", "microservice" |

---

## Testing & Code Quality

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:run-tests` | Run unit/integration/e2e/UI tests, check coverage, verify build | "run tests", "test coverage", "unit test", "e2e", "visual regression", "does it pass" |
| `/tkm:lint-code` | Run SunLint static analysis for code quality, security, architecture, staged/changed files, and CI-ready reports | "lint code", "sunlint", "code quality", "static analysis", "security lint", "architecture lint" |
| `/tkm:audit-licenses` | Audit dependency license compatibility with licenseal and manage policy allow/deny lists for licenses, packages, or risks | "license audit", "audit licenses", "licenseal", "dependency licenses", "license compliance", "license policy", "blacklist license", "whitelist license", "blacklist package", "whitelist package", "blacklist risk", "whitelist risk" |
| `/tkm:review-code` | Adversarial code review — security holes, false assumptions, failure modes | "review code", "code review", "check my PR", "before merging", "is this safe" |
| `/tkm:audit-doc-parity` | Verify generated docs actually MATCH the code — blind reverse-regeneration + field-diff (DRIFT/FABRICATED/MISSING) | "doc parity", "docs match code", "audit docs vs code", "are the specs accurate", "documentation drift" |
| `/tkm:audit-synthesis-judgment` | Audit the JUDGMENT in rebuild-spec synthesis — partition/user-story/inference soundness (3 engines: deterministic coverage FAIL + IPE-conformance WARN + adversarial judgment WARN) | "audit synthesis judgment", "is the partition right", "over-merge", "under-merge", "user stories sound", "is the design intent sound", "judgment soundness" |
| `/tkm:clean-code` | Simplify code for clarity without changing behaviour — extract, rename, flatten, dedupe | "clean up code", "simplify", "refactor for clarity", "reduce complexity", "tidy this" |
| `/tkm:predict-risks` | 5 expert personas debate risks in a proposed change BEFORE implementing | "risks", "what could go wrong", "before major change", "predict failure", "expert review of plan" |
| `/tkm:auto-research` | Autonomous iterative optimization loop against a measurable metric | "improve coverage", "optimize bundle", "iterative improvement", "auto-optimize", "N iterations" |

---

## Deployment & Infrastructure

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:deploy-app` | Deploy to any platform — Vercel, Netlify, Cloudflare, Railway, Fly.io, AWS, GCP | "deploy", "publish", "go live", "push to production", "host this app", platform names |
| `/tkm:ship` | Full ship pipeline: merge main + tests + review + commit + push + open PR | "ship", "merge feature", "open PR", "feature is done", "ready to merge" |
| `/tkm:devops` | Docker, Kubernetes, Cloudflare Workers/R2/D1, GCP Cloud Run, CI/CD pipelines, Helm | "Docker", "Kubernetes", "CI/CD pipeline", "GitOps", "Helm", "Cloudflare Workers" |
| `/tkm:infra` | AWS infrastructure as Terraform code — modules, cost review, IaC | "Terraform", "AWS", "infrastructure as code", "IaC", "EC2", "RDS", "cost estimate" |

---

## Planning & Architecture

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:create-plan` | Detailed implementation plan with phases (see Implementation section) | — |
| `/tkm:brainstorm` | Architecture decisions, trade-off analysis (see Implementation section) | — |
| `/tkm:research` | Technical research before deciding (see Implementation section) | — |
| `/tkm:think-sequential` | Step-by-step analysis with revision capability for complex multi-step problems | "think through step by step", "complex problem", "analyze carefully", "reason through" |
| `/tkm:migrate-aidd` | Migrate GitHub Spec-Kit/SDD projects into Takumi's canonical spec set (reads old specs first, code only to fill gaps) | "migrate spec-kit", "SDD migration", "AIDD", "import specs", "spec-driven", "migrate to takumi" |

---

## Documentation & Knowledge

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:manage-docs` | Update and manage project documentation in `./docs` | "update docs", "document this", "README", "codebase summary", "sync docs" |
| `/tkm:write-journal` | End-of-session journal entry — decisions, lessons, what was built | "journal", "write up session", "wrap up", "document what we did", "session notes" |
| `/tkm:rebuild-spec` | Reverse-engineer codebase → 11 core doc artifacts + per-feature specs + process-flows (architecture, API specs, flows) | "document existing codebase", "reverse engineer", "spec from code", "what does this code do" |
| `/tkm:search-docs` | Search library/framework docs via context7 | "docs for X", "API reference", "how does X work in library Y", "latest docs" |
| `/tkm:generate-llms-txt` | Generate llms.txt / llms-full.txt (llmstxt.org standard) for a project — an agent loads one file and understands the product; docs-first with a fallback ladder | "generate llms.txt", "llm.txt", "llms.txt", "agent-first doc", "file for agents" |
| `/tkm:markdown-novel-viewer` | Serve markdown files in a book-like browser reader over HTTP — for plans, specs, journals, long-form docs | "read in browser", "open plan nicely", "novel viewer", "render markdown", "reading view" |

---

## Git & Version Control

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:git` | Stage, commit, push, optional lint-code gate, and PR flow with conventional commits; secrets scan before commit | "commit", "push", "stage changes", "git", "commit message" |
| `/tkm:ship` | Full ship pipeline (see Deployment) | — |
| `/tkm:create-worktree` | Create isolated git worktrees for parallel feature development | "worktree", "isolated branch", "work in parallel", "don't touch main branch", "separate workspace" |

---

## Project & Context Management

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:scan-codebase` | Parallel codebase scouting — file discovery, pattern search | "find files", "where is X", "what files do I need", "scan code", "map the codebase" |
| `/tkm:manage-project` | Track plan statuses, manage Tasks, generate reports, cross-session continuity | "project status", "what's done", "update plan", "track progress", "task management" |
| `/tkm:confidence` | Confidence taxonomy for agent outputs — tag findings EXTRACTED/INFERRED/AMBIGUOUS with scores (reference convention other skills import) | "confidence level", "EXTRACTED", "INFERRED", "AMBIGUOUS", "evidence taxonomy", "how sure" |
| `/tkm:optimize-context` | Optimize context window — monitor usage, prevent token waste | "context full", "token limit", "optimize context", "memory management" |
| `/tkm:organize-files` | Organize files and directories — naming, structure, output paths | "organize files", "where to put this", "naming convention", "file structure" |

---

## AI & Collaboration

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:ask-expert` | Expert technical and architectural consultation | "expert opinion", "best practice advice", "architectural guidance", "ask an expert" |

---

## Automation & Browser

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:automate-browser` | Puppeteer CLI — screenshots, scraping, performance, form automation | "screenshot", "scrape", "automate browser", "Puppeteer", "web automation", "performance test" |

---

## Specialized Output

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:generate-slide` | Polished presentation slides (HTML scroll-snap or Sun* branded PPTX) | "slides", "presentation", "deck", "tạo slide", "gen deck", "PPTX" |
| `/tkm:artifact` | Upload an HTML/MD file or folder to Takumi Artifacts for a shareable URL | "artifact", "tạo artifact", "share HTML", "publish artifact", "upload artifact", "shareable link" |
| `/tkm:preview-output` | Visual explanations, diagrams, slides in browser as self-contained HTML | "show me", "preview", "explain visually", "make a diagram", "render this" |
| `/tkm:pack-codebase` | Repomix codebase snapshot for LLM context or security audit | "pack codebase", "repomix", "LLM context", "codebase snapshot" |
| `/tkm:document-skills` | Work with Word/PDF/PowerPoint/Excel files | "Word doc", "PDF", "PowerPoint", "Excel", "office document" |
| `/tkm:translate-file` | Translate a file (PDF/DOCX/XLSX/EPUB) into any language via a parallel convert→chunk→glossary→translate→merge pipeline | "translate this document", "dịch file", "translate PDF/Word/Excel", "translate book", "翻訳", "dịch tài liệu" |
| `/tkm:audio-transcribe` | Transcribe audio/video to SRT with domain-aware correction | "transcribe", "subtitles", "SRT", "audio to text", "video captions" |
| `/tkm:solve-problem` | Systematic problem-solving when stuck on a recurring issue | "stuck", "can't figure out", "recurring problem", "break the pattern" |
| `/tkm:kensan` | Learning briefing from trusted watchlists that auto deep-dives the hottest topic: reads papers/repos, mines HN/GitHub/Reddit/X discussion (consensus vs debate), explains how-it-works + what-to-try; de-dupes across days | "news briefing", "learning digest", "deep dive", "technical analysis", "what are people saying about", "update my watchlist", "what's new in", "stay current" |

---

## MCP & External Tools

| Skill | Use for | Key triggers |
|-------|---------|-------------|

---

## Configuration & Level

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:set-level` | Set output detail level from ELI5 (0) to expert (5) | "explain simply", "set level", "junior mode", "expert mode", "ELI5" |
| `/tkm:kaizen` | Improve, compare, or extend an installed Takumi skill — improvements delivered as update-safe extension files, never by editing shipped SKILL.md | "improve skill", "tune skill", "skill is weak", "compare skill", "extend skill", "customize skill", "kaizen" |
| `/tkm:help` | Navigate the kit — find the right skill/workflow when unsure which to use or how to do X | "help", "list skills", "what skills", "skill catalog", "which skill", "capabilities" |

**Don't confuse:**
- `kaizen` = improve/extend an INSTALLED skill (writes `extensions/`, survives `tkm update`)
- Editing `SKILL.md` directly = ❌ causes conflicts on the next kit update

---

## Takumi-Specific (Project/Client Tools)

| Skill | Use for | Key triggers |
|-------|---------|-------------|
| `/tkm:estimate` | Effort estimation from spec docs (PDF/Excel/Word/URL/image) or Clio KG — 5 modes: quick, full, clio, import, calibrate | "estimate", "man-days", "WBS", "effort estimate", "function count", "dự toán", "見積もり", "spec document", "bidding" |
| &nbsp;&nbsp;└ `discovery` | Pre-estimation Q&A from spec directory | "pre-estimate", "discovery Q&A", "spec analysis questions", "before estimating" |
| &nbsp;&nbsp;└ `task-breakdown` | WBS breakdown from feature/function list | "WBS", "task breakdown", "breakdown per feature", "effort per task" |
| `/tkm:generate-ui-specs` | Per-component UI specs from MoMorph/screenshot | "UI specs", "component spec", "MoMorph spec" |
| `/tkm:propose-improvements` | Customer-ready improvement proposal for repository | "improvement proposal", "client proposal" |

> The following skills moved to the `extras` kit. Install with `tkm init --kit extras`:
> - `/tkm:generate-testcases` — QA testcases from MoMorph screen or spec
> - `/tkm:momorph-implement-design` — Pixel-perfect code from MoMorph/Figma screen
> - `/tkm:clio-artifact` — Generate SVN Proposal PPTX from Clio Knowledge Graph
