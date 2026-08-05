# Codex Companion — brainstorm (Counter-View)

> Read this ONLY when `--codex-companion` was passed. Common contract (probe, degradation, invocation
> discipline): `claude/skills/_shared/codex-companion.md` — do NOT duplicate it here.

A second, independent model (OpenAI Codex) challenges the chosen direction — an outside adversarial voice,
not from Claude's own reasoning. Runs ONLY when `--codex-companion` is passed.

**Companion point:** AFTER Claude has a recommended direction (Stage 7), BEFORE sealing/recording. Claude
reasons first; Codex challenges after → no anchoring.

**Why not the plugin's `/codex:adversarial-review`:** that command reviews a **git diff** and takes only focus
text — it cannot review a standalone design proposal (a brainstorm has no code yet). So the counter-view goes
through the codex CLI directly via the helper's `counterview` subcommand.

**Flow:**
1. Probe: `claude/skills/_shared/scripts/codex-companion.sh probe counterview` (needs only an authenticated
   CLI — the plugin runtime is not required for `counterview`).
   - `UNAVAILABLE:plugin-missing` → first run the contract's install-offer (`AskUserQuestion` → `install-plugin`), then degrade. (Note: `counterview` itself only needs the CLI, so this is rare here.)
   - Any other `UNAVAILABLE:*` → emit the one-line degradation warning, proceed to seal without a counter-view.
2. `AVAILABLE` → write the chosen approach (design + rationale + trade-offs) to a temp file, then:
   `claude/skills/_shared/scripts/codex-companion.sh counterview <approach-file>`.
   Returns 4–6 concrete objections (read-only, no git diff needed).
3. Claude answers **each** counter-point: agree → adjust the recommendation; refute → state why. Vague/
   non-actionable points get tagged as such, not silently dropped.

**Codex is advisory** — the final direction stays Claude's after weighing the objections. It never rewrites the
recommendation. Never pass secrets into the approach summary.
