# Redesign Audit Checklist

Reach for this when an existing project needs lifting. Work the three passes in order: Scan → Diagnose → Fix.

## Workflow

1. **Scan** — Read through the codebase. Pin down the framework, the styling approach (Tailwind, vanilla CSS, styled-components), and the design habits already in place.
2. **Diagnose** — Walk every category below. Write down each generic pattern, soft spot, and missing state you find.
3. **Fix** — Make targeted upgrades inside the stack that's already there. No ground-up rewrites.

**Rules:**
- Stay on the existing stack. Don't switch frameworks.
- Keep what works working — test after each change.
- Read `package.json` before reaching for a new dependency.
- Small, reviewable changes beat sweeping rewrites. Keep each one focused.

---

## Audit Categories

### 1. Typography
- [ ] Browser default fonts or Inter everywhere → swap in `Geist`, `Outfit`, `Cabinet Grotesk`, or `Satoshi`
- [ ] Headlines with no weight to them → tighten tracking, drop line-height, push up the display size
- [ ] Body lines running too wide → cap around ~65ch, open up the line-height
- [ ] Only 400 + 700 on hand → bring in 500/600 for a gentler hierarchy
- [ ] Numbers in a proportional face → switch to monospace or `font-variant-numeric: tabular-nums`
- [ ] All-caps subheaders all over → try lowercase italic or sentence case
- [ ] Last words stranded on their own line → `text-wrap: balance` or `text-wrap: pretty`
- [ ] Serif fonts on a dashboard → keep it to high-end sans-serif pairings
### 2. Color and Surfaces
- [ ] Pure `#000000` → trade for off-black or a tinted dark
- [ ] Oversaturated accents → pull saturation under 80%
- [ ] More than one accent color → cut down to a single one
- [ ] Warm and cool grays mixed together → settle on one family and hold it
- [ ] The purple/blue AI gradient look → neutral base plus one accent
- [ ] Stock `box-shadow` → tint the shadow toward the background hue
- [ ] Flat surfaces with no texture → drop in a faint noise/grain overlay
- [ ] Perfectly even linear gradients → go radial, mesh, or noise-overlaid
- [ ] A lone dark block dropped into a light page (or the reverse) → commit to one tone, or use a slightly darker shade of the same palette
### 3. Layout
- [ ] Everything centered and symmetrical → break it with offset margins and mixed aspect ratios
- [ ] Three equal card columns as the feature row → 2-col zig-zag, asymmetric grid, or horizontal scroll
- [ ] `h-screen` / `height: 100vh` → switch to `min-height: 100dvh`
- [ ] Flexbox carrying grid math in `calc()` → hand it to CSS Grid
- [ ] No max-width container → add a 1200-1440px constraint with auto margins
- [ ] One border-radius value everywhere → vary it between inner and outer elements
- [ ] No overlap, no depth → layer with negative margins
- [ ] A left sidebar by reflex on every dashboard → weigh top nav, a command menu, or a collapsible panel
- [ ] CTAs floating mid-card in a card group → pin them to the card bottom
- [ ] Marketing pages starved of whitespace → double the spacing, let it breathe
### 4. Interactivity and States
- [ ] Buttons with no hover state → add a background shift, scale, or translate
- [ ] No pressed feedback → `scale(0.98)` or `translateY(1px)` on press
- [ ] Transitions that snap → ease them over 200-300ms
- [ ] No focus ring → a visible focus indicator (accessibility, not optional)
- [ ] The generic circular spinner → a skeleton loader shaped like the layout
- [ ] No empty state → compose a real "getting started" view
- [ ] No error state → inline messages on forms (never `window.alert()`)
- [ ] Dead links (`href="#"`) → wire to real destinations or visibly disable
- [ ] No current-page marker in nav → style the active link apart
- [ ] Anchor jumps that snap → `scroll-behavior: smooth`
- [ ] Animating `top`/`left`/`width`/`height` → move to `transform` + `opacity`
### 5. Content
- [ ] Boilerplate placeholder names → diverse, realistic ones
- [ ] Round fake numbers → organic, messy data
- [ ] AI copy clichés → plain, specific language
- [ ] Lorem Ipsum → real draft copy
- [ ] Exclamation marks in success states → drop them
- [ ] Title Case On Every Header → sentence case
- [ ] One avatar reused across users → a unique asset per person
- [ ] Every blog post dated the same → randomize them
### 6. Components and Code
- [ ] Generic card (border + shadow + white bg) at high density → use spacing/dividers
- [ ] Always one filled + one ghost button → add text links, quiet the noise
- [ ] Lucide/Feather as the only icon set → try Phosphor or Heroicons to differentiate
- [ ] Worn-out icon metaphors (rocketship, shield) → less obvious choices
- [ ] Div soup → semantic HTML: `nav`, `main`, `article`, `aside`, `section`
- [ ] Inline styles tangled with CSS classes → move it all into the project's system
- [ ] Arbitrary z-index (`z-[9999]`) → a clean z-index scale
- [ ] No alt text on meaningful images → describe them for screen readers
- [ ] Missing meta tags → add `title`, `description`, `og:image`

---

## Fix Priority Order

Run them in this sequence — most payoff for least risk:

1. **Font swap** — the biggest instant lift, lowest risk
2. **Color cleanup** — pull out the clashing and oversaturated tones
3. **Hover and active states** — what makes the surface feel alive
4. **Layout and spacing** — a proper grid, max-width, even padding
5. **Replace generic components** — trade the clichés for modern alternatives
6. **Loading, empty, error states** — what makes it read as finished
7. **Polish the type scale** — the premium last touch

---

## Strategic Omissions (What AI Typically Forgets)

These rarely show up in AI output. Check for them on purpose:

- **No legal links** → privacy policy + terms in the footer
- **No "back" navigation** → every page needs a way out
- **No custom 404** → design a helpful, branded "not found"
- **No form validation** → client-side checks for emails, required fields, formats
- **No "skip to content" link** → essential for keyboard users
- **No favicon** → always include a branded one
- **No social sharing meta** → `og:image`, `og:title`, `twitter:card`
