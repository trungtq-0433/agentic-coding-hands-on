---
name: tkm:audit-licenses
description: "Audit dependency license compatibility with licenseal, including transitive checks, project policy allow/deny lists, review files, CI-ready reports, and explicit add/remove workflows for whitelist or blacklist package/license/risk entries. Use for license audit, audit licenses, licenseal, dependency licenses, license compliance, license policy, blacklist/whitelist license, and blacklist/whitelist package tasks."
argument-hint: "[optional scope or policy request]"
metadata:
  author: takumi-agent-kit
  version: "1.4.0"
module: testing-code-quality
triggers: ["license audit", "audit licenses", "licenseal", "dependency licenses", "license compliance", "license policy", "blacklist license", "whitelist license", "blacklist package", "whitelist package", "blacklist risk", "whitelist risk"]
---

# License Audit Gate

Use this skill when dependency licenses need a compatibility gate or the project license policy needs an explicit allow/deny edit. Bare invocation runs a strict production audit with transitive dependencies included.

## Invocation And Routing

Bare `/tkm:audit-licenses` means strict transitive production audit.

Route direct/dev/non-strict/review requests to licenseal flags. Route create/show/allow/deny/remove policy requests to `references/policy-management.md`. Policy entries cover packages, licenses, and risks.

Vietnamese intent is valid: "cho phep", "whitelist", "allow" map to allow; "cam", "chan", "blacklist", "deny" map to deny; "xoa", "bo", "remove" map to removal.

## Pick The licenseal Command

Detect the invocation in this order: `uv run licenseal` when `uv.lock` exists or uv owns Python tooling, then `poetry run licenseal`, `pdm run licenseal`, `pipenv run licenseal`, and finally `licenseal`.

Verify with `<licenseal> --version`. licenseal is installed automatically by the Takumi
skills installer (via `uv tool` or `pipx`). If no invocation works, handle it like the
codex-companion install-offer: ask ONCE via `AskUserQuestion` — "licenseal is not installed.
Install it now?" with options `Install now (Recommended)` / `Skip`.

- **Install now** → run `uv tool install licenseal` when `uv` is on PATH, else
  `pipx install licenseal`; then re-verify `licenseal --version`. On success, continue the
  audit (usable immediately). On failure, or if neither `uv` nor `pipx` exists, stop and report.
- **Skip** → stop; do not run the audit.

Never install without the user's answer, and never fake an audit result.

## Default Run

Create the report directory, then run strict transitive production checks:

```bash
mkdir -p .takumi/reports
<licenseal> check --path . --format json --output .takumi/reports/licenseal.json
<licenseal> check --path . --format markdown --output .takumi/reports/LICENSES.md
```

Keep dev dependencies out by default. Keep strict mode and transitive scanning on by default.

If licenseal exits before writing a report because registries are unreachable or dependency resolution fails, classify it as an environment/tool failure, keep the gate blocked, and do not create policy approvals or review entries from incomplete data.

## Audit Options

| Intent | Effect |
|--------|--------|
| direct dependencies only | Add `--no-transitive` to both check commands |
| include dev dependencies | Add `--dev` to both check commands |
| relaxed/non-strict audit | Add `--no-strict` to both check commands |
| review findings | After JSON exists, run review mode |
| advisory policy | Apply `licenseal.policy.toml` as warnings unless licenseal itself fails |
| strict policy | Apply `licenseal.policy.toml` as blocking findings |

Automation aliases remain accepted for skill-to-skill calls and CI: `--direct`, `--dev`, `--no-strict`, `--review`, `--policy advisory|strict`, `--init-policy`, `--policy-list`, `--allow-package`, `--deny-package`, `--allow-license`, `--deny-license`, `--allow-risk`, `--deny-risk`, `--remove-package`, `--remove-license`, `--remove-risk`.

## Takumi Policy Layer

If `licenseal.policy.toml` exists at the project root, parse it after `.takumi/reports/licenseal.json` is written. This file is the project-owned allow/deny policy. `licenseal.review.toml` remains the licenseal audit trail, not the main policy.

Before creating, showing, or editing policy, read:

- `references/policy-management.md`
- `references/licenseal.policy.template.toml`

## Review Mode

When `--review` is passed and findings are reviewable:

```bash
<licenseal> init-review-file --from-report .takumi/reports/licenseal.json --merge
```

Guide the user through each flagged dependency. Do not write fake approvals for confirmed incompatibilities. Genuine unresolved incompatibilities stay failed.

## Result Reading

Read `.takumi/reports/licenseal.json` and report total dependencies, ok dependencies, warnings, violations, unknown licenses, reviewed entries, review gaps, and policy denies or allowlist gaps.

If the JSON shape changes, count from dependency and finding lists instead of guessing.

## Blocking Rules

- licenseal violations block.
- policy denies block in strict policy mode.
- licenseal gaps block `/tkm:ship official`.
- Unknown or unlisted licenses are "needs review" in strict policy mode.
- `--policy advisory` keeps Takumi policy findings advisory, but licenseal's own failure remains blocking.

This audit is engineering compliance evidence. It is not legal advice.
