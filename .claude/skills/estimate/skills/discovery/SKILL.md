---
name: discovery
description: "Activate when user asks for pre-estimation discovery, spec analysis, Q&A generation, client questionnaire, or says 'discovery', 'pre-estimate', 'spec review Q&A', 'analyze spec'. Parses spec documents, generates client-facing Q&A (MD+Excel) and internal analysis report, auto-generates estimate-config.yaml."
argument-hint: <input-dir-path> [--lang en|vi|ja]
user-invocable: true
license: MIT
compatibility: Requires Python 3.10+. Works with Claude Code and Cursor.
metadata:
  author: lamngockhuong
  version: "1.0.0"
---

# Discovery Sub-Skill

Analyze specification documents and produce structured discovery outputs before estimation.

## Scope

**This skill handles:**
- Parsing specification documents (reuses agentic-estimate parsers)
- Extracting features, screens, and modules from parsed content
- Generating client-facing Q&A documents (Markdown + Excel)
- Producing internal analysis report (quality, risks, recommendations)
- Auto-generating `estimate-config.yaml` from analysis

**This skill does NOT handle:**
- Effort estimation or story point calculation (use `/agentic-estimate`)
- Task breakdown (use `/agentic-estimate:task-breakdown`)
- Code generation or implementation

## Security

- Do NOT include proprietary client data beyond what's needed for Q&A generation
- Sanitize file paths in output — no absolute paths exposing system structure
- Parser scripts execute locally; no data sent to external services

## Task

Read project specification documents, extract features, identify information gaps, and generate structured Q&A artifacts for client review plus an internal analysis report.

## Instructions

### 1. Input Validation

Detect input types in the provided directory:

```bash
ls <input-dir>/ | head -20
```

- Supported: PDF, Excel, Markdown, DOCX, PPTX, images, URLs
- Require at least one parseable document
- If directory missing or empty → error with usage hint

### 2. Document Parsing

Reuse agentic-estimate parser for each document in the input directory.

- **Check cache first**: `[ -f "<file>.parsed.md" ] && [ "<file>.parsed.md" -nt "<file>" ] && echo "CACHED" || echo "STALE"`
- If CACHED → Read `<file>.parsed.md` directly
- If STALE/missing → `python3 .claude/skills/estimate/scripts/parse-document.py <file> --cache`
- Use `~/.claude/skills/.venv/bin/python3` (system python3 may be < 3.10)
- **Sparse content detection**: Same rules as agentic-estimate Step 2 (OCR fallback, multimodal)
- **Images/screenshots**: Use Read tool (multimodal) to view prototype screenshots or wireframe images. These provide UI context for feature extraction but don't go through parse-document.py.
- **Multi-document**: Parse each file, merge content for analysis

### 3. Feature Extraction

From parsed content, identify:
- **Features/modules** with screen counts (explicit or inferred)
- **User roles/actors** mentioned
- **Integrations** (third-party services, APIs)
- **Non-functional requirements** (performance, i18n, security)

Map features to knowledge base categories using [.claude/skills/estimate/references/knowledge-base.md].

### 4. Gap Analysis

Cross-reference extracted features with KB to find missing information:
- Compare feature detail level against KB expected inputs per task type
- Flag features with insufficient detail for estimation
- Identify common missing items: tech stack, platforms, auth method, data volumes
- Assign gap severity: Critical (blocks architecture), High (affects effort), Medium (improves accuracy)

### 5. Q&A Generation

Generate questions using templates from [references/qa-templates.md]:

- Group questions by feature/screen (not by category)
- Tag each question: `[Functional]`, `[Technical]`, or `[Scope]`
- Assign priority: Critical, High, Medium (see template rules)
- Include context explaining why each question matters
- Add options where applicable (multiple-choice reduces client effort)
- Leave answer field blank for client input

**Output format** — structured JSON:

```json
{
  "project_name": "...",
  "generated_date": "YYYY-MM-DD",
  "source_files": ["spec.pdf", "wireframes.xlsx"],
  "language": "en",
  "questions": [
    {
      "id": "Q1",
      "feature": "General",
      "category": "scope",
      "question": "Target platforms?",
      "context": "Spec mentions 'web app' but no mobile mention.",
      "options": ["Web only", "Web + iOS", "Web + iOS + Android"],
      "answer": "",
      "priority": "critical",
      "priority_reason": "affects all effort calculations"
    }
  ]
}
```

