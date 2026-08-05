# Video Replication Workflow

Recreate a design from a video, animations and interactions included.

## Prerequisites
- Bring up the `tkm:design-ui` skill first

## Workflow Steps

### 1. Read the Video Details
Read the video frames with the Read tool and describe:
- Every visible element and its properties
- All interactions and user flows
- Animation timing, easing, duration
- Transitions between states/pages
- The palette with hex codes
- Typography (predict Google Fonts)
- Borders, spacing, sizing
- Textures, materials, lighting
- Shadows, reflections, blur, glow
- Background effects

**Font Prediction**: Don't default to Inter/Poppins.

### 2. Create the Implementation Plan
Use the `ui-ux-designer` subagent:
- Create the plan directory (follow the `## Naming` pattern)
- Write `plan.md` (<80 lines overview)
- Add `phase-XX-name.md` files with the full sections
- Keep research reports under 150 lines

### 3. Implement
- Work the plan step by step
- Default to HTML/CSS/JS if unspecified
- Put the accuracy into the animation

### 4. Animation Implementation
Where to focus:
- Timing functions that match the video
- State transitions
- Micro-interactions
- Scroll-triggered effects
- Hover/focus states
- Loading animations

Lean on the `animejs.md` reference for animation patterns.

### 5. Verify & Report
- Set the result next to the video
- Exercise every interaction
- Summarize for the user
- Ask for approval

### 6. Document
Once approved, update `./docs/design-guidelines.md`

## Quality Standards
- Frame-accurate animation timing
- Smooth 60fps
- Responsive behavior preserved
- Every interaction working

## Related
- `animejs.md` — animation library reference
- `design-extraction-overview.md` — guidelines extraction
