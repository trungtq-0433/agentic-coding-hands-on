---
name: tkm:design-ui
description: "UI/UX design intelligence for web and mobile — 50+ styles, 161 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types across React, Next.js, Vue, Svelte, SwiftUI, Flutter, Tailwind, shadcn/ui, and HTML/CSS. Activate before designing or building any interface."
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
module: design-frontend
triggers: ["design from scratch", "choose colors", "pick fonts", "design system", "what style should", "UX guidelines", "create UI from idea"]
---

# The Aesthetic Forge

Look is structure, not garnish. The first color a person sees, the reach of a tap target, the beat of a transition — every one of these is a call that either builds trust or quietly burns it. A craftsman at this bench does not chase "pretty." They shape interfaces that work well first: reachable, deliberate, visibly thought-through.

The bench is stocked: 50+ styles, 161 color palettes, 57 font pairings, 161 product types with reasoning rules, 99 UX guidelines, and 25 chart types across 10 technology stacks.

## When to Apply

Reach for this Skill whenever the work touches **UI structure, visual design calls, interaction patterns, or experience quality control**.

### Must Use

Treat the Skill as mandatory in cases like these:

- Laying out new pages — Landing Page, Dashboard, Admin, SaaS, Mobile App
- Building or reworking UI components — buttons, modals, forms, tables, charts, and the rest
- Settling on color schemes, type systems, spacing standards, or layout systems
- Auditing UI code for experience, accessibility, or visual consistency
- Wiring up navigation structures, animations, or responsive behavior
- Calling product-level design decisions — style, information hierarchy, brand expression
- Sharpening the perceived quality, clarity, or usability of an interface

### Recommended

The Skill earns its keep in these softer cases too:

- The UI reads as "not quite professional," but the cause won't name itself
- Usability or experience feedback has landed and needs acting on
- Tightening UI quality ahead of launch
- Keeping a design coherent across Web / iOS / Android
- Standing up design systems or shared component libraries

### Skip

Leave the Skill on the shelf when none of the above applies:

- Backend logic on its own
- Work confined to API or database design
- Performance tuning with no bearing on the interface
- Infrastructure or DevOps tasks
- Non-visual scripts and automation

**The test**: if the change alters how a feature **looks, feels, moves, or responds to touch**, the Skill belongs in the loop.

## Rule Categories by Priority

*Reference for humans and AI alike: work the priorities 1→10 to decide which category deserves attention first; reach for `--domain <Domain>` to pull the details when you need them. The scripts ignore this table.*

| Priority | Category | Impact | Domain | Key Checks (Must Have) | Anti-Patterns (Avoid) |
|----------|----------|--------|--------|------------------------|------------------------|
| 1 | Accessibility | CRITICAL | `ux` | Contrast 4.5:1, Alt text, Keyboard nav, Aria-labels | Removing focus rings, Icon-only buttons without labels |
| 2 | Touch & Interaction | CRITICAL | `ux` | Min size 44×44px, 8px+ spacing, Loading feedback | Reliance on hover only, Instant state changes (0ms) |
| 3 | Performance | HIGH | `ux` | WebP/AVIF, Lazy loading, Reserve space (CLS &lt; 0.1) | Layout thrashing, Cumulative Layout Shift |
| 4 | Style Selection | HIGH | `style`, `product` | Match product type, Consistency, SVG icons (no emoji) | Mixing flat & skeuomorphic randomly, Emoji as icons |
| 5 | Layout & Responsive | HIGH | `ux` | Mobile-first breakpoints, Viewport meta, No horizontal scroll | Horizontal scroll, Fixed px container widths, Disable zoom |
| 6 | Typography & Color | MEDIUM | `typography`, `color` | Base 16px, Line-height 1.5, Semantic color tokens | Text &lt; 12px body, Gray-on-gray, Raw hex in components |
| 7 | Animation | MEDIUM | `ux` | Duration 150–300ms, Motion conveys meaning, Spatial continuity | Decorative-only animation, Animating width/height, No reduced-motion |
| 8 | Forms & Feedback | MEDIUM | `ux` | Visible labels, Error near field, Helper text, Progressive disclosure | Placeholder-only label, Errors only at top, Overwhelm upfront |
| 9 | Navigation Patterns | HIGH | `ux` | Predictable back, Bottom nav ≤5, Deep linking | Overloaded nav, Broken back behavior, No deep links |
| 10 | Charts & Data | LOW | `chart` | Legends, Tooltips, Accessible colors | Relying on color alone to convey meaning |

