# Sun* Slide Layout Library

A library of proven slide layouts for Sun*-branded presentations. Match each content shape to a layout — varying layouts across slides creates the visual rhythm that distinguishes a polished deck from a forgettable one.

## How to use this file

Each layout entry has:
- **When to use it** — the content shape it fits
- **Visual sketch** — quick mental picture
- **Code snippet** — drop into your generator, adapt dimensions and content

Coordinates assume `LAYOUT_WIDE` (13.333 × 7.5 inches). Constants like `SUN_RED`, `LIGHT_GREY`, `FONT_JP` are from `assets/helpers.js`.

## A note about icons & emoji

Slides feel more alive when you sprinkle in icons or emoji thoughtfully. Use them to:
- Reinforce category meaning (✓ for success, ⚠ for warnings, ★ for tiers, → for flow)
- Replace plain bullet points with topical glyphs (📊 for data, 🎯 for goals, 🚀 for launches, 💡 for ideas, 🔧 for tools, 🌍 for global)
- Add personality to numbered points or section headers

Two ways to add them:

**Inline emoji** — easiest, render directly in text:
```javascript
slide.addText("🚀 Launch the product", { ... });
slide.addText([
  { text: "🎯 ", options: { fontSize: 18 } },
  { text: "Strategic priority", options: { fontSize: 14, bold: true } },
], { ... });
```

**Symbol characters from `pres.shapes` or unicode** — used for arrows, checks, etc.:
```javascript
slide.addText("→", { fontSize: 24, color: SUN_RED, bold: true, ... });
slide.addText("✓", { fontSize: 18, color: "FFFFFF", bold: true, ... });
```

Don't go overboard — 1-3 icons per slide is plenty. A slide drowning in emoji feels juvenile.

## Table of contents

**Text-only layouts (always available):**

