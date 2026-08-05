/**
 * combine.test.mjs — Node test suite for lib/combine.mjs.
 *
 * Covers every pure-function case for combineProposals and its internal helpers.
 *
 * Run:
 *   node --test claude/workflows/propose-improvements-workflow/__tests__/combine.test.mjs
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { combineProposals } from "../lib/combine.mjs";

// ---------------------------------------------------------------------------
// Helpers mirroring Python test helpers
// ---------------------------------------------------------------------------

/** Build a minimal proposal string matching _proposal() in test_combine.py. */
function proposal(trackH1, useCtx, body) {
  return `# ${trackH1}\n**Use context:** ${useCtx}\n\n${body}`;
}

// ---------------------------------------------------------------------------
// Extract internal helpers via module source eval
// ---------------------------------------------------------------------------

const MODULE_PATH = resolve(
  new URL(".", import.meta.url).pathname,
  "../lib/combine.mjs"
);
const MODULE_SRC = readFileSync(MODULE_PATH, "utf-8");

// Strip the `export` keyword from combineProposals so eval can define it.
// Also strip the CLI-only import block (node:fs, node:path, etc.) since we're
// evaluating the pure-logic portion only. We guard by removing the `import`
// lines and the `export` keyword, then eval to extract helpers.
const helperSrc = MODULE_SRC
  .replace(/^import \{[^}]+\} from "node:[^"]+";$/gm, "")
  .replace(/^import \{[^}]+\} from "node:[^"]+";$/gm, "")
  .replace(/^export function combineProposals/m, "function combineProposals")
  // Remove the CLI main() and guard block at the bottom (after the pure API).
  .replace(/\/\/ -+\n\/\/ CLI shim[\s\S]*$/, "");

const _helpers = Function(`
  "use strict";
  ${helperSrc}
  return {
    parseUseContextMarker,
    stripH1AndUseContext,
    demoteHeadings,
    prepareTrackBody,
    buildCombined,
    combineProposals,
  };
`)();

const {
  parseUseContextMarker,
  stripH1AndUseContext,
  demoteHeadings,
  prepareTrackBody,
  buildCombined,
} = _helpers;

// ---------------------------------------------------------------------------
// Test group: strip_h1_and_use_context
// ---------------------------------------------------------------------------

test("strip_h1_and_use_context — ATX H1 + use context removed", () => {
  const src = "# Title\n**Use context:** internal\n\n## Body\nfoo";
  assert.equal(stripH1AndUseContext(src), "## Body\nfoo");
});

test("strip_h1_and_use_context — setext H1 removed", () => {
  const src = "Title\n=====\n**Use context:** hybrid\n\n## Body";
  assert.equal(stripH1AndUseContext(src), "## Body");
});

test("strip_h1_and_use_context — skips when no H1", () => {
  const src = "Not a heading\nMore lines";
  assert.equal(stripH1AndUseContext(src), src);
});

test("strip_h1_and_use_context — HTML comments pass through elsewhere", () => {
  const src = "# Title\n**Use context:** internal\n\n<!-- preserved -->\n## Body";
  const out = stripH1AndUseContext(src);
  assert.ok(out.includes("<!-- preserved -->"), `expected '<!-- preserved -->' in:\n${out}`);
});

test("strip_h1_and_use_context — H1 only (no use context line)", () => {
  const src = "# Title\n\n## Body";
  const out = stripH1AndUseContext(src);
  assert.equal(out, "## Body");
});

// ---------------------------------------------------------------------------
// Test group: parse_use_context_marker
// ---------------------------------------------------------------------------

test("parse_use_context_marker — basic internal", () => {
  assert.equal(
    parseUseContextMarker("# T\n**Use context:** internal\n## X"),
    "internal"
  );
});

test("parse_use_context_marker — case insensitive", () => {
  assert.equal(
    parseUseContextMarker("# T\n**USE CONTEXT:** Hybrid\n## X"),
    "hybrid"
  );
});

test("parse_use_context_marker — invalid value returns null", () => {
  assert.equal(parseUseContextMarker("# T\n**Use context:** bogus\n"), null);
});

test("parse_use_context_marker — stops at first H2", () => {
  const src = "# T\n## Body\n**Use context:** internal\n";
  assert.equal(parseUseContextMarker(src), null);
});

// ---------------------------------------------------------------------------
// Test group: demote_headings — order + fence handling
// ---------------------------------------------------------------------------

test("demote_headings — strict two-pass order (no double-demotion)", () => {
  const src = "## Foo\n### Bar";
  assert.equal(demoteHeadings(src), "### Foo\n#### Bar");
});

