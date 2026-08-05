---
name: tkm:kaizen
description: "Improve or compare Takumi skills without touching shipped files — analyze weaknesses, challenge assumptions, benchmark before/after, deliver improvements as user-owned extensions that survive kit updates. Triggers on: 'improve skill', 'tune skill', 'skill is weak', 'compare skill', 'kaizen', 'extend skill', 'customize skill', 'skill extension'."
argument-hint: "<skill-name> [--compare <alt-skill-path>] [--shared] [--auto|--fast]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: configuration-level
triggers: ["improve skill", "tune skill", "skill is weak", "compare skill", "extend skill", "customize skill", "kaizen"]
---

# Kaizen — The Blade Is Never Finished Sharpening

A craftsman does not replace a good tool — they refine it.
Kaizen interrogates an existing skill, finds where it cuts poorly,
and hones it through extensions: layered on top, never carved into the original.

Scope: skill weakness analysis, before/after benchmarking, skill-vs-skill comparison, extension authoring.
Not for: creating new skills (`tkm:document-skills`), fixing app code (`tkm:fix-bug`).

## Usage

```text
/tkm:kaizen <skill-name> [--compare <alt-skill-path>] [--shared] [--auto|--fast]
```

Modes:
- default (improve): full workflow, deliver improvements as extension files
- `--compare <alt-skill-path>`: head-to-head analysis of the target skill vs an alternative implementation (local dir with a SKILL.md). Report only — no extension written.

Delivery target:
- default: write to local `.claude/skills/<dir>/extensions/` (personal, gitignored)
- `--shared`: write to the team-shared, git-tracked dir from `skillExtensions.sharedDir` so teammates get the improvement on pull

Speed:
- `--fast`: skip Challenge and Benchmark, static analysis only, auto-approve
- `--auto`: full workflow, auto-approve gates
- default: full workflow with approval gates

Intent detection:
- "compare", "vs", "against" → `--compare`
- "quick", "fast" → `--fast`
- "share", "team", "push for the team" → `--shared`
- skill name resolves from `.claude/skills/<dir>/SKILL.md` frontmatter `name:` field; accept both `tkm:review-code` and `review-code`

## The Iron Law

<HARD-GATE>
Deliver MUST write ONLY to an extensions location — never edit shipped files:
- default: local `.claude/skills/<dir>/extensions/`
- `--shared`: the team dir from `skillExtensions.sharedDir`, laid out `<sharedDir>/<dir>/`
Editing a shipped SKILL.md or its references is FORBIDDEN — the installer tracks
those files by checksum; direct edits cause update conflicts and lost work.
Extensions live outside the kit manifest, are classified user-owned, and survive
every `tkm update` untouched. This is the entire point of the mechanism.
</HARD-GATE>

## Workflow

```text
[1. Recon] → [2. Map] → [3. Analyze] → [4. Challenge] → [5. Benchmark] → [6. Deliver]
```

Hard gate: Phase 4 must complete before Phase 5/6. Do not benchmark or deliver before confronting trade-offs.

### 1. Recon

Locate and absorb the target.

1. Resolve skill dir: `.claude/skills/<name>/SKILL.md`. Not found → list closest matches (`ls .claude/skills/`), ask via `AskUserQuestion`.
2. Read SKILL.md + every file in `references/`.
3. Read existing `extensions/*.md` and `extensions/evals/` if present.
4. **Anchor drift check**: for each existing extension with `type: override:<section>`, verify the section heading still exists in the current SKILL.md. Stale anchors → flag in report.
5. Compare mode: repeat 1–3 for the alternative path. Invalid path or missing SKILL.md → ask for correction.

Output: skill manifest (name, version, files, existing extensions), drift flags.

### 2. Map

Dissect the skill's anatomy:

1. Frontmatter quality: `name`, `description` trigger coverage, `argument-hint`
2. Workflow structure: phases, ordering, decision points
3. Gates: hard gates, approval gates, anti-rationalization tables
4. References: load-on-demand vs inline, staleness
5. Token footprint: SKILL.md size, what loads eagerly vs lazily
6. Error recovery paths and handoff contracts (which skills/agents it delegates to)

