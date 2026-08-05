# 3D Design Workflow

Make immersive, interactive 3D designs with Three.js.

## Prerequisites
- Bring up the `tkm:design-ui` skill first

## Initial Research
Run the `tkm:design-ui` searches:
```bash
python3 .claude/skills/design-ui/scripts/search.py "<product-type>" --domain product
python3 .claude/skills/design-ui/scripts/search.py "immersive 3d" --domain style
python3 .claude/skills/design-ui/scripts/search.py "animation" --domain ux
```

## Workflow Steps

### 1. Create the Implementation Plan
Use the `ui-ux-designer` + `researcher` subagents:
- Create the plan directory (follow the `## Naming` pattern)
- Write `plan.md` (<80 lines overview)
- Add the `phase-XX-name.md` files
- Keep research reports under 150 lines

### 2. Implement with Three.js
Hand the `ui-ux-designer` subagent the construction of:
- The Three.js scene setup
- Custom GLSL shaders
- GPU particle systems
- Cinematic camera controls
- Post-processing effects
- The interactive elements

### 3. Verify & Report
- Test across devices
- Tune for 60fps
- Report to the user
- Ask for approval

### 4. Document
Update `./docs/design-guidelines.md` with:
- The 3D design patterns
- The shader libraries
- The reusable components

## Technical Requirements

### Three.js Implementation
- Proper scene optimization
- Efficient draw calls
- LOD (Level of Detail) where it earns its place
- Responsive canvas behavior
- Memory management

### Shader Development
- Custom vertex shaders
- Custom fragment shaders
- Uniform management
- Performance optimization

### Particle Systems
- GPU-accelerated rendering
- Efficient buffer geometry
- Point sprite optimization

### Post-Processing
- Render pipeline setup
- Effect composition
- Performance budgeting

## Implementation Stack
- Three.js — 3D rendering
- GLSL — custom shaders
- HTML/CSS/JS — UI integration
- WebGL — GPU graphics

## Performance Targets
- 60fps floor
- < 100ms initial load
- Responsive to the viewport
- Mobile-friendly fallbacks

## Related
- `animejs.md` — UI animation patterns
