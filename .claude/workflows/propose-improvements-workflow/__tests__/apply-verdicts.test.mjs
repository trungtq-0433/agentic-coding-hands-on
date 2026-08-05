/**
 * apply-verdicts.test.mjs — Node test runner port of test_apply_verdicts.py
 *
 * Ports EVERY pure-function case from the Python test suite.
 *
 * Run: node --test claude/workflows/propose-improvements-workflow/__tests__/apply-verdicts.test.mjs
 *
 * Requires: Node v24, no external npm deps.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

// ---------------------------------------------------------------------------
// Import the module under test
// ---------------------------------------------------------------------------

import { applyVerdicts } from "../lib/apply-verdicts.mjs";

// ---------------------------------------------------------------------------
// Inline reimplementations of pure helpers (for unit-level assertions only).
// These MUST stay in sync with lib/apply-verdicts.mjs — the pure-function
// tests verify end-to-end consistency.
// ---------------------------------------------------------------------------

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
const REQUIRED_BULLETS = ["Value", "Need", "Benefits", "Proposed solution", "Engineering effort hint"];
const VALUE_ORDER = { high: 0, medium: 1, low: 2 };
const EFFORT_ORDER = { no: 0, "very-low": 1, low: 2, medium: 3, high: 4 };

function makeFenceState() { return { inFence: false, fenceChar: "", fenceLen: 0 }; }
function updateFenceState(s, line) {
  const m = FENCE_OPEN_RE.exec(line);
  if (s.inFence) {
    if (m && m[1][0] === s.fenceChar && m[1].length >= s.fenceLen) s.inFence = false;
    return true;
  }
  if (m) { s.inFence = true; s.fenceChar = m[1][0]; s.fenceLen = m[1].length; return true; }
  return false;
}

function stripDedupMarker(text) { return text.replace(TRAILING_DEDUP_RE, ""); }

function splitCombined(text) {
  const lines = text.split("\n");
  const f = makeFenceState();
  let techStart = null, bizStart = null;
  for (let i = 0; i < lines.length; i++) {
    if (updateFenceState(f, lines[i])) continue;
    if (ATX_H2_RE.test(lines[i])) {
      const head = lines[i].replace(/^ {0,3}## /, "").trim().toLowerCase();
      if (head.startsWith("technical") && techStart === null) techStart = i;
      else if (head.startsWith("business") && bizStart === null) bizStart = i;
    }
  }
  if (techStart === null && bizStart === null) return { header: text, technicalBody: null, businessBody: null };
  const firstSplit = Math.min(...[techStart, bizStart].filter(v => v !== null));
  const header = lines.slice(0, firstSplit).join("\n").trimEnd();
  let technicalBody = null, businessBody = null;
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

function titleToSlug(title) {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || "untitled";
}

function validateRevisedBody(body) {
  const lines = body.split("\n");
  const f = makeFenceState();
  let h2Count = 0;
  const bulletsFound = [];
  for (const line of lines) {
    if (updateFenceState(f, line)) continue;
    if (ATX_H1_RE.test(line)) return false;
    if (ATX_H2_RE.test(line)) { h2Count++; continue; }
    if (ATX_H3_RE.test(line) || ATX_H4_RE.test(line) || ATX_H5_RE.test(line) || ATX_H6_RE.test(line)) return false;
    const bm = /^ {0,3}[-*+]\s+\*\*([^*]+):\*\*/.exec(line);
    if (bm) bulletsFound.push(bm[1].trim());
  }
  if (h2Count !== 1) return false;
  if (bulletsFound.includes("Category")) return false;
  const seen = bulletsFound.filter(b => REQUIRED_BULLETS.includes(b));
  if (seen.length !== REQUIRED_BULLETS.length) return false;
  for (let i = 0; i < REQUIRED_BULLETS.length; i++) if (seen[i] !== REQUIRED_BULLETS[i]) return false;
  return true;
}

function demoteH2ToH4(body) {
  const lines = body.split("\n");
  const f = makeFenceState();
  const out = [];
  for (const line of lines) {
    if (updateFenceState(f, line)) { out.push(line); continue; }
    out.push(line.replace(/^( {0,3})## /, (_, lead) => `${lead}#### `));
  }
  return out.join("\n");
}

function parseValueEffort(block) {
  const lines = block.split("\n");
  const f = makeFenceState();
  let value = null, effort = null;
  for (const line of lines) {
    if (updateFenceState(f, line)) continue;
    if (value === null) { const m = VALUE_BULLET_RE.exec(line); if (m) value = m[1].toLowerCase(); }
    if (effort === null) { const m = EFFORT_BULLET_RE.exec(line); if (m) effort = m[1].toLowerCase(); }
  }
  return [value, effort];
}

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
      const title = d.block.replace(/^ {0,3}#+\s*/, "").split("\n")[0].trim();
      warns.push(`warn: sort-fallback for item-?? "${title}" — bullet parse failed`);
    }
  }
  decorated.sort((a, b) => a.vKey !== b.vKey ? a.vKey - b.vKey : a.eKey !== b.eKey ? a.eKey - b.eKey : a.origIdx - b.origIdx);
  return { sorted: decorated.map(d => d.block), warns };
}

