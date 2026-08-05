---
name: tkm:run-tests
description: "Temper the work under fire — run unit, integration, e2e, and UI tests. Covers test execution, coverage analysis, build verification, visual regression, and QA reports. A piece untested is a piece unfinished."
argument-hint: "[context] OR ui [url]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: testing-code-quality
triggers: ["run tests", "test coverage", "unit test", "e2e", "visual regression", "does it pass"]
---

# Tempering the Work

A blade fresh from the forge is soft. It cuts nothing.
Tempering is what reveals whether the metal holds — applying heat, then controlled stress, until the flaw shows or the strength proves out.

This skill is that tempering: structured, thorough, unsparing.
Passing builds do not prove correctness. Evidence does.

## When Called Without Arguments

Given a scope to test, get to work. Called bare, with nothing to chew on, surface the two paths through `AskUserQuestion`:

| Operation | Description |
|-----------|-------------|
| `(default)` | Run unit/integration/e2e tests |
| `ui` | Run UI tests on a website |

Frame the `AskUserQuestion` with header "Test Operation" and the prompt "What would you like to do?".

## The Tempering Law

**NEVER IGNORE FAILING TESTS.** Fix root causes, not symptoms. No mocks, tricks, or workarounds to pass builds.

A test that is silenced rather than fixed is a crack hidden under lacquer.

## When to Temper

- **After forging**: Prove out fresh features or the bug you just patched
- **Coverage checks**: Confirm the project's thresholds hold (80%+)
- **UI verification**: Visual regression, responsive layout, accessibility
- **Build validation**: Confirm the build, its dependencies, and CI/CD all behave
- **Before delivery**: The last gate standing between you and a commit or push

## Tempering Methods

### 1. Code Testing (`references/test-execution-workflow.md`)

Drive the suites, read what comes back, pull coverage. Reaches across JS/TS (Jest/Vitest/Mocha), Python (pytest), Go, Rust, and Flutter — carries the procedure, the bar to clear, and the commands to run.

**Load when:** Running unit/integration/e2e tests, checking coverage, validating builds

### 2. UI Testing (`references/ui-testing-workflow.md`)

Visual work driven through the browser via the `tkm:automate-browser` skill: screenshots, responsive sweeps, accessibility audits, form automation, and console-error capture. Carries auth injection for routes behind a login.

**Load when:** Visual regression testing, UI bugs, responsive layout checks, accessibility audits

### 3. Code Quality Preflight (`/tkm:lint-code`)

Run SunLint after typecheck/analyze and before the deeper suites. The lint-code skill chooses changed-aware scanning by default and writes `.takumi/reports/sunlint.json`.

**Load when:** Checking code quality, static analysis, security lint, architecture lint

### 4. Report Format (`references/report-format.md`)

A laid-out QA report template — results at a glance, coverage numbers, the tests that broke, performance, build state, and what to do next.

**Load when:** Generating test summary reports

## Quick Reference

```
Code tests     → test-execution-workflow.md
  npm test / pytest / go test / cargo test / flutter test
  Coverage: npm run test:coverage / pytest --cov

Lint preflight → /tkm:lint-code
  SunLint changed-aware by default; report: .takumi/reports/sunlint.json

UI tests       → ui-testing-workflow.md
  Screenshots, responsive, a11y, forms, console errors
  Auth: inject-auth.js for protected routes

Reports        → report-format.md
  Structured QA summary with metrics & recommendations
```

## The Tempering Process

1. Read the recent changes (or the requirements) and settle on what needs testing
2. Fire the typecheck/analyze commands first — syntax errors should fall here, not mid-suite
3. Run `/tkm:lint-code` for the SunLint quality preflight
4. Run the suites that fit the scope
5. Sift the output, eyes on what broke
6. Pull coverage reports where they apply
7. Frontend work: drive UI tests through the `tkm:automate-browser` skill
8. Write up the structured summary report

## Tools

- **Test runners**: Jest, Vitest, Mocha, pytest, go test, cargo test, flutter test
- **Coverage**: Istanbul/c8/nyc, pytest-cov, go cover
- **Static analysis**: the `tkm:lint-code` skill runs SunLint and reports `.takumi/reports/sunlint.json`
- **Browser**: the `tkm:automate-browser` skill carries the UI work — screenshots, ARIA, console, network
- **Debugging**: reach for the `tkm:debug-code` skill when a test exposes a flaw that needs digging into
- **Thinking**: the `tkm:think-sequential` skill when a failure won't untangle in one pass

## Standards of Craft

- Every critical path carries coverage — no exceptions
- Exercise the path that works AND each way it can fail
- Keep tests isolated — none leaning on another
- A test must give the same answer every run, anywhere
- Sweep up test data once the run ends
- Never quiet a failing test just to clear the build

## Report Output
**IMPORTANT:** Call the "/tkm:organize-files" skill to put the outputs in order.

Name files by the pattern the hooks drop into the `## Naming` section.

## Working in a Team

Working as one of several teammates:
1. At the start, look over `TaskList` and lay claim to your task — or the next one free — through `TaskUpdate`
2. Pull the whole brief with `TaskGet` before a single step
3. Hold off until the upstream (implementation) tasks clear; only then test
4. Stay inside your file ownership — touch only the test files handed to you
5. Finished work means `TaskUpdate(status: "completed")` first, then the results go to the lead by `SendMessage`

**Fallback:** The Task tools (`TaskList`/`TaskUpdate`/`TaskGet`) live in the CLI alone — the VSCode extension has none of them. Should they fail, track progress with `TodoWrite` and keep coordination on `SendMessage`.
