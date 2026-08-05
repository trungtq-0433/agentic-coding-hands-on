<!-- layout-exempt: rebuild-spec reference doc — all docs/generated paths here are this skill's own input/output targets -->
# API Doc Pass (`--api-doc`) — Client-Facing API Design Workbook (Sun* BM-2-901-52)

Standalone `--api-doc` pass of `/tkm:rebuild-spec` (dispatched from SKILL.md when the flag is set). It builds a
**client-facing API Design `.xlsx`** in the Sun* standard form `BM-2-901-52`, by **cloning a
bundled template and writing only cell values** — so the output is **format-identical** to the
Sun* sample (font, size, fills, merges, dropdowns, logo). One detail sheet per API operation,
sourced from the project's OpenAPI `swagger.yaml` **or — when none exists — synthesized from
rebuild-spec artifacts** (`route-list.md` + optional api-map/api-contracts), so the pass runs on any
project/stack, not just rswag ones.

**NOT the same as the built-in `--api-contracts`** (a core-tier pass that synthesises
REST/GraphQL/gRPC contracts as *Markdown* under `docs/`). `--api-doc` produces a single styled
*Excel* deliverable for stakeholders. They are independent and may both be run.

## Invocation

```
/tkm:rebuild-spec --api-doc                      # build + deterministic lint + LLM semantic review
/tkm:rebuild-spec --api-doc --no-semantic-review # skip the B2 LLM review stage (build + lint only)
```

The driver always runs the deterministic semantic lint (B1, `verify_semantics.py`) as a hard gate.
The LLM semantic review (B2) runs by default AFTER the driver SEALs, and is skippable with
`--no-semantic-review` (token cost). Default-on because the audience includes a client deliverable.

## Preflight (ABORT if unmet)

- An **API source** must be resolvable — swagger is NOT required. The driver resolves it in order:
  1. `--swagger PATH` (explicit), or an auto-detected `**/swagger*.y*ml` / `**/openapi*.{yaml,yml,json}`
     (excluding `node_modules`) — highest fidelity.
  2. else **derive from rebuild-spec artifacts** (`docs/generated/route-list.md` required; api-map /
     api-contracts enrich) — works on ANY stack, no swagger needed. Forced with `--from-artifacts`.
  ABORT only if neither a swagger nor `docs/generated/route-list.md` exists:
  `"ERROR: route-list.md required ... Run /tkm:rebuild-spec (core pass) first; optionally --api-contracts."`
- Python with **openpyxl + PyYAML** — use the kit venv `.claude/skills/.venv/bin/python3`
  (ships both). On a non-kit project, install: `pip install openpyxl pyyaml`.
- **Optional enrichment (used if present):** `docs/generated/api-map.md` (curated category names
  per endpoint; both the swagger and derived paths consume it), and on the derived path
  `docs/generated/api-contracts.md` (request/response bodies + status codes). Absent → categories
  fall back to tags/headings and params/responses stay minimal. The pass degrades gracefully.

## How it works (fidelity by construction)

The pass NEVER recreates styles. It loads the bundled `api-design-template.xlsx` (the Sun* form,
keeping every style), clones its `API_Detail_Template` sheet per API, and writes **only** `.value`.
Because `copy_worksheet` drops **data validations** and **images**, the builder re-applies the two
dropdowns (Param Type, Data Type) and the Sun* logo on every sheet. A style-fingerprint verifier
diffs the output against the template and asserts **zero style drift**.

## Steps (run via the bundled driver — single command)

```
.claude/skills/.venv/bin/python3 \
  .claude/skills/rebuild-spec/extensions/api/build_api_doc.py \
  --project-root . \
  --system-name "<System Name>" --creator "Sun Asterisk Vietnam" --date "<YYYY-MM-DD>"
  # optional: --swagger PATH  --api-map PATH  --out-dir DIR  --out FILE.xlsx
  #           --from-artifacts   (force the derived path even when a swagger exists, e.g. it is stale)
  #           --template T.xlsx  --logo L.png   (override the bundled Sun* template/logo)
```

