/**
 * phase-d-prep.mjs — ESM CLI + pure helper for Step 5c (validation prep).
 *
 * Splits combined-initial.md into one per-item validation payload JSON + a
 * _manifest.json. Each payload carries ONLY the proposal item (the item's
 * markdown); the validator self-verifies it against the real repo and writes a
 * verdict per templates/validation-item.md. The manifest tells the orchestrator
 * how many items exist and where each verdict goes (the workflow sandbox has no
 * filesystem access, so it relies on this manifest to drive the validation
 * fan-out).
 *
 * PURE API (re-exported for use by workflow scripts + unit tests):
 *   export function buildPhaseDPayloads({ combinedMarkdown })
 *     => { payloads, manifest }
 *
 * CLI USAGE:
 *   node lib/phase-d-prep.mjs \
 *     --combined-path <path> \
 *     --payloads-dir <dir> \
 *     --manifest-path <path> \
 *     --validation-dir <dir>
 *
 * Stdout contract:
 *   - One `done: step-5c → <abs manifest>` or `skip: step-5c (artifact exists)`.
 *   - Exactly one `Status: DONE` | `Status: BLOCKED — <reason>` trailer.
 *
 * Exit codes: 0 (DONE / skip), 2 (BLOCKED).
 */

import { createHash } from "node:crypto";
import {
  existsSync,
  statSync,
  readFileSync,
  readdirSync,
  mkdirSync,
  writeFileSync,
  renameSync,
  unlinkSync,
} from "node:fs";
import { resolve, join, dirname } from "node:path";
import { pathToFileURL } from "node:url";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEDUP_APPLIED_MARKER = "<!-- dedup: applied";

// ---------------------------------------------------------------------------
// Regex
// ---------------------------------------------------------------------------

