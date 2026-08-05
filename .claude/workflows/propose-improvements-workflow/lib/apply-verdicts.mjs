/**
 * apply-verdicts.mjs — ESM CLI + pure helper for Step 7 (apply validation verdicts).
 *
 * Applies per-item KEEP/REVISE/DROP verdicts to combined-initial.md and writes the final
 * improvement-proposal.md (rollup recompute + Value/effort sort + unvalidated banner).
 *
 * The pure applyVerdicts() export is self-contained (no imports).
 * The CLI shim at the bottom uses node:fs, node:path, node:os, node:url (stdlib only).
 *
 * ---------------------------------------------------------------------------
 * Exported function
 * ---------------------------------------------------------------------------
 *
 * export function applyVerdicts(input) → result
 *
 * Input shape:
 *   {
 *     combinedMarkdown: string,           // content of combined-initial.md
 *     verdicts: Record<string, string>,   // filename → file content
 *                                         //   e.g. { "item-01-foo.md": "---\n..." }
 *     evidenceDegradedWarns: string | string[]  // warn lines from step-5c manifest
 *                                               // (string = newline-joined, or string[])
 *   }
 *
 * Return shape:
 *   {
 *     markdown: string,       // byte-identical to what apply_verdicts.py writes to
 *                             //   improvement-proposal.md (includes trailing newline)
 *     logLines: string[],     // all warn:/drop:/revise: lines in emit order:
 *                             //   verdict-load warns, per-item warns, drops, revises,
 *                             //   orphan warns
 *     warnings: string[],     // same as logLines filtered to warn: prefix
 *     stats: {
 *       unvalidatedCount: number,  // items in the ⚠️ banner
 *       dropCount:        number,
 *       reviseCount:      number,
 *       warnCount:        number,
 *     }
 *   }
 *
 * Error handling:
 *   Throws an Error with message matching the BLOCKED reasons from the Python CLI
 *   (e.g. "combined file missing/empty", "combined proposal missing both '## Technical'
 *   and '## Business' sections").
 *
 * ---------------------------------------------------------------------------
 * Log-line formats (exact)
 * ---------------------------------------------------------------------------
 *   warn: missing verdict for item-<NN> "<title>" — kept as-is
 *   warn: verdict slug mismatch at item-<NN> (expected=<current>, got=<verdict>) — kept original (stale verdict — delete validation/ after regenerating combined-initial.md)
 *   warn: malformed verdict at <name> — ignored
 *   warn: duplicate item_index <N> in <name> — overwrites <previous slug>
 *   warn: revise-without-body for item-<NN> "<title>" — kept original
 *   warn: revise-malformed for item-<NN> "<title>" — kept original
 *   warn: sort-fallback for item-?? "<title>" — bullet parse failed
 *   warn: orphan verdict at item_index=<N> (slug=<slug>, decision=<decision>) — no matching item
 *   warn: validation directory missing at <path> — defaulting all items to KEEP
 *   drop: item-<NN> "<title>" — validator verdict
 *   revise: item-<NN> "<title>" — applied validator revision
 *
 * ---------------------------------------------------------------------------
 * Sort / tie-break
 * ---------------------------------------------------------------------------
 *   Within each ### rollup aspect: Value desc (high=0, medium=1, low=2) →
 *   Effort asc (no=0, very-low=1, low=2, medium=3, high=4) →
 *   original document order (stable, JS Array.sort is stable in V8/Node ≥ 11).
 *
 * ---------------------------------------------------------------------------
 * Rollup recompute
 * ---------------------------------------------------------------------------
 *   "### <title> · <N> item(s) · max=<value> · effort=<effort|range>"
 *   N       = surviving item count
 *   max     = best (lowest-order) value across surviving items; fallback "medium"
 *   effort  = lo if lo==hi, else "lo-hi"; fallback "medium"
 *   "item" when N==1, "items" when N!=1
 *
 * ---------------------------------------------------------------------------
 * CLI usage
 * ---------------------------------------------------------------------------
 *   node apply-verdicts.mjs \
 *     --combined-path <path> \
 *     --validation-dir <path> \
 *     --output-path <path> \
 *     [--evidence-degraded-warns "<newline-joined string>"]
 *
 * FILE-SIZE NOTE (deviates from the repo's <200-line guideline, intentionally):
 * a 1:1 behavioural port of apply_verdicts_lib.py + apply_verdicts.py kept in a single
 * module so the pure core and CLI shim trace to one Python source pair. The pure verdict /
 * rollup / sort logic alone exceeds 200 lines; splitting further would fragment the parity
 * mapping without reducing complexity. Byte-for-byte equivalence with the Python source is
 * locked by __tests__/parity.test.mjs.
 */

import { pathToFileURL } from 'node:url';

// ---------------------------------------------------------------------------
// Regex constants (mirrors Python _*_RE)
// ---------------------------------------------------------------------------

