---
name: tkm:momorph-implement-design
description: Use this skill to code UI pixel-perfect with Figma designs on MoMorph (web or mobile). ACTIVATE when user provides a momorph URL like `https://momorph.ai/files/{fileKey}/screens/{screenId}`, gives a `fileKey`+`screenId` pair, or mentions keywords "momorph", "figma design", "code from design", "implement figma screen", "reproduce UI", "translate design to code", "pixel-perfect Figma", "code app from figma".
---

# MoMorph Implement Design

Code UI from Figma designs on MoMorph — pixel-perfect, parallel, code-first. Both web (React/Vue/Next/Svelte) and mobile (React Native, Flutter, SwiftUI, Compose).

## Philosophy: incremental query, code first, assets in background

DO NOT dump entire frame to file (context overflow). Query incrementally via MCP as needed. Subagent calls MCP tool directly with the `nodeId` it's coding — context-efficient.

```
Phase 1:  get_overview + get_media_files (parallel)        ← grab layout + asset URLs
Phase 2:  plan-only assets.md + bg downloader              ← assets planned immediately
         + spawn N implementer subagents (parallel bg)    ← CODING STARTS NOW
Phase 3:  compose root + validate + visual diff            ← when subagents done → pixel-perfect
Phase 4:  polish (responsive + hover/focus + transition)   ← REQUIRED for web (default-on)
```

## Principles

1. **Figma = source of truth** — never guess. Get values via MCP tools.
2. **Media node = asset** — name contains `mm_media_` (case-insensitive). DO NOT code subtree, render asset element from `assets.md`.
3. **MCP queries by branch** — never pull the whole frame. Each call returns a small region, no context overflow.
4. **Asset path is a PLAN** — `assets.md` is written immediately from `media_files.json` (no need to wait for download). Files land progressively in the background.
5. **Maximize parallelism** — bundle every independent I/O into a single turn.

## Input

`fileKey` + `screenId` — extracted from URL `https://momorph.ai/files/{fileKey}/screens/{screenId}`. Reference: `.claude/rules/momorph/momorph-awareness.md`.

Stack/styling/naming → infer from project files. If unclear → AskUserQuestion.

---

## MCP toolkit

| Tool | When to use |
|------|-------------|
| `get_overview(fileKey, screenId)` | **First call** — overview tree (id/name/type/hierarchy, NO style). Grasp layout + identify sections. |
| `query_section(fileKey, screenId, idOrName, depth?)` | Pull one subtree by node ID or name. Depth-limitable. Subagent zooms into its section. |
| `query_component(fileKey, screenId, name)` | Fuzzy search by component name. Useful for finding repeated patterns. |
| `query_by_type(fileKey, screenId, type)` | All nodes of a type (TEXT/INSTANCE/FRAME...). E.g. find every TEXT to load fonts. |
| `get_node(fileKey, screenId, nodeId)` | Full node detail (with style). Use when accurate styling needed. |
| `get_node_context(fileKey, screenId, nodeId)` | Node + parent + siblings + role hint (background/text/icon/overlay). Understand layer composition. |
| `list_media_nodes(fileKey, screenId)` | List media assets with size + role hint. Optional — use when classification needed first. |
| `get_media_files(fileKey, screenId)` | Map `{nodeId: download_url}` for downloading assets. **Required** in Phase 1. |
| `get_frame_image(fileKey, screenId)` | Design screenshot — only for final visual diff, not in Phase 1. |
| `get_figma_image(fileKey, screenId, nodeId, format)` | **ONLY for subagent fallback case**: `mm_media_*` node has NO URL in `get_media_files` (file not yet uploaded to Figma cloud). DO NOT use otherwise (rate-limit). See rule 2 in `code-rules.md` + subagent code procedure. |

**Recommended subagent workflow:**
`query_section(sectionId)` → read subtree → encounter node needing full style → `get_node(nodeId)` → encounter node needing role context → `get_node_context(nodeId)`.

---

## Phase 1 — Overview + media URLs + media names (3 parallel MCP calls)

Within **a single message**, call in parallel:

| Tool | Output |
|------|--------|
| `get_overview(fileKey, screenId)` | id/name/type/hierarchy tree — read directly |
| `get_media_files(fileKey, screenId)` | File path → `media_files.json` (note path) |
| `list_media_nodes(fileKey, screenId)` | Each media with name + size + role → use for asset DEDUP |

From overview, identify **sections** = direct children of root frame, skip nodes named `mm_media_*`.

From `list_media_nodes`, build map `{nodeId: name}` (save to `data/node_names.json`) → asset_downloader uses it to name files by node name → 2 nodes with same name = 1 file (dedup).

---

## Phase 2 — Asset plan + Spawn N subagents (1 message)

Within **a single message**, in parallel:

### Detect asset dir in PROJECT (first time only)

Assets are NO LONGER stored in plan_dir — write directly to project so code can import them.

| Stack | `--out` (filesystem) | `--code-path-prefix` (manifest path) |
|-------|---------------------|--------------------------------------|
| Next.js / Vue / Svelte (web) | `public/{screen-slug}/` | `/{screen-slug}` |
| Vite React | `public/{screen-slug}/` | `/{screen-slug}` |
| React Native | `src/assets/{screen-slug}/` | `@/assets/{screen-slug}` (per project alias) |
| Flutter | `assets/{screen-slug}/` | `assets/{screen-slug}` (remember to add to `pubspec.yaml`) |
| SwiftUI / Compose | `Resources/Momorph/{ScreenSlug}/` | filename only (use `Image("logo")`) |

If the project has a different convention (`./docs/code-standards.md` or an existing assets folder) → follow it.

### A. Bash chain — write data + plan asset (with name-based dedup)

```bash
mkdir -p {plan_dir}/data && mkdir -p {project_assets_out} && \
cp {media_files_result_path} {plan_dir}/data/media_files.json && \
# node_names.json: {nodeId: name} — from list_media_nodes (Phase 1)
echo '{embed_node_names_json}' > {plan_dir}/data/node_names.json && \
.claude/skills/.venv/bin/python3 .claude/skills/momorph-implement-design/scripts/asset_downloader.py \
  {plan_dir}/data/media_files.json \
  --names {plan_dir}/data/node_names.json \
  --out {project_assets_out} \
  --code-path-prefix {code_path_prefix} \
  --plan-only \
  --manifest {plan_dir}/data/assets.md
```

`--plan-only` writes the full `assets.md` IMMEDIATELY (subagents read it right away). `--names` enables dedup by node name. `--code-path-prefix` makes manifest paths **import-ready** — code can use the path from the manifest as-is, no edits needed.

### B. Bash background — actually download files into project dir

```bash
# run_in_background=true
.claude/skills/.venv/bin/python3 .claude/skills/momorph-implement-design/scripts/asset_downloader.py \
  {plan_dir}/data/media_files.json \
  --names {plan_dir}/data/node_names.json \
  --out {project_assets_out} \
  --code-path-prefix {code_path_prefix} \
  --workers 8 \
  --manifest {plan_dir}/data/assets.md
```

### C. Spawn N implementer subagents (same message, `run_in_background=true`)

One section → one `Agent(subagent_type="implementer", run_in_background=true)`. Prompt template: `references/subagent-prompt-template.md`.

**Resource guardrail:** N ≤ 6 per batch. > 6 sections → batch in groups of 5–6.

### Section too large?

Before spawning, call `query_section(sectionId, depth=2)` to inspect level-2 structure. If many large sub-sections → split into 2–3 subagents per section.

---

## Phase 3 — Compose + validate

### 3.1 — Compose screen root

Create the root file per project convention, importing N section components in the order they appear in the design (from Phase 1 overview).

### 3.2 — Validate coverage (auto)

```bash
.claude/skills/.venv/bin/python3 .claude/skills/momorph-implement-design/scripts/validate_coverage.py \
  --assets {plan_dir}/data/assets.md \
  --code {component_dir}
```

Exit `0` = ok. Exit `2` = some asset missing → prints missing nodeIds → spawn one implementer to fix.

### 3.3 — Visual diff (web — Playwright + native vision)

**Web stack** (Next/React/Vue/Svelte): only requires the `playwright` MCP + Claude `Read` tool (reads images directly).

```
1. Pull design image (once — run parallel with dev-server spawn)
   mcp__momorph__get_frame_image(fileKey, screenId)
   → cp to {plan_dir}/data/preview.png

2. Start dev server (Bash run_in_background=true)

3. Capture actual UI (same message as steps 1+2 if possible):
   browser_navigate(url=http://localhost:3000/{route})
   browser_resize(width={designWidth}, height={designHeight})
   browser_take_screenshot(filename={plan_dir}/data/actual.png, fullPage=true)

4. Orchestrator uses Read tool on both images:
   Read(data/preview.png) + Read(data/actual.png)
   → compare directly, no external skill needed.
   Check 5 categories: FONT / BORDER RADIUS (wrapper matches asset?) /
   ALIGNMENT / SPACING / correct ASSET.

5. Large diff → query MCP for the wrong region → spawn one implementer to fix → loop step 3.
```

**Optimization:** cap at ≤ 2 visual-diff rounds (1 initial + 1 post-fix). Accept small diffs.

**Mobile stack** (RN/Flutter/SwiftUI/Compose): run simulator + screenshot CLI (`xcrun simctl`, `adb screencap`) → orchestrator uses `Read` to compare against `preview.png`. Manual.

