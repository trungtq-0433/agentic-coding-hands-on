# Premium Design Patterns: Creative Arsenal

Draw from this library instead of falling back to generic UI. These are the patterns that make an interface striking and worth remembering.

> Framework note: the examples call out Framer Motion as one option for JS-driven patterns. GSAP/ThreeJS cover scroll storytelling just as well. Don't run both in the same component tree.

---

## Vibe Archetypes (Pick One Before Designing)

Plant the flag on a vibe before any code:

1. **Ethereal Glass** (SaaS / AI / Tech) — Deep OLED black `#050505`, radial mesh-gradient orbs drifting in back, vantablack cards under heavy `backdrop-blur-2xl`, wide geometric Grotesk type
2. **Editorial Luxury** (Lifestyle / Real Estate / Agency) — Warm creams `#FDFBF7`, muted sage, or deep espresso. A variable serif for the big headings, with a faint CSS noise/film-grain overlay for the feel of real paper
3. **Soft Structuralism** (Consumer / Health / Portfolio) — Silver-grey or pure white ground, massive bold Grotesk, airy floating components casting heavily diffused ambient shadows

---

## Navigation

- **Mac Dock Magnification** — Nav icons swell fluidly on hover with spring physics
- **Magnetic Button** — Buttons lean physically toward the cursor via `useMotionValue` + `useTransform`
- **Gooey Menu** — Sub-items peel off the main button like a viscous liquid
- **Dynamic Island** — A pill that morphs to surface status/alerts
- **Fluid Island Nav** — A floating glass pill detached from the top (`mt-6`, `mx-auto`, `rounded-full`). On mobile the hamburger lines rotate fluidly into an X
- **Contextual Radial Menu** — A circular menu blooming from the click point
- **Mega Menu Reveal** — Full-screen dropdowns that stagger-fade dense content into view
- **Floating Speed Dial** — A FAB that springs out into a curved arc of secondary actions

## Layout and Grids

- **Asymmetrical Bento** — A masonry-like CSS Grid of varying card sizes (`col-span-8 row-span-2` beside stacked `col-span-4` cards). Collapses to `grid-cols-1` on mobile
- **Z-Axis Cascade** — Elements stacked like real cards, slight overlap, varied depth. Drop the rotations below 768px
- **Editorial Split** — Massive type filling the left half, scrollable image pills or staggered cards on the right
- **Split Screen Scroll** — The two halves slide in opposite directions as you scroll
- **Curtain Reveal** — A hero parting down the middle like a curtain on scroll
- **Masonry Layout** — A staggered grid with no fixed row heights, Pinterest-style
- **Chroma Grid** — Grid borders or tiles carrying a slow, continuous color-gradient shift

## Cards and Containers

- **Double-Bezel (Doppelrand)** — Cards built like machined hardware: an outer shell (`bg-black/5`, `ring-1 ring-black/5`, `p-1.5`, `rounded-[2rem]`) wrapping an inner core with its own highlight and a concentric radius (`rounded-[calc(2rem-0.375rem)]`)
- **Parallax Tilt Card** — A 3D-tilting card tracking the mouse
- **Spotlight Border Card** — Borders that light up under the cursor
- **Glassmorphism Panel** — Real frosted glass: `backdrop-blur` + a 1px inner border (`border-white/10`) + an inner shadow (`shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`) to fake the edge refraction
- **Holographic Foil Card** — Iridescent rainbow reflections sliding around on hover
- **Tinder Swipe Stack** — A physical stack of cards to swipe away
- **Morphing Modal** — A button that grows seamlessly into a full-screen dialog

## Scroll Animations

- **Sticky Scroll Stack** — Cards that pin to the top and physically pile up as you scroll
- **Horizontal Scroll Hijack** — Vertical scroll redirected into a smooth horizontal gallery pan
- **Zoom Parallax** — A central background image zooming in and out seamlessly with scroll
- **Scroll Progress Path** — SVG lines drawing themselves as the user scrolls
- **Staggered Entry** — Elements cascading in with slight delays, Y-translation + opacity fade. Use `staggerChildren` in Framer Motion or CSS `animation-delay: calc(var(--index) * 100ms)`. Never mount it all at once

## Galleries and Media

- **Coverflow Carousel** — A 3D carousel, center in focus, edges angled back
- **Drag-to-Pan Grid** — A boundless grid you can drag freely in any direction
- **Accordion Image Slider** — Narrow strips that open up fully on hover
- **Hover Image Trail** — A trail of images popping and fading behind the cursor
- **Glitch Effect Image** — A brief RGB-channel shift, digital distortion on hover
- **Dome Gallery** — A 3D gallery with a panoramic dome feel

## Typography and Text

- **Kinetic Marquee** — Endless text bands that flip direction or speed up on scroll
- **Text Mask Reveal** — Massive type cut as a transparent window onto a video behind it
- **Text Scramble Effect** — Matrix-style character decoding on load or hover
- **Variable Font Animation** — Weight/width interpolating on scroll or hover so the text feels alive
- **Outlined-to-Fill Transition** — Text starting as a stroke outline, filling with color as it scrolls in
- **Circular Text Path** — Text bent along a spinning circular path
- **Kinetic Typography Grid** — A grid of letters that dodge or spin away from the cursor

## Micro-Interactions

- **Button-in-Button Trailing Icon** — An arrow nested in its own circular wrapper (`w-8 h-8 rounded-full bg-black/5`) flush against the button's inner right padding. Never a bare icon sitting next to text
- **Particle Explosion Button** — CTAs that burst into particles on success
- **Directional Hover-Aware Button** — The hover fill enters from whichever side the mouse came in from
- **Ripple Click Effect** — Waves rippling out from the exact click point
- **Skeleton Shimmer** — Light sliding across placeholder boxes. Match the layout's shape exactly
- **Tactile Press Feedback** — On `:active`, `scale(0.98)` or `translateY(1px)` to fake the physical push
- **Eyebrow Tags** — A microscopic pill badge above a major heading (`rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.2em]`)

## Surfaces and Effects

- **Grain/Noise Overlay** — A fixed `pointer-events-none` pseudo-element at `z-50`. Never on a scrolling container
- **Colored Tinted Shadows** — Shadows carrying the background hue rather than generic black
- **Mesh Gradient Background** — Organic, lava-lamp color blobs in motion
- **Lens Blur Depth** — Background layers blurring dynamically to push the foreground action forward
- **Animated SVG Line Drawing** — Vectors tracing their own contours in real time