**Multi-project flow (no swagger):** `/tkm:rebuild-spec` (core) → optional `--api-contracts` (richer
bodies/responses) → `--api-doc`. Core works on any stack, so `--api-doc` does too.

The driver runs these stages and **aborts on any non-zero exit**:
1. **Golden** — `verify_format.py --make-golden <template> .golden.json` (style baseline).
1b. **Resolve source** — swagger (explicit/auto) → use it; else `artifacts2openapi.py` synthesizes a
   minimal OpenAPI 3.0 (`openapi.yaml` in the out-dir) from `route-list.md` (+ api-map / api-contracts).
   `:param`→`{param}` + path params; combined `PATCH/PUT`→first verb; infra/non-API routes (health,
   sidekiq, api-docs, mounted engines) are **excluded and reported**. Deterministic: 1 op per API row.
   From api-contracts the `**Request — Body:**` and `**Request — Path/Query:**` tables are split:
   body fields → requestBody (non-GET only), query fields → `in:query` params (GET never gets a body).
   Responses = documented codes ∪ inferred `401`/`403` for authenticated (`Bearer`) routes, labelled
   `(inferred — not in source contract)`; `none`-auth rows (e.g. iOS `body_statuses`) get no forced 401
   and instead carry the auth-divergence security note in the op `description`. Own derived
   `openapi.yaml` in the out-dir is excluded from swagger auto-detect so re-runs always re-derive.
2. **Extract** — `extract_api_content.py` parses the resolved OpenAPI (resolves `$ref`), maps Param Type
   (`path/query/form/body` → template dropdown values) and Data Type (`schema.type`), attaches a
   Category (api-map.md or tags), and writes `api-content.json` / `api-list.json` /
   `status-codes.json` to the out-dir. Path/query/body params only — universal auth headers excluded.
2b. **Semantic lint (B1)** — `verify_semantics.py <openapi> <api-content.json> --route-list <rl>` — a
   pure-Python **hard gate** (driver aborts on non-zero) run BEFORE build. 7 deterministic checks
   guarding the Phase-A fix classes: L1 no-backtick-key · L2 no-header-field · L3 GET-no-body ·
   L4 authed-endpoint-has-4xx (NONE-auth exempt) · L5 query-classified · L6 coverage-no-drops
   (vs route-list) · L7 category-not-file. Turns silent corruption into a loud, named failure.
3. **Build** — `build_api_design.py` clones the template per op (one sheet each), fills meta +
   Request Params + Responses, re-applies dropdowns + logo, populates API List (grouped by
   category) + History (Ver 0.1) + Status code (actual codes seen in the resolved source). Trailing
   template sample rows are normalized to the pattern, so a source with few status codes still seals.
4. **Verify** — `verify_format.py .golden.json <out>` — the **hard gate**: 0 style drift +
   **0 dangling sheet-reference** (guarantees Excel opens) + **every sheet has the logo** +
   **0 content truncation** (reads `api-content.json`; fails if any op has >10 params or >7
   responses — i.e. data the builder dropped) + **full coverage** (every extracted operation maps to
   exactly one detail sheet: `n_ops == n_detail`). "SEALED" = format-perfect AND content-complete AND
   complete coverage. Exit 0 = SEALED.
5. **Health** — `xlsx_health.py <out>` — independent OOXML CONTAINER check (separate from style):
   zip CRC integrity + every XML part well-formed & strict UTF-8 + **every relationship target
   resolves** (the classic "needs repair" cause) + no external links + images present + openpyxl
   reopen (normal & read_only) + data-validation sheet refs + a non-ASCII (e.g. Japanese) encoding
   round-trip. Exit 0 = opens without errors/repair. This is the strongest openability proof when
   no LibreOffice/Excel is available to render.

## Semantic review (B2 — LLM gate, default on; `--no-semantic-review` to skip)

The driver proves the workbook is STYLE-perfect (verify_format) and STRUCTURALLY faithful
(verify_semantics / B1). Neither can reason about whether the *content* matches the actual source —
that is B2. It is an **orchestration stage, not a driver stage** (the driver is pure-Python, no LLM):
after the driver SEALs, the orchestrating skill dispatches a `reviewer` agent. Mirrors rebuild-spec
Wave AC.3.

