# Visual Analysis Overview

Use the Read tool to read design assets and hold them to the standard.

## Purpose

- Confirm a generated asset holds the aesthetic direction
- Make sure it's good enough before it goes into the build
- Surface the exact fixes needed for the next pass
- Decide on the evidence, not the gut
- Pull out the data worth keeping (hex codes, composition notes)

## Quick Start

### Comprehensive Analysis
Read `docs/assets/generated-hero.png` with the detailed prompt from `analysis-prompts.md`. Save to `docs/assets/analysis-report.md`.

### Compare Multiple Variations
Read `docs/assets/option-1.png`, `option-2.png`, and `option-3.png` together with the comparison prompt from `analysis-prompts.md`. Save to `docs/assets/comparison-analysis.md`.

### Extract Color Palette
Read `docs/assets/final-asset.png` with this prompt:
> "Extract 5-8 dominant colors with hex codes. Classify as primary/accent/neutral. Suggest CSS variable names."

Save to `docs/assets/color-palette.md`.

## Decision Framework

### Score ≥ 8/10: Move to Integration
**Actions**:
- Optimize for web delivery
- Build the responsive variants
- Write the implementation guidelines
- Pull the palette into CSS variables

### Score 6-7/10: Minor Refinements Needed
**Actions**:

- Weigh regenerating just the problem areas
- Proceed with care if you're tight on time

### Score < 6/10: Major Iteration Required
**Actions**:
- Read the specific failure points from the report
- Rework the generation prompt substantially
- Regenerate with the corrected parameters
- Weigh a different aesthetic approach altogether

## Detailed References

- `analysis-prompts.md` — every analysis prompt template
- `analysis-techniques.md` — the advanced strategies
- `analysis-best-practices.md` — quality guidelines and pitfalls

## Example Color Extraction Output

```css
/* Extracted Color Palette */
:root {
  /* Primary Colors */
  --color-primary-600: #2C5F7D;  /* Dark teal - headers, CTAs */
  --color-primary-400: #4A90B8;  /* Medium teal - links, accents */

  /* Accent Colors */
  --color-accent-500: #E8B44F;   /* Warm gold - highlights */

  /* Neutral Colors */
  --color-neutral-900: #1A1A1A;  /* Near black - body text */
  --color-neutral-100: #F5F5F5;  /* Light gray - backgrounds */

  /* Semantic Usage */
  --color-text-primary: var(--color-neutral-900);
  --color-text-on-primary: #FFFFFF;
  --color-background: var(--color-neutral-100);
  --color-cta: var(--color-primary-600);
}
```