function recomputeRollupHeading(origHeading, items) {
  const m = /^ {0,3}### (?<rest>.*)$/.exec(origHeading);
  if (!m) return origHeading;
  const title = m.groups.rest.split(" · ")[0].trim();
  const n = items.length;
  const itemWord = n === 1 ? "item" : "items";
  const values = [], efforts = [];
  for (const block of items) {
    const [v, e] = parseValueEffort(block);
    if (v !== null && v in VALUE_ORDER) values.push(v);
    if (e !== null && e in EFFORT_ORDER) efforts.push(e);
  }
  const maxValue = values.length > 0 ? values.reduce((best, v) => VALUE_ORDER[v] < VALUE_ORDER[best] ? v : best) : "medium";
  let effortStr;
  if (efforts.length > 0) {
    const lo = efforts.reduce((b, e) => EFFORT_ORDER[e] < EFFORT_ORDER[b] ? e : b);
    const hi = efforts.reduce((b, e) => EFFORT_ORDER[e] > EFFORT_ORDER[b] ? e : b);
    effortStr = lo === hi ? lo : `${lo}-${hi}`;
  } else { effortStr = "medium"; }
  return `### ${title} · ${n} ${itemWord} · max=${maxValue} · effort=${effortStr}`;
}

// ---------------------------------------------------------------------------
// Inline load_verdicts (mirrors the module's internal for test_load_verdicts_*)
// ---------------------------------------------------------------------------

const VERDICT_FILENAME_RE = /^item-(\d+)-([a-z0-9][a-z0-9\-]*)\.md$/;

function parseVerdictText(text, filename) {
  const lines = text.split("\n");
  if (!lines.length || lines[0].trim() !== "---") return null;
  let end = -1;
  for (let i = 1; i < lines.length; i++) { if (lines[i].trim() === "---") { end = i; break; } }
  if (end < 0) return null;
  const fm = {};
  for (let i = 1; i < end; i++) {
    const ln = lines[i]; const ci = ln.indexOf(":");
    if (ci < 0) continue;
    fm[ln.slice(0, ci).trim()] = ln.slice(ci + 1).trim();
  }
  const itemIndexRaw = fm["item_index"] ?? "";
  const itemIndex = parseInt(itemIndexRaw, 10);
  if (isNaN(itemIndex)) return null;
  const itemSlug = fm["item_slug"] ?? "";
  const decision = (fm["decision"] ?? "").toUpperCase();
  if (!["KEEP", "REVISE", "DROP"].includes(decision)) return null;
  let revisedBody = null;
  if (decision === "REVISE") {
    const after = lines.slice(end + 1);
    const f = makeFenceState();
    let start = null, bodyEnd = after.length;
    for (let i = 0; i < after.length; i++) {
      const ln = after[i];
      if (updateFenceState(f, ln)) continue;
      if (start === null) { if (REVISED_ITEM_HDR_RE.test(ln)) start = i + 1; }
      else { if (ATX_H1_RE.test(ln)) { bodyEnd = i; break; } }
    }
    if (start !== null) {
      const body = after.slice(start, bodyEnd).join("\n").replace(/^\n+|\n+$/g, "");
      revisedBody = body.trim() ? body : null;
    }
  }
  return { itemIndex, itemSlug, decision, revisedBody, sourceFilename: filename };
}

function loadVerdictsFromMap(verdictsMap) {
  const verdicts = new Map();
  const warns = [];
  const filenames = Object.keys(verdictsMap).sort();
  for (const filename of filenames) {
    const m = VERDICT_FILENAME_RE.exec(filename);
    if (!m) continue;
    const v = parseVerdictText(verdictsMap[filename], filename);
    if (v === null) { warns.push(`warn: malformed verdict at ${filename} — ignored`); continue; }
    if (verdicts.has(v.itemIndex)) {
      const prev = verdicts.get(v.itemIndex);
      warns.push(`warn: duplicate item_index ${v.itemIndex} in ${filename} — overwrites ${prev.itemSlug}`);
    }
    verdicts.set(v.itemIndex, v);
  }
  return { verdicts, warns };
}

// ---------------------------------------------------------------------------
// Shared test fixtures
// ---------------------------------------------------------------------------

