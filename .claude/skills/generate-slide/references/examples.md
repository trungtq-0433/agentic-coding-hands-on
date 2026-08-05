# Sun* Presentation — Worked Examples

End-to-end code snippets you can adapt. Each example assumes you've already set up `pptxgen`, the brand constants, and the helper functions (or inlined them).

## Table of contents

1. [Minimal full deck skeleton (5 slides)](#1-minimal-full-deck-skeleton)
2. [Cover slide variations](#2-cover-slide-variations)
3. [Section divider with rich subtitle](#3-section-divider)
4. [Body slide: 3 numbered points + key message](#4-body-slide-numbered-points)
5. [Body slide: comparison table with side panels](#5-body-slide-comparison-table)
6. [Closing slide with contact info](#6-closing-slide)
7. [Visual QA workflow](#7-visual-qa)

---

## 1. Minimal full deck skeleton

A complete generator producing 5 slides: cover → divider → 2 body → closing. Use this as a starting template for any new deck.

```javascript
const pptxgen = require("pptxgenjs");
const path = require("path");

// === Brand constants ===
const SUN_RED = "FF2200";
const SUN_DARK_RED = "AD0C00";
const SUN_GOLD = "B69256";
const LIGHT_GREY = "F7F7F7";
const BORDER_GREY = "DDDDDD";
const TEXT_DARK = "1A1A1A";
const TEXT_GREY = "666666";
const FONT_JP = "Noto Sans JP";
const FONT_EN = "Eina03";
const SLIDE_W = 13.333;
const SLIDE_H = 7.5;
const LOGO_PATH = path.join(__dirname, "logo_sun.png");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Sun* Inc.";
pres.title = "My Presentation";

// === Helpers (inlined for brevity — see helpers.js for full versions) ===
function addFooter(slide, pageNum) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.95, w: SLIDE_W, h: 0.025, fill: { color: SUN_RED }, line: { type: "none" } });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 6.98, w: SLIDE_W, h: 0.015, fill: { color: BORDER_GREY }, line: { type: "none" } });
  slide.addText(String(pageNum), { x: 0.4, y: 7.05, w: 0.6, h: 0.35, fontSize: 10, fontFace: FONT_EN, color: TEXT_GREY, align: "left", valign: "middle", margin: 0 });
  slide.addText("©2025 Sun* Inc.", { x: 5.5, y: 7.05, w: 2.5, h: 0.35, fontSize: 9, fontFace: FONT_EN, color: TEXT_GREY, align: "center", valign: "middle", margin: 0 });
  slide.addImage({ path: LOGO_PATH, x: 12.55, y: 7.0, w: 0.55, h: 0.27 });
}
function addTitle(slide, title) {
  slide.addText(title, { x: 0.5, y: 0.3, w: 12.3, h: 0.6, fontSize: 22, fontFace: FONT_JP, color: TEXT_DARK, bold: true, align: "left", valign: "middle", margin: 0 });
}

let pageNum = 0;

// === Slide 1: Cover ===
{
  const slide = pres.addSlide();
  slide.background = { color: SUN_RED };
  slide.addText("Sun*", { x: 0.7, y: 0.6, w: 2.5, h: 0.8, fontSize: 36, fontFace: FONT_EN, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });
  slide.addText("Your Big Title", { x: 0.7, y: 2.6, w: 11.9, h: 1.5, fontSize: 48, fontFace: FONT_JP, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });
  slide.addText("Subtitle goes here", { x: 0.7, y: 4.1, w: 11.9, h: 0.7, fontSize: 22, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });
  slide.addText("Author / team / date", { x: 0.7, y: 6.3, w: 11.9, h: 0.5, fontSize: 14, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });
}

// === Slide 2: Section divider ===
{
  pageNum++;
  const slide = pres.addSlide();
  slide.background = { color: SUN_RED };
  slide.addText("PART 01", { x: 0.7, y: 2.5, w: 11.9, h: 0.6, fontSize: 18, fontFace: FONT_EN, color: "FFFFFF", valign: "middle", margin: 0, charSpacing: 6 });
  slide.addText("Section title", { x: 0.7, y: 3.1, w: 11.9, h: 1.4, fontSize: 44, fontFace: FONT_JP, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });
  slide.addText("Section subtitle", { x: 0.7, y: 4.5, w: 11.9, h: 0.7, fontSize: 18, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });
  slide.addText("Sun*", { x: 11.5, y: 6.9, w: 1.5, h: 0.4, fontSize: 18, fontFace: FONT_EN, color: "FFFFFF", bold: true, align: "right", valign: "middle", margin: 0 });
}

// === Slide 3: Body — definition with key message ===
{
  pageNum++;
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addTitle(slide, "First content slide");
  // ... add your content here using one of the layouts from references/layouts.md
  addFooter(slide, pageNum);
}

// === Slide 4: Body — comparison ===
{
  pageNum++;
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addTitle(slide, "Second content slide");
  // ...
  addFooter(slide, pageNum);
}

// === Slide 5: Closing ===
{
  pageNum++;
  const slide = pres.addSlide();
  slide.background = { color: SUN_RED };
  slide.addText("Sun*", { x: 0.7, y: 0.6, w: 2.5, h: 0.8, fontSize: 36, fontFace: FONT_EN, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });
  slide.addText("Q&A & Contact", { x: 0.7, y: 1.8, w: 11.9, h: 1.0, fontSize: 44, fontFace: FONT_JP, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });
  slide.addText("contact@sun-asterisk.com", { x: 0.7, y: 4.0, w: 11.9, h: 0.5, fontSize: 18, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });
  slide.addText("©2025 Sun* Inc.", { x: 10.5, y: 7.1, w: 2.5, h: 0.3, fontSize: 9, fontFace: FONT_EN, color: "FFFFFF", align: "right", valign: "middle", margin: 0 });
}

pres.writeFile({ fileName: "output.pptx" }).then(() => {
  console.log(`Saved ${pageNum + 1} slides to ./output.pptx`);
});
```

---

## 2. Cover slide variations

The standard cover is white text on red background. For variations:

**With a hero subtitle line in italics:**
```javascript
slide.addText('"Optional tagline in italic"', {
  x: 0.7, y: 5.0, w: 11.9, h: 0.6,
  fontSize: 20, fontFace: FONT_JP, color: "FFFFFF",
  italic: true, valign: "middle", margin: 0,
});
```

**For a bilingual cover (e.g., Japanese client deck):**
```javascript
// Japanese title large
slide.addText("日本語タイトル", {
  x: 0.7, y: 2.4, w: 11.9, h: 1.0,
  fontSize: 40, fontFace: FONT_JP, color: "FFFFFF",
  bold: true, valign: "middle", margin: 0,
});
// English subtitle below
slide.addText("English Subtitle", {
  x: 0.7, y: 3.5, w: 11.9, h: 0.8,
  fontSize: 28, fontFace: FONT_EN, color: "FFFFFF",
  valign: "middle", margin: 0,
});
```

**With a topical emoji at large scale**: For a more playful cover (e.g., a launch announcement, a celebration deck), add a single big emoji at one corner:
```javascript
slide.addText("🚀", {
  x: 11.0, y: 1.0, w: 2.0, h: 2.0,
  fontSize: 120, valign: "middle", align: "center", margin: 0,
});
```

---

## 3. Section divider

Three-line variant for richer transitions (label + title + brief context):

```javascript
const slide = pres.addSlide();
slide.background = { color: SUN_RED };

// PART label (chunky letter spacing for design feel)
slide.addText("PART 02", {
  x: 0.7, y: 2.3, w: 11.9, h: 0.6,
  fontSize: 18, fontFace: FONT_EN, color: "FFFFFF",
  valign: "middle", margin: 0, charSpacing: 6,
});

// Big title
slide.addText("Big section title here", {
  x: 0.7, y: 2.95, w: 11.9, h: 1.3,
  fontSize: 44, fontFace: FONT_JP, color: "FFFFFF",
  bold: true, valign: "middle", margin: 0,
});

// Subtitle (longer context line)
slide.addText("Brief context for this section — what's coming next", {
  x: 0.7, y: 4.35, w: 11.9, h: 0.6,
  fontSize: 18, fontFace: FONT_JP, color: "FFFFFF",
  valign: "middle", margin: 0,
});

// Sun* mark bottom-right
slide.addText("Sun*", {
  x: 11.5, y: 6.9, w: 1.5, h: 0.4,
  fontSize: 18, fontFace: FONT_EN, color: "FFFFFF",
  bold: true, align: "right", valign: "middle", margin: 0,
});
```

---

## 4. Body slide: numbered points

A complete body slide with 3 numbered points on the left and a key message callout on the right. Combines layout #1 and #11 from the layout library.

```javascript
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };
addTitle(slide, "Slide title here");

// Left: 3 numbered points
const points = [
  { header: "First key idea", body: "Brief description supporting this idea." },
  { header: "Second key idea", body: "Brief description supporting this idea." },
  { header: "Third key idea", body: "Brief description supporting this idea." },
];
points.forEach((p, i) => {
  const y = 1.45 + i * 1.4;
  slide.addShape(pres.shapes.OVAL, { x: 0.7, y, w: 0.6, h: 0.6, fill: { color: SUN_RED }, line: { type: "none" } });
  slide.addText(String(i + 1), { x: 0.7, y, w: 0.6, h: 0.6, fontSize: 22, fontFace: FONT_EN, color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
  slide.addText(p.header, { x: 1.5, y: y - 0.05, w: 6.5, h: 0.45, fontSize: 17, fontFace: FONT_JP, color: TEXT_DARK, bold: true, valign: "middle", margin: 0 });
  slide.addText(p.body, { x: 1.5, y: y + 0.45, w: 6.5, h: 0.85, fontSize: 13, fontFace: FONT_JP, color: TEXT_GREY, valign: "top", margin: 0 });
});

// Right: key message
slide.addShape(pres.shapes.RECTANGLE, { x: 8.6, y: 1.45, w: 4.2, h: 4.0, fill: { color: LIGHT_GREY }, line: { type: "none" } });
slide.addShape(pres.shapes.RECTANGLE, { x: 8.6, y: 1.45, w: 0.08, h: 4.0, fill: { color: SUN_RED }, line: { type: "none" } });
slide.addText("💡 KEY MESSAGE", { x: 8.85, y: 1.65, w: 3.8, h: 0.4, fontSize: 11, fontFace: FONT_EN, color: SUN_RED, bold: true, valign: "middle", margin: 0, charSpacing: 4 });
slide.addText('"Your one-line takeaway that the audience should remember."', {
  x: 8.85, y: 2.1, w: 3.8, h: 3.2,
  fontSize: 18, fontFace: FONT_JP, color: TEXT_DARK,
  italic: true, valign: "top", margin: 0,
});

addFooter(slide, pageNum);
```

---

## 5. Body slide: comparison table

A "Before vs After" / "Today vs Tomorrow" style table, with a side panel of supporting context.

```javascript
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };
addTitle(slide, "Comparison slide title");

// Main table (left ~60%)
const tableData = [
  [
    { text: "", options: { fill: { color: LIGHT_GREY }, fontSize: 11, fontFace: FONT_JP } },
    { text: "Today", options: { bold: true, color: "FFFFFF", fill: { color: TEXT_GREY }, fontSize: 13, fontFace: FONT_JP, align: "center", valign: "middle" } },
    { text: "Tomorrow", options: { bold: true, color: "FFFFFF", fill: { color: SUN_RED }, fontSize: 13, fontFace: FONT_JP, align: "center", valign: "middle" } },
  ],
  [
    { text: "Dimension A", options: { bold: true, fontSize: 11, fontFace: FONT_JP, valign: "middle" } },
    { text: "Current state description", options: { fontSize: 10, fontFace: FONT_JP, valign: "middle" } },
    { text: "Future state description", options: { fontSize: 10, fontFace: FONT_JP, valign: "middle" } },
  ],
  // ... more rows
];

slide.addTable(tableData, {
  x: 0.5, y: 1.3, w: 8.0,
  colW: [1.7, 2.8, 3.5],
  rowH: 0.55,
  border: { type: "solid", pt: 0.5, color: BORDER_GREY },
});

// Right panel: "What's new" (top, light grey)
slide.addShape(pres.shapes.RECTANGLE, { x: 8.85, y: 1.3, w: 4.0, h: 2.3, fill: { color: LIGHT_GREY }, line: { type: "none" } });
slide.addShape(pres.shapes.RECTANGLE, { x: 8.85, y: 1.3, w: 0.08, h: 2.3, fill: { color: SUN_RED }, line: { type: "none" } });
slide.addText("✨ WHAT'S NEW", { x: 9.05, y: 1.45, w: 3.7, h: 0.35, fontSize: 11, fontFace: FONT_EN, color: SUN_RED, bold: true, valign: "middle", margin: 0, charSpacing: 2 });
slide.addText([
  { text: "First new capability", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Second new capability", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Third new capability", options: { bullet: { code: "25AA" } } },
], {
  x: 9.05, y: 1.85, w: 3.65, h: 1.65,
  fontSize: 10, fontFace: FONT_JP, color: TEXT_DARK,
  valign: "top", margin: 0, paraSpaceAfter: 4,
});

// Right panel: "What to watch" (bottom, red-tinted — for caveats / risks)
slide.addShape(pres.shapes.RECTANGLE, { x: 8.85, y: 3.75, w: 4.0, h: 1.5, fill: { color: "FFEEEC" }, line: { type: "none" } });
slide.addShape(pres.shapes.RECTANGLE, { x: 8.85, y: 3.75, w: 0.08, h: 1.5, fill: { color: SUN_RED }, line: { type: "none" } });
slide.addText("⚠  WATCH OUT", { x: 9.05, y: 3.9, w: 3.7, h: 0.35, fontSize: 11, fontFace: FONT_EN, color: SUN_RED, bold: true, valign: "middle", margin: 0, charSpacing: 2 });
slide.addText("The main pitfall to avoid in this transition", {
  x: 9.05, y: 4.3, w: 3.65, h: 0.85,
  fontSize: 11, fontFace: FONT_JP, color: TEXT_DARK,
  valign: "top", margin: 0,
});

addFooter(slide, pageNum);
```

---

## 6. Closing slide

A red-background "Q&A & Contact" with a 2-column information layout (documents on the left, contacts on the right), and a final key message at the bottom.

```javascript
const slide = pres.addSlide();
slide.background = { color: SUN_RED };

// Top: Sun* mark
slide.addText("Sun*", { x: 0.7, y: 0.6, w: 2.5, h: 0.8, fontSize: 36, fontFace: FONT_EN, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });

// Big title + subtitle
slide.addText("Q&A and Contact", { x: 0.7, y: 1.8, w: 11.9, h: 1.0, fontSize: 44, fontFace: FONT_JP, color: "FFFFFF", bold: true, valign: "middle", margin: 0 });
slide.addText("Your questions — and how we keep the conversation going", { x: 0.7, y: 2.85, w: 11.9, h: 0.5, fontSize: 18, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });

// Left column: documents
slide.addText("📚 RESOURCES", { x: 0.7, y: 3.7, w: 6.0, h: 0.35, fontSize: 11, fontFace: FONT_EN, color: "FFFFFF", bold: true, valign: "middle", margin: 0, charSpacing: 3 });
slide.addText([
  { text: "Document one · [link]", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Document two · [link]", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Document three · [link]", options: { bullet: { code: "25AA" } } },
], {
  x: 0.7, y: 4.05, w: 6.0, h: 1.6,
  fontSize: 12, fontFace: FONT_JP, color: "FFFFFF",
  valign: "top", margin: 0, paraSpaceAfter: 4,
});

// Right column: contact + next event
slide.addText("📨 CONTACT", { x: 7.0, y: 3.7, w: 6.0, h: 0.35, fontSize: 11, fontFace: FONT_EN, color: "FFFFFF", bold: true, valign: "middle", margin: 0, charSpacing: 3 });
slide.addText("[Email / Slack channel / contact person]", { x: 7.0, y: 4.05, w: 6.0, h: 0.5, fontSize: 13, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });

slide.addText("📅 WHAT'S NEXT", { x: 7.0, y: 4.75, w: 6.0, h: 0.35, fontSize: 11, fontFace: FONT_EN, color: "FFFFFF", bold: true, valign: "middle", margin: 0, charSpacing: 3 });
slide.addText("[Workshop / Office hour / Next event]", { x: 7.0, y: 5.1, w: 6.0, h: 0.5, fontSize: 13, fontFace: FONT_JP, color: "FFFFFF", valign: "middle", margin: 0 });

// Bottom: final key message
slide.addText('"Final takeaway message in italic, bold."', {
  x: 0.7, y: 6.0, w: 11.9, h: 0.85,
  fontSize: 14, fontFace: FONT_JP, color: "FFFFFF",
  italic: true, bold: true, valign: "top", margin: 0,
});

// Bottom-right copyright
slide.addText("©2025 Sun* Inc.", { x: 10.5, y: 7.1, w: 2.5, h: 0.3, fontSize: 9, fontFace: FONT_EN, color: "FFFFFF", align: "right", valign: "middle", margin: 0 });
```

---

## 7. Visual QA

After your generator runs, **always** convert to PDF and inspect each slide. Default font rendering, text overflow, and shape overlap are easy to miss when reading code.

```bash
# Run from inside your build directory (e.g. ./.sun-presentation-build)

# Convert to PDF
python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx

# Render each page to JPG (rm clears stale images from prior runs)
rm -f slide-*.jpg
pdftoppm -jpeg -r 100 output.pdf slide

# List the resulting files
ls slide-*.jpg
```

Then `view` each `slide-NN.jpg` and check for:
- Text overflowing its container (text cut off at edges)
- Cards or tables overlapping
- Inconsistent alignment between rows
- Sun Red used too heavily on one slide (more than 2 prominent uses)
- Footer collision with content above
- A slide that looks cramped or text-heavy — consider splitting it

For a 30+ slide deck, focus QA on the slides that have dense layouts (tables, multi-card grids). The simple title-only layouts rarely have issues.

After fixing any issues, re-render and re-inspect only the affected slides. Don't loop forever on cosmetic nudges — the goal is "no user-visible defects", not pixel perfection.
