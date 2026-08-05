# Immersive Design Workflow

Make award-quality designs — storytelling, 3D, and micro-interactions all in play.

## Prerequisites
- Bring up the `tkm:design-ui` skill first

## Initial Research
Run the `tkm:design-ui` searches:
```bash
python3 .claude/skills/design-ui/scripts/search.py "<product-type>" --domain product
python3 .claude/skills/design-ui/scripts/search.py "<style-keywords>" --domain style
python3 .claude/skills/design-ui/scripts/search.py "<mood>" --domain typography
python3 .claude/skills/design-ui/scripts/search.py "<industry>" --domain color
```

## Workflow Steps

### 1. Research Phase
Send the `researcher` subagent after:
- The design style and where the trends sit
- Font pairings and typography
- Color theory for the context
- Border and spacing patterns
- The principles of element positioning
- Animation and interaction patterns

### 2. Design Implementation
Use the `ui-ux-designer` subagent:
- Work up from the research, step by step
- Create the plan with the `## Naming` pattern
- Default to HTML/CSS/JS if unspecified

### 3. Storytelling Elements
Work in:
- A narrative that unfolds through scroll
- Emotional pacing
- Visual hierarchy for the story beats
- Progressive disclosure of the content

### 4. 3D Experiences
Where it fits, fold in:
- Three.js scenes
- Interactive 3D elements
- Parallax depth
- WebGL enhancements

### 5. Micro-interactions
Add the polish:
- Button feedback
- Form interactions
- Loading states
- Hover effects
- Scroll responses

### 6. Verify & Report
- Set it against the inspiration
- Report to the user
- Ask for approval
- Update `./docs/design-guidelines.md`

## Quality Standards
Aim at the award-winning tier:
- Dribbble top shots
- Behance featured
- Awwwards winners
- Mobbin patterns
- TheFWA selections

## Design Principles
- **Bold aesthetic choices**: commit fully to the direction
- **Attention to detail**: every pixel earns its place
- **Cohesive experience**: every element pulling together
- **Memorable moments**: make room for surprise and delight
- **Technical excellence**: performance and polish both

## Related
- `workflow-3d.md` — 3D implementation detail
- `animejs.md` — animation patterns
- `technical-best-practices.md` — quality guidelines
