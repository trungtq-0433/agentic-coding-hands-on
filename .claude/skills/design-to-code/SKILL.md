---
name: tkm:design-to-code
description: Turn a design, screenshot, or video into frontend code that honors the original — web components, 3D scenes, fast prototypes, immersive interfaces. Faithful to the source, refined in every detail, never papered over with generic defaults.
license: Complete terms in LICENSE.txt
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: design-frontend
triggers: ["redesign this", "make it look like", "replicate UI", "from screenshot", "from Figma", "pixel-perfect", "convert design to code", "thiết kế lại"]
---

A drawing of a chair is not a chair. The piece has to be made from the drawing — staying true to the original intent, exact in every measurement, refusing the shortcuts that quietly betray what the design was reaching for.

What this skill does is take a visual design and turn it into frontend code fit to ship. Code that actually runs. A craftsman's eye for aesthetic fidelity. None of the stock defaults, none of the tells that read as "AI slop."

**IMPORTANT**: The Design Thinking, Frontend Aesthetics Guidelines, Asset & Analysis References, and Anti-Patterns (AI Slop) sections below are the working rules of this bench. Read them, follow them — do not skip past them.

## Workflow Selection

The kind of input you start with decides the path you take:

| Input | Workflow | Reference |
|-------|----------|-----------|
| Screenshot | Replicate exactly | `./references/workflow-screenshot.md` |
| Video | Replicate with animations | `./references/workflow-video.md` |
| Screenshot/Video (describe only) | Document for devs | `./references/workflow-describe.md` |
| 3D/WebGL request | Three.js immersive | `./references/workflow-3d.md` |
| Quick task | Rapid implementation | `./references/workflow-quick.md` |
| Complex/award-quality | Full immersive | `./references/workflow-immersive.md` |
| Existing project upgrade | Redesign Audit | `./references/redesign-audit-checklist.md` |
| From scratch | Design Thinking below | - |

**Every path starts the same way**: bring up the `tkm:design-ui` skill FIRST for its design intelligence.

**Precedence:** Where the anti-slop rules below clash with a `tkm:design-ui` recommendation (Inter font, AI Purple palette, Lucide-only icons, and the like), take the alternative from `./references/anti-slop-rules.md` — unless the user asked for the conflicting choice on purpose.

## Screenshot/Video Replication (Quick Reference)

1. **Analyze** the source directly — Claude's vision reads the colors, fonts, spacing, and effects straight off the image/video
2. **Plan** the build in phases with the `ui-ux-designer` subagent
3. **Implement** — hold the result tight against the source
4. **Verify** — set it side by side with the original
5. **Document** — write findings into `./docs/design-guidelines.md` once approved

The individual workflow files carry the step-by-step detail.

## Design Dials

Three knobs steer the design decisions. Set them at the start of a session, or let the user turn them mid-conversation:

| Dial | Default | Range | Low (1-3) | High (8-10) |
|------|---------|-------|-----------|-------------|
| `DESIGN_VARIANCE` | 8 | 1-10 | Perfect symmetry, centered layouts, equal grids | Asymmetric, masonry, massive empty zones, fractional CSS Grid |
| `MOTION_INTENSITY` | 6 | 1-10 | CSS hover/active states only | Framer Motion scroll reveals, spring physics, perpetual micro-animations |
| `VISUAL_DENSITY` | 4 | 1-10 | Art gallery — huge whitespace, expensive/clean | Cockpit — tiny paddings, 1px dividers, monospace numbers everywhere |

**How they bite:** each setting triggers concrete rules. Above `DESIGN_VARIANCE` 4, centered heroes are worn out — push to split-screen or left-aligned instead. Above `MOTION_INTENSITY` 5, work in perpetual micro-animations. Above `VISUAL_DENSITY` 7, drop the generic cards and lean on spacing and dividers.

For a dial-driven SaaS dashboard build, see `./references/bento-motion-engine.md`.

## Design Thinking

Before a line of code, plant a flag on a BOLD aesthetic direction:
- **Purpose**: What is this interface for? Who sits in front of it?
- **Tone**: Go to an extreme and commit — brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian. The list is long. Use them as a springboard, then shape one that genuinely fits the direction.
- **Constraints**: The technical givens — framework, performance budget, accessibility.
- **Differentiation**: What makes this UNFORGETTABLE? The one thing a person walks away remembering?

**CRITICAL**: Settle on one clear conceptual direction and execute it cleanly. Loud maximalism and quiet minimalism both succeed — what separates good from forgettable is intent, not volume.

