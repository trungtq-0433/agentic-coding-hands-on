# Analysis Prompt Templates

Ready-to-use prompts for visual analysis and verification.

## Comprehensive Analysis Prompt

```
Read this design asset top to bottom:

## Design Alignment
- Aesthetic Direction: [e.g., brutalist/minimalist/maximalist]
- Expected Style: [describe the target]
- Color Palette Target: [the colors you expect]

## Evaluation Criteria
1. Visual Coherence: does it hold to the intended direction?
2. Color Analysis: list the dominant colors (hex). Weigh harmony and mood.
3. Composition: read the balance, focal points, negative space, flow.
4. Typography Compatibility: rate it for text overlay (contrast, busy areas).
5. Professional Quality: 1-10, with a reason.
6. Technical Assessment: resolution, compression artifacts, aspect ratio.

## Specific Feedback
- What lands?
- What specifically needs work?
- What would push this to 9/10?

## Overall Rating: X/10
Give the final score with clear reasoning.
```

## Comparison Analysis Prompt

```
Weigh these 3 variations against each other:

For each one:
1. Fit with [design direction]
2. Color effectiveness
3. Compositional strength
4. Text-overlay suitability
5. Professional quality (1-10)

Then:
- Ranking: best to worst, with reasons
- Recommendation: which to ship and why
- Hybrid suggestion: the best parts of each, combined
```

## Color Extraction Prompt

```
Pull the full palette from this image:

1. Name 5-8 dominant colors with hex codes
2. Sort each: primary, accent, neutral, or background
3. Propose CSS variable names (e.g., --color-primary-500)
4. Weigh accessibility (WCAG contrast ratios)
5. Say which colors suit text, backgrounds, accents

Hand it back as structured data ready for CSS.
```

## Integration Testing Prompt

```
Read this design asset with the UI laid over it:

1. Text Readability: can every line be read cleanly?
2. Contrast Issues: flag any WCAG violations
3. Visual Hierarchy: do the buttons and CTAs carry?
4. Spacing Problems: any crowding or tight breathing room?
5. Responsive Concerns: will it hold on mobile at 9:16?

Hand back specific adjustments.
```

## A/B Testing Prompt

```
A/B read:

Design A: [minimalist approach]
Design B: [maximalist approach]

Weigh them on:
1. Attention capture (first 3 seconds)
2. Clarity of the information hierarchy
3. Emotional impact and brand read
4. Conversion potential
5. Fit with the audience ([describe audience])

Recommend which to A/B test in production, and why.
```

## Quick Quality Check Template

```
Rate this asset 1-10 on:
1. Aesthetic quality
2. Color harmony
3. Compositional balance
4. Professional polish

Overall: X/10. Brief reasoning.
```

## Comprehensive Evaluation Template

```
Full design-asset evaluation:

## Aesthetic Alignment
- Target style: [describe]
- Actual style: [read it]
- Match quality: [1-10]

## Technical Quality
- Resolution: [assess]
- Compression: [check for artifacts]
- Aspect ratio: [verify]

## Color Analysis
- Dominant colors: [list hex codes]
- Harmony: [weigh it]
- Mood: [describe]

## Composition
- Balance: [read it]
- Focal points: [name them]
- Negative space: [weigh it]

## Integration Readiness
- Text overlay: [rate 1-10]
- UI compatibility: [assess]
- Responsive suitability: [weigh it]

Overall Score: X/10
Key Strengths: [list]
Improvements Needed: [list]
```