## Quick Reference

Full per-category rule catalogs (Accessibility, Touch, Performance, Style, Layout, Typography, Animation, Forms, Navigation, Charts): `references/ux-quick-reference.md`

## How to Use

Query individual domains with the CLI tool below.

---

## Prerequisites

Confirm Python is on the machine:

```bash
python3 --version || python --version
```

If it isn't, install it for the user's OS:

**macOS:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3
```

**Windows:**
```powershell
winget install Python.Python.3.12
```

---

## How to Use This Skill

Reach for the skill when a request lands in any of these lanes:

| Scenario | Trigger Examples | Start From |
|----------|-----------------|------------|
| **New project / page** | "Build a landing page", "Build a dashboard" | Step 1 → Step 2 (design system) |
| **New component** | "Create a pricing card", "Add a modal" | Step 3 (domain search: style, ux) |
| **Choose style / color / font** | "What style fits a fintech app?", "Recommend a color palette" | Step 2 (design system) |
| **Review existing UI** | "Review this page for UX issues", "Check accessibility" | Quick Reference checklist above |
| **Fix a UI bug** | "Button hover is broken", "Layout shifts on load" | Quick Reference → relevant section |
| **Improve / optimize** | "Make this faster", "Improve mobile experience" | Step 3 (domain search: ux, react) |
| **Implement dark mode** | "Add dark mode support" | Step 3 (domain: style "dark mode") |
| **Add charts / data viz** | "Add an analytics dashboard chart" | Step 3 (domain: chart) |
| **Stack best practices** | "React performance tips"、"SwiftUI navigation" | Step 4 (stack search) |

Work the bench in this order:

### Step 1: Analyze User Requirements

Pull the key facts out of the request:
- **Product type**: Entertainment (social, video, music, gaming), Tool (scanner, editor, converter), Productivity (task manager, notes, calendar), or hybrid
- **Target audience**: C-end consumer users; weigh age group and usage context (commute, leisure, work)
- **Style keywords**: playful, vibrant, minimal, dark mode, content-first, immersive, etc.
- **Stack**: React Native (this project's only tech stack)

### Step 2: Generate Design System (REQUIRED)

**Open with `--design-system` every time** — it returns full recommendations with the reasoning attached:

```bash
python3 skills/design-ui/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

What it does:
1. Runs the domains in parallel (product, style, color, landing, typography)
2. Feeds the matches through the reasoning rules in `ui-reasoning.csv` to pick the best fit
3. Hands back the whole design system: pattern, style, colors, typography, effects
4. Names the anti-patterns to stay clear of

**Example:**
```bash
python3 skills/design-ui/scripts/search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### Step 2b: Persist Design System (Master + Overrides Pattern)

To keep the design system around for **hierarchical retrieval across sessions**, tack on `--persist`:

```bash
python3 skills/design-ui/scripts/search.py "<query>" --design-system --persist -p "Project Name"
```

That lays down:
- `design-system/MASTER.md` — the global source of truth, holding every design rule
- `design-system/pages/` — the folder where page-specific overrides go

**With a page-specific override:**
```bash
python3 skills/design-ui/scripts/search.py "<query>" --design-system --persist -p "Project Name" --page "dashboard"
```

That adds:
- `design-system/pages/dashboard.md` — where this page parts ways with the Master

**How hierarchical retrieval works:**
1. Building a given page (say "Checkout"), look first at `design-system/pages/checkout.md`
2. If that page file is there, its rules **win over** the Master
3. If it isn't, the rules in `design-system/MASTER.md` stand alone

**Context-aware retrieval prompt:**
```
I am building the [Page Name] page. Please read design-system/MASTER.md.
Also check if design-system/pages/[page-name].md exists.
If the page file exists, prioritize its rules.
If not, use the Master rules exclusively.
Now, generate the code...
```

### Step 3: Supplement with Detailed Searches (as needed)

Once the design system is in hand, drill into a domain whenever you need more detail:

```bash
python3 skills/design-ui/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

**When a detailed search earns its place:**

