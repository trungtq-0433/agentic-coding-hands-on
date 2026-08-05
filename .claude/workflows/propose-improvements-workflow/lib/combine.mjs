/**
 * combine.mjs — ESM CLI + pure helper for Step 5a (combine-proposals).
 *
 * Combines the technical + business track proposals into combined-initial.md.
 *
 * PURE API (re-exported for use by workflow scripts):
 *   export function combineProposals({ technicalProposal, businessProposal,
 *     useContext, projectName, dateStr }) => { markdown, warnings }
 *
 * CLI USAGE (mirrors combine_proposals.py exactly):
 *   node lib/combine.mjs \
 *     [--technical-path <path>] \
 *     [--business-path <path>] \
 *     [--use-context-json <path>] \
 *     [--output <path>] \
 *     [--project-name <name>] \
 *     [--date-str <YYYY-MM-DD>]
 *
 * Stdout contract (byte-identical to Python):
 *   - Zero or more `warn:` lines.
 *   - One `done: step-5a → <abs path>` OR `skip: step-5a (artifact exists at <path>)`.
 *   - Exactly one `Status: DONE` | `Status: DONE_WITH_CONCERNS — <reason>`
 *     | `Status: BLOCKED — <reason>`.
 *
 * Exit codes: 0 (DONE / DONE_WITH_CONCERNS / skip), 2 (BLOCKED).
 *
 * FILE-SIZE NOTE (deviates from the repo's <200-line guideline, intentionally):
 * this is a 1:1 behavioural port of combine_lib.py + combine_proposals.py kept in a
 * single module so the pure core and its CLI shim stay traceable to one Python source
 * pair. The pure logic alone exceeds 200 lines; splitting it further would fragment the
 * parity mapping without reducing complexity. Byte-for-byte equivalence with the Python
 * source is locked by __tests__/parity.test.mjs.
 */

import { existsSync, statSync, readFileSync, mkdirSync, writeFileSync, renameSync, unlinkSync, openSync, closeSync } from "node:fs";
import { resolve, dirname, basename, isAbsolute } from "node:path";
import { tmpdir } from "node:os";
import { pathToFileURL } from "node:url";

// ---------------------------------------------------------------------------
// Regex constants (mirroring combine_lib.py)
// ---------------------------------------------------------------------------

/** ATX H1: 0-3 leading spaces, single `#` NOT followed by another `#`. */
const ATX_H1_RE = /^ {0,3}# (?!#)/;

/** ATX H2: 0-3 leading spaces, `##` NOT followed by another `#`. */
const ATX_H2_RE = /^ {0,3}## (?!#)/;

/** ATX H3: 0-3 leading spaces, `###` NOT followed by another `#`. */
const ATX_H3_RE = /^ {0,3}### (?!#)/;

/**
 * Fence opening: 0-3 leading spaces followed by 3+ backticks or 3+ tildes.
 * Captured group is the fence marker (e.g. "```", "~~~~").
 */
