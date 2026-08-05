# Skill Weakness Taxonomy

Checklist for the Analyze phase. Walk every category against the skill map. Cite evidence for each finding — quote the offending line or name the missing section.

## Severity Scale

- **Critical**: causes wrong behavior or silent failure (model skips a mandatory gate, contradictory instructions, broken handoff)
- **Major**: degrades output quality or wastes tokens consistently
- **Minor**: polish — clarity, formatting, discoverability

## Categories

### 1. Trigger Quality (frontmatter `description`)

- Missing trigger phrases users actually type (check against the skill's purpose)
- Description too generic — collides with sibling skills, causes wrong-skill activation
- Negative scope absent ("Not for: ...") → skill activates on out-of-scope requests

### 2. Instruction Ambiguity

- Steps that say "appropriately", "as needed", "if necessary" without criteria
- Two sections giving conflicting orders for the same situation
- Implicit assumptions about state (e.g., assumes a plan exists without checking)

### 3. Gate Discipline

- Irreversible/expensive actions without an approval gate
- Hard gates stated but no anti-rationalization table backing them (models talk themselves out of gates)
- Gates placed after the action they should guard

### 4. Error Recovery

- No recovery path for the most likely failures (missing file, invalid input, subagent failure)
- "Stop and ask" missing where blind continuation causes damage
- Retry loops without an escape hatch

### 5. Token Economy

- Eager-loaded content that should be in `references/` (load-on-demand)
- Repeated boilerplate across sections (violates DRY, bloats every activation)
- Verbose prose where a table or list carries the same instruction

### 6. Reference Staleness

- References to renamed/removed skills, agents, or commands (verify against `.claude/skills/*/SKILL.md` frontmatter names)
- Outdated tool names, paths, or APIs
- Dead links to files that no longer exist

### 7. Handoff Contracts

- Delegates to subagents without status format requirements (DONE/BLOCKED/...)
- Missing work-context/reports-path in delegation instructions
- Output location unspecified → artifacts scattered

### 8. Structural Drift

- Workflow diagram disagrees with prose steps
- Section order doesn't match the numbered flow
- `argument-hint` doesn't match documented flags

## Output Format

| # | Category | Evidence | Severity | Fix Sketch |
| --- | --- | --- | --- | --- |
| 1 | Gate discipline | "Phase 5 runs after approval" but no gate defined | Critical | Add AskUserQuestion gate before Phase 5 |