From there, write working code (HTML/CSS/JS, React, Vue, whatever fits) that is:
- Production-grade and functional
- Visually striking and memorable
- Coherent around a single point of view
- Finished down to the small details

## Frontend Aesthetics Guidelines

Where to put the attention:
- **Typography**: Reach for fonts with beauty and character. Skip the wallpaper fonts — Arial, Inter — and pick something with a voice that lifts the whole surface. Pair a distinctive display face with a refined body face.
- **Color & Theme**: Pick an aesthetic and stick to it. Drive it through CSS variables. A dominant color with one sharp accent beats a timid palette spread evenly across the page.
- **Motion**: Use animation for effect and for the small interactions. Favor CSS-only solutions in plain HTML; reach for the Motion library in React when it's available. Spend your motion budget on the high-impact moments — one well-choreographed page load with staggered reveals (animation-delay) lands harder than a scattering of micro-interactions. Use scroll triggers and hover states that catch people off guard.
- **Spatial Composition**: Layouts that surprise. Asymmetry. Overlap. Diagonal flow. Elements that break the grid. Either generous negative space or deliberate, controlled density.
- **Backgrounds & Visual Details**: Build atmosphere and depth instead of falling back on flat fills. Lay in effects and textures that fit the aesthetic — gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, grain overlays.

NEVER reach for the generic AI house style: the overused fonts (Inter, Roboto, Arial, system stacks), the tired color schemes (purple gradients on white above all), the predictable layouts and components, the cookie-cutter look with no character of its own.

Read the context and make choices that feel deliberately built for it. No two designs should land in the same place. Move between light and dark, between fonts, between aesthetics. NEVER let every generation drift toward the same safe pick (Space Grotesk, for one).

**IMPORTANT**: Let the code match the ambition of the vision. A maximalist design wants elaborate code, heavy on animation and effect. A minimal or refined one wants restraint — precise spacing, careful type, subtle touches. The elegance lives in executing the chosen vision fully.

**Remember:** Claude can do extraordinary creative work. Don't hold back — show what comes out of thinking past the obvious and committing all the way to a distinctive vision.

## Asset & Analysis References

| Task | Reference |
|------|-----------|
| Analyze quality | `./references/visual-analysis-overview.md` |
| Extract guidelines | `./references/design-extraction-overview.md` |
| Optimization | `./references/technical-overview.md` |
| Animations | `./references/animejs.md` |
| Magic UI (80+ components) | `./references/magicui-components.md` |
| Anti-slop forbidden patterns | `./references/anti-slop-rules.md` |
| Redesign audit checklist | `./references/redesign-audit-checklist.md` |
| Premium design patterns | `./references/premium-design-patterns.md` |
| Performance guardrails | `./references/performance-guardrails.md` |
| Bento motion engine (SaaS) | `./references/bento-motion-engine.md` |

## Anti-Patterns (AI Slop)

These are the LLM reflexes — reach for the alternative. Full rules: `./references/anti-slop-rules.md`

**Typography** — Steer off Inter/Roboto/Arial. Reach for: trending Google Fonts with Vietnamese glyph coverage, `Geist`, `Outfit`, `Cabinet Grotesk`, `Satoshi` (hunt for the best fit).

**Font size** — Keep input fields above 16px ALWAYS, so mobile browsers don't zoom on focus.

**Color** — Steer off the AI purple/blue gradient look, pure `#000000`, and oversaturated accents. Build on neutral bases with one considered accent.

**Layout** — Steer off 3-column equal card rows, centered heroes at high variance, and `h-screen`. Reach for asymmetric grids, split-screen, `min-h-[100dvh]`. Design mobile-first, not as an afterthought.

**Content** — Steer off "John Doe", "Acme Corp", round numbers, and the AI copy tics ("Elevate", "Seamless", "Unleash"). Use real-sounding names, messy real-world data, and plain specific language.

**Effects** — Steer off neon/outer glows, custom cursors, and gradient text on headers (unless asked). Reach for tinted inner shadows and spring physics.

**Components** — Steer off default unstyled shadcn, Lucide-only icon sets, and the generic card-border-shadow at high density. Always customize; try Phosphor/Heroicons; let spacing do the work cards were doing.

**Quick check:** Run the "AI Tells" list in `./references/anti-slop-rules.md` before you hand anything over.

**Performance:** Animation and blur rules live in `./references/performance-guardrails.md`.

Remember: Claude can do extraordinary creative work. Commit all the way to a distinctive vision.
