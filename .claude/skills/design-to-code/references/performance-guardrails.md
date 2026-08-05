# Performance Guardrails

The rules that keep animation and rendering smooth. Follow them and you sidestep the usual sources of mobile frame drops and layout thrashing.

---

## GPU-Safe Animations

**Animate only these:**
- `transform` (translate, scale, rotate)
- `opacity`

**Never animate:**
- `top`, `left`, `right`, `bottom` — forces a layout reflow
- `width`, `height` — forces layout + paint
- `margin`, `padding` — forces layout
- `background-color` — forces paint (fine for a one-off color transition, but keep it off anything animating constantly)

**Why:** `transform` and `opacity` get composited on the GPU and skip layout and paint entirely. Everything else makes the browser recompute layout on every frame — which is brutal on mobile.

```css
/* Good */
.card { transform: translateY(0); transition: transform 300ms; }
.card:hover { transform: translateY(-4px); }

/* Bad */
.card { top: 0; transition: top 300ms; }
.card:hover { top: -4px; }
```

---

## Blur Constraints

**Put `backdrop-blur` only on:**
- Fixed-position elements (sticky navbars, overlays)
- Modals and dialogs
- Anything that doesn't scroll with the content

**Never blur:**
- Scrolling containers
- Large content areas
- Anything inside an `overflow: auto/scroll` parent

**Why:** `backdrop-blur` re-composites on the GPU every single scroll frame. On a scrolling list of 20+ cards, that tanks the frame rate on mid- and low-end phones.

```css
/* Good — fixed nav */
.navbar { position: fixed; backdrop-filter: blur(12px); }

/* Bad — scrolling card list */
.card-list .card { backdrop-filter: blur(8px); } /* kills mobile perf */
```

---

## Grain and Noise Overlays

**The right way:**
```css
/* Fixed, pointer-events-none pseudo-element only */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 50;
  pointer-events: none;
  background-image: url("data:image/svg+xml,..."); /* or CSS noise */
  opacity: 0.03;
}
```

**Never hang grain/noise on:**
- Scrolling containers
- Individual cards or sections
- Anything with `position: relative` inside a scroll context

---

## Z-Index Discipline

**Use named layers only. Set a scale in your theme/variables:**

```css
:root {
  --z-base: 0;
  --z-card: 10;
  --z-sticky: 100;
  --z-overlay: 200;
  --z-modal: 300;
  --z-tooltip: 400;
  --z-notification: 500;
}
```

**Never:**
- Drop in arbitrary values like `z-[9999]` or an unprompted `z-50`
- Stack z-indexes with no documented reason
- Use z-index to paper over a stacking issue you don't understand

---

## Framer Motion Performance

**Use `useMotionValue` + `useTransform` for continuous animation:**
```jsx
// Good — runs outside React render cycle
const mouseX = useMotionValue(0);
const rotateY = useTransform(mouseX, [-300, 300], [-15, 15]);

// Bad — triggers re-render on every mouse move
const [rotation, setRotation] = useState(0);
```

**For perpetual/infinite animation:**
- Wrap it in `React.memo` so the parent doesn't re-render
- Pull it out as an isolated leaf client component
- Use `<AnimatePresence>` for enter/exit — never conditionally render without it

**For scroll-driven reveals:**
- Use `whileInView` or `IntersectionObserver`
- Never `window.addEventListener('scroll')` — it reflows continuously

**For staggered children:**
- The parent `variants` and the children MUST live in the same Client Component tree
- If the data is async, pass it as props into one centralized parent motion wrapper

---

## RSC Safety (Next.js)

- Global state (Context, providers) works **only** in Client Components
- Wrap providers in a `"use client"` component
- Any section using Framer Motion or an interactive hook becomes its own isolated leaf component with `'use client'` up top
- Server Components render the static layout, nothing more

---

## Mobile Override Rules

For any asymmetric or complex layout, fall back hard below 768px:

```jsx
// All asymmetric layouts collapse to single column
<div className="grid grid-cols-1 md:grid-cols-[2fr_1fr_1fr] gap-6">
```

- Strip the rotations, negative margins, and overlaps below `md:`
- Swap `h-screen` for `min-h-[100dvh]` — stops the iOS Safari viewport from jumping
- Don't put `overflow: hidden` on `html`/`body` without testing on a real phone
- Check horizontal scroll — asymmetric layouts love to leak x-overflow on small screens

---

## `will-change` Guidance

Use it sparingly. `will-change: transform` tells the browser to promote the element to its own GPU layer:

- Apply it only to elements that are **actively animating**
- Drop it once the animation finishes (or scope it to `:hover`)
- Never apply it globally — that piles up GPU memory pressure

```css
/* Good — scoped to hover state */
.card:hover { will-change: transform; }

/* Bad — always promoted */
.card { will-change: transform; }
```
