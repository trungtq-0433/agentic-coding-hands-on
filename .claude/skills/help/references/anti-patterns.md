# Anti-Patterns — Common Wrong Skill Choices

> The most frequent mistakes when picking a Takumi skill.
> Each entry: the wrong choice, the right choice, and WHY.

---

## ❌ Using `/tkm:brainstorm` for design or implementation tasks

**Wrong scenario:**
> "I want to redesign my HTML page" → `/tkm:brainstorm`
> "Tôi muốn thiết kế lại trang HTML của mình" → `/tkm:brainstorm`

**Right choice:** `/tkm:design-to-code` (have asset) or `/tkm:design-ui` (no asset)

**Why it's wrong:**
`brainstorm` is role-aware trade-off analysis (default CTO; `--role`/`--bod` for other lenses) — it debates *which approach* to take, not *does the work*.
It will not produce a redesigned page. It will produce a list of options and their trade-offs.

**Use `brainstorm` when:** "Should I use PostgreSQL or MongoDB?" (default CTO), "Is now the right time to launch? `--role ceo`", "What's the ROI on this? `--role cfo`", "Give me board-level feedback on this plan `--bod`", "Help me outline a course / a marketing angle".

---

## ❌ Using `/tkm:create-plan` to implement a feature

**Wrong scenario:**
> "Implement user authentication" → `/tkm:create-plan`

**Right choice:** `/tkm:takumi` (full pipeline) or `/tkm:create-plan` → then `/tkm:takumi plans/xxx/plan.md`

**Why it's wrong:**
`create-plan` produces a BLUEPRINT only — no code is written, nothing is built.
If the user wants code, they need `takumi`. If they want to plan first then implement explicitly, that's a two-step flow.

**Use `create-plan` when:** "I want a detailed plan before we touch any code", "Create a blueprint for the auth system"

---

## ❌ Using `/tkm:design-ui` to replicate an existing design

**Wrong scenario:**
> User shares a Figma screenshot and says "code this UI" → `/tkm:design-ui`

**Right choice:** `/tkm:design-to-code`

**Why it's wrong:**
`design-ui` is for making design DECISIONS (choosing colors, typography, style system, UX patterns).
It does not translate visuals into code.
`design-to-code` takes an existing visual asset and faithfully forges it into production code.

**Mental model:**
- Have visual, want code → `design-to-code`
- Have requirements, need design decisions → `design-ui` → then `design-to-code`

---

## ❌ Using `/tkm:research` to build something

**Wrong scenario:**
> "Build the payment integration" → `/tkm:research`

**Right choice:** `/tkm:takumi` (or `create-plan` → `takumi`)

**Why it's wrong:**
`research` evaluates options and produces a report with ranked recommendations.
It does not write code. It's the step BEFORE deciding what to build, not the build step.

**Use `research` when:** "What's the best payment library for our stack?", "Evaluate Stripe vs Polar vs SePay"

---

## ❌ Using `/tkm:scan-codebase` to fix a bug

**Wrong scenario:**
> "There's a bug in auth.ts" → `/tkm:scan-codebase`

**Right choice:** `/tkm:fix-bug` (which scans internally as needed)

**Why it's wrong:**
`scan-codebase` discovers file structure and patterns — it's reconnaissance, not repair.
`fix-bug` handles the full repair cycle including any scanning it needs.

**Use `scan-codebase` when:** Starting a new feature and need to understand the codebase before planning, or explicitly "show me the codebase structure"

---

## ❌ Using `/tkm:takumi` without a plan for large/complex features

**Wrong scenario:**
> `/tkm:takumi "Rebuild the entire authentication system from scratch"`

**Better approach:** `/tkm:brainstorm` → `/tkm:create-plan` → `/tkm:takumi plans/xxx/plan.md`

**Why it matters:**
`takumi` will create a plan internally, but for large features you lose visibility and review control.
Explicit planning gives you a blueprint to review and approve before the first line of code.

**Exception:** For small/medium features, `takumi` without a pre-made plan is fine — it handles planning internally.

---

---

## ❌ Editing a shipped SKILL.md directly to customize a skill