| Need | Domain | Example |
|------|--------|---------|
| Product type patterns | `product` | `--domain product "entertainment social"` |
| More style options | `style` | `--domain style "glassmorphism dark"` |
| Color palettes | `color` | `--domain color "entertainment vibrant"` |
| Font pairings | `typography` | `--domain typography "playful modern"` |
| Chart recommendations | `chart` | `--domain chart "real-time dashboard"` |
| UX best practices | `ux` | `--domain ux "animation accessibility"` |
| Alternative fonts | `typography` | `--domain typography "elegant luxury"` |
| Individual Google Fonts | `google-fonts` | `--domain google-fonts "sans serif popular variable"` |
| Landing structure | `landing` | `--domain landing "hero social-proof"` |
| React Native perf | `react` | `--domain react "rerender memo list"` |
| App interface a11y | `web` | `--domain web "accessibilityLabel touch safe-areas"` |
| AI prompt / CSS keywords | `prompt` | `--domain prompt "minimalism"` |

### Step 4: Stack Guidelines (React Native)

Pull the React Native implementation-specific best practices:

```bash
python3 skills/design-ui/scripts/search.py "<keyword>" --stack react-native
```

---

## Search Reference

### Available Domains

| Domain | Use For | Example Keywords |
|--------|---------|------------------|
| `product` | Product type recommendations | SaaS, e-commerce, portfolio, healthcare, beauty, service |
| `style` | UI styles, colors, effects | glassmorphism, minimalism, dark mode, brutalism |
| `typography` | Font pairings, Google Fonts | elegant, playful, professional, modern |
| `color` | Color palettes by product type | saas, ecommerce, healthcare, beauty, fintech, service |
| `landing` | Page structure, CTA strategies | hero, hero-centric, testimonial, pricing, social-proof |
| `chart` | Chart types, library recommendations | trend, comparison, timeline, funnel, pie |
| `ux` | Best practices, anti-patterns | animation, accessibility, z-index, loading |
| `google-fonts` | Individual Google Fonts lookup | sans serif, monospace, japanese, variable font, popular |
| `react` | React/Next.js performance | waterfall, bundle, suspense, memo, rerender, cache |
| `web` | App interface guidelines (iOS/Android/React Native) | accessibilityLabel, touch targets, safe areas, Dynamic Type |
| `prompt` | AI prompts, CSS keywords | (style name) |

### Available Stacks

| Stack | Focus |
|-------|-------|
| `react-native` | Components, Navigation, Lists |

---

## Example Workflow

**User request:** "Make an AI search homepage."

### Step 1: Analyze Requirements
- Product type: Tool (AI search engine)
- Target audience: C-end users after fast, intelligent search
- Style keywords: modern, minimal, content-first, dark mode
- Stack: React Native

### Step 2: Generate Design System (REQUIRED)

```bash
python3 skills/design-ui/scripts/search.py "AI search tool modern minimal" --design-system -p "AI Search"
```

**Output:** the full design system — pattern, style, colors, typography, effects, and anti-patterns.

### Step 3: Supplement with Detailed Searches (as needed)

```bash
# Get style options for a modern tool product
python3 skills/design-ui/scripts/search.py "minimalism dark mode" --domain style

# Get UX best practices for search interaction and loading
python3 skills/design-ui/scripts/search.py "search loading animation" --domain ux
```

### Step 4: Stack Guidelines

```bash
python3 skills/design-ui/scripts/search.py "list performance navigation" --stack react-native
```

**Then:** fold the design system and the detailed searches together, and build the design.

---

## Output Formats

`--design-system` writes out in two shapes:

```bash
# ASCII box (default) - best for terminal display
python3 skills/design-ui/scripts/search.py "fintech crypto" --design-system

# Markdown - best for documentation
python3 skills/design-ui/scripts/search.py "fintech crypto" --design-system -f markdown
```

---

## Tips for Better Results

### Query Strategy

- Stack the keywords **across dimensions** — product + industry + tone + density: `"entertainment social vibrant content-dense"`, not a lone `"app"`
- Rephrase the same intent a few ways: `"playful neon"` → `"vibrant dark"` → `"content-first minimal"`
- Lead with `--design-system` for the full picture, then `--domain` to dig into any dimension you're unsure of
- Always pass `--stack react-native` for implementation-specific guidance

### Common Sticking Points

| Problem | What to Do |
|---------|------------|
| Can't decide on style/color | Re-run `--design-system` with different keywords |
| Dark mode contrast issues | Quick Reference §6: `color-dark-mode` + `color-accessible-pairs` |
| Animations feel unnatural | Quick Reference §7: `spring-physics` + `easing` + `exit-faster-than-enter` |
| Form UX is poor | Quick Reference §8: `inline-validation` + `error-clarity` + `focus-management` |
| Navigation feels confusing | Quick Reference §9: `nav-hierarchy` + `bottom-nav-limit` + `back-behavior` |
| Layout breaks on small screens | Quick Reference §5: `mobile-first` + `breakpoint-consistency` |
| Performance / jank | Quick Reference §3: `virtualize-lists` + `main-thread-budget` + `debounce-throttle` |

