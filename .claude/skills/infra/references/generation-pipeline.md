# Infrastructure Generation Pipeline

5-phase pipeline: context → generate → validate → review → finalize.

## Pipeline Phases

```
Phase 1: Load Context → Phase 2: Generate → Phase 3: Validate → Phase 4: Review → Phase 5: Finalize
```

Track progress in a single todo list. After Phase 1 identifies resources, expand Phase 2 into per-module items so progress is visible at the resource level.

---

## Phase 1: Load Context

1. Read ONLY the references listed in the subcommand's Step 1 (SKILL.md) — do NOT read other references yet
2. Run `python3 scripts/detect-tools.py` — capture JSON output for later phases
3. Identify target resources and dependencies from user input or Mermaid diagram

4. Expand the todo list: add one item per module/resource for Phase 2 (e.g., "Generate VPC module", "Generate ECS module") plus items for Phases 3-5

**Output:** `✓ Phase 1: Context loaded — [N] resources identified, tools: [list]`

---

## Phase 2: Generate Terraform Code

Rules (all mandatory):
1. Follow `references/terraform-conventions.md` naming and structure exactly
2. Create standard module structure: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`
3. For `generate` subcommand: create `modules/` and `envs/{dev,staging,prod}/` layout
4. Add `# REVIEW BEFORE DEPLOY` as first line in every `.tf` file
5. No hardcoded secrets — use variables with `sensitive = true` where needed
6. All security group rules must have `description` fields
7. Include mandatory tags: Name, Environment, Project, ManagedBy
8. Check Version Policy in SKILL.md — never use outdated service versions

**Output:** `✓ Phase 2: Generated [N] files across [M] modules`

---

## Phase 3: Validate

Run available tools (skip unavailable ones gracefully):

```bash
# If terraform available
terraform fmt -recursive -check [path]
terraform validate [path]

# If tfsec available
tfsec [path] --format markdown

# If checkov available
checkov -d [path] --framework terraform --compact
```

Fix any `terraform fmt` or `terraform validate` errors before proceeding.

**Output:** `✓ Phase 3: Validated — fmt [pass/skip], validate [pass/skip], tfsec [N findings/skip], checkov [N findings/skip]`

---

## Phase 4: Review (Security + Cost + Redundancy)

**Read NOW** (not before): `references/security-review-rules.md`, `references/cost-estimation-tools.md`, `references/redundant-resource-guard.md`

### 4a: Security Review
- AI review: check ALL generated `.tf` files against `references/security-review-rules.md` HIGH checklist
- Merge with tfsec/checkov findings from Phase 3 (deduplicate)
- Classify each finding: HIGH / MEDIUM / LOW

### 4b: Cost Estimation
```bash
python3 scripts/run-cost-estimate.py [path]
```
- If no `.tfvars` with `region` exists, create a minimal one so cost tools resolve pricing correctly

### 4c: Redundancy Check
- Review all generated resource types against `references/redundant-resource-guard.md`
- Flag overlapping resources as LOW severity findings
- Remove redundant resources unless user explicitly requested both

### 4d: Code Review (subagent — MANDATORY)
Spawn `reviewer` subagent:
```
Agent(subagent_type="reviewer",
  prompt="Review Terraform code at [path]. Check: security (CIS/Well-Architected), naming conventions, tag coverage, variable validation, hardcoded values. Return score (X/10), critical issues, warnings.",
  description="Review Terraform code")
```
- If score < 8 or critical issues found: fix and re-review (max 2 cycles)
- If score >= 8 with 0 critical: proceed

**Output:** `✓ Phase 4: Review — security [N findings], cost [$X/mo], redundancy [clean/N issues], code [score/10]`

---

## Phase 5: Finalize

### 5a: Output Unified Summary (MANDATORY)

**Read NOW:** `references/unified-summary-template.md` — produce the full Unified Summary with all 5 sections (Tools, Security, Cost, Files, Summary).

### 5b: Save Cost Breakdown
Write to `./docs/infra-cost-breakdown.md` (overwrite each run).
Separate `## Dev`, `## Staging`, `## Production` sections with subtotals. End with `## Total`.

### 5c: Documentation (subagent — if docs impact)
If new modules or significant infrastructure changes:
```
Agent(subagent_type="doc-writer",
  prompt="Update docs/system-architecture.md with new infrastructure: [resource list]. Keep concise.",  # layout-exempt: manage-docs carve-out — system-architecture.md stays at docs/ root in all modes
  description="Update infra docs")
```

### 5d: Ask About Commit
Ask user: "Would you like to commit these changes?"
If yes, spawn git subagent:
```
Agent(subagent_type="git-manager",
  prompt="Stage and commit Terraform changes with conventional commit message. Scope: infra.",
  description="Commit infra changes")
```

**Output:** `✓ Phase 5: Finalized — summary output, cost saved, [committed/pending]`

---

## Subagent Summary

| Phase | Subagent | Required? |
|-------|----------|-----------|
| Phase 4d | `reviewer` | **MANDATORY** |
| Phase 5c | `doc-writer` | If docs impact |
| Phase 5d | `git-manager` | If user approves |

Minimum subagent calls per run: 1 (reviewer). Typical: 2-3.

---

## Error Recovery

| Error | Action |
|-------|--------|
| `terraform validate` fails | Fix syntax errors, re-run Phase 3 |
| Code review score < 8 | Fix critical issues, re-run Phase 4d (max 2 cycles) |
| Cost estimate fails | Fall back to heuristic tier, note in summary |
| Redundant resources found | Remove and re-validate unless user confirmed |
