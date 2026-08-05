'use strict';

/**
 * evidence-validator — the deterministic heart of the Takumi quality gate.
 *
 * Reads a plan's {plan}/evidence/ directory and decides whether the work has
 * earned "done": schema + policy + anti-faking, all in code. This module is the
 * SINGLE SOURCE OF TRUTH (the contract doc at
 * skills/_shared/references/evidence-artifacts.md follows this, not the reverse).
 *
 * No external dependencies — Node built-ins only, so `node --test` runs it with nothing installed.
 * Pure: given a directory it returns a verdict, touches nothing else.
 * Two stages:
 *   hard     — ship/PR + takumi Deliver + fix-bug commit. Real violations BLOCK.
 *   advisory — everywhere else. The same checks, downgraded to warnings.
 * The secret-scan is advisory at BOTH stages (most false-positive-prone; files are
 * guarded at another layer by privacy-block).
 */

const fs = require('node:fs');
const path = require('node:path');
const { checkVerdictFindings } = require('./verdict-findings-location.cjs');
const { checkVerdictRiskGate } = require('./verdict-risk-gate.cjs');

// Known keys — anything else in an artifact is an injected/extra key (blocks).
const STUDY_KEYS = new Set(['task', 'mode', 'acceptanceCriteria', 'touchpoints', 'blastRadius', 'contracts']);
const TEMPER_CMD_KEYS = new Set(['command', 'exitCode', 'status', 'summary', 'ts']);
const VERDICT_KEYS = new Set(['score', 'criticalCount', 'decision', 'acceptanceCovered', 'regressionChecked', 'contractStatus', 'refuted', 'unproven', 'reachableRegressions', 'findings', 'riskGate']);

// Value-level secret patterns. Advisory only — these warn, they never block.
const SECRET_PATTERNS = [
  ['AWS access key', /\bAKIA[0-9A-Z]{16}\b/],
  ['GitHub token', /\bgh[posu]_[A-Za-z0-9]{20,}\b/],
  ['OpenAI key', /\bsk-[A-Za-z0-9]{20,}\b/],
  ['Slack token', /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/],
  ['private key block', /-----BEGIN [A-Z ]*PRIVATE KEY-----/],
  ['JWT', /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\./],
];

function readJson(file) {
  try {
    const obj = JSON.parse(fs.readFileSync(file, 'utf8'));
    // A JSON primitive (null, number, string) or array is not a valid artifact.
    // Reject it as a parse-style failure so it BLOCKS rather than crashing the
    // checks downstream (which would fail the gate open — an anti-faking hole).
    if (obj === null || typeof obj !== 'object' || Array.isArray(obj)) {
      return { parseError: 'not a JSON object' };
    }
    return { obj };
  } catch (err) {
    return err.code === 'ENOENT' ? { missing: true } : { parseError: err.message };
  }
}

function extraKeys(obj, allowed) {
  return Object.keys(obj || {}).filter((k) => !allowed.has(k));
}

function isInt(n) { return typeof n === 'number' && Number.isInteger(n); }

function emptyArr(v) { return Array.isArray(v) && v.length === 0; }

/** Recursively collect every string value, with a dotted path, for the secret scan. */
function collectStrings(node, prefix, out) {
  if (typeof node === 'string') {
    out.push([prefix, node]);
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => collectStrings(v, `${prefix}[${i}]`, out));
  } else if (node && typeof node === 'object') {
    for (const k of Object.keys(node)) collectStrings(node[k], prefix ? `${prefix}.${k}` : k, out);
  }
}

function scanSecrets(artifacts) {
  const warnings = [];
  const strings = [];
  for (const [name, obj] of artifacts) collectStrings(obj, name, strings);
  for (const [where, value] of strings) {
    for (const [label, re] of SECRET_PATTERNS) {
      if (re.test(value)) warnings.push(`possible secret (${label}) in ${where} — redact before shipping`);
    }
  }
  return warnings;
}

/** Code constructs temper-results from captured runs so exitCode is ALWAYS an int. */
function buildTemperResults(rawRuns) {
  const commands = (rawRuns || []).map((run) => {
    const exitCode = Number.isFinite(Number(run.exitCode)) ? Math.trunc(Number(run.exitCode)) : 1;
    const status = run.status || (exitCode === 0 ? 'pass' : 'fail');
    const firstLine = String(run.stdout || '').split('\n').find((l) => l.trim()) || '';
    const summary = (run.summary && String(run.summary)) || firstLine || `${run.command} → exit ${exitCode}`;
    return { command: String(run.command || ''), exitCode, status, summary, ts: run.ts || new Date(0).toISOString() };
  });
  return { commands };
}

function checkStudy(study, V) {
  if (study.missing) return V('study-context.json is missing — no brief to inspect against');
  if (study.parseError) return V(`study-context.json is not valid JSON: ${study.parseError}`);
  const o = study.obj;
  for (const k of extraKeys(o, STUDY_KEYS)) V(`study-context.json has an unknown/extra key: ${k}`);
  if (!o.task || !String(o.task).trim()) V('study-context.json has an empty task');
  if (!Array.isArray(o.acceptanceCriteria) || o.acceptanceCriteria.length === 0) V('study-context.json has no acceptanceCriteria — "done" is unfalsifiable');
}