const FENCE_OPEN_RE = /^ {0,3}(`{3,}|~{3,})/;

/**
 * Use-context marker: `**Use context:** <value>` where value is one of the
 * three valid contexts. Case-insensitive; allows leading/trailing whitespace.
 */
const USE_CONTEXT_RE = /^\s*\*\*Use context:\*\*\s+(internal|hybrid|customer-facing)\s*$/i;

/**
 * HTML comment line: optional leading/trailing whitespace around `<!-- … -->`.
 * Uses a greedy-to-`-->` match (same semantics as Python's `.*`).
 */
const HTML_COMMENT_LINE_RE = /^\s*<!--.*-->\s*$/;

/** Valid use-context values (lowercase). */
const VALID_USE_CONTEXTS = new Set(["internal", "hybrid", "customer-facing"]);

// ---------------------------------------------------------------------------
// Pure helpers (internal, not exported)
// ---------------------------------------------------------------------------

/**
 * Returns true when `line` is a setext underline (`===…` or `---…`).
 * Mirrors _is_setext_underline in combine_lib.py.
 */
function isSetextUnderline(line) {
  const s = line.trim();
  if (!s) return false;
  if (s[0] !== "=" && s[0] !== "-") return false;
  return [...s].every((ch) => ch === s[0]);
}

/**
 * Joins `lines` starting from index `start`, dropping leading blank lines.
 * Mirrors _trim_leading_blanks in combine_lib.py.
 *
 * @param {string[]} lines
 * @param {number} [start=0]
 * @returns {string}
 */
function trimLeadingBlanks(lines, start = 0) {
  let i = start;
  while (i < lines.length && lines[i].trim() === "") {
    i++;
  }
  return lines.slice(i).join("\n");
}

// ---------------------------------------------------------------------------
// parse_use_context_marker
// ---------------------------------------------------------------------------

/**
 * Scan the header region (first 10 lines or until first `## ` heading) for
 * the `**Use context:** <value>` marker. Returns the lowercase value or null.
 *
 * Mirrors parse_use_context_marker() in combine_lib.py.
 *
 * @param {string} body
 * @returns {string | null}
 */
function parseUseContextMarker(body) {
  const lines = body.split("\n");
  for (let idx = 0; idx < lines.length && idx < 10; idx++) {
    const line = lines[idx];
    if (ATX_H2_RE.test(line)) break;
    const m = line.match(USE_CONTEXT_RE);
    if (m) return m[1].toLowerCase();
  }
  return null;
}

// ---------------------------------------------------------------------------
// strip_h1_and_use_context
// ---------------------------------------------------------------------------

/**
 * Remove the leading H1 (ATX or setext) plus the `**Use context:**` line
 * that follows it, including blank-line padding and an optional surrounding
 * HTML comment immediately above or below the marker.
 *
 * Behaviour mirrors strip_h1_and_use_context() in combine_lib.py.
 *
 * @param {string} body
 * @returns {string}
 */
function stripH1AndUseContext(body) {
  const lines = body.split("\n");
  const n = lines.length;
  let i = 0;

  // Skip leading blank lines.
  while (i < n && lines[i].trim() === "") i++;

  if (i >= n) return body;

  // Try ATX H1 first.
  let strippedH1 = false;
  if (ATX_H1_RE.test(lines[i])) {
    i++;
    strippedH1 = true;
  } else if (i + 1 < n && isSetextUnderline(lines[i + 1])) {
    // Setext: a non-blank text line followed by `===` or `---` underline.
    i += 2;
    strippedH1 = true;
  }

  if (!strippedH1) return body;

  // Optional blank line(s) + optional preceding HTML comment + use-context
  // line + optional trailing HTML comment.
  let j = i;
  while (j < n && lines[j].trim() === "") j++;

  let preComment = -1;
  if (
    j < n &&
    HTML_COMMENT_LINE_RE.test(lines[j]) &&
    !lines[j].toLowerCase().includes("use context")
  ) {
    preComment = j;
    j++;
    while (j < n && lines[j].trim() === "") j++;
  }

  if (j < n && USE_CONTEXT_RE.test(lines[j])) {
    const useCtxLine = j;
    j++;

    // Optional trailing comment IMMEDIATELY after the marker (no blank in
    // between). The template emits marker + comment on adjacent lines; a
    // blank-separated comment is treated as document content and passes
    // through verbatim per the "HTML comments pass through" rule.
    let postComment = -1;
    if (
      j < n &&
      HTML_COMMENT_LINE_RE.test(lines[j]) &&
      !lines[j].toLowerCase().includes("use context")
    ) {
      postComment = j;
    }

    // Build set of line indices to drop.
    const drop = new Set();
    // H1 + leading blanks (indices 0..i-1).
    for (let x = 0; x < i; x++) drop.add(x);
    // Blanks between H1 and (comment|use-context) + use-context region.
    for (let x = i; x < j; x++) drop.add(x);
    if (preComment >= 0) drop.add(preComment);
    drop.add(useCtxLine);
    if (postComment >= 0) drop.add(postComment);

    const kept = lines.filter((_, idx) => !drop.has(idx));
    return trimLeadingBlanks(kept);
  }

  // H1 stripped but no use-context line — drop H1 only, keep rest.
  return trimLeadingBlanks(lines, i);
}

// ---------------------------------------------------------------------------
// demote_headings (two-pass, fence-aware)
// ---------------------------------------------------------------------------

/**
 * Run one heading-demotion pass over the body, skipping fenced code regions.
 *
 * Mirrors _demote_pass() in combine_lib.py.
 *
 * @param {string} body
 * @param {RegExp} pattern
 * @param {string} oldPrefix
 * @param {string} newPrefix
 * @returns {string}
 */
function demotePass(body, pattern, oldPrefix, newPrefix) {
  const lines = body.split("\n");
  /** @type {string | null} */
  let fenceChar = null;
  let fenceLen = 0;
  const out = [];

  for (const line of lines) {
    if (fenceChar === null) {
      const fm = line.match(FENCE_OPEN_RE);
      if (fm) {
        const marker = fm[1];
        fenceChar = marker[0];
        fenceLen = marker.length;
        out.push(line);
        continue;
      }
      if (pattern.test(line)) {
        const stripped = line.replace(/^ +/, "");
        const leadWs = line.slice(0, line.length - stripped.length);
        out.push(`${leadWs}${newPrefix}${stripped.slice(oldPrefix.length)}`);
      } else {
        out.push(line);
      }
    } else {
      // Inside a fence — look for matching close.
      const cm = line.match(FENCE_OPEN_RE);
      if (cm) {
        const marker = cm[1];
        if (marker[0] === fenceChar && marker.length >= fenceLen) {
          fenceChar = null;
          fenceLen = 0;
        }
      }
      out.push(line);
    }
  }

  // Preserve trailing newline behaviour of input.
  const suffix = body.endsWith("\n") ? "\n" : "";
  return out.join("\n") + suffix;
}

/**
 * Apply heading demotion in strict two-pass order:
 *   Pass A: `### <title>` H3 → `#### <title>` H4
 *   Pass B: `## <title>`  H2 → `### <title>`  H3
 *
 * Mirrors demote_headings() in combine_lib.py.
 *
 * @param {string} body
 * @returns {string}
 */
function demoteHeadings(body) {
  const afterA = demotePass(body, ATX_H3_RE, "###", "####");
  return demotePass(afterA, ATX_H2_RE, "##", "###");
}

// ---------------------------------------------------------------------------
// prepareTrackBody
// ---------------------------------------------------------------------------

/**
 * Strip H1 + use-context line, then demote headings (H3→H4 then H2→H3).
 * Mirrors prepare_track_body() in combine_lib.py.
 *
 * @param {string} raw
 * @returns {string}
 */
function prepareTrackBody(raw) {
  return demoteHeadings(stripH1AndUseContext(raw));
}

// ---------------------------------------------------------------------------
// resolveUseContextFromJson
// ---------------------------------------------------------------------------

/**
 * Extract validated useContext string from a parsed JSON object.
 * Returns null when the object is invalid or value is not a known context.
 *
 * Mirrors _read_use_context_json() in combine_proposals.py (without I/O).
 *
 * @param {unknown} data
 * @returns {string | null}
 */
function resolveUseContextFromJson(data) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    return null;
  }
  const val = /** @type {Record<string, unknown>} */ (data)["useContext"];
  if (typeof val === "string" && VALID_USE_CONTEXTS.has(val.toLowerCase())) {
    return val.toLowerCase();
  }
  return null;
}

