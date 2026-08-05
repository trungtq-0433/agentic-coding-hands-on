/**
 * phase-d-prep.test.mjs — unit tests for the slimmed phase-d-prep splitter.
 *
 * phase-d-prep now only splits combined-initial.md into one per-item payload
 * (carrying just the proposal item's markdown) + a manifest. The validator
 * self-verifies against the repo, so there is no evidence / stack-context /
 * use-context machinery left to test.
 *
 * Run: node --test claude/workflows/propose-improvements-workflow/__tests__/phase-d-prep.test.mjs
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  titleToSlug,
  validateFilenameSlug,
  parseItems,
  rewriteH4ToH2,
  buildPhaseDPayloads,
  computeSha256,
} from "../lib/phase-d-prep.mjs";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Wrap body with the required trailing dedup-applied marker. */
function buildCombined(body) {
  if (!body.endsWith("\n")) body += "\n";
  return body + "<!-- dedup: applied (n=0) -->\n";
}

// ---------------------------------------------------------------------------
// Pure helper tests
// ---------------------------------------------------------------------------

describe("titleToSlug", () => {
  it("basic conversion", () => {
    assert.equal(titleToSlug("Hello World"), "hello-world");
    assert.equal(titleToSlug("  Mixed CASE — punct!  "), "mixed-case-punct");
  });

  it("untitled fallback for non-ascii and dash-only", () => {
    assert.equal(titleToSlug("アプリ改善"), "untitled");
    assert.equal(titleToSlug("---"), "untitled");
  });
});

describe("validateFilenameSlug", () => {
  it("accepts valid slug", () => {
    assert.ok(validateFilenameSlug("auth-mfa"));
  });
  it("rejects leading dash and empty", () => {
    assert.ok(!validateFilenameSlug("-leading-dash"));
    assert.ok(!validateFilenameSlug(""));
  });
});

describe("parseItems", () => {
  it("basic two-track document", () => {
    const combined = `\
# Improvement Proposal

## Technical

### Architecture · group-1
<!-- aspect-id: architecture -->

#### Refactor auth module

- Value: high
- Need: ...

#### Add caching layer

- Value: medium

## Business

### UX · group-1
<!-- aspect-id: ux-gaps -->

#### Improve signup
- Value: high
`;
    const items = parseItems(combined);
    assert.deepEqual(
      items.map((i) => i.title),
      ["Refactor auth module", "Add caching layer", "Improve signup"]
    );
    assert.deepEqual(
      items.map((i) => i.track),
      ["technical", "technical", "business"]
    );
    assert.deepEqual(
      items.map((i) => i.index),
      [1, 2, 3]
    );
  });

  it("ignores H4 inside fenced code block", () => {
    const combined = `\
## Technical

### Group
<!-- aspect-id: x -->

#### Real item

\`\`\`
#### Fake item inside fence
\`\`\`

#### Real item 2
`;
    const items = parseItems(combined);
    assert.deepEqual(
      items.map((i) => i.title),
      ["Real item", "Real item 2"]
    );
  });

  it("ignores #### outside any track section", () => {
    const combined = `\
# Heading

#### Orphan item before any track

## Technical

### Group
<!-- aspect-id: x -->

#### Real item
`;
    const items = parseItems(combined);
    assert.deepEqual(items.map((i) => i.title), ["Real item"]);
  });
});

describe("rewriteH4ToH2", () => {
  it("rewrites leading #### to ##", () => {
    const body = "#### Refactor auth\n\n- Value: high\n";
    const out = rewriteH4ToH2(body);
    assert.ok(out.startsWith("## Refactor auth"));
    assert.ok(!out.includes("####"));
  });
});

// ---------------------------------------------------------------------------
// buildPhaseDPayloads tests
// ---------------------------------------------------------------------------

describe("buildPhaseDPayloads", () => {
  it("blocks when dedup marker missing", () => {
    const combined = "## Technical\n#### Item\n";
    assert.throws(
      () => buildPhaseDPayloads({ combinedMarkdown: combined }),
      /not finalised by step-5b/
    );
  });

  it("writes payload + manifest with the slim structure", () => {
    const combined = buildCombined(`\
## Technical

### Architecture · group
<!-- aspect-id: architecture -->

#### Refactor auth module

- Value: high
- Need: foo
`);
    const { payloads, manifest } = buildPhaseDPayloads({ combinedMarkdown: combined });

    assert.equal(manifest.schema_version, 1);
    assert.equal(manifest.items.length, 1);
    assert.equal(manifest.items[0].item_slug, "refactor-auth-module");
    assert.equal(manifest.items[0].track, "technical");
    assert.equal(manifest.items[0].payload_path, "item-01-refactor-auth-module.json");
    assert.equal(manifest.items[0].output_path, "item-01-refactor-auth-module.md");
    assert.equal(manifest.combined_md_sha256.length, 64);

    assert.equal(payloads.length, 1);
    const p = payloads[0];
    assert.equal(p.filename, "item-01-refactor-auth-module.json");
    assert.equal(p.json.schema_version, 1);
    assert.ok(p.json.item_markdown.startsWith("## Refactor auth module"));
    // The slimmed payload carries ONLY the proposal item — nothing else.
    assert.deepEqual(Object.keys(p.json), ["schema_version", "item_markdown"]);
  });

  it("zero items emits empty manifest", () => {
    const combined = buildCombined("## Technical\n\nNo items here.\n");
    const { payloads, manifest } = buildPhaseDPayloads({ combinedMarkdown: combined });
    assert.deepEqual(manifest.items, []);
    assert.equal(payloads.length, 0);
  });

  it("single-track business-only run", () => {
    const combined = buildCombined(`\
## Business

### UX-gaps · group
<!-- aspect-id: ux-gaps -->

#### Improve signup
- Value: high
`);
    const { payloads, manifest } = buildPhaseDPayloads({ combinedMarkdown: combined });
    assert.equal(manifest.items.length, 1);
    assert.equal(manifest.items[0].track, "business");
    assert.equal(payloads[0].json.item_markdown.startsWith("## Improve signup"), true);
  });

  it("dual-track run produces items from both tracks in doc order", () => {
    const combined = buildCombined(`\
## Technical

### Architecture · group
<!-- aspect-id: architecture -->

#### Tech item

## Business

### UX · group
<!-- aspect-id: ux -->

#### Business item
`);
    const { payloads, manifest } = buildPhaseDPayloads({ combinedMarkdown: combined });
    assert.equal(payloads.length, 2);
    assert.equal(manifest.items[0].track, "technical");
    assert.equal(manifest.items[1].track, "business");
    assert.equal(manifest.items[0].item_index, 1);
    assert.equal(manifest.items[1].item_index, 2);
  });

  it("manifest sha256 matches computeSha256 of combinedMarkdown", () => {
    const combined = buildCombined("## Technical\n\nNothing here.\n");
    const { manifest } = buildPhaseDPayloads({ combinedMarkdown: combined });
    assert.equal(manifest.combined_md_sha256, computeSha256(combined));
  });

  it("manifest key order is stable", () => {
    const combined = buildCombined("## Technical\n\n");
    const { manifest } = buildPhaseDPayloads({ combinedMarkdown: combined });
    assert.deepEqual(Object.keys(manifest), [
      "schema_version",
      "combined_md_sha256",
      "items",
    ]);
  });
});