Compare mode: build the same map for both, then a two-column matrix.

### 3. Analyze

Load `references/weakness-taxonomy.md`. Walk every category against the map.

For each finding: category, evidence (quote the offending line/section), severity (critical/major/minor), proposed fix sketch.

Compare mode focus: architectural differences, gate discipline, token economy, trigger quality — feed the head-to-head table.

### 4. Challenge

Load `references/challenge-framework.md`.

Produce at least 5 challenge questions against your own findings. For each: current behavior, proposed change, risk if the improvement assumption is wrong.

Present a decision matrix and get approval via `AskUserQuestion` (skip prompt in `--auto`; phase skipped entirely in `--fast`).

| # | Finding | Current | Proposed | Risk | Apply? |
| --- | --- | --- | --- | --- | --- |

### 5. Benchmark

Load `references/benchmark-protocol.md`. Skipped in `--fast` (static analysis stands alone).

1. Load or generate eval cases → `extensions/evals/` (see protocol)
2. **Confirmation gate**: present estimated cost (cases × variants × runs) before spawning anything. `--auto` proceeds only below the protocol's cost ceiling.
3. Run baseline vs candidate (improve mode) or skill A vs skill B (compare mode) via subagents, blind-judged
4. Decision rule per protocol: apply / don't apply / tie-break on token cost

Benchmark infrastructure failure → fall back to static analysis, mark report "benchmark: not run".

### 6. Deliver

Improve mode:
1. Resolve delivery dir:
   - default → `.claude/skills/<dir>/extensions/<improvement-slug>.md` (local, gitignored)
   - `--shared` → `<sharedDir>/<dir>/<improvement-slug>.md`, where `<sharedDir>` = `skillExtensions.sharedDir` from config. If that key is unset, STOP and tell the user to run `tkm config set skillExtensions.sharedDir <path>` first (use an absolute path or a path inside the project root that lives in a git-tracked repo the team commits). Do not silently fall back to local.
2. Write approved improvements as extension files at the resolved dir.
3. Frontmatter contract (full spec: `references/extension-authoring-guide.md`):
   ```markdown
   ---
   extends: tkm:<skill-name>
   type: pre | post | override:<section-heading>
   ---
   ```
4. Prefer `pre`/`post` over `override:` — section headings can be renamed by kit updates
5. Verify: `git diff` shows ONLY new files under the resolved extensions dir. Note: a `--shared` improvement with the same filename as a local file is shadowed at load time (local overrides shared) — avoid slug collisions.
6. Write summary report to `plans/reports/` (improvements, delivery target, benchmark verdict, skipped findings)

Compare mode: write the comparison report to `plans/reports/` and stop.

```markdown
# Skill Comparison: <target> vs <alternative>
## Head-to-Head
| Aspect | <target> | <alternative> | Edge |
| --- | --- | --- | --- |
## Benchmark Verdict
## Recommendation
```

## Error Recovery

- Skill not found → list near matches, ask
- Alt path invalid (compare) → ask for a directory containing SKILL.md
- Benchmark subagent fails repeatedly → fallback to static analysis, note in report
- All findings rejected at Challenge → write analysis report only, no extension
- Extension dir conflicts with an existing same-name file → suffix slug, never overwrite silently
- `--shared` but `skillExtensions.sharedDir` unset → STOP; instruct `tkm config set skillExtensions.sharedDir <path>` (absolute, or inside project root; must be a git-tracked repo the team commits)

## References

- `references/weakness-taxonomy.md` — Analyze checklist
- `references/challenge-framework.md` — Challenge prompts + decision matrix
- `references/benchmark-protocol.md` — A/B run + blind judging protocol
- `references/eval-templates.md` — cases.md / rubric.md skeletons
- `references/extension-authoring-guide.md` — extension format spec + worked example
