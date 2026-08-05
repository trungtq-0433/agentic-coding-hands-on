<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Waves W5.5, W5.6
<!-- Updated: Phase-02 strip — W6/post-W6/W6.5 relocated to pipeline-feature-specs.md -->
Loaded by orchestrator before W5.5/W5.6 dispatch (default/core run). W6 fan-out, post-W6 consolidation, and W6.5 validators now live in `pipeline-feature-specs.md` (loaded only when `--feature-specs` flag is set). See `pipeline.md` for wave dep graph + incremental preamble.


### Wave 5.5 — Feature existence gate

After Wave 5 completes, the orchestrator runs the existence validator BEFORE Wave 6 dispatch. Validator is unconditional — no env var, no opt-in (skipped in incremental mode if `w5_reran === false`).

```
// Wave 5.5 — conditional on w5_reran in incremental mode
if (mode === "full" || w5_reran) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_feature_existence.py \
    --plan-dir plans/<active-plan> \
    --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json

  exit 0 → status PASS or WARN → proceed to Wave 6 fan-out
  exit 1 → status FAIL → HALT pipeline; surface JSON issues to user; prompt fix; NO Wave 6 dispatch
  exit 2 → internal validator error → surface stderr; halt
} else {
  console.log("[INFO] W5.5 skipped — W5 not re-run (incremental: prior validation carries forward)")
}
```

Validator authority: `references/canonical-fcode-schema.md` (schema + slug grammar). Output schema: `validation-summary.json` (see `pipeline-feature-specs.md § Wave FS.2` for the feature-specs pass schema — W6.5 is now FS.2 in the standalone pass).

### Wave 5 post-write: update session-context feature_count

After Wave 5 completes (and W5.5 passes), update the shared session-context file with the actual feature count:

```
const featureCount = JSON.parse(readFile("plans/<active-plan>/artifacts/_canonical-fcodes.json")).features.length
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_session_context.py \
  --plan-dir plans/<active-plan> \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --stack-note "${stackNote}" \
  --feature-count ${featureCount}
```

// --- Wave 5.6: FeatureList sanity review (fast gate before FS.1 dispatch) ---
// Runs after W5.5 passes. Single reviewer task, FeatureList-scoped.
// FS.1 fan-out dispatches ONLY after W5.6 reports passed: true.
// Incremental: skip W5.6 if w5_reran === false (FeatureList not re-generated this run).

let w56TaskId = null
if (mode === "full" || w5_reran) {
  w56TaskId = TaskCreate({
    subject: "Wave5.6: feature-list-review",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Fast sanity review of FeatureList ONLY — do NOT review other core artifacts (that is Wave 7a's scope).

INPUT: plans/<active-plan>/artifacts/feature-list.md

CHECKS (run all, report each separately):

**Group A — Structural integrity (cross-reference checks):**
1. **Coverage completeness**: are all US### from user-stories.md referenced by at least one F###?
   - Missing US### → critical
   - Missing SCR### (from screen-list.md main index) → critical. **SCR coverage applies to ANY stack that produced a screen-list (web route-view AND Delphi dfm-form).** If screen-list.md does NOT exist (headless: screen_source none, e.g. oracle-plsql) → SKIP the SCR coverage check entirely (there are no screens to cover); do NOT flag its absence.
2. **Orphan codes**: codes in FeatureList not found in their source artifact
   - US### in F### but not in user-stories.md → critical
   - SCR### in F### but not in screen-list.md → critical (skip when no screen-list.md is produced)
3. **F-code uniqueness**: no duplicate F-code numbers across Feature Details

**Group B — Quality criteria (per-F### semantic checks; read Feature Details section):**
4. **Single Intent**: each F### describes exactly one user-facing intent
   - Fail: F003_UserManagement describes login + profile edit + admin dashboard (3 intents)
   - → critical if multiple intents detected
5. **Clear Flow**: each F### has an identifiable input→process→output
   - Fail: F007_System — no clear what triggers it, what it processes, or what user gets
   - → warning (flag for human review)
6. **Vague naming**: F### name is too broad to scope a sprint
   - Patterns: "Management", "System", "Handler", "Admin", "CRUD" as the ONLY noun
   - → warning
7. **Scope overlap**: two F### share >50% of the same US### or SCR### keywords in description
   - → warning

**Group C — Grouping coherence:**
8. **Grouping coherence**: do F-code assignments reflect logical feature boundaries?
   - No F### should aggregate unrelated concerns
   - → critical if clearly mixed concerns

OUTPUT: plans/<active-plan>/artifacts/feature-list-review.md

Use this exact frontmatter:
\`\`\`yaml
---
passed: true   # true = FS.1 (feature-specs pass) can proceed; false = halt, surface issues to user
issues: 0      # count of critical findings
warnings: 0    # count of non-blocking findings
---
\`\`\`
Then list issues in markdown body.

Passed Checks: ONE LINE per check (\`✓ <check_name>\`). NO prose.

TOKEN BUDGET: Load full feature-list.md (Feature Details needed for quality checks). Load user-stories.md (headers + US### list only). Load screen-list.md (SCR### index only). DO NOT load full upstream artifacts beyond these.`,
    addBlockedBy: [featureListTaskId]
  })
} else {
  console.log("[INFO] W5.6 skipped — W5 not re-run (incremental: prior FeatureList carries forward)")
  w56TaskId = `SKIPPED:W5.6`
}

// Halt on W5.6 failure before FS.1 dispatch
if (w56TaskId && !w56TaskId.startsWith("SKIPPED:")) {
  if (!existsNonEmpty("plans/<active-plan>/artifacts/feature-list-review.md")) {
    throw new Error("W5.6 HALT — gate output missing: feature-list-review.md was not written. Check W5.6 task for errors.")
  }
  const w56Content = readFile("plans/<active-plan>/artifacts/feature-list-review.md")
  const w56fm = parseFrontmatter(w56Content)
  if (w56fm.passed === "false" || w56fm.passed === false) {
    throw new Error(
      `W5.6 HALT — FeatureList has ${w56fm.issues} critical issue(s). ` +
      `Fix feature-list.md, then re-run Wave 5 (--artifact feature-list) or restart from W5. ` +
      `Review: plans/<active-plan>/artifacts/feature-list-review.md`
    )
  }
  console.log(`[INFO] W5.6 passed (issues: ${w56fm.issues ?? 0}, warnings: ${w56fm.warnings ?? 0})`)
}

const w56Blocker = (w56TaskId && !w56TaskId.startsWith("SKIPPED:")) ? w56TaskId : featureListTaskId

// Default (core) run ends here. After W5.6 gate passes, dispatch W7a directly.
// FS.1 fan-out, FS.1.5 Feature Entry Points consolidation, and FS.2 validators are
// part of the --feature-specs standalone pass (see pipeline-feature-specs.md § Wave FS.1–FS.2).
//
// [RT-SC7/FM5] screen-flow.md is promoted by Wave 9 with {POPULATED_BY_W6} replaced by an
// HTML comment so no raw template token reaches docs/generated/screen-flow.md:
//   <!-- Feature Entry Points: run /tkm:rebuild-spec --feature-specs to populate -->
// The --feature-specs pass (FS.1.5) fills the real content via the same replacement pattern.