test("demote_headings — skips fenced code block (backtick)", () => {
  const src = "## Real\n```\n## In code\n### Also code\n```\n### After\n";
  const out = demoteHeadings(src);
  assert.ok(out.includes("### Real"), `missing '### Real' in:\n${out}`);
  assert.ok(out.includes("## In code"), `fenced H2 should be untouched in:\n${out}`);
  assert.ok(out.includes("### Also code"), `fenced H3 should be untouched in:\n${out}`);
  assert.ok(out.includes("#### After"), `missing '#### After' in:\n${out}`);
});

test("demote_headings — tilde fence with run-length rule (shorter ~~~ does not close ~~~~~)", () => {
  const src = "~~~~~\n## Inside\n~~~\nstill inside\n~~~~~\n## After\n";
  const out = demoteHeadings(src);
  assert.ok(out.includes("## Inside"), `fenced H2 should be untouched in:\n${out}`);
  assert.ok(out.includes("### After"), `missing '### After' in:\n${out}`);
});

test("demote_headings — indented heading (0-3 leading spaces)", () => {
  const src = "   ## Indented\n   ### Item";
  const out = demoteHeadings(src);
  assert.ok(out.includes("   ### Indented"), `missing '   ### Indented' in:\n${out}`);
  assert.ok(out.includes("   #### Item"), `missing '   #### Item' in:\n${out}`);
});

test("demote_headings — ignores H4 and deeper", () => {
  const src = "## A\n### B\n#### C\n##### D\n";
  const out = demoteHeadings(src);
  assert.ok(out.includes("### A"), `missing '### A' in:\n${out}`);
  assert.ok(out.includes("#### B"), `missing '#### B' in:\n${out}`);
  assert.ok(out.includes("#### C"), `H4 should be untouched in:\n${out}`);
  assert.ok(out.includes("##### D"), `H5 should be untouched in:\n${out}`);
});

// ---------------------------------------------------------------------------
// Test group: build_combined
// ---------------------------------------------------------------------------

test("build_combined — both tracks present", () => {
  const out = buildCombined({
    projectName: "proj",
    isoDate: "2026-05-18",
    useContext: "internal",
    techBody: "### Aspect\n#### Item",
    bizBody: "### B-Aspect",
  });
  assert.ok(out.includes("# Improvement Proposal — proj"), `missing H1 in:\n${out}`);
  assert.ok(out.includes("Use context: **internal**"), `missing badge in:\n${out}`);
  assert.ok(out.includes("## Technical"), `missing ## Technical in:\n${out}`);
  assert.ok(out.includes("## Business"), `missing ## Business in:\n${out}`);
  assert.ok(out.trimEnd().endsWith("<!-- dedup: pending -->"), `missing dedup marker in:\n${out}`);
});

test("build_combined — omits Business section when biz absent", () => {
  const out = buildCombined({
    projectName: "proj",
    isoDate: "2026-05-18",
    useContext: "hybrid",
    techBody: "### A",
    bizBody: null,
  });
  assert.ok(out.includes("## Technical"), `missing ## Technical in:\n${out}`);
  assert.ok(!out.includes("## Business"), `unexpected ## Business in:\n${out}`);
  assert.ok(out.includes("<!-- dedup: pending -->"), `missing dedup marker in:\n${out}`);
});

test("build_combined — omits Technical section when tech absent", () => {
  const out = buildCombined({
    projectName: "proj",
    isoDate: "2026-05-18",
    useContext: "customer-facing",
    techBody: null,
    bizBody: "### B",
  });
  assert.ok(out.includes("## Business"), `missing ## Business in:\n${out}`);
  assert.ok(!out.includes("## Technical"), `unexpected ## Technical in:\n${out}`);
});

test("build_combined — omits use-context badge when null", () => {
  const out = buildCombined({
    projectName: "proj",
    isoDate: "2026-05-18",
    useContext: null,
    techBody: "### A",
    bizBody: null,
  });
  assert.ok(!out.includes("Use context"), `unexpected badge in:\n${out}`);
});

test("build_combined — throws when both tracks absent", () => {
  assert.throws(
    () => buildCombined({ projectName: "p", isoDate: "d", useContext: null, techBody: null, bizBody: null }),
    (err) => err instanceof TypeError
  );
});

// ---------------------------------------------------------------------------
// Test group: prepare_track_body integration
// ---------------------------------------------------------------------------

test("prepare_track_body — strips then demotes", () => {
  const src = proposal("Technical Proposal", "internal", "## Aspect\n### Item\n#### Detail");
  const out = prepareTrackBody(src);
  assert.ok(!out.includes("Technical Proposal"), `H1 should be stripped in:\n${out}`);
  assert.ok(!out.includes("Use context"), `use-context should be stripped in:\n${out}`);
  assert.ok(out.includes("### Aspect"), `H2 should be demoted to H3 in:\n${out}`);
  assert.ok(out.includes("#### Item"), `H3 should be demoted to H4 in:\n${out}`);
  assert.ok(out.includes("#### Detail"), `H4 should be untouched in:\n${out}`);
});

