# Advanced Analysis Techniques

Sharper moves for reading and testing visuals.

## Batch Analysis for Rapid Iteration

Read several variations at once with the Read tool:

1. Pull together the variation files (e.g., `docs/assets/var-1.png`, `var-2.png`, `var-3.png`)
2. Read each image with this prompt:
   > "Rank these variations 1-3 with scores. Identify winner."
3. Pass all the images in a single Read call when you want them judged side by side

## Contextual Testing

Test the asset where it actually lives:

1. **Mock up the UI overlay** (in a design tool or in code)
2. **Screenshot** the asset with the real UI on it
3. **Read the combined version** with this prompt:
   > "Evaluate this hero section with actual UI:
   > 1. Headline readability over image
   > 2. CTA button visibility and contrast
   > 3. Navigation bar integration
   > 4. Overall visual hierarchy effectiveness
   > Provide WCAG contrast ratio estimates."

## A/B Testing Analysis

Weigh two directions objectively by reading both images:

> "A/B test analysis:
>
> Design A: [minimalist approach]
> Design B: [maximalist approach]
>
> Compare for:
> 1. User attention capture (first 3 seconds)
> 2. Information hierarchy clarity
> 3. Emotional impact and brand perception
> 4. Conversion optimization potential
> 5. Target audience alignment ([describe audience])
>
> Recommend which to A/B test in production and why."

## Iteration Strategy

When the score lands below 6/10:

1. **Name the top 3 weaknesses** from the analysis
2. **Address each** in a refined build or an adjusted asset
3. **Re-read with the Read tool** before committing
4. **Keep going** until the score clears 7/10

## Documentation Strategy

Keep the analysis reports as part of the design-system record:

```
docs/
  assets/
    hero-image.png
    hero-analysis.md       # Analysis report
    hero-color-palette.md  # Extracted colors
  design-guidelines/
    asset-usage.md         # Guidelines derived from analysis
```
