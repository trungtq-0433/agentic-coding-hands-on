/**
 * Agent identity marker — read by hooks that need to branch by host agent.
 *
 * Shipped value: `claude` (kit default). The Codex installer overwrites this
 * file with `{ agent: 'codex' }` at install time so the same hook source can
 * make agent-specific decisions without sniffing environment variables.
 */
module.exports = { agent: 'claude' };