const FENCE_OPEN_RE = /^[ ]{0,3}(`{3,}|~{3,})/;
const ATX_H2_RE = /^[ ]{0,3}## (?!#)/;
const ATX_H4_RE = /^[ ]{0,3}#### (?!#)/;
const SLUG_VALIDATE_RE = /^[a-z0-9][a-z0-9\-]*$/;

// ---------------------------------------------------------------------------
// SHA-256
// ---------------------------------------------------------------------------

/**
 * Compute sha256 hex digest of a UTF-8 string.
 * @param {string} text
 * @returns {string}
 */
function computeSha256(text) {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

// ---------------------------------------------------------------------------
// Slug + validation helpers
// ---------------------------------------------------------------------------

/**
 * Convert a title string to a kebab-slug.
 * @param {string} title
 * @returns {string}
 */
function titleToSlug(title) {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || "untitled";
}

/**
 * Filename slug must match ^[a-z0-9][a-z0-9\-]*$
 * @param {string} slug
 * @returns {boolean}
 */
function validateFilenameSlug(slug) {
  return SLUG_VALIDATE_RE.test(slug);
}

// ---------------------------------------------------------------------------
// Fence-aware parser state helpers
// ---------------------------------------------------------------------------

/**
 * @typedef {{ inFence: boolean, fenceChar: string, fenceLen: number }} FenceState
 */

/** @returns {FenceState} */
function newFenceState() {
  return { inFence: false, fenceChar: "", fenceLen: 0 };
}

/**
 * Process a single line through the fence-state machine.
 * Returns true if the line is INSIDE a fence (or is a fence marker) and should
 * be skipped for heading detection, false for a normal content line.
 *
 * @param {string} line
 * @param {FenceState} state
 * @returns {boolean}
 */
function processFenceLine(line, state) {
  if (state.inFence) {
    const m = FENCE_OPEN_RE.exec(line);
    if (m && m[1][0] === state.fenceChar && m[1].length >= state.fenceLen) {
      state.inFence = false;
    }
    return true;
  }
  const fm = FENCE_OPEN_RE.exec(line);
  if (fm) {
    state.inFence = true;
    state.fenceChar = fm[1][0];
    state.fenceLen = fm[1].length;
    return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Item walker (fence-aware)
// ---------------------------------------------------------------------------

/**
 * @typedef {{ index: number, title: string, slug: string, track: string, body: string, lineNo: number }} Item
 */

/**
 * Walk combined-initial.md fence-aware. Collect each `#### <title>` block and
 * tag it with its enclosing `## Technical` / `## Business` parent. Item indices
 * are 1-based in document order. Items outside a Technical/Business section are
 * ignored (combine.mjs only emits active-track sections, so every real item is
 * always under one of the two).
 *
 * @param {string} combinedText
 * @returns {Item[]}
 */
function parseItems(combinedText) {
  const lines = combinedText.split("\n");
  const fence = newFenceState();

  /** @type {Item[]} */
  const items = [];
  /** @type {string|null} */
  let currentTrack = null;
  /** @type {number|null} */
  let blockStart = null;
  let blockTitle = "";

  function flush(endLine) {
    if (blockStart === null) return;
    const body = lines.slice(blockStart, endLine).join("\n").replace(/\n+$/, "");
    if (currentTrack === null) {
      blockStart = null;
      return;
    }
    items.push({
      index: items.length + 1,
      title: blockTitle,
      slug: titleToSlug(blockTitle),
      track: currentTrack,
      body,
      lineNo: blockStart,
    });
    blockStart = null;
    blockTitle = "";
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (processFenceLine(line, fence)) continue;

    if (ATX_H2_RE.test(line)) {
      flush(i);
      const stripped = line.replace(/^[ ]*#+/, "").trim().toLowerCase();
      if (stripped.startsWith("technical")) {
        currentTrack = "technical";
      } else if (stripped.startsWith("business")) {
        currentTrack = "business";
      } else {
        currentTrack = null;
      }
      continue;
    }

    if (ATX_H4_RE.test(line)) {
      flush(i);
      blockTitle = line.replace(/^[ ]*#+/, "").trim();
      blockStart = i;
      continue;
    }
  }

  flush(lines.length);
  return items;
}

// ---------------------------------------------------------------------------
// Item markdown rewrite
// ---------------------------------------------------------------------------

/**
 * Rewrite the leading `^ {0,3}#### <title>` → `## <title>` (first occurrence
 * only) so the validator sees the item as a standalone H2 document.
 * @param {string} itemBody
 * @returns {string}
 */
function rewriteH4ToH2(itemBody) {
  return itemBody.replace(/^([ ]{0,3})#### /, (_, spaces) => `${spaces}## `);
}

// ---------------------------------------------------------------------------
// Last non-blank line helper
// ---------------------------------------------------------------------------

/**
 * Return the last non-blank line of a text string.
 * @param {string} text
 * @returns {string}
 */
function lastNonBlankLine(text) {
  const lines = text.split("\n");
  for (let i = lines.length - 1; i >= 0; i--) {
    if (lines[i].trim()) return lines[i];
  }
  return "";
}

// ---------------------------------------------------------------------------
// Main exported pure function
// ---------------------------------------------------------------------------

/**
 * Build Phase-D payloads + manifest from combined-initial.md.
 *
 * Each payload carries only the proposal item markdown. The manifest carries
 * the per-item index/slug/track + bare payload/output filenames (the CLI shim
 * resolves them to absolute paths before writing).
 *
 * @param {object} opts
 * @param {string} opts.combinedMarkdown
 * @returns {{
 *   payloads: Array<{ filename: string, json: object }>,
 *   manifest: object
 * }}
 * @throws {Error} when combined-initial.md is not finalised by step-5b, or an
 *   item slug is invalid.
 */
export function buildPhaseDPayloads({ combinedMarkdown }) {
  // Gate: combined-initial.md must be finalised by step-5b (dedup applied).
  if (!lastNonBlankLine(combinedMarkdown).startsWith(DEDUP_APPLIED_MARKER)) {
    throw new Error("combined-initial.md not finalised by step-5b");
  }

  const combinedSha256 = computeSha256(combinedMarkdown);
  const items = parseItems(combinedMarkdown);

  const payloads = [];
  const manifestItems = [];

  for (const it of items) {
    if (!validateFilenameSlug(it.slug)) {
      throw new Error(`invalid slug for item-${it.index}: ${JSON.stringify(it.slug)}`);
    }

    const nn = String(it.index).padStart(2, "0");
    const payloadFilename = `item-${nn}-${it.slug}.json`;
    const outputFilename = `item-${nn}-${it.slug}.md`;

    // Payload = the proposal item, nothing more. schema_version guards against a
    // future shape the validator wouldn't understand.
    payloads.push({
      filename: payloadFilename,
      json: {
        schema_version: 1,
        item_markdown: rewriteH4ToH2(it.body),
      },
    });

    manifestItems.push({
      item_index: it.index,
      item_slug: it.slug,
      track: it.track,
      payload_path: payloadFilename,
      output_path: outputFilename,
    });
  }

  const manifest = {
    schema_version: 1,
    combined_md_sha256: combinedSha256,
    items: manifestItems,
  };

  return { payloads, manifest };
}

// ---------------------------------------------------------------------------
// Re-exports for test access to internal helpers
// ---------------------------------------------------------------------------

export {
  titleToSlug,
  validateFilenameSlug,
  parseItems,
  rewriteH4ToH2,
  computeSha256,
  lastNonBlankLine,
  DEDUP_APPLIED_MARKER,
};

// ---------------------------------------------------------------------------
// CLI helpers
// ---------------------------------------------------------------------------

/**
 * Atomic write of a JSON object to `targetPath` (tempfile + rename).
 * Serialization: JSON.stringify(obj, null, 2) + "\n".
 *
 * @param {string} targetPath — absolute path
 * @param {object} payload
 */
function atomicWriteJson(targetPath, payload) {
  const dir = dirname(targetPath);
  mkdirSync(dir, { recursive: true });
  const tmpPath = `${targetPath}.${process.pid}.${Date.now()}.tmp`;
  try {
    writeFileSync(tmpPath, JSON.stringify(payload, null, 2) + "\n", "utf-8");
    renameSync(tmpPath, targetPath);
  } catch (err) {
    try { unlinkSync(tmpPath); } catch { /* best-effort */ }
    throw err;
  }
}

/**
 * Validate that `pathStr` has no null bytes or `..` segments and resolves
 * inside `plansRoot`.
 *
 * @param {string} pathStr
 * @param {string} plansRoot — absolute path
 * @returns {{ ok: boolean, reason: string }}
 */
function assertUnderPlans(pathStr, plansRoot) {
  if (pathStr.includes("\x00")) {
    return { ok: false, reason: `null byte in path: ${JSON.stringify(pathStr)}` };
  }
  if (pathStr.includes("..")) {
    return { ok: false, reason: `path traversal (..) in: ${JSON.stringify(pathStr)}` };
  }
  const resolved = resolve(pathStr);
  if (!resolved.startsWith(plansRoot + "/") && resolved !== plansRoot) {
    return { ok: false, reason: `path ${pathStr} escapes plans_root ${plansRoot}` };
  }
  return { ok: true, reason: "" };
}

/**
 * Print Status trailer.
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
 * Parse CLI args.
 * @param {string[]} argv
 */
function parseArgs(argv) {
  const result = {
    combinedPath: null,
    payloadsDir: null,
    manifestPath: null,
    validationDir: null,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--combined-path") { result.combinedPath = next; i++; }
    else if (arg === "--payloads-dir") { result.payloadsDir = next; i++; }
    else if (arg === "--manifest-path") { result.manifestPath = next; i++; }
    else if (arg === "--validation-dir") { result.validationDir = next; i++; }
    else {
      process.stderr.write(`phase-d-prep.mjs: unrecognised argument: ${arg}\n`);
      process.exit(2);
    }
  }
  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.combinedPath || !args.payloadsDir || !args.manifestPath || !args.validationDir) {
    printStatus("BLOCKED", "missing required arguments");
    process.exit(2);
  }

  const plansRoot = resolve("plans");

  // Path-safety on every external path we'll touch.
  for (const p of [args.combinedPath, args.payloadsDir, args.manifestPath, args.validationDir]) {
    const check = assertUnderPlans(p, plansRoot);
    if (!check.ok) {
      printStatus("BLOCKED", `path-safety: ${check.reason}`);
      process.exit(2);
    }
  }

  // Combined-initial.md presence + dedup-applied marker.
  const combinedAbs = resolve(args.combinedPath);
  if (!existsSync(combinedAbs) || !statSync(combinedAbs).isFile()) {
    printStatus("BLOCKED", `combined missing at ${args.combinedPath}`);
    process.exit(2);
  }
  const combinedText = readFileSync(combinedAbs, "utf-8");
  if (!lastNonBlankLine(combinedText).startsWith(DEDUP_APPLIED_MARKER)) {
    printStatus("BLOCKED", "combined-initial.md not finalised by step-5b");
    process.exit(2);
  }

  const currentSha = computeSha256(combinedText);

  // Idempotency: manifest SHA check.
  const manifestAbs = resolve(args.manifestPath);
  if (existsSync(manifestAbs) && statSync(manifestAbs).size > 0) {
    let existing = null;
    try {
      existing = JSON.parse(readFileSync(manifestAbs, "utf-8"));
    } catch { /* ignore */ }
    if (existing && typeof existing === "object" && existing.combined_md_sha256 === currentSha) {
      process.stdout.write("skip: step-5c (artifact exists)\n");
      printStatus("DONE");
      process.exit(0);
    }
    // Stale manifest — wipe payloads_dir entries + manifest, rebuild.
    const payloadsDirAbsStale = resolve(args.payloadsDir);
    if (existsSync(payloadsDirAbsStale)) {
      for (const entry of readdirSync(payloadsDirAbsStale)) {
        if (entry.startsWith("item-") || entry === "_manifest.json") {
          try { unlinkSync(join(payloadsDirAbsStale, entry)); } catch { /* ignore */ }
        }
      }
    }
  }

  // Build payloads + manifest from the pure core.
  let built;
  try {
    built = buildPhaseDPayloads({ combinedMarkdown: combinedText });
  } catch (err) {
    printStatus("BLOCKED", err?.message ?? String(err));
    process.exit(2);
  }

  // Write per-item payloads; resolve manifest paths to absolute.
  const payloadsDirAbs = resolve(args.payloadsDir);
  mkdirSync(payloadsDirAbs, { recursive: true });

  const manifestItems = [];
  for (let i = 0; i < built.payloads.length; i++) {
    const p = built.payloads[i];
    const mItem = built.manifest.items[i];
    const payloadAbs = join(payloadsDirAbs, p.filename);
    const outputAbs = resolve(join(args.validationDir, mItem.output_path));
    atomicWriteJson(payloadAbs, p.json);
    manifestItems.push({
      item_index: mItem.item_index,
      item_slug: mItem.item_slug,
      track: mItem.track,
      payload_path: resolve(payloadAbs),
      output_path: outputAbs,
    });
  }

  // Write manifest LAST (atomic completion marker).
  atomicWriteJson(manifestAbs, {
    schema_version: 1,
    combined_md_sha256: currentSha,
    items: manifestItems,
  });

  if (manifestItems.length === 0) {
    process.stdout.write(`done: step-5c (no items) → ${manifestAbs}\n`);
  } else {
    process.stdout.write(`done: step-5c → ${manifestAbs}\n`);
  }
  printStatus("DONE");
  process.exit(0);
}

// Guard: only run CLI when this module is the entry point.
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  main().catch((err) => {
    process.stderr.write(`phase-d-prep.mjs: fatal: ${err?.message ?? err}\n`);
    process.exit(2);
  });
}
