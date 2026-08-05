---
name: tkm:generate-slide
description: "Generate polished presentation slides from content or outline. Two modes: --html for modern scroll-snap HTML slides (12 style presets, opens in browser), or --sun/--pptx for Sun* brand-compliant PowerPoint decks (.pptx, optional --image mode). Use when user says 'tạo slide', 'làm presentation', 'gen deck', 'create slides', 'プレゼン作って', or provides an outline/markdown to turn into a deck. NOT for quick dev-internal explanations (use tkm:preview-output --slides)."
category: content
keywords: [slides, presentation, pptx, html, sun-asterisk, deck, generate, image-rich]
argument-hint: "<content|outline|*.pptx> [--html|--sun|--pptx] [--image]"
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
module: specialized-output
triggers: ["slides", "presentation", "deck", "tạo slide", "gen deck", "PPTX"]
---

# Generate Slide

Convert content, outlines, or markdown into polished presentation slides.

**Two output modes:**
- `--html` *(default)* — Self-contained HTML file, scroll-snap navigation, 12 style presets, opens directly in browser. Best for internal demos, stakeholder walkthroughs, developer-facing content.
- `--sun` / `--pptx` — Sun\* brand-compliant `.pptx` deck via pptxgenjs. 17 layout patterns (12 text-only + 5 image-rich), Sun Red palette, Noto Sans JP. Best for client deliverables, internal company decks.

**Sub-flags:**
- `--image` — *(PPTX mode only)* Generate image-rich slides with AI prompt placeholders for Gemini (Nano Banana) or ChatGPT (GPT Image). Each placeholder embeds the suggested prompt for copy-paste.
- `--from-pptx <file.pptx>` — Import existing PowerPoint, extract content, then re-style in either mode.

## Usage

```
/tkm:generate-slide "AI governance framework for 20 stakeholders" --sun
/tkm:generate-slide outline.md --html
/tkm:generate-slide outline.md --sun --image
/tkm:generate-slide --from-pptx old-deck.pptx --sun
/tkm:generate-slide "Takumi Kit overview for onboarding" --auto
```

## Intent Detection

| Input Pattern | Mode |
|---------------|------|
| `--sun` or `--pptx` | Sun* PPTX mode |
| Mentions Sun*, STVC, BrSE, client, khách hàng | Auto-select `--sun` |
| `--html` | HTML mode |
| Default / no flag | HTML mode |
| `--image`, "với hình ảnh minh hoạ", "image-rich", "add illustrations", "thêm hình ảnh" | Switch PPTX to image-rich mode |
| `--from-pptx <file>` | PPT import → then HTML or PPTX |
| `--auto` | Skip approval gates |

---

## Phase 0 — Mode Detection

1. Read the argument and detect mode (HTML or PPTX) from flags or context clues above.
2. If `--from-pptx` given: run **PPT Import** first (see section below), then continue to Phase 1 with the extracted content.
3. If no flag and audience context is ambiguous, default to `--html`.
4. If PPTX mode AND user mentions illustrations / `--image` → enable **Image-Rich Mode** (see section below).

---

## HTML Mode Workflow (`--html`)

### Phase 1 — Content Discovery

Read the user's content (markdown, outline, raw notes, or natural-language description). Map to slide roles:

| Content shape | Slide role |
|---------------|-----------|
| Document title | Title slide |
| Top-level `##` headings | Section divider |
| `###` sub-sections or numbered items | Body slides |
| Final "Q&A" / "Contact" / "Next steps" | Closing slide |

**Density rule:** If a section has >80 words or >5 bullets, plan to split it into 2 slides. Ask one clarifying question if intent is unclear, otherwise infer.

**One-shot discovery question (if content is sparse):**
> "Quick questions before I start: (1) Who's the audience? (2) What's the main message? (3) Any content I should avoid?"

### Phase 2 — Style Selection

Generate **3 single-slide HTML previews** — one from each theme group (dark / light / specialty). Use `viewport-base.css` + the chosen preset's color palette. Open the previews or describe them clearly, let user pick.

Skip this step if `--auto` flag is set — pick the most contextually appropriate preset automatically.

