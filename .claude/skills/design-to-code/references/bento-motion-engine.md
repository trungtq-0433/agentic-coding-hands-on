# Bento 2.0 Motion Engine

A blueprint for modern SaaS dashboards and feature sections. It pushes past static cards toward a "Vercel-core meets Dribbble-clean" look where the motion never stops.

Reach for it when you're building: SaaS dashboards, feature showcase grids, marketing bento sections, product landing pages with interactive demos.

---

## Core Design Philosophy

**Aesthetic:** High-end, minimal, functional. Every card carries a pulse.

**Palette:**
- Background: `#f9fafb` (light) or `#050505` (dark)
- Cards: pure white `#ffffff` (light) / vantablack with `bg-white/5` (dark)
- Card borders: `border border-slate-200/50` (light) / `border border-white/10` (dark)

**Surfaces:**
- Every major container rides on `rounded-[2.5rem]`
- Diffusion shadow: `shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]` — depth without the clutter
- Titles and descriptions sit **outside and below** the card, gallery-style
- Inside the card: generous `p-8` or `p-10` padding

**Typography:**
- Font stack: `Geist`, `Satoshi`, or `Cabinet Grotesk` — nothing else
- Header tracking: `tracking-tight`
- Inter has no place in a Bento context

**Double-Bezel structure for premium cards:**
- Outer shell: `bg-black/5 ring-1 ring-black/5 p-1.5 rounded-[2rem]`
- Inner core: its own background + `shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)]` + `rounded-[calc(2rem-0.375rem)]`

---

## Animation Engine Specs

Every card MUST run **Perpetual Micro-Interactions**. The dashboard should never look frozen.

**Spring Physics (no linear easing):**
```js
// Use for all interactive elements
{ type: "spring", stiffness: 100, damping: 20 }
```

**Layout Transitions:**
- Lean on Framer Motion's `layout` and `layoutId` props for smooth reordering, resizing, and shared-element transitions

**Infinite Loops:**
- Each card holds an active state that loops forever: Pulse, Typewriter, Float, or Carousel

**Performance isolation (critical):**
- Wrap every perpetual animation in `React.memo`
- Pull each animated card out into its own isolated leaf `'use client'` component
- Never let it trigger a re-render up in the parent layout

**AnimatePresence:**
- Wrap every dynamic list so enter/exit animations actually fire

---

## Grid Structure

Standard layout: Row 1 = 3 columns | Row 2 = 2 columns (70/30 split)

```jsx
<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
  {/* Row 1: 3 equal cards */}
  <IntelligentListCard />
  <CommandInputCard />
  <LiveStatusCard />
</div>
<div className="grid grid-cols-1 md:grid-cols-[70%_30%] gap-6 mt-6">
  {/* Row 2: wide data stream + contextual UI */}
  <WideDataStreamCard />
  <ContextualUICard />
</div>
```

On mobile, everything folds down to `grid-cols-1` with `gap-6`. No horizontal overflow.

---

## The 5 Card Archetypes

### 1. Intelligent List
A vertical stack of items that auto-sorts on an endless loop.

- Items trade places via `layoutId` — reads like an AI re-prioritizing tasks in real time
- Smooth position swaps on roughly a 3s beat
- Spring-based position transitions give it weight and a physical feel
- Use case: task lists, priority queues, leaderboards

### 2. Command Input
A search/AI bar driven by a multi-step Typewriter Effect.

- Cycles through 3-5 involved prompts
- Cursor blinks between them
- "Processing" state: a shimmering loading gradient across the input
- On "completion": a quick checkmark before the next cycle starts
- Use case: AI search demos, command palette teasers

### 3. Live Status
A scheduling or status panel with indicators that breathe.

- Status dots on an endless `scale` pulse (`1.0 → 1.2 → 1.0`, 2s loop)
- A pop-up notification badge with overshoot spring: arrives, holds 3s, leaves
- Badge entrance: `scale: [0, 1.2, 1]` with overshoot spring physics
- Use case: scheduling UIs, monitoring dashboards, live-feed indicators

### 4. Wide Data Stream
A horizontal, infinite carousel of data cards or metrics.

- Seamless loop with `x: ["0%", "-50%"]` and duplicated items so it never breaks
- The speed feels effortless — neither rushed nor sluggish (~20-30s per full pass)
- Cards carry metrics, user avatars, status chips, mini sparklines
- Use case: social-proof logos, metric streams, activity feeds

### 5. Contextual UI (Focus Mode)
A document or content view that highlights itself and surfaces tools.

- Staggered highlight running through the text block (word/line by line, 300ms stagger)
- Once the highlight finishes, a floating action toolbar drifts in
- Toolbar entrance: `y: [20, 0]` + `opacity: [0, 1]` on a spring, micro-icons staggered
- Toolbar holds 3-5 action icons, each with its own hover state
- Use case: editor demos, AI annotation tools, document-review flows

---

## Pre-Flight Checklist

Before a Bento section goes out:

- [ ] Global state used only to dodge deep prop-drilling, not on a whim
- [ ] Mobile layout folds to a single column with `w-full px-4`
- [ ] Full-height sections use `min-h-[100dvh]`, never `h-screen`
- [ ] Every `useEffect` animation has a cleanup function
- [ ] Empty, loading, and error states present on each card
- [ ] Generic card borders replaced with spacing/dividers where it fits
- [ ] Each perpetual animation isolated in its own memoized Client Component
- [ ] No `window.addEventListener('scroll')` — use `whileInView` or `IntersectionObserver`
- [ ] No arbitrary z-index values
- [ ] `backdrop-blur` lives only on fixed/sticky elements, never on scrolling cards
