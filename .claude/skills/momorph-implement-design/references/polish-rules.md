# Polish Rules (Phase 4 — REQUIRED for web)

Apply AFTER the Phase 3 visual diff has passed. **Additive only**, DO NOT re-edit pixel-perfect UI. **Default-on for web stack** — orchestrator MUST run this phase before reporting the screen as done; do NOT wait for the user to ask.

## Scope

**DO:**
- Responsive (mobile/tablet/desktop) — viewport adaptation
- Hover / focus / pressed states for interactive elements
- Light transitions (200–300ms ease) for state changes
- Simple entrance animation (hero fade-in, mount-in section)

**DO NOT:**
- Redesign away from Figma (changing layout, colors, typography)
- Complex animation (parallax, scroll-jacking, GSAP timelines)
- Drag/swipe/gesture, advanced micro-interactions
- Business logic, validation messages, loading/skeleton states
- Advanced a11y (full ARIA roles, complex keyboard nav) — keep basic a11y only

## 1. Responsive (web)

### Breakpoint convention

Read project breakpoints first:
- Tailwind: `tailwind.config.{js,ts}` → `theme.screens`
- MUI: `theme.breakpoints`
- CSS variables: `:root { --bp-md: ... }`

If absent → default **mobile-first**:
- `< 640px` mobile, `≥ 768px` tablet, `≥ 1024px` desktop

### Common patterns

| Layout pattern | Mobile (< 768) | Tablet (768–1024) | Desktop (≥ 1024) |
|----------------|----------------|-------------------|------------------|
| Containered (max-width) | `padding-inline` 16–24px, max-width = 100% | max-width 720–960 | design max-width (e.g. 1200) |
| Multi-column grid (3–4 col) | 1 col stack | 2 col | 3–4 col |
| Horizontal nav | Hamburger / drawer | Hide some items | Full nav |
| Hero text (e.g. 56px) | scale ~32–40px | ~44px | keep design |
| Card grid | 1 col, smaller gap | 2 col | 3+ col |
| Side-by-side image+text | Stack vertical | May keep side-by-side | Side-by-side |

### Rules

1. **Mobile-first CSS** (with Tailwind) or **container queries** if the component is reusable.
2. Containers with `max-width: Npx` → on mobile become `width: 100%` + side padding (rule 3 Containered already covers this).
3. Large fonts (≥ 32px design) need to scale down on mobile to avoid overflow — use `clamp()` or breakpoint utilities.
4. Wide image/video → keep `width: 100%`, `height: auto`, `object-fit: cover`.
5. Don't hardcode fixed `width`/`height` on elements wider than 50% of the viewport.
6. Test at 3 viewports: **375px** (mobile), **768px** (tablet), **1280px** (desktop).

### When the design has mobile/tablet artboards

If the MoMorph file has a mobile frame (e.g. screenName contains "mobile" / width ~375) → use it as source of truth. Query MCP for that frame the same way as Phase 1, reconcile components per section. DO NOT guess dimensions.

## 2. Hover / Focus / Pressed states

### Elements that need state (web)

- **Button / CTA / button-like link** — must have hover + focus + pressed
- **Text link** — must have hover (color/underline) + focus visible
- **Clickable card** — hover (shadow lift or subtle scale) + focus visible (outline)
- **Input / textarea / select** — focus ring (or border-color shift) + invalid state if applicable
- **Icon button** — hover (background tint) + focus

### Default patterns (when Figma has no variant)

```css
/* Button primary */
.btn { transition: opacity 200ms ease, background-color 200ms ease; }
.btn:hover  { opacity: 0.9; }                   /* or darken bg 8–10% */
.btn:active { transform: translateY(1px); }
.btn:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }

/* Clickable card */
.card { transition: box-shadow 200ms ease, transform 200ms ease; }
.card:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.08); transform: translateY(-2px); }

/* Input */
.input:focus-visible { border-color: var(--primary); outline: none;
  box-shadow: 0 0 0 3px var(--primary-alpha-20); }
```

### When Figma provides variants (Default / Hover / Pressed / Focused)

Prefer those variants — query `mcp__momorph__query_component(name)` to find variants, apply exact styles. DO NOT guess.

### Forbidden

- Hover effects that **shift layout** (e.g. `padding` shift, `font-size` shift) → cause jumps.
- Hover-only critical functionality (mobile has no hover) — keep touch-friendly.
- `:hover` on non-interactive elements (regular text, layout containers).

## 3. Transition / Animation

### Defaults (safe)

- **Duration:** 150–300ms (fast interactions), 400–600ms (section entrance)
- **Easing:** `ease`, `ease-out` (entrance), `ease-in-out` (state change). Avoid `linear`.
- **Properties to animate:** `opacity`, `transform`, `background-color`, `border-color`, `box-shadow`, `color`. DO NOT animate `width`/`height`/`top`/`left` (causes reflow, lag).

### Entrance animation (optional, use sparingly)

- Hero / above-the-fold section: fade-in + subtle slide-up (12–24px) on mount.
- Lazy-loaded images: fade-in when loaded.
- DO NOT apply to every section (too many becomes noise).

### Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
```
Web stack MUST respect `prefers-reduced-motion`.

## 4. Stack-specific notes

### Tailwind

- Hover: `hover:opacity-90 hover:bg-primary/90`
- Focus: `focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring`
- Transition: `transition-all duration-200 ease-out`
- Responsive: `flex-col md:flex-row`, `text-3xl md:text-5xl`
- Avoid `transition-all` on heavy elements (large buttons) → name properties: `transition-[opacity,background-color]`.

### React Native / Flutter / SwiftUI / Compose

- Native mobile — skip hover (use pressed state).
- React Native: `Pressable` with `({ pressed }) => ...`.
- Flutter: `InkWell` / `GestureDetector` + `AnimatedContainer`.
- SwiftUI: `.scaleEffect(isPressed ? 0.98 : 1)` + `.animation(.easeInOut(duration: 0.2), value: isPressed)`.
- Responsive matters less (single device viewport), but support rotation + tablet.

## 5. Phase 4 workflow

1. Read pixel-perfect file list (from Phase 2/3 reports).
2. Scan interactive elements (button/link/card/input) — find ones missing states.
3. Apply default patterns or Figma variants.
4. Apply responsive breakpoint pattern matching the layout (containered / grid / hero).
5. Compile + visual check at 3 viewports (375 / 768 / 1280).
6. Report:
   - States added: [list element + state]
   - Responsive changes: [list breakpoint + change]
   - Anti-scope-creep: ✓ no redesign, no business logic