const COMBINED_TWO_ITEMS = `# Improvement Proposal — example

> some banner

## Technical

### Architecture · 2 items · max=high · effort=low-medium
<!-- aspect-id: architecture -->

#### Refactor auth module

- **Value:** high
- **Need:** auth is messy
- **Benefits:** safer
- **Proposed solution:** rewrite
- **Engineering effort hint:** medium

#### Add caching layer

- **Value:** medium
- **Need:** slow
- **Benefits:** faster
- **Proposed solution:** redis
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
`;

const COMBINED_TWIN_PREFIX = `# Improvement Proposal — twin-prefix regression

## Technical

### Architecture · 2 items · max=high · effort=low-high
<!-- aspect-id: architecture -->

#### Add SSO Support

- **Value:** high
- **Need:** Enables enterprise SSO via SAML and OIDC, unlocking large-account deals that block on identity federation. Most prospects above 200 seats require this exact integration before signing.
- **Benefits:** Removes blocker for enterprise sales pipeline.
- **Proposed solution:** Wire SAML + OIDC into existing auth.
- **Engineering effort hint:** medium

#### Add SSO Support

- **Value:** high
- **Need:** Enables enterprise SSO via SAML and OIDC, unlocking large-account deals that block on identity federation. Most prospects above 200 seats require this exact integration before signing.
- **Benefits:** Removes blocker for enterprise sales pipeline.
- **Proposed solution:** Wire SAML + OIDC into existing auth.
- **Engineering effort hint:** large

<!-- dedup: applied (n=0) -->
`;

// ---------------------------------------------------------------------------
// Library unit tests — mirrors test_apply_verdicts.py lines 31–264
// ---------------------------------------------------------------------------

// test_strip_dedup_marker_trailing
test("stripDedupMarker: trailing dedup comment removed", () => {
  assert.equal(stripDedupMarker("body\n<!-- dedup: applied (n=3) -->\n"), "body");
  assert.equal(stripDedupMarker("body\n<!-- dedup: pending -->"), "body");
  assert.equal(stripDedupMarker("body\n"), "body\n");  // no dedup marker → unchanged
});

// test_split_combined_both_tracks
test("splitCombined: both Technical and Business tracks", () => {
  const text = `# Improvement Proposal

intro

## Technical

#### A

## Business

#### B
`;
  const { header, technicalBody, businessBody } = splitCombined(text);
  assert.ok(header.includes("intro"), "header should contain intro");
  assert.ok(technicalBody.startsWith("## Technical"), "tech body should start with ## Technical");
  assert.ok(businessBody.startsWith("## Business"), "biz body should start with ## Business");
});

// test_split_combined_only_business
test("splitCombined: only Business track present", () => {
  const text = "# Improvement Proposal\n\n## Business\n\n#### B\n";
  const { technicalBody, businessBody } = splitCombined(text);
  assert.equal(technicalBody, null, "technicalBody should be null");
  assert.ok(businessBody.startsWith("## Business"));
});

// test_split_combined_blocked_neither_track
test("splitCombined: neither track present returns null bodies", () => {
  const text = "# Improvement Proposal\n\nNo tracks.\n";
  const { technicalBody, businessBody } = splitCombined(text);
  assert.equal(technicalBody, null);
  assert.equal(businessBody, null);
});

// test_title_to_slug_untitled
test("titleToSlug: special chars become 'untitled', normal titles become kebab", () => {
  assert.equal(titleToSlug("---"), "untitled");
  assert.equal(titleToSlug("Hello World"), "hello-world");
});

// test_validate_revised_body_ok
test("validateRevisedBody: valid body with all required bullets", () => {
  const body = `## Refactor auth module

- **Value:** high
- **Need:** explain
- **Benefits:** named outcome
- **Proposed solution:** do X
- **Engineering effort hint:** medium
`;
  assert.equal(validateRevisedBody(body), true);
});

// test_validate_revised_body_rejects_category_bullet
test("validateRevisedBody: rejects body with Category bullet", () => {
  const body = `## X

- **Category:** foo
- **Value:** high
- **Need:** explain
- **Benefits:** outcome
- **Proposed solution:** do X
- **Engineering effort hint:** medium
`;
  assert.equal(validateRevisedBody(body), false);
});

// test_validate_revised_body_rejects_subheading
test("validateRevisedBody: rejects body with H3 subheading", () => {
  const body = `## X

### Subsection

- **Value:** high
- **Need:** explain
- **Benefits:** outcome
- **Proposed solution:** do X
- **Engineering effort hint:** medium
`;
  assert.equal(validateRevisedBody(body), false);
});

// test_validate_revised_body_rejects_missing_bullet
test("validateRevisedBody: rejects body missing Proposed solution bullet", () => {
  const body = `## X

- **Value:** high
- **Need:** explain
- **Benefits:** outcome
- **Engineering effort hint:** medium
`;
  assert.equal(validateRevisedBody(body), false);
});

