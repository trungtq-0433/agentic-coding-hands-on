# Screenshot Replication Workflow

Recreate a design exactly from a screenshot you're handed.

## Prerequisites
- Bring up the `tkm:design-ui` skill first for the design intelligence

## Workflow Steps

### 1. Read the Screenshot Details
Use the Read tool on the screenshot and pull:
- Design style and visual trends
- Font names (predict Google Fonts), sizes, weights
- The palette with exact hex codes
- Border radius and spacing patterns
- Element positions, sizes, shapes
- Textures, materials, lighting
- Shadows, reflections, blur, glow
- Background transparency and transitions
- Image treatments and effects

**Font Prediction**: Don't default to Inter/Poppins. Match what's actually on screen.

### 2. Create the Implementation Plan
Use the `ui-ux-designer` subagent:
- Create the plan directory (follow the `## Naming` pattern from hooks)
- Write `plan.md` (<80 lines, generic overview)
- Add `phase-XX-name.md` files carrying:
  - Context links, Overview, Key Insights
  - Requirements, Architecture, Related files
  - Implementation Steps, Todo list
  - Success Criteria, Risk Assessment

### 3. Implement
- Work the plan step by step
- Default to HTML/CSS/JS if no framework is named
- Hold it tight against the screenshot

### 4. Verify & Report
- Set the result next to the screenshot
- Summarize the changes for the user
- Ask for approval

### 5. Document
Once approved, update `./docs/design-guidelines.md`

## Quality Standards
- Match the screenshot to the pixel where you can
- Keep the whole visual hierarchy intact
- Hold the exact spacing and proportions
- Reproduce any animation visible in the source

## Related
- `design-extraction-overview.md` — extract design guidelines
- `extraction-prompts.md` — detailed analysis prompts
- `visual-analysis-overview.md` — verify quality
