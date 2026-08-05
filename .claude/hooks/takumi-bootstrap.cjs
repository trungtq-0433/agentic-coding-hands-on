#!/usr/bin/env node
/**
 * SessionStart bootstrap — injects skill-routing discipline at the start of every session.
 *
 * Fires after session-init in the SessionStart chain.
 * Reminds the agent to reach for a Takumi skill before improvising.
 * Does NOT duplicate the catalog — points to `help` skill and
 * skills/help/references/skill-catalog.md for the Use-for + Key-triggers lookup.
 *
 * Output is intentionally terse (injected every session).
 * Entire hook is wrapped so a failure here can never block session start.
 *
 * Exit code: always 0 (non-blocking).
 */
try {
  const lines = [
    '## Takumi — skill routing discipline',
    'Before doing substantive work, check whether a Takumi skill already covers it.',
    '- **1% rule:** if a task overlaps a skill’s purpose even slightly (implement, plan, debug, review, test, research, deploy, docs, estimate…), activate that skill instead of improvising.',
    '- **Lookup:** consult `.claude/skills/help/references/skill-catalog.md` (Use-for + Key-triggers per skill), or run `/tkm:help` when unsure which skill fits.',
    '- **Process skills win:** prefer `/tkm:takumi`, `/tkm:create-plan`, `/tkm:fix-bug`, `/tkm:review-code`, `/tkm:ship` over ad-hoc multi-step work.',
    '- **Red flags you skipped a skill:** writing code with no plan, debugging by guessing, shipping without review/tests, answering an architecture question from memory.',
  ];
  process.stdout.write(`${lines.join('\n')}\n`);
} catch (_err) {
  // Swallow silently — session start must not be blocked by a dispatcher failure.
}
process.exit(0);
