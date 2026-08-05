---
name: tkm:estimate
description: >
  ALWAYS activate when user asks to estimate project effort, story points, man-days, WBS,
  'how long will this take', dự toán, 見積もり from spec documents (PDF, Excel, Markdown,
  images, URLs). Also activate for 'import historical', 'import estimate', 'calibrate',
  'calibration', 'tune knowledge base', 'task-breakdown'. Also for generating
  Sun* project artifacts (user-story, screen-flow, function-list) from Clio KG data.
  SKIP: cost/pricing/budget estimates, hosting costs, sprint planning, code implementation.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - WebFetch
argument-hint: "[mode] [--project-id ID | <document-path> | <dir-path>]"
metadata:
  author: takumi-agent-kit
  version: "2.0.0"
module: takumi-specific
triggers: ["estimate", "man-days", "WBS", "effort estimate", "function count", "dự toán", "見積もり", "spec document", "bidding"]
---

# Estimate — Unified Project Estimation

Analyze spec documents or Clio KG data and generate comprehensive effort estimates for Sun* projects.

**Requires Python 3.10+.** Install deps: `bash claude/skills/estimate/install-deps.sh`

## Setup

### Spec Mode (document-based bidding)

No extra config. Deps installed once via `install-deps.sh`.

### Clio Mode (Sun* internal projects)

Add to `.mcp.json` or `~/.claude/settings.json`:

```json
{ "mcpServers": { "clio": { "type": "http", "url": "https://clio.sun-asterisk.vn/mcp", "headers": { "x-api-key": "${CLIO_API_KEY}" } } } }
```

Set `CLIO_API_KEY` in `~/.claude/.env`. Create `.estimate.yml` in project root:

```yaml
project_id: your-project-id
```

---

## Mode Detection

Detect mode from args and environment **before proceeding**:

| Trigger | Mode | Action |
|---------|------|--------|
| `import <file>`, `import historical`, `import estimate`, `add to historical` | **Import** | Load [references/import-mode.md](references/import-mode.md) |
| `calibrate`, `calibration`, `tune`, `analyze historical` | **Calibrate** | Load [references/calibrate-mode.md](references/calibrate-mode.md) |
| `discovery <dir>`, `pre-estimate`, `spec analysis Q&A` | **Discovery** | Invoke [skills/discovery/SKILL.md] |
| `.estimate.yml` exists + `clio_query` MCP available | **Clio Mode** | Load [references/clio-mode.md](references/clio-mode.md) |
| Document path / spec file provided | **Spec Mode** | Steps 1–8 below |
| No args, no `.estimate.yml` | **Ask user** | Present mode options |

**Clio Mode check:**
1. Look for `.estimate.yml` → read `project_id`
2. Verify `clio_query` MCP tool is available
3. If both → Clio Mode. If `.estimate.yml` exists but no MCP → warn, offer Spec Mode fallback
4. If `.estimate.yml` exists AND a document is provided → ask user: "Clio Mode or Spec Mode?"

---

## Clio Mode

For Sun* internal projects with data in Clio Knowledge Graph.

Load and follow: [references/clio-mode.md](references/clio-mode.md)

**Pipeline:** project-profile → user-story → screen-flow → function-list → estimate

All steps use KB formulas (role-based, Fibonacci SP) — not hours-based.

---

## Spec Mode — Instructions

### 1. Intelligent Input Validation
- Detect input types (PDF, Excel, Markdown, DOCX, PPTX, images, URLs)
- Assess document quality; suggest additional inputs if incomplete
- If input is an existing estimate (WBS, man-days, SPs): ask first — review/validate OR create independent?

### 1.5. Discovery Auto-Detection
```bash
[ -d "<input-dir>/discovery" ] && echo "DISCOVERY_FOUND" || echo "NO_DISCOVERY"
```
If DISCOVERY_FOUND: read `client-qa.md`, `internal-analysis.md`, `estimate-config.yaml`.
Pre-populate: feature list (Step 3), answered questions (Step 4), risk flags (Step 6).

### 2. Document Parsing

**Check cache first** — if `<file>.parsed.md` exists and is newer than source, use Read tool directly (skip parser).

```bash
# Standard parse (caches result):
python3 scripts/parse-document.py <file> --cache

# PDF with sparse text (< 50 words/page):
python3 scripts/parse-document.py <file> --cache --pdf-ocr --ocr-lang jpn

# GitHub URLs (issues, PRs, discussions):
python3 scripts/parse-document.py github.com/owner/repo/issues/123

# Excel with specific sheets:
python3 scripts/parse-document.py <file> --cache --sheets "Sheet1" "Sheet2"
```

**Use `~/.claude/skills/.venv/bin/python3` (not system python3).** System python3 may be < 3.10.

Multimodal fallback for sparse PDFs (diagrams, PowerPoint exports): use Read tool to visually read pages, then save combined content to `<file>.parsed.md`.

### 3. Requirement Extraction
- Identify features, user stories, constraints
- Flag ambiguous requirements with specific questions