// ---------------------------------------------------------------------------
// buildCombined
// ---------------------------------------------------------------------------

/**
 * Assemble the final combined markdown per spec Procedure step 6.
 * Mirrors build_combined() in combine_lib.py.
 *
 * @param {object} opts
 * @param {string} opts.projectName
 * @param {string} opts.isoDate
 * @param {string | null} opts.useContext
 * @param {string | null} opts.techBody
 * @param {string | null} opts.bizBody
 * @returns {string}
 */
function buildCombined({ projectName, isoDate, useContext, techBody, bizBody }) {
  if (!techBody && !bizBody) {
    throw new TypeError("BLOCKED — at least one of techBody / bizBody must be provided");
  }

  const parts = [];
  parts.push(`# Improvement Proposal — ${projectName}`);
  parts.push("");

  if (useContext) {
    parts.push(
      `_Generated ${isoDate}. Use context: **${useContext}**. Based on repository analysis._`
    );
  } else {
    parts.push(`_Generated ${isoDate}. Based on repository analysis._`);
  }
  parts.push("");

  if (techBody !== null) {
    parts.push("## Technical");
    parts.push("");
    parts.push(techBody.replace(/\n+$/, ""));
    parts.push("");
  }

  if (bizBody !== null) {
    parts.push("## Business");
    parts.push("");
    parts.push(bizBody.replace(/\n+$/, ""));
    parts.push("");
  }

  parts.push("<!-- dedup: pending -->");
  return parts.join("\n") + "\n";
}