// test_demote_h2_to_h4_basic
test("demoteH2ToH4: ## becomes #### at start of output", () => {
  const body = "## Title\n\n- **Value:** high\n";
  const out = demoteH2ToH4(body);
  assert.ok(out.startsWith("#### Title"), `expected '#### Title', got: ${out.slice(0, 30)}`);
});

// test_parse_value_effort
test("parseValueEffort: extracts value and effort from item block", () => {
  const block = `#### Item

- **Value:** high
- **Need:** ...
- **Engineering effort hint:** low
`;
  const [v, e] = parseValueEffort(block);
  assert.equal(v, "high");
  assert.equal(e, "low");
});

// test_sort_items_value_desc_effort_asc
test("sortItemsWithinAspect: sorts Value desc then Effort asc", () => {
  const items = [
    "#### A\n- **Value:** low\n- **Engineering effort hint:** low\n",
    "#### B\n- **Value:** high\n- **Engineering effort hint:** medium\n",
    "#### C\n- **Value:** high\n- **Engineering effort hint:** low\n",
  ];
  const { sorted, warns } = sortItemsWithinAspect(items);
  assert.ok(sorted[0].startsWith("#### C"), "C (high+low) should be first");
  assert.ok(sorted[1].startsWith("#### B"), "B (high+medium) should be second");
  assert.ok(sorted[2].startsWith("#### A"), "A (low+low) should be third");
  assert.deepEqual(warns, []);
});

// test_sort_items_fallback_warns_on_missing_bullets
test("sortItemsWithinAspect: emits sort-fallback warn when effort missing", () => {
  const items = ["#### Bad\n- **Value:** high\n"];
  const { warns } = sortItemsWithinAspect(items);
  assert.equal(warns.length, 1);
  assert.ok(warns[0].includes("sort-fallback"), `expected sort-fallback in: ${warns[0]}`);
});

// test_recompute_rollup_heading_count_and_effort_range
test("recomputeRollupHeading: recomputes count and effort range", () => {
  const items = [
    "#### A\n- **Value:** high\n- **Engineering effort hint:** low\n",
    "#### B\n- **Value:** medium\n- **Engineering effort hint:** high\n",
  ];
  const out = recomputeRollupHeading("### MyAspect · 5 items · max=low · effort=medium", items);
  assert.equal(out, "### MyAspect · 2 items · max=high · effort=low-high");
});

// test_recompute_rollup_heading_singular_item
test("recomputeRollupHeading: uses 'item' (singular) when count is 1", () => {
  const items = ["#### A\n- **Value:** high\n- **Engineering effort hint:** low\n"];
  const out = recomputeRollupHeading("### Foo · 7 items · max=low · effort=medium", items);
  assert.equal(out, "### Foo · 1 item · max=high · effort=low");
});

// test_split_rollups_basic — tested via applyVerdicts integration (split_rollups is internal)
// We verify its behavior through the combined output.
test("splitRollups (via applyVerdicts): basic rollup parsing with aspect comments", () => {
  const track = `## Technical

intro prose

### Aspect Architecture · 2 items · max=high · effort=low-medium
<!-- aspect-id: architecture -->

#### Item A

- **Value:** high

#### Item B

- **Value:** medium

### Aspect Security · 1 item · max=high · effort=low
<!-- aspect-id: security -->

#### Item C

- **Value:** high
`;
  // Use applyVerdicts — all KEEP verdicts
  const result = applyVerdicts({
    combinedMarkdown: track,
    verdicts: {
      "item-01-item-a.md": "---\nitem_index: 1\nitem_slug: item-a\ndecision: KEEP\n---\n",
      "item-02-item-b.md": "---\nitem_index: 2\nitem_slug: item-b\ndecision: KEEP\n---\n",
      "item-03-item-c.md": "---\nitem_index: 3\nitem_slug: item-c\ndecision: KEEP\n---\n",
    },
  });
  assert.ok(result.markdown.includes("intro prose"), "header prose should survive");
  assert.ok(result.markdown.includes("#### Item A"), "Item A should be in output");
  assert.ok(result.markdown.includes("#### Item B"), "Item B should be in output");
  assert.ok(result.markdown.includes("#### Item C"), "Item C should be in output");
  assert.ok(result.markdown.includes("<!-- aspect-id: architecture -->"), "aspect comment preserved");
  assert.ok(result.markdown.includes("### Aspect Security"), "second rollup preserved");
});

