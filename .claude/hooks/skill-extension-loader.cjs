#!/usr/bin/env node
/**
 * skill-extension-loader — PreToolUse / Skill hook. Forge stage (skill activation).
 *
 * When a skill fires, loads user-owned extension files and injects them before
 * the skill runs. Two sources are merged:
 *   1. Local (personal):  <root>/.claude/skills/<dir>/extensions/*.md
 *   2. Shared (team):     <sharedDir>/<dir>/*.md, where sharedDir comes from the
 *                         `skillExtensions.sharedDir` key in config.
 * Local overrides shared on filename collision (personal tuning wins).
 *
 * Root resolution for the local source tries, in order: $CLAUDE_PROJECT_DIR,
 * the Skill call's cwd, then $HOME (global install). The first root that has a
 * matching extensions dir wins. This keeps extensions loading across multi-repo
 * layouts (project dir ≠ cwd) and global installs.
 *
 * Extension frontmatter contract:
 *   extends: tkm:<skill-name>   (must match the activated skill)
 *   type: pre | post | override:<section-heading>
 *
 * Injection order: pre → override → post. Total payload capped at MAX_INJECT_CHARS;
 * oversize extensions degrade to a one-line reference so the agent reads them
 * on demand rather than bloating the context window.
 * Fail-open: any error allows the Skill call through untouched.
 */