// ---------------------------------------------------------------------------
// Public API — combineProposals
// ---------------------------------------------------------------------------

/**
 * Combine a technical-track proposal and/or a business-track proposal into
 * the `combined-initial.md` content string.
 *
 * @param {object} opts
 * @param {string | null} opts.technicalProposal
 * @param {string | null} opts.businessProposal
 * @param {object | null} opts.useContext
 * @param {string} opts.projectName
 * @param {string} opts.dateStr
 *
 * @returns {{ markdown: string, warnings: string[] }}
 * @throws {TypeError} with message starting "BLOCKED — "
 */
export function combineProposals({
  technicalProposal,
  businessProposal,
  useContext,
  projectName,
  dateStr,
}) {
  // Step 1a — at least one track must be provided (non-null).
  if (technicalProposal === null && businessProposal === null) {
    throw new TypeError("BLOCKED — no track proposal provided");
  }

  const provided = [
    technicalProposal !== null ? ["technical", technicalProposal] : null,
    businessProposal !== null ? ["business", businessProposal] : null,
  ].filter(Boolean);

  const nonEmpty = provided.filter(([, raw]) => raw !== null && raw.trim() !== "");

  if (nonEmpty.length === 0) {
    throw new TypeError("BLOCKED — provided track proposal(s) missing/empty");
  }

  // Step 3 — resolve effective use_context from the JSON object.
  const jsonUseCtx = resolveUseContextFromJson(useContext);

  // Step 4 — parse + cross-check use-context markers.
  const warnings = [];
  /** @type {Record<string, string | null>} */
  const trackMarkers = {};
  for (const [name, raw] of nonEmpty) {
    trackMarkers[name] = parseUseContextMarker(raw);
  }

  // Cross-track divergence check (only when both tracks provided).
  if ("technical" in trackMarkers && "business" in trackMarkers) {
    const tM = trackMarkers["technical"];
    const bM = trackMarkers["business"];
    if (tM && bM && tM !== bM) {
      warnings.push(
        `warn: step-5a use-context divergence — technical=${tM}, business=${bM}`
      );
    }
  }

  // Per-track disagreement with use-context.json.
  if (jsonUseCtx !== null) {
    for (const [name, marker] of Object.entries(trackMarkers)) {
      if (marker && marker !== jsonUseCtx) {
        warnings.push(
          `warn: step-5a ${name} marker disagrees with use-context.json — ${name}=${marker}, json=${jsonUseCtx}`
        );
      }
    }
  }

  // Resolve effective use_context for the header badge.
  let effectiveUseContext;
  if (jsonUseCtx !== null) {
    effectiveUseContext = jsonUseCtx;
  } else {
    const markers = Object.values(trackMarkers).filter(Boolean);
    const uniqueMarkers = new Set(markers);
    effectiveUseContext =
      markers.length > 0 && uniqueMarkers.size === 1 ? markers[0] : null;
  }

  // Step 5 — per-track: strip H1 + use-context, demote headings.
  const techBody =
    technicalProposal !== null && technicalProposal.trim()
      ? prepareTrackBody(technicalProposal)
      : null;
  const bizBody =
    businessProposal !== null && businessProposal.trim()
      ? prepareTrackBody(businessProposal)
      : null;

  // Step 6 — build combined output.
  const markdown = buildCombined({
    projectName,
    isoDate: dateStr,
    useContext: effectiveUseContext,
    techBody,
    bizBody,
  });

  return { markdown, warnings };
}