**Wrong scenario:**
> "Make `review-code` also check our team conventions" → open `.claude/skills/review-code/SKILL.md` and edit it

**Right choice:** `/tkm:kaizen review-code` — or hand-write an extension file in `.claude/skills/review-code/extensions/`

**Why it's wrong:**
Shipped skill files are tracked by checksum. Direct edits collide with the next `tkm update`:
your changes either block the upgrade with conflicts or get lost. Extensions live outside the
kit manifest, are classified user-owned, and survive every update untouched.

**Use direct edits when:** you are a kit maintainer working in the takumi-kit repo itself, not in an installed project.

---

## ❌ Using `/tkm:predict-risks` as a substitute for testing

**Wrong scenario:**
> Skip `run-tests` and only use `predict-risks` to "validate" an implementation

**Right choice:** `run-tests` after implementation, `predict-risks` before major changes

**Why it matters:**
`predict-risks` debates PROPOSED changes before implementation — it's forward-looking.
`run-tests` verifies ACTUAL code correctness after implementation.
They serve different phases and cannot substitute for each other.

---

## ❌ Using `/tkm:review-code` instead of `/tkm:audit-security` for security work

**Wrong scenario:**
> "Check my API endpoints for injection vulnerabilities" → `/tkm:review-code`

**Right choice:** `/tkm:audit-security`

**Why it's wrong:**
`review-code` is general code quality + logic review. It catches some security issues but is not OWASP/STRIDE focused.
`audit-security` applies the full STRIDE threat model and OWASP Top 10, with optional auto-fix.

---

## ❌ Using `/tkm:review-code` when the user asked for lint/static analysis

**Wrong scenario:**
> "Run SunLint on staged files" → `/tkm:review-code`

**Right choice:** `/tkm:lint-code`

**Why it's wrong:**
`review-code` is a reasoning review. `lint-code` runs the deterministic SunLint gate and writes CI-ready reports.

---

## ❌ Using `/tkm:audit-security` for dependency license policy

**Wrong scenario:**
> "Check whether our dependencies have allowed licenses" → `/tkm:audit-security`

**Right choice:** `/tkm:audit-licenses`

**Why it's wrong:**
`audit-security` looks for vulnerabilities and threat-model issues. `audit-licenses` runs licenseal and applies `licenseal.policy.toml`.

---

## ❌ Using `/tkm:brainstorm` or `/tkm:research` to estimate a project

**Wrong scenario:**
> "Estimate how long this spec will take" → `/tkm:brainstorm`
> "Dự toán dự án này tốn bao nhiêu man-days?" → `/tkm:research`

**Right choice:** `/tkm:estimate` (pass spec document or directory)

**Why it's wrong:**
`brainstorm` debates strategic trade-offs — it won't parse your PDF spec or output a WBS.
`research` looks up information — it won't calculate role-based effort from your document.
`estimate` is purpose-built: it parses the spec, applies knowledge-base formulas, and outputs WBS + man-days.

**Use `/tkm:estimate` when:** "Estimate this spec", "How many man-days for this RFP?", "Generate WBS from this Excel"
**Use `brainstorm` when:** "Should I use T-shirt sizing or man-days for this project?" (methodology decision)

---

## Quick Confusion Matrix

| I have... | And want... | Use |
|-----------|-------------|-----|
| A Figma/screenshot | Code from it | `design-to-code` |
| No design yet | To decide what it looks like | `design-ui` |
| A broken app | It fixed | `fix-bug` |
| Unclear root cause | Investigation | `debug-code` |
| A task to implement | Full pipeline | `takumi` |
| Just want a plan | Blueprint only | `create-plan` |
| A technology question | Expert advice | `research` or `brainstorm` |
| A spec document | Effort estimate | `estimate` |
| Past project data | Calibrate future estimates | `estimate calibrate` |
| Code to merge | Ship it | `ship` |
| Need security check | OWASP audit | `audit-security` |
| Need static lint | SunLint report | `lint-code` |
| Need license compliance | licenseal + policy | `audit-licenses` |
| General code check | Quality review | `review-code` |
