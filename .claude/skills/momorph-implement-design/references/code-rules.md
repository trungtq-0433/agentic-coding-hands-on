# Code Rules (orchestrator + subagent)

Mandatory rules when generating UI code from a Figma node tree. Applies to web (React/Vue/Next/Svelte) and mobile (React Native, Flutter, SwiftUI, Compose).

## 1. 1-1 mapping node → element + comment marker

Each Figma `id` → one element, with a `mm:{nodeId}` comment immediately before the element. **Universal across all stacks** — does not leak into HTML/accessibility tree, does not pollute production output.

| Stack | Comment syntax |
|-------|----------------|
| TS/JS/Vue/Svelte/RN | `// mm:{nodeId}` (line above element) or `{/* mm:{nodeId} */}` (JSX inline) |
| Flutter (Dart) | `// mm:{nodeId}` |
| SwiftUI / Compose | `// mm:{nodeId}` |

**DO NOT use** `data-mm-id="..."` (leaks into HTML) or `accessibilityLabel="mm:..."` (leaks to screen readers, harms a11y).

`validate_coverage.py` scans `// mm:...`, `{/* mm:... */}`, `/* mm:... */`, and `<!-- mm:... -->`.

## 2. Media node (asset)

A node whose name contains `mm_media_` (case-insensitive) is an asset.

- Look up `data/assets.md` → get the file path → render the asset element.
- DO NOT recurse into the children of a media node.
- The path in `assets.md` is a **plan** — the file may still be downloading; just use the path, no need to check existence.
- **Dedup by filename**: multiple `nodeId`s in `assets.md` may point to the same file (because they share the same `mm_media_*` name). Use the mapped path exactly — do not invent another name.
- **`get_figma_image` fallback (the ONLY allowed call site)**: if a node has the name `mm_media_*` BUT has no row in `assets.md` (because `get_media_files` lacked a URL — file not yet uploaded to Figma cloud), call `mcp__momorph__get_figma_image(fileKey, screenId, nodeId, format='svg' for icons | 'png' for raster)` to pull it directly.
   - Save the file to the project assets dir (the same path the orchestrator set up, usually passed via prompt as `{project_assets_out}`).
   - Name the file by convention: `{slug_from_node_name_strip_mm_media_}.{ext}` (same as `asset_downloader.py`).
   - DO NOT call `get_figma_image` for any other purpose (preview, full-screen screenshot, reference look-up, etc.) — Figma rate limits are strict.

## 2a. ⚠️ SVG icon → inline component + currentColor (web)

Figma's exported SVGs usually keep `fill`/`stroke` hardcoded (e.g. `fill="white"`). Rendering with `<img src="...svg">` **locks the color**, CSS can't change it → the icon shows the wrong design color (e.g. white when the design is blue).

**Rule for web stack (React/Next/Vue/Svelte):**

1. **Inline SVG content into JSX/template** (read the SVG file with the `Read` tool, paste content into the component) — DO NOT use `<img>` for SVG icons.
2. **Replace solid fill/stroke with `currentColor`** in the SVG content — preserve `fill="none"`, `fill="url(#...)"` (gradients), and multi-color icons (≥ 2 distinct colors → keep brand palette).
3. **Take the actual color from Figma `fills`** of the icon node (or the closest meaningful ancestor) via `mcp__momorph__get_node(nodeId)` → apply `color: <hex>` on the parent element (or inline style/className).
4. **Extract a reusable component** if the icon is used ≥ 2 times (filename: `icon-{name}.tsx`, `kebab-case`).

```tsx
// ❌ WRONG — color is baked into the file, CSS can't override
{/* mm:1:5 */}
<img src="/home/icon-home.svg" alt="" />

// ✅ RIGHT — inline SVG + currentColor + parent sets color from Figma fills
// icons/icon-home.tsx
export function IconHome(props: React.SVGProps<SVGSVGElement>) {
  return (
    /* mm:1:5 */
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M..." fill="currentColor" />
    </svg>
  );
}

// Usage — color taken from Figma fills of node 1:5 (e.g. #2563EB)
<IconHome style={{ color: '#2563EB' }} />
// or via Tailwind/className: <IconHome className="text-blue-600" />
```

