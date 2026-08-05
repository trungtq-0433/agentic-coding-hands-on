# Design Description Workflow

Turn a screenshot or video into detailed design docs a developer can work from.

## Prerequisites
- Bring up the `tkm:design-ui` skill first

## Workflow Steps

### 1. Comprehensive Visual Analysis
Use the Read tool on the screenshot/image and describe it exhaustively:

**Layout & Structure**
- Element positions (absolute coords or relative)
- Container hierarchy
- Grid/flexbox patterns
- Any responsive breakpoints visible

**Visual Properties**
- Design style and aesthetic trend
- Every color with hex codes
- Every border (width, style, radius)
- Every icon (describe or identify)
- Font names (predict Google Fonts), sizes, weights
- Line heights, letter spacing

**Spacing System**
- Padding values
- Margin values
- Gaps between elements
- Section spacing

**Visual Effects**
- Shapes and geometry
- Textures and materials
- Lighting direction
- Shadows (offset, blur, spread, color)
- Reflections and refractions
- Blur effects (backdrop, gaussian)
- Glow effects
- Background transparency
- Image treatments

**Interactions (if video)**
- Animation sequences
- Transition types and timing
- Hover/focus states
- Scroll behaviors

**Font Prediction**: Match the real fonts; skip the Inter/Poppins reflex.

### 2. Create the Implementation Plan
Use the `ui-ux-designer` subagent:
- Create the plan directory (follow the `## Naming` pattern)
- Write `plan.md` overview (<80 lines)
- Add detailed `phase-XX-name.md` files

### 3. Report to the User
Hand back documentation ready to work from:
- A summary of the design system
- The component breakdown
- The technical specs
- A suggested way in

## Output Format

```markdown
# Design Analysis: [Name]

## Design System
- **Style**: [aesthetic direction]
- **Colors**: [palette with hex]
- **Typography**: [fonts, sizes, weights]
- **Spacing Scale**: [values]

## Component Breakdown
1. [Component] - [specs]
2. [Component] - [specs]

## Implementation Notes
- [Technical considerations]
```

## Related
- `extraction-prompts.md` — detailed prompts
- `extraction-output-templates.md` — output formats
