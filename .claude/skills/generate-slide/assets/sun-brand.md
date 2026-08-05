# Sun* Brand Regulation — Presentation Edition

This is the source of truth for visual identity in Sun* presentations. When in doubt, follow these rules over instinct.

## Notation

The company name is always written: **Sun*** (capital S, lowercase un, asterisk).

| ✓ Correct | ✗ Wrong |
|-----------|---------|
| Sun* | SUN* |
| Sun* Inc. | Sun Inc. |
| Sun* Vietnam | Sun Vietnam |
| Sun* Asterisk | サンアスタリスク (in non-JP context) |

The asterisk is part of the name — don't strip it for "cleanliness". In Japanese contexts where the asterisk is awkward, use `Sun*` in English text and `サン・アスタリスク株式会社` only when writing the formal corporate entity name.

## Colors

### Main brand color

**Sun Red — `#FF2200`**

This is the only color the brand designates as "main". The rule:

> Use Sun Red as **one accent per slide** — not as a background fill for everything.

In practice, this means each body slide should have one or two prominent red elements:
- A red callout bar with a key message
- A red horizontal line under the slide title
- Red text for a single emphasized phrase
- A red icon or number circle

The rest of the slide stays neutral. Flooding a slide with red-tinted cards everywhere defeats the purpose — Sun Red is supposed to direct the eye, not occupy it.

### Sub-colors (sparingly)

Use these only when the slide has multiple categories that need visual distinction (e.g., a 4-column comparison, a multi-row table with different sentiment per row):

| Color name | Hex | When to use |
|------------|-----|-------------|
| Sun Dark Red | `#AD0C00` | Secondary emphasis (e.g., "negative" column in a table where Sun Red is "positive") |
| Sun Gold | `#B69256` | Warm accent for "neutral" or "intermediate" items |
| Sun Yellow | `#FDBA05` | Bright accent for "warning" or "highlight" |
| Light Grey | `#F7F7F7` | Card / panel backgrounds, alternating table rows |

### Neutral palette

| Purpose | Hex |
|---------|-----|
| Body text | `#1A1A1A` |
| Secondary text / captions | `#666666` |
| Borders | `#DDDDDD` |
| White (default background) | `#FFFFFF` |

### Light tints (background only, derived from main palette)

When you need a "tinted" card background that hints at a brand color without using the saturated version:

| Tint | Hex | Derived from |
|------|-----|--------------|
| Light red tint | `#FFEEEC` | Sun Red |
| Light dark-red tint | `#FFF0EE` | Sun Dark Red |
| Light gold tint | `#FAF5EC` | Sun Gold |

These are appropriate for warning callouts, "anti-pattern" cards, etc.

### Don't use

- Random brand colors not on this list (no blues, greens, purples)
- Black `#000000` for text (use `#1A1A1A` instead — softer, brand-consistent)
- The red logo on a red background (it disappears)

## Typography

### Brand fonts (target environments)

- **Eina03** — English headings and body (the official corporate font)
- **Noto Sans JP** — Japanese (and works as a multilingual fallback)

### Practical guidance

Eina03 is licensed and may not be installed on every rendering environment. **Noto Sans JP works as a clean fallback for Vietnamese, English, and Japanese**, so it's the safe default for body text in mixed-language decks.

```javascript
const FONT_JP = "Noto Sans JP";  // Body, multilingual
const FONT_EN = "Eina03";         // English headers (falls back gracefully)
```

### Type scale

| Element | Size | Weight |
|---------|------|--------|
| Cover title | 44-48pt | Bold |
| Cover subtitle | 18-22pt | Regular |
| Section divider title | 40-44pt | Bold |
| Section divider "PART NN" label | 16-18pt | Regular, char-spaced |
| Body slide title | 22pt | Bold |
| Section header within body | 14-16pt | Bold |
| Body text | 11-13pt | Regular |
| Captions / footnotes | 9-10pt | Regular, often grey |
| Small UPPERCASE labels | 9-11pt | Bold, char-spacing 2-3 |