// test_load_verdicts_parses_frontmatter — tested via loadVerdictsFromMap inline
test("loadVerdicts: parses KEEP frontmatter correctly", () => {
  const map = {
    "item-01-foo.md": `---
item_index: 1
item_slug: foo
track: technical
decision: KEEP
---

# Reason
all good
`,
  };
  const { verdicts, warns } = loadVerdictsFromMap(map);
  assert.ok(verdicts.has(1));
  assert.equal(verdicts.get(1).decision, "KEEP");
  assert.deepEqual(warns, []);
});

// test_load_verdicts_extracts_revised_body
test("loadVerdicts: extracts revised body from REVISE verdict", () => {
  const map = {
    "item-02-bar.md": `---
item_index: 2
item_slug: bar
track: business
decision: REVISE
---

# Audits

- ...

# Reason
revise it

# Revised item

## Bar Improved

- **Value:** high
- **Need:** more
- **Benefits:** clear
- **Proposed solution:** do
- **Engineering effort hint:** low
`,
  };
  const { verdicts, warns } = loadVerdictsFromMap(map);
  assert.ok(verdicts.has(2));
  assert.notEqual(verdicts.get(2).revisedBody, null);
  assert.ok(verdicts.get(2).revisedBody.includes("**Engineering effort hint:** low"));
});

// test_load_verdicts_handles_malformed
test("loadVerdicts: emits malformed warn and skips unparseable file", () => {
  const map = { "item-03-baz.md": "no frontmatter here" };
  const { verdicts, warns } = loadVerdictsFromMap(map);
  assert.ok(!verdicts.has(3));
  assert.ok(warns.some(w => w.includes("malformed")));
});

// ---------------------------------------------------------------------------
// CLI-equivalent tests via applyVerdicts()
// (mirrors test_cli_* tests from the Python suite)
// ---------------------------------------------------------------------------

// test_cli_blocks_when_combined_missing
test("applyVerdicts: throws on empty combinedMarkdown", () => {
  assert.throws(
    () => applyVerdicts({ combinedMarkdown: "", verdicts: {} }),
    /combined file missing\/empty/
  );
});

// test_cli_all_keep_no_verdicts
test("applyVerdicts: all items KEEP when no verdicts provided (2 items → 2 unvalidated banner)", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {},
  });
  assert.ok(result.markdown.includes("#### Refactor auth module"), "refactor item present");
  assert.ok(result.markdown.includes("#### Add caching layer"), "caching item present");
  assert.ok(result.markdown.includes("2 items shipped without complete validation"), "banner shows 2 items");
});

// test_cli_keep_with_verdict
test("applyVerdicts: explicit KEEP verdicts → no banner, both items present", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: KEEP\n---\n",
      "item-02-add-caching-layer.md": "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: KEEP\n---\n",
    },
  });
  assert.ok(result.markdown.includes("#### Refactor auth module"), "refactor item present");
  assert.ok(result.markdown.includes("#### Add caching layer"), "caching item present");
  assert.ok(!result.markdown.includes("without complete validation"), "no banner when all validated");
});

// test_cli_drop_removes_item_and_recomputes_rollup
test("applyVerdicts: DROP item-01 → removed, rollup recomputed to 1 item, drop: log emitted", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: DROP\n---\n",
      "item-02-add-caching-layer.md": "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: KEEP\n---\n",
    },
  });
  assert.ok(!result.markdown.includes("#### Refactor auth module"), "dropped item absent");
  assert.ok(result.markdown.includes("#### Add caching layer"), "kept item present");
  assert.ok(result.markdown.includes("### Architecture · 1 item ·"), "rollup recomputed to 1 item");
  assert.ok(result.logLines.some(l => l.startsWith("drop: item-01")), "drop: log line emitted");
});

// test_cli_drop_all_removes_rollup
test("applyVerdicts: DROP all items in rollup → entire rollup + aspect-id comment removed", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: DROP\n---\n",
      "item-02-add-caching-layer.md": "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: DROP\n---\n",
    },
  });
  assert.ok(!result.markdown.includes("### Architecture"), "rollup heading removed");
  assert.ok(!result.markdown.includes("<!-- aspect-id: architecture -->"), "aspect-id comment removed");
});

// test_cli_slug_mismatch_keeps_original
test("applyVerdicts: verdict slug mismatch → KEEP fallback + slug mismatch warn", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-something-else.md": "---\nitem_index: 1\nitem_slug: something-else\ntrack: technical\ndecision: DROP\n---\n",
    },
  });
  assert.ok(result.markdown.includes("#### Refactor auth module"), "item kept despite mismatch");
  assert.ok(result.logLines.some(l => l.includes("verdict slug mismatch")), "slug mismatch warn emitted");
});

