# Subagent Prompt Template

Template for one `implementer` subagent coding one section. The orchestrator fills in real values, embeds the slim subtree from `get_overview`, and spawns `Agent(subagent_type="implementer", run_in_background=true)`.

## Template

```
## Task
Code the UI component for one section of a MoMorph screen, following Figma — pixel-perfect, 1-1 mapping nodeId → element.

## Section
- fileKey: {fileKey}
- screenId: {screenId}
- sectionId: {sectionId}
- sectionName: {sectionName}
- Output file: {component_path}/{section-slug}.{ext}
- Project assets dir: {project_assets_out}    ← used for fallback asset save (see code procedure step 2)
- Asset code-path prefix: {code_path_prefix}  ← import path prefix (e.g. `/home`, `@/assets/home`)

Stack/styling/naming → infer from project files.

## Slim subtree (extracted from get_overview, no styles)
```json
{embed_section_slim_tree_from_overview}
```
↑ This tree shapes the layout and identifies media nodes early. Style/details → query MCP when needed.

## Asset mapping
File: {plan_dir}/data/assets.md (mapping nodeId → file path).
Path is a **plan** — file may still be downloading in the background. Use the path as-is, no need to check existence.

## MCP toolkit (REQUIRED — DO NOT guess values)

| Tool | When to use |
|------|-------------|
| `mcp__momorph__query_section(fileKey, screenId, idOrName, depth?)` | Zoom deeper into the section when the slim subtree is insufficient |
| `mcp__momorph__get_node(fileKey, screenId, nodeId)` | Full node detail INCLUDING STYLE (color, font, padding, radius, shadow...) |
| `mcp__momorph__get_node_context(fileKey, screenId, nodeId)` | Node + parent + siblings + role hint (background/text/icon/overlay) — when role is unclear |
| `mcp__momorph__query_component(fileKey, screenId, name)` | Fuzzy search component by name (e.g. "Button", "Card") — find repeated patterns |
| `mcp__momorph__query_by_type(fileKey, screenId, type)` | All nodes of a type (e.g. `TEXT` to gather fonts to load) |
| `mcp__momorph__get_figma_image(fileKey, screenId, nodeId, format)` | **ONLY for fallback case**: a node named `mm_media_*` with NO row in `assets.md` (file not yet uploaded to Figma cloud). `format` = `'svg'` for icons, `'png'` for raster. Save the file to `{project_assets_out}/` named `{slug-from-node-name-strip-mm_media_}.{ext}`. |

**DO NOT call** `get_overview` (already embedded), `get_media_files` (orchestrator already handled it).
**DO NOT call** `get_figma_image` outside the fallback case above (Figma rate limits are strict). DO NOT use it for preview/screenshot reference.

## Code procedure

1. Read the embedded slim subtree → shape the layout + identify media nodes (`mm_media_*`).
2. Recurse the tree:
   - Media node (`mm_media_*`) → look up `assets.md` for the path:
     - **Raster (png/jpg/webp)** → emit `<img>` / `next/image` / native `Image` element.
     - **SVG icon (web stack)** → read the SVG file content with the `Read` tool → inline into JSX → replace solid fill/stroke with `currentColor` → wrap in a component (see rule 2a in `code-rules.md`). Set `color` from the icon node's Figma `fills` (query `get_node` to get the color).
     - **SVG (mobile stack)** → use `react-native-svg` / `flutter_svg` / `Image.template` with a color prop from the Figma fills.
   - **Fallback** — `mm_media_*` node has NO row in `assets.md` (file not yet uploaded to Figma cloud):
     - Call `mcp__momorph__get_figma_image(fileKey, screenId, nodeId, format='svg' for icons | 'png' for raster)` → receive URL/bytes.
     - Save the file to `{project_assets_out}/{slug-from-node-name-strip-mm_media_}.{ext}` (download the URL if a URL is returned, or write bytes directly). Use `bash curl` or the `Write` tool.
     - Code imports from `{code_path_prefix}/{slug-from-node-name-strip-mm_media_}.{ext}` (same convention).
     - Note in the report: "Fallback get_figma_image: [list of nodeIds]" so the orchestrator is aware.
   - STOP recursion into children of media nodes.
   - FRAME with children → wrapper element + recurse.
   - TEXT → text element with `characters` from `get_node` + style.
3. For every node needing styles → `mcp__momorph__get_node(fileKey, screenId, nodeId)` → apply real values. For SVG icons, also query the node's `fills` to obtain the color and apply it on the parent (CSS `color`).
4. Slim subtree not deep enough → `mcp__momorph__query_section` to zoom.
5. Confused about a node's role (e.g. background vs overlay?) → `mcp__momorph__get_node_context`.
6. Run compile/lint per project — never leave files with syntax errors.

## Required rules

Read + follow: `.claude/skills/momorph-implement-design/references/code-rules.md`

Summary:
- Each element has a **comment marker** immediately before (universal, NO runtime leak): `// mm:{nodeId}` (every stack) or `{/* mm:{nodeId} */}` (JSX inline). DO NOT use `data-mm-id`/`accessibilityLabel`.
- Raster media → `<img>`/`Image`. **SVG media (web) → inline JSX + `currentColor` + parent `color` from Figma `fills`** (rule 2a — DO NOT use `<img>` for SVG icons).
- Wrapper around an asset must match its shape (radius/shadow follow the asset).
- TEXT keeps `characters` exactly, DO NOT translate.
- Root frame defaults to FILL (full width), do not fix design width.

