# Extraction Best Practices

How to capture and read design references so the extraction is worth something.

## Capture Quality Guidelines

### Screenshot Requirements
- High resolution (at least 1920px wide for desktop)
- True color (kill any browser extension that shifts color)
- Real viewport size, not a full-page scroll
- Device-specific resolutions (desktop 1920x1080, mobile 390x844)
- Several states: default, hover, active, responsive breakpoints

### Multiple Examples
- Read 3-5 screens minimum before you trust a pattern
- Mix the page types (home, product, about, contact)
- A single screenshot hides the patterns
- Pull from the same site to see what stays consistent

## Analysis Best Practices

### 1. Demand Specifics
❌ Don't settle for: "Uses blue and gray colors"
✓ Insist on: "Primary: #1E40AF, Secondary: #6B7280, Accent: #F59E0B"

❌ Don't settle for: "Modern sans-serif font"
✓ Insist on: "Inter, weight 600, 48px for h1, tracking -0.02em"

### 2. Document Rationale
Get to *why* a decision works, not just *what* it is:
- Why does this palette read as trustworthy?
- Why does this spacing scale read more easily?
- Why does this type hierarchy steer the eye?

### 3. Create Actionable Guidelines
The output should drop straight into code:

```css
/* Immediately usable CSS from extraction */
:root {
  --font-display: 'Bebas Neue', sans-serif;
  --font-body: 'Inter', sans-serif;

  --color-primary-600: #1E40AF;
  --color-accent-500: #F59E0B;

  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;

  --radius-sm: 4px;
  --radius-md: 8px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}
```

### 4. Cross-Reference
- Check font guesses against the Google Fonts library
- Use font-ID tools (WhatFont, Font Ninja) for accuracy
- Verify the extracted colors by hand with an eyedropper

### 5. Iterate Analysis
The first pass misses the subtleties:
- Run the broad analysis once
- Read the output, find the gaps
- Run focused follow-ups on the specific elements

## Advanced Techniques

### Design System Mining
Recover a full system from a single brand (10+ screens):

Read `docs/inspiration/brand/*.png` (all images in one call) with this prompt:
> "Extract complete, production-ready design system:
> - All color tokens (20+ colors)
> - All typography specs (sizes, weights, line-heights)
> - All spacing tokens
> - All component variants
> - All animation timings
> Output as CSS variables ready for implementation."

Save to `docs/design-guidelines/brand-design-system.md`.

### Trend Analysis
Read several top designs at once to spot what's current:

Read the `docs/inspiration/awwwards-*.png` images with this prompt:
> "Trend analysis across these award-winning designs:
> 1. Dominant aesthetic movements
> 2. Common color strategies
> 3. Typography trends
> 4. Layout innovations
> 5. Animation patterns
> Identify what's currently trending in web design."

Save to `docs/design-guidelines/trend-analysis.md`.

### Historical Evolution
Track how one brand's design has moved over time:

Read both `docs/inspiration/brand-2020.png` and `docs/inspiration/brand-2024.png` with this prompt:
> "Compare 2020 vs 2024 design evolution:
> 1. What changed and why
> 2. What remained consistent (brand identity)
> 3. How trends influenced changes
> 4. Lessons for our design evolution"

Save to `docs/design-guidelines/evolution-analysis.md`.

## Common Pitfalls

### ❌ Surface-Level Analysis
"Uses blue colors and sans-serif fonts"
**Fix**: Demand specifics — hex codes, font names, size values

### ❌ Missing Context
Extracting without knowing the audience or the purpose
**Fix**: Learn the brand context before you analyze

### ❌ Blind Copying
Lifting a design 1:1 onto your project
**Fix**: Extract the principles, then adapt them to your context

### ❌ Single Source
Learning off one example
**Fix**: Read 3-5 to tell the patterns from the one-offs