// Crash wrapper
try {
  const fs = require('fs');
  const path = require('path');
  const os = require('os');
  const {
    isHookEnabled,
    loadConfigFromPath,
    sanitizePath,
    isAbsolutePath,
  } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  if (!isHookEnabled('skill-extension-loader')) {
    process.exit(0);
  }

  const MAX_INJECT_CHARS = 4096; // beyond this, list files rather than inlining
  const TYPE_ORDER = { pre: 0, override: 1, post: 2 };

  /** Strip namespace prefix: "tkm:review-code" → "review-code" */
  function skillDirCandidate(skillName) {
    const idx = skillName.lastIndexOf(':');
    return idx >= 0 ? skillName.slice(idx + 1) : skillName;
  }

  /** Parse YAML-lite frontmatter. Returns {fields, body} or null if absent. */
  function parseFrontmatter(content) {
    const normalized = content.replace(/\r\n/g, '\n');
    if (!normalized.startsWith('---\n')) return null;
    const end = normalized.indexOf('\n---', 4);
    if (end < 0) return null;
    const fields = {};
    for (const line of normalized.slice(4, end).split('\n')) {
      const m = line.match(/^([A-Za-z_-]+):\s*(.*)$/);
      if (m) fields[m[1].toLowerCase()] = m[2].trim().replace(/^["']|["']$/g, '');
    }
    // Closing --- with no trailing newline must not leak into body
    const nlAfterClose = normalized.indexOf('\n', end + 4);
    const body = nlAfterClose < 0 ? '' : normalized.slice(nlAfterClose + 1).trim();
    return { fields, body };
  }

  /** True when extendsField targets skillName, with or without the tkm: prefix. */
  function extendsMatches(extendsField, skillName) {
    if (!extendsField) return false;
    return (
      extendsField === skillName ||
      skillDirCandidate(extendsField) === skillDirCandidate(skillName)
    );
  }

  /** Normalize type field: pre | post | override:<section>. Returns null if invalid. */
  function parseType(typeField) {
    if (typeField === 'pre' || typeField === 'post') return typeField;
    if (/^override:.+$/.test(typeField || '')) return 'override';
    return null;
  }

  /**
   * Resolve the local extensions dir for a skill by trying candidate roots in
   * priority order: $CLAUDE_PROJECT_DIR → cwd → $HOME. The first root whose
   * <root>/.claude/skills/<dir>/extensions/ exists wins. Each candidate is
   * guarded against path traversal independently. Returns the dir or null.
   */
  function resolveLocalExtDir(skillDir, roots) {
    const seen = new Set();
    for (const root of roots) {
      if (!root || seen.has(root)) continue;
      seen.add(root);
      const skillsRoot = path.resolve(root, '.claude', 'skills');
      const extDir = path.resolve(skillsRoot, skillDir, 'extensions');
      // Path-traversal guard: a crafted skill name with "../" must not escape .claude/skills/
      if (extDir !== skillsRoot && !extDir.startsWith(skillsRoot + path.sep)) continue;
      if (fs.existsSync(extDir)) return extDir;
    }
    return null;
  }

  /**
   * Read the team-shared extensions dir pointer from config.
   * Checks both .takumi.json (what the `tkm` CLI / `tkm config set` writes) and the
   * kit-native .tkm.json, project-scope before global — mirroring isGraphifyEnabled's
   * precedence so `tkm config set skillExtensions.sharedDir` takes effect without a
   * broader config-file migration. First file defining a non-empty value wins.
   * Returns '' when unset.
   */
  function readSharedDirFromConfig(projectRoot, home) {
    const candidates = [];
    if (projectRoot) {
      candidates.push(path.join(projectRoot, '.claude', '.takumi.json'));
      candidates.push(path.join(projectRoot, '.claude', '.tkm.json'));
    }
    if (home) {
      candidates.push(path.join(home, '.claude', '.takumi.json'));
      candidates.push(path.join(home, '.claude', '.tkm.json'));
    }
    for (const cfgPath of candidates) {
      const cfg = loadConfigFromPath(cfgPath);
      const val = cfg && cfg.skillExtensions && cfg.skillExtensions.sharedDir;
      if (typeof val === 'string' && val.trim()) return val.trim();
    }
    return '';
  }

  /**
   * Resolve the shared per-skill dir <sharedDir>/<skillDir>. sharedDir may be
   * absolute (allowed as-is) or relative to projectRoot (must stay inside it —
   * sanitizePath rejects "../" escapes). Returns the dir or null.
   */
  function resolveSharedExtDir(skillDir, projectRoot, home) {
    const raw = readSharedDirFromConfig(projectRoot, home);
    if (!raw) return null;
    const sane = sanitizePath(raw, projectRoot); // absolute OK; relative must stay in root
    if (!sane) return null;
    const sharedRoot = isAbsolutePath(sane) ? sane : path.resolve(projectRoot, sane);
    const cand = path.resolve(sharedRoot, skillDir);
    if (cand !== sharedRoot && !cand.startsWith(sharedRoot + path.sep)) return null;
    return fs.existsSync(cand) ? cand : null;
  }

  /**
   * Read + validate extension files from one dir. Top-level *.md only —
   * evals/ subdir holds benchmark data, never inject it. Returns loaded entries
   * (each tagged with its source dir) and skipped filenames.
   */
  function readExtensions(extDir, skillName) {
    const loaded = [];
    const skipped = [];
    let entries;
    try {
      entries = fs
        .readdirSync(extDir, { withFileTypes: true })
        .filter((e) => e.isFile() && e.name.endsWith('.md'))
        .map((e) => e.name)
        .sort();
    } catch (_) {
      return { loaded, skipped };
    }
    for (const name of entries) {
      try {
        const parsed = parseFrontmatter(fs.readFileSync(path.join(extDir, name), 'utf-8'));
        const type = parsed && parseType(parsed.fields.type);
        if (!parsed || !type || !extendsMatches(parsed.fields.extends, skillName)) {
          skipped.push(name);
          continue;
        }
        loaded.push({ name, type, rawType: parsed.fields.type, body: parsed.body, dir: extDir });
      } catch (_) {
        skipped.push(name);
      }
    }
    return { loaded, skipped };
  }

  let input = '';
  process.stdin.on('data', (d) => (input += d));
  process.stdin.on('end', () => {
    const timer = createHookTimer('skill-extension-loader', { event: 'PreToolUse', tool: 'Skill' });
    try {
      const data = JSON.parse(input || '{}');
      const skillName = (data.tool_input && data.tool_input.skill) || '';
      if ((data.tool_name && data.tool_name !== 'Skill') || !skillName) {
        timer.end({ status: 'ok', note: 'not a skill call' });
        process.stdout.write('{}');
        return;
      }

      const cwd = data.cwd || process.cwd();
      const projectDir = process.env.CLAUDE_PROJECT_DIR || '';
      const home = os.homedir();
      const skillDir = skillDirCandidate(skillName);
      // Config + shared-dir resolution anchor on the project root; fall back to cwd.
      const primaryRoot = projectDir || cwd;

      const localExtDir = resolveLocalExtDir(skillDir, [projectDir, cwd, home]);
      const sharedExtDir = resolveSharedExtDir(skillDir, primaryRoot, home);

      if (!localExtDir && !sharedExtDir) {
        timer.end({ status: 'ok', target: skillName, note: 'no extensions' });
        process.stdout.write('{}');
        return;
      }

      const localRead = localExtDir ? readExtensions(localExtDir, skillName) : { loaded: [], skipped: [] };
      const sharedRead = sharedExtDir ? readExtensions(sharedExtDir, skillName) : { loaded: [], skipped: [] };

      // Local overrides shared on filename collision — personal tuning wins.
      const localNames = new Set(localRead.loaded.map((x) => x.name));
      const sharedKept = sharedRead.loaded.filter((x) => !localNames.has(x.name));
      const loaded = [...localRead.loaded, ...sharedKept];
      const skipped = [...localRead.skipped, ...sharedRead.skipped];

      if (loaded.length === 0) {
        timer.end({ status: 'ok', target: skillName, note: `0 valid, ${skipped.length} skipped` });
        process.stdout.write('{}');
        return;
      }

      loaded.sort((a, b) => TYPE_ORDER[a.type] - TYPE_ORDER[b.type]);

      // Display path per entry, relative to cwd when possible, else absolute.
      const relOf = (x) => {
        const rel = path.relative(cwd, path.join(x.dir, x.name));
        return rel.startsWith('..') ? path.join(x.dir, x.name) : rel;
      };

      const totalChars = loaded.reduce((sum, x) => sum + x.body.length, 0);
      let sections;
      if (totalChars > MAX_INJECT_CHARS) {
        // Oversize: reference files only; agent reads on demand to avoid context bloat
        sections = loaded.map((x) => `- [${x.rawType}] ${relOf(x)} (${x.body.length} chars — read this file and apply it)`);
      } else {
        sections = loaded.map((x) => `### [${x.rawType}] ${x.name}\n${x.body}`);
      }

      const sourceDirs = [localExtDir, sharedExtDir]
        .filter(Boolean)
        .map((d) => {
          const rel = path.relative(cwd, d);
          return rel.startsWith('..') ? d : rel;
        });

      const lines = [
        `## Active Extensions for ${skillName} (user-owned, from ${sourceDirs.join(', ')})`,
        'Apply these on top of the skill instructions. Order: pre → override → post. Local overrides shared on name collision.',
        ...sections,
      ];
      if (skipped.length > 0) {
        lines.push(`(Skipped invalid extension files: ${skipped.join(', ')} — check frontmatter extends/type.)`);
      }

      process.stdout.write(
        JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            additionalContext: lines.join('\n\n'),
          },
        })
      );
      timer.end({ status: 'ok', target: skillName, note: `${loaded.length} injected, ${skipped.length} skipped` });
    } catch (error) {
      // Fail-open: extension errors must never block skill activation
      logHookCrash('skill-extension-loader', error, { event: 'PreToolUse', tool: 'Skill' });
      process.stdout.write('{}');
    }
  });
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('skill-extension-loader', e, { event: 'PreToolUse', tool: 'Skill' });
  } catch (_) {}
  process.stdout.write('{}');
  process.exit(0); // fail-open
}