Load `references/style-presets.md` to select three preview candidates. Consider audience:
- Dev-focused / internal tech → Terminal Green (#10) or Neon Cyber (#9)
- Client-facing professional → Electric Studio (#2) or Swiss Modern (#11)
- Creative / product launch → Bold Signal (#1) or Creative Voltage (#3)
- Formal / editorial → Vintage Editorial (#8) or Paper & Ink (#12)

### Phase 3 — Generate HTML

Generate a **single self-contained HTML file** using:
- `references/html-template.md` — `SlidePresentation` class, base structure
- `references/viewport-base.css` — paste inline in `<style>` block
- `references/style-presets.md` — chosen preset's CSS variables
- `references/animation-patterns.md` — `.reveal` animations + optional effects

**Hard rules:**
- All sizing via `clamp()` — no fixed px for typography or spacing
- Negative CSS functions: `calc(-1 * clamp(...))` — never `-clamp(...)`
- Fonts: Fontshare or Google Fonts URLs only — **never** Inter, Roboto, Arial, system fonts
- Images: `max-height: min(50vh, 400px)` — never fill full slide
- `prefers-reduced-motion: reduce` — set `animation-duration: 0.01ms !important`
- Nav dots: always `innerHTML = ''` before building (prevents duplicate dots on re-open)
- Content density: title slides = 1 heading + 1 subtitle; content slides = max 4–6 bullets; grids = max 6 cards

### Phase 4 — Deliver HTML

Open the file in the user's browser or copy it to CWD. Brief the user on:
- File path and how to navigate (arrow keys / swipe)
- Slide count and structure
- Any placeholder content to fill in

**Optional (ask once):**
- Export to PDF? → run `scripts/export-to-pdf.sh`
- Inline edit mode? → enable `contenteditable` hotzone for live editing

---

## Sun* PPTX Mode Workflow (`--sun` / `--pptx`)

### Visual Quality — the bar to aim for

Full visual quality guide (typography scale, container sizing, icons, color discipline): `references/visual-quality-guide.md`

---

### Standard Deck Structure

Every Sun* deck has the same structural skeleton:

```
1. Cover slide                  (red background, title + presenter)
2. Table of Contents (TOC)      ← ALWAYS include, right after the cover
3. Section divider — Part 01    (red background, "PART 01" label)
4. ...body slides for Part 01...
5. Section divider — Part 02
6. ...body slides for Part 02...
7. (more sections)
8. Closing / Q&A slide          (red background, contact info)
```

#### Table of Contents slide — mandatory

The TOC slide goes **right after the cover slide** and lists every Part / section with its starting page number. Skip TOC only if the deck has fewer than 5 slides total.

Standard TOC layout: white background, title "Mục lục" / "目次" / "Contents" (match the deck's language), then a vertical list — each with a big red part number, the section title, and a small page-number reference on the right.

Use the bundled helper `makeTOC(sections, tocPageNum, tocTitle)` from `assets/helpers.js`:

```javascript
helpers.makeTOC([
  { num: "01", title: "Bối cảnh & Vấn đề", page: 3 },
  { num: "02", title: "Vai trò mới của bạn", page: 9 },
  { num: "03", title: "Case study", page: 17 },
], 2, "Mục lục");
```

#### Page numbering convention — count EVERY slide

- Cover = page 1 (white text on red bg, bottom-left)
- TOC = page 2 (full footer with page number)
- Section dividers = numbered (page number on red bg)
- Body slides = numbered (page number in bottom-left)
- Closing = numbered (page number on red bg)

**Do NOT skip any slide in the count.** Even though section dividers and cover have red backgrounds, they still get a page number — this matches how readers navigate.

#### Two-pass page numbering algorithm

The TOC must point to section divider slides. **Don't guess — use two passes:**

**Pass 1 (planning):** Build a flat list of every slide before writing pptxgenjs code. For each entry, note type (cover / toc / divider / body / closing) and section. Walk the list and record the 1-indexed position of each section's divider.

**Pass 2 (generation):** Now build the deck. Increment `pageNum` for EVERY slide. Pass `pageNum` to every helper. TOC receives the pre-computed positions from Pass 1.

```javascript
// Pass 1: lay out slide order
const slideOrder = [
  { type: "cover" },
  { type: "toc" },
  { type: "divider", section: "01", title: "First Section" },
  { type: "body", section: "01" },
  { type: "body", section: "01" },
  { type: "divider", section: "02", title: "Second Section" },
  { type: "body", section: "02" },
  { type: "closing" },
];

// Compute 1-indexed page of each divider
const sectionPages = {};
slideOrder.forEach((s, i) => {
  if (s.type === "divider") sectionPages[s.section] = i + 1;
});

// Pass 2: generate
let pageNum = 0;
pageNum++; helpers.makeCover(title, subtitle, presenter, pageNum);
pageNum++; helpers.makeTOC([
  { num: "01", title: "First Section",  page: sectionPages["01"] },
  { num: "02", title: "Second Section", page: sectionPages["02"] },
], pageNum, "Contents");
pageNum++; helpers.makeSectionDivider("01", "First Section", "subtitle", pageNum);
// ...etc
```

**Why two passes**: It's tempting to guess "section 02 starts around page 9", but content density shifts things by 1-2 slides and your TOC silently points wrong.

---

### Image-Rich Mode (`--image` option)

Full image-rich mode guide (aspect ratios, placeholder design, prompt template, brand imagery rules, palette heuristics, placement strategy, layout table): `references/image-rich-mode-guide.md`

Trigger: `--image`, "với hình ảnh minh hoạ", "image-rich", "add illustrations", "make it lively with visuals". Use `addImagePlaceholder()` helper from `assets/helpers.js`. Load the guide before Phase 2 (layout pick) when image-rich mode is active.

---

### Workflow

#### Phase 0 — Check Dependencies

```bash
echo "Node.js:     $(command -v node >/dev/null 2>&1 && node --version || echo 'MISSING')"
echo "pptxgenjs:   $(npm list -g --depth=0 2>/dev/null | grep -q pptxgenjs && echo 'installed' || echo 'MISSING')"
echo "LibreOffice: $(command -v soffice >/dev/null 2>&1 && echo 'installed' || echo 'MISSING (QA disabled)')"
echo "Poppler:     $(command -v pdftoppm >/dev/null 2>&1 && echo 'installed' || echo 'MISSING (QA disabled)')"
```

**If `pptxgenjs` is missing** — stop: "`pptxgenjs` is not installed. Run `tkm init --install-skills` to install, then retry."

**If `LibreOffice` or `Poppler` is missing** — continue without QA, use conservative defaults, warn user.

**If `Node.js` is missing** — stop: "Node.js not found. Install from https://nodejs.org and retry."

#### Phase 1 — Read Content

Map markdown sections → slide roles:

| Markdown shape | Slide role |
|---------------|------------|
| Document title | Cover slide |
| (auto-generated next) | **Table of Contents** (always include unless deck has <5 slides) |
| Top-level `##` headings | Section divider |
| `###` subsections or numbered items | Body slides |
| Final "Q&A" or "Contact" | Closing slide |

**Detect image-rich mode.** If the user's message contains `--image`, "với hình ảnh", "image-rich", "add illustrations", "thêm hình ảnh minh hoạ", or similar — switch to **image-rich mode**.

**Plan the TOC.** Before writing code, list sections (Part 01, Part 02…) and compute starting page numbers via the two-pass algorithm.

**Judge density per section.** If dense, plan to split across 2 body slides upfront.

**Respect placeholder content.** If markdown has `[X]`, `[link]`, `[tên project]`, preserve as-is.

**If image-rich, plan image placement.** Mark which slides get placeholders (1-2 per important slide; 0 for numerical/table slides). Content-driven, not a quota.

#### Phase 2 — Pick Layouts

Load `references/layouts.md`. For each body slide, pick the layout matching content shape — **vary across slides**, no two consecutive identical.

**Text-only mapping:**
- 3–5 enumerated points → Numbered points (#1)
- 2 things compared → Comparison columns 2 (#2)
- 3 parallel items → Comparison columns 3 (#3)
- 4 grid items → Card grid 2×2 (#4)
- Steps/process → Process flow (#5)
- Before/after metrics → Metrics table (#6)
- Problem/solution → Pain/Solution split (#7)
- Single big message → Hero callout (#8)
- Project metadata → Field grid (#9)
- 2 framed questions → Question cards (#10)
- Definition + key message → Definition slide (#11)
- Levels/tiers → Tier ladder (#12)

**Image-rich mapping (with `--image`):**
- Section opener → Hero image + text (#13)
- Concept with supporting visual → Side image + bullets (#14)
- Multiple examples shown visually → Image grid (#15)
- System / process diagram → Big centerpiece + annotations (#16)
- Quote / mission / dramatic moment → Image background + overlay text (#17)

#### Phase 3 — Generate PPTX

Create `generate.js` in a `.sun-slide-build/` directory inside CWD. Either:

**Option A (recommended):** Inline brand constants. See `references/examples.md` example #1.

**Option B:** `require()` the `assets/helpers.js` file. Cleaner for large decks.

Copy `assets/logo_sun.png` into the build dir.

**Critical pptxgenjs rules (from `assets/helpers.js`):**
- Hex colors: `"FF2200"` — **never** `"#FF2200"` (pptxgenjs corrupts files with `#`)
- Reused option objects: use factory functions `const makeShadow = () => ({...})` — pptxgenjs mutates in-place
- Unicode bullets: `bullet: { code: "25AA" }` — never `"• Item"` (creates double bullets)
- `breakLine: true` on every text run except the last in an array
- `margin: 0` on text boxes aligned with shapes
- CJK / Vietnamese text: `fontFace: "Noto Sans JP"`
- Footer y-coordinate: `7.05` — don't place content below `y = 7.0`
- Slide dimensions: `LAYOUT_WIDE` = 13.333" × 7.5" (16:9)
- Sun Red: `"FF2200"` — one accent element per body slide

Run:
```bash
cd .sun-slide-build && node generate.js
```

#### Phase 4 — Visual QA

If LibreOffice + Poppler available:
```bash
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 100 output.pdf slide
```

View each `slide-*.jpg` and check:
- **Text overflow** — any text cut off at container edges?
- **Under-filled cards** — 30%+ empty space below text? Scale font up 4-6pt and re-render.
- **Cramping** — slide feels busy? Consider splitting.
- **Tiny fonts** — body text 11-13pt inside a roomy card? Scale up.
- **Overlap** — cards / tables overlapping?
- **Footer collision** — content reaching below y=6.95?
- **Color overuse** — more than 2 prominent Sun Red elements? Neutralize extras.
- **Visual monotony** — 3 same-layout slides in a row? Redesign one.
- **Image placeholders** (image-rich mode): readable AI prompt? Aspect ratio close to 3:2/2:3/1:1? Dashed red border visible?

The first render almost always has 1-2 issues. Most common: under-filling. Fix by scaling up; re-render; deliver. One fix-and-verify cycle is usually enough.

If QA tools absent: use conservative defaults (50–60 words/slide, 12–13pt body, generous padding) and warn user.

#### Phase 5 — Deliver PPTX

```bash
cp output.pptx ../<MeaningfulName>.pptx
```

Brief user on:
- Total slide count
- Structure (cover, TOC, parts, body, closing)
- Any `[placeholder]` content to fill in
- **If image-rich**: how many image placeholders and where (e.g., "8 placeholders — 1 on cover, 1 per section divider, 2 on key concept slides"). Remind: each placeholder contains a prompt to copy into Gemini (Nano Banana) or ChatGPT (GPT Image), then paste the resulting image over the placeholder.

---

## PPT Import (`--from-pptx`)

Run the extractor script:
```bash
python3 <skill-path>/scripts/extract-pptx.py input.pptx extracted-content.md
```

If `python-pptx` missing:
```bash
~/.claude/skills/.venv/bin/pip install python-pptx
# or: pip install python-pptx
```

Review extracted content with user, confirm section mapping, then proceed to the chosen output mode (HTML or PPTX).

---

## Common Pitfalls Summary

| Issue | Fix |
|-------|-----|
| pptxgenjs color bug | `"FF2200"` not `"#FF2200"` |
| Negative CSS function | `calc(-1 * clamp(...))` not `-clamp(...)` |
| Double nav dots on re-open | `navDotsContainer.innerHTML = ''` before building |
| Generic AI fonts | Always Fontshare or Google Fonts — never Inter/Roboto/Arial |
| CJK/Vietnamese PPTX font | `fontFace: "Noto Sans JP"` |
| pptxgenjs object mutation | Factory fn `const makeOpts = () => ({...})` |
| Under-filled cards | Scale font 4-6pt up, or shrink container — don't leave 50% empty space |
| One font size everywhere | Scale to container — 18-20pt in large cards, 11-13pt in dense tables |
| Cramming "to honor source" | Split into 2 slides — Overview+Details, Concept+Examples, Problem+Solution |
| TOC pointing to wrong page | Use two-pass algorithm — plan slide order first, then generate |
| Red logo on red background | Use white text "Sun*" instead — never red on red |
| Footer position | y=7.05 max — don't place content below y=7.0 |
| Image prompt without hex codes | Always spell colors: "(#FF2200)" not "Sun Red" |
| Morbid imagery (graveyards, fire) | Use business metaphors (abandoned workshop, tilting tower) |
| Too many text elements in AI image | 0-2 text elements per image, each large enough to read |
| Dramatic style words in prompts | Use "editorial illustration", not "cinematic"/"dark fantasy" |

---

## Reference Files

Load on demand — only what the current phase needs:

| File | When to load |
|------|-------------|
| `references/style-presets.md` | HTML Phase 2 (style selection) |
| `references/viewport-base.css` | HTML Phase 3 (paste inline) |
| `references/html-template.md` | HTML Phase 3 (SlidePresentation class) |
| `references/animation-patterns.md` | HTML Phase 3 (animation CSS/JS) |
| `references/layouts.md` | PPTX Phase 2 (layout selection — 12 text + 5 image-rich) |
| `references/examples.md` | PPTX Phase 3 (code examples) |
| `assets/helpers.js` | PPTX Phase 3 (brand constants + helper fns — addFooter, addTitle, makeCover, makeSectionDivider, makeClosing, makeTOC, addImagePlaceholder, addKeyMessage) |
| `assets/sun-brand.md` | PPTX Phase 3 (when in doubt about colors/fonts) |
| `assets/sun_template.pptx` | PPTX reference template (6-slide official Sun* deck — inspect for layout decisions) |
| `assets/logo_sun.png` | PPTX Phase 3 (copy into build dir for body slide footers) |
| `scripts/extract-pptx.py` | PPT import mode only |
| `scripts/export-to-pdf.sh` | HTML PDF export (user-requested) |