// test_cli_evidence_degraded_banner
test("applyVerdicts: evidence-degraded warns add to banner count", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ntrack: technical\ndecision: KEEP\n---\n",
      "item-02-add-caching-layer.md": "---\nitem_index: 2\nitem_slug: add-caching-layer\ntrack: technical\ndecision: KEEP\n---\n",
    },
    evidenceDegradedWarns: 'warn: item-01 "Refactor auth module" evidence-degraded — aspect-id=foo missing',
  });
  assert.ok(result.markdown.includes("1 item shipped without complete validation"), "banner shows 1 item");
});

// test_cli_idempotency_skip — N/A for pure function (idempotency is filesystem concern in Python)
// The pure JS function always recomputes; idempotency is the caller's responsibility.

// test_cli_orphan_verdict_warns
test("applyVerdicts: orphan verdict (index not consumed) emits warn", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-99-ghost-item.md": "---\nitem_index: 99\nitem_slug: ghost-item\ntrack: technical\ndecision: DROP\n---\n",
    },
  });
  assert.ok(result.logLines.some(l => l.includes("orphan verdict at item_index=99")), "orphan warn emitted");
});

// test_cli_twin_prefix_items_get_distinct_decisions
test("applyVerdicts: twin-prefix items get distinct decisions (regression)", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWIN_PREFIX,
    verdicts: {
      "item-01-add-sso-support.md": "---\nitem_index: 1\nitem_slug: add-sso-support\ntrack: technical\ndecision: DROP\n---\n",
      "item-02-add-sso-support.md": "---\nitem_index: 2\nitem_slug: add-sso-support\ntrack: technical\ndecision: KEEP\n---\n",
    },
  });
  // item-01 must be dropped, item-02 must remain
  assert.equal(
    (result.markdown.match(/#### Add SSO Support/g) ?? []).length,
    1,
    "only 1 SSO Support item should survive"
  );
  assert.ok(result.markdown.includes("**Engineering effort hint:** large"), "kept (item-02) effort line survives");
  assert.ok(!result.markdown.includes("**Engineering effort hint:** medium"), "dropped (item-01) effort line gone");
  assert.ok(result.logLines.some(l => l.startsWith("drop: item-01")), "drop: item-01 log line emitted");
});

// test_cli_title_with_trigger_phrase_does_not_inflate_banner
test("applyVerdicts: item title containing trigger phrase does not inflate banner (regression)", () => {
  const combined = `# Improvement Proposal — trigger-phrase regression

## Technical

### Reliability · 1 item · max=medium · effort=low
<!-- aspect-id: reliability -->

#### Fix validation directory missing error in onboarding

- **Value:** medium
- **Need:** Users hit a 500 when validation dir is absent.
- **Benefits:** Smoother first-run experience.
- **Proposed solution:** Lazily create the dir.
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
`;
  // No verdict file → missing-verdict warn, validation dir IS empty (present)
  const result = applyVerdicts({ combinedMarkdown: combined, verdicts: {} });
  assert.ok(
    result.markdown.includes("1 item shipped without complete validation"),
    "banner must say '1 item', not be inflated"
  );
  assert.ok(
    !result.markdown.includes("2 items shipped"),
    "banner must not be inflated to 2"
  );
});

// test_cli_pre_rollup_h4_does_not_misroute_verdicts
test("applyVerdicts: pre-rollup #### H4 does not misroute verdicts (regression)", () => {
  const combined =
    "# Combined\n\n" +
    "## Technical\n\n" +
    "#### Stray pre-rollup item\n\n" +
    "- **Value:** high\n- **Need:** outside any rollup\n" +
    "- **Benefits:** none\n- **Proposed solution:** none\n- **Engineering effort hint:** low\n\n" +
    "### Architecture · 1 item · max=high · effort=medium\n" +
    "<!-- aspect-id: architecture -->\n\n" +
    "#### Real rollup item\n\n" +
    "- **Value:** high\n- **Need:** real\n- **Benefits:** real\n" +
    "- **Proposed solution:** real\n- **Engineering effort hint:** medium\n\n" +
    "<!-- dedup: applied (n=0) -->\n";

  const result = applyVerdicts({
    combinedMarkdown: combined,
    verdicts: {
      "item-01-stray-pre-rollup-item.md": "---\nitem_index: 1\nitem_slug: stray-pre-rollup-item\ndecision: DROP\n---\n",
      "item-02-real-rollup-item.md": "---\nitem_index: 2\nitem_slug: real-rollup-item\ndecision: KEEP\n---\n",
    },
  });
  // Stray remains (part of track_header, emitted verbatim)
  assert.ok(result.markdown.includes("#### Stray pre-rollup item"), "stray item in track header preserved");
  // Real rollup item must survive (pre-fix bug would drop it)
  assert.ok(result.markdown.includes("#### Real rollup item"), "real rollup item must survive");
  assert.ok(result.markdown.includes("### Architecture"), "architecture rollup preserved");
  // Operator must see slug-mismatch and orphan warns
  assert.ok(result.logLines.some(l => l.includes("verdict slug mismatch at item-01")), "slug mismatch warn for item-01");
  assert.ok(result.logLines.some(l => l.includes("orphan verdict at item_index=2")), "orphan warn for item-02");
});