**Multi-color icon** (logo, illustration ≥ 2 colors): DO NOT convert to currentColor — keep the original palette. Still inline so CSS can override portions if needed (via `[data-part="..."]`).

**Mobile stacks:**
- React Native: `react-native-svg` + `<Svg>...<Path fill={color}/>...</Svg>` (inline JSX, color prop from Figma fills).
- Flutter: `flutter_svg` + `colorFilter: ColorFilter.mode(color, BlendMode.srcIn)` for mono icons.
- SwiftUI: `Image(systemName)` + `.foregroundColor()`, or SVG → SF Symbol; for SVG asset use `Image("name").renderingMode(.template).foregroundColor(color)`.
- Compose: `Icon(painterResource(id), tint = color)`.

## 2b. ⚠️ Wrapper SHAPE must match the asset (easy to miss)

When a PARENT node has effects (`box-shadow`, `border`, `background`, `outline`) wrapping an asset with `border-radius`:

The wrapper **MUST** carry the same `border-radius` (and `overflow: hidden` if needed) — otherwise the wrapper effect leaks a rectangle while the rounded asset sits inside → it looks off-design.

```tsx
// ❌ WRONG — wrapper shadow exposes rectangle, doesn't follow asset radius
// mm:1:1
<div style={{ boxShadow: '0 4px 12px rgba(0,0,0,.1)' }}>
  {/* mm:1:2 */}
  <img src="..." style={{ borderRadius: 16 }} />
</div>

// ✅ RIGHT — wrapper matches asset radius → shadow follows the right shape
// mm:1:1
<div style={{
  boxShadow: '0 4px 12px rgba(0,0,0,.1)',
  borderRadius: 16,             // matches asset
  // overflow: 'hidden' if you need to clip content
}}>
  {/* mm:1:2 */}
  <img src="..." style={{ borderRadius: 16 }} />
</div>
```

When unsure → query `mcp__momorph__get_node_context(nodeId)` to view parent + asset together and reconcile their `cornerRadius`.

## 3. Style mapping (auto-layout + alignment)

Get correct styles from `mcp__momorph__get_node(fileKey, screenId, nodeId)` — DO NOT guess.

**Auto-layout → flex:**
- `layoutMode: HORIZONTAL` → row, `VERTICAL` → column. Web `display: flex`. RN/Flutter `Row`/`Column`. SwiftUI `HStack`/`VStack`. Compose `Row {}`/`Column {}`.
- `itemSpacing` → `gap` (web/RN) / `spacing` (SwiftUI/Compose) / `SizedBox` between children (Flutter).
- `paddingLeft/Right/Top/Bottom` → 4 separate side paddings.

**⚠️ Alignment — MUST query both axes:**
- `primaryAxisAlignItems`: `MIN` | `CENTER` | `MAX` | `SPACE_BETWEEN` → `justify-content: flex-start | center | flex-end | space-between`.
- `counterAxisAlignItems`: `MIN` | `CENTER` | `MAX` | `BASELINE` → `align-items: flex-start | center | flex-end | baseline`.
- TEXT with `textAlignHorizontal: LEFT | CENTER | RIGHT | JUSTIFIED` → `text-align`.
- DO NOT default to left/start.

**Sizing:**
- Root frame defaults to FILL (`width: 100%`), do not fix `{designWidth}px`.
- Fix `width`/`height` only when `layoutSizingHorizontal: FIXED` / `layoutSizingVertical: FIXED`.

**⚠️ Containered layout (a frequent web mistake)** — common pattern: full-bleed artboard (e.g. 1440px) holding a narrower FIXED content frame (e.g. 1200px) centered inside. Mechanically applying "FIXED → `width: Npx`" yields a 1200px block stuck to the left edge → content overflow / off-center.

**How to detect** a content container (heuristic):
- Node has `layoutSizingHorizontal: FIXED` with width < artboard width AND
- Parent has `counterAxisAlignItems: CENTER` (or the node is visually centered in the artboard) AND
- Node wraps a major content region (section / page main).