// ---------------------------------------------------------------------------
// CLI shim — mirrors combine_proposals.py main()
// ---------------------------------------------------------------------------

/**
 * Validate that `pathStr` is safe: no null bytes, no `..` segments, not
 * absolute outside plans/. Mirrors combine_lib.validate_paths() logic.
 *
 * @param {string} pathStr
 * @param {string} plansRoot  — absolute path to plans/
 * @param {"output"|"input"} role
 * @returns {{ ok: boolean, reason: string }}
 */
function validatePath(pathStr, plansRoot, role) {
  if (pathStr.includes("\x00")) {
    return { ok: false, reason: `null byte in path: ${JSON.stringify(pathStr)}` };
  }
  // Deliberately conservative substring check (mirrors combine_lib.validate_paths):
  // rejects any `..` occurrence, not just a `..` path segment. Workflow artifact
  // paths are fully workflow-controlled and never contain `..`, so the rare
  // false-positive (e.g. a filename like `release..notes.md`) is an acceptable
  // trade for keeping the traversal guard dead-simple and Python-parity-identical.
  if (pathStr.includes("..")) {
    return { ok: false, reason: `path traversal (..) in: ${JSON.stringify(pathStr)}` };
  }
  if (isAbsolute(pathStr)) {
    const resolved = resolve(pathStr);
    if (!resolved.startsWith(plansRoot + "/") && resolved !== plansRoot) {
      return { ok: false, reason: `absolute path escapes plans/: ${pathStr}` };
    }
  }
  if (role === "output") {
    const resolved = resolve(pathStr);
    if (!resolved.startsWith(plansRoot + "/") && resolved !== plansRoot) {
      return { ok: false, reason: `output_path escapes plans/: ${pathStr}` };
    }
  }
  return { ok: true, reason: "" };
}

/**
 * Atomic write: write `content` to `targetPath` via tempfile + rename.
 * Mirrors _atomic_write() in combine_proposals.py.
 *
 * @param {string} targetPath  — absolute path
 * @param {string} content
 */
function atomicWrite(targetPath, content) {
  const dir = dirname(targetPath);
  mkdirSync(dir, { recursive: true });
  const tmpPath = `${targetPath}.${process.pid}.${Date.now()}.tmp`;
  try {
    writeFileSync(tmpPath, content, "utf-8");
    renameSync(tmpPath, targetPath);
  } catch (err) {
    try { unlinkSync(tmpPath); } catch { /* best-effort */ }
    throw err;
  }
}

/**
 * Parse a minimal set of CLI args matching combine_proposals.py's argparse.
 * Returns { technicalPath, businessPath, useContextJson, output, projectName }
 * or throws on unknown/missing required args.
 *
 * @param {string[]} argv  — process.argv.slice(2)
 */
function parseArgs(argv) {
  const result = {
    technicalPath: null,
    businessPath: null,
    useContextJson: "plans/improvement-proposal/use-context.json",
    output: "plans/improvement-proposal/combined-initial.md",
    projectName: null,
    dateStr: null,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--technical-path") { result.technicalPath = next; i++; }
    else if (arg === "--business-path") { result.businessPath = next; i++; }
    else if (arg === "--use-context-json") { result.useContextJson = next; i++; }
    else if (arg === "--output") { result.output = next; i++; }
    else if (arg === "--project-name") { result.projectName = next; i++; }
    else if (arg === "--date-str") { result.dateStr = next; i++; }
    else {
      process.stderr.write(`combine.mjs: unrecognised argument: ${arg}\n`);
      process.exit(2);
    }
  }
  return result;
}

/**
 * Print the Status trailer (matching Python's _print_status exactly).
 * @param {string} status
 * @param {string} [reason]
 */
function printStatus(status, reason = "") {
  if (reason) {
    process.stdout.write(`Status: ${status} — ${reason}\n`);
  } else {
    process.stdout.write(`Status: ${status}\n`);
  }
}

/**
 * Read a file at `pathStr` (relative or absolute); return null if pathStr is
 * null, or "" if file does not exist. Mirrors _read_or_none() in Python.
 *
 * @param {string | null} pathStr
 * @returns {string | null}
 */