// ---------------------------------------------------------------------------
// Test group: combineProposals (mirrors CLI integration tests)
// ---------------------------------------------------------------------------

test("combineProposals — both tracks happy path", () => {
  const { markdown, warnings } = combineProposals({
    technicalProposal: proposal("Technical Proposal — p", "internal", "## Reliability\n### Add retries"),
    businessProposal: proposal("Business Proposal — p", "internal", "## Revenue\n### Upsell add-ons"),
    useContext: { useContext: "internal" },
    projectName: "p",
    dateStr: "2026-05-18",
  });
  assert.equal(warnings.length, 0);
  assert.ok(markdown.includes("## Technical"), `missing ## Technical in:\n${markdown}`);
  assert.ok(markdown.includes("## Business"), `missing ## Business in:\n${markdown}`);
  assert.ok(markdown.includes("### Reliability"), `H2 should be demoted in:\n${markdown}`);
  assert.ok(markdown.includes("#### Add retries"), `H3 should be demoted in:\n${markdown}`);
  assert.ok(markdown.trimEnd().endsWith("<!-- dedup: pending -->"), `missing dedup marker`);
});

test("combineProposals — use-context divergence emits warn", () => {
  const { warnings } = combineProposals({
    technicalProposal: proposal("T", "internal", "## A\n### x"),
    businessProposal: proposal("B", "hybrid", "## A\n### y"),
    useContext: null,
    projectName: "p",
    dateStr: "2026-05-18",
  });
  assert.ok(
    warnings.some((w) => w.includes("use-context divergence")),
    `expected divergence warning in: ${JSON.stringify(warnings)}`
  );
});

test("combineProposals — technical only", () => {
  const { markdown, warnings } = combineProposals({
    technicalProposal: proposal("T", "internal", "## A\n### x"),
    businessProposal: null,
    useContext: null,
    projectName: "p",
    dateStr: "2026-05-18",
  });
  assert.equal(warnings.length, 0);
  assert.ok(markdown.includes("## Technical"), `missing ## Technical`);
  assert.ok(!markdown.includes("## Business"), `unexpected ## Business`);
  assert.ok(markdown.includes("<!-- dedup: pending -->"), `missing dedup marker`);
});

test("combineProposals — business only", () => {
  const { markdown } = combineProposals({
    technicalProposal: null,
    businessProposal: proposal("B", "internal", "## A\n### x"),
    useContext: null,
    projectName: "p",
    dateStr: "2026-05-18",
  });
  assert.ok(markdown.includes("## Business"), `missing ## Business`);
  assert.ok(!markdown.includes("## Technical"), `unexpected ## Technical`);
});

test("combineProposals — throws BLOCKED when neither track provided", () => {
  assert.throws(
    () => combineProposals({
      technicalProposal: null,
      businessProposal: null,
      useContext: null,
      projectName: "p",
      dateStr: "2026-05-18",
    }),
    (err) => err instanceof TypeError && err.message.includes("no track proposal provided")
  );
});

test("combineProposals — throws BLOCKED when both tracks empty", () => {
  assert.throws(
    () => combineProposals({
      technicalProposal: "",
      businessProposal: "   \n\n",
      useContext: null,
      projectName: "p",
      dateStr: "2026-05-18",
    }),
    (err) => err instanceof TypeError && err.message.includes("missing/empty")
  );
});

test("combineProposals — use-context.json invalid value treated as null", () => {
  const { markdown } = combineProposals({
    technicalProposal: proposal("T", "internal", "## A"),
    businessProposal: null,
    useContext: { wrongKey: "internal" },
    projectName: "p",
    dateStr: "2026-05-18",
  });
  // jsonUseCtx = null (invalid key) → falls back to track marker "internal".
  assert.ok(markdown.includes("Use context: **internal**"), `expected badge from track marker:\n${markdown}`);
});

test("combineProposals — marker disagrees with use-context.json emits warn", () => {
  const { warnings } = combineProposals({
    technicalProposal: proposal("T", "internal", "## A"),
    businessProposal: null,
    useContext: { useContext: "hybrid" },
    projectName: "p",
    dateStr: "2026-05-18",
  });
  assert.ok(
    warnings.some((w) => w.includes("disagrees with use-context.json")),
    `expected disagrees-warning in: ${JSON.stringify(warnings)}`
  );
});

test("combineProposals — trailing newline always present", () => {
  const { markdown } = combineProposals({
    technicalProposal: proposal("T", "internal", "## A"),
    businessProposal: null,
    useContext: null,
    projectName: "p",
    dateStr: "2026-05-18",
  });
  assert.ok(markdown.endsWith("\n"), "output must end with a newline");
});
