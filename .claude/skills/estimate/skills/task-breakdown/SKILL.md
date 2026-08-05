---
name: task-breakdown
description: "Activate when user asks to break down tasks per team, generate per-role task lists, decompose features into subtasks, or says 'task breakdown', 'break task', 'phân rã task'. Works standalone (from spec docs) or post-estimate (from estimate JSON)."
argument-hint: <document-or-json-path> [--level 1|2|3] [--lang en|vi|ja]
user-invocable: true
license: MIT
compatibility: Requires Python 3.10+. Works with Claude Code and Cursor.
metadata:
  author: lamngockhuong
  version: "1.0.0"
---

# Task Breakdown Skill

Decompose project specs or estimate JSON into per-team task lists at 3 granularity levels.

## Scope

**This skill handles:**
- Breaking down requirements into Epic -> Story -> Task hierarchy
- Generating per-team task files (fe-tasks.md, be-tasks.md, etc.)
- Pre-estimate mode: scope decomposition from raw documents (no MD numbers)
- Post-estimate mode: expand estimate JSON into actionable tasks with MD numbers

**This skill does NOT handle:**
- Effort estimation or story point calculation (use `/agentic-estimate`)
- Code generation or implementation
- Sprint planning or project management

## Security

- Do NOT include proprietary client data beyond what's needed for decomposition
- Sanitize file paths in output — no absolute paths exposing system structure
- Parser scripts execute locally; no data sent to external services

## Task

Read project specifications or estimate JSON, decompose requirements into Epic -> Story -> Task hierarchy, and generate per-team breakdown files.

## Instructions

### 1. Detect Input Type

Determine input type from the argument:

- **No file path** (text description like "Website bán hàng B2C") → **TEXT_INPUT** (pre-estimate mode, skip Step 2)
- **File path provided** → run detection script:

```bash
python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    if 'template_tier' in d and 'options' in d:
        print('ESTIMATE_JSON')
    else:
        print('RAW_DOCUMENT')
except: print('RAW_DOCUMENT')
" <input-file>
```

- **TEXT_INPUT** → pre-estimate mode, skip Step 2, use text as scope description
- **ESTIMATE_JSON** → post-estimate mode (inherit MD, roles from JSON)
- **RAW_DOCUMENT** → pre-estimate mode (no MD numbers, ask user for roles)

### 2. Parse Input

- **Text input (no file)**: Skip parsing. Use the text description as scope input for Step 4.
- **Pre-estimate (raw docs)**:
  - Check cache: `[ -f "<file>.parsed.md" ] && [ "<file>.parsed.md" -nt "<file>" ] && echo "CACHED" || echo "STALE"`
  - If CACHED → Read `<file>.parsed.md` directly
  - If STALE/missing → `python3 .claude/skills/estimate/scripts/parse-document.py <file> --cache`
  - Use `~/.claude/skills/.venv/bin/python3` (system python3 may be < 3.10)
- **Post-estimate (JSON)**: Read JSON directly with Read tool
  - Extract `parameters.active_roles`, `parameters.role_names`
  - Extract tasks from `options[0].categories[].tasks[]` or `options[0].tasks[]`

### 3. Clarification

Ask the user:
1. **Language**: English, Vietnamese, or Japanese
2. **Breakdown level**: L1 (Epic overview), L2 (Stories), L3 (Tasks + AC)
   - Default: L2 for pre-estimate, L3 for post-estimate
3. **Roles** (pre-estimate only): Which teams? Suggest defaults: FE, BE, QA
   - Available: FE, BE, QA Manual, QA Auto, Design, PM, BrSE, Infra
   - Post-estimate: inherited from JSON `active_roles`
4. **Scope details** (text input only): Ask about key features/modules if not already described. Offer to decompose based on common patterns for the project type.

### 4. AI Decomposition

Load role definitions from `.claude/skills/estimate/knowledge-base/roles-config-defaults.yaml`.

**Pre-estimate mode:**
- Read parsed content
- Identify features/requirements
- Create Epic -> Story -> Task hierarchy
- Assign tasks to roles based on task nature
- No MD/SP numbers — focus on scope decomposition
- Add checklist items and acceptance criteria (L3 only)

**Post-estimate mode:**
- Read estimate JSON tasks
- Expand each estimate task into subtasks per role
- Set `estimate_ref` to link back to estimate task IDs
- Inherit `md` values from estimate JSON effort breakdown
- Compute story-level `total_md` from constituent task MDs
- Add checklist items and acceptance criteria (L3 only)

### 5. Write breakdown.json

Write structured JSON following [references/breakdown-json-schema.md](references/breakdown-json-schema.md).

Save to: `output/<project-slug>/breakdown/breakdown.json`
- **Multi-estimate**: If generating breakdowns for multiple estimates from the same project, use separate dirs:
  `output/<project-slug>/breakdown-<scope-slug>/breakdown.json`
  Example: `breakdown-loopa/`, `breakdown-ec-platform/`

```json
{
  "project_name": "string",
  "breakdown_level": 3,
  "language": "en",
  "source": "pre-estimate",
  "source_file": "spec.pdf",
  "generated_date": "2026-04-27",
  "active_roles": ["fe", "be", "qa_manual"],
  "role_names": { "fe": "Frontend", "be": "Backend", "qa_manual": "QA (Manual)" },
  "epics": [...]
}
```

### 5b. Validate breakdown.json

Verify before rendering:
1. Parse JSON — must be valid
2. Every epic has ≥1 story, every story has ≥1 task (L3)
3. All task `role` values in `active_roles`
4. Post-estimate: all `estimate_ref` resolve to source JSON task IDs
5. Post-estimate: sum of task `md` per story = story `total_md` = estimate task `total_md`

If agent-delegated, verify output JSON after agent completes (don't trust agent self-report).

### 6. Render Output

```bash
python3 .claude/skills/estimate/scripts/render-breakdown.py output/<project-slug>/breakdown/breakdown.json -o output/<project-slug>/breakdown/
```

Produces:
- `breakdown-index.md` — entry point linking to overview and all per-team files
- `breakdown-overview.md` — all epics + stories (L1/L2 combined)
- `{role}-tasks.md` — per-team task files (L3 only, one per active role)

## Rules

- Never generate MD/SP numbers in pre-estimate mode
- Post-estimate `md` values must match estimate JSON exactly
- Each task must have exactly one `role` assignment
- `estimate_ref` must reference valid task IDs from source estimate JSON
- L3 tasks must include `checklist` (implementation steps) and `acceptance_criteria`
- Maximum 200 lines per output file. The render script auto-splits files exceeding 200 lines at epic (`## `) boundaries into `{name}-part1.md`, `{name}-part2.md`, etc.
- **Multi-language**: The renderer produces English only. For Vietnamese/Japanese, hand-write translated markdown from breakdown.json data. Name convention: `{role}-tasks-{lang}.md` (e.g. `fe-tasks-vi.md`)

### Level Upgrade (L2 → L3 or L1 → L2)

If user requests deeper breakdown after initial output:
1. Read existing breakdown.json
2. Expand to requested level (add tasks/checklists per story)
3. Overwrite breakdown.json with new level
4. Re-render all output files

## Validation

Before generating output:
1. Every epic has at least one story
2. Every story has at least one task (L3)
3. All task roles are in `active_roles`
4. Post-estimate: `estimate_ref` links resolve to real estimate task IDs
5. Post-estimate: `md` values match source JSON

## Additional Resources

Load on demand:
- [references/breakdown-json-schema.md](references/breakdown-json-schema.md) — JSON schema docs
- [references/level-examples.md](references/level-examples.md) — L1/L2/L3 output examples