function readOrNone(pathStr) {
  if (pathStr === null) return null;
  if (!existsSync(pathStr)) return "";
  return readFileSync(pathStr, "utf-8");
}

/**
 * Read use-context.json; return parsed object (with useContext key) or null.
 * Mirrors _read_use_context_json() in combine_proposals.py.
 *
 * @param {string} pathStr
 * @returns {object | null}
 */
function readUseContextJson(pathStr) {
  if (!existsSync(pathStr)) return null;
  let data;
  try {
    data = JSON.parse(readFileSync(pathStr, "utf-8"));
  } catch {
    return null;
  }
  if (data === null || typeof data !== "object" || Array.isArray(data)) return null;
  const val = data["useContext"];
  if (typeof val === "string" && VALID_USE_CONTEXTS.has(val.toLowerCase())) {
    return data;
  }
  return null;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  // Procedure step 1(a) — at least one track required.
  if (args.technicalPath === null && args.businessPath === null) {
    printStatus("BLOCKED", "no track proposal provided");
    process.exit(2);
  }

  // Path-safety — reject null bytes + traversal.
  const plansRoot = resolve("plans");
  const pathChecks = [
    [args.output, "output"],
    [args.technicalPath, "input"],
    [args.businessPath, "input"],
    [args.useContextJson, "input"],
  ].filter(([p]) => p !== null);

  for (const [pathStr, role] of pathChecks) {
    const check = validatePath(pathStr, plansRoot, role);
    if (!check.ok) {
      printStatus("BLOCKED", `path-safety violation: ${check.reason}`);
      process.exit(2);
    }
  }

  // Idempotency — skip when output already non-empty.
  const outputAbs = resolve(args.output);
  if (existsSync(outputAbs)) {
    const st = statSync(outputAbs);
    if (st.size > 0) {
      process.stdout.write(`skip: step-5a (artifact exists at ${args.output})\n`);
      printStatus("DONE");
      process.exit(0);
    }
  }

  // Read each provided track.
  const techRaw = readOrNone(args.technicalPath);
  const bizRaw = readOrNone(args.businessPath);

  // Procedure step 1(b) — all provided paths empty/missing → BLOCKED.
  const provided = [
    techRaw !== null ? ["technical", techRaw] : null,
    bizRaw !== null ? ["business", bizRaw] : null,
  ].filter(Boolean);
  const nonEmpty = provided.filter(([, raw]) => raw !== null && raw.trim() !== "");
  if (nonEmpty.length === 0) {
    printStatus("BLOCKED", "provided track proposal(s) missing/empty");
    process.exit(2);
  }

  // Procedure step 3 — use-context.json (optional source of truth).
  const useContextData = readUseContextJson(args.useContextJson);

  // combineProposals handles steps 4-6.
  let markdown, warnings;
  try {
    ({ markdown, warnings } = combineProposals({
      technicalProposal: techRaw,
      businessProposal: bizRaw,
      useContext: useContextData,
      projectName: args.projectName || basename(resolve(".")),
      // Prefer the caller-supplied date (the workflow resolves it once at Preflight
      // via `date +%F` and passes --date-str) so the proposal header date is the
      // run's canonical date. Fall back to today's date for standalone CLI use.
      dateStr: args.dateStr || new Date().toISOString().slice(0, 10),
    }));
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    printStatus("BLOCKED", msg.replace(/^BLOCKED\s*[—-]\s*/, ""));
    process.exit(2);
  }

  // Procedure step 7 — atomic write.
  atomicWrite(outputAbs, markdown);

  // Emit warns, done, status.
  for (const w of warnings) {
    process.stdout.write(`${w}\n`);
  }
  process.stdout.write(`done: step-5a → ${outputAbs}\n`);
  if (warnings.length > 0) {
    const reason = warnings.map((w) => w.replace(/^warn:\s*/, "")).join("; ");
    printStatus("DONE_WITH_CONCERNS", reason);
  } else {
    printStatus("DONE");
  }
  process.exit(0);
}

// Guard: only run CLI when this module is the entry point.
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  main().catch((err) => {
    process.stderr.write(`combine.mjs: fatal: ${err?.message ?? err}\n`);
    process.exit(2);
  });
}
