# Codex Companion — Shared Opt-In Contract

> Imported by skills that support the `--codex-companion` flag (review-code, fix-bug, brainstorm, …).
> One source of truth for availability, degradation, and invocation discipline. DO NOT duplicate per skill.

## What it does

`--codex-companion` invites a **second, independent model** (OpenAI Codex, via the `codex-plugin-cc` plugin)
to cross-check Claude's work at the skill's adversarial point. Claude always produces its result **first**;
Codex reviews/challenges **after** — never the reverse (prevents anchoring Claude to Codex's framing).

## Why every call goes through Bash (critical)

The plugin's slash-commands are **not usable from inside a skill**:
- `/codex:review`, `/codex:adversarial-review`, `/codex:status`, `/codex:result` declare
  `disable-model-invocation: true` → the model cannot invoke them.
- `/codex:review` / `/codex:adversarial-review` review a **git diff** only; they cannot take a free-text
  design proposal (so brainstorm cannot use them at all).

So all companion calls run through one Bash entrypoint, which drives the plugin's own runtime
(`codex-companion.mjs`) or the `codex` CLI directly — the same engine the slash-commands use:

```
claude/skills/_shared/scripts/codex-companion.sh <probe|review|counterview|rescue> ...
```

## Activation gate

Run ONLY when the user passed `--codex-companion`. Otherwise skip entirely — behavior is unchanged.
Probe by the subcommand you need (`counterview` needs only the CLI; `review`/`rescue` also need the plugin):

```
claude/skills/_shared/scripts/codex-companion.sh probe <counterview|review|rescue>
```

| Signal | Meaning | Action |
|--------|---------|--------|
| `AVAILABLE` | codex CLI + authenticated + plugin runtime found | Proceed at the companion point |
| `UNAVAILABLE:no-cli` | `codex` binary not on PATH | Degrade — tip: `npm install -g @openai/codex` then `codex login` (or run `/codex:setup`) |
| `UNAVAILABLE:not-authed` | CLI present, not logged in | Degrade — tip: `codex login` |
| `UNAVAILABLE:plugin-missing` | plugin not installed | **Offer install** (see below), then degrade for THIS session |

### Offer to install the plugin (on `plugin-missing`)

When the flag is set and the probe returns `UNAVAILABLE:plugin-missing`, before degrading, ask ONCE via
`AskUserQuestion` — "Codex companion needs the codex plugin. Install it now?" with options
`Install now (Recommended)` / `Skip`:

- **Install now** → run `claude/skills/_shared/scripts/codex-companion.sh install-plugin`. It is idempotent
  (`marketplace add` + `plugin install codex@openai-codex`). On success it prints
  `INSTALLED: restart …`. **Tell the user the plugin activates only after a session restart** — it CANNOT be
  used in the current session. Continue THIS run Claude-only regardless.
- **Skip** → degrade quietly, Claude-only.

Never auto-install without the user's answer. Only offer once per run.

## Subcommand per skill

| Skill | Subcommand | Notes |
|-------|-----------|-------|
| review-code | `review <scope> [--base <ref>] [focus]` | plugin adversarial review over a git diff; map target → `working-tree` or `branch --base <ref>` **only when HEAD is the reviewed change**; PR needs HEAD == PR head; commit-not-HEAD / codebase / context-only diffs unsupported → degrade; secret pre-scan degrades on `UNAVAILABLE:secrets-in-diff` (never egresses `.env`/keys) |
| brainstorm | `counterview <approach-file>` | codex CLI direct (design proposal has no diff); returns 4–6 objections; needs only `probe counterview` |
| create-plan | `plan-review <plan-dir>` | codex CLI **with repo access** (red-team grounds findings in code); emits the persona `## Finding` schema with `**Evidence:** file:line`; helper drops findings whose citation doesn't resolve (file exists + line/range in bounds) or whose severity is invalid; needs only `probe plan-review`; bounded by `timeout` (default 300s, `CODEX_PLAN_TIMEOUT`). Degrades (→ persona-only) on `UNAVAILABLE:timeout`/`no-timeout`/`codex-failed`/`empty-output`/`no-grounded-findings`. Location check ≠ semantic grounding — Step 6/7 still adjudicate merit |
| fix-bug | `rescue "<prompt>"` | plugin task, **read-only** (Codex proposes, does not apply); bounded by `timeout` (default 300s, `CODEX_RESCUE_TIMEOUT`) — prints `TIMEOUT:<n>s` on expiry → escalate; wrap the Bash call `run_in_background: true` for a long run |

## Graceful degradation (never hard-fail)

On any `UNAVAILABLE:*`, emit **one** line and continue the skill Claude-only:

```
⚠️ Codex companion off (<reason>) — running Claude-only.
```

Never abort the skill. Never retry the probe in a loop.

## Invocation discipline

1. Codex runs **after** Claude's own output exists for this stage.
2. Codex output is **advisory** — Claude reaches the final conclusion after weighing it.
3. Never auto-accept a Codex code change without the skill's own verification step (e.g. fix-bug Step 5).
   The helper runs Codex read-only, so a fix is always a *proposal* Claude must apply + verify.
4. Never pass secrets (`.env`, keys, tokens) into a Codex prompt/focus/approach summary.

## Security

- Probe suppresses `codex login status` output — no account/credential detail is printed.
- Review + counterview run in a read-only sandbox. Rescue is read-only unless a fix is explicitly applied
  by Claude after verification.