**Code pattern (web):**
```tsx
// ❌ WRONG — fixed width doesn't auto-center, sticks left
{/* mm:1:2 */}
<div style={{ width: 1200 }}> ... </div>

// ✅ RIGHT — max-width + auto margin = centered container
{/* mm:1:2 */}
<div style={{ maxWidth: 1200, marginInline: 'auto', width: '100%' }}> ... </div>
// Tailwind equivalent: `mx-auto w-full max-w-[1200px]`
```

**When NOT to apply the container pattern:** the FIXED node is a card/button/input/icon (not a wrapper section) → keep `width: Npx`. The container pattern only applies to a FIXED node **wrapping a major layout region** centered inside a wider parent.

**Mobile (RN/Flutter):** containered layout is rare since viewport ≈ design width. If a tablet/landscape design uses this pattern, use `maxWidth` + center alignment equivalents.

## 4. Text + font (query all fields)

- `characters` field → text content. DO NOT translate / edit / fabricate.
- TEXT nodes MUST query 6 fields via `get_node`:
   - `fontFamily` (e.g. `"Inter"`)
   - `fontWeight` (`400`/`600`/`700`...)
   - `fontSize` (e.g. `14`)
   - `lineHeight` (e.g. `{value: 24, unit: "PIXELS"}` or `{value: 1.5, unit: "PERCENT"}`)
   - `letterSpacing`
   - `textAlignHorizontal` (see rule 3)
- Load fonts properly via the appropriate loader:
   - Next.js: `next/font/google` or `next/font/local`
   - Other web: `@font-face` or CDN
   - RN: `expo-font`
   - Flutter: declare in `pubspec.yaml` + `fontFamily`
   - SwiftUI: `.font(.custom(...))`
   - Compose: `FontFamily(Font(R.font.xxx))`
- DO NOT inherit the default browser/OS font.

## 5. Reusable component

Same pattern (same type + same style signature) ≥ 2 times → extract a sub-component file.

## 6. Naming

- File:
   - JS/TS/Vue/Svelte: kebab-case (`.tsx`/`.vue`/`.svelte`)
   - Flutter: snake_case (`.dart`)
   - SwiftUI/Kotlin: PascalCase (`.swift`/`.kt`)
- Component / class name: PascalCase across all stacks.

## 7. Project conventions

Read `./docs/code-standards.md` and existing components to follow established patterns (import paths, styling system, state pattern). DO NOT introduce new patterns.

## Figma → Code mapping (quick reference)

| Figma | Web | React Native | Flutter | SwiftUI | Compose |
|-------|-----|--------------|---------|---------|---------|
| FRAME row | `<div style={{display:'flex',flexDirection:'row'}}>` | `<View style={{flexDirection:'row'}}>` | `Row(children:[...])` | `HStack { ... }` | `Row { ... }` |
| FRAME column | `<div style={{display:'flex',flexDirection:'column'}}>` | `<View style={{flexDirection:'column'}}>` | `Column(...)` | `VStack { ... }` | `Column { ... }` |
| TEXT | `<span>`/`<p>`/`<h*>` | `<Text>` | `Text(...)` | `Text(...)` | `Text(...)` |
| RECTANGLE solid | `<div>` + bg | `<View>` + bg | `Container(decoration:...)` | `Rectangle().fill(...)` | `Box(modifier=Modifier.background(...))` |
| Media `mm_media_*` raster (png/jpg) | `<img>` / `next/image` | `<Image source={...} />` | `Image.asset(...)` | `Image(...)` | `Image(painter=...)` |
| Media `mm_media_*` SVG icon | inline `<svg>` + `currentColor` (rule 2a) | `react-native-svg` JSX + color prop | `flutter_svg` + colorFilter | `Image.renderingMode(.template)` + foregroundColor | `Icon(painter, tint=...)` |
| INSTANCE reusable | sub-component | sub-component | sub-widget | sub-view | sub-composable |
| padding/gap | `padding` / `gap` | `padding` / `gap` (RN ≥0.71) | `Padding`/`SizedBox` | `.padding()` / spacing | `Modifier.padding()` |
| cornerRadius | `border-radius` | `borderRadius` | `BorderRadius.circular(...)` | `.cornerRadius()` | `RoundedCornerShape` |
| effects DROP_SHADOW | `box-shadow` | `shadowColor`+`elevation` | `BoxShadow` | `.shadow()` | `Modifier.shadow()` |
