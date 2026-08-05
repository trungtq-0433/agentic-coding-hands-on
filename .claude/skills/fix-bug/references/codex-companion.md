# Codex Companion — fix-bug (Rescue)

> Read this ONLY when `--codex-companion` was passed. Common contract (probe, degradation, invocation
> discipline): `claude/skills/_shared/codex-companion.md` — do NOT duplicate it here.

When Claude stalls, hand the bug to a second model (Codex) for an independent investigation BEFORE escalating to the user.

**Trigger:** exactly at the **2nd** failed Step 5 verification (not on the 1st — cheap bugs shouldn't pay for it;
not at the 3rd — the point is to try Codex *before* the user hand-off). Skip entirely if the flag is off.

**Invocation is via Bash, NOT `/codex:rescue`.** The plugin's rescue defaults to foreground and its
`/codex:status`/`/codex:result` are `disable-model-invocation` (a skill cannot poll them). Drive the plugin
runtime through the helper, which runs Codex **read-only** (Codex *proposes* a fix; it does not apply one):

1. Probe: `claude/skills/_shared/scripts/codex-companion.sh probe rescue`.
   - `UNAVAILABLE:plugin-missing` → first run the contract's install-offer (`AskUserQuestion` → `install-plugin`), then degrade for this session.
   - Any other `UNAVAILABLE:*` → emit the one-line degradation warning, keep the standard 3-fail → question-architecture path.
2. `AVAILABLE` → run (for a long rescue, wrap the Bash call `run_in_background: true` and read with `BashOutput`):
   `claude/skills/_shared/scripts/codex-companion.sh rescue "<bug summary + confirmed file:line from Step 2 + what Claude already tried>"`
   - The helper bounds the run with `timeout` (default 300s, override `CODEX_RESCUE_TIMEOUT`). If it prints
     `TIMEOUT:<n>s` (exit 124) or `UNAVAILABLE:no-timeout` (no timeout utility present) → treat as no result:
     escalate via the standard path. Rescue never blocks indefinitely.
   - The prompt is passed after a `--` marker, so a bug summary containing `--write`/`--cwd` stays literal and
     cannot flip Codex out of its read-only sandbox.
3. Codex returns its diagnosis + a **proposed** fix. Apply it, then take it through **Step 5 verification
   (mandatory)** — never auto-accept:
   - Verify **PASS** → adopt the fix → Step 6 Finalize.
   - Verify **FAIL** → resume the standard path (question architecture + user), and report what Codex proposed.

**Never** adopt a Codex fix without passing Step 5. **Never** put secrets in the rescue prompt.