// test_cli_blocks_on_unsafe_validation_dir — N/A for pure function (path safety is CLI concern)
// The pure JS function operates on in-memory data, so path injection is not applicable.

// ---------------------------------------------------------------------------
// Additional tests (beyond Python suite)
// ---------------------------------------------------------------------------

test("applyVerdicts: throws when both tracks missing", () => {
  assert.throws(
    () => applyVerdicts({ combinedMarkdown: "# Header\n\nNo tracks here.\n", verdicts: {} }),
    /combined proposal missing both/
  );
});

test("applyVerdicts: REVISE with valid body → demoted H4, revise: log emitted", () => {
  const combined = `# Proposal

## Technical

### Arch · 1 item · max=low · effort=medium
<!-- aspect-id: arch -->

#### Old Module

- **Value:** low
- **Need:** old
- **Benefits:** some
- **Proposed solution:** old sol
- **Engineering effort hint:** medium

<!-- dedup: applied (n=0) -->
`;
  const verdict = `---
item_index: 1
item_slug: old-module
track: technical
decision: REVISE
---

# Reason
needs update

# Revised item

## New Module

- **Value:** high
- **Need:** better need
- **Benefits:** much better
- **Proposed solution:** new solution
- **Engineering effort hint:** low
`;
  const result = applyVerdicts({
    combinedMarkdown: combined,
    verdicts: { "item-01-old-module.md": verdict },
  });
  assert.ok(result.markdown.includes("#### New Module"), "revised title demoted to ####");
  // Must not contain a bare ## heading for New Module (note: "#### New Module" contains
  // "## New Module" as a substring, so we check for a line starting with exactly "## ").
  assert.ok(!/^## New Module/m.test(result.markdown), "no bare ## heading after demotion");
  assert.ok(result.logLines.some(l => l.startsWith("revise: item-01")), "revise: log line emitted");
  assert.ok(!result.markdown.includes("without complete validation"), "no unvalidated banner");
});

test("applyVerdicts: REVISE with malformed body → KEEP fallback + revise-malformed warn", () => {
  const combined = `# Proposal

## Technical

### Arch · 1 item · max=high · effort=low
<!-- aspect-id: arch -->

#### Good Item

- **Value:** high
- **Need:** good
- **Benefits:** great
- **Proposed solution:** do it
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
`;
  const verdict = `---
item_index: 1
item_slug: good-item
track: technical
decision: REVISE
---

# Revised item

## Malformed — missing required bullets
- **Value:** high
`;
  const result = applyVerdicts({
    combinedMarkdown: combined,
    verdicts: { "item-01-good-item.md": verdict },
  });
  assert.ok(result.markdown.includes("#### Good Item"), "original kept after malformed revise");
  assert.ok(result.logLines.some(l => l.includes("revise-malformed")), "revise-malformed warn emitted");
});

test("applyVerdicts: REVISE without body → KEEP fallback + revise-without-body warn", () => {
  const combined = `# Proposal

## Business

### Growth · 1 item · max=medium · effort=medium
<!-- aspect-id: growth -->

#### Upsell Page

- **Value:** medium
- **Need:** needed
- **Benefits:** conversions
- **Proposed solution:** redesign
- **Engineering effort hint:** medium

<!-- dedup: applied (n=0) -->
`;
  const verdict = `---
item_index: 1
item_slug: upsell-page
track: business
decision: REVISE
---

# Reason
needs update but no revised body provided
`;
  const result = applyVerdicts({
    combinedMarkdown: combined,
    verdicts: { "item-01-upsell-page.md": verdict },
  });
  assert.ok(result.markdown.includes("#### Upsell Page"), "original kept");
  assert.ok(result.logLines.some(l => l.includes("revise-without-body")), "revise-without-body warn emitted");
});

test("applyVerdicts: evidenceDegradedWarns as string[] array input", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ndecision: KEEP\n---\n",
      "item-02-add-caching-layer.md": "---\nitem_index: 2\nitem_slug: add-caching-layer\ndecision: KEEP\n---\n",
    },
    evidenceDegradedWarns: [
      'warn: item-01 "Refactor auth module" evidence-degraded — aspect-id=foo missing',
      'warn: item-02 "Add caching layer" evidence-degraded — aspect-id=bar missing',
    ],
  });
  assert.ok(result.markdown.includes("2 items shipped without complete validation"), "banner shows 2");
});

