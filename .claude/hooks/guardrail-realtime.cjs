#!/usr/bin/env node
/**
 * guardrail-realtime — PostToolUse / Edit+Write+MultiEdit hook. Temper, in real time.
 *
 * After a file is forged, run the project's own typecheck/lint/test commands
 * against it and surface any failure straight back to the agent — so a mistake
 * is caught at the bench, not three steps later.
 *
 * Advisory only: it never blocks (always exits 0 / continue:true); a failing
 * check is injected as context for the agent to fix. Opt-in and config-driven —
 * commands come from .tkm.json `hooks.guardrail`, never guessed. Fail-open: any
 * hook error is swallowed silently so it can never stall the Forge.
 *
 * Config (.tkm.json):
 *   hooks.guardrail.enabled    — false by default; hook is a no-op until set true
 *   hooks.guardrail.debounceMs — min gap between runs in one session (default 5000)
 *   hooks.guardrail.checks     — { typecheck, lint, test }: shell command or "".
 *                                A `{file}` token is replaced by the edited path
 *                                (shell-escaped) so the check stays file-scoped;
 *                                omit it to run repo-wide. Empty/missing = skipped.
 */

try {
  const fs = require('fs');
  const path = require('path');
  const os = require('os');
  const { execSync } = require('child_process');
  const { loadConfig, escapeShellValue } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  const EDIT_TOOLS = ['Edit', 'Write', 'MultiEdit'];
  const CHECK_ORDER = ['typecheck', 'lint', 'test'];
  const COMMAND_TIMEOUT_MS = 30_000;
  const DEBOUNCE_FILE = path.join(os.tmpdir(), 'tkm-guardrail-session.json');

  /** Read the guardrail config block, or null when disabled/absent. */
  function readGuardrailConfig() {
    const cfg = loadConfig({ includeProject: true, includeAssertions: false });
    const g = cfg.hooks && cfg.hooks.guardrail;
    if (!g || typeof g !== 'object' || g.enabled !== true) return null;
    return g;
  }

  /** True when a run happened within debounceMs — caller should skip this edit. */
  function debounced(debounceMs) {
    try {
      const last = JSON.parse(fs.readFileSync(DEBOUNCE_FILE, 'utf8')).lastRun || 0;
      return Date.now() - last < debounceMs;
    } catch {
      return false;
    }
  }

  /** Stamp the current run time so the next edits inside the window are skipped. */
  function stampRun() {
    try {
      fs.writeFileSync(DEBOUNCE_FILE, JSON.stringify({ lastRun: Date.now() }));
    } catch {
      // non-fatal
    }
  }

  /** Build the runnable command for a check, or null to skip it. */
  function buildCommand(rawCommand, filePath) {
    if (!rawCommand || typeof rawCommand !== 'string' || !rawCommand.trim()) return null;
    if (!rawCommand.includes('{file}')) return rawCommand;
    return rawCommand.split('{file}').join(escapeShellValue(filePath));
  }

  /** Run one check; return its failure text, or null when it passes. */
  function runCheck(name, command, cwd) {
    try {
      execSync(command, { cwd, timeout: COMMAND_TIMEOUT_MS, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
      return null;
    } catch (err) {
      // Command exited non-zero (or timed out) — capture what it reported.
      const detail = `${err.stdout || ''}${err.stderr || ''}`.trim() || err.message || 'check failed';
      const trimmed = detail.split('\n').slice(0, 20).join('\n');
      return `### ${name} failed (\`${command}\`)\n${trimmed}`;
    }
  }

  function main() {
    const timer = createHookTimer('guardrail-realtime', { event: 'PostToolUse' });
    try {
      const hookData = JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
      const toolName = hookData.tool_name || '';
      if (!EDIT_TOOLS.includes(toolName)) {
        timer.end({ tool: toolName, status: 'skip', exit: 0, note: 'non-edit-tool' });
        return console.log(JSON.stringify({ continue: true }));
      }

      const config = readGuardrailConfig();
      if (!config) {
        timer.end({ status: 'skip', exit: 0, note: 'disabled' });
        return console.log(JSON.stringify({ continue: true }));
      }

      const debounceMs = Number.isFinite(config.debounceMs) ? config.debounceMs : 5000;
      if (debounced(debounceMs)) {
        timer.end({ status: 'skip', exit: 0, note: 'debounced' });
        return console.log(JSON.stringify({ continue: true }));
      }

      const toolInput = hookData.tool_input || {};
      const filePath = toolInput.file_path || toolInput.path || '';
      const cwd = hookData.cwd || process.cwd();
      const checks = config.checks || {};

      stampRun();

      const failures = [];
      for (const name of CHECK_ORDER) {
        const command = buildCommand(checks[name], filePath);
        if (!command) continue;
        const failure = runCheck(name, command, cwd);
        if (failure) failures.push(failure);
      }

      const result = { continue: true };
      if (failures.length) {
        result.additionalContext =
          `\n\n[Guardrail] Real-time checks reported issues after editing \`${filePath}\`. ` +
          `Fix these before moving on:\n\n${failures.join('\n\n')}`;
      }

      timer.end({ tool: toolName, status: 'ok', exit: 0, note: failures.length ? 'failures-injected' : 'clean' });
      console.log(JSON.stringify(result));
    } catch (e) {
      // Fail-open: a guardrail must never block the Forge.
      logHookCrash('guardrail-realtime', e, { event: 'PostToolUse' });
      console.log(JSON.stringify({ continue: true }));
    }
  }

  main();
} catch (e) {
  try {
    require('./lib/hook-logger.cjs').logHookCrash('guardrail-realtime', e, { event: 'PostToolUse' });
  } catch (_) {}
  process.exit(0); // fail-open
}
