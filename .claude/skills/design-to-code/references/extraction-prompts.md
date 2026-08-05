# Extraction Prompt Templates

Ready-to-use prompts for pulling design guidelines out of a reference.

## Comprehensive Design Analysis Prompt

```
Read full design guidelines off this interface:

## Aesthetic Identification
- Design Style: name the movement at work (minimalism, brutalism, maximalism, glassmorphism, neo-brutalism, organic, luxury, editorial, etc.)
- Overall Mood: professional, playful, serious, energetic, calm, bold, refined
- Differentiation Factor: what makes this one stick in memory?

## Typography System
- Display Font: best guess at the family (lean toward Google Fonts: Playfair Display, Bebas Neue, DM Serif, Archivo Black, etc.). Offer 2-3 backups if unsure.
- Body Font: name it or suggest near matches
- Font Sizes: rough px for h1, h2, h3, body, small text
- Font Weights: which weights appear (300, 400, 500, 600, 700)
- Line Heights: estimate the leading ratios
- Letter Spacing: tight, normal, or wide tracking

## Color System (CRITICAL)
- Pull 8-12 distinct colors with accurate hex codes
- Sort them: Primary (1-2), Secondary (1-2), Accent (2-3), Neutral/Gray (3-5), Background (1-2)
- Note how the colors relate and where each gets used
- Flag any gradients (give start/end hex and direction)

## Spatial Composition
- Layout Type: grid-based, asymmetric, centered, multi-column, magazine-style
- Grid System: estimate columns and gutter widths
- Spacing Scale: read the rhythm (4px, 8px, 16px, 24px, etc.)
- White Space Strategy: generous, tight, varied
- Section Hierarchy: how the content is ordered and ranked

## Visual Elements
- Border Styles: radius values (sharp, lightly rounded, fully rounded)
- Shadows: box-shadow character (elevation, spread, blur)
- Backgrounds: solid, gradients, patterns, textures, images
- Effects: blur, overlays, transparency, grain, noise
- Decorative Elements: lines, shapes, illustrations, icons

## Component Patterns
- Button Styles: shape, size, states, hover behavior
- Card Design: borders, shadows, padding, content layout
- Navigation: style, position, behavior
- Forms: input styling, validation, spacing
- Interactive Elements: hover states, transitions

## Motion & Animation (if video)
- Transition Timing: fast (100-200ms), medium (200-400ms), slow (400-600ms+)
- Easing Functions: linear, ease-out, ease-in, specific cubic-bezier
- Animation Types: fade, slide, scale, rotate, stagger
- Scroll Interactions: parallax, reveal-on-scroll, sticky elements

## Accessibility Considerations
- Color Contrast: weigh the text/background pairings
- Font Sizes: the smallest sizes in use
- Interactive Targets: button/link sizes
- Visual Hierarchy: is the content clearly ranked

## Design Highlights
- The 3 standout decisions
- Why the design works
- What could be pushed further

Hand it back as structured markdown for easy reference.
```

## Multi-Screen System Extraction Prompt

```
Work across these screens to recover the shared design system:

Per screen:
1. Spot the consistent tokens (colors, typography, spacing)
2. Note the variations and why they exist
3. Pull out the reusable component patterns

Then bring it together:
- Core design system: shared colors, fonts, spacing scales
- Component library: buttons, cards, navigation, forms
- Layout patterns: grid systems, responsive behavior
- Visual language: the aesthetic principles in common
- Design tokens: recommend the CSS variables

Hand back a single unified design-system spec.
```

## Motion Design Extraction Prompt

```
Work through this video to recover the motion guidelines:

1. Transition Timing: time the key animations (in ms)
2. Easing Curves: describe the accel/decel (ease-in, ease-out, spring)
3. Animation Types: list every style in play
4. Micro-interactions: button hovers, form focus, feedback
5. Page Transitions: how the screens hand off
6. Scroll Interactions: parallax, sticky headers, reveals
7. Loading States: skeletons, spinners, progressive reveals
8. Stagger Effects: the sequential delays and their pattern

Hand back implementable specs with real timing values.
```

## Competitive Analysis Prompt

```
Side-by-side design read of 3 competitors:

Per competitor:
1. Design style and aesthetic approach
2. Color strategy and brand read
3. Typography choices and hierarchy
4. Layout and information architecture
5. The one or two unique elements
6. Strengths and weaknesses

Synthesis:
- Common industry patterns (what everyone does)
- Differentiation openings (the gaps to exploit)
- Best practices on display (the proven moves)
- Design recommendations (how to stand apart)

Hand back a strategic design direction grounded in the read.
```