### Pre-Delivery Checklist

- Run `--domain ux "animation accessibility z-index loading"` as a UX pass before you build
- Walk Quick Reference **§1–§3** (CRITICAL + HIGH) as the final review
- Try it at 375px (small phone) and in landscape
- Check it with **reduced-motion** on and **Dynamic Type** cranked to its largest
- Verify dark mode contrast on its own — don't trust the light-mode values to carry over
- Confirm every touch target ≥44pt and nothing tucked behind a safe area

---

## Common Rules for Professional UI

The slips below are the ones that quietly make a UI read as amateur:
Scope notice: these rules cover App UI (iOS/Android/React Native/Flutter), not desktop-web interaction patterns.

### Icons & Visual Elements

| Rule | Standard | Avoid | Why It Matters |
|------|----------|--------|----------------|
| **No Emoji as Structural Icons** | Reach for vector icons (e.g., Lucide, react-native-vector-icons, @expo/vector-icons). | Wiring emojis (🎨 🚀 ⚙️) into navigation, settings, or system controls. | Emojis ride on the font, drift across platforms, and slip past your design tokens. |
| **Vector-Only Assets** | SVG or platform vector icons that scale clean and take a theme. | Raster PNG icons that go blurry or pixelated. | Keeps assets scalable, crisp, and ready for dark/light mode. |
| **Stable Interaction States** | Express press states with color, opacity, or elevation — never by moving the layout bounds. | Layout-shifting transforms that nudge neighboring content or jitter. | Keeps interactions steady and the motion/perceived quality smooth on mobile. |
| **Correct Brand Logos** | Pull official brand assets and follow their usage rules (spacing, color, clear space). | Guessing at logo paths, recoloring off-book, or warping proportions. | Stays clear of brand misuse and keeps you legal/platform-compliant. |
| **Consistent Icon Sizing** | Pin icon sizes to design tokens (e.g., icon-sm, icon-md = 24pt, icon-lg). | Scattering arbitrary values like 20pt / 24pt / 28pt. | Holds rhythm and visual hierarchy across the interface. |
| **Stroke Consistency** | One stroke width per visual layer (e.g., 1.5px or 2px). | Mixing thick and thin strokes at random. | Mismatched strokes drain the polish and cohesion right out of a UI. |
| **Filled vs Outline Discipline** | One icon style per hierarchy level. | Filled and outline icons sharing a hierarchy level. | Keeps the meaning clear and the style coherent. |
| **Touch Target Minimum** | A 44×44pt interactive area at minimum (reach for hitSlop when the icon is smaller). | Small icons with no expanded tap area. | Clears the accessibility and platform usability bar. |
| **Icon Alignment** | Sit icons on the text baseline with even padding. | Icons off-baseline or padded unevenly. | Heads off the subtle imbalance that chips away at perceived quality. |
| **Icon Contrast** | Meet WCAG contrast: 4.5:1 for small elements, 3:1 floor for larger UI glyphs. | Low-contrast icons that vanish into the background. | Keeps icons legible in both light and dark modes. |


### Interaction (App)

| Rule | Do | Don't |
|------|----|----- |
| **Tap feedback** | Answer a press with something clear (ripple/opacity/elevation) inside 80-150ms | A tap that draws no visual response |
| **Animation timing** | Hold micro-interactions near 150-300ms with platform-native easing | Instant transitions or slow ones (>500ms) |
| **Accessibility focus** | Line screen-reader focus order up with visual order and keep labels descriptive | Unlabeled controls or a confusing focus path |
| **Disabled state clarity** | Mark disabled with the semantics (`disabled`/native disabled props), dial down emphasis, kill the tap | Controls that look tappable but do nothing |
| **Touch target minimum** | Tap areas at >=44x44pt (iOS) or >=48x48dp (Android); grow the hit area when the icon is smaller | Tiny tap targets or icon-only hits with no padding |
| **Gesture conflict prevention** | One primary gesture per region; no nested tap/drag clashes | Overlapping gestures that fire by accident |
| **Semantic native controls** | Build on native primitives (`Button`, `Pressable`, platform equivalents) with the right accessibility roles | Plain containers pressed into service as primary controls |

