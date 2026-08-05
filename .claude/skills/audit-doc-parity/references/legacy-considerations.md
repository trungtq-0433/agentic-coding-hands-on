# Legacy-Project Considerations — `audit-doc-parity`

**Governing rule (above all four groups):**

> **Ambiguous legacy signal → UNVERIFIABLE. NEVER assert a false DRIFT or MISSING.**
> A parity tool dies on its first wrong finding. When in doubt, degrade — do not accuse.

Real codebases — especially long-lived Sun* repos — break the clean assumptions of "doc cites code,
code says X". Four hazard groups, each with its safe degradation. The Python plumbing
(`scope_doc_units.py`, `_citation_lib.py`) enforces A and C mechanically; the LLM stages
(blind-regen, diff, adjudication) enforce B and D by instruction.

## A. Exclusion (BOTH directions)

Generated, vendored, minified, binary, and lock artifacts are **never regenerated** (doc→code side)
and **never flagged MISSING** (code→doc side). A drift between a doc and a `node_modules` file is not
a finding; an undocumented behavior in a minified bundle is not a coverage gap.

- **DRY — reuse rebuild-spec's exclusion convention.** The de-facto skip set across rebuild-spec
  extractors (`_credential_scrub_lib.py`, `extract_data_flow.py`, `_extractor_lib.py`) is:
  `.git`, `node_modules`, `vendor`, `dist`, `build`, `target`, `__pycache__`, `.venv`.
  `scope_doc_units.py` mirrors this set + minified (`*.min.js`, `*.min.css`), lock files
  (`*.lock`, `package-lock.json`, `yarn.lock`, `composer.lock`, `Gemfile.lock`), and binaries.
- **Behavior-logic exclusion table** (`rebuild-spec/templates/behavior-logic-template.md` §
  Inclusion/Exclusion Matrix): test files (`*Test.php`, `*Spec.rb`, `test_*.py`, `*.test.ts`),
  files < 10 LOC (scaffolding/stubs), abstract base classes / traits / interfaces. These are excluded
  from the MISSING side — an undocumented abstract base is not a coverage gap.
- **File-size cap (god-class guard).** Enclosing-block extraction has a size cap; a block over the cap
  falls back to the cited span + a **logged truncation** (no silent cap — the unit records
  `truncated: true`). An oversized god-class never silently swallows the regen budget.

## B. Non-conventional behavior sources

Citations legitimately point beyond mainstream source files. These are **documentation-worthy and
must be regen-readable**:

- SQL / stored procedures / triggers (`.sql`)
- Crontab / scheduler config
- Shell scripts (`.sh`)
- Config-as-code: Spring XML, `.htaccess`, `web.config`, route/DI definition files
- Logic-bearing templates: PHP, ERB, JSP (behavior embedded in markup)

`_citation_lib.py` accepts these extensions; the blind-regen agent reads and re-describes them like any
source. **Binaries, compiled artifacts, opaque macros → UNVERIFIABLE** (cannot be read as behavior).

## C. Citation reliability

The citation may resolve to a real file but the bytes/lines may not be trustworthy:

- **Encoding.** Sun* JP repos commonly use Shift-JIS / Latin-1 / BOM / CRLF, not UTF-8. `_citation_lib.py`
  reads **encoding-safe** (detect-and-decode, never UTF-8-only). An undecodable file → UNVERIFIABLE.
- **Stale line numbers.** A doc written at commit X cites `foo.py:88-95`, but the code moved since.
  Before trusting the span, a **plausibility check**: does the cited span still look like the symbol the
  claim is about? If not → optionally symbol re-anchor, else **degrade to UNVERIFIABLE**. A drifted line
  number must **never** become a false DRIFT.
- **File-size cap** with logged truncation (shared with group A).

## D. Live vs dead code

Not all code that exists runs:

- Feature-flag-gated branches, dead branches, commented-out paths, v1/v2 duplicate implementations.
- The blind-regen agent **notes reachability uncertainty** — behavior it cannot confirm is live is
  marked low confidence.
- **Dead-code-only divergence → low confidence → UNVERIFIABLE, not DRIFT.** If the only thing that
  makes the doc "wrong" is a dead branch, the doc is not lying about live behavior — do not accuse it.

## How each group degrades

| Group | Mechanism | Degradation |
|-------|-----------|-------------|
| A | `scope_doc_units.py` skip-list (both directions) | excluded entirely (not a finding either way) |
| B | `_citation_lib.py` accepts non-source ext; regen reads it | binary/opaque → UNVERIFIABLE |
| C | encoding-safe read + stale-anchor plausibility check | undecodable / stale → UNVERIFIABLE |
| D | blind-regen reachability note + confidence floor | dead-code-only divergence → UNVERIFIABLE |