function checkTemper(temperFiles, V) {
  if (temperFiles.length === 0) return V('no temper-results*.json — nothing was tempered');
  let anyPass = false;
  for (const { name, res } of temperFiles) {
    if (res.parseError) { V(`${name} is not valid JSON: ${res.parseError}`); continue; }
    const cmds = res.obj && res.obj.commands;
    if (!Array.isArray(cmds) || cmds.length === 0) { V(`${name} has no commands`); continue; }
    for (const c of cmds) {
      for (const k of extraKeys(c, TEMPER_CMD_KEYS)) V(`${name}: command has an unknown/extra key: ${k}`);
      if (!c.command || !String(c.command).trim()) V(`${name}: a command entry is empty`);
      if (!isInt(c.exitCode)) V(`${name}: exitCode must be an integer, got ${JSON.stringify(c.exitCode)}`);
      if (!['pass', 'fail', 'skipped'].includes(c.status)) V(`${name}: invalid status ${JSON.stringify(c.status)}`);
      if (!c.summary || !String(c.summary).trim()) V(`${name}: a command has an empty summary`);
      if (c.status === 'fail') V(`${name}: command failed (${c.command}) — cannot ship over a red test`);
      // status must agree with exitCode — a 'pass' over a non-zero exit is a forged green.
      if (c.status === 'pass' && isInt(c.exitCode) && c.exitCode !== 0) V(`${name}: command (${c.command}) claims status:pass but exitCode is ${c.exitCode} — inconsistent`);
      if (c.status === 'fail' && isInt(c.exitCode) && c.exitCode === 0) V(`${name}: command (${c.command}) claims status:fail but exitCode is 0 — inconsistent`);
      if (c.status === 'pass' && isInt(c.exitCode) && c.exitCode === 0) anyPass = true;
    }
  }
  if (!anyPass) V('no temper command with status:pass — no proof anything ran green');
}

/** Normalize a string for lenient criterion matching (case + whitespace). */
function norm(s) {
  return String(s).toLowerCase().replace(/\s+/g, ' ').trim();
}

function checkVerdict(verdict, V, W, studyObj) {
  if (verdict.missing) return V('inspection-verdict.json is missing — the work was never inspected');
  if (verdict.parseError) return V(`inspection-verdict.json is not valid JSON: ${verdict.parseError}`);
  const o = verdict.obj;
  for (const k of extraKeys(o, VERDICT_KEYS)) V(`inspection-verdict.json has an unknown/extra key: ${k}`);

  // Subset check: every acceptance criterion from the brief must be echoed by an
  // acceptanceCovered entry — proof maps back to what was promised, not vibes.
  const criteria = studyObj && Array.isArray(studyObj.acceptanceCriteria) ? studyObj.acceptanceCriteria : [];
  if (Array.isArray(o.acceptanceCovered) && criteria.length) {
    const covered = o.acceptanceCovered.map(norm);
    for (const c of criteria) {
      const nc = norm(c);
      if (nc && !covered.some((e) => e.includes(nc))) V(`inspection-verdict acceptanceCovered does not cover the criterion: "${c}" — echo the criterion text in the entry that proves it`);
    }
  }
  if (o.decision !== 'SEALED') V(`inspection-verdict decision is ${JSON.stringify(o.decision)} — only SEALED passes (score never seals by itself)`);
  if (!isInt(o.criticalCount) || o.criticalCount !== 0) V(`inspection-verdict criticalCount must be 0, got ${JSON.stringify(o.criticalCount)}`);
  if (!Array.isArray(o.acceptanceCovered) || o.acceptanceCovered.length === 0) V('inspection-verdict acceptanceCovered is empty — no acceptance criteria were proven');
  if (!Array.isArray(o.regressionChecked) || o.regressionChecked.length === 0) V('inspection-verdict regressionChecked is empty — no blast-radius was walked');
  if (!emptyArr(o.refuted)) V('inspection-verdict has refuted claims — the adversarial pass disproved something');
  if (!emptyArr(o.unproven)) V('inspection-verdict has unproven claims — asserted but not demonstrated');
  if (!emptyArr(o.reachableRegressions)) V('inspection-verdict has reachableRegressions — a regression is reachable');
  if (o.contractStatus === 'UNKNOWN' || o.contractStatus == null) V('inspection-verdict contractStatus is UNKNOWN — an unexamined contract is not a passed one');
  checkVerdictFindings(o.findings, V, W);
  checkVerdictRiskGate(o.riskGate, V);
}

/** Validate a plan's evidence directory. Returns {ok, blocking[], warnings[], stage}. */
function validateEvidence({ evidenceDir, stage }) {
  const hard = stage === 'hard';
  const violations = []; const V = (msg) => violations.push(msg);
  const advisories = []; const W = (msg) => advisories.push(msg);

  const study = readJson(path.join(evidenceDir, 'study-context.json'));
  const verdict = readJson(path.join(evidenceDir, 'inspection-verdict.json'));

  let temperNames = [];
  try {
    // Match temper-results.json and per-instance temper-results-<label>.json, but
    // never a raw-runs sidecar (those are bare arrays the tester drops for the code
    // to construct from — matching them would false-block).
    temperNames = fs.readdirSync(evidenceDir).filter((f) => /^temper-results.*\.json$/.test(f) && !/raw/i.test(f));
  } catch { /* dir missing → handled as no temper files */ }
  const temperFiles = temperNames.map((name) => ({ name, res: readJson(path.join(evidenceDir, name)) }));

  checkStudy(study, V);
  checkTemper(temperFiles, V);
  checkVerdict(verdict, V, W, study.obj);

  const artifacts = [];
  if (study.obj) artifacts.push(['study-context.json', study.obj]);
  if (verdict.obj) artifacts.push(['inspection-verdict.json', verdict.obj]);
  for (const { name, res } of temperFiles) if (res.obj) artifacts.push([name, res.obj]);
  const secretWarnings = scanSecrets(artifacts);

  const blocking = hard ? violations.slice() : [];
  const warnings = (hard ? secretWarnings : violations.concat(secretWarnings)).concat(advisories);
  return { ok: blocking.length === 0, blocking, warnings, stage: stage || 'advisory' };
}

module.exports = { validateEvidence, buildTemperResults };