1. [Numbered points (3-5 items)](#1-numbered-points)
2. [Comparison columns (2 columns)](#2-comparison-columns-2)
3. [Comparison columns (3 columns)](#3-comparison-columns-3)
4. [Card grid (2×2)](#4-card-grid-2x2)
5. [Process flow (horizontal)](#5-process-flow-horizontal)
6. [Metrics table (Before / After / Δ)](#6-metrics-table-before-after-delta)
7. [Pain / Solution split](#7-pain-solution-split)
8. [Hero callout (single big message)](#8-hero-callout)
9. [Field grid (project info / metadata)](#9-field-grid)
10. [Question cards (Q1 / Q2)](#10-question-cards)
11. [Definition slide (3 points + side callout)](#11-definition-slide)
12. [Tier ladder (1, 2, 3 stars)](#12-tier-ladder)

**Image-rich layouts (used with `--image` mode):**

13. [Hero image + headline + paragraph](#13-hero-image--headline--paragraph)
14. [Side image + bullets](#14-side-image--bullets)
15. [Image grid (2×2 or 1×3)](#15-image-grid-2x2-or-1x3)
16. [Big centerpiece + annotations](#16-big-centerpiece--annotations)
17. [Image background + overlay text](#17-image-background--overlay-text)

## Right-sizing typography per layout

This is a reference for picking font sizes that fill containers gracefully. **Default to the higher end** of each range; drop to the lower end only when content is genuinely dense or the container is small.

| Layout | Card / cell size | Card header | Body text | Big visual |
|--------|------------------|-------------|-----------|------------|
| Numbered points (3-4 items) | full-width row | 22pt bold | 16-18pt | circle 28pt |
| Numbered points (5 items, compact) | full-width row | 18pt bold | 14-15pt | circle 22pt |
| Comparison cols (2) | 6" × 4.7" each | 22pt bold | 18-20pt | — |
| Comparison cols (3) | 4" × 5.4" each | 20pt bold | 14-16pt | — |
| Card grid (2×2) | 6" × 2.5" each | 20pt bold | 14-16pt | icon 40pt |
| Process flow (5 boxes) | 2.4" × 0.95" each | — | 11-12pt | step number 14pt |
| Metrics table | rowH 0.55-0.65" | header 13pt | 11-13pt | big number 24pt |
| Pain/Solution split | 4" × 4" + 8" × 4" | 14pt UPPERCASE | 14-16pt | — |
| Hero callout | full slide | — | 24-32pt | quote glyph 80pt |
| Field grid | 6" × 0.95" each | 11pt UPPERCASE | 14-16pt | — |
| Question cards (Q1/Q2) | 6" × 3.7" each | 18pt | 14-16pt | Q-number 48pt |
| Definition slide | 7" left + 4" right | 22pt header | 18pt left, 20pt right | circle 28pt |
| Tier ladder | 8.5" × 1.25" each | 22pt | 14-16pt | stars 22pt |

**When the table doesn't fit your case** — pick the layout with the most similar card dimensions and use those sizes as a starting point. Adjust up or down based on actual content length, then verify in visual QA.

---

## 1. Numbered points

**When**: 3–5 sequential or enumerated points, each with a header + 1–2 lines of detail.

**Sketch**: Red circle with number on the left, bold header + description text on the right, repeated vertically.

**Font sizing**: With only 3-4 points spread vertically over ~5", each point has lots of room. Use **circle number 28pt**, **header 22pt bold**, **body 16-18pt**. For 5 points (more compact), drop to circle 22pt / header 18pt / body 14-15pt.

```javascript
const points = [
  { header: "First key idea here", body: "Brief description supporting the first idea." },
  { header: "Second key idea here", body: "Brief description supporting the second idea." },
  { header: "Third key idea here", body: "Brief description supporting the third idea." },
];

points.forEach((p, i) => {
  const y = 1.5 + i * 1.55; // wider gap for breathing room
  // Number circle (red) — larger to match generous typography
  slide.addShape(pres.shapes.OVAL, {
    x: 0.7, y: y, w: 0.75, h: 0.75,
    fill: { color: SUN_RED }, line: { type: "none" },
  });
  slide.addText(String(i + 1), {
    x: 0.7, y: y, w: 0.75, h: 0.75,
    fontSize: 28, fontFace: FONT_EN, color: "FFFFFF",
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  // Header — bigger and more confident
  slide.addText(p.header, {
    x: 1.7, y: y - 0.05, w: 10.8, h: 0.5,
    fontSize: 22, fontFace: FONT_JP, color: TEXT_DARK,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  // Body — readable at presenting distance
  slide.addText(p.body, {
    x: 1.7, y: y + 0.5, w: 10.8, h: 0.95,
    fontSize: 17, fontFace: FONT_JP, color: TEXT_GREY,
    align: "left", valign: "top", margin: 0,
  });
});
```

For 5 points (compact spacing): use `y = 1.5 + i * 0.7` and reduce height to 0.4-0.6.

**Variation with emoji**: replace the numeric circle with a topical emoji to add personality:
```javascript
const points = [
  { icon: "🎯", header: "Goal", body: "..." },
  { icon: "🚀", header: "Approach", body: "..." },
  { icon: "📊", header: "Outcome", body: "..." },
];
// Instead of the OVAL + number, render the emoji at fontSize 28
slide.addText(p.icon, { x: 0.7, y, w: 0.7, h: 0.7, fontSize: 32, valign: "middle", margin: 0 });
```

---

## 2. Comparison columns (2)

**When**: Two things compared in detail — "Before vs After", "Option A vs Option B", "Old approach vs New approach".

**Sketch**: Two equal-width cards side by side, each with a left accent bar in the column's color.

**Font sizing**: Cards this large (~6" wide × 4-5" tall) are roomy. Use generous typography — **header 22pt bold**, **bullet items 18-20pt**, and only drop to 16pt if you have 6+ bullets per card. Going below 14pt body text inside a card this big leaves the slide looking under-filled.

```javascript
const colW = 6.0;
const startX = 0.5;
const startY = 1.3;
const colH = 4.7;

// Left column (e.g. "Approach A" — gold accent)
slide.addShape(pres.shapes.RECTANGLE, {
  x: startX, y: startY, w: colW, h: colH,
  fill: { color: "FAF5EC" }, line: { type: "none" },
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: startX, y: startY, w: 0.1, h: colH,
  fill: { color: SUN_GOLD }, line: { type: "none" },
});
slide.addText("Approach A", {
  x: startX + 0.3, y: startY + 0.2, w: colW - 0.5, h: 0.5,
  fontSize: 22, fontFace: FONT_EN, color: SUN_GOLD,
  bold: true, align: "left", valign: "middle", margin: 0,
});

// Bullet items inside the card — use generous fontSize because the card is large
slide.addText([
  { text: "First key point in this column", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Second key point in this column", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Third key point in this column", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Fourth key point in this column", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Fifth key point in this column", options: { bullet: { code: "25AA" } } },
], {
  x: startX + 0.3, y: startY + 0.9, w: colW - 0.6, h: colH - 1.1,
  fontSize: 18, fontFace: FONT_JP, color: TEXT_DARK,
  align: "left", valign: "top", margin: 0,
  paraSpaceAfter: 10,
});

// Right column (e.g. "Approach B" — Sun Red accent)
const rx = startX + colW + 0.3;
slide.addShape(pres.shapes.RECTANGLE, {
  x: rx, y: startY, w: colW, h: colH,
  fill: { color: "FFEEEC" }, line: { type: "none" },
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: rx, y: startY, w: 0.1, h: colH,
  fill: { color: SUN_RED }, line: { type: "none" },
});
// ... title + bullet items same pattern as left column, fontSize 18-20pt for bullets
```

Pair this with a centered "key message" beneath the columns at y=6.2 to summarize.

**Scale guide for this layout**: with 4-5 short bullets per column, body 18-20pt fills the card nicely. With 6-7 bullets, drop to 16pt. With 8+ bullets, drop to 14pt and consider whether the card should be split into 2 slides instead.

---

## 3. Comparison columns (3)

**When**: Three things on a spectrum or progression (e.g., "Beginner / Intermediate / Advanced", "Past / Present / Future", "Small / Medium / Large").

**Sketch**: Three equal cards across, each with a top accent bar, title, subtitle, separator, and labeled items.

```javascript
const cols = [
  { title: "Tier 1", subtitle: "Entry level", color: TEXT_GREY, bgColor: "F2F2F2", items: [...] },
  { title: "Tier 2", subtitle: "Intermediate", color: SUN_GOLD, bgColor: "FAF5EC", items: [...] },
  { title: "Tier 3", subtitle: "Advanced", color: SUN_RED, bgColor: "FFEEEC", items: [...] },
];

const colW = 4.0;
const colGap = 0.15;
const startX = 0.5;

cols.forEach((col, i) => {
  const x = startX + i * (colW + colGap);
  // Card
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: 1.4, w: colW, h: 5.4,
    fill: { color: col.bgColor }, line: { type: "none" },
  });
  // Top accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: 1.4, w: colW, h: 0.08,
    fill: { color: col.color }, line: { type: "none" },
  });
  // Title
  slide.addText(col.title, {
    x: x + 0.25, y: 1.55, w: colW - 0.5, h: 0.5,
    fontSize: 22, fontFace: FONT_EN, color: col.color,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  // Subtitle, separator, items...
});
```

---

## 4. Card grid (2x2)

**When**: 4 parallel concepts of equal weight (e.g., "4 personas", "4 risk categories", "4 quadrants").

**Sketch**: 2 rows × 2 columns of cards, each with an icon/symbol + label + body.

**Font sizing**: Each card is ~6" wide × 2.5" tall — substantial real estate. Use **icon 36-40pt**, **title 18-20pt bold**, **body 14-16pt**. The default below uses larger sizes than you might instinctively reach for — that's intentional. Don't drop body text below 13pt unless you have a paragraph-length body inside each card.

```javascript
const items = [
  { icon: "🎯", title: "First topic", body: "Short description for first card." },
  { icon: "💡", title: "Second topic", body: "Short description for second card." },
  { icon: "🚀", title: "Third topic", body: "Short description for third card." },
  { icon: "📊", title: "Fourth topic", body: "Short description for fourth card." },
];

items.forEach((item, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.5 + col * 6.2;
  const y = 1.4 + row * 2.5; // increased from 2.3 to give more vertical space

  // Card with red left accent
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 6.0, h: 2.3,
    fill: { color: LIGHT_GREY }, line: { type: "none" },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.1, h: 2.3,
    fill: { color: SUN_RED }, line: { type: "none" },
  });

  // Big emoji icon at generous size
  slide.addText(item.icon, {
    x: x + 0.25, y: y + 0.2, w: 0.9, h: 0.9,
    fontSize: 40, align: "left", valign: "middle", margin: 0,
  });
  // Label / category tag — slightly larger, more confident
  slide.addText(`Item ${i + 1}`, {
    x: x + 1.2, y: y + 0.2, w: 4.6, h: 0.35,
    fontSize: 12, fontFace: FONT_EN, color: SUN_RED,
    bold: true, align: "left", valign: "middle", margin: 0,
    charSpacing: 2,
  });
  // Title — larger to match card scale
  slide.addText(item.title, {
    x: x + 1.2, y: y + 0.55, w: 4.6, h: 0.5,
    fontSize: 20, fontFace: FONT_JP, color: TEXT_DARK,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  // Body — 15pt is the sweet spot for this card size; 14pt for longer body
  slide.addText(item.body, {
    x: x + 0.3, y: y + 1.2, w: 5.5, h: 1.0,
    fontSize: 15, fontFace: FONT_JP, color: TEXT_DARK,
    align: "left", valign: "top", margin: 0,
  });
});
```

For an "anti-patterns" or "common mistakes" variant, use ✗ as the symbol and a light red tint as the card background (`FFEEEC`).

---

## 5. Process flow (horizontal)

**When**: Sequential steps (3-5 steps work best — more becomes cluttered).

**Sketch**: Boxes in a row, connected by arrows, each box numbered + brief description.

```javascript
const steps = [
  "Step one description",
  "Step two description",
  "Step three description",
  "Step four description",
  "Step five description",
];
const stepW = 2.4;
const stepGap = 0.05;
const totalW = stepW * 5 + stepGap * 4;
const startX = (13.333 - totalW) / 2;

steps.forEach((s, i) => {
  const x = startX + i * (stepW + stepGap);
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: 4.3, w: stepW, h: 0.95,
    fill: { color: LIGHT_GREY }, line: { type: "none" },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: 4.3, w: 0.08, h: 0.95,
    fill: { color: SUN_RED }, line: { type: "none" },
  });
  slide.addText(`${i + 1}`, {
    x: x + 0.18, y: 4.35, w: 0.4, h: 0.35,
    fontSize: 14, fontFace: FONT_EN, color: SUN_RED,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(s, {
    x: x + 0.2, y: 4.7, w: stepW - 0.3, h: 0.5,
    fontSize: 9, fontFace: FONT_JP, color: TEXT_DARK,
    align: "left", valign: "top", margin: 0,
  });
});
```

For a "colored journey" version where each step has a different color (e.g., raw → processed → validated → final), use a `flowSteps[i].color` field for the box fill and white text inside, with red `→` arrows between boxes.

---

## 6. Metrics table (Before / After / Δ)

**When**: Quantitative comparisons — case study results, A/B test outcomes, pre/post data.

**Sketch**: Multi-row table with metric name + Before column + After column + Delta column. The delta column uses Sun Red bold for "improved" values.

```javascript
const tableData = [
  // Header
  [
    { text: "Metric", options: { bold: true, color: "FFFFFF", fill: { color: SUN_RED }, fontSize: 13, fontFace: FONT_JP, align: "left", valign: "middle" } },
    { text: "Before", options: { bold: true, color: "FFFFFF", fill: { color: TEXT_GREY }, fontSize: 13, fontFace: FONT_JP, align: "center", valign: "middle" } },
    { text: "After", options: { bold: true, color: "FFFFFF", fill: { color: SUN_RED }, fontSize: 13, fontFace: FONT_JP, align: "center", valign: "middle" } },
    { text: "Δ", options: { bold: true, color: "FFFFFF", fill: { color: SUN_DARK_RED }, fontSize: 13, fontFace: FONT_JP, align: "center", valign: "middle" } },
  ],
  // Data rows (use placeholders if user hasn't supplied real numbers)
  [
    { text: "Metric A", options: { bold: true, fontSize: 11, fontFace: FONT_JP, valign: "middle" } },
    { text: "[X]", options: { fontSize: 12, fontFace: FONT_EN, align: "center", valign: "middle" } },
    { text: "[Y]", options: { fontSize: 12, fontFace: FONT_EN, align: "center", valign: "middle" } },
    { text: "[+%]", options: { fontSize: 12, fontFace: FONT_EN, color: SUN_RED, bold: true, align: "center", valign: "middle" } },
  ],
  // ... more rows
];

slide.addTable(tableData, {
  x: 0.5, y: 1.3, w: 12.35,
  colW: [4.85, 2.5, 2.5, 2.5],
  rowH: 0.55,
  border: { type: "solid", pt: 0.5, color: BORDER_GREY },
});
```

---

## 7. Pain / Solution split

**When**: Slides where you describe a problem first, then the solution. Particularly useful for use-case slides.

**Sketch**: Left side is a red-tinted card titled "⚠ THE PROBLEM" with bullets. Right side is a wider area with the solution details.

```javascript
// Left: Problem (red-tinted)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.3, w: 4.0, h: 4.0,
  fill: { color: "FFEEEC" }, line: { type: "none" },
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.3, w: 0.08, h: 4.0,
  fill: { color: SUN_RED }, line: { type: "none" },
});
slide.addText("⚠  THE PROBLEM", {
  x: 0.7, y: 1.45, w: 3.8, h: 0.3,
  fontSize: 10, fontFace: FONT_EN, color: SUN_RED,
  bold: true, align: "left", valign: "middle", margin: 0,
  charSpacing: 2,
});
slide.addText([
  { text: "Pain point one description", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Pain point two description", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Pain point three description", options: { bullet: { code: "25AA" } } },
], {
  x: 0.7, y: 1.8, w: 3.7, h: 3.4,
  fontSize: 11, fontFace: FONT_JP, color: TEXT_DARK,
  align: "left", valign: "top", margin: 0,
  paraSpaceAfter: 6,
});

// Right: Solution (full width, no special background)
slide.addText("✓  OUR APPROACH", {
  x: 4.85, y: 1.3, w: 8.0, h: 0.35,
  fontSize: 11, fontFace: FONT_EN, color: SUN_RED,
  bold: true, align: "left", valign: "middle", margin: 0,
  charSpacing: 2,
});
// ... solution content (e.g., a small metrics table or numbered list)
```

---

## 8. Hero callout

**When**: A single high-impact message you want to dominate the slide. Use sparingly — once or twice in a deck max.

**Sketch**: Most of the slide is empty whitespace. A red bar runs across the bottom with a quote in white.

Or: a red-tinted callout fills 70% of the slide content area, with a single quote in large italic text.

```javascript
// Variant A: red bar at bottom
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 6.0, w: 12.35, h: 0.85,
  fill: { color: SUN_RED }, line: { type: "none" },
});
slide.addText('"Your single biggest takeaway in one line."', {
  x: 0.5, y: 6.0, w: 12.35, h: 0.85,
  fontFace: FONT_JP, fontSize: 14, color: "FFFFFF",
  italic: true, bold: true, align: "center", valign: "middle", margin: 0,
});
```

For variant B (whole-slide hero), enlarge the rectangle to occupy y=2 to y=5 and add a quotation mark glyph or 💡 emoji at large scale (60-80pt) as the visual anchor.

---

## 9. Field grid

**When**: Structured metadata, project parameters, or specs (e.g., "Project name", "Customer", "Domain", "Team size").

**Sketch**: 2-column grid of small cards, each with an UPPERCASE label + a value below.

```javascript
const fields = [
  { label: "Field one", val: "[Value placeholder]" },
  { label: "Field two", val: "[Value placeholder]" },
  { label: "Field three", val: "[Value placeholder]" },
  { label: "Field four", val: "[Value placeholder]" },
  { label: "Field five", val: "[Value placeholder]" },
  { label: "Field six", val: "[Value placeholder]" },
];

const cardW = 6.0, cardH = 0.95, gapX = 0.35, gapY = 0.2;
fields.forEach((f, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * (cardW + gapX);
  const y = 1.4 + row * (cardH + gapY);
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: cardW, h: cardH,
    fill: { color: LIGHT_GREY }, line: { type: "none" },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.08, h: cardH,
    fill: { color: SUN_RED }, line: { type: "none" },
  });
  slide.addText(f.label.toUpperCase(), {
    x: x + 0.25, y: y + 0.1, w: cardW - 0.4, h: 0.3,
    fontSize: 9, fontFace: FONT_EN, color: SUN_RED,
    bold: true, align: "left", valign: "middle", margin: 0,
    charSpacing: 2,
  });
  slide.addText(f.val, {
    x: x + 0.25, y: y + 0.4, w: cardW - 0.4, h: 0.5,
    fontSize: 13, fontFace: FONT_JP, color: TEXT_DARK,
    align: "left", valign: "middle", margin: 0,
  });
});
```

---

## 10. Question cards

**When**: Two questions framed as a checklist or screening criteria.

**Sketch**: Two large cards labeled "Q1" / "Q2" with a big red Q-number in the corner and the question + reasoning below.

```javascript
const qCards = [
  { num: "Q1", title: "First question?", body: "Reasoning and detail behind question 1." },
  { num: "Q2", title: "Second question?", body: "Reasoning and detail behind question 2." },
];

qCards.forEach((q, i) => {
  const x = 0.5 + i * 6.3;
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y: 1.6, w: 6.0, h: 3.7,
    fill: { color: LIGHT_GREY }, line: { type: "none" },
  });
  slide.addText(q.num, {
    x: x + 0.3, y: 1.75, w: 1.0, h: 0.7,
    fontSize: 36, fontFace: FONT_EN, color: SUN_RED,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(q.title, {
    x: x + 0.3, y: 2.5, w: 5.5, h: 1.0,
    fontSize: 14, fontFace: FONT_JP, color: TEXT_DARK,
    bold: true, align: "left", valign: "top", margin: 0,
  });
  slide.addText(q.body, {
    x: x + 0.3, y: 3.6, w: 5.5, h: 1.6,
    fontSize: 11, fontFace: FONT_JP, color: TEXT_GREY,
    align: "left", valign: "top", margin: 0,
  });
});

// Conclusion bar at the bottom
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 5.6, w: 12.3, h: 1.0,
  fill: { color: SUN_RED }, line: { type: "none" },
});
slide.addText("✓  Both YES   →   Conclusion", {
  x: 0.5, y: 5.6, w: 12.3, h: 1.0,
  fontFace: FONT_JP, fontSize: 22, color: "FFFFFF",
  bold: true, align: "center", valign: "middle", margin: 0,
});
```

---

## 11. Definition slide

**When**: Defining a concept with 3 supporting points + a key message callout.

**Sketch**: Left 60% — three numbered points with circle + header + body. Right 40% — a key message callout.

This is a great "first content slide" after the cover, because it sets up a definition + the takeaway.

```javascript
// Left side — 3 numbered points (using the Numbered Points pattern, narrowed to w=6.5)
const points = [
  { header: "First supporting point", body: "Brief description." },
  { header: "Second supporting point", body: "Brief description." },
  { header: "Third supporting point", body: "Brief description." },
];
points.forEach((p, i) => {
  const y = 1.45 + i * 1.4;
  slide.addShape(pres.shapes.OVAL, {
    x: 0.7, y, w: 0.6, h: 0.6,
    fill: { color: SUN_RED }, line: { type: "none" },
  });
  slide.addText(String(i + 1), {
    x: 0.7, y, w: 0.6, h: 0.6,
    fontSize: 22, fontFace: FONT_EN, color: "FFFFFF",
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  slide.addText(p.header, {
    x: 1.5, y: y - 0.05, w: 6.5, h: 0.45,
    fontSize: 17, fontFace: FONT_JP, color: TEXT_DARK,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(p.body, {
    x: 1.5, y: y + 0.45, w: 6.5, h: 0.85,
    fontSize: 13, fontFace: FONT_JP, color: TEXT_GREY,
    align: "left", valign: "top", margin: 0,
  });
});

// Right side — key message callout
slide.addShape(pres.shapes.RECTANGLE, {
  x: 8.6, y: 1.45, w: 4.2, h: 4.0,
  fill: { color: LIGHT_GREY }, line: { type: "none" },
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: 8.6, y: 1.45, w: 0.08, h: 4.0,
  fill: { color: SUN_RED }, line: { type: "none" },
});
slide.addText("💡 KEY MESSAGE", {
  x: 8.85, y: 1.65, w: 3.8, h: 0.4,
  fontSize: 11, fontFace: FONT_EN, color: SUN_RED,
  bold: true, align: "left", valign: "middle", margin: 0,
  charSpacing: 4,
});
slide.addText('"Your one-line takeaway here."', {
  x: 8.85, y: 2.1, w: 3.8, h: 3.2,
  fontSize: 18, fontFace: FONT_JP, color: TEXT_DARK,
  italic: true, align: "left", valign: "top", margin: 0,
});
```

---

## 12. Tier ladder

**When**: Skill levels, maturity tiers, progression (e.g., "Basic / Intermediate / Advanced", or "★ / ★★ / ★★★").

**Sketch**: 3 horizontal bars stacked vertically, each darker/redder than the last, with stars + title + description on the left and "impact / who" details on the right.

```javascript
const levels = [
  { stars: "★", title: "Tier one", desc: "Description for tier one.", impact: "Impact note", who: "Audience note", color: SUN_GOLD, bgColor: "FAF5EC" },
  { stars: "★★", title: "Tier two", desc: "Description for tier two.", impact: "Impact note", who: "Audience note", color: SUN_DARK_RED, bgColor: "FFF0EE" },
  { stars: "★★★", title: "Tier three", desc: "Description for tier three.", impact: "Impact note", who: "Audience note", color: SUN_RED, bgColor: "FFEEEC" },
];

levels.forEach((lv, i) => {
  const y = 1.55 + i * 1.4;
  // Card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y, w: 8.5, h: 1.25,
    fill: { color: lv.bgColor }, line: { type: "none" },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y, w: 0.1, h: 1.25,
    fill: { color: lv.color }, line: { type: "none" },
  });
  slide.addText(lv.stars, {
    x: 0.75, y: y + 0.1, w: 1.0, h: 0.4,
    fontSize: 18, fontFace: FONT_EN, color: lv.color,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(lv.title, {
    x: 1.65, y: y + 0.1, w: 7.0, h: 0.4,
    fontSize: 18, fontFace: FONT_JP, color: lv.color,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(lv.desc, {
    x: 0.75, y: y + 0.55, w: 8.0, h: 0.7,
    fontSize: 11, fontFace: FONT_JP, color: TEXT_DARK,
    align: "left", valign: "top", margin: 0,
  });
  // Right-side impact + who labels
  slide.addText("IMPACT", {
    x: 9.2, y: y + 0.1, w: 3.6, h: 0.25,
    fontSize: 8, fontFace: FONT_EN, color: TEXT_GREY,
    bold: true, align: "left", valign: "middle", margin: 0,
    charSpacing: 2,
  });
  slide.addText(lv.impact, {
    x: 9.2, y: y + 0.32, w: 3.6, h: 0.4,
    fontSize: 10, fontFace: FONT_JP, color: TEXT_DARK,
    align: "left", valign: "top", margin: 0,
  });
  // ... and similar for "WHO"
});
```

---

# Image-Rich Layouts (used with `--image` mode)

The following 5 layouts are designed for image-rich mode. Each uses an `addImagePlaceholder()` helper that renders a dashed-bordered rectangle containing the AI image prompt — the user copies the prompt into Gemini / ChatGPT, generates the image, then pastes it over the placeholder.

**Helper function** (define once, reuse across layouts):

```javascript
function addImagePlaceholder(slide, x, y, w, h, prompt) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: "F7F7F7" },
    line: { color: SUN_RED, width: 1.5, dashType: "dash" },
  });
  slide.addText("🖼  AI PROMPT — COPY & PASTE", {
    x: x + 0.15, y: y + 0.15, w: w - 0.3, h: 0.3,
    fontSize: 9, fontFace: FONT_EN, color: SUN_RED,
    bold: true, align: "left", valign: "top", margin: 0,
    charSpacing: 2,
  });
  slide.addText(prompt, {
    x: x + 0.2, y: y + 0.55, w: w - 0.4, h: h - 0.7,
    fontSize: 10, fontFace: FONT_JP, color: TEXT_GREY,
    italic: true, align: "left", valign: "top", margin: 0,
  });
}
```

## 13. Hero image + headline + paragraph

**When**: Section openers, "what is X" slides, narrative kickoffs. The image carries the emotional weight; the text is short.

**Sketch**: A 3:2 landscape image fills the top ~60% of the slide. Below it, a bold headline and a short paragraph.

```javascript
// Hero image — 3:2 landscape, top of slide
// Width: 12.3", Height: 12.3 * 2/3 = 8.2"... too tall.
// Better: use 9" × 3" (3:1 close to 3:2), or 7.5" × 3" (5:2). Pick 9" × 3" (close to 3:2 cinematic).
// Actually for a true 3:2 fitting the slide: width 8.7", height 5.8" — but that's too tall for header+text below.
// Practical compromise: 7.5" × 5" = 3:2 exactly, centered, with text beside or below.
// Simpler: full-width banner 12.3" × 4.1" = 3:1 (works with Nano Banana 3:1 if needed) OR
// 12.3" × 6.15" = 2:1 — also works. For 3:2 strictly, use 9.45" × 6.3":
addImagePlaceholder(slide, 0.5, 1.3, 9.45, 4.1,  // ≈ 3:1.3, close to 21:9 banner
  "Aspect ratio: 3:2 landscape (or 21:9 wide if your tool supports it). Style: clean professional editorial illustration, flat design with subtle depth. Subject: <describe the visual concept here>. Mood: optimistic, modern. Color palette: predominantly white background (#FFFFFF) with light grey supporting tones (#F7F7F7), and one bold red accent (#FF2200) on the focal element. Pick palette per slide tone — see SKILL.md palette heuristics.");

// Headline beside or below — here, beside (right column)
slide.addText("Big headline goes here", {
  x: 10.15, y: 1.5, w: 2.85, h: 0.8,
  fontSize: 26, fontFace: FONT_JP, color: TEXT_DARK,
  bold: true, align: "left", valign: "top", margin: 0,
});
slide.addText("Brief paragraph describing this slide's key concept. Keep this to 2-3 short sentences max.", {
  x: 10.15, y: 2.4, w: 2.85, h: 3.0,
  fontSize: 14, fontFace: FONT_JP, color: TEXT_DARK,
  align: "left", valign: "top", margin: 0,
});

// Optional bottom-row key message
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 5.6, w: 12.5, h: 0.9,
  fill: { color: LIGHT_GREY }, line: { type: "none" },
});
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 5.6, w: 0.08, h: 0.9,
  fill: { color: SUN_RED }, line: { type: "none" },
});
slide.addText('"Key message in italic underneath."', {
  x: 0.75, y: 5.6, w: 12.0, h: 0.9,
  fontSize: 14, fontFace: FONT_JP, color: TEXT_DARK,
  italic: true, align: "left", valign: "middle", margin: 0,
});
```

## 14. Side image + bullets

**When**: Concept slides where the image illustrates the text on the side. Standard editorial layout — left image, right bullets (or reversed).

**Sketch**: 2:3 portrait image on left (~40% width), bullet list on right (~55% width).

```javascript
// Left: 2:3 portrait image — 4" × 6"
addImagePlaceholder(slide, 0.5, 1.3, 4.0, 5.4,  // close to 2:3
  "Aspect ratio: 2:3 portrait. Style: clean editorial illustration. Subject: <describe the figure or scene>. Mood: focused, professional. Color palette: white background (#FFFFFF), figure rendered in neutral dark (#1A1A1A), with one accent color chosen by slide tone — red (#FF2200) for energy, gold (#B69256) for warmth/growth, dark red (#AD0C00) for caution. Pick one accent per image, don't mix all three.");

// Right: title + bullets
slide.addText("Slide headline here", {
  x: 4.85, y: 1.3, w: 8.0, h: 0.6,
  fontSize: 24, fontFace: FONT_JP, color: TEXT_DARK,
  bold: true, align: "left", valign: "middle", margin: 0,
});

slide.addText([
  { text: "First bullet point with substance — 1 line of detail", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Second bullet point with substance — 1 line of detail", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Third bullet point with substance — 1 line of detail", options: { bullet: { code: "25AA" }, breakLine: true } },
  { text: "Fourth bullet point — final supporting detail", options: { bullet: { code: "25AA" } } },
], {
  x: 4.85, y: 2.1, w: 8.0, h: 4.6,
  fontSize: 17, fontFace: FONT_JP, color: TEXT_DARK,
  align: "left", valign: "top", margin: 0,
  paraSpaceAfter: 12,
});
```

## 15. Image grid (2×2 or 1×3)

**When**: Showing multiple examples / variants / personas / quadrants. Each image represents one concept, with a label below.

**Sketch (2×2)**: Four 1:1 square images in a grid, each with a label / short caption.

```javascript
const items = [
  { label: "First item", caption: "Short description", prompt: "Aspect ratio: 1:1. Style: minimalist icon illustration. Subject: <first thing>." },
  { label: "Second item", caption: "Short description", prompt: "Aspect ratio: 1:1. Style: minimalist icon illustration. Subject: <second thing>." },
  { label: "Third item", caption: "Short description", prompt: "Aspect ratio: 1:1. Style: minimalist icon illustration. Subject: <third thing>." },
  { label: "Fourth item", caption: "Short description", prompt: "Aspect ratio: 1:1. Style: minimalist icon illustration. Subject: <fourth thing>." },
];

items.forEach((item, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.7 + col * 6.2;
  const y = 1.4 + row * 2.7;

  // 1:1 square image placeholder, 2" × 2"
  addImagePlaceholder(slide, x, y, 2.0, 2.0, item.prompt);

  // Label + caption beside the image
  slide.addText(item.label, {
    x: x + 2.2, y: y + 0.3, w: 3.5, h: 0.5,
    fontSize: 18, fontFace: FONT_JP, color: TEXT_DARK,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(item.caption, {
    x: x + 2.2, y: y + 0.85, w: 3.5, h: 1.1,
    fontSize: 13, fontFace: FONT_JP, color: TEXT_GREY,
    align: "left", valign: "top", margin: 0,
  });
});
```

**1×3 horizontal variant**: Three 1:1 images in a row, each ~3.5" × 3.5", with labels below.

## 16. Big centerpiece + annotations

**When**: System diagrams, conceptual maps, "how it works" slides. A single big illustration anchors the slide, with small annotations / labels around it.

**Sketch**: A 1:1 or 3:2 image takes the center 60-70% of the slide. Short labeled callouts arranged around it (top, sides, bottom).

```javascript
// Center: big square image, ~5" × 5"
addImagePlaceholder(slide, 4.15, 1.4, 5.0, 5.0,
  "Aspect ratio: 1:1 square. Style: isometric flat illustration / system diagram. Subject: <central concept — a system, a flow, a structure>. Composition: centered, balanced. Mood: clear, educational. Color palette: white background (#FFFFFF), structure rendered in neutral grey tones (#666666, #999999) with a single red accent (#FF2200) on the critical/highlighted element of the diagram. Keep most of the diagram neutral so the accent reads.");

// Four annotation callouts around the centerpiece — corners
const annotations = [
  { x: 0.5, y: 1.4, label: "Component A", text: "Short label" },
  { x: 9.5, y: 1.4, label: "Component B", text: "Short label" },
  { x: 0.5, y: 5.0, label: "Component C", text: "Short label" },
  { x: 9.5, y: 5.0, label: "Component D", text: "Short label" },
];

annotations.forEach(a => {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: a.x, y: a.y, w: 3.5, h: 1.4,
    fill: { color: LIGHT_GREY }, line: { type: "none" },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: a.x, y: a.y, w: 0.08, h: 1.4,
    fill: { color: SUN_RED }, line: { type: "none" },
  });
  slide.addText(a.label, {
    x: a.x + 0.2, y: a.y + 0.15, w: 3.2, h: 0.4,
    fontSize: 14, fontFace: FONT_JP, color: SUN_RED,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(a.text, {
    x: a.x + 0.2, y: a.y + 0.55, w: 3.2, h: 0.7,
    fontSize: 12, fontFace: FONT_JP, color: TEXT_DARK,
    align: "left", valign: "top", margin: 0,
  });
});
```

## 17. Image background + overlay text

**When**: Quote slides, mission statements, dramatic moments. The image is full-bleed; text overlays on top with high contrast.

**Sketch**: A full-slide 3:2 image (placeholder fills nearly the entire slide). A semi-transparent red overlay covers part of it, with bold white text on top.

```javascript
// Full-bleed image placeholder — covers most of the slide
addImagePlaceholder(slide, 0.5, 1.3, 12.3, 5.4,  // close to 3:2 / 2:1
  "Aspect ratio: 3:2 landscape (or 16:9 if your tool supports it). Style: cinematic editorial photography or rich illustration. Subject: <dramatic visual that fits the message>. Mood: <dramatic / inspiring / serious>. Lighting: contrasted, with darker areas on the lower-left for text overlay. Color palette: rich tones with one dominant accent matching slide tone — bold red (#FF2200) for energy/decisiveness, deep red (#AD0C00) for gravitas/warning, or warm gold (#B69256) for achievement/legacy. Pick one accent that matches the slide's emotion.");

// Semi-opaque red overlay strip on the left for text contrast
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 4.5, w: 7.0, h: 2.2,
  fill: { color: SUN_RED, transparency: 15 }, // 15% transparent
  line: { type: "none" },
});

// Overlay text — bold white quote or statement
slide.addText('"Your bold statement or quote, in italic, fills this overlay area."', {
  x: 0.85, y: 4.65, w: 6.3, h: 1.9,
  fontSize: 20, fontFace: FONT_JP, color: "FFFFFF",
  italic: true, bold: true, align: "left", valign: "middle", margin: 0,
});
```

**Note about overlay**: The image generator won't know where you'll place the overlay. Either:
1. Mention in the prompt where the dark/quiet area should be ("lighting: contrasted, with darker areas on the lower-left for text overlay")
2. Or use a high-transparency red box that works regardless of image content

---

## Picking layouts: a heuristic

If your content is...

| Content shape | Try layout |
|--------------|------------|
| 3-5 sequential or enumerated points | Numbered points (#1) or process flow (#5) |
| 2 things compared in detail | Comparison columns 2 (#2) |
| 3 things on a spectrum | Comparison columns 3 (#3) |
| 4 parallel items of equal weight | Card grid 2×2 (#4) |
| Sequential steps | Process flow (#5) |
| Pre/post numbers | Metrics table (#6) |
| Problem → solution slide | Pain/Solution split (#7) |
| One huge takeaway | Hero callout (#8) |
| Project parameters / metadata | Field grid (#9) |
| 2 framed questions | Question cards (#10) |
| Definition + key message | Definition slide (#11) |
| Levels / progression | Tier ladder (#12) |
| **Section opener (image-rich)** | **Hero image + text (#13)** |
| **Concept with supporting visual (image-rich)** | **Side image + bullets (#14)** |
| **Multiple examples shown visually (image-rich)** | **Image grid (#15)** |
| **System / process diagram (image-rich)** | **Big centerpiece + annotations (#16)** |
| **Quote / mission / dramatic moment (image-rich)** | **Image background + overlay text (#17)** |

When picking layouts across consecutive slides, **vary the choice** — don't run three "numbered points" slides in a row. The variety is what makes a deck feel polished.
