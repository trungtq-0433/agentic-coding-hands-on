# Codex Companion — review-code

> Read this ONLY when `--codex-companion` was passed. Common contract (probe, degradation, invocation
> discipline): `claude/skills/_shared/codex-companion.md` — do NOT duplicate it here.

A second, independent model (OpenAI Codex) runs an adversarial review over the **same git diff** so Claude's
findings get cross-checked. Runs ONLY when `--codex-companion` is passed.

**Companion point:** AFTER Stage 3 adversarial produces Claude's findings, BEFORE the Verification Gate.
Codex reviews the diff independently → no anchoring.

**Invocation is via Bash, NOT a slash-command.** The plugin's `/codex:review` and `/codex:adversarial-review`
are `disable-model-invocation: true` — a skill cannot call them. Drive the plugin runtime through the helper:

1. Probe: `claude/skills/_shared/scripts/codex-companion.sh probe review`.
   - `UNAVAILABLE:plugin-missing` → first run the contract's install-offer (`AskUserQuestion` → `install-plugin`), then degrade for this session.
   - Any other `UNAVAILABLE:*` → emit the one-line degradation warning, skip to the Verification Gate with Claude's findings only.
2. `AVAILABLE` → map the resolved target to a plugin-supported scope, then run the helper. **Codex reviews the
   working-tree or a `base...HEAD` branch diff — it must be the SAME change Claude reviewed, or degrade:**
   | review-code target | helper call | guard |
   |--------------------|-------------|-------|
   | `--pending` (uncommitted) | `codex-companion.sh review working-tree "<focus>"` | working-tree diff must be non-empty |
   | `#PR` | `codex-companion.sh review branch --base <baseRefOid> "<focus>"` | resolve exact SHAs: `gh pr view <n> --json headRefOid,baseRefOid`; require `git rev-parse HEAD` == `headRefOid` (else degrade); `git fetch` `baseRefOid` if the object is missing locally, then pass that **SHA** (not a local branch name, which may be stale) so `base...HEAD` matches `gh pr diff` |
   | commit `abc1234` **== HEAD** | `codex-companion.sh review branch --base abc1234~1 "<focus>"` | HEAD must equal that commit |
   | default (recent changes in context) | — | if the change is uncommitted → treat as `--pending`; if it's a context-only diff with no git artifact → **degrade** (do not map to working-tree) |
   | commit not HEAD / `codebase` / `codebase parallel` | — | **not a supported diff → degrade**: note "Codex companion supports working-tree and branch diffs only" |
   - `<focus>` = short line steering Codex at the risk areas Claude cares about (optional).
   - On any degrade case: emit the one-line warning and continue Claude-only.
3. Codex returns rendered findings (`[severity] file:line` + recommendation). Tag them `[codex-adv]`; tag Claude's
   `[claude]`. Push all into one pool → Verification Gate.

**Read-only:** the helper runs Codex in a read-only sandbox — it never modifies code. Never pass secrets in `<focus>`.

**Secret guard:** before sending, the helper scans the scope's changed files + diff for `.env`/keys/credentials
and secret-ish assignments. On a hit it returns `UNAVAILABLE:secrets-in-diff` → emit the degradation warning
and run Claude-only (the diff is never egressed to Codex). Conservative by design; false positives just fall
back to Claude-only.