## ⚠️ Anti-pitfall checklist (REQUIRED before reporting DONE)

These 5 errors account for 90% of failures. **MUST** verify all 5 before returning DONE:

1. **FONT** — every TEXT node has been queried with `get_node` for real `fontFamily`/`fontSize`/`fontWeight`/`lineHeight`/`letterSpacing` + font loaded via the proper loader (next/font, expo-font, pubspec, ...)? DO NOT leave defaults.
2. **WRAPPER RADIUS** — every wrapper around media (with shadow/border/background) has `border-radius` matching the inner asset? When unsure → `get_node_context(asset_nodeId)` to compare `cornerRadius` of parent vs asset.
3. **ALIGNMENT** — every auto-layout FRAME has been queried for `primaryAxisAlignItems` + `counterAxisAlignItems` → applied `justify-content`/`align-items` correctly. TEXT with `textAlignHorizontal` → applied `text-align`. DO NOT default to left.
4. **FILL VIEWPORT + CONTAINERED LAYOUT** — two sides of the same rule:
   (a) Root section **DOES NOT** hardcode `width: {designWidth}px` → use `width: 100%` so the background fills the viewport.
   (b) If a section contains a FIXED-width node narrower than the artboard and centered (parent `counterAxisAlignItems: CENTER`) → that's a **content container** → use `max-width: Npx + margin: 0 auto + width: 100%` (NOT a rigid `width: Npx`).
   Common bug: using `width: Npx` for a content container → content sticks to the left / off-center. See rule 3 + Containered layout in `code-rules.md`.
5. **ICON COLOR** — every SVG icon (`mm_media_*`, file `.svg`) on web stack has been:
   (a) inlined as JSX (NOT `<img>`),
   (b) solid `fill`/`stroke` replaced with `currentColor` (preserve `none`, gradients, multi-color),
   (c) `color: <hex>` from Figma `fills` (query `get_node` of the icon node or the closest ancestor with a fill) applied on the parent.
   → Default white / wrong color = FAIL. See rule 2a in `code-rules.md`.

In the report write: `Anti-pitfall: ✓ font ✓ radius ✓ alignment ✓ fill-viewport+container ✓ icon-color` (or note clearly which item is not OK).

## Output report

- Files created: [paths]
- Component tree: [brief summary]
- Props/data interface: [if external data is needed]
- Anti-pitfall: [✓ font ✓ radius ✓ alignment ✓ fill-viewport+container ✓ icon-color]
- MCP calls: [number of calls per tool — for performance debugging]
- Blockers: [if any]

**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
**Summary:** [1-2 sentences]

## MoMorph refs:
- {screen name}: https://momorph.ai/files/{fileKey}/screens/{screenId}
- Clarifications: {plan_dir}/clarifications.md (if any)

## Work context
Work context: {project_root}
Reports: {plan_dir}/reports/
Plans: {plan_dir}/
```

## Guidance for orchestrator when spawning

- **Same message:** N `Agent` calls in parallel with the asset_downloader bg job.
- **Embed the slim section subtree:** before spawning, extract the section branch from the `get_overview` output (Phase 1) → paste a compact JSON into the prompt → subagent saves at least 1 first MCP call.
- **Resource:** N ≤ 6 per batch.
- **Status handling:** see "Subagent status" in SKILL.md.
