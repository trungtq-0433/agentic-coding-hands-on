---
name: tkm:lint-code
description: "Run SunLint static analysis for code quality, security, architecture, staged/changed files, and CI-ready reports. Use for lint code, sunlint, code quality, static analysis, security lint, and architecture lint checks."
argument-hint: "[optional scope: staged, full, security, architecture, HTML report]"
metadata:
  author: takumi-agent-kit
  version: "1.2.0"
module: testing-code-quality
triggers: ["lint code", "sunlint", "code quality", "static analysis", "security lint", "architecture lint"]
---

# SunLint Gate

Use this skill when code needs a static quality gate. Bare invocation should run the useful default. Users should be able to ask in plain language; do not make them memorize flags.

## Invocation

```bash
/tkm:lint-code
```

Common requests:

| User says | Do |
|-----------|----|
| `/tkm:lint-code` or "lint this" | Changed-aware scan when changes exist, otherwise full scan |
| "lint staged files" | Scan staged files |
| "run full lint" | Scan the whole repo |
| "security lint" | Run SunLint security checks |
| "architecture lint" | Run SunLint architecture checks and architecture report |
| "also generate HTML report" | Add the HTML report to whichever scan is selected |

## Required Tool

Before running anything, verify SunLint:

```bash
sunlint --version
```

SunLint is installed automatically by the Takumi skills installer. If it is still missing,
handle it like the codex-companion install-offer: ask ONCE via `AskUserQuestion` —
"SunLint is not installed. Install it now?" with options `Install now (Recommended)` / `Skip`.

- **Install now** → run `npm install -g @sun-asterisk/sunlint`, then re-verify with
  `sunlint --version`. On success, continue with the scan (usable immediately — no restart
  needed). On failure, stop and report the error.
- **Skip** → stop; do not run the scan.

Never install without the user's answer, and never fake a lint result when the tool is unavailable.

## Default Run

Create the report directory before invoking SunLint:

```bash
mkdir -p .takumi/reports
```

Called with no flags:

1. If this is a git repo and `git status --short` shows changed files, run a changed-aware scan:
   ```bash
   sunlint --all --changed-files --input=. --output-summary=.takumi/reports/sunlint.json
   ```
   If that command exits `0` but does not create `.takumi/reports/sunlint.json`, or stdout/stderr says changed-file detection failed, rerun the full scan:
   ```bash
   sunlint --all --input=. --output-summary=.takumi/reports/sunlint.json
   ```
   This keeps the default stable in sandboxed Codex runs where SunLint cannot spawn a shell to discover changed files.
2. If there are no changed files, or the repository is not a git repo, run a full scan:
   ```bash
   sunlint --all --input=. --output-summary=.takumi/reports/sunlint.json
   ```

## Intent Routing

Map plain-language intent to SunLint commands:

| Intent | Command shape |
|--------|---------------|
| staged files | `sunlint --all --staged-files --input=. --output-summary=.takumi/reports/sunlint.json` |
| full repo | `sunlint --all --input=. --output-summary=.takumi/reports/sunlint.json` |
| security | `sunlint --security --input=. --output-summary=.takumi/reports/sunlint.json` |
| architecture | `sunlint --architecture --input=. --arch-report --output-summary=.takumi/reports/sunlint.json` |
| HTML report | Add `--output-html=.takumi/reports/sunlint.html` to the selected command |

Automation aliases remain accepted for skill-to-skill calls and CI: `--staged`, `--full`, `--security`, `--architecture`, `--report-html`. When more than one mode is requested, prefer the most specific scan in this order: security, architecture, staged, full, default.

## Result Reading

After the command finishes, read `.takumi/reports/sunlint.json` when it exists. Report the useful summary fields:

- score and grade
- files analyzed
- total violations
- error count
- warning count
- report paths written

If SunLint prints useful details but no JSON file is written, summarize stdout/stderr and call out that the summary file was missing.

## Blocking Rules

- Tool failure or a non-zero exit blocks.
- Error-level violations block.
- Warning-only findings are advisory by default.
- When the caller is `/tkm:ship official`, warning-only findings should be surfaced as release concerns, but only error-level violations block unless project policy says otherwise.

SunLint evidence supports review. It does not replace reasoning review by `tkm:review-code`.