/** Matches opening fence: 0–3 leading spaces then 3+ backticks or tildes */
const FENCE_OPEN_RE = /^ {0,3}(`{3,}|~{3,})/;
const ATX_H1_RE = /^ {0,3}# (?!#)/;
const ATX_H2_RE = /^ {0,3}## (?!#)/;
const ATX_H3_RE = /^ {0,3}### (?!#)/;
const ATX_H4_RE = /^ {0,3}#### (?!#)/;
const ATX_H5_RE = /^ {0,3}##### (?!#)/;
const ATX_H6_RE = /^ {0,3}###### (?!#)/;
const REVISED_ITEM_HDR_RE = /^ {0,3}#\s+Revised\s+item\s*$/;
const TRAILING_DEDUP_RE = /\n*<!--\s*dedup:[^>]*-->\s*\n?$/i;
const VALUE_BULLET_RE = /^\s{0,3}[-*+]\s+\*\*Value:\*\*\s+(high|medium|low)/i;
const EFFORT_BULLET_RE = /^\s{0,3}[-*+]\s+\*\*Engineering effort hint:\*\*\s+(no|very-low|low|medium|high)/i;
const VERDICT_FILENAME_RE = /^item-(\d+)-([a-z0-9][a-z0-9\-]*)\.md$/;
const REQUIRED_BULLETS = ["Value", "Need", "Benefits", "Proposed solution", "Engineering effort hint"];
const VALUE_ORDER = { high: 0, medium: 1, low: 2 };
const EFFORT_ORDER = { no: 0, "very-low": 1, low: 2, medium: 3, high: 4 };

// ---------------------------------------------------------------------------
// Fence-tracking helper
// ---------------------------------------------------------------------------

/**
 * Returns a fresh fence-state object for use in a line-walking loop.
 * Call updateFenceState(state, line) before checking state.inFence.
 */
function makeFenceState() {
  return { inFence: false, fenceChar: "", fenceLen: 0 };
}

/**
 * Updates fence state given a line. Returns true if the line itself was a
 * fence marker (opening or closing) — callers that want to skip the line can
 * check the return value.
 *
 * Closing fence: same char as opening, run length >= opening run length.
 */
function updateFenceState(state, line) {
  const m = FENCE_OPEN_RE.exec(line);
  if (state.inFence) {
    if (m && m[1][0] === state.fenceChar && m[1].length >= state.fenceLen) {
      state.inFence = false;
    }
    return true; // line is inside (or closing) fence → skip for heading detection
  }
  if (m) {
    state.inFence = true;
    state.fenceChar = m[1][0];
    state.fenceLen = m[1].length;
    return true; // line opened a fence → skip for heading detection
  }
  return false;
}

// ---------------------------------------------------------------------------
// strip_dedup_marker
// ---------------------------------------------------------------------------

/**
 * Strips trailing `<!-- dedup: ... -->` marker (case-insensitive).
 * @param {string} text
 * @returns {string}
 */
function stripDedupMarker(text) {
  return text.replace(TRAILING_DEDUP_RE, "");
}

// ---------------------------------------------------------------------------
// split_combined
// ---------------------------------------------------------------------------

/**
 * Splits combined markdown into { header, technicalBody, businessBody }.
 * Either body may be null when its track isn't present.
 * Header = everything before the first track H2.
 *
 * @param {string} text
 * @returns {{ header: string, technicalBody: string|null, businessBody: string|null }}
 */
function splitCombined(text) {
  const lines = text.split("\n");
  const fence = makeFenceState();

  let techStart = null;
  let bizStart = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (updateFenceState(fence, line)) continue;
    if (ATX_H2_RE.test(line)) {
      const head = line.replace(/^ {0,3}## /, "").trim().toLowerCase();
      if (head.startsWith("technical") && techStart === null) {
        techStart = i;
      } else if (head.startsWith("business") && bizStart === null) {
        bizStart = i;
      }
    }
  }

  if (techStart === null && bizStart === null) {
    return { header: text, technicalBody: null, businessBody: null };
  }

  const firstSplit = Math.min(
    ...[techStart, bizStart].filter((v) => v !== null)
  );
  const header = lines.slice(0, firstSplit).join("\n").trimEnd();

  let technicalBody = null;
  let businessBody = null;

  if (techStart !== null && bizStart !== null) {
    if (techStart < bizStart) {
      technicalBody = lines.slice(techStart, bizStart).join("\n").trimEnd();
      businessBody = lines.slice(bizStart).join("\n").trimEnd();
    } else {
      businessBody = lines.slice(bizStart, techStart).join("\n").trimEnd();
      technicalBody = lines.slice(techStart).join("\n").trimEnd();
    }
  } else if (techStart !== null) {
    technicalBody = lines.slice(techStart).join("\n").trimEnd();
  } else {
    businessBody = lines.slice(bizStart).join("\n").trimEnd();
  }

  return { header, technicalBody, businessBody };
}

// ---------------------------------------------------------------------------
// Verdict parsing
// ---------------------------------------------------------------------------

/**
 * Parses a verdict file's content. Returns verdict object or null on failure.
 * @param {string} text
 * @param {string} filename
 * @returns {{ itemIndex: number, itemSlug: string, decision: string, revisedBody: string|null, sourceFilename: string }|null}
 */
function parseVerdict(text, filename) {
  const lines = text.split("\n");
  if (!lines.length || lines[0].trim() !== "---") return null;

  let end = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") { end = i; break; }
  }
  if (end < 0) return null;

  const fm = {};
  for (let i = 1; i < end; i++) {
    const ln = lines[i];
    const colonIdx = ln.indexOf(":");
    if (colonIdx < 0) continue;
    const key = ln.slice(0, colonIdx).trim();
    const val = ln.slice(colonIdx + 1).trim();
    fm[key] = val;
  }

  const itemIndexRaw = fm["item_index"] ?? "";
  const itemIndex = parseInt(itemIndexRaw, 10);
  if (isNaN(itemIndex) || String(itemIndex) !== itemIndexRaw) return null;

  const itemSlug = fm["item_slug"] ?? "";
  const decision = (fm["decision"] ?? "").toUpperCase();
  if (!["KEEP", "REVISE", "DROP"].includes(decision)) return null;

  let revisedBody = null;
  if (decision === "REVISE") {
    revisedBody = extractRevisedBody(lines.slice(end + 1));
  }

  return { itemIndex, itemSlug, decision, revisedBody, sourceFilename: filename };
}

/**
 * Extracts the `# Revised item` H1 body (fence-aware).
 * Returns null when absent or empty.
 * @param {string[]} lines
 * @returns {string|null}
 */
function extractRevisedBody(lines) {
  const fence = makeFenceState();
  let start = null;
  let end = lines.length;

  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i];
    if (updateFenceState(fence, ln)) continue;

    if (start === null) {
      if (REVISED_ITEM_HDR_RE.test(ln)) {
        start = i + 1;
      }
    } else {
      if (ATX_H1_RE.test(ln)) {
        end = i;
        break;
      }
    }
  }

  if (start === null) return null;
  const body = lines.slice(start, end).join("\n").replace(/^\n+|\n+$/g, "");
  return body.trim() ? body : null;
}