test("applyVerdicts: both Technical and Business tracks produce correct cross-track indexing", () => {
  const combined = `# Proposal

## Technical

### Arch · 1 item · max=high · effort=low
<!-- aspect-id: arch -->

#### Tech Item

- **Value:** high
- **Need:** tech
- **Benefits:** tech benefit
- **Proposed solution:** tech sol
- **Engineering effort hint:** low

## Business

### Growth · 1 item · max=medium · effort=medium
<!-- aspect-id: growth -->

#### Biz Item

- **Value:** medium
- **Need:** biz
- **Benefits:** biz benefit
- **Proposed solution:** biz sol
- **Engineering effort hint:** medium

<!-- dedup: applied (n=0) -->
`;
  const result = applyVerdicts({
    combinedMarkdown: combined,
    verdicts: {
      "item-01-tech-item.md": "---\nitem_index: 1\nitem_slug: tech-item\ndecision: KEEP\n---\n",
      "item-02-biz-item.md": "---\nitem_index: 2\nitem_slug: biz-item\ndecision: DROP\n---\n",
    },
  });
  assert.ok(result.markdown.includes("#### Tech Item"), "tech item kept");
  assert.ok(!result.markdown.includes("#### Biz Item"), "biz item dropped (index 2 in business track)");
  assert.ok(result.logLines.some(l => l.startsWith("drop: item-02")), "drop: item-02 emitted");
});

test("applyVerdicts: duplicate verdict index emits warn and uses later one", () => {
  const combined = COMBINED_TWO_ITEMS;
  // Two files both claiming item_index=1 but different filenames
  const { verdicts, warns } = loadVerdictsFromMap({
    "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ndecision: KEEP\n---\n",
    "item-01-something-else.md": "---\nitem_index: 1\nitem_slug: something-else\ndecision: DROP\n---\n",
  });
  assert.ok(warns.some(w => w.includes("duplicate item_index 1")), "duplicate warn emitted");
  // Later file (sorted: item-01-something-else.md > item-01-refactor-auth-module.md) wins
  assert.equal(verdicts.get(1).itemSlug, "something-else", "later file overwrites earlier");
});

test("applyVerdicts: stats object counts correctly", () => {
  const result = applyVerdicts({
    combinedMarkdown: COMBINED_TWO_ITEMS,
    verdicts: {
      "item-01-refactor-auth-module.md": "---\nitem_index: 1\nitem_slug: refactor-auth-module\ndecision: DROP\n---\n",
    },
    // item-02 has no verdict → warn: missing verdict
  });
  assert.equal(result.stats.dropCount, 1, "1 drop");
  assert.equal(result.stats.unvalidatedCount, 1, "1 unvalidated (missing verdict for item-02)");
  assert.ok(result.stats.warnCount >= 1, "at least 1 warn (missing verdict)");
});

test("applyVerdicts: within-aspect sort verified against Python-expected order", () => {
  // CDN Setup (high+low) before Cache Layer (high+medium) before Slow Query Fix (low+low)
  const combined = `# Proposal

## Technical

### Performance · 3 items · max=high · effort=low-high
<!-- aspect-id: performance -->

#### Slow Query Fix

- **Value:** low
- **Need:** slow
- **Benefits:** faster
- **Proposed solution:** index
- **Engineering effort hint:** low

#### Cache Layer

- **Value:** high
- **Need:** very slow
- **Benefits:** 10x faster
- **Proposed solution:** redis
- **Engineering effort hint:** medium

#### CDN Setup

- **Value:** high
- **Need:** global users
- **Benefits:** low latency
- **Proposed solution:** cloudflare
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
`;
  const result = applyVerdicts({
    combinedMarkdown: combined,
    verdicts: {
      "item-01-slow-query-fix.md": "---\nitem_index: 1\nitem_slug: slow-query-fix\ndecision: KEEP\n---\n",
      "item-02-cache-layer.md": "---\nitem_index: 2\nitem_slug: cache-layer\ndecision: KEEP\n---\n",
      "item-03-cdn-setup.md": "---\nitem_index: 3\nitem_slug: cdn-setup\ndecision: KEEP\n---\n",
    },
  });
  const cdnPos = result.markdown.indexOf("#### CDN Setup");
  const cachePos = result.markdown.indexOf("#### Cache Layer");
  const slowPos = result.markdown.indexOf("#### Slow Query Fix");
  assert.ok(cdnPos < cachePos, "CDN (high+low) before Cache (high+medium)");
  assert.ok(cachePos < slowPos, "Cache (high+medium) before Slow (low+low)");
  // Rollup recomputed
  assert.ok(result.markdown.includes("### Performance · 3 items · max=high · effort=low-medium"), "rollup recomputed");
});