### 3.4 — Hand-off to Phase 4 (web stack — DO NOT skip)

After visual diff passes, the screen is **pixel-perfect but not done**. Proceed directly to Phase 4. Do NOT report the screen as completed yet. Do NOT pause for user confirmation unless user explicitly opted out earlier.

---

## Phase 4 — Polish (REQUIRED for web)

Run AFTER Phase 3 visual diff has passed. This is a **restrained additive** step, NOT a re-edit of pixel-perfect output.

**Trigger:** ⚠️ **Default-on for web stack** — orchestrator MUST run Phase 4 before declaring the screen done. Do NOT skip. Do NOT wait for the user to ask. Pixel-perfect alone is NOT a complete screen — interactive states + responsive breakpoints are part of the deliverable.

**Skip only when:** user explicitly says "skip polish" / "no responsive" / "static only", OR mobile native stack with single device viewport (still apply hover→pressed mapping where applicable).

### Scope (see `references/polish-rules.md` for details)

| Item | Content |
|------|---------|
| Responsive | Mobile/tablet/desktop breakpoint adaptation. Containered → mobile padding; multi-col → stack; hero text scale |
| Hover/focus/pressed | Button/link/card/input — default pattern (200ms ease) or Figma variant if available |
| Transition | `opacity`/`transform`/`background`/`shadow` 150–300ms ease. Respect `prefers-reduced-motion` |
| Entrance | Optional: fade-in/slide-up for hero. Use sparingly |

### DO NOT

- Redesign away from Figma (changing layout/colors/typography)
- Complex animation (parallax, scroll-jacking, GSAP timelines)
- Drag/swipe/gesture, advanced micro-interactions
- Business logic, validation, loading/skeleton states

### Procedure

1. Read pixel-perfect file list from Phase 2/3 reports.
2. Read project breakpoint convention (Tailwind config / MUI theme / CSS vars).
3. Spawn one implementer subagent with prompt: "polish UI per `polish-rules.md`. File list: [...]. Stack: [...]. Breakpoint: [...]." — subagent handles whole-screen (responsive needs cross-section view).
4. Verify visually at 3 viewports: 375 / 768 / 1280 (web). Mobile native: check rotation + tablet if applicable.
5. Compile + lint pass. Report: states added, breakpoint changes.

**Common bug check** (always check after diff):
- **UI not filling viewport**, fixed at design width (e.g. `390px`) → empty side gutters on larger screens. Root component must be `width: 100%`, DO NOT hardcode design width. See rule 3 `Sizing` + Anti-pitfall #4.
- **Containered layout misuse** (web design uses 1440 artboard + 1200 centered content) → agent applies `width: 1200px` rigidly → content sticks to the left. Must use `max-width: 1200px + margin: 0 auto + width: 100%`. See rule 3 Containered layout in `code-rules.md`.
- Wrapper element missing `border-radius` matching the inner asset → shadow exposes a rectangle (rule 2b in code-rules.md).
- **SVG icon wrong color** (e.g. shows white) → asset rendered as `<img>` instead of inline component → CSS can't control color. Convert to inline SVG + `currentColor` + parent `color` from Figma `fills`. See rule 2a + Anti-pitfall #5.
- Multiple nodeIds mapped to the same `assets.md` filename but code imports 2 different files → re-check asset paths.

---

## Subagent status

| Status | Action |
|--------|--------|
| `DONE` | Note files, continue |
| `DONE_WITH_CONCERNS` | Correctness concern → fix; observational → continue |
| `BLOCKED` | Provide more context / split task → re-spawn once. Still BLOCKED → escalate |
| `NEEDS_CONTEXT` | Provide missing context → re-spawn |

Never retry blindly 3 times.

---

## Code rules

`references/code-rules.md` — shared by orchestrator and subagents.

## When to stop and ask

- Missing `fileKey` / `screenId`.
- Section too large (sub-sections > 5 levels deep) → confirm splitting.

## Resources

| File | Purpose |
|------|---------|
| `scripts/asset_downloader.py` | Plan + parallel asset download. Supports `--plan-only` |
| `scripts/validate_coverage.py` | Auto check asset coverage |
| `scripts/README.md` | Script details |
| `references/code-rules.md` | General code rules (Phase 2) |
| `references/polish-rules.md` | Responsive + hover/focus + transition (Phase 4) |
| `references/subagent-prompt-template.md` | Implementer prompt template |
| `references/mcp-template.json` | Sample momorph MCP config |

## Scope

**DO:** code static/presentational UI (web + mobile), pull assets, validate coverage. **Phase 4 polish (REQUIRED for web):** responsive + hover/focus + light transition.

**DO NOT:** backend/API, business logic, complex state, complex animation (parallax, scroll-jacking), redesign away from the design.