/**
 * Loads verdicts from a map of filename → content strings.
 * Mirrors load_verdicts() but operates on in-memory data.
 *
 * @param {Record<string, string>} verdictsMap  filename → file content
 * @returns {{ verdicts: Map<number, object>, warns: string[] }}
 */
function loadVerdicts(verdictsMap) {
  /** @type {Map<number, object>} */
  const verdicts = new Map();
  const warns = [];

  // Sort filenames for deterministic order (mirrors Python sorted(iterdir()))
  const filenames = Object.keys(verdictsMap).sort();

  for (const filename of filenames) {
    const m = VERDICT_FILENAME_RE.exec(filename);
    if (!m) continue;

    const text = verdictsMap[filename];
    const v = parseVerdict(text, filename);
    if (v === null) {
      warns.push(`warn: malformed verdict at ${filename} — ignored`);
      continue;
    }
    if (verdicts.has(v.itemIndex)) {
      const prev = verdicts.get(v.itemIndex);
      warns.push(
        `warn: duplicate item_index ${v.itemIndex} in ${filename} — overwrites ${prev.itemSlug}`
      );
    }
    verdicts.set(v.itemIndex, v);
  }

  return { verdicts, warns };
}

// ---------------------------------------------------------------------------
// Revised body schema validation + H2 → H4 demotion
// ---------------------------------------------------------------------------

/**
 * Validates the revised body per spec "Revised body schema".
 * Returns true iff well-formed (fence-aware).
 * @param {string} body
 * @returns {boolean}
 */
function validateRevisedBody(body) {
  const lines = body.split("\n");
  const fence = makeFenceState();
  let h2Count = 0;
  const bulletsFound = [];

  for (const line of lines) {
    if (updateFenceState(fence, line)) continue;
    if (ATX_H1_RE.test(line)) return false;
    if (ATX_H2_RE.test(line)) { h2Count++; continue; }
    if (ATX_H3_RE.test(line) || ATX_H4_RE.test(line) || ATX_H5_RE.test(line) || ATX_H6_RE.test(line)) {
      return false;
    }
    const bm = /^ {0,3}[-*+]\s+\*\*([^*]+):\*\*/.exec(line);
    if (bm) {
      bulletsFound.push(bm[1].trim());
    }
  }

  if (h2Count !== 1) return false;
  if (bulletsFound.includes("Category")) return false;

  // Filter to required labels in discovery order, check exact sequence
  const seenRequired = bulletsFound.filter((b) => REQUIRED_BULLETS.includes(b));
  if (seenRequired.length !== REQUIRED_BULLETS.length) return false;
  for (let i = 0; i < REQUIRED_BULLETS.length; i++) {
    if (seenRequired[i] !== REQUIRED_BULLETS[i]) return false;
  }
  return true;
}

/**
 * Demotes `## ` headings → `#### ` (fence-aware, 0–3 leading spaces).
 * @param {string} body
 * @returns {string}
 */