### 4. Clarification
- If document has distinct sub-projects → ask: one combined or separate estimates?
- Ask output preferences: language(s), format(s), cost rate (default ¥40,000/MD)
- Check for `estimate-config.yaml` in input dir → confirm roles; else ask which roles to include
  - Defaults: FE, BE, QA (Manual)
  - Available: QA Auto, Design, PM, BrSE, Infra

### 5. Estimation Calculation
Load [references/knowledge-base.md](references/knowledge-base.md) for YAML config values.
Load [references/historical-summary.md](references/historical-summary.md) if data exists (inform, don't override).

Formula: `md = base × complexity × tech × experience × (1 + buffer_pct/100)`
SP: Fibonacci scale 1,2,3,5,8,13,21 — 1 SP ≈ 0.5 MD. See [references/estimation-formulas.md](references/estimation-formulas.md).

**Per-role effort:** For each task, distribute MD across active roles using role-split heuristics.
Each role: `md = round(base × complexity × experience × (1 + buffer_pct/100))`
`total_md` = sum of all role `md` values.

### 6. Risk Assessment
Load [references/risk-validation.md](references/risk-validation.md).
Identify risks, score by probability × impact, suggest mitigations.

### 7. Output Generation (JSON → MD + Excel + HTML)

**Write JSON** following [references/estimate-json-schema.md](references/estimate-json-schema.md):

```
output/<project-slug>/<name-slug>-estimate-<YYMMDD-HHMM>.json
```

Template tiers: `discovery` (business consultation) | `quick` (brief spec) | `bidding` (≥3 of: user stories, screen list, tech stack, NFR, actor list in source doc).

Each task `effort` keyed by role slug:
```json
"effort": { "fe": {"base":3.0,"complexity":1.2,"experience":1.0,"buffer_pct":15,"md":4} }
```

**Render from JSON:**
```bash
python3 scripts/render-estimate.py output/<slug>/<name>-estimate-<ts>.json -o output/<slug> -f md,xlsx,html
```

HTML check: `node -e "const fs=require('fs'),h=fs.readFileSync('<html>','utf8'),m=h.match(/const DATA = (.+?);\n/s);try{JSON.parse(m[1]);console.log('HTML OK')}catch(e){console.error(e.message);process.exit(1)}"`

Validate JSON: `python3 scripts/validate-estimate.py output/<slug>/<name>-estimate-<ts>.json`

**Manifest:** `python3 scripts/init-manifest.py output/<slug>/` — tracks all generated files.

#### 7.5. Infra Deliverables (if infra role active)
Load [references/infra-deliverables.md](references/infra-deliverables.md).

### 8. Task Breakdown (Optional)
After rendering, ask: "Would you like a detailed task breakdown per team?"
If yes: invoke `/task-breakdown <estimate-json-path> --level 3`

---

## Rules

- Always ask clarifying questions before finalizing
- Document all assumptions explicitly
- Minimum buffer: 10%
- Never estimate tasks > 13 SP (split if larger; PM/BrSE overhead tasks may be 0 SP)
- Each task must have at least one role in `effort`
- `total_md` must equal sum of role `md` values
- Only assign roles from `parameters.active_roles`
- **Clio Mode only:** All Clio queries run sequentially; no fabrication; `project_id` required

---

## Validation (before final report)

1. All requirements have estimates
2. Total SP < 500
3. No task > 13 SP (split if violated)
4. Buffer ≥ 10%
5. `python3 scripts/validate-estimate.py <json-path>` exits 0
6. HTML JS check passes (Step 7)

---

## Additional Resources

Load ON DEMAND (not upfront):

| Reference | Load when |
|-----------|-----------|
| [references/clio-mode.md](references/clio-mode.md) | Clio Mode triggered |
| [references/knowledge-base.md](references/knowledge-base.md) | Calculating estimates |
| [references/estimation-formulas.md](references/estimation-formulas.md) | Complex calculations |
| [references/estimate-json-schema.md](references/estimate-json-schema.md) | Writing JSON output |
| [references/risk-validation.md](references/risk-validation.md) | Risk assessment |
| [references/output-templates.md](references/output-templates.md) | Selecting template tier |
| [references/output-template-discovery.md](references/output-template-discovery.md) | Discovery tier |
| [references/output-template-quick.md](references/output-template-quick.md) | Quick tier |
| [references/output-template-bidding.md](references/output-template-bidding.md) | Bidding tier |
| [references/import-mode.md](references/import-mode.md) | Import triggered |
| [references/calibrate-mode.md](references/calibrate-mode.md) | Calibrate triggered |
| [references/infra-deliverables.md](references/infra-deliverables.md) | Infra role active |
| [references/gotchas.md](references/gotchas.md) | Parser edge cases |
| [references/historical-summary.md](references/historical-summary.md) | Historical context during estimation |
| [references/rfp-analysis-templates.md](references/rfp-analysis-templates.md) | RFP analysis diagrams |
| [references/estimate-config-sample.yaml](references/estimate-config-sample.yaml) | Role config template |
| [skills/discovery/SKILL.md] | Discovery mode |
| [skills/task-breakdown/SKILL.md] | Task breakdown |