The contrast between title (22pt bold) and body (11-13pt) is what creates hierarchy. Avoid intermediate sizes like 18pt body — they muddy the rhythm.

## Layout & Composition

### Slide size

16:9 widescreen. In `pptxgenjs`: `LAYOUT_WIDE` (13.333" × 7.5").

### Margins

- Outer margin: 0.5" minimum from any edge
- Header line at y=0.95"
- Footer at y=7.0" (mini logo) / y=7.05" (page number, copyright)
- Content area: roughly y=1.05" to y=6.8"

Don't place content above y=1.0" or below y=7.0" — those zones are reserved for header/footer chrome.

### Header

Body slides have a consistent header:
- Title: top-left, 22pt bold, dark text
- A thin **Sun Red** line (height 0.025") at y=0.95" spanning full width

Do **not** add:
- Decorative bars or ribbons
- Icons next to the title
- Subtitle or breadcrumb text in the header area
- Page number in the header (it's in the footer)

### Footer

- Page number at left (`x=0.4`)
- `©YEAR Sun* Inc.` centered (`x=5.5, w=2.5`)
- Mini Sun* logo at right (`x=12.55, w=0.55`)
- A faint grey separator line (`#DDDDDD`) at y=6.98"

The footer is identical on every body slide. Cover slides, section dividers, and closing slides have a different footer (just `©YEAR Sun* Inc.` in white, bottom-right).

## Logo Usage

### What's in `assets/logo_sun.png`

The bundled logo is the **red Sun* logo on transparent background**. This works on:
- White / light grey backgrounds (body slides)
- As the mini logo in body footers

### What to do on red backgrounds (cover, dividers, closing)

The red logo on a red background is invisible. Two options:

**Option A (simplest, what we use)**: Use white text "Sun*" instead of the logo image.

```javascript
slide.addText("Sun*", {
  x: 0.7, y: 0.6, w: 2.5, h: 0.8,
  fontSize: 36, fontFace: FONT_EN, color: "FFFFFF",
  bold: true, align: "left", valign: "middle", margin: 0,
});
```

**Option B**: Source a white-version of the logo file separately (not bundled in this skill).

### Logo placement rules

- Aspect ratio: never stretch or distort
- Clearance: keep at least the height of the "Sun" letters' x-height as padding around the logo
- The logo's "center" for alignment purposes is the **"Sun" letters**, not including the asterisk
- Don't place the Sunbear character together with the logo (separate brand asset)
- Don't put the gold-version logo on red — that pairing is forbidden

## Tone

The brand voice for slides:

- **Optimistic**: Frame challenges as opportunities. Avoid corporate gloom.
- **Generous**: Credit teams and partners. Don't oversell ego.
- **Agile**: Short sentences, direct verbs. Cut hedging.
- **Skillful**: Show technical depth where relevant. Don't over-simplify.
- **Adventurous**: It's OK to use bold framings, novel comparisons, unexpected callouts. The brand isn't conservative.

For Japanese-audience decks, layer in keigo (敬語) appropriately — but the underlying message stays in this voice register.

## Common Mistakes Checklist

Run through this before delivering:

- [ ] All references to the company are written as "Sun*" (with asterisk)
- [ ] Sun Red used as accent (one-two prominent uses per body slide), not as flood fill
- [ ] Body slides have white background, header line, and full footer
- [ ] Cover and section divider use red background; body uses white
- [ ] No red logo on red background (use white "Sun*" text instead)
- [ ] Page numbers present on body slides, absent on cover
- [ ] No decorative chrome (ribbons, accent bars under titles, side borders) beyond the Sun Red header line
- [ ] Fonts: Noto Sans JP or Eina03 only; no Arial / Calibri / Times
- [ ] Hex colors don't include `#` (pptxgenjs requirement)
- [ ] No text overflow — every text box's content fits inside its bounds