### 6. Internal Analysis

Generate analysis report using templates from [references/analysis-templates.md]:

- **Document Quality**: completeness %, clarity, detail tier (discovery/quick/bidding)
- **Feature Inventory**: table of features with complexity, confidence, gap level
- **Integrations**: identified third-party services and APIs
- **Risk Flags**: assumptions, unclear scope, missing info
- **Recommended Configuration**: roles, template tier, complexity class
- **Q&A Coverage Summary**: total questions by priority and feature

Save as: `<input-dir>/discovery/internal-analysis.md`

### 7. Config Generation

Auto-generate `estimate-config.yaml` from analysis:

- Determine active roles based on feature types (e.g., file uploads → infra)
- Set role flags (true/false) based on recommendations
- Include team size suggestions if inferable

Save as: `<input-dir>/estimate-config.yaml`

### 8. Output Rendering

Write Q&A JSON, then render to client-facing formats:

1. Save Q&A JSON to temporary file
2. Render MD + Excel:
   ```bash
   python3 .claude/skills/estimate/scripts/render-qa.py discovery-qa.json -o <input-dir>/discovery/<lang>/ -f md,xlsx --lang <lang>
   ```
   - `--lang` translates headers/labels only — question content stays in the source JSON language
   - **Multi-language**: If user requests multiple languages (e.g., en+vi), create a separate translated JSON per language, then render each to its own subdirectory:
     ```
     discovery-qa.json      → discovery/en/client-qa.{md,xlsx}
     discovery-qa-vi.json   → discovery/vi/client-qa.{md,xlsx}
     ```
   - render-qa.py **overwrites** output files — never render multiple languages to the same directory
3. Report output summary to user:
   - Number of questions by priority
   - Features covered
   - Path to outputs

**Final output structure (single language):**
```
<input-dir>/
  ├── discovery/
  │   ├── discovery-qa.json    # Source Q&A data
  │   ├── client-qa.md         # Client-facing Q&A
  │   ├── client-qa.xlsx       # Excel Q&A (editable Answer column)
  │   └── internal-analysis.md # Internal gaps/risks/recommendations
  └── estimate-config.yaml     # Auto-generated role config
```

**Final output structure (multi-language, e.g., en+vi):**
```
<input-dir>/
  ├── discovery/
  │   ├── discovery-qa.json      # Source JSON (primary language)
  │   ├── discovery-qa-vi.json   # Translated JSON (secondary)
  │   ├── en/
  │   │   ├── client-qa.md
  │   │   └── client-qa.xlsx
  │   ├── vi/
  │   │   ├── client-qa.md
  │   │   └── client-qa.xlsx
  │   └── internal-analysis.md
  └── estimate-config.yaml
```

## Rules

- Questions must be grouped by feature, not by category
- Every question needs a context line explaining why it matters
- Critical questions = blocks architecture decisions
- Never generate more than ~30 questions (focus on gaps, not exhaustive checklists)
- `--lang` flag in render-qa.py controls output headers/labels only (e.g., "Question" → "Câu hỏi")
- AI generates question **content** in the language requested by the user
- For multi-language output: create separate source JSON files with translated content, then render each
- Discovery outputs are INPUT for estimation, not deliverables themselves

## Validation

Before finalizing:
1. Q&A JSON has all required fields: id, feature, category, question, context, options, answer, priority, priority_reason
2. Every feature from extraction has at least one question
3. At least one Critical priority question exists (if spec has gaps)
4. Internal analysis includes all required sections
5. estimate-config.yaml has valid role flags

## Additional Resources

Load on demand:
- [references/qa-templates.md](references/qa-templates.md) — Question templates per feature type
- [references/analysis-templates.md](references/analysis-templates.md) — Internal analysis report structure
- Shared: [.claude/skills/estimate/references/knowledge-base.md] — KB for gap analysis
- Shared: [.claude/skills/estimate/references/rfp-analysis-templates.md] — Business flow templates