### Light/Dark Mode Contrast

| Rule | Do | Don't |
|------|----|----- |
| **Surface readability (light)** | Set cards/surfaces apart from the background with enough opacity/elevation | Over-transparent surfaces that smear the hierarchy |
| **Text contrast (light)** | Hold body text at >=4.5:1 against light surfaces | Low-contrast gray body text |
| **Text contrast (dark)** | Hold primary text at >=4.5:1 and secondary at >=3:1 on dark surfaces | Dark-mode text that melts into the background |
| **Border and divider visibility** | Keep separators visible in both themes, not just light mode | Borders that vanish in one mode |
| **State contrast parity** | Keep pressed/focused/disabled equally legible in both light and dark | Interaction states defined for one theme only |
| **Token-driven theming** | Drive surfaces/text/icons from semantic color tokens mapped per theme | Per-screen hardcoded hex |
| **Scrim and modal legibility** | A modal scrim strong enough to lift the foreground clear (typically 40-60% black) | A weak scrim that lets the background compete |

### Layout & Spacing

| Rule | Do | Don't |
|------|----|----- |
| **Safe-area compliance** | Honor top/bottom safe areas for every fixed header, tab bar, and CTA bar | Fixed UI parked under the notch, status bar, or gesture area |
| **System bar clearance** | Leave room for the status/navigation bars and gesture home indicator | Tappable content colliding with OS chrome |
| **Consistent content width** | Keep content width predictable per device class (phone/tablet) | Arbitrary widths that drift screen to screen |
| **8dp spacing rhythm** | Run one 4/8dp spacing system through padding/gaps/section spacing | Random spacing increments with no rhythm |
| **Readable text measure** | Keep long-form text legible on large devices — no edge-to-edge paragraphs on tablets | Full-width long text that fights readability |
| **Section spacing hierarchy** | Set clear vertical rhythm tiers (e.g., 16/24/32/48) by hierarchy | Like-level UI spaced inconsistently |
| **Adaptive gutters by breakpoint** | Widen horizontal insets on larger widths and in landscape | The same narrow gutter at every size/orientation |
| **Scroll and fixed element coexistence** | Add top/bottom content insets so lists clear the fixed bars | Scroll content hidden behind sticky headers/footers |

---

## Pre-Delivery Checklist

Walk this before the UI code leaves your hands:
Scope notice: this checklist covers App UI (iOS/Android/React Native/Flutter).

### Visual Quality
- [ ] No emoji standing in for icons (SVG instead)
- [ ] Every icon drawn from one consistent family and style
- [ ] Official brand assets, right proportions, right clear space
- [ ] Pressed-state visuals hold the layout bounds — no shift, no jitter
- [ ] Semantic theme tokens used throughout — no per-screen hardcoded colors

### Interaction
- [ ] Every tappable element answers a press (ripple/opacity/elevation)
- [ ] Touch targets clear the minimum (>=44x44pt iOS, >=48x48dp Android)
- [ ] Micro-interactions land in 150-300ms with native-feeling easing
- [ ] Disabled states read clearly and don't respond
- [ ] Screen-reader focus order tracks visual order; interactive labels are descriptive
- [ ] Gesture regions steer clear of nested/conflicting interactions (tap/drag/back-swipe)

### Light/Dark Mode
- [ ] Primary text >=4.5:1 in both light and dark mode
- [ ] Secondary text >=3:1 in both light and dark mode
- [ ] Dividers/borders and interaction states stay distinct in both modes
- [ ] Modal/drawer scrim opaque enough to keep the foreground legible (typically 40-60% black)
- [ ] Both themes actually tested — neither inferred from the other

### Layout
- [ ] Safe areas honored for headers, tab bars, and bottom CTA bars
- [ ] No scroll content hiding behind fixed/sticky bars
- [ ] Checked on small phone, large phone, and tablet (portrait + landscape)
- [ ] Horizontal insets/gutters adapt by device size and orientation
- [ ] 4/8dp spacing rhythm holds across component, section, and page levels
- [ ] Long-form text measure stays readable on larger devices (no edge-to-edge paragraphs)

### Accessibility
- [ ] Every meaningful image/icon carries an accessibility label
- [ ] Form fields have labels, hints, and clear error messages
- [ ] Color is never the lone indicator
- [ ] Reduced motion and dynamic text size both work without breaking the layout
- [ ] Accessibility traits/roles/states (selected, disabled, expanded) announced correctly