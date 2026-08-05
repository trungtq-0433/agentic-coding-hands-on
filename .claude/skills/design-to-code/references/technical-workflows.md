# Complete Workflow Examples

Start-to-finish pipelines for analyzing and optimizing assets.

## Example 1: Hero Section (Analysis & Optimize Pipeline)

1. **Read the aesthetic quality** — Read `docs/assets/hero-desktop.png` with:
   > "Rate this image 1-10 for: visual appeal, color harmony, suitability for overlaying white text, professional quality. List any improvements needed."
   Save to `docs/assets/hero-evaluation.md`.

2. **If it clears 7/10, optimize for the web:**
   ```bash
   python scripts/media_optimizer.py \
     --input docs/assets/hero-desktop.png \
     --output docs/assets/hero-desktop.webp \
     --quality 85
   ```

3. **Do the mobile variant (9:16):**
   ```bash
   python scripts/media_optimizer.py \
     --input docs/assets/hero-mobile.png \
     --output docs/assets/hero-mobile.webp \
     --quality 85
   ```

## Example 2: Extract, Analyze Loop

1. **Pull guidelines off the inspiration** — Read `docs/inspiration/competitor-hero.png` with the extraction prompt from `extraction-prompts.md`. Save to `docs/design-guidelines/competitor-analysis.md`.

2. **Read your own asset** — Read `docs/assets/our-hero.png` with:
   > "Compare to competitor design. Rate differentiation (1-10). Are we too similar or successfully distinct?"
   Save to `docs/assets/differentiation-analysis.md`.

3. **Pull colors for CSS** — Read `docs/assets/our-hero.png` with the color-extraction prompt from `visual-analysis-overview.md`. Save to `docs/assets/color-palette.md`.

## Example 3: A/B Test Assets

1. **Weigh the variants** — Read `docs/assets/variant-a.png` and `docs/assets/variant-b.png` together with:
   > "A/B comparison for [target audience]:
   > 1. Attention capture
   > 2. Brand alignment
   > 3. Conversion potential
   > Recommend which to use."
   Save to `docs/assets/ab-comparison.md`.

## Batch Analysis for Rapid Iteration

Read several variation images at once (e.g., `docs/assets/var-1.png`, `var-2.png`, `var-3.png`) in a single call with:
> "Rank these variations 1-3 with scores. Identify winner."