function demoteH2ToH4(body) {
  const lines = body.split("\n");
  const fence = makeFenceState();
  const out = [];

  for (const line of lines) {
    if (updateFenceState(fence, line)) {
      out.push(line);
      continue;
    }
    // Fence was not active (and line is not a fence opener already pushed above).
    // Re-check: updateFenceState returns true for fence lines → they're pushed above.
    // For non-fence lines: demote ## if matches.
    out.push(line.replace(/^( {0,3})## /, (_, lead) => `${lead}#### `));
  }
  return out.join("\n");
}

// ---------------------------------------------------------------------------
// Per-item value/effort parse
// ---------------------------------------------------------------------------

/**
 * Returns [value, effort] from the block's bullets (lower-cased), or null.
 * @param {string} block
 * @returns {[string|null, string|null]}
 */
function parseValueEffort(block) {
  const lines = block.split("\n");
  const fence = makeFenceState();
  let value = null;
  let effort = null;

  for (const line of lines) {
    if (updateFenceState(fence, line)) continue;
    if (value === null) {
      const vm = VALUE_BULLET_RE.exec(line);
      if (vm) value = vm[1].toLowerCase();
    }
    if (effort === null) {
      const em = EFFORT_BULLET_RE.exec(line);
      if (em) effort = em[1].toLowerCase();
    }
  }

  return [value, effort];
}

// ---------------------------------------------------------------------------
// title_to_slug
// ---------------------------------------------------------------------------

/**
 * Converts item title to kebab-slug (mirrors Python title_to_slug).
 * @param {string} title
 * @returns {string}
 */
function titleToSlug(title) {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || "untitled";
}

// ---------------------------------------------------------------------------
// sanitize_title_for_log
// ---------------------------------------------------------------------------

/**
 * Replaces control whitespace (\r\n\t runs) with single spaces and trims.
 * @param {string} title
 * @returns {string}
 */
function sanitizeTitleForLog(title) {
  return title.replace(/[\r\n\t]+/g, " ").trim();
}

// ---------------------------------------------------------------------------
// split_rollups
// ---------------------------------------------------------------------------

/**
 * @typedef {{ rollupHeading: string|null, aspectComment: string|null, items: string[] }} RollupBlock
 */

/**
 * Splits a track body (starts with `## Technical` / `## Business`) into
 * [trackHeader, RollupBlock[]]. fence-aware.
 *
 * @param {string} trackBody
 * @returns {{ trackHeader: string, rollups: RollupBlock[] }}
 */
function splitRollups(trackBody) {
  if (!trackBody) return { trackHeader: "", rollups: [] };

  const lines = trackBody.split("\n");

  // Find the first ### heading
  let firstH3 = null;
  const fence2 = makeFenceState();
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (updateFenceState(fence2, line)) continue;
    if (ATX_H3_RE.test(line)) { firstH3 = i; break; }
  }

  const trackHeaderEnd = firstH3 !== null ? firstH3 : lines.length;
  const trackHeader = lines.slice(0, trackHeaderEnd).join("\n").trimEnd();

  const rollups = [];
  if (firstH3 === null) return { trackHeader, rollups };

  // Walk each ### rollup block
  let i = firstH3;

  while (i < lines.length) {
    const line = lines[i];
    if (!ATX_H3_RE.test(line)) { i++; continue; }

    const rollupHeading = line;

    // Look at next non-blank line for aspect-id comment
    let aspectComment = null;
    let j = i + 1;
    while (j < lines.length && !lines[j].trim()) j++;
    if (j < lines.length && /^\s*<!--\s*aspect-id:.*-->\s*$/.test(lines[j])) {
      aspectComment = lines[j];
      j++;
    }

    // Find end of this rollup block (next ### or ## outside fences)
    const itemsBlockStart = j;
    let blockEnd = lines.length;
    const innerFence = makeFenceState();
    for (let k = j; k < lines.length; k++) {
      const ln = lines[k];
      if (updateFenceState(innerFence, ln)) continue;
      if (ATX_H3_RE.test(ln) || ATX_H2_RE.test(ln)) {
        blockEnd = k;
        break;
      }
    }

    const items = extractItemBlocks(lines.slice(itemsBlockStart, blockEnd));
    rollups.push({ rollupHeading, aspectComment, items });
    i = blockEnd;
  }

  return { trackHeader, rollups };
}

/**
 * Extracts `#### ...` blocks from a slice of lines (fence-aware).
 * @param {string[]} sliceLines
 * @returns {string[]}
 */
function extractItemBlocks(sliceLines) {
  const fence = makeFenceState();
  const starts = [];

  for (let i = 0; i < sliceLines.length; i++) {
    const line = sliceLines[i];
    if (updateFenceState(fence, line)) continue;
    if (ATX_H4_RE.test(line)) starts.push(i);
  }

  if (!starts.length) return [];

  const blocks = [];
  for (let idx = 0; idx < starts.length; idx++) {
    const s = starts[idx];
    const e = idx + 1 < starts.length ? starts[idx + 1] : sliceLines.length;
    blocks.push(sliceLines.slice(s, e).join("\n").trimEnd());
  }
  return blocks;
}

// ---------------------------------------------------------------------------
// sort_items_within_aspect
// ---------------------------------------------------------------------------

/**
 * Stable sort by Value desc → Effort asc → original order.
 * @param {string[]} items
 * @returns {{ sorted: string[], warns: string[] }}
 */
function sortItemsWithinAspect(items) {
  const decorated = items.map((block, origIdx) => {
    const [value, effort] = parseValueEffort(block);
    const vUsed = (value !== null && value in VALUE_ORDER) ? value : "medium";
    const eUsed = (effort !== null && effort in EFFORT_ORDER) ? effort : "medium";
    return { vKey: VALUE_ORDER[vUsed], eKey: EFFORT_ORDER[eUsed], origIdx, block, value, effort };
  });

  const warns = [];
  for (const d of decorated) {
    if (d.value === null || d.effort === null) {
      // Extract title from first non-empty line after stripping leading # and spaces
      const title = d.block.replace(/^ {0,3}#+\s*/, "").split("\n")[0].trim();
      warns.push(`warn: sort-fallback for item-?? "${title}" — bullet parse failed`);
    }
  }

  // Stable sort (JS Array.sort is stable in V8 ≥ Node 11)
  decorated.sort((a, b) => {
    if (a.vKey !== b.vKey) return a.vKey - b.vKey; // Value desc (lower index = better)
    if (a.eKey !== b.eKey) return a.eKey - b.eKey; // Effort asc
    return a.origIdx - b.origIdx;                   // Preserve document order
  });

  return { sorted: decorated.map((d) => d.block), warns };
}

// ---------------------------------------------------------------------------
// recompute_rollup_heading
// ---------------------------------------------------------------------------

/**
 * Recomputes the rollup heading: `### <title> · <N> item(s) · max=<X> · effort=<Y>`.
 * Called only when items is non-empty.
 * @param {string} origHeading
 * @param {string[]} items
 * @returns {string}
 */
function recomputeRollupHeading(origHeading, items) {
  const m = /^ {0,3}### (?<rest>.*)$/.exec(origHeading);
  if (!m) return origHeading;

  const rest = m.groups.rest;
  const title = rest.split(" · ")[0].trim();
  const n = items.length;
  const itemWord = n === 1 ? "item" : "items";

  const values = [];
  const efforts = [];
  for (const block of items) {
    const [v, e] = parseValueEffort(block);
    if (v !== null && v in VALUE_ORDER) values.push(v);
    if (e !== null && e in EFFORT_ORDER) efforts.push(e);
  }

  // max value = lowest order key (best)
  const maxValue = values.length > 0
    ? values.reduce((best, v) => VALUE_ORDER[v] < VALUE_ORDER[best] ? v : best)
    : "medium";

  let effortStr;
  if (efforts.length > 0) {
    const lo = efforts.reduce((b, e) => EFFORT_ORDER[e] < EFFORT_ORDER[b] ? e : b);
    const hi = efforts.reduce((b, e) => EFFORT_ORDER[e] > EFFORT_ORDER[b] ? e : b);
    effortStr = lo === hi ? lo : `${lo}-${hi}`;
  } else {
    effortStr = "medium";
  }

  return `### ${title} · ${n} ${itemWord} · max=${maxValue} · effort=${effortStr}`;
}

// ---------------------------------------------------------------------------
// _apply_to_track (core per-track verdict application)
// ---------------------------------------------------------------------------

/**
 * Applies verdicts to one track body. Returns output body, next item index,
 * and unvalidated count for this track.
 *
 * Single-walk design: iterates split_rollups output (rollups → items) and
 * assigns sequential indices in document order. Items outside rollups (in the
 * track header) are NOT indexed — this matches the Python fix that avoids
 * misrouting verdicts when a #### H4 exists before the first ### H3 rollup.
 *
 * @param {string} trackBody
 * @param {number} startIndex
 * @param {Map<number, object>} verdicts
 * @param {string[]} logWarns
 * @param {string[]} logDrops
 * @param {string[]} logRevises
 * @param {Set<number>} consumed
 * @returns {{ outputBody: string, nextIndex: number, unvalidatedLocal: number }}
 */
function applyToTrack(trackBody, startIndex, verdicts, logWarns, logDrops, logRevises, consumed) {
  if (!trackBody) return { outputBody: "", nextIndex: startIndex, unvalidatedLocal: 0 };

  const { trackHeader, rollups } = splitRollups(trackBody);

  let unvalidatedLocal = 0;
  let nextIndex = startIndex;
  const outChunks = [trackHeader];

  for (const ru of rollups) {
    const surviving = [];

    for (const blk of ru.items) {
      const itIndex = nextIndex++;
      consumed.add(itIndex);

      // Extract title from the leading `#### <title>` line
      const firstLine = blk ? blk.split("\n")[0] : "";
      const itTitle = firstLine.replace(/^ {0,3}#+ /, "").trim();
      const logTitle = sanitizeTitleForLog(itTitle);

      const verdict = verdicts.get(itIndex) ?? null;

      if (verdict === null) {
        logWarns.push(`warn: missing verdict for item-${String(itIndex).padStart(2, "0")} "${logTitle}" — kept as-is`);
        surviving.push(blk);
        unvalidatedLocal++;
        continue;
      }

      const currentSlug = titleToSlug(itTitle);
      if (verdict.itemSlug && currentSlug !== verdict.itemSlug) {
        logWarns.push(
          `warn: verdict slug mismatch at item-${String(itIndex).padStart(2, "0")} ` +
          `(expected=${currentSlug}, got=${verdict.itemSlug}) — ` +
          `kept original (stale verdict — delete validation/ after regenerating combined-initial.md)`
        );
        surviving.push(blk);
        unvalidatedLocal++;
        continue;
      }

      if (verdict.decision === "DROP") {
        logDrops.push(`drop: item-${String(itIndex).padStart(2, "0")} "${logTitle}" — validator verdict`);
        continue;
      }

      if (verdict.decision === "KEEP") {
        surviving.push(blk);
        continue;
      }

      // REVISE
      const body = verdict.revisedBody;
      if (!body || !body.trim()) {
        logWarns.push(`warn: revise-without-body for item-${String(itIndex).padStart(2, "0")} "${logTitle}" — kept original`);
        surviving.push(blk);
        unvalidatedLocal++;
        continue;
      }
      if (!validateRevisedBody(body)) {
        logWarns.push(`warn: revise-malformed for item-${String(itIndex).padStart(2, "0")} "${logTitle}" — kept original`);
        surviving.push(blk);
        unvalidatedLocal++;
        continue;
      }

      logRevises.push(`revise: item-${String(itIndex).padStart(2, "0")} "${logTitle}" — applied validator revision`);
      surviving.push(demoteH2ToH4(body));
    }

    if (!surviving.length) continue; // drop entire rollup + aspect-id comment

    const newHeading = recomputeRollupHeading(ru.rollupHeading ?? "", surviving);
    const { sorted: sortedItems, warns: sortWarns } = sortItemsWithinAspect(surviving);
    logWarns.push(...sortWarns);

    const parts = [newHeading];
    if (ru.aspectComment) parts.push(ru.aspectComment);
    parts.push("");
    for (const blk of sortedItems) {
      parts.push(blk.trimEnd());
      parts.push("");
    }
    outChunks.push(parts.join("\n").trimEnd());
  }

  return {
    outputBody: outChunks.join("\n\n"),
    nextIndex,
    unvalidatedLocal,
  };
}

// ---------------------------------------------------------------------------
// Main exported function: applyVerdicts
// ---------------------------------------------------------------------------

/**
 * Apply per-item KEEP/REVISE/DROP verdicts to produce the final proposal.
 *
 * @param {{ combinedMarkdown: string, verdicts: Record<string, string>, evidenceDegradedWarns: string|string[] }} input
 * @returns {{ markdown: string, logLines: string[], warnings: string[], stats: { unvalidatedCount: number, dropCount: number, reviseCount: number, warnCount: number } }}
 * @throws {Error} with BLOCKED-reason message when input is invalid
 */
export function applyVerdicts({ combinedMarkdown, verdicts: verdictsMap, evidenceDegradedWarns = [] }) {
  // Validate input
  if (!combinedMarkdown || !combinedMarkdown.trim()) {
    throw new Error("combined file missing/empty");
  }

  const combinedText = stripDedupMarker(combinedMarkdown);
  const { header, technicalBody, businessBody } = splitCombined(combinedText);

  if (technicalBody === null && businessBody === null) {
    throw new Error("combined proposal missing both '## Technical' and '## Business' sections");
  }

  // Load verdicts from in-memory map
  const { verdicts, warns: verdictWarns } = loadVerdicts(verdictsMap ?? {});

  const logWarns = [...verdictWarns];
  const logDrops = [];
  const logRevises = [];

  const consumed = new Set();
  let unvalidatedTotal = 0;

  // Apply to technical track first, then business
  const { outputBody: outputTech, nextIndex: nextIndex1, unvalidatedLocal: ut } =
    applyToTrack(technicalBody ?? "", 1, verdicts, logWarns, logDrops, logRevises, consumed);
  unvalidatedTotal += ut;

  const { outputBody: outputBiz, nextIndex: _nextIndex2, unvalidatedLocal: ub } =
    applyToTrack(businessBody ?? "", nextIndex1, verdicts, logWarns, logDrops, logRevises, consumed);
  unvalidatedTotal += ub;

  // Orphan verdicts (sorted by index, mirrors Python `sorted(verdicts.items())`)
  const sortedVerdictKeys = [...verdicts.keys()].sort((a, b) => a - b);
  for (const idx of sortedVerdictKeys) {
    if (!consumed.has(idx)) {
      const v = verdicts.get(idx);
      logWarns.push(
        `warn: orphan verdict at item_index=${idx} ` +
        `(slug=${v.itemSlug}, decision=${v.decision.toLowerCase()}) — no matching item`
      );
    }
  }

  // Count evidence-degraded items
  const evidenceDegradedLines =
    Array.isArray(evidenceDegradedWarns)
      ? evidenceDegradedWarns
      : (evidenceDegradedWarns ? String(evidenceDegradedWarns).split("\n") : []);

  let evidenceDegradedCount = 0;
  for (const line of evidenceDegradedLines) {
    if (/^warn: item-(\d+) ".*" evidence-degraded /.test(line)) {
      evidenceDegradedCount++;
    }
  }
  unvalidatedTotal += evidenceDegradedCount;

  // Assemble output
  const parts = [];
  if (header.trim()) parts.push(header.trimEnd());

  if (unvalidatedTotal > 0) {
    const plural = unvalidatedTotal === 1 ? "item" : "items";
    parts.push(
      `> ⚠️ **${unvalidatedTotal} ${plural} shipped without complete validation.** ` +
      `Review the orchestrator log (\`warn:\` lines) before sharing this proposal.`
    );
  }

  if (outputTech.trim()) parts.push(outputTech.trimEnd());
  if (outputBiz.trim()) parts.push(outputBiz.trimEnd());

  const markdown = parts.join("\n\n").trimEnd() + "\n";

  // Build logLines in spec emit order: warns (includes orphan warns at end), drops, revises.
  // The Python emits: all logWarns first (includes orphan warns), then drops, then revises.
  const logLines = [...logWarns, ...logDrops, ...logRevises];
  const warnings = logLines.filter((l) => l.startsWith("warn:"));

  return {
    markdown,
    logLines,
    warnings,
    stats: {
      unvalidatedCount: unvalidatedTotal,
      dropCount: logDrops.length,
      reviseCount: logRevises.length,
      warnCount: logWarns.length,
    },
  };
}

// ---------------------------------------------------------------------------
// CLI shim — mirrors apply_verdicts.py main() exactly
// Guarded by import.meta.url check; only runs when file is executed directly.
// Uses node:fs, node:path, node:os, node:url (stdlib only, no external deps).
// ---------------------------------------------------------------------------

/**
 * Print `Status: <status>` or `Status: <status> — <reason>` (em-dash U+2014).
 * Mirrors Python _print_status().
 * @param {string} status
 * @param {string} reason
 */
function printStatus(status, reason = '') {
  if (reason) {
    console.log(`Status: ${status} — ${reason}`);
  } else {
    console.log(`Status: ${status}`);
  }
}

/**
 * Parse CLI arguments matching apply_verdicts.py argparse configuration.
 * Required: --combined-path, --validation-dir, --output-path
 * Optional: --evidence-degraded-warns
 * @param {string[]} argv  process.argv
 * @returns {{ combinedPath: string, validationDir: string, outputPath: string, evidenceDegradedWarns: string }}
 */
function parseCliArgs(argv) {
  const args = {
    combinedPath: null,
    validationDir: null,
    outputPath: null,
    evidenceDegradedWarns: '',
  };

  const positional = argv.slice(2);
  for (let i = 0; i < positional.length; i++) {
    const flag = positional[i];
    if (flag === '--combined-path') {
      args.combinedPath = positional[++i] ?? null;
    } else if (flag === '--validation-dir') {
      args.validationDir = positional[++i] ?? null;
    } else if (flag === '--output-path') {
      args.outputPath = positional[++i] ?? null;
    } else if (flag === '--evidence-degraded-warns') {
      args.evidenceDegradedWarns = positional[++i] ?? '';
    } else {
      process.stderr.write(`Unknown argument: ${flag}\n`);
      process.exit(1);
    }
  }

  const missing = [];
  if (!args.combinedPath) missing.push('--combined-path');
  if (!args.validationDir) missing.push('--validation-dir');
  if (!args.outputPath) missing.push('--output-path');
  if (missing.length) {
    process.stderr.write(`Missing required arguments: ${missing.join(', ')}\n`);
    process.exit(1);
  }

  return args;
}

/**
 * Atomic write of text content to target path.
 * Creates parent dirs (mkdir -p), writes to tempfile, renames (mirrors Python _atomic_write).
 * @param {import('node:fs')} fs
 * @param {import('node:path')} path
 * @param {string} target  absolute path
 * @param {string} content
 */
function atomicWrite(fs, path, target, content) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const tmpPath = `${target}.${process.pid}.${Date.now()}.tmp`;
  try {
    fs.writeFileSync(tmpPath, content, 'utf8');
    fs.renameSync(tmpPath, target);
  } catch (err) {
    try { fs.unlinkSync(tmpPath); } catch { /* ignore cleanup error */ }
    throw err;
  }
}

async function main() {
  const fs = (await import('node:fs')).default;
  const path = (await import('node:path')).default;

  const args = parseCliArgs(process.argv);
  const cwd = path.resolve(process.cwd());

  // Resolve paths relative to cwd
  const combinedPath = path.resolve(cwd, args.combinedPath);
  const validationDir = path.resolve(cwd, args.validationDir);
  const outputPath = path.resolve(cwd, args.outputPath);

  // Path-safety check: resolved path must be inside cwd (mirrors Python _path_safe).
  // A path is safe if it starts with cwd + sep, or equals cwd.
  function pathSafe(p) {
    if (p.includes('\x00')) return false;
    const resolved = path.resolve(p);
    return resolved === cwd || resolved.startsWith(cwd + path.sep);
  }

  if (!pathSafe(combinedPath)) {
    printStatus('BLOCKED', `unsafe combined path: ${args.combinedPath}`);
    process.exit(2);
  }
  if (!pathSafe(validationDir)) {
    printStatus('BLOCKED', `unsafe validation_dir: ${args.validationDir}`);
    process.exit(2);
  }

  // Output path must be inside plans/ relative to cwd (mirrors Python plans_root check).
  const plansRoot = path.resolve(cwd, 'plans');
  const outputResolved = path.resolve(outputPath);
  const relToPlans = path.relative(plansRoot, outputResolved);
  if (relToPlans.startsWith('..') || path.isAbsolute(relToPlans)) {
    printStatus('BLOCKED', `output path outside plans/: ${args.outputPath}`);
    process.exit(2);
  }

  // Idempotency: if output exists and is non-empty, skip (mirrors Python check).
  try {
    const stat = fs.statSync(outputPath);
    if (stat.size > 0) {
      console.log(`skip: step-7 (artifact exists at ${outputPath})`);
      printStatus('DONE');
      process.exit(0);
    }
  } catch {
    // file absent — proceed
  }

  // Read combined file (mirrors Python is_file + read_text checks).
  let combinedRaw;
  try {
    const stat = fs.statSync(combinedPath);
    if (!stat.isFile()) throw new Error('not a file');
    combinedRaw = fs.readFileSync(combinedPath, 'utf8');
  } catch {
    printStatus('BLOCKED', `combined missing at ${combinedPath}`);
    process.exit(2);
  }
  if (!combinedRaw.trim()) {
    printStatus('BLOCKED', 'combined file missing/empty');
    process.exit(2);
  }

  // Detect whether validation dir is present (mirrors Python validation_dir_missing).
  let validationDirMissing = false;
  try {
    const stat = fs.statSync(validationDir);
    if (!stat.isDirectory()) validationDirMissing = true;
  } catch {
    validationDirMissing = true;
  }

  // Collect verdict files from validation-dir.
  // Glob: item-*.md only; exclude _payloads/ entries and _manifest.json.
  const verdictsMap = {};
  if (!validationDirMissing) {
    let entries;
    try {
      entries = fs.readdirSync(validationDir);
    } catch {
      entries = [];
    }
    for (const entry of entries.sort()) {
      if (entry === '_payloads' || entry === '_manifest.json') continue;
      if (!VERDICT_FILENAME_RE.test(entry)) continue;
      const fullPath = path.join(validationDir, entry);
      try {
        const stat = fs.statSync(fullPath);
        if (!stat.isFile()) continue;
        verdictsMap[entry] = fs.readFileSync(fullPath, 'utf8');
      } catch {
        // skip unreadable files
      }
    }
  }

  // Run the pure function — may throw on BLOCKED conditions.
  let result;
  try {
    result = applyVerdicts({
      combinedMarkdown: combinedRaw,
      verdicts: verdictsMap,
      evidenceDegradedWarns: args.evidenceDegradedWarns,
    });
  } catch (err) {
    printStatus('BLOCKED', err.message);
    process.exit(2);
  }

  // If validation dir was missing, insert the dir-missing warn at the front of logLines
  // and set unvalidated_total = len(consumed), mirroring Python's exact behavior.
  if (validationDirMissing) {
    const dirMissingWarn = `warn: validation directory missing at ${validationDir} — defaulting all items to KEEP`;
    result.logLines.unshift(dirMissingWarn);
    result.warnings.unshift(dirMissingWarn);
    result.stats.warnCount += 1;
    // Python sets unvalidated_total = len(consumed) when dir missing.
    // When the dir is absent all items have no verdicts so unvalidatedCount already
    // equals the total consumed count. No override needed.
  }

  // Atomic write (tempfile + rename, mkdir -p parent).
  try {
    atomicWrite(fs, path, outputPath, result.markdown);
  } catch (err) {
    printStatus('BLOCKED', `write failed: ${err.message}`);
    process.exit(2);
  }

  // Emit log lines in spec order: warns, drops, revises (already ordered in logLines).
  for (const line of result.logLines) {
    console.log(line);
  }

  // done: line with U+2192 arrow and absolute output path.
  console.log(`done: step-7 → ${outputPath}`);

  // Status trailer — matches Python exactly.
  // DONE_WITH_CONCERNS when any warn:, drop:, or revise: lines exist.
  const warnLines = result.logLines.filter(l => l.startsWith('warn:'));
  const dropLines = result.logLines.filter(l => l.startsWith('drop:'));
  const reviseLines = result.logLines.filter(l => l.startsWith('revise:'));

  if (warnLines.length > 0 || dropLines.length > 0 || reviseLines.length > 0) {
    const reasons = [];
    if (warnLines.length > 0) reasons.push(`${warnLines.length} warn(s)`);
    if (dropLines.length > 0) reasons.push(`${dropLines.length} drop(s)`);
    if (reviseLines.length > 0) reasons.push(`${reviseLines.length} revise(s)`);
    printStatus('DONE_WITH_CONCERNS', reasons.join('; '));
  } else {
    printStatus('DONE');
  }
}

// CLI entry point guard: only execute main() when run directly as a script.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(err => {
    process.stderr.write(`${err.message}\n`);
    process.exit(2);
  });
}