**Reviewer dispatch contract:**
- **Agent:** `reviewer` (via the Agent/Task tool).
- **Inputs (explicit):** `docs/api/api-content.json`, `docs/api/openapi.yaml`,
  `docs/generated/api-contracts.md`, `docs/generated/route-list.md`. Plus: read the source files
  cited in api-contracts `**Source:**` lines for spot-checks (Grep/Read).
- **Checks (SR-1..SR-5):**
  - SR-1 — no fabricated request/response fields (every doc field traces to a source DTO or contract row).
  - SR-2 — endpoint set == route-list set (minus reported infra); no fabricated/dropped endpoints.
  - SR-3 — field types match source (e.g. `records` = Array not scalar; iOS/Android type divergence noted, not flattened).
  - SR-4 — auth accuracy: `body_statuses` iOS=NONE / Android=Bearer divergence present; inferred `401`s
    that are LABELLED `(inferred …)` are **acceptable — do NOT flag them as fabricated**. Only unlabelled
    unsourced content is a defect.
  - SR-5 — categories are real domains, no `File:`/file-path garbage (semantic cross-check of A5/L7).
- **Output:** `docs/api/api-doc-semantic-review-report.md` — rebuild-spec review-report template:
  frontmatter `passed: N` / `failed: N` / `warnings: N`; `## Passed Checks` one-line `✓ SR-x`;
  `## Issues` per finding with file:line evidence.
- **Gate:** orchestrator reads frontmatter. `failed > 0` → print findings + amend the handoff to
  "REVIEW FOUND ISSUES" (findings are pipeline-code/Phase-A class → fix + re-run; B2 does NOT auto-fix
  and does NOT un-seal the already-built workbook). `failed == 0` → handoff notes "semantic review: PASS".
- **Missing source:** files cited in api-contracts but absent from the repo → `warning` (unverifiable),
  not `fail` (matches the EXTRACTED/INFERRED confidence legend).

## Outputs (default `docs/api/`)
- `<System Name> - API Design.xlsx` — the deliverable (one sheet per API + API List / History /
  Status code / Common Conventions / Appendix).
- `.golden.json` + `api-content.json` / `api-list.json` / `status-codes.json` — intermediates
  (regenerated each run; safe to delete).

## Limits & edge cases
- Template area holds ≤10 params and ≤7 responses per op. An op exceeding either is **dropped to
  fit by the builder and then FAILS verification** (`=== CONTENT TRUNCATED ===`, exit 2) — the
  pass refuses to seal an incomplete deliverable. Both are rare (the template allows ≤10 params and
  ≤7 responses — its static response band is 3 rows, which the builder expands to 7). On a fail:
  split the op, trim params to the template area, or extend the template's response band — then re-run.
- Sheet names are `NN.MET hint` (≤31-char Excel limit); full URL is in the **API List** sheet.
- `--template`/`--logo` override the bundled Sun* assets for non-Sun* forms (the template must keep
  the sheet names `API_Detail_Template`, `API List`, `History of changes`, `Status code`, `Appendix`).
- Visual render is not performed (no LibreOffice dependency); fidelity is proven by fingerprint.
  Open the `.xlsx` to eyeball once.

## Idempotency
Re-running regenerates the workbook + intermediates from the current swagger. Writes only inside the
out-dir; never touches the core/feature/flow/glossary artifacts.

## Completion handoff
```
─── api-doc pass complete ───
Built: docs/api/<System Name> - API Design.xlsx  (verify: SEALED — 0 drift / 0 dangling-ref / logo on every sheet / 0 truncation)
Semantic lint (B1): 7/7 checks passed.
Semantic review (B2): PASS — 0 fabricated fields   |OR|   REVIEW FOUND <N> ISSUES → see docs/api/api-doc-semantic-review-report.md (fix in pipeline, re-run)
Open the .xlsx to confirm visually. Re-run: /tkm:rebuild-spec --api-doc
```
