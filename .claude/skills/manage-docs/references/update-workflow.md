# Update Workflow

## Phase 1: Parallel Codebase Scouting

1. Sweep the tree and count files and LOC per directory, skipping the noise: `.claude`, `.opencode`, `.git`, `tests`, `node_modules`, `__pycache__`, `secrets`, and the like.
2. Point only at directories **that genuinely exist** — bend to the project's real structure.
3. Reach for the `tkm:scan-codebase` skill to survey the code and send back detailed summary reports.
4. Combine those scout reports into one context summary.

## Phase 1.5: Parallel Documentation Reading

**The main agent has to launch the readers** — a subagent can't spawn its own subagents.

1. Tally the docs: `ls docs/*.md 2>/dev/null | wc -l`
2. Size them: `wc -l docs/*.md 2>/dev/null | sort -rn`
3. Pick the approach by count:
   - 1-3 files: don't bother with parallelism — doc-writer reads them itself
   - 4-6 files: send out 2-3 `Explore` agents
   - 7+ files: send out 4-5 `Explore` agents (5 is the ceiling)
4. Split the files by LOC, giving the heaviest ones their own agent
5. Brief each agent the same way: "Read these docs, extract: purpose, key sections, areas needing update. Files: {list}"
6. Roll the results back into context for doc-writer

## Phase 2.a: Detect layered docs/ spec artifacts (v4.0.0+)

Do this BEFORE you spawn `doc-writer`. It mirrors `tkm:takumi` Step 6.a, so whichever path got you here lands on the same doc-writer prompt.

> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). The commands below use `docs/` root which is correct for single-lang mode (the common case). manage-docs narrative files (`project-roadmap.md`, `code-standards.md`, `system-architecture.md`, `deployment-guide.md`) stay at `docs/` root in all modes per the manage-docs carve-out.

```bash
SPECS_PRESENT=$(ls docs/system/*.md docs/generated/*.md docs/features/*/*.md docs/flows/*.md 2>/dev/null | wc -l | tr -d ' ')  # layout-exempt: detection command; docs/ root single-lang per pointer above
# manage-docs update is typically invoked AFTER commits, so prefer last-commit diff,
# falling back to working-tree diff if HEAD~ doesn't exist (initial commit / shallow clone).
CHANGED_FILES=$(git diff --name-only HEAD~..HEAD 2>/dev/null)
[ -z "$CHANGED_FILES" ] && CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null)

# Advisory: signal absent doc layer when session changed substantial feature surface.
# Source for trigger patterns: claude/skills/takumi/references/subagent-patterns.md
#                              → ## Documentation → Trigger Mapping
TRIGGER_HITS=0
if [ -n "$CHANGED_FILES" ]; then
  TRIGGER_HITS=$(echo "$CHANGED_FILES" \
    | grep -vE '/(tests?|__tests__|spec|mocks?|fixtures?)/|\.(test|spec)\.' \
    | grep -cE '/(routes?|controllers?|api|endpoints?|models?|schema|migrations?|prisma|pages?|screens?|views?|router|navigation|auth|rbac|policy|guard|middleware|jobs?|queues?|workers?|cron|listeners?|webhooks?|observers?|sockets?|websockets?|gateways?|realtime|channels?|sse)/')
fi

if [ ! -d docs ] && [ "$TRIGGER_HITS" -ge 2 ]; then
  echo "ℹ  ./docs/ not found — ${TRIGGER_HITS} feature-surface files changed this session." 1>&2
  echo "ℹ  Consider /tkm:manage-docs init to scaffold project docs." 1>&2
elif [ -d docs ] && [ "$SPECS_PRESENT" = "0" ] && [ "$TRIGGER_HITS" -ge 2 ]; then
  echo "ℹ  spec layer (docs/system, docs/generated, docs/features, docs/flows) absent — ${TRIGGER_HITS} feature-surface files changed this session." 1>&2  # layout-exempt: advisory message text; docs/ root single-lang
  echo "ℹ  Consider /tkm:rebuild-spec to generate spec layer for richer planning context." 1>&2
fi
```

When `SPECS_PRESENT > 0`, assemble `IMPACT_MAP` from `CHANGED_FILES` against the trigger table in `claude/skills/takumi/references/subagent-patterns.md` → `## Documentation` → Trigger Mapping. When `SPECS_PRESENT == 0`, drop the artifact branch outright — say nothing. And if `CHANGED_FILES` comes back empty (a clean tree), skip the artifact branch too: there is nothing to map onto.

**Absent-layer advisory:** that `if/elif` block writes to stderr only and **never** reaches the `doc-writer` prompt — the surgical-edit contract stays untouched. The two layers can't both be missing in a meaningful way: an absent `docs/` mutes the spec-layer advisory, since the layered namespaces (`docs/system/`, `docs/generated/`, …) <!-- layout-exempt: advisory prose naming the spec namespaces -->
have nowhere to live without their `docs/` parent. The `≥ 2` threshold is counted **after** test/mock/fixture paths are stripped out. Contract: [`_shared/docs-canonical-mapping.md` § Absent-Layer Advisory](../../_shared/docs-canonical-mapping.md#absent-layer-advisory).

## Phase 2: Documentation Update (doc-writer Agent)

**CRITICAL:** Spawn the `doc-writer` agent through the Task tool, carrying both the merged reports and the doc readings.

Drive it with the canonical structured prompt from `claude/skills/takumi/references/subagent-patterns.md` → `## Documentation`. Swap `[plan-name]` for `manage-docs update session (YYYY-MM-DD)`. Inline `CHANGED_FILES`, the general docs list, and — when `SPECS_PRESENT > 0` — the resolved `IMPACT_MAP`. Don't restate the template body here; link to it and keep things DRY.

The short version (the whole thing lives in `subagent-patterns.md`):
- General docs: README plus the 7 under `docs/` (project-overview-pdr, codebase-summary, code-standards, system-architecture, project-roadmap, deployment-guide, design-guidelines).
- When `SPECS_PRESENT > 0`: tack on the surgical-edit instructions, the `IMPACT_MAP`, and the escalation rule — more than 3 changed source files hitting one artifact means advise `/tkm:rebuild-spec --artifact NAME`.
- Don't author new feature spec files yourself; point to `/tkm:rebuild-spec --features F###`.

## Additional requests
<additional_requests>
  $ARGUMENTS
</additional_requests>

## Phase 3: Size Check (Post-Update)

Once doc-writer is done:
1. Check line counts: `wc -l docs/*.md 2>/dev/null | sort -rn`
2. Read `docs.maxLoc` off the session context (defaults to 800)
3. Any file over the limit: report it and hand the decision to the user

## Phase 4: Documentation Validation (Post-Update)

Run a validation pass to catch anything that drifted from reality:
1. Run: `node .claude/scripts/validate-docs.cjs docs/`
2. Show the validation report — warnings only, nothing blocking
3. It looks at: code references, internal links, config keys

## Important
- `docs/` is the source of truth.
- **Do not** start implementing.
